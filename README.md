# FlexScan

Evaluación de la flexibilidad con una **cámara única** y control de acceso mediante una **secuencia de patrones visuales**.
Proyecto final de *Visión por Ordenador I* (3º IMAT, ICAI).

## Estado
En desarrollo. Ya funciona el **recorrido completo de una persona**, con una sola cámara, desde la calibración hasta el resultado de la medida:
- la captura de la webcam a 1280×720, el contador de FPS y la corrección de la distorsión de la lente en directo;
- el **detector de patrones**: localiza la tarjeta en el vídeo, la pone de frente y reconoce cuál de los cuatro símbolos es (círculos concéntricos, triángulo, barras o hexágono);
- el **control de acceso** con una secuencia de cuatro patrones: registro de usuarios (nombre y apellido, clave visual y datos personales), entrada enseñando las tarjetas a la cámara en orden, bloqueo tras tres fallos seguidos y sesión abierta con el usuario y sus datos en pantalla;
- el **tracker** de la persona: aprende el fondo con MOG2, extrae su silueta, sigue su centroide con un **filtro de Kalman** y dibuja una **caja punteada de colocación** (roja sin persona, amarilla cuando entra y verde cuando está quieta);
- los **puntos clave del cuerpo** con MediaPipe Pose y la **medida del ejercicio** (sit-and-reach): distancia horizontal entre la yema del dedo y el pie, en cm, con la escala sacada de una hoja A4, filtrada con la mediana de 15 fotogramas y validada por una regla (línea base, mejor ventana de 2 s, fin a los 5 s sin mejora);
- la **integración guiada** (bloque C8): calibración de la escala dentro del programa, ventana de instrucciones, aprendizaje automático del fondo, avisos de la medida en semáforo con pitido de comienzo y de fin, y una **ventana de resultado** con tres opciones (repetir la medida, ver el análisis de flexibilidad o cerrar la sesión). Cada toma se guarda en `datos/en_vivo/<usuario>/` con captura, gráfica, serie y un `resumen.json` que incluye el perfil de la persona.

Queda por hacer la parte de aprendizaje automático: el análisis ya compara la medida con el valor de un modelo, pero ese valor aparece como «pendiente del modelo» hasta que se integre (punto de enganche único en `src/flexscan/modelo_ml.py`, contrato en `docs/prompt_gonzalo.md`), y después el veredicto final automático. El proyecto se centra en **un solo ejercicio, el sit-and-reach**.

La documentación técnica de cada bloque está en la carpeta del proyecto (ver «Documentación»).

## Requisitos
- Python 3
- Webcam (probado con la del portátil, en Windows)
- Dependencias de `requirements.txt`: `numpy`, `opencv-contrib-python` y `mediapipe`
- Una hoja **A4** para calibrar la escala (los pitidos de aviso solo suenan en Windows)

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
La primera vez en cada escenario hay que **calibrar la escala** (el fichero `datos/escala.json` no se sube a GitHub, así que cada persona lo genera en su ordenador y debe repetirlo si cambia la cámara o su posición). El propio programa lo pide: mientras falte, la imagen se oscurece, un panel rojo avisa y no funciona nada más. Coloca la hoja **A4** en el sitio del ejercicio, pulsa **k** y marca sus cuatro esquinas sobre la foto congelada. (También se puede hacer con `python -m flexscan.calibrar_escala`.)

Al arrancar con la escala calibrada aparecen la presentación del proyecto y la ventana de teclas. Las teclas valen **solo en la fase del programa en que tienen sentido** (fuera de ella no hacen nada y salta un aviso); la tecla **h** abre la ventana con la tabla completa y marca en verde lo que vale en cada momento.

| Tecla | Acción | Fase |
|---|---|---|
| **r** | registrar un usuario nuevo (nombre y apellido, clave de 4 símbolos y datos personales) | inicio |
| **e** | entrar: pide el nombre y después hay que enseñar a la cámara los cuatro símbolos de la clave, en orden | inicio y acceso |
| **Esc** | cancela el acceso y vuelve al inicio | acceso |
| **n** | descarta la medida y empieza otra (sin mover la cámara) | medida y resultado |
| **s** | cierra la sesión | preparación, medida y resultado |
| **h** | abre o cierra la ventana de teclas | todas menos la calibración |
| **q** | sale | todas |
| **k** | calibra la escala con la hoja A4 | calibración, inicio, medida y resultado |
| **c** | alterna entre imagen corregida y original | calibración, inicio y acceso |
| **m** | muestra la máscara binaria del detector de tarjeta | inicio y acceso |
| **t** | muestra la tarjeta enderezada con sus rasgos | inicio y acceso |
| **f** | vuelve a aprender el fondo (con la escena vacía) | inicio |
| **b** | muestra la silueta limpia (necesita el fondo aprendido) | desde el inicio |
| **v** | muestra la caja, el centroide y la ganancia de Kalman (necesita el fondo aprendido) | desde el inicio |
| **p** | muestra u oculta los puntos del cuerpo (la captura guardada los incluye siempre) | medida |

## Cómo se usa el detector
1. Imprime o dibuja una tarjeta con uno de los símbolos de la carpeta `patrones/`, **con su marco negro**, sobre papel blanco.
2. Enséñala a la cámara con buena luz. Puede ir girada o inclinada.
3. Cuando el símbolo se mantiene estable aparece en pantalla como `Simbolo: ...`. Si lo que se ve no encaja con ninguno, pone `desconocido`.

## Cómo se usa el tracker
1. El programa aprende el fondo con la escena **vacía**: en el recorrido normal lo hace solo tras las instrucciones (cuenta atrás de 5 s para apartarse); con **f** se repite.
2. Entra en la escena. Aparece la caja punteada de colocación, **roja** mientras no haya nadie dentro.
3. Colócate dentro de la caja: pasa a **amarilla** tras 5 fotogramas seguidos dentro.
4. Quédate quieto: con unos 0,6 s sin moverte pasa a **verde** y sale «COMENZAR ESTIRAMIENTO». Si te mueves, vuelve a amarilla.

Parámetros ajustables (constantes al inicio de cada módulo): tamaño de la caja y grosor del trazo (`zona.py`), fotogramas de confirmación (`zona.py`), umbrales de quietud y fotogramas necesarios (`quietud.py`), área mínima de la silueta (`silueta.py`) y ruidos del filtro de Kalman (`seguimiento.py`). El umbral de quietud depende de los FPS y de la distancia a la cámara, así que habrá que revisarlo si cambia el montaje. Una superficie clara cercana puede unirse a la silueta y el fondo congelado falla ante cambios bruscos de luz; en ambos casos se repite el aprendizaje con **f**.

## Recorrido de una persona
1. **Calibrar** la escala (una vez por escenario, ver «Ejecución»).
2. **Registrarse** con **r** (solo la primera vez) y **entrar** con **e**: nombre y apellido y secuencia de patrones. Los datos personales se leen del perfil y salen junto al nombre.
3. Leer las **instrucciones** (figura animada y cinco pasos) y pulsar «He leído y entendido».
4. **Fondo automático**: pantalla roja con cuenta atrás de 5 s para apartarse del encuadre, aprendizaje del fondo y aviso verde «Fondo aprendido».
5. **Colocarse**: siéntate de lado con las piernas estiradas y las **manos en las rodillas**, quieto dentro de la zona marcada (aviso rojo hasta estar en el sitio).
6. **Medir**: al fijarse la posición de partida sale un aviso **amarillo** y suena un **pitido agudo**: extiende los brazos hacia los pies y mantén la postura. Unos 5 s después de tu mejor ventana suena un **pitido grave largo** y sale en verde «MEDICIÓN REALIZADA» con los centímetros (negativos si la yema no llega al pie). Si no hay ventana válida en 60 s, suenan dos graves cortos y sale «NO SE HA PODIDO MEDIR».
7. **Resultado**: una ventana detiene el vídeo con la medida y tres opciones: **repetir** (**n**; no hay que mover la cámara), **obtener el análisis de flexibilidad** (**a**, que compara la medida con el valor del modelo, aún pendiente) o **cerrar sesión** (**s**).
8. Cada toma se guarda sola en `datos/en_vivo/<usuario>/toma_AAAAMMDD_HHMMSS/` (`captura.png`, `grafica.png`, `serie.csv`, `resumen.json`).

Error esperado de la medida: unos 3–4 cm. Parámetros ajustables en `medida.py` (ventana, variaciones, subida mínima, fin sin mejora, límite) y `escala.py`.

## Cómo se usa el control de acceso
1. **Registrarse.** Pulsa **r**, escribe nombre y apellido y pulsa en orden los cuatro símbolos de la clave (se pueden repetir). Después, la ventana de datos personales (edad, sexo, altura y peso, con el rango de cada casilla en rojo) y «Guardar».
2. **Entrar.** Pulsa **e**, escribe el nombre y enseña a la cámara las tarjetas en el mismo orden. Cada símbolo aceptado aparece en el panel de abajo a la izquierda. Para repetir un símbolo hay que retirar la tarjeta y volver a enseñarla.
3. **Resultado.** Con la clave correcta sale *acceso concedido* y, a los 3 s, queda el usuario escrito arriba a la derecha (sesión abierta). Si no, sale *acceso denegado*. Tras **3 fallos seguidos** hay un bloqueo de 30 s en el que **e** no hace nada.
4. **Salir.** Con **s** se cierra la sesión y se puede entrar con otro usuario. Mientras hay una sesión abierta no se detectan las tarjetas.

Los usuarios se guardan en `usuarios.json` (nombre, sal y hash de la clave; nunca la clave) y sus datos personales en `datos/en_vivo/<usuario>/perfil.json`. Ambos **no se suben a GitHub**: cada persona tiene los suyos y debe registrarse en su ordenador. Las tarjetas se imprimen a partir de las imágenes de `patrones/`.

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
    puntos.py          puntos del cuerpo con MediaPipe Pose (tecla p) y yema del dedo
    escala.py          px por cm a partir de la hoja A4
    calibrar_escala.py calibración de la escala (python -m flexscan.calibrar_escala)
    medida.py          distancia yema-pie en cm y regla de validez de la medida
    registro_medida.py pitidos y guardado de cada toma (captura, gráfica, serie, resumen)
    escala_en_vivo.py  calibración de la escala dentro del programa (tecla k)
    perfil.py          datos personales: formulario, perfil.json y lectura al entrar
    instrucciones.py   ventana de instrucciones del ejercicio (figura animada y cinco pasos)
    preparacion.py     cuenta atrás y aprendizaje automático del fondo
    teclas.py          tabla única de teclas y fases del programa
    ventana_teclas.py  ventana de teclas (tecla h)
    bienvenida.py      presentación del proyecto
    pantalla_medida.py avisos temporizados de la medida (rojo, amarillo y verde)
    ventana_resultado.py  ventana de resultado: repetir, análisis o cerrar sesión
    ventana_analisis.py   ventana del análisis: medida frente al valor del modelo
    modelo_ml.py       punto de enganche del modelo de aprendizaje automático
docs/                prompt_gonzalo.md: contrato para integrar el modelo de ML
modelos/             modelo de MediaPipe Pose
patrones/            los cuatro símbolos en PNG
usuarios.json        usuarios registrados (local, no se sube a GitHub)
datos/               escala de la sesión, en_vivo/ (tomas guardadas por el programa) y pruebas_y_calibracion/ (ver datos/README.md)
C1-C2 - .../         calibración de la cámara (se ejecuta una vez)
requirements.txt     dependencias con versiones fijas
```

## Documentación
```
Propuesta_FlexScan_v3.pdf                          propuesta anterior (15 nov): tres pruebas e índice de flexibilidad
Propuesta_FlexScan_version_final.pdf               propuesta final (17 nov), ajustada a las decisiones del desarrollo
FlexScan_Plan_de_trabajo.pdf                       plan por bloques y estado
FlexScan_C1-C2_Calibracion_y_preparacion.pdf       cuaderno técnico: calibración y preparación
FlexScan_C3-C4_Deteccion_de_patrones.pdf           cuaderno técnico: cámara y detección de patrones
FlexScan_C5_Seguridad.pdf                          cuaderno técnico: control de acceso
FlexScan_C6_Tracker.pdf                            cuaderno técnico: tracker y caja de colocación
FlexScan_C7_Puntos_clave.pdf                       cuaderno técnico: puntos clave y medida de flexibilidad
FlexScan_C8_Integracion.pdf                        cuaderno técnico: integración del recorrido completo
FlexScan_Explicaciones_tecnicas.docx               cuaderno técnico en curso (C9 en adelante; vacío por ahora)
```
Cada grupo de bloques cerrado se pasa a su propio PDF y el Word queda libre para el siguiente.

## Calibración
La cámara se calibró con 19 fotos de un damero (9×6 esquinas, cuadro de 23 mm), con un error RMS de 1,52 px. Los parámetros se guardan en `calibracion.npz`, único fichero que el programa necesita de esa fase. Si se cambia de cámara o de resolución, hay que recalibrar y sustituirlo.

**Importante:** ese `calibracion.npz` es de la cámara de Mateo. Con otra cámara hay que pulsar **c** para desactivar la corrección (o recalibrar).

## Autores
Mateo Gómez-Acebo · Gonzalo Crespo Comín
