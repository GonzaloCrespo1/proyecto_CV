"""Entrena y compara los modelos del valor esperado, uno por ejercicio (bloque C11).

Para cada ejercicio (sit-and-reach, apertura de piernas y elevación de brazo) se buscan los
hiperparámetros de cada modelo candidato con validación cruzada sobre el 80 % de los datos.
El 20 % de test se aparta al principio, el mismo para los tres ejercicios, y no se usa aquí.

Uso (desde la raíz del repositorio):
    python "C11 - Datos y modelo/entrenar_modelos.py"
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.model_selection import GridSearchCV, KFold, train_test_split

CARPETA = Path(__file__).resolve().parent
DATOS = CARPETA / "datos" / "dataset_sintetico.csv"

SEMILLA = 2026
FRACCION_TEST = 0.20
PLIEGUES = KFold(n_splits=5, shuffle=True, random_state=SEMILLA)

ENTRADAS = ["edad", "altura_cm", "peso_kg", "sexo"]
EJERCICIOS = {
    "sit_reach": "sit_reach_cm",
    "piernas": "apertura_piernas_grados",
    "brazo": "elevacion_brazo_grados",
}
METRICAS = {"rmse": "neg_root_mean_squared_error", "mae": "neg_mean_absolute_error", "r2": "r2"}


def cargar_y_partir():
    """Lee el conjunto y separa un 20 % de test, el mismo para todos los ejercicios."""
    df = pd.read_csv(DATOS)
    entreno, test = train_test_split(df, test_size=FRACCION_TEST, random_state=SEMILLA,
                                     stratify=df["sexo"])
    return entreno, test


def candidatos():
    """Modelos candidatos con su rejilla de hiperparámetros, de más sencillo a más complejo."""
    return {
        "media": (DummyRegressor(strategy="mean"), {}),
    }


def buscar(modelo, rejilla, X, y):
    """GridSearchCV con 5 pliegues: elige por RMSE y devuelve la búsqueda ya ajustada."""
    busqueda = GridSearchCV(modelo, rejilla, cv=PLIEGUES, scoring=METRICAS, refit="rmse", n_jobs=-1)
    return busqueda.fit(X, y)


def resumen(busqueda):
    """Métricas medias (y desviación entre pliegues) de la mejor combinación."""
    r = busqueda.cv_results_
    i = busqueda.best_index_
    return {
        "rmse": -r["mean_test_rmse"][i], "rmse_desv": r["std_test_rmse"][i],
        "mae": -r["mean_test_mae"][i], "r2": r["mean_test_r2"][i],
        "mejores": busqueda.best_params_,
    }


if __name__ == "__main__":
    entreno, test = cargar_y_partir()
    print(f"entrenamiento: {len(entreno)} personas   test (apartado): {len(test)} personas")
    for ejercicio, columna in EJERCICIOS.items():
        X, y = entreno[ENTRADAS], entreno[columna]
        print(f"\n== {ejercicio} ({columna}) · media {y.mean():.1f} · desv. típica {y.std():.1f}")
        print(f"{'modelo':<14}{'RMSE (CV)':>12}{'± pliegues':>12}{'MAE':>8}{'R²':>8}  mejores hiperparámetros")
        for nombre, (modelo, rejilla) in candidatos().items():
            m = resumen(buscar(modelo, rejilla, X, y))
            print(f"{nombre:<14}{m['rmse']:>12.2f}{m['rmse_desv']:>12.2f}{m['mae']:>8.2f}"
                  f"{m['r2']:>8.3f}  {m['mejores']}")
