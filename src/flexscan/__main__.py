"""Punto de entrada del programa: python -m flexscan"""
import cv2

from flexscan.camara import abrir_camara
from flexscan.fps import ContadorFPS

def main():
    cap = abrir_camara()
    contador = ContadorFPS()
    print("Pulsa 'q' para salir")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("No se pudo leer el fotograma")
            break
        
        fps = contador.actualizar()  
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2) 

        cv2.imshow("FlexScan", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()