# FlexScan

Evaluación de la flexibilidad con una **cámara única** y control de acceso mediante una **secuencia de patrones visuales**.
Proyecto final de *Visión por Ordenador I* (3º IMAT, ICAI).

## Estado
En desarrollo. Ya funciona:
- la captura de la webcam a 1280×720, el contador de FPS y la corrección de la distorsión de la lente en directo;
- el **detector de patrones**: localiza la tarjeta en el vídeo, la pone de frente y reconoce cuál de los cuatro símbolos es (círculos concéntricos, triángulo, barras o hexágono). El símbolo detectado aparece sobre la imagen cuando se mantiene estable durante 5 fotogramas.

La secuencia de símbolos y el control de acceso se añaden en el siguiente bloque.

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
Teclas:

| Tecla | Acción |
|---|---|
| **c** | alterna entre imagen corregida y original |
| **m** | muestra u oculta la máscara binaria |
| **t** | muestra u oculta la tarjeta enderezada con sus rasgos |
| **q** | sale |

## Cómo se usa el detector
1. Imprime o dibuja una tarjeta con uno de los símbolos de la carpeta `patrones/`, **con su marco negro**, sobre papel blanco.
2. Enséñala a la cámara con buena luz. Puede ir girada o inclinada.
3. Cuando el símbolo se mantiene estable aparece en pantalla como `Simbolo: ...`. Si lo que se ve no encaja con ninguno, pone `desconocido`.

## Estructura
```
src/flexscan/
    __main__.py        programa principal (bucle de vídeo)
    camara.py          apertura de la webcam a 1280x720
    fps.py             contador de FPS
    calibracion.py     corrección de la distorsión con calibracion.npz
    preprocesado.py    máscara binaria (umbral adaptativo y morfología)
    tarjeta.py         localiza el marco y endereza la tarjeta (homografía)
    rasgos.py          manchas, huecos, vértices y circularidad del símbolo
    clasificador.py    decide el símbolo por reglas a partir de los rasgos
    estabilidad.py     confirma el símbolo tras varios fotogramas seguidos
    generar_patrones.py  dibuja los cuatro símbolos en patrones/
patrones/            los cuatro símbolos en PNG
C1-C2 - .../         calibración de la cámara (se ejecuta una vez)
requirements.txt     dependencias con versiones fijas
```

## Calibración
La cámara se calibró con 19 fotos de un damero (9×6 esquinas, cuadro de 23 mm), con un error RMS de 1,52 px. Los parámetros se guardan en `calibracion.npz`, único fichero que el programa necesita de esa fase. Si se cambia de cámara o de resolución, hay que recalibrar y sustituirlo.

**Importante:** ese `calibracion.npz` es de la cámara de Mateo. Con otra cámara hay que pulsar **c** para desactivar la corrección (o recalibrar).

## Autores
Mateo Gómez-Acebo · Gonzalo Crespo Comín
