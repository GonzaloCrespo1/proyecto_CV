# C11 · Datos sintéticos y modelo del índice esperado

Carpeta del bloque C11 (Gonzalo Crespo Comín). Contiene todo lo necesario para **crear el conjunto de datos sintético y elegir el modelo** que estima el índice de flexibilidad esperado Î (0–100) a partir de la edad, la altura, el peso y el sexo. No forma parte de la visión por ordenador y no depende del resto del programa.

| Ruta | Contenido |
|---|---|
| `dataset_sintetico.py` | Generador reproducible (semilla fija) del conjunto de datos. |
| `modelo_indice.py` | Partición 80/20, búsqueda de hiperparámetros, evaluación en test, elección del modelo y guardado. |
| `datos/` | CSV generado. |
| `modelos/` | Modelo elegido (`indice_esperado.joblib`), con σ, versiones y semilla. |
| `figuras/` | Gráficas de validación. |

El programa principal solo usa `src/flexscan/esperado.py`, que carga el modelo guardado aquí.

Dependencias (solo para esta carpeta, aún no están en `requirements.txt`): `scikit-learn==1.9.1`, `scipy==1.18.1`, `joblib==1.6.0`, `threadpoolctl==3.8.0`, `narwhals==2.28.0`, `cloudpickle==3.1.2`, sobre Python 3.12.10.
