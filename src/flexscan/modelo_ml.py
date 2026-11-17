"""Punto de enganche con el modelo de aprendizaje automático (parte de Gonzalo Crespo Comín).

FlexScan llama a `predecir_valor_ml(ruta_toma)` cuando la persona pide el análisis de flexibilidad y
enseña el valor devuelto junto a su medida experimental. Mientras el modelo no esté listo, la pantalla
muestra «valor_ml» con la etiqueta «pendiente del modelo».

PARA INTEGRAR EL MODELO (lo único que hay que tocar en este fichero):
  1. Escribir el cuerpo de `predecir_valor_ml`.
  2. Poner `MODELO_LISTO = True`.
No hace falta tocar ninguna pantalla ni `__main__.py`.
"""
import json
from pathlib import Path

MODELO_LISTO = False           # False: la pantalla enseña «valor_ml» pendiente. True: enseña el número devuelto.


def cargar_resumen(ruta_toma):
    """Lee `resumen.json` de la toma y lo devuelve como diccionario (ver docs/prompt_gonzalo.md)."""
    return json.loads((Path(ruta_toma) / "resumen.json").read_text(encoding="utf-8"))


def predecir_valor_ml(ruta_toma):
    """Valor del modelo para la toma guardada en `ruta_toma`, o None si todavía no hay modelo.

    `ruta_toma` es la carpeta de la toma (`datos/en_vivo/<usuario>/toma_AAAAMMDD_HHMMSS/`), que contiene
    `resumen.json` (medida, perfil, parámetros), `serie.csv` (distancia dedo-pie en el tiempo),
    `captura.png` y `grafica.png`. El valor debe darse en las mismas unidades que `medida_cm` (cm), para
    poder compararlos. Si el modelo devolviera otra cosa (por ejemplo una clase), hay que acordarlo antes.
    """
    # ---- AQUÍ VA EL MODELO ----------------------------------------------------------------------
    # resumen = cargar_resumen(ruta_toma)
    # perfil = resumen["perfil"]            # edad, sexo, altura_cm, peso_kg
    # medida = resumen["medida_cm"]         # medida experimental de FlexScan
    # return float(modelo.predict(...))
    # ---------------------------------------------------------------------------------------------
    return None
