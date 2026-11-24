import csv
import time
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as tareas
from mediapipe.tasks.python import vision

K_YEMA = 1.64          # el mismo factor que usa puntos.py
CUENTA = 10.0          # segundos para colocarte
DURACION = 5.0         # segundos grabando
PUNTOS = {"dedo_i": 19, "dedo_d": 20, "mun_i": 15, "mun_d": 16, "pie_i": 31, "pie_d": 32}

opciones = vision.PoseLandmarkerOptions(
    base_options=tareas.BaseOptions(model_asset_path="pose.task"),
    running_mode=vision.RunningMode.VIDEO)
detector = vision.PoseLandmarker.create_from_options(opciones)

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
for _ in range(10):
    cap.read()
t0 = time.time()

estado = "vivo"        # vivo -> cuenta -> grabando -> clics
inicio = 0.0
filas = []             # fotogramas de la toma en curso
clics = []             # [yema real, punta del pie real]
congelado = None
verdad = []            # una fila por toma guardada
import glob
import os
tomas = len(glob.glob("toma_*.csv"))           # sigue desde la última toma guardada
if os.path.exists("verdad.csv"):
    verdad = list(csv.reader(open("verdad.csv")))[1:]   # conserva las filas anteriores


def raton(evento, x, y, flags, param):
    if evento == cv2.EVENT_LBUTTONDOWN and estado == "clics" and len(clics) < 2:
        clics.append((x, y))


cv2.namedWindow("medir")
cv2.setMouseCallback("medir", raton)


def leer():
    ok, frame = cap.read()
    if not ok:
        return None, None
    imagen = mp.Image(image_format=mp.ImageFormat.SRGB,
                      data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    res = detector.detect_for_video(imagen, int((time.time() - t0) * 1000))
    if not res.pose_landmarks:
        return frame, None
    h, w = frame.shape[:2]
    m = res.pose_landmarks[0]
    return frame, {n: (m[j].x * w, m[j].y * h, m[j].visibility) for n, j in PUNTOS.items()}


def dibujar(vista, p):
    lado = "i" if p["dedo_i"][2] >= p["dedo_d"][2] else "d"
    xi, yi, _ = p["dedo_" + lado]
    xm, ym, _ = p["mun_" + lado]
    punta = (int(xi + K_YEMA * (xi - xm)), int(yi + K_YEMA * (yi - ym)))
    cv2.drawMarker(vista, punta, (255, 0, 255), cv2.MARKER_TILTED_CROSS, 25, 3)
    pie = p["pie_i"] if p["pie_i"][2] >= p["pie_d"][2] else p["pie_d"]
    cv2.circle(vista, (int(pie[0]), int(pie[1])), 6, (0, 255, 0), -1)


while True:
    ahora = time.time()
    if estado != "clics":
        frame, p = leer()
        if frame is None:
            break
        vista = frame.copy()
        if p is not None:
            dibujar(vista, p)
        if estado == "vivo":
            cv2.putText(vista, f"tomas: {tomas}   ESPACIO: empezar   q: salir",
                        (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        elif estado == "cuenta":
            resto = CUENTA - (ahora - inicio)
            cv2.putText(vista, f"Colocate y quieto: {resto:0.1f}", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 255), 3)
            if resto <= 0:
                estado, inicio, filas = "grabando", ahora, []
        elif estado == "grabando":
            if p is not None:
                fila = [ahora - inicio]
                for n in PUNTOS:
                    fila += list(p[n])
                filas.append(fila)
            cv2.putText(vista, f"GRABANDO {DURACION - (ahora - inicio):0.1f}", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 255), 3)
            if ahora - inicio >= DURACION:
                congelado, estado, clics = frame.copy(), "clics", []
    else:
        vista = congelado.copy()
        texto = ["Clic 1: yema real del dedo", "Clic 2: punta real del pie"][min(len(clics), 1)]
        if len(clics) == 2:
            texto = "ENTER: guardar | ESC: descartar"
        cv2.putText(vista, texto, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        for k, c in enumerate(clics):
            cv2.drawMarker(vista, c, (0, 165, 255) if k == 0 else (255, 200, 0),
                           cv2.MARKER_TILTED_CROSS, 30, 3)
    cv2.imshow("medir", vista)

    tecla = cv2.waitKey(1) & 0xFF
    if tecla == ord("q"):
        break
    if tecla == 32 and estado == "vivo" and p is not None:
        estado, inicio = "cuenta", time.time()
    if tecla == 27 and estado == "clics":
        estado, clics = "vivo", []
    if tecla == 13 and estado == "clics" and len(clics) == 2 and filas:
        tomas += 1
        cabecera = ["t"] + [f"{n}_{c}" for n in PUNTOS for c in ("x", "y", "vis")]
        with open(f"toma_{tomas}.csv", "w", newline="") as f:
            csv.writer(f).writerows([cabecera] + filas)
        cv2.imwrite(f"toma_{tomas}.png", vista)
        cm = input(f"Toma {tomas} guardada ({len(filas)} fotogramas). "
                   "Distancia real yema-pie en cm (ENTER para omitir): ")
        verdad.append([tomas, clics[0][0], clics[0][1], clics[1][0], clics[1][1], cm])
        with open("verdad.csv", "w", newline="") as f:
            csv.writer(f).writerows([["toma", "yema_x", "yema_y", "pie_x", "pie_y", "cm"]] + verdad)
        estado, clics = "vivo", []

cap.release()
cv2.destroyAllWindows()