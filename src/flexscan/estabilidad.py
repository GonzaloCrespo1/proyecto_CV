"""Estabilizador: da un símbolo por bueno solo si se repite varios fotogramas."""

FRAMES_ESTABLE = 5   # fotogramas seguidos con la misma lectura para confirmarla


class Estabilizador:
    """Recuerda la última lectura estable (None = no hay tarjeta)."""

    def __init__(self, frames=FRAMES_ESTABLE):
        self.frames = frames
        self.candidato = None   # última lectura recibida
        self.cuenta = 0         # fotogramas seguidos con esa lectura
        self.estable = None     # lectura ya confirmada

    def actualizar(self, lectura):
        """Recibe la lectura del fotograma y devuelve la lectura estable."""
        if lectura == self.candidato:
            self.cuenta += 1
        else:
            self.candidato = lectura
            self.cuenta = 1
        if self.cuenta >= self.frames:
            self.estable = self.candidato
        return self.estable