"""Gráfica en tiempo real de la ganancia de Kalman (posición y velocidad)."""
from collections import deque

import cv2
import numpy as np

MUESTRAS = 200          # fotogramas que se muestran (unos 10 s a 20 FPS)
ANCHO, ALTO = 480, 300  # tamaño de la ventana (píxeles)
MARGEN = 34             # espacio a la izquierda para los números
FUENTE = cv2.FONT_HERSHEY_SIMPLEX


class GraficaGanancia:
    def __init__(self):
        self.posicion = deque(maxlen=MUESTRAS)
        self.velocidad = deque(maxlen=MUESTRAS)

    def anadir(self, ganancia):
        """Recibe (K posición, K velocidad), o None si no hubo corrección."""
        self.posicion.append(None if ganancia is None else ganancia[0])
        self.velocidad.append(None if ganancia is None else ganancia[1])

    def dibujar(self):
        lienzo = np.full((ALTO, ANCHO, 3), 255, np.uint8)
        self._panel(lienzo, 0, self.posicion, "K posicion", (138, 138, 31))
        self._panel(lienzo, ALTO // 2, self.velocidad, "K velocidad", (58, 131, 232))
        return lienzo

    def _panel(self, lienzo, y0, datos, titulo, color):
        alto = ALTO // 2
        cv2.putText(lienzo, titulo, (8, y0 + 16), FUENTE, 0.5, (0, 0, 0), 1)
        for guia in (0.0, 0.5, 1.0):                        # líneas guía en 0, 0.5 y 1
            y = y0 + alto - 12 - int(guia * (alto - 36))
            cv2.line(lienzo, (MARGEN, y), (ANCHO - 6, y), (225, 225, 225), 1)
            cv2.putText(lienzo, f"{guia:.1f}", (4, y + 4), FUENTE, 0.35, (120, 120, 120), 1)

        tramo = []                                          # tramo continuo de puntos
        for i, k in enumerate(datos):
            if k is None:                                   # sin corrección: se corta la línea
                self._linea(lienzo, tramo, color)
                tramo = []
                continue
            x = MARGEN + int(i * (ANCHO - MARGEN - 6) / MUESTRAS)
            y = y0 + alto - 12 - int(min(k, 1.0) * (alto - 36))
            tramo.append((x, y))
        self._linea(lienzo, tramo, color)

        ultimo = datos[-1] if datos else None
        if ultimo is not None:                              # valor actual
            cv2.putText(lienzo, f"{ultimo:.3f}", (ANCHO - 70, y0 + 16), FUENTE, 0.5, color, 1)

    @staticmethod
    def _linea(lienzo, puntos, color):
        if len(puntos) > 1:
            cv2.polylines(lienzo, [np.array(puntos, np.int32)], False, color, 2)
