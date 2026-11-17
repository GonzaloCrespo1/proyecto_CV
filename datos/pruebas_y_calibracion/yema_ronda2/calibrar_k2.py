import csv
import time
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as tareas
from mediapipe.tasks.python import vision

opciones = vision.PoseLandmarkerOptions(
    base_options=tareas.BaseOptions(model_asset_path="pose.task"),
    running_mode=vision.RunningMode.VIDEO)
detector = vision.PoseLandmarker.create_from_options(opciones)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
t0 = time.time()
filas = []             # una fila por muestra guardada
congelado = None       # (fotograma, puntos) mientras la imagen está parada
clic = None
puntos = None

# (dedo, muñeca, codo, hombro, cadera) de cada lado
LADOS = {"i": (19, 15, 13, 11, 23), "d": (20, 16, 14, 12, 24)}


def raton(evento, x, y, flags, param):
    global clic
    if evento == cv2.EVENT_LBUTTONDOWN and congelado is not None:
        clic = (x, y)


cv2.namedWindow("calibrar")
cv2.setMouseCallback("calibrar", raton)

while True:
    if congelado is None:
        ok, frame = cap.read()
        if not ok:
            break
        imagen = mp.Image(image_format=mp.ImageFormat.SRGB,
                          data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        res = detector.detect_for_video(imagen, int((time.time() - t0) * 1000))
        h, w = frame.shape[:2]
        puntos = None
        if res.pose_landmarks:
            m = res.pose_landmarks[0]
            lado = "i" if m[19].visibility >= m[20].visibility else "d"
            puntos = np.array([[m[j].x * w, m[j].y * h] for j in LADOS[lado]])
            for p in puntos:
                cv2.circle(frame, (int(p[0]), int(p[1])), 7, (0, 255, 0), -1)
        vista = frame.copy()
        cv2.putText(vista, f"muestras: {len(filas)}   ESPACIO: congelar   q: salir",
                    (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    else:
        vista = congelado[0].copy()
        cv2.putText(vista, "Clic en la yema del dedo | ENTER: guardar | ESC: descartar",
                    (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        if clic is not None:
            cv2.drawMarker(vista, clic, (0, 165, 255), cv2.MARKER_TILTED_CROSS, 30, 3)
    cv2.imshow("calibrar", vista)

    tecla = cv2.waitKey(1) & 0xFF
    if tecla == ord("q"):
        break
    if tecla == 32 and congelado is None and puntos is not None:       # ESPACIO
        congelado = (frame.copy(), puntos.copy())
        clic = None
    if tecla == 27 and congelado is not None:                           # ESC
        congelado, clic = None, None
    if tecla == 13 and congelado is not None and clic is not None:      # ENTER
        filas.append(list(congelado[1].flatten()) + list(clic))
        cv2.imwrite(f"calib2_{len(filas)}.png", vista)
        print(f"muestra {len(filas)} guardada")
        congelado, clic = None, None

cap.release()
cv2.destroyAllWindows()
if filas:
    cabecera = ["ind_x", "ind_y", "mun_x", "mun_y", "cod_x", "cod_y",
                "hom_x", "hom_y", "cad_x", "cad_y", "punta_x", "punta_y"]
    with open("calib_datos.csv", "w", newline="") as f:
        csv.writer(f).writerows([cabecera] + filas)
    print(f"{len(filas)} muestras guardadas en calib_datos.csv")