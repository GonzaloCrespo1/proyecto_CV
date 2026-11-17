"""Escala de la imagen (píxeles por centímetro), guardada por la calibración con la hoja A4."""
import json
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
RUTA_ESCALA = RAIZ / "datos" / "escala.json"
RUTA_FOTO = RAIZ / "datos" / "escala_foto.jpg"
ANCHO_A4_CM = 21.0         # la hoja se coloca en vertical
ALTO_A4_CM = 29.7


def guardar_escala(px_por_cm, ancho_px, alto_px):
    """Guarda la escala y las medidas de la hoja en datos/escala.json."""
    RUTA_ESCALA.parent.mkdir(exist_ok=True)
    datos = {"px_por_cm": round(px_por_cm, 3), "ancho_hoja_px": ancho_px, "alto_hoja_px": alto_px,
             "fecha": time.strftime("%Y-%m-%d %H:%M:%S")}
    RUTA_ESCALA.write_text(json.dumps(datos, indent=2), encoding="utf-8")


def cargar_escala():
    """Devuelve los píxeles por centímetro guardados, o None si todavía no hay calibración."""
    if not RUTA_ESCALA.exists():
        return None
    return float(json.loads(RUTA_ESCALA.read_text(encoding="utf-8"))["px_por_cm"])


def escala_desde_hoja(ancho_px, alto_px):
    """Escala (px/cm) a partir del ancho y el alto de la hoja A4 en la imagen.

    Devuelve (escala, discrepancia): la media de las dos escalas y su diferencia relativa,
    que debe ser pequeña si la hoja está de frente.
    """
    por_ancho = ancho_px / ANCHO_A4_CM
    por_alto = alto_px / ALTO_A4_CM
    media = (por_ancho + por_alto) / 2
    return media, abs(por_ancho - por_alto) / media
