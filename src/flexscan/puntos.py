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


class DetectorPose:
    def __init__(self):
        opciones = vision.PoseLandmarkerOptions(
            base_options=tareas.BaseOptions(model_asset_path=str(RUTA_MODELO)),
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


def dibujar_puntos(frame, puntos):
    """Dibuja cada punto con su nombre y visibilidad (solo para depurar)."""
    for nombre, (x, y, visibilidad) in puntos.items():
        color = (0, 255, 0) if visibilidad >= VISIBILIDAD_MIN else (0, 165, 255)
        cv2.circle(frame, (int(x), int(y)), 7, color, -1)
        cv2.putText(frame, f"{nombre} {visibilidad:.2f}", (int(x) + 8, int(y)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)