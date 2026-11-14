"""Pantalla de acceso: ventana para pedir el nombre y panel con la secuencia sobre el vídeo."""
import math

import cv2
import numpy as np

from flexscan import secuencia as sec
from flexscan import usuarios
from flexscan.registro import (AZUL_OSCURO, BLANCO, CARPETA_PATRONES, FUENTE,
                               GRIS, MAX_NOMBRE, ROJO, VERDE)

LADO = 64                      # lado de cada miniatura, en píxeles
_miniaturas = {}               # imágenes ya cargadas

COLOR_ESTADO = {sec.CONCEDIDO: VERDE, sec.DENEGADO: ROJO, sec.BLOQUEADO: ROJO}
TEXTO_ESTADO = {sec.CONCEDIDO: "ACCESO CONCEDIDO",
                sec.DENEGADO: "ACCESO DENEGADO",
                sec.BLOQUEADO: "BLOQUEADO"}


def _miniatura(simbolo):
    """Imagen pequeña del símbolo, leída de patrones/ una sola vez."""
    if simbolo not in _miniaturas:
        img = cv2.imread(str(CARPETA_PATRONES / f"{simbolo}.png"))
        if img is None:
            img = np.full((LADO, LADO, 3), 200, np.uint8)
        _miniaturas[simbolo] = cv2.resize(img, (LADO, LADO))
    return _miniaturas[simbolo]


def _pista(acceso, ahora):
    """Texto de ayuda según el estado."""
    if acceso.estado == sec.ESPERANDO:
        return "Ensena el primer simbolo"
    if acceso.estado == sec.EN_CURSO:
        return f"Ensena el simbolo {len(acceso.simbolos) + 1} de {usuarios.LONGITUD}"
    if acceso.estado == sec.CONCEDIDO:
        return "Acceso correcto"
    if acceso.estado == sec.DENEGADO:
        return "Clave incorrecta"
    return f"Demasiados fallos: espera {math.ceil(acceso.segundos_bloqueo(ahora))} s"


def dibujar_acceso(frame, acceso, ahora):
    """Dibuja sobre el vídeo el panel con la secuencia y el resultado. Modifica frame."""
    alto, ancho = frame.shape[:2]
    y0, y1 = alto - 160, alto - 20
    x0, x1 = 20, 440
    frame[y0:y1, x0:x1] = (frame[y0:y1, x0:x1] * 0.35).astype(np.uint8)   # fondo oscuro
    cv2.putText(frame, f"Usuario: {acceso.nombre}", (x0 + 16, y0 + 30), FUENTE, 0.7, BLANCO, 2)

    borde = COLOR_ESTADO.get(acceso.estado, BLANCO)
    for i in range(usuarios.LONGITUD):
        x, y = x0 + 16 + i * 84, y0 + 44
        cv2.rectangle(frame, (x, y), (x + LADO, y + LADO), BLANCO, -1)
        if i < len(acceso.simbolos):
            frame[y:y + LADO, x:x + LADO] = _miniatura(acceso.simbolos[i])
        else:
            cv2.putText(frame, str(i + 1), (x + 20, y + 44), FUENTE, 0.9, (190, 190, 190), 2)
        cv2.rectangle(frame, (x - 2, y - 2), (x + LADO + 2, y + LADO + 2), borde, 3)
    cv2.putText(frame, _pista(acceso, ahora), (x0 + 16, y1 - 12), FUENTE, 0.55, BLANCO, 1)

    if acceso.estado in TEXTO_ESTADO:
        texto = TEXTO_ESTADO[acceso.estado]
        if acceso.estado == sec.BLOQUEADO:
            texto += f"  {math.ceil(acceso.segundos_bloqueo(ahora))} s"
        (ancho_texto, _), _ = cv2.getTextSize(texto, FUENTE, 1.6, 4)
        cv2.putText(frame, texto, ((ancho - ancho_texto) // 2, 130), FUENTE, 1.6,
                    COLOR_ESTADO[acceso.estado], 4)


class FormularioNombre:
    """Ventanita para escribir el nombre con el que se quiere entrar."""

    def __init__(self):
        self.nombre = ""
        self.resultado = None          # None mientras sigue abierta; luego "aceptado" o "cancelado"

    def escribir(self, tecla):
        """Recibe el código de una tecla (lo que devuelve waitKey & 0xFF)."""
        if tecla == 8:                                   # retroceso
            self.nombre = self.nombre[:-1]
        elif tecla == 13:                                # intro
            if self.nombre.strip():
                self.resultado = "aceptado"
        elif tecla == 27:                                # escape
            self.resultado = "cancelado"
        elif 32 <= tecla <= 126 and len(self.nombre) < MAX_NOMBRE:
            self.nombre += chr(tecla)

    def dibujar(self):
        lienzo = np.full((190, 560, 3), GRIS, np.uint8)
        cv2.rectangle(lienzo, (0, 0), (560, 46), AZUL_OSCURO, -1)
        cv2.putText(lienzo, "Entrar", (20, 32), FUENTE, 0.9, BLANCO, 2)
        cv2.putText(lienzo, "Nombre:", (30, 78), FUENTE, 0.55, AZUL_OSCURO, 1)
        cv2.rectangle(lienzo, (30, 88), (530, 128), BLANCO, -1)
        cv2.rectangle(lienzo, (30, 88), (530, 128), AZUL_OSCURO, 2)
        cv2.putText(lienzo, self.nombre + "_", (40, 118), FUENTE, 0.8, AZUL_OSCURO, 2)
        cv2.putText(lienzo, "Intro: aceptar     Esc: cancelar", (30, 165), FUENTE, 0.55, AZUL_OSCURO, 1)
        return lienzo


def pedir_nombre():
    """Abre la ventanita del nombre. Devuelve el nombre, o None si se cancela."""
    formulario = FormularioNombre()
    ventana = "FlexScan - Entrar"
    cv2.namedWindow(ventana)
    while formulario.resultado is None:
        cv2.imshow(ventana, formulario.dibujar())
        formulario.escribir(cv2.waitKey(30) & 0xFF)
        if cv2.getWindowProperty(ventana, cv2.WND_PROP_VISIBLE) < 1:
            formulario.resultado = "cancelado"           # se cerró la ventana con la X
    cv2.destroyWindow(ventana)
    return formulario.nombre.strip() if formulario.resultado == "aceptado" else None

def iniciar_acceso(anterior=None):                                          
    """Pide el nombre y devuelve una Secuencia nueva, o None si no se puede o se cancela.   
                                                                            
    No se puede mientras haya un bloqueo en marcha. Si se vuelve a entrar con el mismo      
    nombre se conservan los fallos, para que repetir la tecla no sirva para saltarse el bloqueo.   
    """                                                                     
    if anterior is not None and anterior.estado == sec.BLOQUEADO:           
        return None                                                          
    nombre = pedir_nombre()                                                
    if nombre is None:                                                      
        return None                                                          
    nueva = sec.Secuencia(nombre)                                            
    if anterior is not None and (usuarios.normalizar(anterior.nombre)        
                                 == usuarios.normalizar(nombre)):            
        nueva.intentos = anterior.intentos                                   
    return nueva                               

def dibujar_usuario(frame, nombre):                                                       
    """Escribe, discretamente y arriba a la derecha, el usuario que tiene la sesión abierta."""   
    texto = f"Usuario: {nombre}"                                                           
    (ancho_texto, _), _ = cv2.getTextSize(texto, FUENTE, 0.6, 1)                            
    x1, y1 = frame.shape[1] - 10, 38                                                       
    x0, y0 = x1 - ancho_texto - 16, 10                                                      
    frame[y0:y1, x0:x1] = (frame[y0:y1, x0:x1] * 0.4).astype(np.uint8)    # fondo oscuro    
    cv2.putText(frame, texto, (x0 + 8, y1 - 10), FUENTE, 0.6, BLANCO, 1)                                                  