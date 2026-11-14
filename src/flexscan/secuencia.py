"""Máquina de estados de la entrada: recoge los símbolos mostrados y decide si se concede el acceso."""
from flexscan import usuarios
from flexscan.clasificador import DESCONOCIDO

ESPERANDO = "esperando"
EN_CURSO = "en curso"
CONCEDIDO = "concedido"
DENEGADO = "denegado"
BLOQUEADO = "bloqueado"

TIEMPO_MAX = 10.0        # segundos máximos entre dos símbolos antes de empezar de cero
PAUSA_RESULTADO = 2.0    # segundos que se muestra "denegado" antes de volver a empezar
MAX_INTENTOS = 3         # fallos seguidos antes de bloquear
TIEMPO_BLOQUEO = 30.0    # segundos de bloqueo
PAUSA_CONCEDIDO = 3.0    # segundos que se muestra "concedido" antes de abrir la sesión


class Secuencia:
    """Recibe en cada fotograma el símbolo estable y va completando la secuencia."""

    def __init__(self, nombre, ruta=usuarios.RUTA):
        self.nombre = nombre
        self.ruta = ruta
        self.estado = ESPERANDO
        self.simbolos = []       # símbolos aceptados en este intento
        self.intentos = 0        # fallos seguidos
        self._visto = None       # último símbolo visto sin haber retirado la tarjeta
        self._t_cambio = 0.0     # instante del último símbolo aceptado o cambio de estado

    def reiniciar(self):
        """Empieza un intento nuevo. No borra los fallos ni obliga a retirar la tarjeta."""
        self.estado = ESPERANDO
        self.simbolos = []
        
    def segundos_bloqueo(self, ahora):                                    
        """Segundos que faltan para que acabe el bloqueo (0 si no está bloqueado)."""   
        if self.estado != BLOQUEADO:                                      
            return 0.0                                                    
        return max(0.0, TIEMPO_BLOQUEO - (ahora - self._t_cambio))        

    def sesion_lista(self, ahora):                                                         
        """True cuando el acceso está concedido y el mensaje ya se ha mostrado el tiempo suficiente."""   
        return self.estado == CONCEDIDO and ahora - self._t_cambio >= PAUSA_CONCEDIDO  
        
    def actualizar(self, simbolo, ahora):
        """simbolo: None (sin tarjeta), DESCONOCIDO o un símbolo. ahora: tiempo en segundos."""
        if self.estado == CONCEDIDO:
            return self.estado
        if self.estado in (DENEGADO, BLOQUEADO):
            espera = PAUSA_RESULTADO if self.estado == DENEGADO else TIEMPO_BLOQUEO
            if ahora - self._t_cambio >= espera:
                if self.estado == BLOQUEADO:
                    self.intentos = 0
                self.reiniciar()
            return self.estado
        if self.estado == EN_CURSO and ahora - self._t_cambio > TIEMPO_MAX:
            self.reiniciar()
        if simbolo is None:
            self._visto = None           # tarjeta retirada: el mismo símbolo puede volver a contar
            return self.estado
        if simbolo == DESCONOCIDO or simbolo == self._visto:
            return self.estado
        self._visto = simbolo
        self.simbolos.append(simbolo)
        self._t_cambio = ahora
        self.estado = EN_CURSO
        if len(self.simbolos) == usuarios.LONGITUD:
            self._decidir(ahora)
        return self.estado

    def _decidir(self, ahora):
        """Con la secuencia completa, comprueba la contraseña."""
        if usuarios.verificar(self.nombre, self.simbolos, self.ruta):
            self.estado = CONCEDIDO
        else:
            self.intentos += 1
            self.estado = BLOQUEADO if self.intentos >= MAX_INTENTOS else DENEGADO
        self._t_cambio = ahora