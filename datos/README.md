# Carpeta `datos/`

Reúne todo lo que el proyecto guarda en disco aparte del código: lo que **escribe el programa** en cada uso y las **pruebas y calibraciones** hechas durante el desarrollo, que se conservan para poder repetir los análisis.

```
datos/
├── README.md                  este fichero
├── escala.json                última calibración de la escala (se regenera en cada sesión)
├── escala_foto.jpg            foto de la hoja A4 de esa calibración (ídem)
├── en_vivo/                   lo que guarda el programa: una carpeta por toma
│   └── [<usuario>/]toma_AAAAMMDD_HHMMSS/
│       ├── captura.png        pantalla del programa con el resultado
│       ├── grafica.png        distancia (cm) frente al tiempo, con la base, la ventana elegida y la medida
│       ├── serie.csv          serie temporal (t_s, d_cm)
│       └── resumen.json       estado, medida, línea base, tiempos, escala y parámetros
└── pruebas_y_calibracion/     pruebas y calibraciones del desarrollo (se versionan)
```

## Qué se sube a GitHub y qué no

| Ruta | ¿Se versiona? | Motivo |
|---|---|---|
| `README.md` y `pruebas_y_calibracion/` | Sí | Son la evidencia de las pruebas. |
| `escala.json`, `escala_foto.jpg` | No (`.gitignore`) | Dependen de la cámara y de la posición en cada sesión: se vuelven a generar con `python -m flexscan.calibrar_escala`. |
| `en_vivo/` | No (`.gitignore`) | Lo escribe el programa en cada uso. Si una toma sirve como prueba, se **copia** a `pruebas_y_calibracion/`. |

## `en_vivo/`

El programa crea una carpeta por toma cuando una medida termina (con valor o sin él) y avisa con un pitido (uno si hay medida, dos si no). El nombre lleva la fecha y la hora, de modo que ninguna toma pisa a otra. Cuando el inicio de sesión esté conectado, la toma se guardará dentro de la carpeta de la persona (`en_vivo/<usuario>/toma_…/`); sin sesión, va directa a `en_vivo/`. Lo hace `src/flexscan/registro_medida.py`.

## `pruebas_y_calibracion/`

| Carpeta | Qué es | Bloque |
|---|---|---|
| `yema_ronda1/`, `yema_ronda2/`, `yema_ronda3/` | Calibración del factor `K_YEMA` (estimar la yema del dedo a partir del nudillo). Capturas, clics y scripts de análisis; cada script se ejecuta desde su propia carpeta. | C7, Paso 3 |
| `c7_paso4_repetibilidad/` | Series de capturas con calcetín blanco y descalzo para medir la **repetibilidad** de la distancia dedo-pie. Sin escala en centímetros. `valores.csv`: archivo y `d` en píxeles. | C7, Paso 4 |
| `c7_paso4_escala/` | **Prueba principal del Paso 4:** serie `calcetin_recta_*` con la cámara recta y `escala_a4.jpg` (hoja A4 en el plano de los pies, 111 × 155 px → 5,3 px/cm). `valores.csv`: `d` en píxeles, tronco y posiciones. Incluye `captura_distancia.py`, el script con el que se tomó. | C7, Paso 4 |
| `c7_paso5_validez/` | Series temporales (un CSV por toma) con la distancia dedo-pie y el ángulo del tronco, para fijar la condición de validez de la medida. `toma1–3`: ronda 1 (sentado recto); `b1–b3`: brazos estirados; `a1–a2`: manos en las rodillas (postura adoptada). `captura_validez.py` es el script con el que se grabaron. | C7, Paso 5 |
| `c7_figuras_y_funcionamiento/` | **Pruebas en vivo del programa** (17 nov 2026): una carpeta por toma, con la misma estructura que `en_vivo/`. Tres tomas con medida: −9,0, −9,5 y −13,1 cm. | C7, Paso 6 |
| `datos_velocidad.csv` | Medidas de velocidad (FPS) del programa. En el cuaderno del bloque C6 figura con su ruta anterior (`datos/datos_velocidad.csv`). | C6 |

Los scripts de captura (`captura_distancia.py`, `captura_validez.py`) se ejecutan desde `src/` y escriben en su propia carpeta de `pruebas_y_calibracion/`.
