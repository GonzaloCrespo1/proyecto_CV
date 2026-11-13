"""Medición de fotogramas por segundo (FPS)."""
import time


class ContadorFPS:
    """Estima los FPS suavizando la medida con una media móvil exponencial."""

    def __init__(self, alpha=0.1):
        self.alpha = alpha
        self.fps = 0.0
        self._ultimo = time.perf_counter()

    def actualizar(self):
        """Llamar una vez por fotograma. Devuelve los FPS suavizados."""
        ahora = time.perf_counter()
        dt = ahora - self._ultimo
        self._ultimo = ahora

        if dt > 0:
            instantaneo = 1.0 / dt
            if self.fps == 0.0:
                self.fps = instantaneo
            else:
                self.fps = self.alpha * instantaneo + (1 - self.alpha) * self.fps
        return self.fps