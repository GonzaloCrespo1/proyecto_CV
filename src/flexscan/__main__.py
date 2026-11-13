"""Punto de entrada del programa: python -m flexscan"""
import cv2

from flexscan.calibracion import Corrector, RUTA_CALIBRACION
from flexscan.camara import abrir_camara
from flexscan.fps import ContadorFPS

def main():
    cap = abrir_camara()
    corrector = Corrector(RUTA_CALIBRACION) 
    contador = ContadorFPS()
    corregir = True 
    print("Pulsa 'c' para alternar original/corregida, 'q' para salir")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("No se pudo leer el fotograma")
            break
        
        if corregir:
            frame = corrector.corregir(frame) 
        
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

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()