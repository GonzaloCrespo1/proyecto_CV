"""Prepara el conjunto de sit-and-reach de Kaggle (Korea Sports Promotion Foundation).

Se queda con las variables del perfil y la medida de sit-and-reach, elimina duplicados y
valores físicamente imposibles, y guarda un CSV limpio con nombres y codificación propios.
Del conjunto limpio solo se usa la correlación IMC - sit-and-reach (ver generar_dataset.py).

Uso (desde la raíz del repositorio):
    python "C11 - Datos y modelo/preparar_datos.py"
"""

from pathlib import Path

import pandas as pd

CARPETA = Path(__file__).resolve().parent
ORIGEN = CARPETA / "fuentes" / "bodyPerformanceKaggle.csv"
DESTINO = CARPETA / "datos" / "sit_and_reach_limpio.csv"

SIT_REACH_MIN, SIT_REACH_MAX = -30.0, 50.0   # cm; fuera de aquí, imposible
IMC_MIN = 15.0                               # por debajo: error de registro del peso


def preparar(ruta):
    """Lee el CSV original, lo limpia y devuelve el DataFrame limpio y un resumen."""
    df = pd.read_csv(ruta)
    resumen = {"originales": len(df)}

    df = df.drop_duplicates()                               # filas repetidas enteras
    resumen["duplicados"] = resumen["originales"] - len(df)

    df = df.rename(columns={"age": "edad", "height_cm": "altura_cm", "weight_kg": "peso_kg",
                            "sit and bend forward_cm": "sit_reach_cm"})
    df["sexo"] = (df["gender"] == "M").astype(int)          # 1 = hombre, 0 = mujer
    df = df[["edad", "altura_cm", "peso_kg", "sexo", "sit_reach_cm"]]

    imposible_sr = ~df["sit_reach_cm"].between(SIT_REACH_MIN, SIT_REACH_MAX)
    imc = df["peso_kg"] / (df["altura_cm"] / 100) ** 2
    imposible_imc = imc < IMC_MIN
    resumen["sit_reach_imposible"] = int(imposible_sr.sum())
    resumen["imc_imposible"] = int(imposible_imc.sum())

    df = df[~(imposible_sr | imposible_imc)]
    resumen["finales"] = len(df)
    return df, resumen


if __name__ == "__main__":
    limpio, resumen = preparar(ORIGEN)
    for clave, valor in resumen.items():
        print(f"{clave:<22}{valor:>6}")
    print(limpio.describe().round(1))
    print(limpio.groupby("sexo")["sit_reach_cm"].agg(["count", "mean", "std"]).round(1))
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    limpio.to_csv(DESTINO, index=False)
    print(f"Guardado: {DESTINO.relative_to(CARPETA.parent)}")
