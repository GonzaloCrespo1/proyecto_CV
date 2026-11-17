"""Calibración de la escala sobre una foto ya hecha, con cuatro clics en los bordes de la hoja A4.

La usan el programa principal (tecla k) y el script python -m flexscan.calibrar_escala.
"""
import cv2
import numpy as np

from flexscan.escala import RUTA_FOTO, escala_desde_hoja, guardar_escala

BORDES = ["IZQUIERDO", "DERECHO", "SUPERIOR", "INFERIOR"]
AMARILLO, ROJO, VERDE = (0, 255, 255), (0, 0, 255), (0, 255, 0)
DISCREPANCIA_MAX = 0.08    # diferencia relativa entre la escala del ancho y la del alto


def texto(img, s, y, color=ROJO, tam=0.9):
    cv2.putText(img, s, (10, y), cv2.FONT_HERSHEY_SIMPLEX, tam, (0, 0, 0), 5)
    cv2.putText(img, s, (10, y), cv2.FONT_HERSHEY_SIMPLEX, tam, color, 2)


def _centrado(img, s, y, color, tam, grosor, x0, ancho):
    """Escribe s centrado horizontalmente en el tramo [x0, x0 + ancho)."""
    (w, _), _ = cv2.getTextSize(s, cv2.FONT_HERSHEY_SIMPLEX, tam, grosor)
    cv2.putText(img, s, (x0 + (ancho - w) // 2, y), cv2.FONT_HERSHEY_SIMPLEX, tam, color, grosor,
                cv2.LINE_AA)


def dibujar_aviso_calibracion(frame):
    """Oscurece la imagen y muestra un panel central: sin calibración no funciona nada más."""
    alto, ancho = frame.shape[:2]
    k = ancho / 1280                                   # los tamaños se escalan con la imagen
    frame[:] = (frame * 0.45).astype(frame.dtype)
    w, h = int(ancho * 0.66), int(250 * k)
    x0, y0 = (ancho - w) // 2, (alto - h) // 2
    cv2.rectangle(frame, (x0, y0), (x0 + w, y0 + h), (30, 30, 30), -1)
    cv2.rectangle(frame, (x0, y0), (x0 + w, y0 + h), ROJO, 3)
    cv2.rectangle(frame, (x0, y0), (x0 + w, y0 + int(62 * k)), ROJO, -1)
    blanco = (255, 255, 255)
    _centrado(frame, "CALIBRACION DE DISTANCIA: PENDIENTE", y0 + int(42 * k), blanco, 0.95 * k, 2, x0, w)
    _centrado(frame, "Hasta calibrar no funciona nada mas", y0 + int(115 * k), AMARILLO, 0.85 * k, 2, x0, w)
    _centrado(frame, "(ni registro, ni entrada, ni medida)", y0 + int(150 * k), blanco, 0.65 * k, 1, x0, w)
    _centrado(frame, "Coloca la hoja A4 en el sitio del ejercicio y pulsa K", y0 + int(210 * k), VERDE,
              0.7 * k, 2, x0, w)


def pedir_bordes(foto, ventana):
    """Cuatro clics (izquierdo, derecho, superior, inferior). Devuelve los puntos o None si se cancela."""
    puntos = []

    def raton(evento, x, y, flags, param):
        if evento == cv2.EVENT_LBUTTONDOWN and len(puntos) < 4:
            puntos.append((x, y))

    cv2.setMouseCallback(ventana, raton)
    while len(puntos) < 4:
        img = foto.copy()
        for i, (x, y) in enumerate(puntos):
            if i < 2:
                cv2.line(img, (x, 0), (x, img.shape[0]), AMARILLO, 1)
            else:
                cv2.line(img, (0, y), (img.shape[1], y), AMARILLO, 1)
        texto(img, f"Clic en el borde {BORDES[len(puntos)]} de la hoja ({len(puntos) + 1}/4)", 40)
        texto(img, "q o Esc: cancelar", 80, AMARILLO, 0.7)
        cv2.imshow(ventana, img)
        if cv2.waitKey(30) & 0xFF in (ord("q"), 27):
            cv2.setMouseCallback(ventana, lambda *args: None)
            return None
    cv2.setMouseCallback(ventana, lambda *args: None)
    return puntos


def calibrar_sobre_foto(foto, ventana, espera_ms=0):
    """Pide los cuatro bordes sobre la foto, guarda la escala (sobrescribe) y la devuelve en px/cm.

    Devuelve None si se cancela. espera_ms es lo que se muestra el resultado (0 = hasta pulsar
    una tecla); si ancho y alto no cuadran se espera siempre una tecla para ver el aviso.
    """
    puntos = pedir_bordes(foto, ventana)
    if puntos is None:
        return None
    ancho = abs(puntos[1][0] - puntos[0][0])
    alto = abs(puntos[3][1] - puntos[2][1])
    escala, discrepancia = escala_desde_hoja(ancho, alto)
    guardar_escala(escala, ancho, alto)
    cv2.imwrite(str(RUTA_FOTO), foto)
    img = foto.copy()
    cv2.rectangle(img, (puntos[0][0], puntos[2][1]), (puntos[1][0], puntos[3][1]), VERDE, 2)
    texto(img, f"Escala: {escala:.2f} px/cm  (hoja {ancho} x {alto} px)", 40, VERDE)
    mala = discrepancia > DISCREPANCIA_MAX
    if mala:
        texto(img, "AVISO: ancho y alto no cuadran, repite con la hoja de frente", 80)
        texto(img, "Pulsa una tecla para seguir", 120, AMARILLO, 0.7)
    print(f"Escala guardada: {escala:.2f} px/cm (discrepancia ancho/alto: {discrepancia:.1%})")
    cv2.imshow(ventana, img)
    cv2.waitKey(0 if mala else espera_ms)
    return escala
