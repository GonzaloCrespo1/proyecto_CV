"""Pantalla de registro: formulario con el nombre y la clave de cuatro símbolos (ventana de OpenCV)."""
import unicodedata
from pathlib import Path

import cv2
import numpy as np

from flexscan import usuarios

ANCHO, ALTO = 700, 530
CARPETA_PATRONES = Path(__file__).resolve().parents[2] / "patrones"
MAX_NOMBRE = 20

# Rectángulos de la pantalla (x0, y0, x1, y1), en píxeles
CAJA_NOMBRE = (50, 80, 650, 120)
BOTONES_SIMBOLO = [(50 + i * 160, 170, 170 + i * 160, 300) for i in range(len(usuarios.SIMBOLOS))]
HUECOS = [(50 + i * 80, 335, 114 + i * 80, 399) for i in range(usuarios.LONGITUD)]
BOTON_BORRAR = (50, 450, 230, 500)
BOTON_GUARDAR = (260, 450, 440, 500)
BOTON_CANCELAR = (470, 450, 650, 500)

# Colores (BGR)
AZUL_OSCURO = (63, 38, 18)
VERDE = (46, 138, 60)
ROJO = (79, 52, 192)
GRIS = (240, 236, 232)
BLANCO = (255, 255, 255)
FUENTE = cv2.FONT_HERSHEY_SIMPLEX


def _ascii(texto):
    """Quita tildes y ñ: las fuentes de OpenCV solo dibujan caracteres ASCII."""
    sin = unicodedata.normalize("NFKD", texto)
    return sin.encode("ascii", "ignore").decode("ascii")


def _dentro(x, y, rect):
    x0, y0, x1, y1 = rect
    return x0 <= x <= x1 and y0 <= y <= y1


class Formulario:
    """Estado del formulario (nombre, clave elegida, mensaje) y su dibujo."""

    def __init__(self, ruta=usuarios.RUTA):
        self.ruta = ruta
        self.nombre = ""
        self.secuencia = []
        self.mensaje = ""
        self.resultado = None            # None mientras sigue abierto; luego "guardado" o "cancelado"
        self._imagenes = {}

    def escribir(self, tecla):
        """Recibe el código de una tecla (lo que devuelve waitKey & 0xFF)."""
        if tecla == 8:                                   # retroceso
            self.nombre = self.nombre[:-1]
        elif tecla == 13:                                # intro
            self.guardar()
        elif tecla == 27:                                # escape
            self.resultado = "cancelado"
        elif 32 <= tecla <= 126 and len(self.nombre) < MAX_NOMBRE:
            self.nombre += chr(tecla)

    def pulsar(self, x, y):
        """Recibe un clic del ratón."""
        for simbolo, rect in zip(usuarios.SIMBOLOS, BOTONES_SIMBOLO):
            if _dentro(x, y, rect):
                if len(self.secuencia) < usuarios.LONGITUD:
                    self.secuencia.append(simbolo)
                    self.mensaje = ""
                else:
                    self.mensaje = "Ya hay 4 simbolos: borra o guarda"
                return
        if _dentro(x, y, BOTON_BORRAR):
            if self.secuencia:
                self.secuencia.pop()
            self.mensaje = ""
        elif _dentro(x, y, BOTON_GUARDAR):
            self.guardar()
        elif _dentro(x, y, BOTON_CANCELAR):
            self.resultado = "cancelado"

    def guardar(self):
        """Guarda al usuario; si algo no es válido, deja el motivo en el mensaje."""
        try:
            usuarios.registrar(self.nombre, self.secuencia, self.ruta)
        except usuarios.ErrorUsuario as error:
            texto = _ascii(str(error))
            self.mensaje = texto[:1].upper() + texto[1:]
        else:
            self.mensaje = "Usuario registrado"
            self.resultado = "guardado"

    def _imagen(self, simbolo, lado):
        """Imagen del símbolo desde patrones/, a tamaño lado x lado (se carga una vez)."""
        clave = (simbolo, lado)
        if clave not in self._imagenes:
            img = cv2.imread(str(CARPETA_PATRONES / f"{simbolo}.png"))
            if img is None:
                img = np.full((lado, lado, 3), 200, np.uint8)
            self._imagenes[clave] = cv2.resize(img, (lado, lado))
        return self._imagenes[clave]

    def dibujar(self):
        """Devuelve la imagen del formulario en su estado actual."""
        lienzo = np.full((ALTO, ANCHO, 3), GRIS, np.uint8)
        cv2.rectangle(lienzo, (0, 0), (ANCHO, 50), AZUL_OSCURO, -1)
        cv2.putText(lienzo, "Registro de usuario", (20, 34), FUENTE, 0.9, BLANCO, 2)

        cv2.putText(lienzo, "Nombre (sin tildes):", (50, 72), FUENTE, 0.55, AZUL_OSCURO, 1)
        cv2.rectangle(lienzo, CAJA_NOMBRE[:2], CAJA_NOMBRE[2:], BLANCO, -1)
        cv2.rectangle(lienzo, CAJA_NOMBRE[:2], CAJA_NOMBRE[2:], AZUL_OSCURO, 2)
        cv2.putText(lienzo, self.nombre + "_", (60, 108), FUENTE, 0.8, AZUL_OSCURO, 2)

        cv2.putText(lienzo, "Clave: pulsa los 4 simbolos en orden", (50, 160), FUENTE, 0.55, AZUL_OSCURO, 1)
        for simbolo, rect in zip(usuarios.SIMBOLOS, BOTONES_SIMBOLO):
            x0, y0, x1, y1 = rect
            cv2.rectangle(lienzo, (x0, y0), (x1, y1), BLANCO, -1)
            cv2.rectangle(lienzo, (x0, y0), (x1, y1), AZUL_OSCURO, 2)
            lienzo[y0 + 5:y0 + 105, x0 + 10:x0 + 110] = self._imagen(simbolo, 100)
            cv2.putText(lienzo, simbolo, (x0 + 10, y1 - 8), FUENTE, 0.5, AZUL_OSCURO, 1)

        cv2.putText(lienzo, "Tu clave:", (50, 326), FUENTE, 0.55, AZUL_OSCURO, 1)
        for i, rect in enumerate(HUECOS):
            x0, y0, x1, y1 = rect
            cv2.rectangle(lienzo, (x0, y0), (x1, y1), BLANCO, -1)
            cv2.rectangle(lienzo, (x0, y0), (x1, y1), AZUL_OSCURO, 2)
            if i < len(self.secuencia):
                lienzo[y0 + 2:y1 - 2, x0 + 2:x1 - 2] = self._imagen(self.secuencia[i], 60)
            else:
                cv2.putText(lienzo, str(i + 1), (x0 + 22, y0 + 42), FUENTE, 0.9, (190, 190, 190), 2)

        color = VERDE if self.resultado == "guardado" else ROJO
        cv2.putText(lienzo, _ascii(self.mensaje), (50, 432), FUENTE, 0.6, color, 2)

        for rect, texto, fondo in ((BOTON_BORRAR, "Borrar ultimo", AZUL_OSCURO),
                                   (BOTON_GUARDAR, "Guardar", VERDE),
                                   (BOTON_CANCELAR, "Cancelar", ROJO)):
            cv2.rectangle(lienzo, rect[:2], rect[2:], fondo, -1)
            (ancho, alto), _ = cv2.getTextSize(texto, FUENTE, 0.65, 2)
            cx, cy = (rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2
            cv2.putText(lienzo, texto, (cx - ancho // 2, cy + alto // 2), FUENTE, 0.65, BLANCO, 2)
        return lienzo


def pedir_registro(ruta=usuarios.RUTA):
    """Abre la pantalla de registro. Devuelve True si se ha guardado un usuario."""
    formulario = Formulario(ruta)
    ventana = "FlexScan - Registro"
    cv2.namedWindow(ventana)

    def raton(evento, x, y, flags, parametro):
        if evento == cv2.EVENT_LBUTTONDOWN:
            formulario.pulsar(x, y)

    cv2.setMouseCallback(ventana, raton)
    while formulario.resultado is None:
        cv2.imshow(ventana, formulario.dibujar())
        formulario.escribir(cv2.waitKey(30) & 0xFF)
        if cv2.getWindowProperty(ventana, cv2.WND_PROP_VISIBLE) < 1:
            formulario.resultado = "cancelado"       # se cerró la ventana con la X
    if formulario.resultado == "guardado":
        cv2.imshow(ventana, formulario.dibujar())
        cv2.waitKey(1200)                            # deja ver «Usuario registrado»
    cv2.destroyWindow(ventana)
    return formulario.resultado == "guardado"