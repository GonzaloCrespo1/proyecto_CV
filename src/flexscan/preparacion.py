"""Preparación tras aceptar las instrucciones: cuenta atrás en rojo, aprendizaje del fondo y aviso en verde."""
import math

import cv2
import numpy as np
from PIL import Image, ImageDraw

from flexscan.instrucciones import _fuente

CUENTA_S = 5.0         # segundos para apartarse del encuadre
AVISO_S = 3.0          # segundos que se muestra el aviso en verde

# Fases
CUENTA, APRENDIENDO, LISTO = "cuenta", "aprendiendo", "listo"

# Colores (RGB para Pillow; se pasan a BGR para OpenCV)
NAVY = (18, 38, 63)
BLANCO, GRIS_CLARO = (255, 255, 255), (214, 222, 232)
ROJO, ROJO_CLARO = (214, 48, 48), (255, 120, 110)
VERDE, VERDE_CLARO = (30, 190, 80), (130, 235, 150)


def _bgr(rgb):
    return (rgb[2], rgb[1], rgb[0])


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


def _panel(esc, titulo, texto, numero, acento, acento_claro):
    """Panel central (BGR y opacidad) con el aro, el título y el texto. El aro se completa al dibujar."""
    pw, ph = int(800 * esc), int(330 * esc)
    im = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, pw - 1, ph - 1), int(26 * esc), fill=NAVY + (238,), outline=acento + (255,),
                        width=max(2, int(5 * esc)))
    cx, cy, r = int(175 * esc), int(ph * 0.5), int(105 * esc)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 255, 255, 60), width=int(14 * esc))
    if numero is not None:
        d.text((cx, cy - int(6 * esc)), str(numero), font=_fuente(int(150 * esc), True), fill=BLANCO + (255,), anchor="mm")
    x = int(335 * esc)
    d.text((x, int(70 * esc)), titulo, font=_fuente(int(44 * esc), True), fill=acento_claro + (255,))
    fuente = _fuente(int(27 * esc))
    for i, linea in enumerate(_lineas(d, texto, fuente, pw - x - int(30 * esc))):
        d.text((x, int(135 * esc) + i * int(36 * esc)), linea, font=fuente, fill=GRIS_CLARO + (255,))
    a = np.array(im)
    alfa = a[:, :, 3:4].astype(np.float32) / 255.0
    bgr = cv2.cvtColor(a[:, :, :3], cv2.COLOR_RGB2BGR).astype(np.float32)
    premultiplicado = (bgr * alfa).round().astype(np.uint8)            # lo que aporta el panel
    transparencia = np.repeat(((1 - alfa) * 255).round().astype(np.uint8), 3, axis=2)   # lo que deja pasar del vídeo
    return premultiplicado, transparencia, (cx, cy, r)


class Preparacion:
    """Máquina de estados: cuenta atrás → aprender el fondo → aviso de «fondo aprendido»."""

    def __init__(self, fondo):
        self.fondo = fondo
        self.fase = None
        self.t0 = 0.0
        self.t_fin = 0.0
        self._cache = {}

    @property
    def activa(self):
        return self.fase is not None

    def empezar(self, ahora):
        self.fase, self.t0 = CUENTA, ahora

    def cancelar(self):
        self.fase = None

    def actualizar(self, ahora):
        """Avanza de fase. Se llama una vez por fotograma."""
        if self.fase == CUENTA and ahora - self.t0 >= CUENTA_S:
            self.fondo.aprender()
            self.fase = APRENDIENDO
        elif self.fase == APRENDIENDO and not self.fondo.aprendiendo:
            self.fase, self.t_fin = LISTO, ahora
        elif self.fase == LISTO and ahora - self.t_fin >= AVISO_S:
            self.fase = None

    # ------------------------------------------------------------------ dibujo
    def _capas(self, forma):
        """Paneles ya renderizados para este tamaño de imagen (se crean una vez)."""
        if forma not in self._cache:
            esc = forma[1] / 1280
            c = {}
            for n in range(int(CUENTA_S), 0, -1):
                c[(CUENTA, n)] = _panel(esc, "SAL DE LA IMAGEN",
                                        "Apártate del encuadre: el programa va a aprender el fondo vacío.",
                                        n, ROJO, ROJO_CLARO)
            c[APRENDIENDO] = _panel(esc, "APRENDIENDO FONDO",
                                    "No entres en la imagen hasta que termine.", None, ROJO, ROJO_CLARO)
            c[LISTO] = _panel(esc, "FONDO APRENDIDO",
                              "Ya puedes colocarte en tu sitio, con las manos sobre las rodillas.", None, VERDE, VERDE_CLARO)
            solidos = {k: np.full(forma, _bgr(v), np.uint8) for k, v in (("rojo", ROJO), ("verde", VERDE))}
            self._cache[forma] = (c, solidos)
        return self._cache[forma]

    def dibujar(self, frame, ahora):
        """Dibuja la pantalla de preparación sobre el fotograma. Modifica frame."""
        if self.fase is None:
            return
        alto, ancho = frame.shape[:2]
        capas, solidos = self._capas(frame.shape)
        esc = ancho / 1280
        rojo = self.fase != LISTO
        solido = solidos["rojo" if rojo else "verde"]
        # tinte de toda la pantalla y borde que late (en cuatro tiras, sin copiar el fotograma)
        peso = 0.32 if rojo else 0.24
        cv2.addWeighted(frame, 1 - peso, solido, peso, 0, frame)
        pulso = 0.5 + 0.5 * math.sin(2 * math.pi * 1.2 * ahora)
        g = int((12 + 14 * pulso) * esc) if rojo else int(16 * esc)
        for sl in (np.s_[0:g, :], np.s_[alto - g:alto, :], np.s_[:, 0:g], np.s_[:, ancho - g:ancho]):
            tira = frame[sl]
            cv2.addWeighted(tira, 0.15, solido[sl], 0.85, 0, tira)
        # panel central
        if self.fase == CUENTA:
            restante = max(0.0, CUENTA_S - (ahora - self.t0))
            panel, transp, (cx, cy, r) = capas[(CUENTA, min(int(CUENTA_S), max(1, math.ceil(restante))))]
            fraccion = restante / CUENTA_S
        else:
            panel, transp, (cx, cy, r) = capas[self.fase]
            fraccion = 1.0 - self.fondo.restantes / self.fondo.fotogramas if self.fase == APRENDIENDO else 1.0
        ph, pw = panel.shape[:2]
        x0, y0 = (ancho - pw) // 2, int(alto * 0.5 - ph * 0.55)
        roi = frame[y0:y0 + ph, x0:x0 + pw]
        cv2.add(cv2.multiply(roi, transp, scale=1 / 255), panel, dst=roi)
        # aro de progreso y, al terminar, el visto
        grosor_aro = max(3, int(14 * esc))
        centro = (x0 + cx, y0 + cy)
        if fraccion > 0:
            cv2.ellipse(frame, centro, (r, r), -90, 0, 360 * fraccion, _bgr(BLANCO if rojo else VERDE_CLARO),
                        grosor_aro, cv2.LINE_AA)
        if self.fase == LISTO:
            pts = np.array([(centro[0] - 0.45 * r, centro[1] + 0.02 * r), (centro[0] - 0.12 * r, centro[1] + 0.38 * r),
                            (centro[0] + 0.50 * r, centro[1] - 0.32 * r)], np.int32)
            cv2.polylines(frame, [pts], False, _bgr(BLANCO), max(6, int(16 * esc)), cv2.LINE_AA)
