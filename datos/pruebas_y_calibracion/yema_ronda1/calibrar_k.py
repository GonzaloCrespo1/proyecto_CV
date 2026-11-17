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
muestras = []          # valores de k guardados
congelado = None       # (fotograma, indice, muneca) mientras la imagen está parada
clic = None


def raton(evento, x, y, flags, param):
    global clic
    if evento == cv2.EVENT_LBUTTONDOWN and congelado is not None:
        clic = (x, y)


cv2.namedWindow("calibrar k")
cv2.setMouseCallback("calibrar k", raton)

while True:
    if congelado is None:
        ok, frame = cap.read()
        if not ok:
            break
        imagen = mp.Image(image_format=mp.ImageFormat.SRGB,
                          data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        res = detector.detect_for_video(imagen, int((time.time() - t0) * 1000))
        h, w = frame.shape[:2]
        indice = muneca = None
        if res.pose_landmarks:
            m = res.pose_landmarks[0]
            # lado con el dedo más visible: 19-15 (izquierda) o 20-16 (derecha)
            i_ind, i_mun = (19, 15) if m[19].visibility >= m[20].visibility else (20, 16)
            indice = np.array([m[i_ind].x * w, m[i_ind].y * h])
            muneca = np.array([m[i_mun].x * w, m[i_mun].y * h])
            cv2.circle(frame, tuple(indice.astype(int)), 7, (0, 255, 0), -1)
            cv2.circle(frame, tuple(muneca.astype(int)), 7, (255, 0, 0), -1)
        vista = frame.copy()
        cv2.putText(vista, f"muestras: {len(muestras)}   ESPACIO: congelar   q: salir",
                    (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    else:
        vista = congelado[0].copy()
        cv2.putText(vista, "Clic en la yema del dedo | ENTER: guardar | ESC: descartar",
                    (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        if clic is not None:
            cv2.drawMarker(vista, clic, (0, 165, 255), cv2.MARKER_TILTED_CROSS, 30, 3)
    cv2.imshow("calibrar k", vista)

    tecla = cv2.waitKey(1) & 0xFF
    if tecla == ord("q"):
        break
    if tecla == 32 and congelado is None and indice is not None:      # ESPACIO
        congelado = (frame.copy(), indice.copy(), muneca.copy())
        clic = None
    if tecla == 27 and congelado is not None:                          # ESC
        congelado, clic = None, None
    if tecla == 13 and congelado is not None and clic is not None:     # ENTER
        _, ind, mun = congelado
        v = ind - mun                                  # muñeca -> nudillo
        k = float(np.dot(np.array(clic) - ind, v) / np.dot(v, v))
        muestras.append(k)
        cv2.imwrite(f"calib_{len(muestras)}.png", vista)
        print(f"muestra {len(muestras)}: k = {k:.2f}   (|nudillo-muñeca| = {np.linalg.norm(v):.0f} px)")
        congelado, clic = None, None

cap.release()
cv2.destroyAllWindows()
if muestras:
    print(f"\nk mediana = {np.median(muestras):.2f}   media = {np.mean(muestras):.2f}   "
          f"desviación = {np.std(muestras):.2f}   n = {len(muestras)}")
    with open("calib_k.csv", "w", newline="") as f:
        csv.writer(f).writerows([["k"]] + [[k] for k in muestras])