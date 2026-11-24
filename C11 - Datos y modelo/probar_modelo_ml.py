"""Prueba sin cámara de src/flexscan/modelo_ml.py (punto de enganche del modelo con FlexScan).

Crea tomas de prueba en una carpeta temporal, con perfiles inventados, y comprueba que
predecir_valor_ml devuelve un float en cm (o None si la toma no tiene perfil) y que tarda menos de 1 s.

Uso (desde la raíz del repositorio):
    python "C11 - Datos y modelo/probar_modelo_ml.py"
"""
import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from flexscan.modelo_ml import MODELO_LISTO, predecir_valor_ml, sigma_cm   # noqa: E402

PERFILES = [   # inventados: perfil -> qué se espera ver
    {"edad": 20, "sexo": "mujer", "altura_cm": 165, "peso_kg": 58},
    {"edad": 20, "sexo": "hombre", "altura_cm": 180, "peso_kg": 75},
    {"edad": 65, "sexo": "hombre", "altura_cm": 172, "peso_kg": 95},
    None,      # toma sin perfil: debe devolver None
]


def crear_toma(carpeta, perfil):
    carpeta.mkdir()
    resumen = {"estado": "terminada", "medida_cm": 0.0}
    if perfil is not None:
        resumen["perfil"] = perfil
    (carpeta / "resumen.json").write_text(json.dumps(resumen), encoding="utf-8")
    return carpeta


if __name__ == "__main__":
    print(f"MODELO_LISTO = {MODELO_LISTO}")
    with tempfile.TemporaryDirectory() as tmp:
        for i, perfil in enumerate(PERFILES):
            toma = crear_toma(Path(tmp) / f"toma_{i}", perfil)
            inicio = time.perf_counter()
            valor = predecir_valor_ml(toma)
            ms = (time.perf_counter() - inicio) * 1000
            print(f"{str(perfil):<70} -> {valor!r:>6} cm   ({ms:.0f} ms)")
    print(f"sigma = {sigma_cm():.2f} cm")
