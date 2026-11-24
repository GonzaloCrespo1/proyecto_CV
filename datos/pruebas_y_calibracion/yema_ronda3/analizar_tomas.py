"""Analiza las tomas de medida de ruido y sesgo de la yema (ronda 3).

Lee verdad.csv (clics de la yema y la punta del pie reales) y toma_N.csv
(fotograma a fotograma: dedo, muñeca y pie de ambos lados) de esta carpeta.
Uso:  python analizar_tomas.py
"""
import csv
import numpy as np

K_ACTUAL = 1.64          # factor con el que se grabaron las tomas
DESCARTADAS = {1}        # toma 1: el modelo puso el dedo en otro sitio
MAXIMA_FLEXION = [2, 3, 6, 7, 9]
BRAZOS_RECTOS = [4, 8]

verdad = {int(f["toma"]): f for f in csv.DictReader(open("verdad.csv"))}


def cargar(n):
    R = np.genfromtxt(f"toma_{n}.csv", delimiter=",", names=True)
    m = R["t"] >= 2.0                      # se descartan los 2 primeros segundos
    lado = "i" if R["dedo_i_vis"][m].mean() >= R["dedo_d_vis"][m].mean() else "d"
    ind = np.c_[R[f"dedo_{lado}_x"], R[f"dedo_{lado}_y"]][m]
    mun = np.c_[R[f"mun_{lado}_x"], R[f"mun_{lado}_y"]][m]
    return ind, mun


def k_implicito(n):
    """K que haría coincidir la yema estimada con el clic de la yema real."""
    ind, mun = cargar(n)
    yema = np.array([float(verdad[n]["yema_x"]), float(verdad[n]["yema_y"])])
    mi, mm = np.median(ind, 0), np.median(mun, 0)
    v = mi - mm
    return ((yema - mi) @ v) / (v @ v)


def error_x(n, K):
    ind, mun = cargar(n)
    punta = np.median(ind + K * (ind - mun), 0)
    return punta[0] - float(verdad[n]["yema_x"])


ks = {n: k_implicito(n) for n in verdad if n not in DESCARTADAS}
print("K implícito por toma:", {n: round(k, 2) for n, k in ks.items()})
for nombre, lista in (("máxima flexión", MAXIMA_FLEXION), ("brazos rectos", BRAZOS_RECTOS)):
    v = np.array([ks[n] for n in lista])
    print(f"{nombre}: mediana {np.median(v):.2f}, media {v.mean():.2f}, std {v.std(ddof=1) if len(v) > 1 else float('nan'):.2f}")

print("\nError horizontal medio de la yema en máxima flexión (px):")
for K in (0.0, 1.0, 1.15, 1.3, 1.64):
    e = np.array([error_x(n, K) for n in MAXIMA_FLEXION])
    print(f"  K = {K:<4}: |error| medio {np.abs(e).mean():5.1f}   con signo {e.mean():+5.1f}")
loo = []
for n in MAXIMA_FLEXION:
    K = np.median([ks[m] for m in MAXIMA_FLEXION if m != n])
    loo.append(error_x(n, K))
print(f"  Validación dejando una toma fuera: |error| medio {np.abs(loo).mean():.1f} px")
