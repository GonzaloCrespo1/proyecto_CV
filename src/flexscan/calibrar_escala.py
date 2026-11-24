"""Calibración de la escala con una hoja A4:  python -m flexscan.calibrar_escala

1. Se coloca la hoja A4 en vertical, de cara a la cámara, en el sitio donde se sienta la persona.
2. Se abre la cámara con una cuadrícula para comprobar que está recta. ESPACIO inicia una
   cuenta atrás de 10 s para apartarse; al llegar a 0 se hace la foto.
3. Se hacen cuatro clics sobre la foto: borde izquierdo, derecho, superior e inferior de la hoja.
4. Se guarda la escala (píxeles por centímetro) en datos/escala.json.

Los cuatro clics y el guardado están en flexscan/escala_en_vivo.py, que también usa el programa
principal (tecla k).
"""
import time

import cv2

from flexscan.calibracion import Corrector, RUTA_CALIBRACION
from flexscan.camara import abrir_camara
from flexscan.escala_en_vivo import AMARILLO, calibrar_sobre_foto, texto

CUENTA_ATRAS = 10
VENTANA = "Calibracion de la escala"


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


def main():
    foto = hacer_foto()
    if foto is None:
        return
    calibrar_sobre_foto(foto, VENTANA)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
