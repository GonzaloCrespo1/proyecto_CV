"""Distancia horizontal entre la yema del dedo y el punto del pie (ejercicio 1)."""
from collections import deque
from statistics import median

import cv2

from flexscan.puntos import VISIBILIDAD_MIN, mejor_punto, punta_dedo

N_FOTOGRAMAS = 15          # mediana de los últimos fotogramas (≈1 s a 17 FPS)


class DistanciaDedoPie:
    """Distancia horizontal yema-pie en píxeles, filtrada con la mediana.

    Es positiva si la yema sobrepasa el punto del pie y negativa si no llega.
    """

    def __init__(self, n=N_FOTOGRAMAS):
        self.valores = deque(maxlen=n)

    def actualizar(self, puntos):
        """Añade el fotograma actual; devuelve la mediana o None si aún no hay n válidos."""
        punta = punta_dedo(puntos)
        pie = mejor_punto(puntos, "pie")
        cadera = mejor_punto(puntos, "cadera")
        if punta is None or pie is None or cadera is None or punta[2] < VISIBILIDAD_MIN \
                or pie[2] < VISIBILIDAD_MIN:
            self.valores.clear()
            return None
        sentido = 1 if pie[0] > cadera[0] else -1          # hacia qué lado mira la persona
        self.valores.append(sentido * (punta[0] - pie[0]))
        if len(self.valores) < self.valores.maxlen:
            return None
        return median(self.valores)


def dibujar_distancia(frame, puntos, distancia, px_por_cm=None):
    """Dibuja la vertical del pie, la distancia horizontal hasta la yema y su valor.

    Con la escala (px_por_cm) de la calibración con la hoja A4 el valor sale en centímetros.
    """
    punta = punta_dedo(puntos)
    pie = mejor_punto(puntos, "pie")
    if punta is None or pie is None:
        return
    x_pie, y_punta = int(pie[0]), int(punta[1])
    cv2.line(frame, (x_pie, 0), (x_pie, frame.shape[0]), (0, 165, 255), 2)
    cv2.line(frame, (x_pie, y_punta), (int(punta[0]), y_punta), (0, 255, 255), 2)
    if distancia is None:
        texto = "midiendo..."
    elif px_por_cm:
        texto = f"d = {distancia / px_por_cm:+.0f} cm"       # el error esperado es de 3-4 cm
    else:
        texto = f"d = {distancia:+.0f} px (sin calibrar)"
    cv2.putText(frame, texto, (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
