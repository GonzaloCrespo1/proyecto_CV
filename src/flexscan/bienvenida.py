"""Ventana de presentación del proyecto: nombre, qué es y cómo funciona, con la figura animada del ejercicio.

Se muestra una sola vez al arrancar, una vez calibrada la escala, y precede a la ventana de teclas.
"""
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw

from flexscan.instrucciones import (AZUL, BLANCO, FASES as FASES_ANIMACION, FONDO, GRIS, GRIS_CLARO,
                                    SUELO, SUELO_PX, TARJETA_FIG, TURQUESA, _fase, _fuente,
                                    _texto_ajustado, dibujar_figura)

VENTANA = "FlexScan"
ANCHO, ALTO = 1280, 720
IDEAS = [
    ("Una sola cámara",
     "Una webcam normal basta: el programa detecta tu cuerpo y calcula en centímetros hasta dónde llegas."),
    ("Entras con un patrón de símbolos",
     "No hay contraseña escrita: muestras a la cámara una secuencia de tarjetas con símbolos que solo tú conoces."),
    ("Ejercicio sit-and-reach",
     "Sentado, extiendes los brazos hacia los pies lo más lejos posible. Un pitido agudo empieza y uno grave termina."),
    ("Comparación con un modelo de ML",
     "Tu resultado se compara con un modelo de aprendizaje automático que clasifica tu nivel de flexibilidad."),
]
COL_X0, COL_X1, IDEA_Y0, IDEA_ALTO, IDEA_SEP = 670, 1250, 106, 112, 14
BOTON = (670, 630, 1250, 696)


def _capa(fase, sobre_boton):
    im = Image.new("RGB", (ANCHO, ALTO), FONDO)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, ANCHO, 92), fill=AZUL)
    d.text((34, 10), "FlexScan", font=_fuente(56, True), fill=BLANCO)
    ancho = d.textlength("FlexScan", font=_fuente(56, True))
    d.text((34 + ancho + 22, 40), "Mide tu flexibilidad con una cámara", font=_fuente(30), fill=(150, 214, 214))
    # tarjeta de la figura
    x0, y0, x1, y1 = TARJETA_FIG
    d.rounded_rectangle((x0, y0, x1, y1), 18, fill=(250, 248, 246), outline=GRIS_CLARO, width=2)
    suelo = Image.new("RGB", (x1 - x0 - 4, y1 - SUELO_PX - 2), SUELO)
    mascara = Image.new("L", suelo.size, 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, -40, suelo.width, suelo.height), 16, fill=255)
    im.paste(suelo, (x0 + 2, SUELO_PX), mascara)
    d.line((x0 + 3, SUELO_PX, x1 - 3, SUELO_PX), fill=GRIS_CLARO, width=2)
    d.text((x0 + 22, y0 + 14), FASES_ANIMACION[fase][3], font=_fuente(25, True), fill=AZUL)
    # las tres ideas
    for i, (titulo, cuerpo) in enumerate(IDEAS):
        ya = IDEA_Y0 + i * (IDEA_ALTO + IDEA_SEP)
        d.rounded_rectangle((COL_X0, ya, COL_X1, ya + IDEA_ALTO), 16, fill=BLANCO, outline=GRIS_CLARO, width=2)
        cx, cy = COL_X0 + 40, ya + 38
        d.ellipse((cx - 24, cy - 24, cx + 24, cy + 24), fill=TURQUESA)
        d.text((cx, cy - 1), str(i + 1), font=_fuente(30, True), fill=BLANCO, anchor="mm")
        d.text((COL_X0 + 82, ya + 12), titulo, font=_fuente(26, True), fill=AZUL)
        fuente = _fuente(19)
        for j, linea in enumerate(_texto_ajustado(d, cuerpo, fuente, COL_X1 - COL_X0 - 108)):
            d.text((COL_X0 + 82, ya + 50 + j * 24), linea, font=fuente, fill=GRIS)
    # pie y botón
    d.text((34, 636), "Mateo Gómez-Acebo · Gonzalo Crespo Comín", font=_fuente(21, True), fill=AZUL)
    d.text((34, 666), "Visión por Ordenador I · 3º IMAT · ICAI", font=_fuente(19), fill=GRIS)
    bx0, by0, bx1, by1 = BOTON
    d.rounded_rectangle((bx0, by0, bx1, by1), 16, fill=AZUL if sobre_boton else TURQUESA)
    d.text(((bx0 + bx1) // 2, (by0 + by1) // 2 - 1), "Continuar", font=_fuente(30, True), fill=BLANCO, anchor="mm")
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


def mostrar_bienvenida(ventana=VENTANA):
    """Muestra la presentación hasta que se pulsa «Continuar» (o Esc / cerrar la ventana)."""
    capas = {(f, h): _capa(f, h) for f in range(len(FASES_ANIMACION)) for h in (False, True)}
    estado = {"sobre": False, "clic": False}

    def raton(evento, x, y, flags, parametro):
        x0, y0, x1, y1 = BOTON
        estado["sobre"] = x0 <= x <= x1 and y0 <= y <= y1
        if evento == cv2.EVENT_LBUTTONDOWN and estado["sobre"]:
            estado["clic"] = True

    cv2.namedWindow(ventana, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(ventana, raton)
    inicio = time.monotonic()
    while True:
        t = time.monotonic() - inicio
        img = capas[(_fase(t), estado["sobre"])].copy()
        dibujar_figura(img, t)
        cv2.imshow(ventana, img)
        tecla = cv2.waitKey(15) & 0xFF
        if estado["clic"] or tecla == 27:
            break
        if cv2.getWindowProperty(ventana, cv2.WND_PROP_VISIBLE) < 1:
            break
    cv2.destroyWindow(ventana)
