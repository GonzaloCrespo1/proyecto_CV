# -*- coding: utf-8 -*-
"""
CALIBRACIÓN DE UNA CÁMARA A PARTIR DE FOTOS DE UN DAMERO
=========================================================

Uso:
    1. Pon las fotos del damero en la carpeta "fotos_damero" (junto a este .py).
    2. Ajusta TAMANO_DAMERO y TAMANO_CUADRO si tu damero es distinto.
    3. Ejecuta:  python calibrar_camara.py

Resultado:
    - Imprime por pantalla la matriz intrínseca K, los coeficientes de
      distorsión, el error RMS de reproyección y los extrínsecos de cada foto.
    - Guarda todo en "resultados_calibracion/":
        * calibracion.txt         -> resumen legible
        * calibracion.npz         -> K, D, rvecs, tvecs (para cargar con np.load)
        * esquinas/               -> fotos con las esquinas detectadas dibujadas
        * sin_distorsion/         -> fotos corregidas con la calibración obtenida

Requisitos:  pip install opencv-python numpy
"""

import os
import glob
import sys

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# PARÁMETROS (cámbialos si tu damero es distinto)
# ---------------------------------------------------------------------------
# Nº de esquinas INTERIORES (columnas, filas). No es el nº de cuadros:
# un damero de 9x7 cuadros tiene 8x6 esquinas interiores.
TAMANO_DAMERO = (9, 6)

# Lado de cada cuadro en mm (las unidades de los tvecs saldrán en mm)
TAMANO_CUADRO = 30.0

CARPETA_FOTOS = "fotos_damero"
CARPETA_RESULTADOS = "resultados_calibracion"

# Criterio de parada para refinar las esquinas a nivel subpíxel
CRITERIO_SUBPIX = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.01)


# ---------------------------------------------------------------------------
# FUNCIONES
# ---------------------------------------------------------------------------
def cargar_rutas(carpeta):
    """Devuelve las rutas de todas las imágenes de la carpeta, ordenadas."""
    extensiones = ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.tif", "*.tiff")
    rutas = []
    for ext in extensiones:
        rutas += glob.glob(os.path.join(carpeta, ext))
        rutas += glob.glob(os.path.join(carpeta, ext.upper()))
    return sorted(set(rutas))


def puntos_damero_3d(tamano_damero, lado):
    """Coordenadas 3D (en mm) de las esquinas del damero, con Z = 0."""
    columnas, filas = tamano_damero
    puntos = np.zeros((columnas * filas, 3), np.float32)
    puntos[:, :2] = np.mgrid[0:columnas, 0:filas].T.reshape(-1, 2) * lado
    return puntos


def detectar_esquinas(img_gris, tamano_damero):
    """Busca las esquinas del damero y las refina a nivel subpíxel."""
    flags = (cv2.CALIB_CB_ADAPTIVE_THRESH
             + cv2.CALIB_CB_NORMALIZE_IMAGE
             + cv2.CALIB_CB_FAST_CHECK)
    encontrado, esquinas = cv2.findChessboardCorners(img_gris, tamano_damero, flags)
    if not encontrado:
        return False, None
    # La ventana de refinado se adapta al tamaño del cuadro en la foto
    # (~1/4 del lado del cuadro): fija y grande falla en fotos pequeñas.
    pts = esquinas.reshape(-1, 2)
    lado_px = np.median(np.linalg.norm(pts[1:tamano_damero[0]] - pts[:tamano_damero[0] - 1], axis=1))
    w = int(np.clip(lado_px / 4, 2, 11))
    esquinas = cv2.cornerSubPix(img_gris, esquinas, (w, w), (-1, -1), CRITERIO_SUBPIX)
    return True, esquinas


def error_por_imagen(puntos_3d, puntos_2d, rvecs, tvecs, K, D):
    """Error RMS de reproyección (en px) de cada imagen por separado."""
    errores = []
    for p3d, p2d, rvec, tvec in zip(puntos_3d, puntos_2d, rvecs, tvecs):
        proyectados, _ = cv2.projectPoints(p3d, rvec, tvec, K, D)
        dif = proyectados.reshape(-1, 2) - p2d.reshape(-1, 2)
        errores.append(np.sqrt(np.mean(np.sum(dif ** 2, axis=1))))
    return errores


# ---------------------------------------------------------------------------
# PROGRAMA PRINCIPAL
# ---------------------------------------------------------------------------
def main():
    # Trabajar siempre desde la carpeta donde está el script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    np.set_printoptions(precision=4, suppress=True)

    # 1. Cargar fotos ---------------------------------------------------------
    rutas = cargar_rutas(CARPETA_FOTOS)
    if not rutas:
        os.makedirs(CARPETA_FOTOS, exist_ok=True)
        sys.exit(f"No hay imágenes en '{CARPETA_FOTOS}/'. Pon ahí las fotos del damero y vuelve a ejecutar.")
    print(f"Imágenes encontradas: {len(rutas)}")
    print(f"Damero: {TAMANO_DAMERO[0]}x{TAMANO_DAMERO[1]} esquinas interiores, cuadro de {TAMANO_CUADRO} mm\n")

    os.makedirs(os.path.join(CARPETA_RESULTADOS, "esquinas"), exist_ok=True)
    os.makedirs(os.path.join(CARPETA_RESULTADOS, "sin_distorsion"), exist_ok=True)

    patron_3d = puntos_damero_3d(TAMANO_DAMERO, TAMANO_CUADRO)
    puntos_3d, puntos_2d, nombres_validos = [], [], []
    tamano_imagen = None

    # 2. Detectar esquinas en cada foto ---------------------------------------
    for ruta in rutas:
        nombre = os.path.basename(ruta)
        img = cv2.imread(ruta)
        if img is None:
            print(f"  [X] {nombre}: no se pudo leer")
            continue

        gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        tam = gris.shape[::-1]  # (ancho, alto)
        if tamano_imagen is None:
            tamano_imagen = tam
        elif tam != tamano_imagen:
            print(f"  [X] {nombre}: tamaño {tam} distinto de {tamano_imagen}, se descarta")
            continue

        ok, esquinas = detectar_esquinas(gris, TAMANO_DAMERO)
        if not ok:
            print(f"  [X] {nombre}: damero NO detectado")
            continue

        print(f"  [OK] {nombre}")
        puntos_3d.append(patron_3d)
        puntos_2d.append(esquinas)
        nombres_validos.append(nombre)

        dibujo = cv2.drawChessboardCorners(img.copy(), TAMANO_DAMERO, esquinas, ok)
        cv2.imwrite(os.path.join(CARPETA_RESULTADOS, "esquinas", nombre), dibujo)

    print(f"\nDetecciones válidas: {len(nombres_validos)} / {len(rutas)}")
    if len(nombres_validos) < 3:
        sys.exit("Se necesitan al menos 3 fotos con el damero detectado (mejor 10-20). "
                 "Revisa TAMANO_DAMERO (esquinas INTERIORES) o la calidad de las fotos.")

    # 3. Calibrar -------------------------------------------------------------
    rms, K, D, rvecs, tvecs = cv2.calibrateCamera(puntos_3d, puntos_2d, tamano_imagen, None, None)

    # Extrínsecos [R | t] de cada foto
    extrinsecos = [np.hstack((cv2.Rodrigues(r)[0], t)) for r, t in zip(rvecs, tvecs)]
    errores = error_por_imagen(puntos_3d, puntos_2d, rvecs, tvecs, K, D)

    # Parámetros "físicos" derivados de K
    fx, fy, cx, cy = K[0, 0], K[1, 1], K[0, 2], K[1, 2]
    fovx, fovy, _, _, _ = cv2.calibrationMatrixValues(K, tamano_imagen, 0, 0)

    # 4. Mostrar resultados ---------------------------------------------------
    lineas = []
    lineas.append("=" * 60)
    lineas.append("RESULTADOS DE LA CALIBRACIÓN")
    lineas.append("=" * 60)
    lineas.append(f"Imágenes usadas: {len(nombres_validos)} / {len(rutas)}")
    lineas.append(f"Resolución: {tamano_imagen[0]} x {tamano_imagen[1]} px")
    lineas.append(f"Damero: {TAMANO_DAMERO} esquinas interiores, cuadro {TAMANO_CUADRO} mm\n")
    lineas.append(f"Error RMS de reproyección: {rms:.4f} px  "
                  f"({'bueno' if rms < 0.5 else 'mejorable: revisa fotos borrosas o mal detectadas'})\n")
    lineas.append("Matriz intrínseca K:")
    lineas.append(str(K) + "\n")
    lineas.append(f"  fx = {fx:.2f} px   fy = {fy:.2f} px")
    lineas.append(f"  cx = {cx:.2f} px   cy = {cy:.2f} px")
    lineas.append(f"  Campo de visión: {fovx:.2f}° (horizontal) x {fovy:.2f}° (vertical)\n")
    d = D.ravel()
    lineas.append("Coeficientes de distorsión [k1, k2, p1, p2, k3]:")
    lineas.append(str(d) + "\n")
    lineas.append("Error de reproyección por imagen (px):")
    for nombre, e in zip(nombres_validos, errores):
        lineas.append(f"  {nombre:30s} {e:.4f}{'   <-- alto' if e > 2 * rms else ''}")
    lineas.append("\nExtrínsecos [R | t] de cada imagen (t en mm):")
    for nombre, E in zip(nombres_validos, extrinsecos):
        lineas.append(f"  {nombre}:")
        lineas.append("    " + str(E).replace("\n", "\n    "))

    texto = "\n".join(lineas)
    print("\n" + texto)

    # 5. Guardar resultados ---------------------------------------------------
    with open(os.path.join(CARPETA_RESULTADOS, "calibracion.txt"), "w", encoding="utf-8") as f:
        f.write(texto)
    np.savez(os.path.join(CARPETA_RESULTADOS, "calibracion.npz"),
             K=K, D=D, rms=rms, rvecs=np.array(rvecs), tvecs=np.array(tvecs),
             tamano_imagen=np.array(tamano_imagen), imagenes=np.array(nombres_validos))

    # Imágenes corregidas (quitando la distorsión)
    K_nueva, roi = cv2.getOptimalNewCameraMatrix(K, D, tamano_imagen, 1, tamano_imagen)
    for ruta in rutas:
        img = cv2.imread(ruta)
        if img is None or img.shape[1::-1] != tamano_imagen:
            continue
        corregida = cv2.undistort(img, K, D, None, K_nueva)
        cv2.imwrite(os.path.join(CARPETA_RESULTADOS, "sin_distorsion", os.path.basename(ruta)), corregida)

    print(f"\nResultados guardados en '{CARPETA_RESULTADOS}/'")


if __name__ == "__main__":
    main()
