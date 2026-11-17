"""Ventana de teclas: qué hace cada tecla y cuáles funcionan en la fase actual (en verde).

No detiene el programa: se abre aparte, se actualiza sola al cambiar de fase y se cierra con su
botón, con Esc o con la tecla h. Se genera desde la tabla de teclas.py.
"""
import cv2
import numpy as np
from PIL import Image, ImageDraw

from flexscan import teclas as tk
from flexscan.instrucciones import AZUL, BLANCO, FONDO, GRIS, GRIS_CLARO, NARANJA, TURQUESA, _fuente

VENTANA = "FlexScan - Teclas"
ANCHO, ALTO = 1280, 720

VERDE, VERDE_OSC, VERDE_CLARO = (46, 138, 60), (30, 100, 44), (222, 243, 227)
APAGADO, APAGADO_TXT, APAGADO_BORDE = (244, 245, 247), (150, 158, 170), (222, 226, 232)
ETIQUETA_FASE = {tk.CALIBRACION: "CAL", tk.INICIO: "INI", tk.ACCESO: "ACC",
                 tk.PREPARACION: "PRE", tk.MEDIDA: "MED", tk.RESULTADO: "RES"}
GRUPOS = ((tk.USO, "Teclas del recorrido"), (tk.DEPURACION, "Teclas del equipo y de depuración"))

COL_X = (30, 650)
COL_ANCHO = 600
FILA_Y0, FILA_ALTO, FILA_PASO = 168, 52, 56
SEPARACION_PUNTOS = 24
BOTON = (490, 654, 790, 704)


def _dibujar_tecla(d, x, y, codigo, estado):
    fuente = _fuente(24, True)
    ancho = max(46, int(d.textlength(codigo, font=fuente)) + 24)
    color = VERDE if estado == tk.ACTIVA else (NARANJA if estado == tk.FALTA_FONDO else (176, 184, 194))
    d.rounded_rectangle((x, y + 2, x + ancho, y + 46), 10, fill=color)
    d.text((x + ancho / 2, y + 24), codigo, font=fuente, fill=BLANCO, anchor="mm")


NARANJA_CLARO = (255, 240, 222)


def _capa(fase, fondo_listo, sobre_boton, texto_boton):
    im = Image.new("RGB", (ANCHO, ALTO), FONDO)
    d = ImageDraw.Draw(im)
    # cabecera: título y fase actual
    d.rectangle((0, 0, ANCHO, 120), fill=AZUL)
    d.text((34, 10), "Teclas del programa", font=_fuente(44, True), fill=BLANCO)
    etiqueta = f"Estás en: {tk.NOMBRE_FASE[fase]}"
    fuente = _fuente(26, True)
    ancho = int(d.textlength(etiqueta, font=fuente)) + 36
    d.rounded_rectangle((ANCHO - 34 - ancho, 20, ANCHO - 34, 64), 22, fill=VERDE)
    d.text((ANCHO - 34 - ancho / 2, 42), etiqueta, font=fuente, fill=BLANCO, anchor="mm")
    d.text((34, 70), f"Fase actual: {tk.DESCRIPCION_FASE[fase]}.", font=_fuente(20), fill=(150, 214, 214))
    d.text((34, 94), "Las teclas en verde funcionan ahora mismo; las demás se activan en otras fases (puntos de la derecha).",
           font=_fuente(19), fill=BLANCO)

    for col, (tipo, titulo) in enumerate(GRUPOS):
        x0 = COL_X[col]
        d.text((x0 + 4, 134), titulo, font=_fuente(22, True), fill=AZUL)
        x_puntos = x0 + COL_ANCHO - 10 - SEPARACION_PUNTOS * len(tk.FASES) + SEPARACION_PUNTOS // 2
        for i, f in enumerate(tk.FASES):
            cx = x_puntos + i * SEPARACION_PUNTOS
            if f == fase:
                d.rounded_rectangle((cx - 13, 138, cx + 13, 155), 8, fill=VERDE)
            d.text((cx, 146), ETIQUETA_FASE[f], font=_fuente(12, True), fill=BLANCO if f == fase else GRIS,
                   anchor="mm")
        for fila, tecla in enumerate(t for t in tk.TECLAS if t.tipo == tipo):
            y = FILA_Y0 + fila * FILA_PASO
            estado = tk.estado_tecla(tecla, fase, fondo_listo)
            activa = estado == tk.ACTIVA
            falta = estado == tk.FALTA_FONDO
            d.rounded_rectangle((x0, y, x0 + COL_ANCHO, y + FILA_ALTO), 12,
                                fill=VERDE_CLARO if activa else (NARANJA_CLARO if falta else APAGADO),
                                outline=VERDE if activa else (NARANJA if falta else APAGADO_BORDE),
                                width=3 if (activa or falta) else 2)
            _dibujar_tecla(d, x0 + 10, y, tecla.codigo, estado)
            d.text((x0 + 76, y + 4), tecla.nombre, font=_fuente(19, True),
                   fill=AZUL if (activa or falta) else APAGADO_TXT)
            if activa or falta:
                ancho_n = int(d.textlength(tecla.nombre, font=_fuente(19, True)))
                etiqueta = "AHORA" if activa else "FALTA FONDO"
                ancho_e = 66 if activa else 96
                d.rounded_rectangle((x0 + 76 + ancho_n + 12, y + 6, x0 + 76 + ancho_n + 12 + ancho_e, y + 24), 9,
                                    fill=VERDE if activa else NARANJA)
                d.text((x0 + 76 + ancho_n + 12 + ancho_e / 2, y + 15), etiqueta, font=_fuente(12, True),
                       fill=BLANCO, anchor="mm")
            d.text((x0 + 76, y + 28), tecla.efecto, font=_fuente(15), fill=GRIS if (activa or falta) else APAGADO_TXT)
            for i, f in enumerate(tk.FASES):
                cx, cy = x_puntos + i * SEPARACION_PUNTOS, y + FILA_ALTO // 2
                if f in tecla.fases:
                    if f == fase:
                        d.ellipse((cx - 8, cy - 8, cx + 8, cy + 8), fill=VERDE)
                    else:
                        d.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=(168, 205, 205) if not activa else TURQUESA)
                else:
                    d.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill=GRIS_CLARO)

    # caja de ayuda en el hueco de la columna izquierda
    n_uso = sum(1 for t in tk.TECLAS if t.tipo == tk.USO)
    y = FILA_Y0 + n_uso * FILA_PASO
    d.rounded_rectangle((COL_X[0], y, COL_X[0] + COL_ANCHO, y + FILA_ALTO), 12, fill=(221, 240, 240),
                        outline=TURQUESA, width=2)
    d.text((COL_X[0] + 16, y + 4), "Esta ventana no detiene el programa", font=_fuente(19, True), fill=AZUL)
    d.text((COL_X[0] + 16, y + 28), "Se actualiza sola al cambiar de fase. Ciérrala con el botón, Esc o la tecla H.",
           font=_fuente(15), fill=AZUL)

    leyenda = "  ·  ".join(f"{ETIQUETA_FASE[f]} {tk.NOMBRE_FASE[f]}" for f in tk.FASES)
    d.text((ANCHO // 2, 634), "Punto: la tecla funciona en esa fase.   Naranja: falta el fondo aprendido.   " + leyenda,
           font=_fuente(14), fill=GRIS, anchor="mm")

    bx0, by0, bx1, by1 = BOTON
    d.rounded_rectangle((bx0, by0, bx1, by1), 16, fill=AZUL if sobre_boton else TURQUESA)
    d.text(((bx0 + bx1) // 2, (by0 + by1) // 2 - 1), texto_boton, font=_fuente(28, True), fill=BLANCO, anchor="mm")
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


class VentanaTeclas:
    """Ventana de teclas que convive con el programa (no lo detiene)."""

    def __init__(self):
        self.abierta = False
        self._capas = {}
        self._texto_boton = "Cerrar"
        self._sobre = False
        self._clic = False
        self._mostrado = None

    def _imagen(self, fase, fondo_listo):
        clave = (fase, fondo_listo, self._sobre, self._texto_boton)
        if clave not in self._capas:
            self._capas[clave] = _capa(fase, fondo_listo, self._sobre, self._texto_boton)
        return self._capas[clave]

    def _raton(self, evento, x, y, flags, parametro):
        x0, y0, x1, y1 = BOTON
        self._sobre = x0 <= x <= x1 and y0 <= y <= y1
        if evento == cv2.EVENT_LBUTTONDOWN and self._sobre:
            self._clic = True

    def abrir(self, fase, fondo_listo=False, arranque=False):
        if self.abierta:
            return
        self._texto_boton = "Entendido" if arranque else "Cerrar"
        self._sobre, self._clic, self._mostrado = False, False, None
        cv2.namedWindow(VENTANA, cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback(VENTANA, self._raton)
        self.abierta = True
        self.actualizar(fase, fondo_listo)

    def cerrar(self):
        if self.abierta:
            tk.cerrar_ventana(VENTANA)
            self.abierta = False

    def alternar(self, fase, fondo_listo=False):
        if self.abierta:
            self.cerrar()
        else:
            self.abrir(fase, fondo_listo)

    def actualizar(self, fase, fondo_listo=False):
        """Se llama en cada vuelta: redibuja solo si cambia la fase o el estado del botón."""
        if not self.abierta:
            return
        if self._mostrado is not None:                 # ya mostrada una vez: ¿la han cerrado con la X?
            try:
                if cv2.getWindowProperty(VENTANA, cv2.WND_PROP_VISIBLE) < 1:
                    self.abierta = False
                    return
            except cv2.error:
                self.abierta = False
                return
        if self._clic:
            self.cerrar()
            return
        clave = (fase, fondo_listo, self._sobre, self._texto_boton)
        if clave != self._mostrado:
            cv2.imshow(VENTANA, self._imagen(fase, fondo_listo))
            self._mostrado = clave
