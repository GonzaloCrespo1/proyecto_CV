"""Localiza la tarjeta en la máscara y la endereza a una vista frontal."""
import cv2
import numpy as np

LADO = 300                 # lado (px) de la tarjeta enderezada
AREA_MIN = 2000            # área mínima del marco (descarta motas)
CUADRADO_MIN = 0.7         # relación mínima lado menor / lado mayor
TARJETA_VACIA = np.zeros((LADO, LADO, 3), np.uint8)


def ordenar_esquinas(puntos):
    """Ordena 4 puntos: arriba-izq., arriba-der., abajo-der., abajo-izq."""
    suma = puntos.sum(axis=1)
    resta = puntos[:, 1] - puntos[:, 0]
    return np.array([puntos[np.argmin(suma)], puntos[np.argmin(resta)],
                     puntos[np.argmax(suma)], puntos[np.argmax(resta)]],
                    np.float32)


def buscar_marco(mascara):
    """Devuelve las 4 esquinas del marco de la tarjeta, o None."""
    contornos, _ = cv2.findContours(
        mascara, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    mejor, mejor_area = None, AREA_MIN
    for c in contornos:
        area = cv2.contourArea(c)
        if area < mejor_area:
            continue
        poligono = cv2.approxPolyDP(c, 0.02 * cv2.arcLength(c, True), True)
        if len(poligono) != 4 or not cv2.isContourConvex(poligono):
            continue
        _, (ancho, alto), _ = cv2.minAreaRect(poligono)
        if min(ancho, alto) / max(ancho, alto) < CUADRADO_MIN:
            continue
        mejor, mejor_area = poligono, area
    if mejor is None:
        return None
    return ordenar_esquinas(mejor.reshape(4, 2).astype(np.float32))


def enderezar(frame, esquinas):
    """Vista frontal LADO x LADO de la tarjeta."""
    destino = np.array([[0, 0], [LADO - 1, 0],
                        [LADO - 1, LADO - 1], [0, LADO - 1]], np.float32)
    homografia = cv2.getPerspectiveTransform(esquinas, destino)
    return cv2.warpPerspective(frame, homografia, (LADO, LADO))


def dibujar_marco(frame, esquinas):
    """Dibuja el contorno de la tarjeta detectada sobre el fotograma."""
    cv2.polylines(frame, [esquinas.astype(np.int32)], True, (0, 255, 0), 3)