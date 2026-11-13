"""Carga de la calibración y corrección de la distorsión de la lente."""
from pathlib import Path

import cv2
import numpy as np

# Raíz del repositorio: este fichero está en <raíz>/src/flexscan/
RAIZ = Path(__file__).resolve().parents[2]
RUTA_CALIBRACION = (RAIZ / "C1-C2 - Calibración + propuestas y flujo"
                    / "resultados_calibracion" / "calibracion.npz")


class Corrector:
    """Corrige la distorsión con los parámetros guardados en calibracion.npz."""

    def __init__(self, ruta):
        datos = np.load(ruta)
        K = datos["K"]
        D = datos["D"]
        ancho, alto = (int(v) for v in datos["tamano_imagen"])

        # Se calculan UNA vez los mapas: para cada píxel, de dónde copiar el color
        K_nueva, _ = cv2.getOptimalNewCameraMatrix(K, D, (ancho, alto), 0)
        self.mapa_x, self.mapa_y = cv2.initUndistortRectifyMap(
            K, D, None, K_nueva, (ancho, alto), cv2.CV_16SC2)

    def corregir(self, frame):
        """Devuelve el fotograma sin distorsión (se llama en cada fotograma)."""
        return cv2.remap(frame, self.mapa_x, self.mapa_y, cv2.INTER_LINEAR)