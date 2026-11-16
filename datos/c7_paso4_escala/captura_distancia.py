"""Toma de medidas de la distancia dedo-pie con la distancia real conocida.

Uso (desde la carpeta src, con el entorno activado):
    python ..\\datos\\c7_paso4_escala\\captura_distancia.py ETIQUETA DISTANCIA_REAL_CM
Ejemplo:
    python ..\\datos\\c7_paso4_escala\\captura_distancia.py d20_descalzo 20

Se abre la cámara y la cuenta atrás de 20 s empieza al pulsar ESPACIO. Después hace
6 capturas (una cada 1,5 s) y guarda las fotos y una fila por captura en
datos/c7_paso4_escala/valores.csv. Con q se sale.
"""
import csv
import math
import os
import sys
import time

import cv2

sys.path.insert(0, os.getcwd())
from flexscan.calibracion import Corrector, RUTA_CALIBRACION
from flexscan.camara import abrir_camara
from flexscan.medida import DistanciaDedoPie, dibujar_distancia
from flexscan.puntos import DetectorPose, dibujar_puntos, mejor_punto, punta_dedo

etiqueta, real_cm = sys.argv[1], float(sys.argv[2])
carpeta = os.path.join(os.getcwd(), "..", "datos", "c7_paso4_escala")
os.makedirs(carpeta, exist_ok=True)
ruta_csv = os.path.join(carpeta, "valores.csv")
if not os.path.exists(ruta_csv):
    with open(ruta_csv, "w", newline="") as f:
        csv.writer(f).writerow(["archivo", "etiqueta", "real_cm", "d_px", "tronco_px", "x_punta", "x_pie"])

cap, corrector = abrir_camara(), Corrector(RUTA_CALIBRACION)
pose, medida = DetectorPose(), DistanciaDedoPie()
t0, n, t_ult = None, 0, 0.0      # t0: instante en que se pulsa ESPACIO

while n < 6:
    ok, frame = cap.read()
    if not ok:
        break
    frame = corrector.corregir(frame)
    puntos = pose.detectar(frame)
    d = medida.actualizar(puntos)
    dibujar_puntos(frame, puntos)
    dibujar_distancia(frame, puntos, d)
    if t0 is None:
        cv2.putText(frame, f"{etiqueta}: pulsa ESPACIO para empezar", (10, 190),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    elif 20 - (time.time() - t0) > 0:
        cv2.putText(frame, f"{etiqueta}: captura en {20 - (time.time() - t0):.0f} s", (10, 190),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    elif time.time() - t_ult >= 1.5:
        n += 1
        t_ult = time.time()
        nombre = f"{etiqueta}_{time.strftime('%H%M%S')}_{n}.jpg"
        cv2.imwrite(os.path.join(carpeta, nombre), frame)
        h, c = mejor_punto(puntos, "hombro"), mejor_punto(puntos, "cadera")
        tronco = math.hypot(h[0] - c[0], h[1] - c[1]) if h and c else ""
        punta, pie = punta_dedo(puntos), mejor_punto(puntos, "pie")
        with open(ruta_csv, "a", newline="") as f:
            csv.writer(f).writerow([nombre, etiqueta, real_cm, "" if d is None else round(d, 1),
                                    tronco if tronco == "" else round(tronco, 1),
                                    "" if punta is None else round(punta[0], 1), "" if pie is None else round(pie[0], 1)])
        print(f"Captura {n}/6 guardada, d = {d}")
    if n >= 6:
        cv2.putText(frame, "TERMINADO", (10, 190), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 4)
    cv2.imshow("Captura", frame)
    tecla = cv2.waitKey(1) & 0xFF
    if tecla == ord("q"):
        break
    if tecla == 32 and t0 is None:       # ESPACIO: empieza la cuenta atrás
        t0 = time.time()

cap.release()
cv2.destroyAllWindows()
print("TERMINADO")
