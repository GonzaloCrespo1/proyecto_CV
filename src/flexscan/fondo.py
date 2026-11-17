"""Modelo de fondo: aprende la escena vacía y devuelve lo que no encaja con ella."""
import cv2

FOTOGRAMAS = 60   # fotogramas de aprendizaje (unos 2 s)      
TASA = 0.05       # ritmo de aprendizaje: memoria ~ 1/TASA = 20 fotogramas   
UMBRAL = 40       # distancia de Mahalanobis al cuadrado (~6 desviaciones)  


class Fondo:
    """Sustractor MOG2 con una fase de aprendizaje y luego congelado."""

    def __init__(self, fotogramas=FOTOGRAMAS):
        self.fotogramas = fotogramas
        self.restantes = 0
        self.mog = None

    def aprender(self):
        """Empieza de cero: la escena debe estar vacía durante el aprendizaje."""
        self.mog = cv2.createBackgroundSubtractorMOG2(
            varThreshold=UMBRAL, detectShadows=True)
        self.restantes = self.fotogramas

    @property
    def aprendiendo(self):
        return self.restantes > 0

    def aplicar(self, frame):
        """Aprende mientras queden fotogramas; después devuelve la máscara."""
        if self.mog is None:
            return None
        if self.restantes > 0:
            self.mog.apply(frame, learningRate=TASA)
            self.restantes -= 1
            return None
        return self.mog.apply(frame, learningRate=0)   # fondo congelado