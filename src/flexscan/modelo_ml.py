"""Punto de enganche con el modelo de aprendizaje automático (parte de Gonzalo Crespo Comín).

FlexScan llama a `predecir_valor_ml(ruta_toma)` cuando la persona pide el análisis de flexibilidad y
enseña el valor devuelto junto a su medida experimental.

QUÉ PREDICE. El sit-and-reach ESPERADO para el perfil de la persona, en cm y con el mismo cero y signo
que `medida_cm`: 0 = la vertical de la punta del pie, negativo si no llega, positivo si la pasa.
«Esperado» significa típico para alguien de su edad, sexo, altura y peso, no óptimo.

ENTRADAS. Solo el `perfil` de `resumen.json`: edad, sexo («hombre» = 1, «mujer» = 0), altura_cm y peso_kg.
No usa `serie.csv` ni la medida.

MODELO Y DATOS. Ridge (regresión lineal regularizada, alpha = 10) con escalado de las entradas,
guardado en `modelos/sit_reach.joblib` por `C11 - Datos y modelo/entrenar_modelos.py`. Se entrenó
con un conjunto sintético de 4663 adultos de 20 a 69 años: perfiles reales y anónimos de la encuesta
pública NHANES 2021-2023 y un sit-and-reach sorteado de los percentiles publicados por CHMS (Canadá),
según su sexo, su edad y su IMC. No contiene datos personales de nadie del proyecto.
Fuera de 20-69 años, el valor es una extrapolación de la misma fórmula.

ERROR. RMSE en un 20 % de test apartado: 9,27 cm. Es también sigma, la desviación típica de los
residuos, que sirve para el veredicto: z = (medida_cm - valor_ml) / sigma. El modelo está a 0,01 cm
del mejor posible con estas entradas: casi toda la variación entre personas no la explica el perfil.
Explicación completa en FlexScan_Explicaciones_tecnicas_GONZALO.docx.
"""
import json
from functools import lru_cache
from pathlib import Path

MODELO_LISTO = True            # False: la pantalla enseña «valor_ml» pendiente. True: enseña el número devuelto.

RUTA_MODELO = Path(__file__).resolve().parents[2] / "modelos" / "sit_reach.joblib"
SEXO = {"hombre": 1, "mujer": 0}


def cargar_resumen(ruta_toma):
    """Lee `resumen.json` de la toma y lo devuelve como diccionario (ver docs/prompt_gonzalo.md)."""
    return json.loads((Path(ruta_toma) / "resumen.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def cargar_modelo():
    """Carga el modelo guardado la primera vez que se pide y lo recuerda para las siguientes.
    Devuelve el diccionario de entrenar_modelos.py: el modelo, sigma_cm, las entradas, etc."""
    import joblib
    return joblib.load(RUTA_MODELO)


def sigma_cm():
    """Desviación típica de los errores del modelo en test (cm), para el veredicto."""
    return cargar_modelo()["sigma_cm"]


def predecir_valor_ml(ruta_toma):
    """Sit-and-reach esperado (cm) para el perfil de la toma guardada en `ruta_toma`, o None si la toma
    no tiene un perfil completo (por ejemplo, tomas antiguas sin registro)."""
    import pandas as pd

    perfil = cargar_resumen(ruta_toma).get("perfil") or {}
    sexo = SEXO.get(str(perfil.get("sexo", "")).lower())
    try:
        datos = {"edad": float(perfil["edad"]), "altura_cm": float(perfil["altura_cm"]),
                 "peso_kg": float(perfil["peso_kg"]), "sexo": sexo}
    except (KeyError, TypeError, ValueError):
        return None
    if sexo is None:
        return None
    guardado = cargar_modelo()
    fila = pd.DataFrame([datos])[guardado["entradas"]]      # mismas columnas y orden que al entrenar
    return round(float(guardado["modelo"].predict(fila)[0]), 1)


# Carga al arrancar el programa (__main__.py importa este módulo al empezar): la primera carga de
# pandas, scikit-learn y el modelo tarda unos 3 s y así no congela la pantalla del análisis.
# Si falla, el programa arranca igual y predecir_valor_ml lo reintentará al pedir el análisis.
if MODELO_LISTO:
    try:
        import pandas  # noqa: F401
        cargar_modelo()
    except Exception as error:
        print(f"Modelo de ML: no se pudo cargar al arrancar ({error})")
