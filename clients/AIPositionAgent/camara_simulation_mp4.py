import cv2
import numpy as np
import time

# Dimensiones idénticas a tu sistema de visión
MAX_WIDTH = 1280
MAX_HEIGHT = 720
FPS = 30
OUTPUT_FILENAME = "camara_simulada.mp4"

def generar_video_camara():
    print(f"Iniciando generador de video MP4: '{OUTPUT_FILENAME}'...")
    print("Simulando robots ArUco y obstáculos móviles/estáticos...")
    print("Presiona Ctrl+C en la terminal para detener y guardar el video.")

    # --- Configuración del VideoWriter ---
    # FourCC 'mp4v' es ampliamente compatible para archivos .mp4 en Windows, Linux y macOS
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(OUTPUT_FILENAME, fourcc, FPS, (MAX_WIDTH, MAX_HEIGHT))

    if not out.isOpened():
        print("[ERROR] No se pudo inicializar el VideoWriter. Revisa los codecs instalados.")
        return

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

    frame_count = 0
    total_frames_to_record = FPS * 10  # Opcional: Generar 10 segundos de video, o usa un bucle infinito

    try:
        # Puedes cambiar 'True' por un contador si deseas limitar la duración exacta
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
            cv2.circle(frame, (1050, 150), 35, (255, 255, 255), -1)
            cv2.rectangle(frame, (100, 550), (250, 600), (255, 255, 255), -1)

            # 6. ESCRIBIR EL FOTOGRAMA EN EL ARCHIVO MP4
            out.write(frame)
            frame_count += 1

            # Mantener una tasa de refresco fluida de 30 FPS sincronizada
            time.sleep(1.0 / FPS)

    except KeyboardInterrupt:
        print(f"\nGeneración detenida por el usuario. Total de frames escritos: {frame_count}")
    
    finally:
        # Liberar el recurso de video correctamente para evitar archivos corruptos
        out.release()
        print(f"Video guardado con éxito como '{OUTPUT_FILENAME}'. Ya puedes usarlo en tu agente de visión.")

if __name__ == "__main__":
    generar_video_camara()
