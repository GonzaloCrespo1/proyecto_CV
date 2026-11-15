"""Genera el conjunto de datos del bloque C11: tres ejercicios por persona, anclados en datos reales.

Cada persona es un adulto REAL de la NHANES 2021-2023 (edad, sexo, altura y peso medidos).
Para cada ejercicio se sortea su resultado de la distribución REAL publicada para su sexo y
edad, desplazada según su IMC con una correlación medida en datos reales (cópula gaussiana):

  - sit_reach_cm: sit-and-reach en cm respecto a la punta de los pies (CHMS ciclo 5, Canadá);
    correlación con el IMC medida en el conjunto de Kaggle.
  - apertura_piernas_grados: ángulo entre las dos piernas (abducción derecha + izquierda de
    NHANES I, 1971-75); correlación con el IMC medida en los propios datos de NHANES I.
  - elevacion_brazo_grados: flexión activa de hombro de pie, 0 = brazo junto al cuerpo
    (Gill et al. 2020, Australia); sin efecto del IMC (no hay datos que lo cuantifiquen).

Los tres ejercicios se sortean de forma independiente dentro de cada perfil: cada uno tendrá
su propio modelo, así que no hace falta suponer cómo se relacionan entre sí.

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
NHANES1 = CARPETA / "fuentes" / "DU4111.txt"
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

# ---------------------------------------------------------------- elevación de brazo (Gill)
# Gill et al. 2020, BMC Musculoskeletal Disorders, tabla 1: flexión activa del hombro derecho,
# de pie, con inclinómetro; mediana y rango intercuartílico (P25, P50, P75) en grados.
PERC_GILL = (0.25, 0.50, 0.75)
EDADES_GILL = (22, 27, 32, 37, 42, 47, 52, 57, 62, 67)
GILL = {
    1: [(170, 179.0, 180), (160, 164.0, 174), (160, 170.0, 177), (160, 168.0, 176), (156, 166.0, 174),
        (160, 168.0, 176), (160, 170.0, 176), (150, 160.0, 171), (150, 160.0, 170), (144, 156.1, 162)],
    0: [(160, 165.8, 174), (155, 170.0, 180), (156, 166.3, 173), (158, 168.0, 180), (156, 164.0, 176),
        (150, 160.0, 170), (150, 160.0, 170), (149, 160.0, 170), (140, 150.0, 163), (144, 152.0, 162)],
}
LIMITES_BRAZO = (0.0, 180.0)

# ---------------------------------------------------------------- apertura de piernas (NHANES I)
# NHANES I (1971-75), fichero 4111: abducción de cadera derecha (col. 341-343) e izquierda
# (col. 354-356), tumbado; se registra 90 + abducción (90 = pierna recta). 888 = sin dato.
PERC_PIERNAS = (0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95)
DECADAS_NHANES1 = (25, 35, 45, 55, 65, 75)                  # bordes 25-34, ..., 65-74
CENTROS_NHANES1 = (29.5, 39.5, 49.5, 59.5, 69.5)
LIMITES_PIERNAS = (15.0, 180.0)   # mínimo observado en NHANES I: 15°


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


def suavizar(edades, filas):
    """Ajusta, para cada percentil, una parábola en la edad. Los grupos publicados son pequeños
    (Gill: 55-170 personas; NHANES I: 135-224) y sus percentiles saltan de un grupo a otro."""
    filas = np.asarray(filas, dtype=float)
    return np.column_stack([np.polyval(np.polyfit(edades, filas[:, k], 2), edades)
                            for k in range(filas.shape[1])])


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


def leer_nhanes1():
    """Apertura de piernas (abducción dcha. + izda.) de NHANES I: percentiles por sexo y década
    de edad, y correlación con el IMC dentro de cada sexo."""
    columnas = {"sexo": (104, 104), "edad": (144, 145), "peso": (260, 264),
                "altura": (266, 269), "abd_d": (341, 343), "abd_i": (354, 356)}
    d = pd.read_fwf(NHANES1, colspecs=[(a - 1, b) for a, b in columnas.values()],
                    names=list(columnas), header=None, dtype=str).apply(pd.to_numeric, errors="coerce")
    d = d[(d["abd_d"] <= 180) & (d["abd_i"] <= 180)]                  # quita 888 y vacíos
    d["apertura"] = (d["abd_d"] - 90) + (d["abd_i"] - 90)
    d["sexo"] = (d["sexo"] == 1).astype(int)                           # NHANES I: 1 = hombre
    d["imc"] = (d["peso"] / 100) / (d["altura"] / 1000) ** 2           # kg·100 y cm·10
    d["decada"] = pd.cut(d["edad"], DECADAS_NHANES1, right=False)
    tablas, rho = {}, {}
    for s, g in d.groupby("sexo"):
        tablas[s] = suavizar(CENTROS_NHANES1,
                             g.groupby("decada", observed=True)["apertura"].quantile(PERC_PIERNAS).unstack().values)
        rho[s] = g["imc"].corr(g["apertura"])
    return tablas, rho, len(d)


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
    """Construye el conjunto: personas NHANES y un resultado por ejercicio."""
    rng = np.random.default_rng(SEMILLA)       # la secuencia del sit-and-reach va primero
    df = leer_nhanes()
    df["z_imc"] = puntuacion_imc(df)

    rho_sr = correlacion_kaggle()
    df["sit_reach_cm"] = [round(v - CERO_CHMS, 1) for v in sortear(
        df, rho_sr, rng, lambda p, s, e: cuantil(p, e, EDADES_CHMS, PERC_CHMS, CHMS[s], LIMITES_CHMS))]

    tablas_p, rho_p, n_nhanes1 = leer_nhanes1()
    df["apertura_piernas_grados"] = [round(v) for v in sortear(
        df, rho_p, rng, lambda p, s, e: cuantil(p, e, CENTROS_NHANES1, PERC_PIERNAS, tablas_p[s], LIMITES_PIERNAS))]

    gill = {s: suavizar(EDADES_GILL, t) for s, t in GILL.items()}
    df["elevacion_brazo_grados"] = [round(v) for v in sortear(
        df, {0: 0.0, 1: 0.0}, rng, lambda p, s, e: cuantil(p, e, EDADES_GILL, PERC_GILL, gill[s], LIMITES_BRAZO))]

    df[["altura_cm", "peso_kg"]] = df[["altura_cm", "peso_kg"]].round(1)
    info = {"rho_sit_reach": rho_sr, "rho_piernas": rho_p, "n_nhanes1": n_nhanes1}
    return df.drop(columns=["imc", "z_imc"]), info


def comprobar(df, info):
    """Medianas generadas por sexo y década, y correlaciones con el IMC."""
    print(f"personas: {len(df)}  (hombres {int(df['sexo'].sum())}, mujeres {int((1 - df['sexo']).sum())})")
    print(f"rho IMC usada (hombres, mujeres): sit-and-reach {info['rho_sit_reach'][1]:.3f}, "
          f"{info['rho_sit_reach'][0]:.3f} | piernas {info['rho_piernas'][1]:.3f}, "
          f"{info['rho_piernas'][0]:.3f} | brazo 0, 0   (NHANES I: {info['n_nhanes1']} personas)")
    ejercicios = ["sit_reach_cm", "apertura_piernas_grados", "elevacion_brazo_grados"]
    print(df.groupby(["sexo", df["edad"] // 10 * 10])[ejercicios].median().round(1))
    imc = df["peso_kg"] / (df["altura_cm"] / 100) ** 2
    for e in ejercicios:
        print(f"correlación IMC - {e}:",
              {int(s): round(float(imc[g.index].corr(g[e])), 3) for s, g in df.groupby("sexo")})


if __name__ == "__main__":
    datos, info = generar()
    comprobar(datos, info)
    datos.to_csv(DESTINO, index=False)
    print(f"Guardado: {DESTINO.relative_to(CARPETA.parent)}")
