"""Gráficas y números del modelo del sit-and-reach esperado (bloque C11, paso 7).

1. Diagnóstico con el 20 % de test (sintético): el modelo se entrena con el 80 %, igual que en
   entrenar_modelos.py, para no evaluarlo con personas que ya ha visto. Predicho frente a real,
   residuos frente a lo predicho y frente a cada variable de entrada, e histograma de residuos.
2. Qué ha aprendido: la fórmula en unidades reales y el valor esperado según la edad, con el
   modelo guardado en modelos/sit_reach.joblib (el que usa FlexScan).
3. Contraste con las medidas reales de datos/medidas_reales.csv (si existe; no se sube a GitHub).

Las figuras se guardan en figuras/. Uso (desde la raíz del repositorio):
    python "C11 - Datos y modelo/graficas_modelo.py"
"""

from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")                    # solo se guardan ficheros, no se abre ninguna ventana
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                       # noqa: E402
import pandas as pd                      # noqa: E402
from scipy.stats import norm             # noqa: E402
from sklearn.base import clone           # noqa: E402

from entrenar_modelos import ENTRADAS, MODELO, OBJETIVO, cargar_y_partir   # noqa: E402

CARPETA = Path(__file__).resolve().parent
FIGURAS = CARPETA / "figuras"
REALES = CARPETA / "datos" / "medidas_reales.csv"

AZUL, VERDE, NARANJA, GRIS = "#12263F", "#1F8A8A", "#E09F00", "#8A96A3"
COLORES = {1: AZUL, 0: VERDE}
NOMBRES = {1: "Hombres", 0: "Mujeres"}
plt.rcParams.update({"font.family": ["Lato", "Inter", "Segoe UI", "DejaVu Sans"], "font.size": 11,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titlesize": 13, "figure.dpi": 100})


def guardar(fig, nombre):
    FIGURAS.mkdir(exist_ok=True)
    fig.savefig(FIGURAS / nombre, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"   figura: figuras/{nombre}")


def media_por_tramos(x, r, tramos=10):
    """Media de los residuos en tramos de x con el mismo número de personas (para ver tendencias)."""
    bordes = np.unique(np.quantile(x, np.linspace(0, 1, tramos + 1)))
    grupo = np.clip(np.searchsorted(bordes, x, side="right") - 1, 0, len(bordes) - 2)
    centros = [x[grupo == g].mean() for g in range(len(bordes) - 1)]
    medias = [r[grupo == g].mean() for g in range(len(bordes) - 1)]
    errores = [r[grupo == g].std(ddof=1) / np.sqrt((grupo == g).sum()) for g in range(len(bordes) - 1)]
    return np.array(centros), np.array(medias), np.array(errores)


def diagnostico(guardado):
    """Entrena con el 80 %, predice el 20 % de test y dibuja las cuatro figuras de diagnóstico."""
    entreno, test = cargar_y_partir()
    modelo = clone(guardado["modelo"]).fit(entreno[ENTRADAS], entreno[OBJETIVO])
    y, pred = test[OBJETIVO].to_numpy(), modelo.predict(test[ENTRADAS])
    r = y - pred
    sigma = r.std(ddof=1)
    rmse = np.sqrt((r ** 2).mean())
    r2 = 1 - (r ** 2).sum() / ((y - y.mean()) ** 2).sum()
    sexo = test["sexo"].to_numpy()
    print(f"== Test ({len(test)} personas): RMSE {rmse:.2f} cm · R² {r2:.3f} · sesgo {r.mean():+.2f} cm"
          f" · sigma {sigma:.2f} cm")
    for k in (1, 2):
        print(f"   dentro de ±{k}σ: {np.mean(np.abs(r) <= k * sigma):.1%}"
              f" (una normal daría {norm.cdf(k) - norm.cdf(-k):.1%})")

    # 1) Predicho frente a real
    fig, ax = plt.subplots(figsize=(6.2, 5.6))
    for s in (1, 0):
        m = sexo == s
        ax.scatter(pred[m], y[m], s=10, alpha=0.35, color=COLORES[s], label=NOMBRES[s])
    lim = [min(y.min(), pred.min()) - 2, max(y.max(), pred.max()) + 2]
    ax.plot(lim, lim, color=NARANJA, lw=2, label="predicción perfecta (y = x)")
    ax.set(xlim=lim, ylim=lim, xlabel="sit-and-reach predicho (cm)", ylabel="sit-and-reach real (cm)",
           title="Predicho frente a real (test)")
    ax.text(0.03, 0.97, f"RMSE = {rmse:.2f} cm\nR² = {r2:.2f}", transform=ax.transAxes, va="top")
    ax.legend(loc="lower right", frameon=True, facecolor="white", edgecolor="white", framealpha=0.9)
    guardar(fig, "pred_frente_real_test.png")

    # 2) Residuos frente a lo predicho
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    ax.scatter(pred, r, s=10, alpha=0.3, color=GRIS)
    c, mu, e = media_por_tramos(pred, r)
    ax.errorbar(c, mu, yerr=1.96 * e, color=NARANJA, lw=2, marker="o", capsize=3,
                label="media por tramos (IC 95 %)")
    ax.axhline(0, color=AZUL, lw=1.2)
    for k in (-1, 1):
        ax.axhline(k * sigma, color=AZUL, lw=1, ls="--")
    ax.text(pred.max(), sigma, " +σ", va="bottom", ha="right", color=AZUL)
    ax.text(pred.max(), -sigma, " −σ", va="top", ha="right", color=AZUL)
    ax.set(xlabel="sit-and-reach predicho (cm)", ylabel="residuo = real − predicho (cm)",
           title="Residuos frente a lo predicho (test)")
    ax.legend(loc="lower left", frameon=False)
    guardar(fig, "residuos_frente_predicho.png")

    # 3) Residuos frente a cada variable de entrada
    fig, ejes = plt.subplots(2, 2, figsize=(11, 8))
    for ax, (col, etiqueta) in zip(ejes.flat[:3], [("edad", "edad (años)"), ("altura_cm", "altura (cm)"),
                                                    ("peso_kg", "peso (kg)")]):
        x = test[col].to_numpy(dtype=float)
        ax.scatter(x, r, s=8, alpha=0.25, color=GRIS)
        c, mu, e = media_por_tramos(x, r)
        ax.errorbar(c, mu, yerr=1.96 * e, color=NARANJA, lw=2, marker="o", capsize=3)
        ax.axhline(0, color=AZUL, lw=1.2)
        ax.set(xlabel=etiqueta, ylabel="residuo (cm)", title=f"Residuos frente a {etiqueta.split(' ')[0]}")
    ax = ejes.flat[3]
    cajas = ax.boxplot([r[sexo == 1], r[sexo == 0]], tick_labels=["Hombres", "Mujeres"], widths=0.5,
                       patch_artist=True, medianprops={"color": NARANJA, "lw": 2})
    for caja, color in zip(cajas["boxes"], (AZUL, VERDE)):
        caja.set(facecolor=color, alpha=0.35, edgecolor=color)
    ax.axhline(0, color=AZUL, lw=1.2)
    for i, s in enumerate((1, 0), 1):
        ax.text(i + 0.3, r[sexo == s].mean(), f"media\n{r[sexo == s].mean():+.2f} cm", va="center", fontsize=9)
    ax.set(ylabel="residuo (cm)", title="Residuos por sexo")
    fig.suptitle("Si el modelo capta toda la información, las medias (naranja) quedan en 0", y=1.0)
    fig.tight_layout()
    guardar(fig, "residuos_frente_variables.png")
    print("   media de los residuos por sexo:",
          {NOMBRES[s]: round(float(r[sexo == s].mean()), 2) for s in (1, 0)})

    # 4) Histograma de residuos con la normal N(0, sigma)
    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    ax.hist(r, bins=35, density=True, color=GRIS, alpha=0.6, label="residuos en test")
    xs = np.linspace(r.min(), r.max(), 300)
    ax.plot(xs, norm.pdf(xs, 0, sigma), color=NARANJA, lw=2.2, label=f"normal N(0; {sigma:.2f})")
    for k in (-1, 1):
        ax.axvline(k * sigma, color=AZUL, lw=1, ls="--")
    dentro = np.mean(np.abs(r) <= sigma)
    ax.text(0, ax.get_ylim()[1] * 0.97, f"{dentro:.0%} entre −σ y +σ", ha="center", va="top", color=AZUL)
    ax.set(xlabel="residuo (cm)", ylabel="densidad", title="Distribución de los residuos (test)")
    ax.legend(frameon=False)
    guardar(fig, "histograma_residuos.png")


def aprendido(guardado, df):
    """Fórmula del modelo guardado en unidades reales y valor esperado según la edad."""
    escalado, ridge = guardado["modelo"].named_steps.values()
    pesos = ridge.coef_ / escalado.scale_                     # cm por unidad de cada entrada
    termino = ridge.intercept_ - (pesos * escalado.mean_).sum()
    print("== Modelo guardado (100 % de los datos):")
    print(f"   esperado = {termino:+.2f} " + " ".join(f"{p:+.3f}·{n}" for n, p in zip(ENTRADAS, pesos)))
    for n, p, u in zip(ENTRADAS, pesos, ["año", "cm", "kg", "(hombre = 1)"]):
        print(f"   {n:<10} {p:+.3f} cm por {u}")

    sigma = guardado["sigma_cm"]
    edades = np.arange(20, 70)
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    for s in (1, 0):
        tipico = df[df["sexo"] == s][["altura_cm", "peso_kg"]].median()
        filas = pd.DataFrame({"edad": edades, "altura_cm": tipico["altura_cm"],
                              "peso_kg": tipico["peso_kg"], "sexo": s})[ENTRADAS]
        esperado = guardado["modelo"].predict(filas)
        ax.plot(edades, esperado, color=COLORES[s], lw=2.2,
                label=f"{NOMBRES[s]} ({tipico['altura_cm']:.0f} cm, {tipico['peso_kg']:.0f} kg)")
        ax.fill_between(edades, esperado - sigma, esperado + sigma, color=COLORES[s], alpha=0.12)
    ax.axhline(0, color=GRIS, lw=1, ls=":")
    ax.set(xlabel="edad (años)", ylabel="sit-and-reach esperado (cm)",
           title="Valor esperado según la edad (banda: ±σ)")
    ax.legend(frameon=False, loc="upper right")
    guardar(fig, "esperado_segun_edad.png")


def contraste_real(guardado):
    """Medidas reales frente al modelo de FlexScan: tabla, sesgo, dispersión y gráfica."""
    if not REALES.exists():
        print("== Sin medidas reales (datos/medidas_reales.csv no existe): se omite el contraste.")
        return
    reales = pd.read_csv(REALES)
    reales["sexo_num"] = (reales["sexo"].str.lower() == "hombre").astype(int)
    filas = reales.rename(columns={"sexo_num": "sexo_m"})[["edad", "altura_cm", "peso_kg", "sexo_m"]]
    filas = filas.rename(columns={"sexo_m": "sexo"})[ENTRADAS]
    sigma = guardado["sigma_cm"]
    reales["esperado_cm"] = guardado["modelo"].predict(filas).round(1)
    reales["residuo_cm"] = (reales["medida_cm"] - reales["esperado_cm"]).round(1)
    reales["z"] = (reales["residuo_cm"] / sigma).round(2)
    n, r = len(reales), reales["residuo_cm"]
    print(f"== Medidas reales ({n} personas)")
    print(reales[["persona", "edad", "sexo", "altura_cm", "peso_kg", "medida_cm", "esperado_cm",
                  "residuo_cm", "z"]].to_string(index=False))
    print(f"   sesgo medio {r.mean():+.2f} cm (IC 95 % ±{1.96 * r.std(ddof=1) / np.sqrt(n):.2f})"
          f" · desv. típica de los residuos {r.std(ddof=1):.2f} cm frente a sigma {sigma:.2f}"
          f" · dentro de ±1σ: {int((reales['z'].abs() <= 1).sum())} de {n}")

    fig, ax = plt.subplots(figsize=(6.4, 5.6))
    lim = [min(reales["medida_cm"].min(), reales["esperado_cm"].min()) - 12,
           max(reales["medida_cm"].max(), reales["esperado_cm"].max()) + 12]
    xs = np.array(lim)
    ax.fill_between(xs, xs - sigma, xs + sigma, color=GRIS, alpha=0.15, label="±σ alrededor de y = x")
    ax.plot(xs, xs, color=NARANJA, lw=2, label="medida = esperado")
    for s in (1, 0):
        m = reales["sexo_num"] == s
        ax.scatter(reales.loc[m, "esperado_cm"], reales.loc[m, "medida_cm"], s=60, color=COLORES[s],
                   label=NOMBRES[s], zorder=3)
    for _, f in reales.iterrows():
        ax.annotate(f["persona"], (f["esperado_cm"], f["medida_cm"]), xytext=(6, 4),
                    textcoords="offset points", fontsize=9)
    ax.set(xlim=lim, ylim=lim, xlabel="sit-and-reach esperado por el modelo (cm)",
           ylabel="sit-and-reach medido con FlexScan (cm)", title=f"Medidas reales ({n} personas)")
    ax.legend(frameon=False, loc="upper left")
    guardar(fig, "contraste_medidas_reales.png")


if __name__ == "__main__":
    guardado = joblib.load(MODELO)
    diagnostico(guardado)
    aprendido(guardado, pd.read_csv(CARPETA / "datos" / "dataset_sintetico.csv"))
    contraste_real(guardado)
