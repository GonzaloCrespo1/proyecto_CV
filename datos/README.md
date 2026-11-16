# Datos y pruebas

Cada carpeta guarda las capturas y los datos de una prueba del proyecto, para poder repetir los análisis.

| Carpeta | Qué es | Bloque |
|---|---|---|
| `yema_ronda1/`, `yema_ronda2/`, `yema_ronda3/` | Calibración del factor `K_YEMA` (estimar la yema del dedo a partir del nudillo). Capturas, clics y scripts de análisis. | C7, Paso 3 |
| `c7_paso4_repetibilidad/` | Series de capturas con calcetín blanco y descalzo para medir la **repetibilidad** de la distancia dedo-pie. Sin escala en centímetros. `valores.csv`: archivo y `d` en píxeles. | C7, Paso 4 |
| `c7_paso4_escala/` | **Prueba principal del Paso 4:** serie `calcetin_recta_*` con la cámara recta y `escala_a4.jpg` (hoja A4 en el plano de los pies, 111 × 155 px → 5,3 px/cm). `valores.csv`: `d` en píxeles, tronco y posiciones. Incluye `captura_distancia.py`, el script con el que se tomó. | C7, Paso 4 |
| `datos_velocidad.csv` | Medidas de velocidad (FPS) del programa. | C6 |
| `escala.json`, `escala_foto.jpg` | Última calibración de la escala con la hoja A4 (`python -m flexscan.calibrar_escala`). Se vuelven a generar en cada sesión. | C7 |
