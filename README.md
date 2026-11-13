# FlexScan

Evaluación de la flexibilidad con una **cámara única** y control de acceso mediante una **secuencia de patrones visuales**.
Proyecto final de *Visión por Ordenador I* (3º IMAT, ICAI).

## Estado
En desarrollo. Ya funciona la captura de la webcam a 1280×720, el contador de FPS y la corrección de la distorsión de la lente en directo.

## Requisitos
- Python 3
- Webcam (probado con la del portátil, en Windows)

## Instalación
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
En Linux o macOS, el segundo comando es `source venv/bin/activate`.

## Ejecución
```
cd src
python -m flexscan
```
Teclas: **c** alterna entre imagen original y corregida, **q** sale.

## Estructura
```
src/flexscan/
    __main__.py      programa principal (bucle de vídeo)
    camara.py        apertura de la webcam a 1280x720
    fps.py           contador de FPS
    calibracion.py   corrección de la distorsión con calibracion.npz
C1-C2 - .../         calibración de la cámara (se ejecuta una vez)
requirements.txt     dependencias con versiones fijas
```

## Calibración
La cámara se calibró con 19 fotos de un damero (9×6 esquinas, cuadro de 23 mm), con un error RMS de 1,52 px. Los parámetros se guardan en `calibracion.npz`, único fichero que el programa necesita de esa fase. Si se cambia de cámara o de resolución, hay que recalibrar y sustituirlo.

## Autores
Mateo Gómez-Acebo · Gonzalo Crespo Comín# FlexScan

Evaluación de la flexibilidad con una **cámara única** y control de acceso mediante una **secuencia de patrones visuales**.
Proyecto final de *Visión por Ordenador I* (3º IMAT, ICAI).

## Estado
En desarrollo. Ya funciona la captura de la webcam a 1280×720, el contador de FPS y la corrección de la distorsión de la lente en directo.

## Requisitos
- Python 3
- Webcam (probado con la del portátil, en Windows)

## Instalación
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
En Linux o macOS, el segundo comando es `source venv/bin/activate`.

## Ejecución
```
cd src
python -m flexscan
```
Teclas: **c** alterna entre imagen original y corregida, **q** sale.

## Estructura
```
src/flexscan/
    __main__.py      programa principal (bucle de vídeo)
    camara.py        apertura de la webcam a 1280x720
    fps.py           contador de FPS
    calibracion.py   corrección de la distorsión con calibracion.npz
C1-C2 - .../         calibración de la cámara (se ejecuta una vez)
requirements.txt     dependencias con versiones fijas
```

## Calibración
La cámara se calibró con 19 fotos de un damero (9×6 esquinas, cuadro de 23 mm), con un error RMS de 1,52 px. Los parámetros se guardan en `calibracion.npz`, único fichero que el programa necesita de esa fase. Si se cambia de cámara o de resolución, hay que recalibrar y sustituirlo.

## Autores
Mateo Gómez-Acebo · Gonzalo Crespo Comín