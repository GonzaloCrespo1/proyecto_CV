"""Distancia horizontal entre la yema del dedo y el punto del pie (ejercicio 1)."""
import time
from collections import deque
from statistics import median

import cv2

from flexscan.puntos import VISIBILIDAD_MIN, mejor_punto, punta_dedo

N_FOTOGRAMAS = 15          # mediana de los últimos fotogramas (≈1 s a 17 FPS)

# Condición de validez de la medida (valores iniciales, ajustados con las series del Paso 5)
VENTANA_S = 2.0            # duración de la ventana de estabilidad (s)
VARIACION_BASE_CM = 4.0    # variación máxima de la ventana para fijar la línea base (cm)
VARIACION_MAX_CM = 6.0     # variación máxima de una ventana candidata (cm)
SUBIDA_MIN_CM = 10.0       # subida mínima sobre la línea base para ser candidata (cm)
FIN_SIN_MEJORA_S = 5.0     # la medida termina si la mejor candidata no mejora en este tiempo (s)
LIMITE_S = 60.0            # tiempo máximo del intento desde que hay línea base (s)

ESPERANDO_BASE, MIDIENDO, TERMINADA, FALLIDA = "esperando_base", "midiendo", "terminada", "fallida"


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


class MedidaValida:
    """Decide cuándo la distancia dedo-pie es una medida válida (máxima flexión mantenida).

    Tres estados: espera la línea base (persona quieta y distancia estable), mide (busca
    ventanas estables y suficientemente por encima de la base, y se queda con la mayor)
    y termina cuando la mejor no mejora en FIN_SIN_MEJORA_S o se agota LIMITE_S.
    """

    def __init__(self):
        self.reiniciar()

    def reiniciar(self):
        self.estado = ESPERANDO_BASE
        self.ventana = deque()          # pares (instante, distancia en cm)
        self.base = None                # línea base (cm)
        self.mejor = None               # mayor candidata hasta ahora (cm)
        self.t_inicio = self.t_mejor = None
        self.historial = []             # pares (segundos desde la primera muestra, distancia en cm)
        self.t0 = self.t_fin = None     # instante de la primera muestra y del fin de la medida
        self.ventana_mejor = None       # (inicio, fin) en segundos de la ventana de la mejor candidata

    def _ventana_llena(self, ahora):
        """Mediana y variación de la ventana de VENTANA_S segundos, o None si aún no está llena."""
        while self.ventana and ahora - self.ventana[0][0] > VENTANA_S:
            self.ventana.popleft()
        if len(self.ventana) < 2 or ahora - self.ventana[0][0] < 0.9 * VENTANA_S:
            return None
        valores = [d for _, d in self.ventana]
        return median(valores), max(valores) - min(valores)

    def actualizar(self, distancia_px, px_por_cm, quieta, colocado, ahora=None):
        """Procesa un fotograma. distancia_px es la mediana de DistanciaDedoPie (o None)."""
        ahora = time.monotonic() if ahora is None else ahora
        if self.estado in (TERMINADA, FALLIDA):
            return self.estado                      # la medida se queda hasta reiniciar()
        if not colocado or distancia_px is None or not px_por_cm:
            self.ventana.clear()
            if not colocado:
                self.reiniciar()
            return self.estado
        self.ventana.append((ahora, distancia_px / px_por_cm))
        if self.t0 is None:
            self.t0 = ahora
        self.historial.append((ahora - self.t0, distancia_px / px_por_cm))
        datos = self._ventana_llena(ahora)
        if datos is None:
            return self.estado
        mediana, variacion = datos
        if self.estado == ESPERANDO_BASE:
            if quieta and variacion <= VARIACION_BASE_CM:
                self.base, self.estado, self.t_inicio = mediana, MIDIENDO, ahora
            return self.estado
        # MIDIENDO
        if self.mejor is None and quieta and variacion <= VARIACION_BASE_CM \
                and mediana < self.base + SUBIDA_MIN_CM:
            self.base = mediana                     # falsa salida: se reescribe la línea base
        if variacion <= VARIACION_MAX_CM and mediana - self.base >= SUBIDA_MIN_CM \
                and (self.mejor is None or mediana > self.mejor):
            self.mejor, self.t_mejor = mediana, ahora
            self.ventana_mejor = (self.ventana[0][0] - self.t0, ahora - self.t0)
        if self.mejor is not None and (ahora - self.t_mejor >= FIN_SIN_MEJORA_S
                                       or ahora - self.t_inicio >= LIMITE_S):
            self.estado = TERMINADA
            self.t_fin = ahora - self.t0
        elif self.mejor is None and ahora - self.t_inicio >= LIMITE_S:
            self.estado = FALLIDA
            self.t_fin = ahora - self.t0
        return self.estado


def dibujar_estado(frame, validador, px_por_cm=None):
    """Escribe en pantalla qué debe hacer la persona y, al terminar, la medida."""
    if not px_por_cm:
        texto, color = "Falta calibrar la escala (calibrar_escala)", (0, 0, 255)
    elif validador.estado == ESPERANDO_BASE:
        texto, color = "Manos en las rodillas y quieto", (0, 165, 255)
    elif validador.estado == MIDIENDO:
        texto = "Inclinate hacia delante" if validador.mejor is None \
            else f"Manten la postura (mejor: {validador.mejor:+.0f} cm)"
        color = (0, 255, 255)
    elif validador.estado == TERMINADA:
        texto, color = f"MEDIDA: {validador.mejor:+.0f} cm   (n: nueva medida)", (0, 255, 0)
    else:
        texto, color = "Sin medida valida (n: repetir)", (0, 0, 255)
    cv2.putText(frame, texto, (10, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)


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
