"""Acceso a la webcam."""
import cv2


def abrir_camara(indice=0, ancho=1280, alto=720):
    """Abre la cámara a la resolución indicada y la devuelve.

    La resolución debe coincidir con la de la calibración (1280x720).
    """
    cap = cv2.VideoCapture(indice, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError(f"No se pudo abrir la cámara {indice}")

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, ancho)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, alto)

    # Descartar los primeros fotogramas: la exposición y el balance de blancos
    # automáticos tardan un poco en estabilizarse
    for _ in range(10):
        cap.read()

    real = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    if real != (ancho, alto):
        print(f"Aviso: la cámara da {real}, no {(ancho, alto)}. La calibración no sería válida.")
    return cap