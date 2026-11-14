"""Rasgos geométricos del símbolo, medidos sobre la tarjeta enderezada."""
from dataclasses import dataclass

import cv2
import numpy as np

from flexscan.preprocesado import preprocesar

MARGEN = 25            # px del borde que se ignoran (el marco de la tarjeta)
AREA_MIN_FORMA = 150   # área mínima de una mancha o hueco (descarta ruido)
TOL_POLIGONO = 0.03    # tolerancia de approxPolyDP (fracción del perímetro)
BANDA = 44             # alto de la banda de texto bajo la tarjeta


@dataclass
class Rasgos:
    n_manchas: int       # regiones de tinta (sin contar el marco)
    n_huecos: int        # huecos dentro de esas regiones
    vertices: tuple      # vértices de cada hueco
    circularidad: tuple  # circularidad de cada hueco (1 = círculo)


def circularidad(contorno):
    """4·pi·área / perímetro²: 1 para un círculo, menos para otras formas."""
    area = cv2.contourArea(contorno)
    perimetro = cv2.arcLength(contorno, True)
    return 4 * np.pi * area / perimetro ** 2 if perimetro > 0 else 0.0


def medir_rasgos(tarjeta):
    """Tarjeta BGR enderezada -> (Rasgos, contornos de manchas y huecos)."""
    mascara = preprocesar(tarjeta)[MARGEN:-MARGEN, MARGEN:-MARGEN]
    contornos, jerarquia = cv2.findContours(
        mascara, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    manchas, huecos = [], []
    if jerarquia is not None:
        for c, h in zip(contornos, jerarquia[0]):
            if cv2.contourArea(c) < AREA_MIN_FORMA:
                continue
            (huecos if h[3] != -1 else manchas).append(c)
    vertices = tuple(
        len(cv2.approxPolyDP(c, TOL_POLIGONO * cv2.arcLength(c, True), True))
        for c in huecos)
    circ = tuple(round(circularidad(c), 2) for c in huecos)
    return Rasgos(len(manchas), len(huecos), vertices, circ), (manchas, huecos)


def anotar(imagen, lineas):
    """Añade bajo la imagen una banda blanca con las líneas de texto."""
    imagen = cv2.copyMakeBorder(imagen, 0, BANDA, 0, 0,
                                cv2.BORDER_CONSTANT, value=(255, 255, 255))
    base = imagen.shape[0] - BANDA + 18
    for i, linea in enumerate(lineas):
        cv2.putText(imagen, linea, (8, base + 18 * i),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    return imagen


def dibujar_rasgos(tarjeta, rasgos, formas):
    """Tarjeta con manchas (verde), huecos (rojo) y los rasgos debajo."""
    img = tarjeta.copy()
    manchas, huecos = formas
    cv2.drawContours(img, manchas, -1, (0, 200, 0), 2, offset=(MARGEN, MARGEN))
    cv2.drawContours(img, huecos, -1, (0, 0, 255), 2, offset=(MARGEN, MARGEN))
    return anotar(img, (f"manchas {rasgos.n_manchas}  huecos {rasgos.n_huecos}",
                        f"vertices {rasgos.vertices}"))