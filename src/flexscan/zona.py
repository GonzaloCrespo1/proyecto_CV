"""Caja de colocación: zona donde debe situarse la persona."""
import cv2
import numpy as np

FRACCION_ANCHO = 0.80      # parte del ancho de la imagen que ocupa la caja
FRACCION_ALTO = 0.90       # parte del alto de la imagen que ocupa la caja
GROSOR = 2                 # grosor de la línea punteada (px)
LONG_RAYA = 20             # longitud de cada raya del punteado (px)
HUECO = 12                 # separación entre rayas (px)
FRAMES_CONFIRMACION = 5    # fotogramas seguidos dentro antes de pasar a amarillo
ROJO = (0, 0, 255)         # BGR
AMARILLO = (0, 255, 255)
VERDE = (0, 255, 0)


def caja_colocacion(forma):
    """Rectángulo (x, y, ancho, alto) centrado en la imagen."""
    alto_img, ancho_img = forma[:2]
    ancho = int(ancho_img * FRACCION_ANCHO)
    alto = int(alto_img * FRACCION_ALTO)
    return (ancho_img - ancho) // 2, (alto_img - alto) // 2, ancho, alto


def esta_dentro(punto, caja):
    """True si el punto (u, v) cae dentro de la caja."""
    if punto is None:
        return False
    x, y, ancho, alto = caja
    return x <= punto[0] <= x + ancho and y <= punto[1] <= y + alto


def _linea_punteada(frame, p1, p2, color):
    p1 = np.array(p1, dtype=float)
    p2 = np.array(p2, dtype=float)
    largo = np.linalg.norm(p2 - p1)
    for d in np.arange(0, largo, LONG_RAYA + HUECO):
        a = p1 + (p2 - p1) * d / largo
        b = p1 + (p2 - p1) * min(d + LONG_RAYA, largo) / largo
        cv2.line(frame, tuple(a.astype(int)), tuple(b.astype(int)),
                 color, GROSOR)


def dibujar_caja(frame, caja, color):
    x, y, ancho, alto = caja
    esquinas = [(x, y), (x + ancho, y), (x + ancho, y + alto), (x, y + alto)]
    for i in range(4):
        _linea_punteada(frame, esquinas[i], esquinas[(i + 1) % 4], color)
