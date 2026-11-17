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
from flexscan.medida import (DistanciaDedoPie, ESPERANDO_BASE, FALLIDA, MedidaValida, MIDIENDO, TERMINADA,
                             dibujar_distancia, dibujar_estado)
from flexscan.instrucciones import mostrar_instrucciones
from flexscan.perfil import cargar_perfil
from flexscan.preparacion import Preparacion
from flexscan.registro_medida import guardar_toma, pitar_fin, pitar_inicio
from flexscan.pantalla_medida import AVISO_FINAL_S, PantallaMedida
from flexscan.modelo_ml import MODELO_LISTO, predecir_valor_ml
from flexscan.ventana_analisis import mostrar_analisis
from flexscan.ventana_resultado import ANALISIS, CERRAR, REPETIR, mostrar_resultado
from flexscan.teclas import (AvisoTecla, BotonTeclas, FASES_BOTON, MEDIDA, RESULTADO, cerrar_auxiliares,
                              cerrar_ventana, fase_actual, filtrar, normalizar)
from flexscan.bienvenida import mostrar_bienvenida
from flexscan.ventana_teclas import VentanaTeclas
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
    ver_puntos = False                   # puntos del cuerpo sobre la imagen (la tecla p los muestra u oculta)
    detector_pose = None
    medida = DistanciaDedoPie()
    validador = MedidaValida()           # decide cuándo la medida es válida
    px_por_cm = cargar_escala()          # None si aún no se ha calibrado con la hoja A4
    seguidos = 0
    acceso = None
    usuario = None 
    perfil = None
    ultimo_acceso = None                 # último acceso cancelado, para conservar sus fallos
    preparacion = Preparacion(fondo)     # cuenta atrás y aprendizaje automático del fondo
    aviso_tecla = AvisoTecla()           # aviso en pantalla de una tecla fuera de su fase
    fase_anterior = None
    boton_teclas = BotonTeclas()         # botón «Teclas (H)» de la pantalla principal
    pantalla_medida = PantallaMedida()   # guía de la medida y pantalla de resultado
    ventana_teclas = VentanaTeclas()     # ventana de teclas: en verde las que valen en la fase actual
    bienvenida_mostrada = False          # presentación del proyecto, una vez calibrada la escala
    abrir_teclas_al_arrancar = False
    raton_puesto = False
    estimado_final = None                # último estado del seguimiento: se congela al terminar la medida
    ruta_toma = None                     # carpeta de la última toma guardada
    t_resultado = None                   # instante en que apareció el resultado (pitido grave)
    resultado_visto = False              # la ventana de resultado ya se ha enseñado para esta medida
    
    print("Teclas: 'c' corregida, 'm' máscara, 't' tarjeta, 'r' registro, 'e' entrar, 's' cerrar sesión, 'f' aprender fondo, 'b' silueta, 'v' caja y centro, 'p' puntos, 'n' nueva medida, 'k' calibrar la escala, 'q' salir") 
    

    while True:
        ok, frame = cap.read()
        if not ok:
            print("No se pudo leer el fotograma")
            break

        if px_por_cm is not None and not bienvenida_mostrada:    # presentación del proyecto al arrancar
            mostrar_bienvenida()
            bienvenida_mostrada = True
            abrir_teclas_al_arrancar = True      # y justo después, la ventana de teclas
            estabilizador = Estabilizador()
            continue

        if corregir:
            frame = corrector.corregir(frame)
        limpio = frame.copy()                # fotograma sin dibujos, por si se calibra la escala (k)
            
        primer_plano = fondo.aplicar(frame)
        silueta, caja, centro = None, None, None
        if primer_plano is not None:
            silueta, caja, centro = limpiar(primer_plano)
        medida_cerrada = (px_por_cm is not None and usuario is not None and not preparacion.activa
                          and validador.estado in (TERMINADA, FALLIDA))
        if medida_cerrada and estimado_final is not None:
            estimado = estimado_final                    # el seguimiento (Kalman) termina con la medida
        else:
            estimado = seguidor.actualizar(centro)
            estimado_final = estimado
            grafica.anadir(seguidor.ganancia)
        quieta = quietud.actualizar(estimado)
        caja_zona = caja_colocacion(frame.shape)
        dentro = esta_dentro(estimado[:2] if estimado is not None else None,
                             caja_zona)
        seguidos = seguidos + 1 if dentro and centro is not None else 0
        colocado = seguidos >= FRAMES_CONFIRMACION
        en_medida = px_por_cm is not None and usuario is not None and not preparacion.activa
        midiendo = en_medida and validador.estado not in (TERMINADA, FALLIDA)
        puntos = detector_pose.detectar(frame) if midiendo and colocado else {}
        distancia = medida.actualizar(puntos) if midiendo else None
        aviso = False
        if en_medida:                              # la medida corre sola en cuanto acaba la preparación
            estado_antes = validador.estado
            validador.actualizar(distancia, px_por_cm, quieta, colocado)
            aviso = estado_antes not in (TERMINADA, FALLIDA) and validador.estado in (TERMINADA, FALLIDA)
            if estado_antes == ESPERANDO_BASE and validador.estado == MIDIENDO:
                pitar_inicio()                     # pitido agudo: ya puede empezar el estiramiento

        mascara = None
        esquinas = None
        lectura = None
        buscando_patron = acceso is not None          # solo se busca el patrón de símbolos durante el acceso
        if usuario is None and (buscando_patron or ver_mascara or ver_tarjeta):
            mascara = preprocesar(frame)
            esquinas = buscar_marco(mascara)
            if esquinas is not None:
                tarjeta = enderezar(frame, esquinas)
                rasgos, formas = medir_rasgos(tarjeta)
                lectura = clasificar(rasgos)
                if buscando_patron or ver_tarjeta:      # el marco verde solo se ve cuando importa
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
                else:
                    if detector_pose is None:
                        detector_pose = DetectorPose()      # el modelo tarda en cargar: se prepara antes de la cuenta atrás
                    validador.reiniciar()
                    seguidor, quietud, estimado_final = Seguidor(), Quietud(), None     # seguimiento nuevo
                    resultado_visto = False
                    preparacion.empezar(time.monotonic())   # 5 s para apartarse y aprender el fondo

        fondo_listo = fondo.mog is not None and not fondo.aprendiendo
        fase = fase_actual(px_por_cm is not None, acceso is not None, usuario is not None,
                           preparacion.activa, validador.estado)
        if fase != fase_anterior:                  # al avanzar en el programa, se cierran las ventanas de depuración
            ver_mascara = ver_tarjeta = ver_silueta = ver_deteccion = False
            cerrar_auxiliares()
            fase_anterior = fase
        if abrir_teclas_al_arrancar:
            ventana_teclas.abrir(fase, fondo_listo, arranque=True)
            abrir_teclas_al_arrancar = False
        ventana_teclas.actualizar(fase, fondo_listo)     # el verde sigue a la fase actual


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
        if ver_puntos and fase == MEDIDA:          # puntos del cuerpo y distancia; la tecla p los oculta
            dibujar_puntos(frame, puntos)
            dibujar_distancia(frame, puntos, distancia, px_por_cm)
            
        if fondo.aprendiendo and not preparacion.activa:                             
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

        if fase == MEDIDA:                         # la zona de colocación solo se ve al medir
            if colocado and quieta:
                color = VERDE
            else:
                color = AMARILLO if colocado else ROJO
            dibujar_caja(frame, caja_zona, color)

        if px_por_cm is None:
            dibujar_aviso_calibracion(frame)      # bloquea el recorrido hasta calibrar

        if aviso:                                  # imagen de la toma, antes de dibujar la pantalla de resultado
            captura = frame.copy()
            dibujar_puntos(captura, puntos)
            dibujar_distancia(captura, puntos, distancia, px_por_cm)
            dibujar_estado(captura, validador, px_por_cm)
        pantalla_medida.dibujar(frame, ahora, fase, colocado, quieta, validador)   # guía o resultado

        preparacion.actualizar(ahora)
        preparacion.dibujar(frame, ahora)
        aviso_tecla.dibujar(frame, ahora)
        boton_teclas.dibujar(frame, fase in FASES_BOTON)
        cv2.imshow("FlexScan", frame)
        if not raton_puesto:                       # el ratón de la ventana principal sirve para el botón
            cv2.setMouseCallback("FlexScan", boton_teclas.raton)
            raton_puesto = True
        if aviso:                                  # la medida acaba de terminar: guardar y avisar
            ruta = guardar_toma(captura, validador, px_por_cm, usuario=usuario)
            print(f"Medida {validador.estado}: guardada en {ruta}")
            ruta_toma, t_resultado, resultado_visto = ruta, time.monotonic(), False
            pitar_fin(validador.estado == TERMINADA)       # pitido grave: la medida ha terminado

        forzada = None
        if (fase == RESULTADO and not resultado_visto and t_resultado is not None
                and time.monotonic() - t_resultado >= AVISO_FINAL_S + 0.3):
            resultado_visto = True                 # tras la pantalla verde, la ventana de resultado detiene el vídeo
            ventana_teclas.cerrar()
            medida_cm = round(validador.mejor, 1) if validador.estado == TERMINADA else None
            accion = mostrar_resultado(medida_cm, usuario, perfil)
            while accion == ANALISIS and medida_cm is not None:
                try:
                    valor_ml = predecir_valor_ml(ruta_toma) if MODELO_LISTO else None
                except Exception as error:         # un fallo del modelo nunca debe romper el programa
                    print(f"Modelo de ML: {error}")
                    valor_ml = None
                mostrar_analisis(medida_cm, valor_ml, MODELO_LISTO and valor_ml is not None)
                accion = mostrar_resultado(medida_cm, usuario, perfil)
            forzada = ord("n") if accion == REPETIR else ord("s") if accion == CERRAR else None
        tecla = normalizar(cv2.waitKey(1) & 0xFF)
        if forzada is not None:
            tecla = forzada                        # la opción elegida en la ventana equivale a pulsar N o S
        if tecla == ord("q"):
            break
        if tecla == 27 and ventana_teclas.abierta:           # Esc cierra primero la ventana de teclas
            ventana_teclas.cerrar()
            tecla = 255
        tecla = filtrar(tecla, fase, aviso_tecla, ahora, fondo_listo)     # una tecla fuera de su fase no hace nada
        if tecla == ord("k"):
            nueva = calibrar_sobre_foto(limpio, "FlexScan", espera_ms=1500)
            if nueva is not None:
                px_por_cm = nueva
                validador.reiniciar()
                if fase in (MEDIDA, RESULTADO):
                    aviso_tecla.mostrar("Escala recalibrada: la medida se ha descartado.", time.monotonic())
            raton_puesto = False                   # la calibración cambia el ratón de la ventana
        if tecla == ord("c"):
            corregir = not corregir
        if tecla == ord("m"):
            ver_mascara = not ver_mascara
            if not ver_mascara:
                cerrar_ventana("Mascara")
        if tecla == ord("t"):
            ver_tarjeta = not ver_tarjeta
            if not ver_tarjeta:
                cerrar_ventana("Tarjeta")
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
            if fase == MEDIDA and validador.estado == MIDIENDO:     # medida en curso: se descarta primero
                validador.reiniciar()
                aviso_tecla.mostrar("Medida descartada. Pulsa S otra vez para cerrar la sesión.", ahora)
            else:
                usuario = None
                perfil = None
                preparacion.cancelar()
                validador.reiniciar()               # la próxima sesión empieza de cero
                seguidor, quietud, estimado_final = Seguidor(), Quietud(), None
                resultado_visto = False
        if tecla == ord("f"):
            fondo.aprender()     
        if tecla == ord("b"):
            ver_silueta = not ver_silueta
            if not ver_silueta:
                cerrar_ventana("Silueta")
        if tecla == ord("v"):
            ver_deteccion = not ver_deteccion
            if not ver_deteccion:
                cerrar_ventana("Ganancia K")
        if tecla == ord("n"):                      # nueva medida: nuevo seguimiento, y vuelven los pasos de antes
            validador.reiniciar()
            seguidor, quietud, estimado_final = Seguidor(), Quietud(), None
            resultado_visto = False
        if tecla == ord("p"):                      # muestra u oculta los puntos; la medida no se ve afectada
            ver_puntos = not ver_puntos
        clic_teclas = boton_teclas.pulsado()
        if tecla == ord("h") or (clic_teclas and fase in FASES_BOTON):    # ventana de teclas
            ventana_teclas.alternar(fase, fondo_listo)
        

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
