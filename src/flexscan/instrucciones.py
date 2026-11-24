"""Ventana de instrucciones del ejercicio: figura animada, cinco pasos y botón «He leído y entendido»."""
import math
import time
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

VENTANA = "FlexScan - Instrucciones"
ANCHO, ALTO = 1280, 720
FUENTES = Path(__file__).parent / "fuentes"

# Paleta del proyecto (RGB para Pillow; BGR para OpenCV)
def _bgr(rgb):
    return (rgb[2], rgb[1], rgb[0])

AZUL, TURQUESA, NARANJA = (18, 38, 63), (31, 138, 138), (232, 131, 58)
TURQUESA_OSC = (22, 104, 104)
GRIS, GRIS_CLARO, FONDO, BLANCO = (107, 118, 134), (203, 211, 220), (238, 242, 245), (255, 255, 255)
PIEL, MAGENTA, SUELO = (233, 190, 160), (200, 40, 190), (222, 214, 204)

# Texto de los cinco pasos: (título, descripción)
PASOS = [
    ("Aprendizaje del fondo",
     "Al pulsar el botón tienes 5 segundos para apartarte del encuadre. El programa aprende el fondo vacío."),
    ("Colócate en tu sitio",
     "Siéntate donde te indique el equipo del proyecto: es el lugar donde se hizo la calibración."),
    ("Posición inicial",
     "Piernas estiradas y manos sobre las rodillas. Espera sin moverte."),
    ("Pitido agudo: extiéndete",
     "Estira los brazos paralelos a las piernas y llega lo más lejos que puedas, sin agarrarte ni empujar los pies."),
    ("Quieto hasta el pitido grave",
     "Mantén tu máxima flexibilidad, sin moverte, hasta oír el pitido grave."),
]

# La animación dura DURACION s y tiene cuatro fases: (inicio, nombre, paso resaltado, leyenda)
DURACION = 9.0
FASES = [
    (0.0, 2.0, 2, "Posición inicial: manos sobre las rodillas"),
    (2.0, 4.0, 3, "Pitido agudo: extiéndete hacia delante"),
    (4.0, 7.2, 4, "Máximo alcance: quieto hasta el pitido grave"),
    (7.2, 9.0, 4, "Pitido grave: la medida ha terminado"),
]

# Geometría de la escena (unidades del dibujo, eje y hacia arriba) y su paso a píxeles
LADO_X, LADO_Y = 40, 150          # esquina de la tarjeta de la figura
ESC, CADERA_PX, SUELO_PX = 3.0, 520, 505
PIERNA, TRONCO, BRAZO_1, BRAZO_2, CABEZA_R = 125.0, 58.0, 29.0, 28.0, 11.0
CADERA = (0.0, 9.0)
TH_INI, TH_MAX = 24.0, 54.0       # inclinación del tronco en cada pose (grados desde la vertical)
MANO_INI, MANO_MAX = (-61.0, 21.5), (-102.5, 31.0)


@lru_cache(maxsize=None)
def _fuente(tam, negrita=False):
    nombre = "Carlito-Bold.ttf" if negrita else "Carlito-Regular.ttf"
    return ImageFont.truetype(str(FUENTES / nombre), tam)


def _suave(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def _px(p):
    """Punto del dibujo (x, y hacia arriba) a píxel."""
    return (int(round(CADERA_PX + p[0] * ESC)), int(round(SUELO_PX - p[1] * ESC)))


def _ik(hombro, objetivo, l1, l2):
    """Codo de un brazo de dos tramos que va del hombro al objetivo, doblado hacia abajo."""
    dx, dy = objetivo[0] - hombro[0], objetivo[1] - hombro[1]
    d = min(math.hypot(dx, dy), l1 + l2 - 1e-3)
    base = math.atan2(dy, dx)
    delta = math.acos(max(-1.0, min(1.0, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))
    candidatos = [(hombro[0] + l1 * math.cos(base + s * delta), hombro[1] + l1 * math.sin(base + s * delta))
                  for s in (1, -1)]
    codo = min(candidatos, key=lambda c: c[1])
    mano = (hombro[0] + d * math.cos(base), hombro[1] + d * math.sin(base))
    return codo, mano


def _pose(t):
    """Parámetros de la pose en el instante t de la animación: (θ tronco, objetivo de la mano)."""
    t = t % DURACION
    if t < 2.0:
        k = 0.0
    elif t < 4.0:
        k = _suave((t - 2.0) / 2.0)
    elif t < 7.2:
        k = 1.0
    else:
        k = 1.0 - _suave((t - 7.2) / 1.8)
    th = TH_INI + (TH_MAX - TH_INI) * k
    mano = (MANO_INI[0] + (MANO_MAX[0] - MANO_INI[0]) * k, MANO_INI[1] + (MANO_MAX[1] - MANO_INI[1]) * k)
    return th, mano, k


def _fase(t):
    t = t % DURACION
    for i, (a, b, _paso, _txt) in enumerate(FASES):
        if a <= t < b:
            return i
    return len(FASES) - 1


def _miembro(img, a, b, grosor, color, borde=None):
    """Segmento con extremos redondos y, si se pide, contorno."""
    a, b = _px(a) if not isinstance(a[0], int) else a, _px(b) if not isinstance(b[0], int) else b
    if borde is not None:
        cv2.line(img, a, b, _bgr(borde), grosor + 6, cv2.LINE_AA)
        cv2.circle(img, a, (grosor + 6) // 2, _bgr(borde), -1, cv2.LINE_AA)
        cv2.circle(img, b, (grosor + 6) // 2, _bgr(borde), -1, cv2.LINE_AA)
    cv2.line(img, a, b, _bgr(color), grosor, cv2.LINE_AA)
    cv2.circle(img, a, grosor // 2, _bgr(color), -1, cv2.LINE_AA)
    cv2.circle(img, b, grosor // 2, _bgr(color), -1, cv2.LINE_AA)


def dibujar_figura(img, t):
    """Dibuja la escena (suelo, figura sentada de perfil y marcas de medida) en el instante t."""
    th, objetivo, k = _pose(t)
    fase = _fase(t)
    r = math.radians(th)
    cadera = CADERA
    rodilla, tobillo = (-PIERNA / 2, CADERA[1]), (-PIERNA, CADERA[1])
    hombro = (cadera[0] - TRONCO * math.sin(r), cadera[1] + TRONCO * math.cos(r))
    rh = math.radians(th * 0.7)
    cabeza = (hombro[0] - 21 * math.sin(rh), hombro[1] + 21 * math.cos(rh))
    codo, mano = _ik(hombro, objetivo, BRAZO_1, BRAZO_2)

    # sombra y suelo
    sombra = img.copy()
    cv2.ellipse(sombra, (CADERA_PX - 150, SUELO_PX + 4), (250, 12), 0, 0, 360, _bgr(GRIS), -1, cv2.LINE_AA)
    cv2.addWeighted(sombra, 0.18, img, 0.82, 0, img)

    # línea de los pies (como la del programa) con su etiqueta
    x_pie = _px((-PIERNA - 4, 0))[0]
    for y in range(LADO_Y + 70, SUELO_PX + 6, 16):
        cv2.line(img, (x_pie, y), (x_pie, y + 8), _bgr(NARANJA), 2, cv2.LINE_AA)
    cv2.putText(img, "pies", (x_pie - 18, LADO_Y + 62), cv2.FONT_HERSHEY_SIMPLEX, 0.55, _bgr(NARANJA), 1, cv2.LINE_AA)

    # piernas y pie
    _miembro(img, cadera, rodilla, 50, AZUL)
    _miembro(img, rodilla, tobillo, 46, AZUL)
    _miembro(img, (tobillo[0] - 1, 4), (tobillo[0] - 1, 22), 34, (236, 236, 236), AZUL)
    # tronco
    _miembro(img, (cadera[0] + 2, cadera[1] + 6), (hombro[0], hombro[1] - 4), 58, TURQUESA, AZUL)
    # cabeza: pelo detrás, cara delante
    c = _px(cabeza)
    cv2.circle(img, c, int(CABEZA_R * ESC) + 2, _bgr(AZUL), -1, cv2.LINE_AA)
    cv2.circle(img, (c[0] - 5, c[1] + 1), int(CABEZA_R * ESC) - 3, _bgr(PIEL), -1, cv2.LINE_AA)
    cv2.circle(img, (c[0] - int(CABEZA_R * ESC) + 1, c[1] + 4), 5, _bgr(PIEL), -1, cv2.LINE_AA)    # nariz
    cv2.circle(img, (c[0] - 17, c[1] - 6), 3, _bgr(AZUL), -1, cv2.LINE_AA)                            # ojo
    # brazo
    _miembro(img, hombro, codo, 24, TURQUESA_OSC, AZUL)
    _miembro(img, codo, mano, 18, PIEL, AZUL)
    cv2.circle(img, _px(mano), 12, _bgr(PIEL), -1, cv2.LINE_AA)
    cv2.circle(img, _px(mano), 12, _bgr(AZUL), 2, cv2.LINE_AA)

    # punta de los dedos (aspa) y distancia a los pies, como en el programa
    dedos = (mano[0] - 11, mano[1] - 1)
    p = _px(dedos)
    if k > 0.02:
        cv2.line(img, (p[0] - 8, p[1] - 8), (p[0] + 8, p[1] + 8), _bgr(MAGENTA), 3, cv2.LINE_AA)
        cv2.line(img, (p[0] - 8, p[1] + 8), (p[0] + 8, p[1] - 8), _bgr(MAGENTA), 3, cv2.LINE_AA)
        if p[0] - x_pie > 24:                         # la distancia solo se dibuja si hay espacio
            cv2.line(img, (x_pie, p[1] - 22), (p[0], p[1] - 22), _bgr(NARANJA), 2, cv2.LINE_AA)
            cv2.putText(img, "d", ((x_pie + p[0]) // 2 - 4, p[1] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        _bgr(NARANJA), 2, cv2.LINE_AA)
    return fase


# ---------------------------------------------------------------- composición de la ventana
TARJETA_FIG = (30, 110, 640, 610)          # x0, y0, x1, y1
COL_X0, COL_X1, FILA_Y0, FILA_ALTO, FILA_SEP = 670, 1250, 110, 92, 10
BOTON = (670, 630, 1250, 696)


def _texto_ajustado(dib, texto, fuente, ancho):
    """Divide el texto en líneas que quepan en `ancho` píxeles."""
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = (actual + " " + palabra).strip()
        if dib.textlength(prueba, font=fuente) <= ancho:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    lineas.append(actual)
    return lineas


def _capa(fase, sobre_boton):
    """Parte fija de la ventana para una fase de la animación y para el estado del botón."""
    im = Image.new("RGB", (ANCHO, ALTO), FONDO)
    d = ImageDraw.Draw(im)
    # cabecera
    d.rectangle((0, 0, ANCHO, 84), fill=AZUL)
    d.text((34, 14), "Antes de empezar: así se hace la medida", font=_fuente(34, True), fill=BLANCO)
    d.text((36, 54), "Lee las instrucciones con calma: de ellas depende que la medida sea válida.",
           font=_fuente(19), fill=GRIS_CLARO)
    # tarjeta de la figura: pared, suelo y leyenda de pitidos
    x0, y0, x1, y1 = TARJETA_FIG
    d.rounded_rectangle((x0, y0, x1, y1), 18, fill=(250, 248, 246), outline=GRIS_CLARO, width=2)
    suelo = Image.new("RGB", (x1 - x0 - 4, y1 - SUELO_PX - 2), SUELO)
    mascara = Image.new("L", suelo.size, 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, -40, suelo.width, suelo.height), 16, fill=255)
    im.paste(suelo, (x0 + 2, SUELO_PX), mascara)
    d.line((x0 + 3, SUELO_PX, x1 - 3, SUELO_PX), fill=GRIS_CLARO, width=2)
    d.text((x0 + 22, y0 + 14), FASES[fase][3], font=_fuente(25, True), fill=AZUL)
    for i, (txt, color) in enumerate((("Pitido AGUDO: empieza", TURQUESA), ("Pitido GRAVE: termina", NARANJA))):
        bx = x0 + 22 + i * 292
        d.rounded_rectangle((bx, y1 - 52, bx + 270, y1 - 14), 19, fill=color)
        d.text((bx + 135, y1 - 33), txt, font=_fuente(20, True), fill=BLANCO, anchor="mm")
    # los cinco pasos
    activo = FASES[fase][2]
    for i, (titulo, cuerpo) in enumerate(PASOS):
        ya = FILA_Y0 + i * (FILA_ALTO + FILA_SEP)
        resaltado = i == activo
        d.rounded_rectangle((COL_X0, ya, COL_X1, ya + FILA_ALTO), 14,
                            fill=(221, 240, 240) if resaltado else BLANCO,
                            outline=TURQUESA if resaltado else GRIS_CLARO, width=3 if resaltado else 2)
        cx, cy = COL_X0 + 38, ya + FILA_ALTO // 2
        d.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill=TURQUESA if resaltado else AZUL)
        d.text((cx, cy - 1), str(i + 1), font=_fuente(28, True), fill=BLANCO, anchor="mm")
        d.text((COL_X0 + 78, ya + 9), titulo, font=_fuente(23, True), fill=AZUL)
        fuente = _fuente(19)
        for j, linea in enumerate(_texto_ajustado(d, cuerpo, fuente, COL_X1 - COL_X0 - 98)):
            d.text((COL_X0 + 78, ya + 40 + j * 23), linea, font=fuente, fill=GRIS if not resaltado else AZUL)
    # botón
    bx0, by0, bx1, by1 = BOTON
    d.rounded_rectangle((bx0, by0, bx1, by1), 16, fill=AZUL if sobre_boton else TURQUESA)
    d.text(((bx0 + bx1) // 2, (by0 + by1) // 2 - 1), "He leído y entendido", font=_fuente(30, True),
           fill=BLANCO, anchor="mm")
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


def construir_capas():
    """Pre-renderiza las capas fijas: una por fase y estado del botón."""
    return {(f, h): _capa(f, h) for f in range(len(FASES)) for h in (False, True)}


def dibujar_ventana(capas, t, sobre_boton):
    """Imagen completa de la ventana en el instante t de la animación."""
    fase = _fase(t)
    img = capas[(fase, sobre_boton)].copy()
    dibujar_figura(img, t)
    return img


def mostrar_instrucciones(ventana=VENTANA):
    """Muestra la ventana hasta que se pulsa el botón. Devuelve True al aceptar y False si se cancela (Esc)."""
    capas = construir_capas()
    estado = {"sobre": False, "clic": False}

    def raton(evento, x, y, flags, parametro):
        x0, y0, x1, y1 = BOTON
        estado["sobre"] = x0 <= x <= x1 and y0 <= y <= y1
        if evento == cv2.EVENT_LBUTTONDOWN and estado["sobre"]:
            estado["clic"] = True

    cv2.namedWindow(ventana, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(ventana, raton)
    inicio, aceptada = time.monotonic(), False
    while True:
        cv2.imshow(ventana, dibujar_ventana(capas, time.monotonic() - inicio, estado["sobre"]))
        tecla = cv2.waitKey(15) & 0xFF
        if estado["clic"]:
            aceptada = True
            break
        if tecla == 27:
            break
        if cv2.getWindowProperty(ventana, cv2.WND_PROP_VISIBLE) < 1:
            break
    cv2.destroyWindow(ventana)
    return aceptada
