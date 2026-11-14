"""Preprocesado: separa la tinta del fondo y devuelve una máscara binaria."""
import cv2

BLOQUE = 101       # vecindad del umbral adaptativo (impar)
CONSTANTE = 10     # margen por debajo de la media local
NUCLEO = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))


def preprocesar(frame):
    """Imagen BGR -> máscara 0/255 con la tinta en blanco."""
    gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    suave = cv2.GaussianBlur(gris, (5, 5), 0)
    mascara = cv2.adaptiveThreshold(
        suave, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, BLOQUE, CONSTANTE)
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, NUCLEO)
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, NUCLEO)
    return mascara