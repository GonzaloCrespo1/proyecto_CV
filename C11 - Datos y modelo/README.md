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
| `entrenar_modelos.py` | Compara seis modelos con validación cruzada y test, elige el más sencillo que empata con el mejor (Ridge, σ = 9,27 cm), lo reentrena con todos los datos y lo guarda en `modelos/sit_reach.joblib` (en la raíz del repositorio). |
| `graficas_modelo.py` | Diagnóstico del modelo con el test, su fórmula en unidades reales y el contraste con medidas reales. Guarda las figuras en `figuras/`. |
| `probar_modelo_ml.py` | Prueba sin cámara de la integración (`src/flexscan/modelo_ml.py`) con tomas de perfiles inventados. |
| `fuentes/DEMO_L.xpt`, `fuentes/BMX_L.xpt` | NHANES 2021–2023: edad, sexo, altura y peso (dominio público). |
| `datos/dataset_sintetico.csv` | Conjunto final: 4663 personas, 5 columnas (edad, altura, peso, sexo y sit-and-reach). |
| `datos/medidas_reales.csv` | Medidas con FlexScan de personas reales, anónimas. **Solo en local**: no se sube a GitHub (datos personales). Sin él, `graficas_modelo.py` omite el contraste. |
| `figuras/` | Las seis figuras de `graficas_modelo.py`. |

## Cómo se usa el modelo en FlexScan

`src/flexscan/modelo_ml.py` carga `modelos/sit_reach.joblib` al arrancar el programa. `predecir_valor_ml(ruta_toma)` lee el perfil de `resumen.json` y devuelve el sit-and-reach esperado en cm (mismo cero y signo que la medida), y `sigma_cm()` devuelve σ. El análisis compara la medida con el esperado mediante z = (medida − esperado) / σ: por debajo de −1, poco flexible; entre −1 y +1, en la media; por encima de +1, muy flexible.

## Cómo regenerar el conjunto y el modelo

1. Descargar `bodyPerformanceKaggle.csv` de Kaggle («Body Performance Data», kukuroo3) en `fuentes/`. No se sube al repositorio hasta confirmar su licencia.
2. Desde la raíz del repositorio:
   ```
   python "C11 - Datos y modelo/preparar_datos.py"
   python "C11 - Datos y modelo/generar_dataset.py"
   python "C11 - Datos y modelo/entrenar_modelos.py"
   python "C11 - Datos y modelo/graficas_modelo.py"
   python "C11 - Datos y modelo/probar_modelo_ml.py"
   ```
   El tercero tarda unos 2–3 minutos y sobrescribe `modelos/sit_reach.joblib`.

Las dependencias están en `requirements.txt` de la raíz (scikit-learn, pandas, joblib, matplotlib…), sobre Python 3.12.10. La explicación completa está en `FlexScan_Explicaciones_tecnicas_GONZALO.docx`, en la raíz del repositorio.
