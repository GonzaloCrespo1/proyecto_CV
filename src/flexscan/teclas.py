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

DESCRIPCION_FASE = {
    CALIBRACION: "todavía no hay escala en centímetros",
    INICIO: "programa calibrado, sin acceso ni sesión",
    ACCESO: "enseñando el patrón de símbolos a la cámara",
    PREPARACION: "cuenta atrás y aprendizaje del fondo",
    MEDIDA: "colocarse y hacer el estiramiento",
    RESULTADO: "medida terminada, a la espera de otra",
}

USO = "uso"                    # teclas del recorrido normal
DEPURACION = "depuración"      # teclas del equipo y para ver cómo trabaja el programa por dentro

Tecla = namedtuple("Tecla", "codigo nombre tipo fases efecto requiere", defaults=(None,))

# Estado de una tecla en un momento dado
ACTIVA, OTRA_FASE, FALTA_FONDO = "activa", "otra_fase", "falta_fondo"

TECLAS = (
    Tecla("q", "Salir", USO, FASES,
          "Cierra el programa."),
    Tecla("Esc", "Volver al inicio", USO, (ACCESO,),
          "Cancela el acceso y vuelve al inicio."),
    Tecla("e", "Entrar", USO, (INICIO, ACCESO),
          "Empieza el acceso con tu patrón de símbolos."),
    Tecla("r", "Registrarse", USO, (INICIO,),
          "Registra un usuario nuevo."),
    Tecla("s", "Cerrar sesión", USO, (PREPARACION, MEDIDA, RESULTADO),
          "Cierra la sesión (si hay medida en curso, la descarta)."),
    Tecla("n", "Nueva medida", USO, (MEDIDA, RESULTADO),
          "Descarta la medida actual y prepara otra."),
    Tecla("h", "Teclas", USO, (INICIO, ACCESO, PREPARACION, MEDIDA, RESULTADO),
          "Abre o cierra la ventana de teclas."),
    Tecla("k", "Calibrar escala", DEPURACION, (CALIBRACION, INICIO, MEDIDA, RESULTADO),
          "Calibra con la hoja A4 (descarta la medida en curso)."),
    Tecla("c", "Imagen corregida u original", DEPURACION, (CALIBRACION, INICIO, ACCESO),
          "Alterna imagen corregida y original."),
    Tecla("m", "Máscara", DEPURACION, (INICIO, ACCESO),
          "Ventana con la máscara del detector de tarjeta."),
    Tecla("t", "Tarjeta", DEPURACION, (INICIO, ACCESO),
          "Ventana con la tarjeta enderezada y sus rasgos."),
    Tecla("f", "Aprender fondo", DEPURACION, (INICIO,),
          "Aprende de nuevo el fondo (sin nadie delante)."),
    Tecla("b", "Silueta", DEPURACION, (INICIO, ACCESO, PREPARACION, MEDIDA, RESULTADO),
          "Silueta separada del fondo (necesita fondo aprendido).", "fondo"),
    Tecla("v", "Caja y centro", DEPURACION, (INICIO, ACCESO, PREPARACION, MEDIDA, RESULTADO),
          "Caja, centro y ganancia K (necesita fondo aprendido).", "fondo"),
    Tecla("p", "Puntos del cuerpo", DEPURACION, (MEDIDA,),
          "Muestra u oculta los puntos del cuerpo en la imagen."),
)
FASES_BOTON = (INICIO, ACCESO, PREPARACION, MEDIDA, RESULTADO)   # fases en las que se puede abrir la ventana de teclas
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


def estado_tecla(entrada, fase, fondo_listo):
    """ACTIVA si vale ahora; OTRA_FASE si no vale en esta fase; FALTA_FONDO si vale en ella pero aún no hay fondo."""
    if fase not in entrada.fases:
        return OTRA_FASE
    if entrada.requiere == "fondo" and not fondo_listo:
        return FALTA_FONDO
    return ACTIVA


def permitida(tecla, fase, fondo_listo=True):
    entrada = POR_CODIGO.get(_codigo(tecla))
    return entrada is not None and estado_tecla(entrada, fase, fondo_listo) == ACTIVA


def texto_no_disponible(entrada):
    fases = ", ".join(NOMBRE_FASE[f] for f in entrada.fases)
    return f"La tecla {entrada.codigo.upper()} ({entrada.nombre}) no está disponible ahora. Funciona en: {fases}."


def filtrar(tecla, fase, aviso, ahora, fondo_listo=True):
    """Devuelve la tecla si vale en esta fase; si no, 255 (ninguna) y, si procede, un aviso.

    Las teclas que no están en la tabla se ignoran sin más, como hasta ahora.
    """
    entrada = POR_CODIGO.get(_codigo(tecla))
    if entrada is None:
        return 255
    estado = estado_tecla(entrada, fase, fondo_listo)
    if estado == ACTIVA:
        return tecla
    if estado == FALTA_FONDO:
        aviso.mostrar(f"La tecla {entrada.codigo.upper()} necesita el fondo aprendido: se aprende tras las instrucciones "
                      "(o con F en inicio).", ahora)
    elif entrada.codigo != "Esc":
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


class BotonTeclas:
    """Botón «Teclas (H)» abajo a la derecha de la ventana principal; abre la ventana de teclas."""
    ANCHO, ALTO, MARGEN = 150, 40, 12

    def __init__(self):
        self.rect = None
        self._sobre = False
        self._clic = False
        self._visible = False
        self._capas = {}

    def _capa(self, sobre):
        if sobre not in self._capas:
            img = Image.new("RGBA", (self.ANCHO, self.ALTO), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            fondo = (18, 38, 63, 240) if sobre else (31, 138, 138, 235)
            d.rounded_rectangle((0, 0, self.ANCHO - 1, self.ALTO - 1), radius=12, fill=fondo,
                                outline=(255, 255, 255, 255), width=2)
            d.text((self.ANCHO // 2, self.ALTO // 2 - 1), "Teclas (H)", font=_fuente(21, True),
                   fill=(255, 255, 255, 255), anchor="mm")
            rgba = np.asarray(img)
            self._capas[sobre] = (rgba[..., 2::-1].astype(np.float32), (rgba[..., 3:4] / 255.0).astype(np.float32))
        return self._capas[sobre]

    def dibujar(self, frame, visible):
        alto_f, ancho_f = frame.shape[:2]
        x0, y0 = ancho_f - self.ANCHO - self.MARGEN, alto_f - self.ALTO - self.MARGEN
        self.rect = (x0, y0, x0 + self.ANCHO, y0 + self.ALTO)
        self._visible = visible
        if not visible:
            self._sobre = False
            return
        if x0 < 0 or y0 < 0:
            return
        bgr, alfa = self._capa(self._sobre)
        roi = frame[y0:y0 + self.ALTO, x0:x0 + self.ANCHO].astype(np.float32)
        frame[y0:y0 + self.ALTO, x0:x0 + self.ANCHO] = (roi * (1 - alfa) + bgr * alfa).astype(np.uint8)

    def raton(self, evento, x, y, flags, parametro):
        if not self._visible or self.rect is None:
            return
        x0, y0, x1, y1 = self.rect
        self._sobre = x0 <= x <= x1 and y0 <= y <= y1
        if evento == cv2.EVENT_LBUTTONDOWN and self._sobre:
            self._clic = True

    def pulsado(self):
        """True una sola vez por clic."""
        clic, self._clic = self._clic, False
        return clic
