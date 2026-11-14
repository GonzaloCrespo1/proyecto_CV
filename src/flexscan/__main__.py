"""Punto de entrada del programa: python -m flexscan"""
import cv2
import time


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



def main():
    cap = abrir_camara()
    corrector = Corrector(RUTA_CALIBRACION)
    contador = ContadorFPS()
    estabilizador = Estabilizador()       
                       
    corregir = True
    ver_mascara = False
    ver_tarjeta = False
    acceso = None
    usuario = None 
    
    print("Teclas: 'c' corregida, 'm' máscara, 't' tarjeta, 'r' registro, 'e' entrar, 's' cerrar sesión, 'q' salir") 
    

    while True:
        ok, frame = cap.read()
        if not ok:
            print("No se pudo leer el fotograma")
            break

        if corregir:
            frame = corrector.corregir(frame)

        mascara = preprocesar(frame)                         
        esquinas = buscar_marco(mascara)                    
        lectura = None                                     
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
                acceso = None
            
            
        if ver_mascara:
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

        if simbolo is not None:                                        
            color = (0, 255, 0) if simbolo != DESCONOCIDO else (0, 165, 255)   
            cv2.putText(frame, f"Simbolo: {simbolo}", (10, 70),        
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)    
            
        if acceso is not None:                                 
            dibujar_acceso(frame, acceso, ahora)     
            
        if usuario is not None:                                                     
            dibujar_usuario(frame, usuario)

        cv2.imshow("FlexScan", frame)

        tecla = cv2.waitKey(1) & 0xFF
        if tecla == ord("q"):
            break
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
        if tecla == ord("e") and usuario is None:                                   
            nuevo = iniciar_acceso(acceso)                      
            if nuevo is not None:                               
                acceso = nuevo                                  
            estabilizador = Estabilizador()
        if tecla == ord("s"):
            usuario = None               
        

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
