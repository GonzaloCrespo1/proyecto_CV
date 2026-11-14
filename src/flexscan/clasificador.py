"""Clasificador por reglas: decide qué símbolo es a partir de sus rasgos."""
from flexscan.rasgos import Rasgos

VERTICES_REDONDO = 7   # un hueco con al menos tantos vértices se considera redondo
DESCONOCIDO = "desconocido"


def clasificar(r: Rasgos) -> str:
    """Rasgos -> nombre del símbolo, o 'desconocido' si no encaja con ninguno."""
    if r.n_manchas == 3 and r.n_huecos == 0:
        return "barras"
    if r.n_manchas == 1 and r.n_huecos == 1 and r.vertices == (3,):
        return "triangulo"
    if r.n_manchas == 2 and r.n_huecos == 1 and r.vertices == (6,):
        return "hexagono"
    if (r.n_manchas == 3 and r.n_huecos == 2
            and all(v >= VERTICES_REDONDO for v in r.vertices)):
        return "circulos"
    return DESCONOCIDO