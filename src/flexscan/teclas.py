"""Teclas del programa: una única tabla dice qué hace cada una y en qué fase funciona.

La misma tabla sirve para filtrar las pulsaciones (una tecla fuera de su fase no hace nada
y solo muestra un aviso) y, más adelante, para generar la ventana de ayuda de teclas.
"""
from collections import namedtuple

import cv2
import numpy as np
from PIL import Image, ImageDraw

from flexscan.instrucciones import _fuente
from flexscan.medida import FALLIDA, TERMINADA

# Fases del programa
CALIBRACION = "calibracion"    # aún no hay escala en centímetros
INICIO = "inicio"              # sin sesión ni acceso en curso
ACCESO = "acceso"              # enseñando el patrón de símbolos
PREPARACION = "preparacion"    # cuenta atrás y aprendizaje del fondo
MEDIDA = "medida"              # colocarse y hacer el estiramiento
RESULTADO = "resultado"        # medida terminada, a la espera de otra

FASES = (CALIBRACION, INICIO, ACCESO, PREPARACION, MEDIDA, RESULTADO)
NOMBRE_FASE = {
    CALIBRACION: "calibración",
    INICIO: "inicio",
    ACCESO: "acceso",
    PREPARACION: "preparación del fondo",
    MEDIDA: "medida",
    RESULTADO: "resultado",
}

USO = "uso"                    # teclas del recorrido normal
DEPURACION = "depuración"      # teclas para ver cómo trabaja el programa por dentro

Tecla = namedtuple("Tecla", "codigo nombre tipo fases efecto")

TECLAS = (
    Tecla("q", "Salir", USO, FASES,
          "Cierra el programa."),
    Tecla("Esc", "Volver al inicio", USO, (ACCESO,),
          "Cancela el acceso en curso y vuelve a la pantalla de inicio (no con el acceso bloqueado)."),
    Tecla("e", "Entrar", USO, (INICIO, ACCESO),
          "Empieza el acceso: hay que enseñar a la cámara el patrón de símbolos."),
    Tecla("r", "Registrarse", USO, (INICIO,),
          "Abre el formulario para registrar un usuario nuevo."),
    Tecla("s", "Cerrar sesión", USO, (PREPARACION, MEDIDA, RESULTADO),
          "Cierra la sesión y vuelve al inicio. Con una medida en curso, la descarta primero."),
    Tecla("n", "Nueva medida", USO, (MEDIDA, RESULTADO),
          "Descarta la medida actual y prepara otra."),
    Tecla("k", "Calibrar escala", USO, (CALIBRACION, INICIO),
          "Calibra los centímetros con la hoja A4 colocada en el sitio del ejercicio."),
    Tecla("c", "Imagen corregida u original", DEPURACION, (CALIBRACION, INICIO, ACCESO),
          "Alterna entre la imagen con la distorsión de la lente corregida y la original."),
    Tecla("m", "Máscara", DEPURACION, (INICIO, ACCESO),
          "Abre una ventana con la máscara que usa el detector de la tarjeta."),
    Tecla("t", "Tarjeta", DEPURACION, (INICIO, ACCESO),
          "Abre una ventana con la tarjeta enderezada y los rasgos que se miden en ella."),
    Tecla("f", "Aprender fondo", DEPURACION, (INICIO,),
          "Aprende de nuevo el fondo vacío (unos 2 s, sin nadie en la imagen)."),
    Tecla("b", "Silueta", DEPURACION, (INICIO, ACCESO, PREPARACION, MEDIDA),
          "Abre una ventana con la silueta de la persona separada del fondo."),
    Tecla("v", "Caja y centro", DEPURACION, (INICIO, ACCESO, PREPARACION, MEDIDA),
          "Dibuja la caja y el centro detectados, y abre la gráfica de la ganancia K del seguimiento."),
    Tecla("p", "Puntos del cuerpo", DEPURACION, (MEDIDA,),
          "Activa la detección de los puntos del cuerpo, necesaria para medir la distancia."),
)
POR_CODIGO = {t.codigo: t for t in TECLAS}

VENTANAS_AUXILIARES = ("Mascara", "Tarjeta", "Silueta", "Ganancia K")


def fase_actual(calibrado, acceso_activo, hay_usuario, preparando, estado_medida):
    """Fase del programa a partir de su estado."""
    if not calibrado:
        return CALIBRACION
    if acceso_activo:
        return ACCESO
    if not hay_usuario:
        return INICIO
    if preparando:
        return PREPARACION
    if estado_medida in (TERMINADA, FALLIDA):
        return RESULTADO
    return MEDIDA


def normalizar(tecla):
    """Las mayúsculas valen como minúsculas (por si está activada la tecla de bloqueo)."""
    return tecla + 32 if 65 <= tecla <= 90 else tecla


def _codigo(tecla):
    if tecla == 27:
        return "Esc"
    if 32 <= tecla < 127:
        return chr(tecla)
    return None


def permitida(tecla, fase):
    entrada = POR_CODIGO.get(_codigo(tecla))
    return entrada is not None and fase in entrada.fases


def texto_no_disponible(entrada):
    fases = ", ".join(NOMBRE_FASE[f] for f in entrada.fases)
    return f"La tecla {entrada.codigo.upper()} ({entrada.nombre}) no está disponible ahora. Funciona en: {fases}."


def filtrar(tecla, fase, aviso, ahora):
    """Devuelve la tecla si vale en esta fase; si no, 255 (ninguna) y, si procede, un aviso.

    Las teclas que no están en la tabla se ignoran sin más, como hasta ahora.
    """
    entrada = POR_CODIGO.get(_codigo(tecla))
    if entrada is None:
        return 255
    if fase in entrada.fases:
        return tecla
    if entrada.codigo != "Esc":
        aviso.mostrar(texto_no_disponible(entrada), ahora)
    return 255


def cerrar_ventana(nombre):
    """Cierra una ventana de OpenCV sin fallar si no estaba abierta."""
    try:
        cv2.destroyWindow(nombre)
    except cv2.error:
        pass


def cerrar_auxiliares():
    for nombre in VENTANAS_AUXILIARES:
        cerrar_ventana(nombre)


class AvisoTecla:
    """Franja de texto abajo a la izquierda que se desvanece sola."""
    DURACION_S = 3.0
    DESVANECER_S = 0.6
    MARGEN = 10

    def __init__(self):
        self._hasta = 0.0
        self._bgr = None
        self._alfa = None

    def mostrar(self, texto, ahora):
        fuente = _fuente(22)
        caja = fuente.getbbox(texto)
        ancho, alto = caja[2] - caja[0] + 32, 42
        img = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((0, 0, ancho - 1, alto - 1), radius=10, fill=(24, 24, 24, 225),
                            outline=(232, 131, 58, 255), width=2)
        d.text((16, alto // 2), texto, font=fuente, fill=(255, 255, 255, 255), anchor="lm")
        rgba = np.asarray(img)
        self._bgr = rgba[..., 2::-1].astype(np.float32)
        self._alfa = (rgba[..., 3:4] / 255.0).astype(np.float32)
        self._hasta = ahora + self.DURACION_S

    def dibujar(self, frame, ahora):
        if self._bgr is None or ahora >= self._hasta:
            return
        alto_f, ancho_f = frame.shape[:2]
        alto, ancho = self._alfa.shape[:2]
        ancho_v = min(ancho, ancho_f - 2 * self.MARGEN)
        if ancho_v <= 0:
            return
        y0 = alto_f - alto - self.MARGEN
        x0 = self.MARGEN
        factor = min(1.0, (self._hasta - ahora) / self.DESVANECER_S)
        a = self._alfa[:, :ancho_v] * factor
        roi = frame[y0:y0 + alto, x0:x0 + ancho_v].astype(np.float32)
        frame[y0:y0 + alto, x0:x0 + ancho_v] = (roi * (1 - a) + self._bgr[:, :ancho_v] * a).astype(np.uint8)
