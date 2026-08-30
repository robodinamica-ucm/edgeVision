'''
The Logitech C920 Pro HD Webcam
supports a maximum video resolution of 1920 × 1080 pixels (Full HD) at 30 frames per second. 
Supported Video Resolutions

    1080p Full HD: 1920 × 1080 pixels at 30 fps
    720p HD: 1280 × 720 pixels at 30 fp
'''

import cv2
import numpy as np
import time

import cv2
import numpy as np
import time

# Dimensiones idénticas a tu sistema de visión
MAX_WIDTH = 1280
MAX_HEIGHT = 720

def generar_video_camara():
    print("Iniciando simulador de cámara INVISIBLE con MÚLTIPLES OBSTÁCULOS BLANCOS...")
    print("Generando archivo continuamente en: 'camara_simulada.png'")
    print("Presiona Ctrl+C en la terminal para detener el generador.")

    # --- Configuración del Obstáculo Móvil 1 (Círculo grande) ---
    obs1_x, obs1_y = 200, 350
    vel1_x, vel1_y = 8, 5

    # --- Configuración del Obstáculo Móvil 2 (Cuadrado mediano) ---
    obs2_x, obs2_y = 900, 150
    vel2_x, vel2_y = -6, 7

    # --- DISEÑO DEL ARUCO SIMULADO (Robot en posición fija) ---
    aruco_bgr = np.zeros((80, 80, 3), dtype=np.uint8) 
    cv2.rectangle(aruco_bgr, (15, 15), (65, 65), (255, 255, 255), -1) 
    cv2.rectangle(aruco_bgr, (25, 25), (40, 40), (0, 0, 0), -1)
    cv2.rectangle(aruco_bgr, (50, 50), (65, 65), (0, 0, 0), -1)

    try:
        while True:
            # 1. Crear el fondo oscuro del tatami (píxeles color gris oscuro = 40)
            frame = np.ones((MAX_HEIGHT, MAX_WIDTH, 3), dtype=np.uint8) * 40

            # 2. Insertar el Robot ArUco fijo en la pista
            frame[400:480, 200:280] = aruco_bgr

            # 3. ACTUALIZAR Y DIBUJAR OBSTÁCULO MÓVIL 1 (Círculo Blanco Puro)
            obs1_x += vel1_x
            obs1_y += vel1_y
            if obs1_x < 50 or obs1_x > MAX_WIDTH - 50: vel1_x *= -1
            if obs1_y < 50 or obs1_y > MAX_HEIGHT - 50: vel1_y *= -1
            cv2.circle(frame, (obs1_x, obs1_y), 45, (255, 255, 255), -1)

            # 4. ACTUALIZAR Y DIBUJAR OBSTÁCULO MÓVIL 2 (Caja/Cuadrado Blanco Puro)
            obs2_x += vel2_x
            obs2_y += vel2_y
            if obs2_x < 60 or obs2_x > MAX_WIDTH - 60: vel2_x *= -1
            if obs2_y < 60 or obs2_y > MAX_HEIGHT - 60: vel2_y *= -1
            cv2.rectangle(frame, (obs2_x - 30, obs2_y - 30), (obs2_x + 30, obs2_y + 30), (255, 255, 255), -1)

            # 5. DIBUJAR OBSTÁCULOS BLANCOS FIJOS (Para simular objetos estáticos en las esquinas)
            # Obstáculo estático 1: Cilindro/círculo en la zona superior derecha
            cv2.circle(frame, (1050, 150), 35, (255, 255, 255), -1)
            # Obstáculo estático 2: Barrera rectangular en la zona inferior izquierda
            cv2.rectangle(frame, (100, 550), (250, 600), (255, 255, 255), -1)

            # 6. GUARDAR EL FOTOGRAMA EN EL DISCO DURO
            cv2.imwrite("camara_simulada.png", frame)

            # Mantener una tasa de refresco fluida de 30 FPS
            time.sleep(0.03)

    except KeyboardInterrupt:
        print("\nGenerador de cámara simulada detenido correctamente.")

if __name__ == "__main__":
    generar_video_camara()
