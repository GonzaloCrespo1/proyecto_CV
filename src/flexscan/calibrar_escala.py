"""Calibración de la escala con una hoja A4:  python -m flexscan.calibrar_escala

1. Se coloca la hoja A4 en vertical, de cara a la cámara, en el sitio donde se sienta la persona.
2. Se abre la cámara con una cuadrícula para comprobar que está recta. ESPACIO inicia una
   cuenta atrás de 10 s para apartarse; al llegar a 0 se hace la foto.
3. Se hacen cuatro clics sobre la foto: borde izquierdo, derecho, superior e inferior de la hoja.
4. Se guarda la escala (píxeles por centímetro) en datos/escala.json.
"""
import time

import cv2

from flexscan.calibracion import Corrector, RUTA_CALIBRACION
from flexscan.camara import abrir_camara
from flexscan.escala import RUTA_FOTO, escala_desde_hoja, guardar_escala

CUENTA_ATRAS = 10
BORDES = ["IZQUIERDO", "DERECHO", "SUPERIOR", "INFERIOR"]
VENTANA = "Calibracion de la escala"
AMARILLO, ROJO, VERDE = (0, 255, 255), (0, 0, 255), (0, 255, 0)


def texto(img, s, y, color=ROJO, tam=0.9):
    cv2.putText(img, s, (10, y), cv2.FONT_HERSHEY_SIMPLEX, tam, (0, 0, 0), 5)
    cv2.putText(img, s, (10, y), cv2.FONT_HERSHEY_SIMPLEX, tam, color, 2)


def hacer_foto():
    """Vista previa con cuadrícula y cuenta atrás; devuelve la foto sin dibujos."""
    cap, corrector = abrir_camara(), Corrector(RUTA_CALIBRACION)
    t0 = None
    while True:
        ok, frame = cap.read()
        if not ok:
            raise RuntimeError("No se pudo leer la cámara")
        frame = corrector.corregir(frame)
        limpio = frame.copy()
        alto, ancho = frame.shape[:2]
        for x in range(ancho // 8, ancho, ancho // 8):
            cv2.line(frame, (x, 0), (x, alto), (255, 255, 255), 1)
        for y in range(alto // 6, alto, alto // 6):
            cv2.line(frame, (0, y), (ancho, y), (255, 255, 255), 1)
        cv2.line(frame, (ancho // 2, 0), (ancho // 2, alto), AMARILLO, 2)
        cv2.line(frame, (0, alto // 2), (ancho, alto // 2), AMARILLO, 2)
        if t0 is None:
            texto(frame, "Hoja A4 en vertical. Pulsa ESPACIO para empezar", 40)
        else:
            resto = CUENTA_ATRAS - (time.time() - t0)
            if resto <= 0:
                cap.release()
                return limpio
            texto(frame, f"Apartate. Foto en {resto:.0f} s", 40)
        cv2.imshow(VENTANA, frame)
        tecla = cv2.waitKey(1) & 0xFF
        if tecla == ord("q"):
            cap.release()
            return None
        if tecla == 32 and t0 is None:
            t0 = time.time()


def pedir_bordes(foto):
    """Cuatro clics (izquierdo, derecho, superior, inferior). Devuelve la lista de puntos."""
    puntos = []

    def raton(evento, x, y, flags, param):
        if evento == cv2.EVENT_LBUTTONDOWN and len(puntos) < 4:
            puntos.append((x, y))

    cv2.setMouseCallback(VENTANA, raton)
    while len(puntos) < 4:
        img = foto.copy()
        for i, (x, y) in enumerate(puntos):
            if i < 2:
                cv2.line(img, (x, 0), (x, img.shape[0]), AMARILLO, 1)
            else:
                cv2.line(img, (0, y), (img.shape[1], y), AMARILLO, 1)
        texto(img, f"Clic en el borde {BORDES[len(puntos)]} de la hoja ({len(puntos) + 1}/4)", 40)
        cv2.imshow(VENTANA, img)
        if cv2.waitKey(30) & 0xFF == ord("q"):
            return None
    return puntos


def main():
    foto = hacer_foto()
    if foto is None:
        return
    cv2.imwrite(str(RUTA_FOTO), foto)
    puntos = pedir_bordes(foto)
    if puntos is None:
        return
    ancho = abs(puntos[1][0] - puntos[0][0])
    alto = abs(puntos[3][1] - puntos[2][1])
    escala, discrepancia = escala_desde_hoja(ancho, alto)
    guardar_escala(escala, ancho, alto)
    img = foto.copy()
    cv2.rectangle(img, (puntos[0][0], puntos[2][1]), (puntos[1][0], puntos[3][1]), VERDE, 2)
    texto(img, f"Escala: {escala:.2f} px/cm  (hoja {ancho} x {alto} px)", 40, VERDE)
    if discrepancia > 0.08:
        texto(img, "AVISO: ancho y alto no cuadran, repite con la hoja de frente", 80)
    texto(img, "Pulsa una tecla para cerrar", 120, AMARILLO, 0.7)
    print(f"Escala guardada: {escala:.2f} px/cm (discrepancia ancho/alto: {discrepancia:.1%})")
    cv2.imshow(VENTANA, img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
