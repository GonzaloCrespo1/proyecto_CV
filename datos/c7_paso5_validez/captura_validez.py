"""Captura de series temporales para fijar la condición de validez de la medida (C7, Paso 5).

Uso (desde la carpeta src, con el entorno activado):
    python ..\\datos\\c7_paso5_validez\\captura_validez.py TOMA
Ejemplo:
    python ..\\datos\\c7_paso5_validez\\captura_validez.py toma1

Se abre la cámara y ESPACIO inicia una cuenta atrás de 10 s para colocarse. Después se
siguen cuatro fases guiadas en pantalla (34 s en total):
    1. Sentado recto, manos apoyadas sobre las rodillas, quieto (0-8 s)
    2. Inclinarse despacio hacia delante (8-20 s)
    3. Mantener la máxima flexión        (20-26 s)
    4. Volver recto, manos en las rodillas y quieto (26-34 s)
En cada fotograma se guarda una fila en datos/c7_paso5_validez/serie_TOMA_HHMMSS.csv con la
distancia dedo-pie (instantánea y filtrada) y el ángulo del tronco. Con q se sale.
Hay que haber calibrado antes la escala (python -m flexscan.calibrar_escala).
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
from flexscan.escala import cargar_escala
from flexscan.medida import DistanciaDedoPie, dibujar_distancia
from flexscan.puntos import DetectorPose, VISIBILIDAD_MIN, dibujar_puntos, mejor_punto, punta_dedo

CUENTA_ATRAS = 10
FASES = [(8, "1. Sentado recto, manos sobre las rodillas, quieto"), (20, "2. Inclinate despacio hacia delante"),
         (26, "3. MANTEN la maxima flexion"), (34, "4. Vuelve recto, manos en las rodillas, quieto")]
COLUMNAS = ["t_s", "fase", "d_px_instantanea", "d_px_mediana", "d_cm_mediana", "angulo_tronco_grados",
            "tronco_px", "visibilidad_min"]


def fase_en(t):
    """Número y texto de la fase en el segundo t de la grabación (None si ya terminó)."""
    for i, (fin, texto) in enumerate(FASES, start=1):
        if t < fin:
            return i, texto
    return None


def angulo_tronco(puntos):
    """Ángulo (grados) del segmento cadera-hombro respecto a la vertical, y su longitud en px."""
    h, c = mejor_punto(puntos, "hombro"), mejor_punto(puntos, "cadera")
    if h is None or c is None:
        return None, None
    return math.degrees(math.atan2(abs(h[0] - c[0]), c[1] - h[1])), math.hypot(h[0] - c[0], h[1] - c[1])


def distancia_instantanea(puntos):
    """Misma regla que DistanciaDedoPie, pero sin filtrar: sentido * (x_punta - x_pie)."""
    punta, pie, cadera = punta_dedo(puntos), mejor_punto(puntos, "pie"), mejor_punto(puntos, "cadera")
    if punta is None or pie is None or cadera is None:
        return None
    return (1 if pie[0] > cadera[0] else -1) * (punta[0] - pie[0])


def main():
    toma = sys.argv[1]
    carpeta = os.path.join(os.getcwd(), "..", "datos", "c7_paso5_validez")
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, f"serie_{toma}_{time.strftime('%H%M%S')}.csv")
    px_por_cm = cargar_escala()
    if px_por_cm is None:
        print("AVISO: no hay escala guardada, d_cm_mediana quedará vacío")

    cap, corrector = abrir_camara(), Corrector(RUTA_CALIBRACION)
    pose, medida = DetectorPose(), DistanciaDedoPie()
    t0, terminado = None, False
    with open(ruta, "w", newline="") as f:
        escritor = csv.writer(f)
        escritor.writerow(COLUMNAS)
        while not terminado:
            ok, frame = cap.read()
            if not ok:
                break
            frame = corrector.corregir(frame)
            puntos = pose.detectar(frame)
            mediana = medida.actualizar(puntos)
            dibujar_puntos(frame, puntos)
            dibujar_distancia(frame, puntos, mediana, px_por_cm)
            if t0 is None:
                cv2.putText(frame, f"{toma}: pulsa ESPACIO para empezar", (10, 190),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            elif time.time() - t0 < CUENTA_ATRAS:
                cv2.putText(frame, f"{toma}: empieza en {CUENTA_ATRAS - (time.time() - t0):.0f} s", (10, 190),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            else:
                t = time.time() - t0 - CUENTA_ATRAS
                fase = fase_en(t)
                if fase is None:
                    terminado = True
                    cv2.putText(frame, "TERMINADO", (10, 190), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 4)
                else:
                    cv2.putText(frame, fase[1], (10, 190), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
                    angulo, tronco = angulo_tronco(puntos)
                    vis = min((p[2] for p in puntos.values()), default=0)
                    escritor.writerow([round(t, 2), fase[0], _r(distancia_instantanea(puntos)), _r(mediana),
                                       "" if mediana is None or not px_por_cm else round(mediana / px_por_cm, 1),
                                       _r(angulo), _r(tronco), round(vis, 2)])
            cv2.imshow("Captura", frame)
            tecla = cv2.waitKey(1) & 0xFF
            if tecla == ord("q"):
                break
            if tecla == 32 and t0 is None:      # ESPACIO: empieza la cuenta atrás
                t0 = time.time()
    cap.release()
    cv2.destroyAllWindows()
    print("Guardado en", ruta)


def _r(x):
    return "" if x is None else round(x, 1)


if __name__ == "__main__":
    main()
