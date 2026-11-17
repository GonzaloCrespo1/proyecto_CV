"""Punto de entrada del programa: python -m flexscan"""
import cv2
import time


from flexscan import secuencia as sec
from flexscan.acceso import dibujar_acceso, iniciar_acceso, dibujar_usuario
from flexscan.calibracion import Corrector, RUTA_CALIBRACION
from flexscan.camara import abrir_camara
from flexscan.clasificador import DESCONOCIDO, clasificar   
from flexscan.estabilidad import Estabilizador              
from flexscan.fps import ContadorFPS
from flexscan.preprocesado import preprocesar
from flexscan.rasgos import anotar, dibujar_rasgos, medir_rasgos
from flexscan.tarjeta import (TARJETA_VACIA, buscar_marco, dibujar_marco,
                              enderezar)
from flexscan.registro import pedir_registro  
from flexscan.fondo import Fondo 
from flexscan.silueta import limpiar
from flexscan.seguimiento import Seguidor
from flexscan.grafica import GraficaGanancia
from flexscan.quietud import Quietud
from flexscan.puntos import DetectorPose, dibujar_puntos
from flexscan.escala import cargar_escala
from flexscan.escala_en_vivo import calibrar_sobre_foto, dibujar_aviso_calibracion
from flexscan.medida import (DistanciaDedoPie, FALLIDA, MedidaValida, MIDIENDO, TERMINADA,
                             dibujar_distancia, dibujar_estado)
from flexscan.instrucciones import mostrar_instrucciones
from flexscan.perfil import cargar_perfil
from flexscan.registro_medida import guardar_toma, pitar
from flexscan.zona import (AMARILLO, FRAMES_CONFIRMACION, ROJO, VERDE, caja_colocacion,
                           dibujar_caja, esta_dentro)

def main():
    cap = abrir_camara()
    corrector = Corrector(RUTA_CALIBRACION)
    contador = ContadorFPS()
    estabilizador = Estabilizador()   
    fondo = Fondo()
    seguidor = Seguidor() 
    quietud = Quietud()
    grafica = GraficaGanancia()
                       
    corregir = True
    ver_mascara = False
    ver_tarjeta = False
    ver_silueta = False
    ver_deteccion = False
    ver_puntos = False
    detector_pose = None
    medida = DistanciaDedoPie()
    validador = MedidaValida()           # decide cuándo la medida es válida
    px_por_cm = cargar_escala()          # None si aún no se ha calibrado con la hoja A4
    seguidos = 0
    acceso = None
    usuario = None 
    perfil = None
    ultimo_acceso = None                 # último acceso cancelado, para conservar sus fallos
    
    print("Teclas: 'c' corregida, 'm' máscara, 't' tarjeta, 'r' registro, 'e' entrar, 's' cerrar sesión, 'f' aprender fondo, 'b' silueta, 'v' caja y centro, 'p' puntos, 'n' nueva medida, 'k' calibrar la escala, 'q' salir") 
    

    while True:
        ok, frame = cap.read()
        if not ok:
            print("No se pudo leer el fotograma")
            break

        if corregir:
            frame = corrector.corregir(frame)
        limpio = frame.copy()                # fotograma sin dibujos, por si se calibra la escala (k)
            
        primer_plano = fondo.aplicar(frame)
        silueta, caja, centro = None, None, None
        if primer_plano is not None:
            silueta, caja, centro = limpiar(primer_plano)
        estimado = seguidor.actualizar(centro) 
        quieta = quietud.actualizar(estimado)
        grafica.anadir(seguidor.ganancia)
        caja_zona = caja_colocacion(frame.shape)
        dentro = esta_dentro(estimado[:2] if estimado is not None else None,
                             caja_zona)
        seguidos = seguidos + 1 if dentro and centro is not None else 0
        colocado = seguidos >= FRAMES_CONFIRMACION
        puntos = detector_pose.detectar(frame) if ver_puntos and colocado else {}
        distancia = medida.actualizar(puntos) if ver_puntos else None
        aviso = False
        if ver_puntos:
            estado_antes = validador.estado
            validador.actualizar(distancia, px_por_cm, quieta, colocado)
            aviso = estado_antes not in (TERMINADA, FALLIDA) and validador.estado in (TERMINADA, FALLIDA)

        mascara = None
        esquinas = None
        lectura = None
        if usuario is None:
            mascara = preprocesar(frame)
            esquinas = buscar_marco(mascara)
            if esquinas is not None:
                tarjeta = enderezar(frame, esquinas)
                rasgos, formas = medir_rasgos(tarjeta)
                lectura = clasificar(rasgos)
                dibujar_marco(frame, esquinas)

        simbolo = estabilizador.actualizar(lectura)          

        
        ahora = time.monotonic()   
                                    
        if acceso is not None:                                  
            acceso.actualizar(simbolo, ahora) 
            if acceso.sesion_lista(ahora):
                usuario = acceso.nombre
                perfil = cargar_perfil(usuario)     # datos personales, para mostrarlos
                acceso = None
                ultimo_acceso = None
                if not mostrar_instrucciones():     # ventana de instrucciones; Esc = no continuar
                    usuario, perfil = None, None
            
            
        if ver_mascara and mascara is not None:
            cv2.imshow("Mascara", mascara)

        if ver_tarjeta:
            if esquinas is None:
                cv2.imshow("Tarjeta", anotar(TARJETA_VACIA, ("sin tarjeta",)))
            else:
                cv2.imshow("Tarjeta",                                  
                           dibujar_rasgos(tarjeta, rasgos, formas, lectura))

        fps = contador.actualizar()
        modo = "CORREGIDA" if corregir else "ORIGINAL"
        cv2.putText(frame, f"{modo}  FPS: {fps:.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        
        if ver_silueta and silueta is not None:
            cv2.imshow("Silueta", silueta)
        if ver_deteccion and caja is not None:
            x, y, ancho, alto = caja
            cv2.rectangle(frame, (x, y), (x + ancho, y + alto), (0, 255, 0), 2)
            cv2.drawMarker(frame, (int(centro[0]), int(centro[1])), (0, 0, 255),
                           cv2.MARKER_CROSS, 30, 2)
        
        if ver_deteccion and estimado is not None:   
            cv2.drawMarker(frame, (int(estimado[0]), int(estimado[1])),    
                           (255, 0, 0), cv2.MARKER_CROSS, 30, 2) 
        if ver_deteccion:
            cv2.imshow("Ganancia K", grafica.dibujar())
        if ver_puntos:
            dibujar_puntos(frame, puntos)
            dibujar_distancia(frame, puntos, distancia, px_por_cm)
            dibujar_estado(frame, validador, px_por_cm)
            
        if fondo.aprendiendo:                             
            cv2.putText(frame, f"Aprendiendo fondo: {fondo.restantes}",   
                        (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)   
        
        

        if simbolo is not None and acceso is None:                                        
            color = (0, 255, 0) if simbolo != DESCONOCIDO else (0, 165, 255)   
            cv2.putText(frame, f"Simbolo: {simbolo}", (10, 70),        
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)    
            
        if acceso is not None:                                 
            dibujar_acceso(frame, acceso, ahora)     
            
        if usuario is not None:                                                     
            dibujar_usuario(frame, usuario, perfil)

        if colocado and quieta:
            color = VERDE
        else:
            color = AMARILLO if colocado else ROJO
        if colocado and quieta and validador.estado == MIDIENDO and validador.mejor is None:
            cv2.putText(frame, "COMENZAR ESTIRAMIENTO",
                        (caja_zona[0] + 20, caja_zona[1] + 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, VERDE, 3)
        dibujar_caja(frame, caja_zona, color)

        if px_por_cm is None:
            dibujar_aviso_calibracion(frame)      # bloquea el recorrido hasta calibrar

        cv2.imshow("FlexScan", frame)
        if aviso:                                  # la medida acaba de terminar: guardar y avisar
            ruta = guardar_toma(frame, validador, px_por_cm, usuario=usuario)
            print(f"Medida {validador.estado}: guardada en {ruta}")
            pitar(validador.estado == TERMINADA)

        tecla = cv2.waitKey(1) & 0xFF
        if tecla == ord("q"):
            break
        if px_por_cm is None and tecla not in (255, ord("q"), ord("k"), ord("c")):
            print("Falta la calibración de distancia: pulsa 'k' con la hoja A4 en el sitio del ejercicio")
            tecla = 255                            # sin calibrar solo valen k, c y q
        if tecla == ord("k"):
            nueva = calibrar_sobre_foto(limpio, "FlexScan", espera_ms=1500)
            if nueva is not None:
                px_por_cm = nueva
                validador.reiniciar()
        if tecla == ord("c"):
            corregir = not corregir
        if tecla == ord("m"):
            ver_mascara = not ver_mascara
            if not ver_mascara:
                cv2.destroyWindow("Mascara")
        if tecla == ord("t"):
            ver_tarjeta = not ver_tarjeta
            if not ver_tarjeta:
                cv2.destroyWindow("Tarjeta")
        if tecla == ord("r"):                                      
            if pedir_registro():                                    
                print("Usuario registrado")                        
            estabilizador = Estabilizador()         
        if tecla == 27 and acceso is not None and acceso.estado != sec.BLOQUEADO:    # Esc: volver al inicio
            ultimo_acceso, acceso = acceso, None            # se recuerdan sus fallos
            estabilizador = Estabilizador()
        if tecla == ord("e") and usuario is None:                                   
            nuevo = iniciar_acceso(acceso if acceso is not None else ultimo_acceso)                      
            if nuevo is not None:                               
                acceso = nuevo                                  
            estabilizador = Estabilizador()
        if tecla == ord("s"):
            usuario = None
            perfil = None          
        if tecla == ord("f"):
            fondo.aprender()     
        if tecla == ord("b"):
            ver_silueta = not ver_silueta
            if not ver_silueta:
                cv2.destroyWindow("Silueta")
        if tecla == ord("v"):
            ver_deteccion = not ver_deteccion
            if not ver_deteccion:
                cv2.destroyWindow("Ganancia K")
        if tecla == ord("n"):
            validador.reiniciar()
        if tecla == ord("p"):
            if detector_pose is None:
                detector_pose = DetectorPose()
            ver_puntos = not ver_puntos
        

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
