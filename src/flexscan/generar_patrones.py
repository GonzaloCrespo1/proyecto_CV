"""Generación de los cuatro símbolos de acceso (tarjetas para imprimir)."""
from pathlib import Path

import cv2
import numpy as np

LADO = 600
NEGRO, BLANCO = 0, 255
RAIZ = Path(__file__).resolve().parents[2]
CARPETA = RAIZ / "patrones"


def tarjeta():
    """Lienzo blanco con el marco negro que delimita la tarjeta."""
    img = np.full((LADO, LADO), BLANCO, np.uint8)
    cv2.rectangle(img, (30, 30), (LADO - 30, LADO - 30), NEGRO, 24)
    return img

def circulos():
    """Círculos concéntricos: dos anillos y un punto central."""
    img = tarjeta()
    centro = (LADO // 2, LADO // 2)
    for radio in (190, 120):
        cv2.circle(img, centro, radio, NEGRO, 22)
    cv2.circle(img, centro, 45, NEGRO, -1)
    return img

def triangulo():
    """Triángulo hueco."""
    img = tarjeta()
    puntos = np.array([(300, 95), (105, 480), (495, 480)], np.int32)
    cv2.polylines(img, [puntos], True, NEGRO, 24)
    return img


def barras():
    """Tres barras paralelas."""
    img = tarjeta()
    for x in (150, 270, 390):
        cv2.rectangle(img, (x, 130), (x + 60, 470), NEGRO, -1)
    return img


def hexagono():
    """Hexágono hueco con un punto en el centro."""
    img = tarjeta()
    centro = LADO // 2
    angulos = np.deg2rad(np.arange(0, 360, 60))
    puntos = np.stack([centro + 190 * np.cos(angulos),
                       centro + 190 * np.sin(angulos)], axis=1).astype(np.int32)
    cv2.polylines(img, [puntos], True, NEGRO, 22)
    cv2.circle(img, (centro, centro), 35, NEGRO, -1)
    return img


SIMBOLOS = {"circulos": circulos, "triangulo": triangulo,
            "barras": barras, "hexagono": hexagono}


def main():
    CARPETA.mkdir(exist_ok=True)
    for nombre, dibujar in SIMBOLOS.items():
        ok, datos = cv2.imencode(".png", dibujar())
        (CARPETA / f"{nombre}.png").write_bytes(datos.tobytes())
        print(f"Guardado patrones/{nombre}.png")


if __name__ == "__main__":
    main()