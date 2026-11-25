"""Ventana del análisis de flexibilidad: animación de análisis y comparación.

Durante unos segundos se ve un núcleo que procesa los datos de la persona (perfil y medida), sin representar
ningún tipo de modelo concreto; después se enseñan juntos el valor de la medida experimental y el valor del modelo. Mientras el modelo no esté listo, el valor del
modelo aparece como «valor_ml» con la etiqueta «pendiente del modelo». Con el modelo listo, encima de los dos
valores sale el veredicto (poco flexible, en la media o muy flexible) según z = (medida - esperado) / sigma.
"""
import math
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw

from flexscan.instrucciones import AZUL, BLANCO, GRIS_CLARO, NARANJA, TURQUESA, _fuente
from flexscan.modelo_ml import veredicto
from flexscan.pantalla_medida import texto_cm

VENTANA = "FlexScan - Analisis de flexibilidad"
ANCHO, ALTO = 1280, 720
DURACION_ANALISIS = 4.5          # segundos de animación antes de enseñar los dos valores
FONDO_OSC = (11, 24, 42)
TURQUESA_CL, AZUL_LINEA = (120, 225, 225), (48, 84, 118)
BOTON = (480, 640, 800, 704)


def _bgr(rgb):
    return (rgb[2], rgb[1], rgb[0])


NUCLEO = (640, 268)                       # centro de la animación: un núcleo que procesa los datos
ENTRADAS = {"Tu perfil": (250, 214), "Tu medida": (250, 322)}      # fichas de datos de entrada
SALIDA = (1030, 268)                      # ficha de salida: valor del modelo
R_NUCLEO = 92
NARANJA_CL = (255, 190, 140)
COLOR_VEREDICTO = {"POCO FLEXIBLE": NARANJA, "EN LA MEDIA": TURQUESA_CL, "MUY FLEXIBLE": (120, 215, 130)}
VEREDICTO = (150, 404, 1130, 470)          # franja del veredicto, encima de las dos tarjetas


def _ficha(d, centro, texto, color, ancho=190):
    x, y = centro
    d.rounded_rectangle((x - ancho // 2, y - 27, x + ancho // 2, y + 27), 27, fill=(20, 40, 66), outline=color, width=3)
    d.text((x, y - 1), texto, font=_fuente(24, True), fill=BLANCO, anchor="mm")


def _tarjeta(d, caja, titulo, valor, unidad, color, etiqueta=None, pequeno=False, compacta=False):
    x0, y0, x1, y1 = caja
    d.rounded_rectangle(caja, 20, fill=(20, 40, 66), outline=color, width=3)
    if compacta:                                   # versión baja, para dejar sitio al veredicto
        d.text(((x0 + x1) // 2, y0 + 26), titulo, font=_fuente(22, True), fill=color, anchor="mm")
        d.text(((x0 + x1) // 2, y0 + 78), valor, font=_fuente(66, True), fill=BLANCO, anchor="mm")
        d.text(((x0 + x1) // 2, y0 + 127), unidad, font=_fuente(22), fill=GRIS_CLARO, anchor="mm")
        return
    d.text(((x0 + x1) // 2, y0 + 34), titulo, font=_fuente(25, True), fill=color, anchor="mm")
    d.text(((x0 + x1) // 2, y0 + 96), valor, font=_fuente(64 if pequeno else 88, True), fill=BLANCO, anchor="mm")
    if unidad:
        d.text(((x0 + x1) // 2, y0 + 158), unidad, font=_fuente(26), fill=GRIS_CLARO, anchor="mm")
    if etiqueta:
        w = int(d.textlength(etiqueta, font=_fuente(19, True))) + 30
        cx = (x0 + x1) // 2
        d.rounded_rectangle((cx - w // 2, y1 - 40, cx + w // 2, y1 - 10), 15, fill=NARANJA)
        d.text((cx, y1 - 25), etiqueta, font=_fuente(19, True), fill=BLANCO, anchor="mm")


def _base(medida_cm, valor_ml, modelo_listo, fase, puntos, sobre):
    """Parte fija de la ventana. fase: 'analizando' o 'listo'."""
    im = Image.new("RGB", (ANCHO, ALTO), FONDO_OSC)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, ANCHO, 92), fill=(8, 18, 32))
    d.text((34, 10), "Análisis de flexibilidad", font=_fuente(46, True), fill=BLANCO)
    d.text((36, 62), "Comparación de tu medida con un modelo de aprendizaje automático", font=_fuente(21),
           fill=TURQUESA_CL)
    for texto, centro in ENTRADAS.items():
        _ficha(d, centro, texto, TURQUESA_CL)
    _ficha(d, SALIDA, "Valor del modelo", NARANJA_CL, ancho=230)
    if fase == "analizando":
        d.text((ANCHO // 2, 480), "Analizando" + "." * puntos, font=_fuente(40, True), fill=BLANCO, anchor="mm")
        d.text((ANCHO // 2, 530), "Se estudian tu perfil y tu medida", font=_fuente(24), fill=GRIS_CLARO,
               anchor="mm")
        d.rounded_rectangle((340, 590, 940, 606), 8, fill=(30, 54, 84))
    elif modelo_listo and valor_ml is not None:
        _veredicto(d, medida_cm, valor_ml)
        _tarjeta(d, (150, 480, 610, 632), "TU MEDIDA EXPERIMENTAL", texto_cm(medida_cm), "cm", TURQUESA_CL,
                 compacta=True)
        _tarjeta(d, (670, 480, 1130, 632), "VALOR ESPERADO PARA TU PERFIL", texto_cm(valor_ml), "cm",
                 (255, 190, 140), compacta=True)
    else:
        _tarjeta(d, (150, 432, 610, 622), "TU MEDIDA EXPERIMENTAL", texto_cm(medida_cm), "cm", TURQUESA_CL)
        _tarjeta(d, (670, 432, 1130, 622), "MODELO DE APRENDIZAJE AUTOMÁTICO", "valor_ml", None,
                 (255, 190, 140), etiqueta="PENDIENTE DEL MODELO", pequeno=True)
    if fase != "analizando":
        bx0, by0, bx1, by1 = BOTON
        d.rounded_rectangle(BOTON, 16, fill=AZUL if sobre else TURQUESA, outline=TURQUESA_CL if sobre else None, width=2)
        d.text(((bx0 + bx1) // 2, (by0 + by1) // 2 - 1), "Volver", font=_fuente(30, True), fill=BLANCO, anchor="mm")
    img = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
    for y in range(140, 400, 26):                                 # fondo de puntos tenues
        for x in range(160, 1130, 26):
            cv2.circle(img, (x, y), 1, _bgr((26, 48, 76)), -1)
    for centro in ENTRADAS.values():                              # trayectos de los datos hacia el núcleo
        cv2.line(img, (centro[0] + 95, centro[1]), (NUCLEO[0] - R_NUCLEO, NUCLEO[1]), _bgr(AZUL_LINEA), 1, cv2.LINE_AA)
    cv2.line(img, (NUCLEO[0] + R_NUCLEO, NUCLEO[1]), (SALIDA[0] - 115, SALIDA[1]), _bgr(AZUL_LINEA), 1, cv2.LINE_AA)
    return img


def _veredicto(d, medida_cm, valor_ml):
    """Franja con la categoría (color según el veredicto) y, debajo, z y la diferencia en cm."""
    z, categoria = veredicto(medida_cm, valor_ml)
    color = COLOR_VEREDICTO[categoria]
    x0, y0, x1, y1 = VEREDICTO
    d.rounded_rectangle(VEREDICTO, 18, fill=(20, 40, 66), outline=color, width=3)
    d.text(((x0 + x1) // 2, y0 + 22), categoria, font=_fuente(32, True), fill=color, anchor="mm")
    dif = medida_cm - valor_ml
    lado = "por encima de" if dif > 0 else "por debajo de" if dif < 0 else "justo en"
    texto_z = f"{z:+.2f}".replace("-", "−").replace(".", ",")
    detalle = f"z = {texto_z}  ·  {abs(dif):.1f} cm {lado} lo esperado para tu perfil".replace(".", ",")
    d.text(((x0 + x1) // 2, y0 + 50), detalle, font=_fuente(20), fill=GRIS_CLARO, anchor="mm")


def _anillo(img, radio, t, velocidad, color, grosor, arcos=3):
    """Anillo discontinuo que gira alrededor del núcleo."""
    inicio = (t * velocidad) % 360
    for k in range(arcos):
        a0 = inicio + k * 360 / arcos
        cv2.ellipse(img, NUCLEO, (radio, radio), 0, a0, a0 + 360 / arcos * 0.62, _bgr(color), grosor, cv2.LINE_AA)


def _particulas(img, a, b, t, ritmo, n, color):
    """Pequeños puntos que viajan de a a b, como datos que fluyen."""
    for k in range(n):
        f = (t * ritmo + k / n) % 1.0
        x = int(a[0] + (b[0] - a[0]) * f)
        y = int(a[1] + (b[1] - a[1]) * f)
        cola = max(0.0, f - 0.07)
        cv2.line(img, (int(a[0] + (b[0] - a[0]) * cola), int(a[1] + (b[1] - a[1]) * cola)), (x, y), _bgr(color), 2, cv2.LINE_AA)
        cv2.circle(img, (x, y), 4, _bgr((235, 255, 255)), -1, cv2.LINE_AA)


def _animar(img, t, listo):
    """Dibuja encima el núcleo que procesa los datos: anillos que giran, pulso y datos que fluyen."""
    ritmo = 0.35 if listo else 0.8
    for centro in ENTRADAS.values():
        _particulas(img, (centro[0] + 95, centro[1]), (NUCLEO[0] - R_NUCLEO, NUCLEO[1]), t, ritmo, 4, TURQUESA)
    _particulas(img, (NUCLEO[0] + R_NUCLEO, NUCLEO[1]), (SALIDA[0] - 115, SALIDA[1]), t, ritmo, 4, NARANJA)
    velocidad = 40 if listo else 130
    _anillo(img, R_NUCLEO, t, velocidad, TURQUESA, 3)
    _anillo(img, R_NUCLEO - 26, t, -velocidad * 1.4, (170, 245, 245), 2, 4)
    _anillo(img, R_NUCLEO - 52, t, velocidad * 2.0, NARANJA_CL, 2, 2)
    pulso = 0.5 + 0.5 * math.sin(t * (2.2 if listo else 5.0))
    cv2.circle(img, NUCLEO, int(20 + 6 * pulso), _bgr((18, 38, 63)), -1, cv2.LINE_AA)
    cv2.circle(img, NUCLEO, int(20 + 6 * pulso), _bgr(TURQUESA), 3, cv2.LINE_AA)
    cv2.circle(img, NUCLEO, int(7 + 3 * pulso), _bgr((235, 255, 255)), -1, cv2.LINE_AA)


def dibujar_analisis(medida_cm, valor_ml, modelo_listo, t, sobre=False, capas=None):
    """Imagen de la ventana en el instante t (s). `capas` es una caché opcional de las partes fijas."""
    listo = t >= DURACION_ANALISIS
    puntos = int(t * 2.5) % 4
    clave = ("listo", sobre) if listo else ("analizando", puntos)
    if capas is not None and clave in capas:
        img = capas[clave].copy()
    else:
        img = _base(medida_cm, valor_ml, modelo_listo, clave[0], puntos, sobre)
        if capas is not None:
            capas[clave] = img.copy()
    _animar(img, t, listo)
    if not listo:                                                # barra de progreso
        ancho = int(600 * min(1.0, t / DURACION_ANALISIS))
        cv2.rectangle(img, (340, 590), (340 + ancho, 606), _bgr(TURQUESA), -1, cv2.LINE_AA)
    return img


def mostrar_analisis(medida_cm, valor_ml=None, modelo_listo=False, ventana=VENTANA):
    """Muestra el análisis hasta que se pulsa «Volver» (o Esc, o se cierra la ventana)."""
    capas = {}
    estado = {"sobre": False, "clic": False}

    def raton(evento, x, y, flags, parametro):
        x0, y0, x1, y1 = BOTON
        estado["sobre"] = x0 <= x <= x1 and y0 <= y <= y1
        if evento == cv2.EVENT_LBUTTONDOWN and estado["sobre"]:
            estado["clic"] = True

    cv2.namedWindow(ventana, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(ventana, raton)
    inicio = time.monotonic()
    while True:
        t = time.monotonic() - inicio
        cv2.imshow(ventana, dibujar_analisis(medida_cm, valor_ml, modelo_listo, t, estado["sobre"], capas))
        tecla = cv2.waitKey(25) & 0xFF
        listo = t >= DURACION_ANALISIS
        if not listo:
            estado["clic"] = False                    # un clic durante la animación no cuenta
        if tecla == 27 or (listo and (estado["clic"] or tecla in (13, 32, ord("v"), ord("V")))):
            break
        if cv2.getWindowProperty(ventana, cv2.WND_PROP_VISIBLE) < 1:
            break
    cv2.destroyWindow(ventana)
