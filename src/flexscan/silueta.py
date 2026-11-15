"""Limpieza de la máscara de primer plano: deja solo la silueta de la persona."""
import cv2
import numpy as np

LADO = 5            # lado de la apertura (píxeles)
LADO_CIERRE = 9     # lado del cierre (píxeles)
AREA_MINIMA = 3000  # área mínima de la mancha para considerar que hay alguien

ELEMENTO = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (LADO, LADO))
ELEMENTO_CIERRE = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                            (LADO_CIERRE, LADO_CIERRE))


def mayor_componente(binaria):
    """Deja solo la mancha blanca de mayor área (o todo negro si no hay)."""
    n, etiquetas, stats, _ = cv2.connectedComponentsWithStats(binaria)
    if n < 2:                      # solo existe el fondo
        return np.zeros_like(binaria)
    mayor = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])   # la etiqueta 0 es el fondo
    if stats[mayor, cv2.CC_STAT_AREA] < AREA_MINIMA:
        return np.zeros_like(binaria)
    return np.where(etiquetas == mayor, 255, 0).astype(np.uint8)


def limpiar(primer_plano):
    """Recibe la máscara de MOG2 (0, 127, 255) y devuelve solo la persona."""
    # Quedarse solo con el primer plano seguro (255) y descartar sombras (127)
    _, binaria = cv2.threshold(primer_plano, 200, 255, cv2.THRESH_BINARY)
    # Apertura: erosión y dilatación, elimina puntos sueltos y líneas finas
    abierta = cv2.morphologyEx(binaria, cv2.MORPH_OPEN, ELEMENTO)
    # Cierre: dilatación y erosión, rellena huecos y une trozos cercanos
    cerrada = cv2.morphologyEx(abierta, cv2.MORPH_CLOSE, ELEMENTO_CIERRE)
    # Quedarse solo con la mancha más grande: la persona
    return mayor_componente(cerrada)
