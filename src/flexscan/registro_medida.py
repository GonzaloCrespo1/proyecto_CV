"""Pitidos y registro de cada medida: captura, gráfica, serie temporal y resumen.

Al terminar una medida (con valor o sin él) se crea una carpeta por toma, con la fecha y la
hora en el nombre para que ninguna toma pise a otra, y dentro cuatro ficheros:
  datos/en_vivo/toma_AAAAMMDD_HHMMSS/                con la persona sin identificar
  datos/en_vivo/<usuario>/toma_AAAAMMDD_HHMMSS/      con la persona identificada en el login
      captura.png   imagen del programa con el resultado en pantalla
      grafica.png   distancia (cm) frente al tiempo, con la ventana elegida
      serie.csv     la serie temporal (t_s, d_cm)
      resumen.json  estado, medida, línea base, tiempos y parámetros
"""
import csv
import io
import json
import math
import threading
import time
import wave
from pathlib import Path

import cv2
import numpy as np

from flexscan.escala import RAIZ
from flexscan.perfil import cargar_perfil, carpeta_usuario
from flexscan.usuarios import normalizar
from flexscan.medida import (FIN_SIN_MEJORA_S, LIMITE_S, SUBIDA_MIN_CM, TERMINADA,
                             VARIACION_BASE_CM, VARIACION_MAX_CM, VENTANA_S)

CARPETA = RAIZ / "datos" / "en_vivo"
ANCHO, ALTO = 960, 480
M_IZQ, M_DER, M_SUP, M_INF = 70, 150, 50, 60      # márgenes (a la derecha, las etiquetas)
FUENTE = cv2.FONT_HERSHEY_SIMPLEX
AZUL, TURQUESA, NARANJA = (63, 38, 18), (138, 138, 31), (58, 131, 232)    # BGR
GRIS, GRIS_CLARO = (120, 120, 120), (215, 215, 215)


# Pitidos: lista de (frecuencia en Hz, duración en ms); None en la frecuencia es un silencio
PITIDO_INICIO = [(1600, 250), (None, 120), (1600, 250)]      # agudo: empieza el estiramiento
PITIDO_FIN = [(450, 1000)]                                   # grave: termina la medida
PITIDO_SIN_MEDIDA = [(450, 350), (None, 150), (450, 350)]    # grave doble: termina sin medida


FRECUENCIA_MUESTREO = 44100
ARRANQUE_S = 0.30            # silencio inicial: despierta la salida de audio (altavoces o auriculares) antes del tono
_sonidos = {}


def _wav(secuencia):
    """Sonido en memoria (WAV mono de 16 bits) con la secuencia de tonos y silencios, con un silencio inicial."""
    if tuple(secuencia) not in _sonidos:
        trozos = [np.zeros(int(ARRANQUE_S * FRECUENCIA_MUESTREO))]
        for frecuencia, ms in secuencia:
            n = int(ms / 1000 * FRECUENCIA_MUESTREO)
            if frecuencia is None:
                trozos.append(np.zeros(n))
                continue
            t = np.arange(n) / FRECUENCIA_MUESTREO
            borde = min(n // 2, int(0.01 * FRECUENCIA_MUESTREO))             # 10 ms de subida y bajada: sin chasquidos
            envolvente = np.ones(n)
            envolvente[:borde] = np.linspace(0, 1, borde)
            envolvente[n - borde:] = np.linspace(1, 0, borde)
            trozos.append(0.8 * envolvente * np.sin(2 * math.pi * frecuencia * t))
        datos = (np.concatenate(trozos) * 32767).astype("<i2").tobytes()
        memoria = io.BytesIO()
        with wave.open(memoria, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(FRECUENCIA_MUESTREO)
            w.writeframes(datos)
        _sonidos[tuple(secuencia)] = memoria.getvalue()
    return _sonidos[tuple(secuencia)]


def _tocar(secuencia):
    """Toca la secuencia en un hilo aparte, para no parar el vídeo mientras suena."""
    def tocar():
        try:
            import winsound
        except ImportError:                  # fuera de Windows: la campana de la terminal
            print("\a", end="", flush=True)
            return
        try:                                 # por la salida de audio normal, como cualquier sonido del sistema
            winsound.PlaySound(_wav(secuencia), winsound.SND_MEMORY | winsound.SND_NODEFAULT)
        except Exception:                    # si falla, el altavoz del sistema
            for frecuencia, ms in secuencia:
                if frecuencia is None:
                    time.sleep(ms / 1000)
                    continue
                try:
                    winsound.Beep(frecuencia, ms)
                except RuntimeError:
                    pass
    threading.Thread(target=tocar, daemon=True).start()


def pitar_inicio():
    """Pitido agudo: la persona puede empezar el estiramiento."""
    print("[FlexScan] Pitido de inicio: ya puedes extender los brazos.", flush=True)
    _tocar(PITIDO_INICIO)


def pitar_fin(hay_medida):
    """Pitido grave: la medida ha terminado (uno largo si hay medida, dos cortos si no la hay)."""
    print("[FlexScan] Pitido final:", "medida realizada." if hay_medida else "sin medida.", flush=True)
    _tocar(PITIDO_FIN if hay_medida else PITIDO_SIN_MEDIDA)


def _paso(rango, objetivo):
    """Paso 'redondo' (1, 2, 5, 10, 20...) para unas `objetivo` marcas en un rango."""
    bruto = rango / objetivo
    magnitud = 10 ** math.floor(math.log10(bruto))
    for m in (1, 2, 5, 10):
        if bruto <= m * magnitud:
            return m * magnitud
    return 10 * magnitud


def dibujar_grafica(validador):
    """Gráfica de la distancia en cm frente al tiempo, con la base, la medida y la ventana."""
    lienzo = np.full((ALTO, ANCHO, 3), 255, np.uint8)
    cv2.putText(lienzo, "Distancia dedo-pie (cm) frente al tiempo", (M_IZQ, 30), FUENTE, 0.7, AZUL, 2)
    datos = validador.historial
    if len(datos) < 2:
        cv2.putText(lienzo, "Sin datos", (M_IZQ, 80), FUENTE, 0.7, GRIS, 2)
        return lienzo
    ts = [t for t, _ in datos]
    ds = [d for _, d in datos]
    base, mejor = validador.base, validador.mejor
    referencias = [v for v in (base, None if base is None else base + SUBIDA_MIN_CM, mejor)
                   if v is not None]
    # la escala vertical se ajusta a lo ocurrido desde poco antes de fijar la línea base;
    # lo anterior (la persona entrando y sentándose) puede salir de la escala y se recorta
    t_vista = 0.0 if validador.t_inicio is None or validador.t0 is None \
        else max(0.0, validador.t_inicio - validador.t0 - 2.0)
    vista = [d for t, d in datos if t >= t_vista] or ds
    y_min, y_max = min(vista + referencias) - 3, max(vista + referencias) + 3
    t_max = max(ts[-1], 1e-6)
    x0, x1, y0, y1 = M_IZQ, ANCHO - M_DER, M_SUP, ALTO - M_INF

    def px(t):
        return int(x0 + t / t_max * (x1 - x0))

    def py(d):
        return int(min(max(y1 - (d - y_min) / (y_max - y_min) * (y1 - y0), y0), y1))

    # cuadrícula y ejes con números
    paso_y = _paso(y_max - y_min, 6)
    y = math.ceil(y_min / paso_y) * paso_y
    while y <= y_max:
        cv2.line(lienzo, (x0, py(y)), (x1, py(y)), GRIS_CLARO, 1)
        cv2.putText(lienzo, f"{y:.0f}", (x0 - 45, py(y) + 5), FUENTE, 0.45, GRIS, 1)
        y += paso_y
    paso_x = _paso(t_max, 8)
    t = 0.0
    while t <= t_max:
        cv2.line(lienzo, (px(t), y0), (px(t), y1), GRIS_CLARO, 1)
        cv2.putText(lienzo, f"{t:.0f}", (px(t) - 8, y1 + 20), FUENTE, 0.45, GRIS, 1)
        t += paso_x
    cv2.rectangle(lienzo, (x0, y0), (x1, y1), GRIS, 1)
    cv2.putText(lienzo, "t (s)", ((x0 + x1) // 2 - 15, ALTO - 15), FUENTE, 0.5, GRIS, 1)
    cv2.putText(lienzo, "d (cm)", (8, y0 - 8), FUENTE, 0.5, GRIS, 1)

    # ventana elegida (sombreada)
    if validador.ventana_mejor is not None:
        a, b = validador.ventana_mejor
        capa = lienzo.copy()
        cv2.rectangle(capa, (px(a), y0), (px(b), y1), TURQUESA, -1)
        lienzo = cv2.addWeighted(capa, 0.25, lienzo, 0.75, 0)
        cv2.putText(lienzo, f"Ventana de {VENTANA_S:.0f} s", (px(a) - 20, y1 - 28), FUENTE, 0.45, TURQUESA, 1)

    # línea base, umbral de flexión y medida
    def horizontal(valor, color, etiqueta, grosor):
        cv2.line(lienzo, (x0, py(valor)), (x1, py(valor)), color, grosor)
        cv2.putText(lienzo, etiqueta, (x1 + 6, py(valor) + 5), FUENTE, 0.45, color, 1)

    if base is not None:
        horizontal(base, GRIS, f"base {base:+.0f}", 1)
        horizontal(base + SUBIDA_MIN_CM, GRIS_CLARO, f"base+{SUBIDA_MIN_CM:.0f}", 1)
    if mejor is not None:
        palabra = "Medida" if validador.estado == TERMINADA else "Mejor"
        horizontal(mejor, NARANJA, f"{palabra} {mejor:+.0f} cm", 2)

    # curva y marcas verticales
    puntos = np.array([[px(t_), py(d_)] for t_, d_ in datos], np.int32)
    cv2.polylines(lienzo, [puntos], False, AZUL, 2, cv2.LINE_AA)
    if min(ds) < y_min or max(ds) > y_max:
        cv2.putText(lienzo, "(valores fuera de escala, recortados)", (x1 - 290, y0 - 8), FUENTE, 0.45, GRIS, 1)
    if validador.t_inicio is not None and validador.t0 is not None:
        t_base = validador.t_inicio - validador.t0
        cv2.line(lienzo, (px(t_base), y0), (px(t_base), y1), GRIS, 1)
        cv2.putText(lienzo, "Base fijada", (px(t_base) + 4, y1 - 8), FUENTE, 0.45, GRIS, 1)
    if validador.t_fin is not None:
        cv2.line(lienzo, (px(validador.t_fin), y0), (px(validador.t_fin), y1), NARANJA, 1)
        cv2.putText(lienzo, "Aviso", (px(validador.t_fin) - 40, y1 - 8), FUENTE, 0.45, NARANJA, 1)
    return lienzo


def guardar_toma(frame, validador, px_por_cm, carpeta=CARPETA, usuario=None):
    """Guarda captura, gráfica, serie y resumen de la medida en una carpeta propia.

    Devuelve la ruta de esa carpeta. Con `usuario` (el nombre del login) la toma se guarda
    dentro de la carpeta de esa persona.
    """
    carpeta = Path(carpeta)
    raiz = carpeta                                            # carpeta común de todas las personas
    if usuario:
        carpeta = carpeta_usuario(usuario, raiz)
    nombre = "toma_" + time.strftime("%Y%m%d_%H%M%S")
    while (carpeta / nombre).exists():                        # nunca se pisa una toma anterior
        nombre += "_b"
    carpeta = carpeta / nombre
    carpeta.mkdir(parents=True)
    cv2.imwrite(str(carpeta / "captura.png"), frame)
    cv2.imwrite(str(carpeta / "grafica.png"), dibujar_grafica(validador))
    with open(carpeta / "serie.csv", "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(["t_s", "d_cm"])
        escritor.writerows((f"{t:.3f}", f"{d:.2f}") for t, d in validador.historial)
    t_base = None if validador.t_inicio is None or validador.t0 is None \
        else round(validador.t_inicio - validador.t0, 2)
    perfil = cargar_perfil(usuario, raiz) if usuario else None
    if perfil is not None:
        perfil = {k: v for k, v in perfil.items() if k != "usuario"}   # copia de los datos de ese momento
    resumen = {
        "usuario": normalizar(usuario) if usuario else None,
        "perfil": perfil,
        "fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
        "estado": validador.estado,
        "medida_cm": None if validador.estado != TERMINADA else round(validador.mejor, 1),
        "mejor_candidata_cm": None if validador.mejor is None else round(validador.mejor, 1),
        "base_cm": None if validador.base is None else round(validador.base, 1),
        "t_base_s": t_base,
        "ventana_mejor_s": None if validador.ventana_mejor is None
        else [round(v, 2) for v in validador.ventana_mejor],
        "t_fin_s": None if validador.t_fin is None else round(validador.t_fin, 2),
        "px_por_cm": px_por_cm,
        "parametros": {"ventana_s": VENTANA_S, "variacion_base_cm": VARIACION_BASE_CM,
                       "variacion_max_cm": VARIACION_MAX_CM, "subida_min_cm": SUBIDA_MIN_CM,
                       "fin_sin_mejora_s": FIN_SIN_MEJORA_S, "limite_s": LIMITE_S},
    }
    (carpeta / "resumen.json").write_text(
        json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    return carpeta
