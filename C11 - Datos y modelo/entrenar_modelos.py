"""Entrena y compara los modelos del valor esperado del sit-and-reach (bloque C11).

Para cada modelo candidato se buscan los hiperparámetros con validación cruzada sobre el
80 % de los datos. El 20 % de test se aparta al principio y solo se usa al final: cada modelo,
reentrenado con todo el 80 %, se evalúa una vez en test. Con un bootstrap emparejado se decide
qué modelos no son peores que el mejor y, entre ellos, se elige el más sencillo (parsimonia).
Por último se calcula sigma, la dispersión de los residuos en test, y el modelo elegido se
reentrena con el 100 % de los datos y se guarda en modelos/sit_reach.joblib.

Uso (desde la raíz del repositorio):
    python "C11 - Datos y modelo/entrenar_modelos.py"
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.compose import TransformedTargetRegressor
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import GridSearchCV, KFold, train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR

CARPETA = Path(__file__).resolve().parent
DATOS = CARPETA / "datos" / "dataset_sintetico.csv"
MODELO = CARPETA.parent / "modelos" / "sit_reach.joblib"   # carpeta modelos/ de la raíz

SEMILLA = 2026
FRACCION_TEST = 0.20
PLIEGUES = KFold(n_splits=5, shuffle=True, random_state=SEMILLA)
REMUESTREOS = 1000

ENTRADAS = ["edad", "altura_cm", "peso_kg", "sexo"]
OBJETIVO = "sit_reach_cm"            # cm respecto a la vertical del pie (negativo si no llega)
METRICAS = {"rmse": "neg_root_mean_squared_error", "mae": "neg_mean_absolute_error", "r2": "r2"}


def cargar_y_partir():
    """Lee el conjunto y separa un 20 % de test, estratificado por sexo."""
    df = pd.read_csv(DATOS)
    entreno, test = train_test_split(df, test_size=FRACCION_TEST, random_state=SEMILLA,
                                     stratify=df["sexo"])
    return entreno, test


def candidatos():
    """Modelos candidatos con su rejilla de hiperparámetros, de más sencillo a más complejo.
    Las entradas se estandarizan dentro de cada pipeline (con la media y la desviación del
    pliegue de entrenamiento). En el SVR y el MLP también se estandariza la salida, para que
    sus hiperparámetros (epsilon, alpha) no dependan de que la salida esté en cm. Los árboles
    (Random Forest y boosting) no necesitan escalado: solo comparan umbrales.
    Las rejillas de los árboles y la red son pequeñas a propósito, para que el tiempo sea razonable."""
    ridge = make_pipeline(StandardScaler(), Ridge())
    svr = TransformedTargetRegressor(regressor=make_pipeline(StandardScaler(), SVR(kernel="rbf")),
                                     transformer=StandardScaler())
    bosque = RandomForestRegressor(n_estimators=200, random_state=SEMILLA, n_jobs=-1)
    boosting = HistGradientBoostingRegressor(random_state=SEMILLA)
    red = TransformedTargetRegressor(
        regressor=make_pipeline(StandardScaler(),
                                MLPRegressor(max_iter=2000, early_stopping=True, random_state=SEMILLA)),
        transformer=StandardScaler())
    return {
        "media": (DummyRegressor(strategy="mean"), {}),
        "ridge": (ridge, {"ridge__alpha": np.logspace(-3, 3, 13)}),
        "svr_rbf": (svr, {"regressor__svr__C": [0.1, 1, 10, 100],
                          "regressor__svr__epsilon": [0.5, 1.0, 1.5],
                          "regressor__svr__gamma": [0.001, 0.01, 0.1, 1.0]}),
        "random_forest": (bosque, {"max_depth": [4, 8, None],
                                   "min_samples_leaf": [5, 20, 50]}),
        "boosting": (boosting, {"learning_rate": [0.03, 0.1],
                                "max_depth": [2, 3],
                                "max_iter": [100, 300]}),
        "mlp": (red, {"regressor__mlpregressor__hidden_layer_sizes": [(16,), (32, 16)],
                      "regressor__mlpregressor__alpha": [0.001, 0.1, 1.0]}),
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
        "mejores": {k.split("__")[-1]: round(float(v), 4) if isinstance(v, float) else v
                    for k, v in busqueda.best_params_.items()},
    }


def bootstrap_rmse(errores, rng):
    """RMSE de cada modelo en REMUESTREOS remuestreos del test. Todos los modelos usan los
    mismos remuestreos (bootstrap emparejado), así sus diferencias se pueden comparar."""
    n = len(next(iter(errores.values())))
    indices = rng.integers(0, n, size=(REMUESTREOS, n))
    return {nombre: np.sqrt((e[indices] ** 2).mean(axis=1)) for nombre, e in errores.items()}


def elegir(errores, rng):
    """Compara cada modelo con el de menor RMSE en test mediante el intervalo del 95 % de la
    diferencia de RMSE. Devuelve la tabla y el modelo más sencillo cuyo intervalo contiene el
    0 (no es significativamente peor). El orden de candidatos() es el orden de sencillez."""
    rmse_test = {nombre: float(np.sqrt((e ** 2).mean())) for nombre, e in errores.items()}
    mejor = min(rmse_test, key=rmse_test.get)
    remuestreos = bootstrap_rmse(errores, rng)
    tabla, elegido = {}, None
    for nombre in errores:
        diferencia = remuestreos[nombre] - remuestreos[mejor]
        bajo, alto = np.percentile(diferencia, [2.5, 97.5])
        empata = bajo <= 0
        tabla[nombre] = (rmse_test[nombre], bajo, alto, empata)
        if empata and elegido is None:
            elegido = nombre
    return tabla, mejor, elegido


def guardar(busqueda, nombre, sigma, df):
    """Reentrena el modelo elegido, con sus mejores hiperparámetros, con el 100 % de los datos
    y lo guarda junto con sigma y lo necesario para saber de dónde sale."""
    final = clone(busqueda.best_estimator_).fit(df[ENTRADAS], df[OBJETIVO])
    MODELO.parent.mkdir(exist_ok=True)
    joblib.dump({
        "modelo": final,                        # pipeline completo: escalado + modelo
        "nombre": nombre,
        "hiperparametros": busqueda.best_params_,
        "sigma_cm": sigma,                      # desviación típica de los residuos en test
        "entradas": ENTRADAS,
        "objetivo": OBJETIVO,
        "personas": len(df),
        "semilla": SEMILLA,
        "version_sklearn": sklearn.__version__,  # el .joblib solo se abre con esta versión
    }, MODELO)
    return final


if __name__ == "__main__":
    entreno, test = cargar_y_partir()
    rng = np.random.default_rng(SEMILLA)
    print(f"entrenamiento: {len(entreno)} personas   test (apartado): {len(test)} personas")
    X, y = entreno[ENTRADAS], entreno[OBJETIVO]
    X_test, y_test = test[ENTRADAS], test[OBJETIVO]
    print(f"\n== {OBJETIVO} · media {y.mean():.1f} · desv. típica {y.std():.1f}")
    print(f"{'modelo':<14}{'RMSE (CV)':>12}{'± pliegues':>12}{'MAE':>8}{'R²':>8}  mejores hiperparámetros")
    errores, busquedas = {}, {}
    for nombre, (modelo, rejilla) in candidatos().items():
        busqueda = buscar(modelo, rejilla, X, y)
        m = resumen(busqueda)
        print(f"{nombre:<14}{m['rmse']:>12.2f}{m['rmse_desv']:>12.2f}{m['mae']:>8.2f}"
              f"{m['r2']:>8.3f}  {m['mejores']}")
        # GridSearchCV ya ha reentrenado la mejor combinación con todo el 80 %.
        errores[nombre] = (y_test - busqueda.predict(X_test)).to_numpy()
        busquedas[nombre] = busqueda

    tabla, mejor, elegido = elegir(errores, rng)
    print(f"\n   examen en test ({len(test)} personas) · diferencia de RMSE frente a {mejor}, IC 95 %")
    print(f"{'modelo':<14}{'RMSE test':>12}{'IC 95 %':>20}  ¿empata con el mejor?")
    for nombre, (rmse, bajo, alto, empata) in tabla.items():
        marca = "sí" if empata else "no (peor)"
        print(f"{nombre:<14}{rmse:>12.2f}{f'[{bajo:+.2f}, {alto:+.2f}]':>20}  {marca}")
    residuos = errores[elegido]
    sigma = float(residuos.std(ddof=1))
    print(f"   elegido por parsimonia: {elegido} · sesgo medio {residuos.mean():+.2f} cm"
          f" · sigma {sigma:.2f} cm")

    guardar(busquedas[elegido], elegido, sigma, pd.concat([entreno, test]))
    print(f"\nGuardado: {MODELO.relative_to(CARPETA.parent)} ({elegido} reentrenado con "
          f"{len(entreno) + len(test)} personas · sigma {sigma:.2f} cm)")
