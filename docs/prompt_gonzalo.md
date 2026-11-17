# Prompt para Claude de Gonzalo: integrar el modelo de ML en FlexScan

> Pega este documento entero como primer mensaje en la sesión de Claude de Gonzalo, con el repositorio clonado.
> Está escrito para que Claude sepa **qué datos puede usar, dónde entrega su valor y qué archivos no debe tocar**.

---

## 1. Contexto

FlexScan es un programa de Visión por Ordenador I (3º IMAT, ICAI) que mide la flexibilidad con una sola webcam
mediante el ejercicio **sit-and-reach** (sentado, brazos hacia los pies). Mateo Gómez-Acebo ha construido toda la
parte de cámara: calibración, acceso con patrón de símbolos, seguimiento, puntos del cuerpo, medida y pantallas.
Tu parte, la de Gonzalo Crespo Comín, es el **modelo de aprendizaje automático** que compara la medida
experimental con una estimación del modelo.

El recorrido completo ya funciona y está probado. Al terminar la medida, la persona ve una ventana con su resultado
y un botón **«Obtener análisis de flexibilidad»**. Ese botón abre una pantalla con una animación y, al terminar,
enseña dos valores lado a lado:

- **Tu medida experimental** (la de FlexScan), en cm.
- **Modelo de aprendizaje automático**: el valor que devuelva tu modelo. Hoy sale el texto «valor_ml» con la
  etiqueta «pendiente del modelo».

El veredicto final automático (MUY FLEXIBLE, POCO FLEXIBLE…, según la diferencia entre ambos valores) **se hará
después**, cuando el modelo esté terminado. No lo implementes ahora.

## 2. Qué tienes que hacer

Escribir el modelo y conectarlo en **un único punto**: el archivo `src/flexscan/modelo_ml.py`.

1. Implementa el cuerpo de `predecir_valor_ml(ruta_toma)`.
2. Cambia `MODELO_LISTO = False` por `MODELO_LISTO = True`.

No hace falta ningún otro cambio para que aparezca tu valor en pantalla.

```python
# src/flexscan/modelo_ml.py  (ya existe; solo se rellena esto)
MODELO_LISTO = False

def predecir_valor_ml(ruta_toma):
    """Valor del modelo para la toma guardada en `ruta_toma`, o None si todavía no hay modelo."""
```

**Contrato de la función**

- **Entrada:** `ruta_toma`, la carpeta de la toma recién guardada, p. ej.
  `datos/en_vivo/<usuario>/toma_20261117_131354/`. Ya existe cuando se llama a la función.
- **Salida:** un `float` **en centímetros**, en las mismas unidades que `medida_cm`, para poder compararlos
  directamente. Si devuelves `None`, la pantalla vuelve a mostrar «valor_ml pendiente», sin romper nada.
- Si tu modelo devuelve otra cosa (una clase, una probabilidad…), **habladlo antes con Mateo**: cambia la pantalla.
- **Velocidad:** la función se llama con la ventana de vídeo parada. Debe tardar menos de 1 segundo. Carga el
  modelo **una sola vez** (al importar el módulo o con una caché), nunca en cada llamada.
- **Solo calcula:** no abras ventanas (`cv2.imshow`), no pidas datos por teclado, no uses internet ni GPU.
- Cualquier excepción se captura fuera y se trata como «sin modelo», pero conviene que tu código no lance
  errores con tomas normales.

## 3. Qué datos tienes de cada toma

Carpeta `datos/en_vivo/<usuario>/toma_AAAAMMDD_HHMMSS/`:

| Archivo | Contenido |
|---|---|
| `resumen.json` | Todo lo importante de la toma (abajo). |
| `serie.csv` | Dos columnas, `t_s` y `d_cm`: la distancia dedo-pie a lo largo del tiempo (unos 20 datos por segundo). |
| `captura.png` | Imagen de la toma con los puntos del cuerpo y el resultado. |
| `grafica.png` | Gráfica de la distancia frente al tiempo. |

`resumen.json` (ejemplo real, con el usuario anonimizado):

```json
{
  "usuario": "ejemplo",
  "perfil": {"edad": 20, "sexo": "hombre", "altura_cm": 188, "peso_kg": 75, "fecha": "2026-11-17 10:39:41"},
  "fecha": "2026-11-17 13:13:54",
  "estado": "terminada",
  "medida_cm": -4.7,
  "mejor_candidata_cm": -4.7,
  "base_cm": -48.7,
  "t_base_s": 3.53,
  "ventana_mejor_s": [8.18, 10.18],
  "t_fin_s": 15.2,
  "px_por_cm": 4.877,
  "parametros": {"ventana_s": 2.0, "variacion_base_cm": 4.0, "variacion_max_cm": 6.0,
                 "subida_min_cm": 10.0, "fin_sin_mejora_s": 5.0, "limite_s": 60.0}
}
```

Qué significa cada campo:

- **`perfil`**: datos que la persona rellena al registrarse (`edad`, `sexo`, `altura_cm`, `peso_kg`). Son las
  variables «personales» candidatas para el modelo.
- **`medida_cm`**: la medida experimental final. Es la mediana de la mejor ventana estable de 2 s. Es `null` si la
  medida falló (`estado` = `"fallida"`).
- **Punto cero y signo.** La distancia es la horizontal entre la **yema del dedo** y la **vertical que pasa por el
  punto del pie**. Es **positiva** si la yema supera ese punto (más flexible) y **negativa** si no llega (menos
  flexible). Está en centímetros gracias a la escala calibrada con una hoja A4 (`px_por_cm`).
- **`base_cm`**: distancia de partida, con las manos sobre las rodillas, antes de estirar.
- **`serie.csv`**: la curva completa. Los primeros 1-2 s pueden traer valores espurios mientras el programa detecta
  el cuerpo (se ven en `grafica.png`); no los tomes como datos de la persona.
- Un solo ejercicio, un solo tipo de toma. Cada persona puede tener varias tomas; se guardan todas.

## 4. Reglas para no pisar el trabajo de Mateo

**Solo puedes modificar:**

- `src/flexscan/modelo_ml.py` (es tu punto de enganche).
- Código nuevo tuyo en una carpeta nueva, por ejemplo `src/flexscan/ml/` (entrenamiento, utilidades), o fuera de
  `src/` si prefieres (`ml/` en la raíz).
- Los pesos o ficheros del modelo, en `modelos/` (pero **no toques `modelos/pose.task`**, que usa el programa).
- `requirements.txt`: **solo añadir** líneas, con versión exacta. No cambies ni borres las que hay.

**No modifiques, ni siquiera para «mejorar» algo:**

- `src/flexscan/__main__.py` y el resto de archivos de `src/flexscan/` (pantallas, medida, seguimiento, acceso,
  registro, teclas, calibración…).
- `datos/` (hay datos reales y de calibración), `patrones/`, `usuarios.json`, los PDF, el Word y el README.
  No subas al repositorio datos personales de otras personas.

**Flujo de trabajo con git:**

- Mateo fusionará su rama `c8-integracion` en `main` antes de que empieces. Trabaja desde `main` actualizado, en una
  rama propia (por ejemplo `ml-gonzalo`), y propón los cambios con un Pull Request. No hagas `push --force` ni
  commits directos en `main`.
- Si necesitas algo que esté en los archivos protegidos (otro dato en `resumen.json`, otro formato…), **no lo
  cambies tú**: descríbeselo a Mateo y lo acordáis.

## 5. Cómo probar tu parte sin la cámara

`modelo_ml.py` solo importa `json` y `pathlib`, así que se prueba sin cámara ni MediaPipe:

```bash
python -c "from flexscan.modelo_ml import predecir_valor_ml; print(predecir_valor_ml('datos/en_vivo/<usuario>/toma_AAAAMMDD_HHMMSS'))"
```

(con `src` en el `PYTHONPATH`). Para ver tu valor en la pantalla del programa, hay que ejecutar `python -m flexscan`
con la cámara: haz el recorrido completo, pulsa **«Obtener análisis de flexibilidad»** y comprueba que aparece tu
número junto a la medida experimental.

## 6. Qué documentar, para el veredicto final

Deja escrito en la cabecera de `modelo_ml.py` (o en un `README` dentro de tu carpeta):

- **Qué predice** exactamente el modelo: ¿los centímetros esperados para ese perfil?, ¿otra cosa?
- **Con qué entradas** (columnas de `perfil`, `serie.csv`, etc.) y con qué datos de entrenamiento: cuántas personas
  y tomas, de dónde vienen y si hay **consentimiento y anonimización**.
- **Error esperado** (por ejemplo RMSE en cm) y cómo se ha validado.

Con eso se fijarán después los umbrales del veredicto (MUY FLEXIBLE, POCO FLEXIBLE…) a partir de la diferencia
entre `valor_ml` y `medida_cm`.

## 7. Lista de comprobación antes de entregar

- [ ] `predecir_valor_ml` devuelve un `float` en cm o `None`, en menos de 1 s.
- [ ] `MODELO_LISTO = True` y el valor sale en la pantalla del análisis, junto a la medida experimental.
- [ ] No se ha modificado ningún archivo protegido (`git diff main --stat` solo muestra `modelo_ml.py`, tu carpeta,
      `modelos/` y `requirements.txt`).
- [ ] Las dependencias nuevas están en `requirements.txt` con versión exacta.
- [ ] Está documentado qué predice el modelo, con qué datos y con qué error.
