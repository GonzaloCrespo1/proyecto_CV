"""Punto de entrada del programa: python -m flexscan"""
import cv2

from flexscan.calibracion import Corrector, RUTA_CALIBRACION
from flexscan.camara import abrir_camara
from flexscan.fps import ContadorFPS
from flexscan.preprocesado import preprocesar

def main():
    cap = abrir_camara()
    corrector = Corrector(RUTA_CALIBRACION) 
    contador = ContadorFPS()
    corregir = True 
    ver_mascara = False                               
    print("Teclas: 'c' original/corregida, 'm' máscara, 'q' salir")   
    

    while True:
        ok, frame = cap.read()
        if not ok:
            print("No se pudo leer el fotograma")
            break
        
        if corregir:
            frame = corrector.corregir(frame) 
        
        if ver_mascara:                              
            cv2.imshow("Mascara", preprocesar(frame))
            
        fps = contador.actualizar()  
        modo = "CORREGIDA" if corregir else "ORIGINAL"
        cv2.putText(frame, f"{modo}  FPS: {fps:.1f}", (10, 30),      
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("FlexScan", frame)

        tecla = cv2.waitKey(1) & 0xFF
        if tecla == ord("q"):
            break
        if tecla == ord("c"):                                        
            corregir = not corregir
        if tecla == ord("m"):                         #
            ver_mascara = not ver_mascara
            if not ver_mascara:
                cv2.destroyWindow("Mascara")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()