"""Perfil de cada persona (edad, sexo, altura y peso): ventana para pedirlo y guardado.

Se guarda en datos/en_vivo/<usuario>/perfil.json, junto a las carpetas de sus tomas.
"""
import json
import time

import cv2
import numpy as np

from flexscan import usuarios
from flexscan.escala import RAIZ
from flexscan.registro import _ascii, _dentro

CARPETA = RAIZ / "datos" / "en_vivo"
SEXOS = ("hombre", "mujer")
RANGOS = {"edad": (10, 100), "altura_cm": (100, 220), "peso_kg": (30, 200)}   # límites admitidos
NOMBRES = {"edad": "la edad", "altura_cm": "la altura", "peso_kg": "el peso"}
AYUDAS = {"edad": "Edad: entre 10 y 100 anios", "altura_cm": "Altura: entre 100 y 220 cm",
          "peso_kg": "Peso: entre 30 y 200 kg"}      # se muestra en rojo para la casilla activa
MAX_DIGITOS = 3

ANCHO, ALTO = 700, 430
CAJAS = {"edad": (50, 90, 330, 130), "altura_cm": (50, 180, 330, 220), "peso_kg": (370, 180, 650, 220)}
BOTONES_SEXO = {"hombre": (370, 90, 500, 130), "mujer": (520, 90, 650, 130)}
BOTON_ACEPTAR = (50, 350, 330, 400)
BOTON_CANCELAR = (370, 350, 650, 400)
ORDEN = ("edad", "altura_cm", "peso_kg")

AZUL_OSCURO = (63, 38, 18)
VERDE = (46, 138, 60)
ROJO = (79, 52, 192)
GRIS = (240, 236, 232)
BLANCO = (255, 255, 255)
FUENTE = cv2.FONT_HERSHEY_SIMPLEX


class ErrorPerfil(Exception):
    """Datos personales no válidos (vacíos o fuera de rango)."""


def carpeta_usuario(nombre, carpeta=CARPETA):
    """Carpeta de una persona: su nombre normalizado ('Mateo ' y 'mateo' son la misma)."""
    limpio = "".join(c if c.isalnum() or c in "-_" else "_" for c in usuarios.normalizar(nombre))
    return carpeta / limpio


def validar_perfil(edad, sexo, altura_cm, peso_kg):
    """Devuelve el perfil como diccionario con números enteros. Lanza ErrorPerfil si no es válido."""
    if sexo not in SEXOS:
        raise ErrorPerfil("elige el sexo")
    perfil = {"edad": edad, "sexo": sexo, "altura_cm": altura_cm, "peso_kg": peso_kg}
    for campo, (minimo, maximo) in RANGOS.items():
        try:
            valor = int(perfil[campo])
        except (TypeError, ValueError):
            raise ErrorPerfil(f"escribe {NOMBRES[campo]}") from None
        if not minimo <= valor <= maximo:
            raise ErrorPerfil(f"{NOMBRES[campo]} debe estar entre {minimo} y {maximo}")
        perfil[campo] = valor
    return perfil


def guardar_perfil(nombre, perfil, carpeta=CARPETA):
    """Guarda perfil.json en la carpeta de la persona (sobrescribe) y devuelve su ruta."""
    destino = carpeta_usuario(nombre, carpeta)
    destino.mkdir(parents=True, exist_ok=True)
    datos = {"usuario": usuarios.normalizar(nombre), **perfil, "fecha": time.strftime("%Y-%m-%d %H:%M:%S")}
    ruta = destino / "perfil.json"
    ruta.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")
    return ruta


def cargar_perfil(nombre, carpeta=CARPETA):
    """Devuelve el perfil guardado de esa persona, o None si todavía no tiene."""
    ruta = carpeta_usuario(nombre, carpeta) / "perfil.json"
    if not ruta.exists():
        return None
    return json.loads(ruta.read_text(encoding="utf-8"))


class FormularioPerfil:
    """Estado de la ventana de datos personales (campos, campo activo, mensaje) y su dibujo."""

    def __init__(self, nombre):
        self.nombre = nombre
        self.texto = {campo: "" for campo in ORDEN}
        self.sexo = None
        self.activo = ORDEN[0]
        self.mensaje = ""
        self.perfil = None
        self.resultado = None                 # None mientras sigue abierto; luego "aceptado" o "cancelado"

    def escribir(self, tecla):
        """Recibe el código de una tecla (lo que devuelve waitKey & 0xFF)."""
        if tecla == 8:                                        # retroceso
            self.texto[self.activo] = self.texto[self.activo][:-1]
        elif tecla == 9:                                      # tabulador: siguiente campo
            self.activo = ORDEN[(ORDEN.index(self.activo) + 1) % len(ORDEN)]
        elif tecla == 13:                                     # intro
            self.aceptar()
        elif tecla == 27:                                     # escape
            self.resultado = "cancelado"
        elif ord("0") <= tecla <= ord("9") and len(self.texto[self.activo]) < MAX_DIGITOS:
            self.texto[self.activo] += chr(tecla)

    def pulsar(self, x, y):
        """Recibe un clic del ratón."""
        for campo, rect in CAJAS.items():
            if _dentro(x, y, rect):
                self.activo = campo
                return
        for sexo, rect in BOTONES_SEXO.items():
            if _dentro(x, y, rect):
                self.sexo = sexo
                self.mensaje = ""
                return
        if _dentro(x, y, BOTON_ACEPTAR):
            self.aceptar()
        elif _dentro(x, y, BOTON_CANCELAR):
            self.resultado = "cancelado"

    def aceptar(self):
        """Valida los datos; si algo no es válido, deja el motivo en el mensaje."""
        try:
            self.perfil = validar_perfil(self.texto["edad"], self.sexo,
                                         self.texto["altura_cm"], self.texto["peso_kg"])
        except ErrorPerfil as error:
            texto = _ascii(str(error))
            self.mensaje = texto[:1].upper() + texto[1:]
        else:
            self.resultado = "aceptado"

    def dibujar(self):
        """Devuelve la imagen de la ventana en su estado actual."""
        lienzo = np.full((ALTO, ANCHO, 3), GRIS, np.uint8)
        cv2.rectangle(lienzo, (0, 0), (ANCHO, 50), AZUL_OSCURO, -1)
        cv2.putText(lienzo, _ascii(f"Datos personales: {self.nombre}"), (20, 34), FUENTE, 0.8, BLANCO, 2)

        etiquetas = {"edad": ("Edad (anios):", (50, 82)), "altura_cm": ("Altura (cm):", (50, 172)),
                     "peso_kg": ("Peso (kg):", (370, 172))}
        for campo, (texto, pos) in etiquetas.items():
            cv2.putText(lienzo, texto, pos, FUENTE, 0.55, AZUL_OSCURO, 1)
            rect = CAJAS[campo]
            cv2.rectangle(lienzo, rect[:2], rect[2:], BLANCO, -1)
            activo = campo == self.activo
            cv2.rectangle(lienzo, rect[:2], rect[2:], VERDE if activo else AZUL_OSCURO, 4 if activo else 2)
            cursor = "_" if activo else ""
            cv2.putText(lienzo, self.texto[campo] + cursor, (rect[0] + 12, rect[1] + 30), FUENTE, 0.9,
                        AZUL_OSCURO, 2)

        cv2.putText(lienzo, "Sexo:", (370, 82), FUENTE, 0.55, AZUL_OSCURO, 1)
        for sexo, rect in BOTONES_SEXO.items():
            elegido = sexo == self.sexo
            cv2.rectangle(lienzo, rect[:2], rect[2:], AZUL_OSCURO if elegido else BLANCO, -1)
            cv2.rectangle(lienzo, rect[:2], rect[2:], AZUL_OSCURO, 2)
            texto = sexo.capitalize()
            (ancho, alto), _ = cv2.getTextSize(texto, FUENTE, 0.65, 2)
            cx, cy = (rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2
            cv2.putText(lienzo, texto, (cx - ancho // 2, cy + alto // 2), FUENTE, 0.65,
                        BLANCO if elegido else AZUL_OSCURO, 2)

        cv2.putText(lienzo, AYUDAS[self.activo], (50, 255), FUENTE, 0.65, ROJO, 2)
        cv2.putText(lienzo, "Tab: cambiar de campo    Intro: aceptar    Esc: cancelar", (50, 288), FUENTE,
                    0.5, (120, 120, 120), 1)
        if self.mensaje:
            cv2.putText(lienzo, "! " + _ascii(self.mensaje), (50, 328), FUENTE, 0.65, ROJO, 2)
        for rect, texto, fondo in ((BOTON_ACEPTAR, "Aceptar", VERDE), (BOTON_CANCELAR, "Cancelar", ROJO)):
            cv2.rectangle(lienzo, rect[:2], rect[2:], fondo, -1)
            (ancho, alto), _ = cv2.getTextSize(texto, FUENTE, 0.65, 2)
            cx, cy = (rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2
            cv2.putText(lienzo, texto, (cx - ancho // 2, cy + alto // 2), FUENTE, 0.65, BLANCO, 2)
        return lienzo


def pedir_perfil(nombre):
    """Abre la ventana de datos personales. Devuelve el perfil (dict) o None si se cancela."""
    formulario = FormularioPerfil(nombre)
    ventana = "FlexScan - Datos personales"
    cv2.namedWindow(ventana)

    def raton(evento, x, y, flags, parametro):
        if evento == cv2.EVENT_LBUTTONDOWN:
            formulario.pulsar(x, y)

    cv2.setMouseCallback(ventana, raton)
    while formulario.resultado is None:
        cv2.imshow(ventana, formulario.dibujar())
        formulario.escribir(cv2.waitKey(30) & 0xFF)
        if cv2.getWindowProperty(ventana, cv2.WND_PROP_VISIBLE) < 1:
            formulario.resultado = "cancelado"           # se cerró la ventana con la X
    cv2.destroyWindow(ventana)
    return formulario.perfil if formulario.resultado == "aceptado" else None
