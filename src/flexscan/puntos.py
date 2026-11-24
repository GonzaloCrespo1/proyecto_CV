"""Puntos clave del cuerpo con un modelo de pose preentrenado (MediaPipe)."""
import time
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks import python as tareas
from mediapipe.tasks.python import vision

RUTA_MODELO = Path(__file__).resolve().parents[2] / "modelos" / "pose.task"

# Número del punto en el modelo -> nombre (i = izquierda, d = derecha de la persona)
PUNTOS = {11: "hombro_i", 12: "hombro_d", 15: "muneca_i", 16: "muneca_d",
          19: "dedo_i", 20: "dedo_d", 23: "cadera_i", 24: "cadera_d",
          27: "tobillo_i", 28: "tobillo_d", 31: "pie_i", 32: "pie_d"}
VISIBILIDAD_MIN = 0.5      # por debajo, el punto se considera poco fiable
K_YEMA = 1.15              # prolongación muñeca -> nudillo en máxima flexión (ronda 3)


class DetectorPose:
    def __init__(self):
        opciones = vision.PoseLandmarkerOptions(
            # Se pasa el contenido y no la ruta: MediaPipe no abre rutas con caracteres no ASCII
            # en Windows (p. ej. «3º» en el nombre de una carpeta).
            base_options=tareas.BaseOptions(model_asset_buffer=RUTA_MODELO.read_bytes()),
            running_mode=vision.RunningMode.VIDEO)
        self.detector = vision.PoseLandmarker.create_from_options(opciones)
        self.t0 = time.time()

    def detectar(self, frame):
        """Devuelve {nombre: (x, y, visibilidad)} en píxeles, o {} si no hay persona."""
        imagen = mp.Image(image_format=mp.ImageFormat.SRGB,
                          data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        ms = int((time.time() - self.t0) * 1000)
        resultado = self.detector.detect_for_video(imagen, ms)
        if not resultado.pose_landmarks:
            return {}
        alto, ancho = frame.shape[:2]
        marcas = resultado.pose_landmarks[0]
        return {nombre: (marcas[i].x * ancho, marcas[i].y * alto, marcas[i].visibility)
                for i, nombre in PUNTOS.items()}


def mejor_punto(puntos, parte):
    """Punto de la parte ('dedo', 'pie', 'tobillo'...) del lado con mayor visibilidad."""
    izquierdo, derecho = puntos.get(parte + "_i"), puntos.get(parte + "_d")
    if izquierdo is None or derecho is None:
        return None
    return izquierdo if izquierdo[2] >= derecho[2] else derecho


def punta_dedo(puntos):
    """Estima la yema del dedo del lado más visible: (x, y, visibilidad) o None."""
    if not puntos:
        return None
    lado = "i" if puntos["dedo_i"][2] >= puntos["dedo_d"][2] else "d"
    xi, yi, vi = puntos["dedo_" + lado]
    xm, ym, vm = puntos["muneca_" + lado]
    return (xi + K_YEMA * (xi - xm), yi + K_YEMA * (yi - ym), min(vi, vm))


def dibujar_puntos(frame, puntos):
    """Dibuja cada punto con su nombre y visibilidad (solo para depurar)."""
    for nombre, (x, y, visibilidad) in puntos.items():
        color = (0, 255, 0) if visibilidad >= VISIBILIDAD_MIN else (0, 165, 255)
        cv2.circle(frame, (int(x), int(y)), 7, color, -1)
        cv2.putText(frame, f"{nombre} {visibilidad:.2f}", (int(x) + 8, int(y)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    punta = punta_dedo(puntos)
    if punta is not None:
        cv2.drawMarker(frame, (int(punta[0]), int(punta[1])), (255, 0, 255),
                       cv2.MARKER_TILTED_CROSS, 25, 3)