"""Genera el conjunto de datos del bloque C11: sit-and-reach por persona, anclado en datos reales.

Cada persona es un adulto REAL de la NHANES 2021-2023 (edad, sexo, altura y peso medidos).
Su resultado se sortea de la distribución REAL publicada para su sexo y edad, desplazada según
su IMC con una correlación medida en datos reales (cópula gaussiana):

  - sit_reach_cm: sit-and-reach en cm respecto a la punta de los pies (CHMS ciclo 5, Canadá);
    negativo si no llega y positivo si la supera. Correlación con el IMC medida en el conjunto
    de Kaggle.

Requisitos previos: haber ejecutado preparar_datos.py (correlación IMC - sit-and-reach).
Dependencias: numpy y pandas.
Uso (desde la raíz del repositorio):
    python "C11 - Datos y modelo/generar_dataset.py"
"""

from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

CARPETA = Path(__file__).resolve().parent
DEMO = CARPETA / "fuentes" / "DEMO_L.xpt"
BMX = CARPETA / "fuentes" / "BMX_L.xpt"
KAGGLE_LIMPIO = CARPETA / "datos" / "sit_and_reach_limpio.csv"
DESTINO = CARPETA / "datos" / "dataset_sintetico.csv"

SEMILLA = 2026
EDAD_MIN, EDAD_MAX = 20, 69
IMC_MIN = 15.0              # mismo criterio de plausibilidad que en preparar_datos.py
NORMAL = NormalDist()

# ---------------------------------------------------------------- sit-and-reach (CHMS)
# CHMS ciclo 5 (2016-2017), Hoffmann et al. 2019, Health Reports, tabla 3 (cm, escala CHMS)
CERO_CHMS = 26.0            # en el flexómetro de CHMS, tocar la punta de los pies = 26 cm
LIMITES_CHMS = (0.0, 60.0)  # recorrido físico del flexómetro (cm en su escala)
PERC_CHMS = (0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95)
EDADES_CHMS = (22, 27, 32, 37, 42, 47, 52, 57, 62, 67)     # centros de 20-24, ..., 65-69
CHMS = {
    1: [  # hombres
        (8.9, 11.7, 15.5, 18.7, 21.7, 24.6, 27.5, 30.4, 33.5, 37.2, 39.9),
        (8.8, 11.6, 15.4, 18.6, 21.6, 24.5, 27.4, 30.3, 33.4, 37.1, 39.7),
        (8.7, 11.5, 15.3, 18.4, 21.3, 24.2, 27.0, 29.9, 32.9, 36.6, 39.3),
        (8.6, 11.3, 15.1, 18.2, 21.0, 23.8, 26.5, 29.3, 32.3, 36.0, 38.6),
        (8.4, 11.1, 14.9, 17.8, 20.6, 23.3, 25.9, 28.6, 31.6, 35.2, 37.8),
        (8.2, 10.9, 14.6, 17.5, 20.1, 22.7, 25.3, 27.9, 30.7, 34.3, 36.9),
        (8.0, 10.7, 14.3, 17.1, 19.7, 22.1, 24.6, 27.1, 29.8, 33.4, 36.0),
        (7.8, 10.5, 14.0, 16.7, 19.2, 21.5, 23.9, 26.3, 28.9, 32.4, 35.1),
        (7.6, 10.3, 13.7, 16.4, 18.7, 20.9, 23.1, 25.5, 28.0, 31.4, 34.1),
        (7.4, 10.1, 13.4, 16.0, 18.2, 20.3, 22.4, 24.6, 27.1, 30.5, 33.1),
    ],
    0: [  # mujeres
        (14.4, 18.3, 22.9, 26.1, 28.7, 31.1, 33.5, 36.0, 38.8, 42.6, 45.7),
        (14.1, 17.9, 22.5, 25.8, 28.5, 31.1, 33.7, 36.2, 39.1, 42.9, 45.8),
        (13.8, 17.5, 22.0, 25.4, 28.3, 31.0, 33.7, 36.4, 39.3, 43.0, 45.7),
        (13.5, 17.0, 21.4, 24.8, 27.8, 30.7, 33.5, 36.2, 39.2, 42.8, 45.4),
        (13.0, 16.4, 20.8, 24.2, 27.3, 30.2, 33.1, 35.9, 38.8, 42.3, 44.8),
        (12.5, 15.8, 20.1, 23.5, 26.6, 29.6, 32.5, 35.4, 38.3, 41.7, 44.1),
        (12.0, 15.3, 19.6, 23.0, 26.1, 29.1, 32.0, 34.9, 37.8, 41.1, 43.5),
        (11.6, 14.9, 19.2, 22.6, 25.8, 28.8, 31.7, 34.6, 37.5, 40.9, 43.2),
        (11.3, 14.7, 19.1, 22.5, 25.7, 28.8, 31.7, 34.6, 37.6, 41.0, 43.4),
        (11.1, 14.5, 19.0, 22.6, 25.8, 28.9, 31.8, 34.7, 37.7, 41.3, 43.8),
    ],
}

def cuantil(p, edad, edades, percentiles, filas, limites):
    """Valor en el percentil p para una edad: interpola cada percentil publicado entre los
    centros de edad y, entre percentiles, en escala normal; fuera del rango publicado
    prolonga el último tramo y recorta a los límites físicos."""
    filas = np.asarray(filas, dtype=float)
    zs = np.array([NORMAL.inv_cdf(q) for q in percentiles])
    fila = np.array([np.interp(edad, edades, filas[:, k]) for k in range(len(percentiles))])
    z = NORMAL.inv_cdf(p)
    if z < zs[0]:
        valor = fila[0] + (fila[1] - fila[0]) / (zs[1] - zs[0]) * (z - zs[0])
    elif z > zs[-1]:
        valor = fila[-1] + (fila[-1] - fila[-2]) / (zs[-1] - zs[-2]) * (z - zs[-1])
    else:
        valor = np.interp(z, zs, fila)
    return float(np.clip(valor, *limites))


def leer_nhanes():
    """Adultos de 20 a 69 años, no embarazadas, con altura y peso medidos e IMC plausible."""
    demo = pd.read_sas(DEMO, format="xport")[["SEQN", "RIAGENDR", "RIDAGEYR", "RIDEXPRG"]]
    bmx = pd.read_sas(BMX, format="xport")[["SEQN", "BMXHT", "BMXWT"]]
    df = demo.merge(bmx, on="SEQN").dropna(subset=["BMXHT", "BMXWT"])
    df = df[df["RIDAGEYR"].between(EDAD_MIN, EDAD_MAX) & (df["RIDEXPRG"] != 1)]
    df = pd.DataFrame({"edad": df["RIDAGEYR"].astype(int),
                       "altura_cm": df["BMXHT"],
                       "peso_kg": df["BMXWT"],
                       "sexo": (df["RIAGENDR"] == 1).astype(int)})   # NHANES: 1 = hombre
    df["imc"] = df["peso_kg"] / (df["altura_cm"] / 100) ** 2
    return df[df["imc"] >= IMC_MIN].reset_index(drop=True)


def correlacion_kaggle():
    """Correlación IMC - sit-and-reach dentro de cada sexo en el conjunto real limpio."""
    k = pd.read_csv(KAGGLE_LIMPIO)
    k["imc"] = k["peso_kg"] / (k["altura_cm"] / 100) ** 2
    return {s: g["imc"].corr(g["sit_reach_cm"]) for s, g in k.groupby("sexo")}


def puntuacion_imc(df):
    """Posición del IMC de cada persona dentro de su sexo y década de edad, en escala normal."""
    grupo = df.groupby(["sexo", df["edad"] // 10])["imc"]
    rango = grupo.rank(method="first")
    n = grupo.transform("count")
    return ((rango - 0.5) / n).map(NORMAL.inv_cdf)


def sortear(df, rho, rng, funcion):
    """Cópula gaussiana: mezcla la posición del IMC (peso rho) con azar y lee el valor."""
    r = df["sexo"].map(rho)
    z = r * df["z_imc"] + np.sqrt(1 - r ** 2) * rng.standard_normal(len(df))
    return [funcion(NORMAL.cdf(zi), s, e) for zi, s, e in zip(z, df["sexo"], df["edad"])]


def generar():
    """Construye el conjunto: personas NHANES y su resultado de sit-and-reach."""
    rng = np.random.default_rng(SEMILLA)
    df = leer_nhanes()
    df["z_imc"] = puntuacion_imc(df)

    rho_sr = correlacion_kaggle()
    df["sit_reach_cm"] = [round(v - CERO_CHMS, 1) for v in sortear(
        df, rho_sr, rng, lambda p, s, e: cuantil(p, e, EDADES_CHMS, PERC_CHMS, CHMS[s], LIMITES_CHMS))]

    df[["altura_cm", "peso_kg"]] = df[["altura_cm", "peso_kg"]].round(1)
    info = {"rho_sit_reach": rho_sr}
    return df.drop(columns=["imc", "z_imc"]), info


def comprobar(df, info):
    """Medianas generadas por sexo y década, y correlación con el IMC."""
    print(f"personas: {len(df)}  (hombres {int(df['sexo'].sum())}, mujeres {int((1 - df['sexo']).sum())})")
    print(f"rho IMC usada (hombres, mujeres): {info['rho_sit_reach'][1]:.3f}, {info['rho_sit_reach'][0]:.3f}")
    print(df.groupby(["sexo", df["edad"] // 10 * 10])["sit_reach_cm"].median().round(1))
    imc = df["peso_kg"] / (df["altura_cm"] / 100) ** 2
    print("correlación IMC - sit_reach_cm:",
          {int(s): round(float(imc[g.index].corr(g["sit_reach_cm"])), 3) for s, g in df.groupby("sexo")})


if __name__ == "__main__":
    datos, info = generar()
    comprobar(datos, info)
    datos.to_csv(DESTINO, index=False)
    print(f"Guardado: {DESTINO.relative_to(CARPETA.parent)}")
