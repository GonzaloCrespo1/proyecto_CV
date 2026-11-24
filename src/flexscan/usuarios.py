"""Almacén de usuarios: guarda y comprueba la contraseña visual (secuencia de símbolos)."""
import hashlib
import hmac
import json
import os
from pathlib import Path

SIMBOLOS = ("circulos", "triangulo", "barras", "hexagono")
LONGITUD = 4
ITERACIONES = 100_000
RUTA = Path(__file__).resolve().parents[2] / "usuarios.json"


class ErrorUsuario(Exception):
    """Datos no válidos al registrar (nombre vacío, repetido o secuencia incorrecta)."""


def normalizar(nombre):
    """Quita espacios sobrantes y mayúsculas: 'Mateo  Gomez ' y 'mateo gomez' son el mismo usuario."""
    return " ".join(nombre.split()).lower()


def _hash(secuencia, sal):
    """Convierte la secuencia en un resumen irreversible (PBKDF2-SHA256 con sal)."""
    texto = ",".join(secuencia).encode("utf-8")
    return hashlib.pbkdf2_hmac("sha256", texto, sal, ITERACIONES)


def _leer(ruta):
    if not Path(ruta).exists():
        return {}
    with open(ruta, encoding="utf-8") as f:
        texto = f.read()
    return json.loads(texto) if texto.strip() else {}      # un fichero vacío es «sin usuarios»


def _escribir(datos, ruta):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)


def existe(nombre, ruta=RUTA):
    return normalizar(nombre) in _leer(ruta)


def validar(nombre, secuencia, ruta=RUTA):
    """Comprueba que se puede registrar ese usuario, sin guardar nada. Lanza ErrorUsuario si no."""
    clave = normalizar(nombre)
    if not clave:
        raise ErrorUsuario("el nombre está vacío")
    if len(clave.split()) < 2:
        raise ErrorUsuario("escribe nombre y apellido")
    if len(secuencia) != LONGITUD:
        raise ErrorUsuario(f"la secuencia debe tener {LONGITUD} símbolos")
    if any(s not in SIMBOLOS for s in secuencia):
        raise ErrorUsuario("la secuencia contiene un símbolo desconocido")
    if clave in _leer(ruta):
        raise ErrorUsuario("ese usuario ya existe")


def registrar(nombre, secuencia, ruta=RUTA):
    """Guarda un usuario nuevo. Lanza ErrorUsuario si algo no es válido."""
    validar(nombre, secuencia, ruta)
    clave = normalizar(nombre)
    datos = _leer(ruta)
    sal = os.urandom(16)
    datos[clave] = {"sal": sal.hex(), "hash": _hash(secuencia, sal).hex()}
    _escribir(datos, ruta)


def verificar(nombre, secuencia, ruta=RUTA):
    """True si la secuencia coincide con la registrada. Usuario inexistente -> False."""
    registro = _leer(ruta).get(normalizar(nombre))
    if registro is None:
        return False
    esperado = bytes.fromhex(registro["hash"])
    obtenido = _hash(secuencia, bytes.fromhex(registro["sal"]))
    return hmac.compare_digest(esperado, obtenido)