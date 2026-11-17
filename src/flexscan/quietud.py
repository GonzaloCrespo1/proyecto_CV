"""Decide si la persona está quieta a partir de la velocidad estimada por Kalman."""

UMBRAL_QUIETO = 0.5    # px/fotograma: por debajo, cuenta como quieta
UMBRAL_SALIDA = 1.0    # px/fotograma: por encima, deja de estar quieta (histéresis)
FRAMES_QUIETO = 15     # fotogramas seguidos bajo el umbral para pasar a quieta


class Quietud:
    def __init__(self):
        self.seguidos = 0
        self.quieta = False

    def actualizar(self, estimado):
        if estimado is None:                       # sin estimación del filtro
            self.seguidos = 0
            self.quieta = False
            return False
        modulo = (estimado[2] ** 2 + estimado[3] ** 2) ** 0.5
        self.seguidos = self.seguidos + 1 if modulo < UMBRAL_QUIETO else 0
        if not self.quieta and self.seguidos >= FRAMES_QUIETO:
            self.quieta = True
        elif self.quieta and modulo > UMBRAL_SALIDA:
            self.quieta = False
            self.seguidos = 0
        return self.quieta
