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

    # Congelar exposición y balance de blancos en el valor ya estabilizado:
    # si la cámara los reajusta al entrar una persona, cambia toda la imagen
    # y el modelo de fondo deja de valer
    exposicion = cap.get(cv2.CAP_PROP_EXPOSURE)
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)   # 0.25 = manual en DirectShow
    cap.set(cv2.CAP_PROP_EXPOSURE, exposicion)
    temperatura = cap.get(cv2.CAP_PROP_WB_TEMPERATURE)
    cap.set(cv2.CAP_PROP_AUTO_WB, 0)
    cap.set(cv2.CAP_PROP_WB_TEMPERATURE, temperatura)
    print(f"Exposición fijada en {exposicion}, balance de blancos en {temperatura}")

    real = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    if real != (ancho, alto):
        print(f"Aviso: la cámara da {real}, no {(ancho, alto)}. La calibración no sería válida.")
    return cap