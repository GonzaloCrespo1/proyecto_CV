"""Seguimiento del centro de la persona con un filtro de Kalman de velocidad constante."""
import cv2
import numpy as np

VAR_MEDIDA = 25.0       # Q_t: varianza del error del detector (px²), σ = 5 px
VAR_MODELO_POS = 1.0    # R_t: lo que el modelo no explica en la posición
VAR_MODELO_VEL = 0.1    # R_t: lo que el modelo no explica en la velocidad
SIGMA_VEL0 = 10.0       # σ inicial de la velocidad (px/fotograma): se desconoce
MAX_PERDIDOS = 15       # fotogramas sin medida antes de dar el seguimiento por perdido


class Seguidor:
    def __init__(self):
        self.kf = cv2.KalmanFilter(4, 2)    # estado (u, v, du, dv) y medida (u, v)
        self.kf.transitionMatrix = np.array([[1, 0, 1, 0],
                                             [0, 1, 0, 1],
                                             [0, 0, 1, 0],
                                             [0, 0, 0, 1]], np.float32)    # A
        self.kf.measurementMatrix = np.array([[1, 0, 0, 0],
                                              [0, 1, 0, 0]], np.float32)   # C
        self.kf.processNoiseCov = np.diag(
            [VAR_MODELO_POS, VAR_MODELO_POS,
             VAR_MODELO_VEL, VAR_MODELO_VEL]).astype(np.float32)           # R_t
        self.kf.measurementNoiseCov = VAR_MEDIDA * np.eye(2, dtype=np.float32)  # Q_t
        self.iniciado = False
        self.perdidos = 0

    def actualizar(self, centro):
        """Recibe el centro medido (u, v) o None; devuelve (u, v, du, dv) o None."""
        if centro is None:
            self.perdidos += 1
            if not self.iniciado or self.perdidos > MAX_PERDIDOS:
                self.iniciado = False
                return None
            return tuple(float(x) for x in self.kf.predict()[:, 0])   # solo predicción

        if not self.iniciado:        # t = 0: posición medida, velocidad desconocida
            self.kf.statePost = np.array([[centro[0]], [centro[1]], [0], [0]], np.float32)
            self.kf.errorCovPost = np.diag(
                [VAR_MEDIDA, VAR_MEDIDA, SIGMA_VEL0 ** 2, SIGMA_VEL0 ** 2]).astype(np.float32)
            self.iniciado = True
            self.perdidos = 0
            return centro[0], centro[1], 0.0, 0.0

        self.perdidos = 0
        self.kf.predict()
        medida = np.array([[centro[0]], [centro[1]]], np.float32)
        return tuple(float(x) for x in self.kf.correct(medida)[:, 0])
