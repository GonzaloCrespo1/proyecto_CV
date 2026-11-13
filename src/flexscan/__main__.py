"""Punto de entrada del programa: python -m flexscan"""
import cv2

from flexscan.camara import abrir_camara


def main():
    cap = abrir_camara()
    print("Pulsa 'q' para salir")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("No se pudo leer el fotograma")
            break

        cv2.imshow("FlexScan", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()