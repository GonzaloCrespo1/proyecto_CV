# C11 · Conjunto de datos sintético y modelo del valor esperado

Carpeta del bloque C11 (Gonzalo Crespo Comín). Contiene lo necesario para **crear el conjunto de datos** y **entrenar el modelo** que estima, para una persona de cierta edad, altura, peso y sexo, el resultado esperado en el ejercicio de FlexScan:

| Ejercicio | Columna | Unidad |
|---|---|---|
| Sit-and-reach (sentado) | `sit_reach_cm` | cm respecto a la vertical de la punta del pie: negativo si no llega, positivo si la supera |

## Ficheros

| Ruta | Contenido |
|---|---|
| `preparar_datos.py` | Limpia el conjunto de Kaggle (solo se usa su correlación IMC – sit-and-reach). |
| `generar_dataset.py` | Genera `datos/dataset_sintetico.csv` (semilla fija). |
| `entrenar_modelos.py` | Compara seis modelos con validación cruzada y test, y elige el más sencillo que empata con el mejor (Ridge, σ = 9,27 cm). |
| `fuentes/DEMO_L.xpt`, `fuentes/BMX_L.xpt` | NHANES 2021–2023: edad, sexo, altura y peso (dominio público). |
| `datos/dataset_sintetico.csv` | Conjunto final: 4663 personas, 5 columnas (edad, altura, peso, sexo y sit-and-reach). |
| `modelos/`, `figuras/` | Se crearán al guardar el modelo y sus gráficas. |

## Cómo regenerar el conjunto

1. Descargar `bodyPerformanceKaggle.csv` de Kaggle («Body Performance Data», kukuroo3) en `fuentes/`. No se sube al repositorio hasta confirmar su licencia.
2. Desde la raíz del repositorio:
   ```
   python "C11 - Datos y modelo/preparar_datos.py"
   python "C11 - Datos y modelo/generar_dataset.py"
   ```

Dependencias (solo para esta carpeta; se añadirán a `requirements.txt` en la integración): `scikit-learn==1.9.1`, `scipy==1.18.1`, `joblib==1.6.0`, `threadpoolctl==3.8.0`, `narwhals==2.28.0`, `cloudpickle==3.1.2`, `pandas==3.1.1`, `python-dateutil==4.0.0`, `tzdata==2026.6`, sobre Python 3.12.10. La explicación completa está en `FlexScan_Explicaciones_tecnicas_GONZALO.docx`, en la raíz del repositorio.
