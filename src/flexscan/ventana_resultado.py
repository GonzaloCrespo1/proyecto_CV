"""Ventana de resultado: aparece al terminar la medida y detiene el vídeo.

Enseña el resultado en centímetros y tres opciones: repetir la medida, obtener el análisis de flexibilidad
(comparación con el modelo de aprendizaje automático) y cerrar la sesión. Es una pantalla de diseño: no
cambia nada de cómo se mide.
"""
import cv2
import numpy as np
from PIL import Image, ImageDraw

from flexscan.instrucciones import AZUL, BLANCO, FONDO, GRIS, GRIS_CLARO, NARANJA, TURQUESA, TURQUESA_OSC, _fuente, \
    _texto_ajustado
from flexscan.pantalla_medida import texto_cm

VENTANA = "FlexScan - Resultado"
ANCHO, ALTO = 1280, 720
VERDE, ROJO = (30, 190, 80), (214, 48, 48)
NARANJA_OSC = (196, 98, 30)
GRIS_OFF = (176, 184, 194)

REPETIR, ANALISIS, CERRAR = "repetir", "analisis", "cerrar"
TARJETA = (50, 128, 650, 668)
BOTONES = {REPETIR: (690, 128, 1230, 298), ANALISIS: (690, 326, 1230, 526), CERRAR: (690, 604, 1230, 668)}


def _boton_repetir(d, caja, activo):
    x0, y0, x1, y1 = caja
    d.rounded_rectangle(caja, 20, fill=TURQUESA_OSC if activo else TURQUESA)
    d.text((x0 + 32, y0 + 22), "Repetir medida", font=_fuente(38, True), fill=BLANCO)
    d.rounded_rectangle((x1 - 84, y0 + 22, x1 - 28, y0 + 70), 10, fill=BLANCO)
    d.text((x1 - 56, y0 + 46), "N", font=_fuente(30, True), fill=TURQUESA_OSC, anchor="mm")
    fuente = _fuente(20)
    texto = "No muevas la cámara. Empieza otra medida con los mismos pasos: colocarte, pitido agudo, " \
            "estiramiento y pitido grave."
    for i, linea in enumerate(_texto_ajustado(d, texto, fuente, x1 - x0 - 64)):
        d.text((x0 + 32, y0 + 82 + i * 26), linea, font=fuente, fill=(222, 240, 240))


def _icono_analisis(d, cx, cy, color):
    """Icono de análisis: barras que crecen y una línea de tendencia."""
    for i, alto in enumerate((16, 30, 46)):
        x = cx - 30 + i * 22
        d.rounded_rectangle((x, cy + 24 - alto, x + 14, cy + 24), 3, fill=color)
    d.line([(cx - 34, cy + 4), (cx - 8, cy - 8), (cx + 10, cy - 2), (cx + 34, cy - 26)], fill=BLANCO, width=4, joint="curve")
    d.ellipse((cx + 28, cy - 32, cx + 40, cy - 20), fill=BLANCO)


def _boton_analisis(d, caja, activo, disponible):
    x0, y0, x1, y1 = caja
    fondo = (NARANJA_OSC if activo else NARANJA) if disponible else GRIS_OFF
    d.rounded_rectangle(caja, 20, fill=fondo)
    _icono_analisis(d, x0 + 70, y0 + 100, (255, 214, 176) if disponible else (230, 234, 238))
    d.text((x0 + 142, y0 + 24), "Obtener análisis", font=_fuente(38, True), fill=BLANCO)
    d.text((x0 + 142, y0 + 66), "de flexibilidad", font=_fuente(38, True), fill=BLANCO)
    d.rounded_rectangle((x1 - 84, y0 + 24, x1 - 28, y0 + 72), 10, fill=BLANCO)
    d.text((x1 - 56, y0 + 48), "A", font=_fuente(30, True), fill=fondo, anchor="mm")
    fuente = _fuente(20)
    texto = ("Compara tu medida con la de un modelo de aprendizaje automático." if disponible
             else "No disponible: no hay una medida que comparar.")
    for i, linea in enumerate(_texto_ajustado(d, texto, fuente, x1 - x0 - 170)):
        d.text((x0 + 142, y0 + 118 + i * 26), linea, font=fuente, fill=(255, 238, 222) if disponible else BLANCO)


def _boton_cerrar(d, caja, activo):
    x0, y0, x1, y1 = caja
    d.rounded_rectangle(caja, 16, fill=(226, 232, 239) if activo else BLANCO, outline=AZUL, width=3)
    d.text(((x0 + x1) // 2, (y0 + y1) // 2 - 1), "Cerrar sesión   (S)", font=_fuente(28, True), fill=AZUL, anchor="mm")


def _capa(ok, resultado, linea_usuario, activo):
    """Imagen de la ventana. `activo` es el botón sobre el que está el ratón (o None)."""
    im = Image.new("RGB", (ANCHO, ALTO), FONDO)
    d = ImageDraw.Draw(im)
    color = VERDE if ok else ROJO
    d.rectangle((0, 0, ANCHO, 92), fill=AZUL)
    d.ellipse((34, 18, 90, 74), fill=color)
    if ok:
        d.line([(47, 47), (58, 58), (78, 36)], fill=BLANCO, width=7, joint="curve")
    else:
        d.line([(50, 32), (74, 60)], fill=BLANCO, width=7)
        d.line([(50, 60), (74, 32)], fill=BLANCO, width=7)
    d.text((112, 12), "Medición realizada" if ok else "No se ha podido medir", font=_fuente(44, True), fill=BLANCO)
    d.text((114, 60), linea_usuario, font=_fuente(21), fill=(150, 214, 214))
    # tarjeta del resultado
    x0, y0, x1, y1 = TARJETA
    d.rounded_rectangle(TARJETA, 22, fill=BLANCO, outline=color, width=4)
    d.text(((x0 + x1) // 2, y0 + 50), "TU RESULTADO" if ok else "SIN RESULTADO", font=_fuente(26, True),
           fill=TURQUESA, anchor="mm")
    if ok:
        d.text(((x0 + x1) // 2, y0 + 190), texto_cm(resultado), font=_fuente(170, True), fill=AZUL, anchor="mm")
        d.text(((x0 + x1) // 2, y0 + 322), "centímetros", font=_fuente(34), fill=GRIS, anchor="mm")
        explica = ("La yema del dedo supera el punto del pie." if resultado >= 0
                   else "La yema del dedo no llega al punto del pie.")
        d.text(((x0 + x1) // 2, y0 + 392), explica, font=_fuente(28), fill=AZUL, anchor="mm")
        d.line((x0 + 50, y0 + 440, x1 - 50, y0 + 440), fill=GRIS_CLARO, width=2)
        d.text(((x0 + x1) // 2, y0 + 486), "La medida ya está guardada.", font=_fuente(22), fill=GRIS, anchor="mm")
    else:
        fuente = _fuente(30)
        texto = "No se ha detectado un estiramiento mantenido. Colócate de nuevo y repite la medida."
        for i, linea in enumerate(_texto_ajustado(d, texto, fuente, x1 - x0 - 100)):
            d.text(((x0 + x1) // 2, y0 + 190 + i * 44), linea, font=fuente, fill=AZUL, anchor="mm")
    _boton_repetir(d, BOTONES[REPETIR], activo == REPETIR)
    _boton_analisis(d, BOTONES[ANALISIS], activo == ANALISIS, ok)
    _boton_cerrar(d, BOTONES[CERRAR], activo == CERRAR)
    d.text((960, 568), "Esc: cerrar esta ventana", font=_fuente(19), fill=GRIS, anchor="mm")
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


def linea_de_usuario(usuario, perfil):
    """Texto de la cabecera con el nombre y los datos del perfil."""
    partes = [usuario.title()] if usuario else []
    if perfil:
        if perfil.get("edad") is not None:
            partes.append(f"{perfil['edad']} años")
        if perfil.get("sexo"):
            partes.append(str(perfil["sexo"]).capitalize())
        if perfil.get("altura_cm") is not None:
            partes.append(f"{perfil['altura_cm']} cm")
        if perfil.get("peso_kg") is not None:
            partes.append(f"{perfil['peso_kg']} kg")
    return "  ·  ".join(partes)


def _boton_en(x, y):
    for nombre, (x0, y0, x1, y1) in BOTONES.items():
        if x0 <= x <= x1 and y0 <= y <= y1:
            return nombre
    return None


def mostrar_resultado(medida_cm, usuario=None, perfil=None, ventana=VENTANA):
    """Muestra el resultado hasta que se elige una opción. `medida_cm` es None si no hubo medida.

    Devuelve REPETIR, ANALISIS o CERRAR; o None si se cierra la ventana con Esc o con la X.
    """
    ok = medida_cm is not None
    linea = linea_de_usuario(usuario, perfil)
    capas = {}
    estado = {"sobre": None, "clic": None}

    def raton(evento, x, y, flags, parametro):
        estado["sobre"] = _boton_en(x, y)
        if evento == cv2.EVENT_LBUTTONDOWN and estado["sobre"] is not None:
            estado["clic"] = estado["sobre"]

    cv2.namedWindow(ventana, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(ventana, raton)
    accion = None
    while True:
        if estado["sobre"] not in capas:
            capas[estado["sobre"]] = _capa(ok, medida_cm, linea, estado["sobre"])
        cv2.imshow(ventana, capas[estado["sobre"]])
        tecla = cv2.waitKey(20) & 0xFF
        elegido = estado["clic"]
        if tecla in (ord("n"), ord("N")):
            elegido = REPETIR
        elif tecla in (ord("a"), ord("A")):
            elegido = ANALISIS
        elif tecla in (ord("s"), ord("S")):
            elegido = CERRAR
        if elegido == ANALISIS and not ok:
            elegido, estado["clic"] = None, None             # sin medida no hay análisis
        if elegido is not None:
            accion = elegido
            break
        if tecla == 27 or cv2.getWindowProperty(ventana, cv2.WND_PROP_VISIBLE) < 1:
            break
    cv2.destroyWindow(ventana)
    return accion
