"""Pantalla que ve la persona durante la medida: qué hacer en cada momento y, al terminar, el resultado.

Situaciones: colocarse, quedarse quieto, fijar la posición de partida, comenzar el estiramiento (con el
pitido agudo), extenderse, mantener la postura y, al terminar (pitido grave), la medida realizada o el
aviso de que no se ha podido medir. Usa el mismo estilo que la preparación del fondo.
"""
import math

import cv2
import numpy as np
from PIL import Image, ImageDraw

from flexscan.instrucciones import _fuente
from flexscan.medida import ESPERANDO_BASE, FALLIDA, TERMINADA

# Situaciones
COLOCARSE, QUIETO, BASE, COMENZAR, EXTENDER, MANTENER = "colocarse", "quieto", "base", "comenzar", "extender", "mantener"
RESULTADO, SIN_MEDIDA = "resultado", "sin_medida"

NAVY = (18, 38, 63)
BLANCO, GRIS_CLARO = (255, 255, 255), (214, 222, 232)
ROJO, ROJO_CLARO = (214, 48, 48), (255, 120, 110)
AMBAR, AMBAR_CLARO = (235, 160, 30), (255, 214, 120)
VERDE, VERDE_CLARO = (30, 190, 80), (130, 235, 150)
TURQUESA, TURQUESA_CLARO = (31, 138, 138), (120, 225, 225)
NARANJA, NARANJA_CLARO = (232, 131, 58), (255, 190, 140)


def _bgr(rgb):
    return (rgb[2], rgb[1], rgb[0])


def texto_cm(valor):
    """Centímetros con un decimal, signo y coma decimal: −4,7"""
    return f"{valor:+.1f}".replace("-", "−").replace(".", ",")


def situacion(colocado, quieta, validador):
    """Qué debe ver la persona según el estado de la colocación y de la medida."""
    if validador.estado == TERMINADA:
        return RESULTADO
    if validador.estado == FALLIDA:
        return SIN_MEDIDA
    if not colocado:
        return COLOCARSE
    if validador.estado == ESPERANDO_BASE:
        return BASE if quieta else QUIETO
    if validador.mejor is None:
        return COMENZAR if quieta else EXTENDER
    return MANTENER


def _lineas(dib, texto, fuente, ancho):
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = (actual + " " + palabra).strip()
        if dib.textlength(prueba, font=fuente) <= ancho:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    lineas.append(actual)
    return lineas


def _capas(im):
    """Imagen RGBA -> (lo que aporta el panel, lo que deja pasar del vídeo), para mezclar sin copiar el fotograma."""
    a = np.array(im)
    alfa = a[:, :, 3:4].astype(np.float32) / 255.0
    bgr = cv2.cvtColor(a[:, :, :3], cv2.COLOR_RGB2BGR).astype(np.float32)
    premultiplicado = (bgr * alfa).round().astype(np.uint8)
    transparencia = np.repeat(((1 - alfa) * 255).round().astype(np.uint8), 3, axis=2)
    return premultiplicado, transparencia


def _panel_guia(esc, titulo, texto, acento, acento_claro):
    """Panel de guía, arriba y centrado: franja de color, título y una o dos líneas de texto."""
    pw, ph = int(960 * esc), int(168 * esc)
    im = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, pw - 1, ph - 1), int(24 * esc), fill=NAVY + (238,), outline=acento + (255,),
                        width=max(2, int(5 * esc)))
    d.rounded_rectangle((int(22 * esc), int(24 * esc), int(38 * esc), ph - int(24 * esc)), int(8 * esc),
                        fill=acento + (255,))
    x = int(62 * esc)
    d.text((x, int(20 * esc)), titulo, font=_fuente(int(54 * esc), True), fill=acento_claro + (255,))
    fuente = _fuente(int(31 * esc))
    for i, linea in enumerate(_lineas(d, texto, fuente, pw - x - int(28 * esc))[:2]):
        d.text((x, int(92 * esc) + i * int(36 * esc)), linea, font=fuente, fill=GRIS_CLARO + (255,))
    return _capas(im)


def _panel_final(esc, ok, valor=None):
    """Panel central del resultado: visto o cruz, título, valor en cm, explicación y teclas."""
    pw, ph = int(960 * esc), int(430 * esc)
    acento, claro = (VERDE, VERDE_CLARO) if ok else (ROJO, ROJO_CLARO)
    im = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, pw - 1, ph - 1), int(28 * esc), fill=NAVY + (240,), outline=acento + (255,),
                        width=max(2, int(6 * esc)))
    cx, cy, r = int(180 * esc), int(190 * esc), int(105 * esc)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=acento + (255,), width=int(14 * esc))
    ancho_trazo = max(6, int(18 * esc))
    if ok:
        puntos = [(cx - 0.45 * r, cy + 0.02 * r), (cx - 0.12 * r, cy + 0.38 * r), (cx + 0.50 * r, cy - 0.32 * r)]
        d.line(puntos, fill=BLANCO + (255,), width=ancho_trazo, joint="curve")
    else:
        d.line([(cx - 0.4 * r, cy - 0.4 * r), (cx + 0.4 * r, cy + 0.4 * r)], fill=BLANCO + (255,), width=ancho_trazo)
        d.line([(cx - 0.4 * r, cy + 0.4 * r), (cx + 0.4 * r, cy - 0.4 * r)], fill=BLANCO + (255,), width=ancho_trazo)
    x = int(340 * esc)
    if ok:
        texto = texto_cm(valor)
        d.text((x, int(34 * esc)), "MEDICIÓN REALIZADA", font=_fuente(int(46 * esc), True), fill=claro + (255,))
        d.text((x, int(92 * esc)), f"{texto} cm", font=_fuente(int(150 * esc), True), fill=BLANCO + (255,))
        explica = ("La yema del dedo supera el punto del pie." if valor >= 0
                   else "La yema del dedo no llega al punto del pie.")
        d.text((x, int(272 * esc)), explica, font=_fuente(int(28 * esc)), fill=GRIS_CLARO + (255,))
    else:
        d.text((x, int(34 * esc)), "NO SE HA PODIDO MEDIR", font=_fuente(int(46 * esc), True), fill=claro + (255,))
        fuente = _fuente(int(30 * esc))
        for i, linea in enumerate(_lineas(d, "No se ha detectado un estiramiento mantenido. "
                                              "Colócate de nuevo e inténtalo otra vez.", fuente, pw - x - int(30 * esc))):
            d.text((x, int(110 * esc) + i * int(40 * esc)), linea, font=fuente, fill=GRIS_CLARO + (255,))
    d.line((int(40 * esc), int(344 * esc), pw - int(40 * esc), int(344 * esc)), fill=(255, 255, 255, 70), width=2)
    pie = "N: nueva medida   ·   S: cerrar sesión   ·   H: ver teclas"
    d.text((pw // 2, int(388 * esc)), pie, font=_fuente(int(26 * esc)), fill=GRIS_CLARO + (255,), anchor="mm")
    return _capas(im)


TEXTOS = {
    COLOCARSE: ("COLÓCATE EN TU SITIO", "Siéntate dentro de la zona marcada, con las piernas estiradas.", ROJO, ROJO_CLARO),
    QUIETO: ("QUÉDATE QUIETO", "Manos sobre las rodillas, sin moverte.", AMBAR, AMBAR_CLARO),
    BASE: ("MANTÉN LA POSICIÓN", "Estamos fijando tu posición de partida. Sigue sin moverte.", AMBAR, AMBAR_CLARO),
    COMENZAR: ("COMENZAR ESTIRAMIENTO", "Ha sonado el pitido: extiende los brazos hacia los pies.",
               AMBAR, AMBAR_CLARO),
    EXTENDER: ("EXTIÉNDETE", "Llega lo más lejos que puedas, con las manos paralelas a las piernas.",
               TURQUESA, TURQUESA_CLARO),
}


AVISO_INICIO_S = 3.0      # el aviso amarillo de comenzar se ve solo unos segundos
AVISO_FINAL_S = 4.0       # la pantalla de resultado se ve solo unos segundos


def _chip(esc, ok, valor):
    """Resumen pequeño que queda arriba tras la pantalla de resultado, sin tapar el cuerpo."""
    pw, ph = int(760 * esc), int(58 * esc)
    acento, claro = (VERDE, VERDE_CLARO) if ok else (ROJO, ROJO_CLARO)
    im = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, pw - 1, ph - 1), int(16 * esc), fill=NAVY + (225,), outline=acento + (255,),
                        width=max(2, int(3 * esc)))
    texto = (f"Última medida: {texto_cm(valor)} cm" if ok else "No se pudo medir")
    d.text((int(24 * esc), ph // 2), texto, font=_fuente(int(27 * esc), True), fill=claro + (255,), anchor="lm")
    d.text((pw - int(22 * esc), ph // 2), "N: nueva · S: cerrar · H: teclas", font=_fuente(int(22 * esc)),
           fill=GRIS_CLARO + (255,), anchor="rm")
    return _capas(im)


class PantallaMedida:
    def __init__(self):
        self._cache = {}
        self._t_inicio = None      # instante en que se fijó la posición de partida (pitido agudo)
        self._t_final = None       # instante en que apareció el resultado (pitido grave)
        self._base_vista = False

    def _panel(self, forma, clave, crear):
        k = (forma, clave)
        if k not in self._cache:
            self._cache[k] = crear(forma[1] / 1280)
        return self._cache[k]

    @staticmethod
    def _mezclar(frame, panel, transp, x0, y0):
        ph, pw = panel.shape[:2]
        roi = frame[y0:y0 + ph, x0:x0 + pw]
        cv2.add(cv2.multiply(roi, transp, scale=1 / 255), panel, dst=roi)

    @staticmethod
    def _tinte_y_borde(frame, color_rgb, peso, grosor, ahora, late):
        alto, ancho = frame.shape[:2]
        solido = np.full(frame.shape, _bgr(color_rgb), np.uint8)
        if peso:
            cv2.addWeighted(frame, 1 - peso, solido, peso, 0, frame)
        pulso = 0.5 + 0.5 * math.sin(2 * math.pi * 1.2 * ahora) if late else 1.0
        g = int(grosor * (0.6 + 0.8 * pulso) * ancho / 1280)
        for sl in (np.s_[0:g, :], np.s_[alto - g:alto, :], np.s_[:, 0:g], np.s_[:, ancho - g:ancho]):
            tira = frame[sl]
            cv2.addWeighted(tira, 0.15, solido[sl], 0.85, 0, tira)

    def dibujar(self, frame, ahora, fase_medida, colocado, quieta, validador):
        """Dibuja los avisos de la medida. Solo ocupan pantalla unos segundos: colocarse (hasta estar en su
        sitio), el aviso amarillo de comenzar y el resultado. El resto del tiempo se ve la imagen con los
        puntos y la depuración que la persona haya activado."""
        if fase_medida not in ("medida", "resultado"):
            return
        alto, ancho = frame.shape[:2]
        sit = situacion(colocado, quieta, validador)
        # Instantes de los dos pitidos, para temporizar los avisos
        if validador.estado == ESPERANDO_BASE:
            self._base_vista, self._t_inicio, self._t_final = True, None, None
        elif sit in (RESULTADO, SIN_MEDIDA):
            if self._t_final is None:
                self._t_final = ahora
        else:
            if self._base_vista and self._t_inicio is None:
                self._t_inicio = ahora
            self._t_final = None
        if sit in (RESULTADO, SIN_MEDIDA):
            ok = sit == RESULTADO
            valor = round(validador.mejor, 1) if ok else None
            if self._t_final is not None and ahora - self._t_final < AVISO_FINAL_S:
                self._tinte_y_borde(frame, VERDE if ok else ROJO, 0.24 if ok else 0.30, 16, ahora, late=False)
                panel, transp = self._panel(frame.shape, (sit, valor), lambda e: _panel_final(e, ok, valor))
                ph, pw = panel.shape[:2]
                self._mezclar(frame, panel, transp, (ancho - pw) // 2, max(0, (alto - ph) // 2))
            else:
                panel, transp = self._panel(frame.shape, ("chip", sit, valor), lambda e: _chip(e, ok, valor))
                ph, pw = panel.shape[:2]
                self._mezclar(frame, panel, transp, (ancho - pw) // 2, 54)
            return
        if sit == COLOCARSE:
            mostrar = COLOCARSE
        elif self._t_inicio is not None and ahora - self._t_inicio < AVISO_INICIO_S:
            mostrar = COMENZAR
        else:
            return                                   # quieto, extendiéndose o manteniendo: imagen limpia
        titulo, texto, acento, claro = TEXTOS[mostrar]
        if mostrar == COMENZAR:
            self._tinte_y_borde(frame, AMBAR, 0.0, 14, ahora, late=True)
        panel, transp = self._panel(frame.shape, mostrar, lambda e: _panel_guia(e, titulo, texto, acento, claro))
        ph, pw = panel.shape[:2]
        self._mezclar(frame, panel, transp, (ancho - pw) // 2, 54)     # por debajo del texto de FPS y del usuario
