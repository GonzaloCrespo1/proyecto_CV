# FlexScan

Evaluación de la flexibilidad con una **cámara única** y control de acceso mediante una **secuencia de patrones visuales**.
Proyecto final de *Visión por Ordenador I* (3º IMAT, ICAI).

## Estado
En desarrollo. Ya funciona:
- la captura de la webcam a 1280×720, el contador de FPS y la corrección de la distorsión de la lente en directo;
- el **detector de patrones**: localiza la tarjeta en el vídeo, la pone de frente y reconoce cuál de los cuatro símbolos es (círculos concéntricos, triángulo, barras o hexágono). El símbolo detectado aparece sobre la imagen cuando se mantiene estable durante 5 fotogramas;
- el **control de acceso** con una secuencia de cuatro patrones: registro de usuarios (nombre y clave visual), entrada enseñando las tarjetas a la cámara en orden, bloqueo tras tres fallos seguidos y sesión abierta con el usuario en pantalla.

- el **tracker** de la persona: aprende el fondo con MOG2 y lo congela, extrae su silueta (la componente conexa mayor), sigue su centroide con un **filtro de Kalman** de velocidad constante y dibuja una **caja punteada de colocación** que es roja sin persona, amarilla cuando entra y verde con el mensaje «COMENZAR ESTIRAMIENTO» cuando está quieta (velocidad estimada por debajo de 0,5 px/fotograma durante 15 fotogramas, umbral medido con datos reales).

Queda por construir la medida de la flexibilidad (puntos clave y ángulos) y la sesión completa.

**Nota.** De momento la caja y el estado verde se muestran siempre, para poder depurar sin registrarse cada vez. En la integración final solo funcionarán con la sesión iniciada.

La documentación técnica de cada bloque está en la carpeta del proyecto (ver «Documentación»).

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
| **f** | vuelve a aprender el fondo (hacerlo con la escena vacía) |
| **b** | muestra u oculta la silueta limpia (primer plano) |
| **v** | muestra u oculta la caja, el centroide y la estimación de Kalman |
| **r** | abre la ventana para registrar un usuario nuevo (nombre y clave de 4 símbolos) |
| **e** | entrar: pide el nombre y después hay que enseñar a la cámara los cuatro símbolos de la clave, en orden |
| **s** | cierra la sesión abierta |
| **q** | sale |

## Cómo se usa el detector
1. Imprime o dibuja una tarjeta con uno de los símbolos de la carpeta `patrones/`, **con su marco negro**, sobre papel blanco.
2. Enséñala a la cámara con buena luz. Puede ir girada o inclinada.
3. Cuando el símbolo se mantiene estable aparece en pantalla como `Simbolo: ...`. Si lo que se ve no encaja con ninguno, pone `desconocido`.

## Cómo se usa el tracker
1. Al arrancar, deja la escena **vacía** unos segundos: el programa aprende el fondo (con **f** se repite).
2. Entra en la escena. Aparece la caja punteada de colocación, **roja** mientras no haya nadie dentro.
3. Colócate dentro de la caja: pasa a **amarilla** tras 5 fotogramas seguidos dentro.
4. Quédate quieto: con unos 0,6 s sin moverte pasa a **verde** y sale «COMENZAR ESTIRAMIENTO». Si te mueves, vuelve a amarilla.

Parámetros ajustables (constantes al inicio de cada módulo): tamaño de la caja y grosor del trazo (`zona.py`), fotogramas de confirmación (`zona.py`), umbrales de quietud y fotogramas necesarios (`quietud.py`), área mínima de la silueta (`silueta.py`) y ruidos del filtro de Kalman (`seguimiento.py`). El umbral de quietud depende de los FPS y de la distancia a la cámara, así que habrá que revisarlo si cambia el montaje. Una superficie clara cercana puede unirse a la silueta y el fondo congelado falla ante cambios bruscos de luz; en ambos casos se repite el aprendizaje con **f**.

## Cómo se usa el control de acceso
1. **Registrarse.** Pulsa **r**, escribe el nombre y pulsa en orden los cuatro símbolos de la clave (se pueden repetir). Después, «Guardar».
2. **Entrar.** Pulsa **e**, escribe el nombre y enseña a la cámara las tarjetas en el mismo orden. Cada símbolo aceptado aparece en el panel de abajo a la izquierda. Para repetir un símbolo hay que retirar la tarjeta y volver a enseñarla.
3. **Resultado.** Con la clave correcta sale *acceso concedido* y, a los 3 s, queda el usuario escrito arriba a la derecha (sesión abierta). Si no, sale *acceso denegado*. Tras **3 fallos seguidos** hay un bloqueo de 30 s en el que **e** no hace nada.
4. **Salir.** Con **s** se cierra la sesión y se puede entrar con otro usuario. Mientras hay una sesión abierta no se detectan las tarjetas.

Los usuarios se guardan en `usuarios.json` (nombre, sal y hash de la clave; nunca la clave). Ese fichero **no se sube a GitHub**: cada persona tiene el suyo y debe registrarse en su ordenador. Las tarjetas se imprimen a partir de las imágenes de `patrones/`.

### Limitaciones
- Solo hay 256 claves posibles (4 símbolos con 4 opciones cada uno): el hash protege frente a leer la clave del fichero, no frente a probarlas todas.
- El bloqueo vale para la ejecución actual: al cerrar y volver a abrir el programa se reinicia.
- El registro no pide autenticación: cualquiera con acceso al teclado puede crear usuarios.
- El nombre no admite tildes ni ñ (límite de las fuentes de OpenCV).
- Solo hay una sesión a la vez.

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
    usuarios.py        guarda y comprueba los usuarios (sal + hash) en usuarios.json
    registro.py        ventana de registro: nombre y clave de 4 símbolos
    secuencia.py       máquina de estados de la entrada (símbolos, fallos, bloqueo)
    acceso.py          ventana del nombre, panel con la secuencia y usuario en pantalla
    fondo.py           aprendizaje y congelado del fondo (MOG2)
    silueta.py         umbral, apertura, cierre y componente conexa mayor
    seguimiento.py     filtro de Kalman de velocidad constante sobre el centroide
    grafica.py         ventana con la ganancia de Kalman en tiempo real
    zona.py            caja punteada de colocación y sus estados
    quietud.py         decide si la persona está quieta (umbral con histéresis)
patrones/            los cuatro símbolos en PNG
usuarios.json        usuarios registrados (local, no se sube a GitHub)
datos/               escala de la sesión, en_vivo/ (tomas guardadas por el programa) y pruebas_y_calibracion/ (ver datos/README.md)
C1-C2 - .../         calibración de la cámara (se ejecuta una vez)
requirements.txt     dependencias con versiones fijas
```

## Documentación
```
FlexScan_Plan_de_trabajo.pdf                       plan por bloques y estado
FlexScan_C1-C2_Calibracion_y_preparacion.pdf       cuaderno técnico: calibración y preparación
FlexScan_C3-C4_Deteccion_de_patrones.pdf           cuaderno técnico: cámara y detección de patrones
FlexScan_C5_Seguridad.pdf                          cuaderno técnico: control de acceso
FlexScan_C6_Tracker.pdf                            cuaderno técnico: tracker y caja de colocación
FlexScan_Explicaciones_tecnicas.docx               cuaderno técnico en curso (C7 en adelante)
```
Cada grupo de bloques cerrado se pasa a su propio PDF y el Word queda libre para el siguiente.

## Calibración
La cámara se calibró con 19 fotos de un damero (9×6 esquinas, cuadro de 23 mm), con un error RMS de 1,52 px. Los parámetros se guardan en `calibracion.npz`, único fichero que el programa necesita de esa fase. Si se cambia de cámara o de resolución, hay que recalibrar y sustituirlo.

**Importante:** ese `calibracion.npz` es de la cámara de Mateo. Con otra cámara hay que pulsar **c** para desactivar la corrección (o recalibrar).

## Autores
Mateo Gómez-Acebo · Gonzalo Crespo Comín
