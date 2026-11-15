"""Limpieza de la máscara de primer plano: deja solo la silueta de la persona."""
import cv2

LADO = 5   # lado del elemento estructurante (píxeles)

ELEMENTO = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (LADO, LADO))


def limpiar(primer_plano):
    """Recibe la máscara de MOG2 (0, 127, 255) y devuelve una binaria limpia."""
    # Quedarse solo con el primer plano seguro (255) y descartar sombras (127)
    _, binaria = cv2.threshold(primer_plano, 200, 255, cv2.THRESH_BINARY)
    # Apertura: erosión y dilatación, elimina puntos sueltos y líneas finas
    return cv2.morphologyEx(binaria, cv2.MORPH_OPEN, ELEMENTO)