https://gemini.google.com/app/19c39e159ed9b9e8

# Documentación Técnica: Sistema de Visión y Telemetría Robotarium

Esta documentación detalla la arquitectura, el entorno de emulación local, las correcciones de compatibilidad y el procedimiento de ejecución del sistema distribuido de visión artificial y control basado en ZeroMQ y OpenCV.

---

### 1. Arquitectura del Sistema

El sistema opera bajo un modelo distribuido asíncrono compuesto por dos componentes principales comunicados por ZeroMQ:

hub/robotarium_hub_julio.py
* **`RobotariumHub` (Servidor Central)**:
* **Socket REP (`tcp://*:5555`)**: Recibe registros de nuevos agentes (`hello`) y asigna recursos.
* **Socket SUB dinámico**: Se suscribe al socket PUB de cada agente registrado usando `zmq.Poller`.
* **Socket PUB (`tcp://*:5556`)**: Reenvía la telemetría unificada a consumidores de la red o clientes MQTT.

ai-clases/visio_pos_agent_nuevo.py
* **`VisionPosDevice` / `Agent` (Nodo de Percepción)**:
* Captura flujos de video cenitales duales.
* Aplica transformaciones de perspectiva y costura de imágenes (*stitching*).
* Extrae pose de robots ($x, y, \theta$) mediante marcadores ArUco.
* Segmenta obstáculos estáticos y móviles en coordenadas métricas del tatami.
* Publica la información a través de su socket local en el puerto `5559`.



---

### 2. Archivos de Configuración y Calibración
archivosCalibracion.py

Para desacoplar las dimensiones en píxeles de las coordenadas métricas reales, se generaron dos archivos esenciales mediante `cv2.getPerspectiveTransform`:

* **`homography_matrix.npy`**: Matriz $3 \times 3$ (identidad o calculada) utilizada por `cv2.warpPerspective` para alinear los fotogramas de las cámaras A y B en un único lienzo.
* **`tatami_config.json`**:
* `boundaries`: Límites del área útil en píxeles ($x_{\min}, x_{\max}, y_{\min}, y_{\max}$).
* `M_pixel_to_real`: Matriz de transformación proyectiva que convierte centroides de píxeles a centímetros físicos ($200 \times 200\text{ cm}$).



---

### 3. Entorno de Emulación Local (Sin Hardware Físico)

Para validar el sistema en un solo equipo de desarrollo sin cámaras físicas conectadas:

1. **Generador de Video Sintético (`camara_simulada.mp4`)**: camara_simulation_mp4.py
* Genera un flujo de video MP4 ($1280 \times 720$ a 30 FPS) codificado con `mp4v`.
* Incluye un marcador ArUco estacionario y obstáculos geométricos (círculos y rectángulos) móviles y fijos.


2. **Abstracción de Cámara A (`cv2.VideoCapture`)**:
* Lee el archivo `camara_simulada.mp4`.
* Implementa rebobinado automático (`CAP_PROP_POS_FRAMES = 0`) al detectar fin de archivo (EOF).


3. **Abstracción de Cámara B (`MockBlackCapture`)**:
* Clase adaptadora que simula la interfaz de `cv2.VideoCapture`.
* Entrega fotogramas negros (`np.zeros`) continuos sin lanzar excepciones ni consumir I/O.



---

### 4. Correcciones Críticas de Código y Red

| Problema Detectado | Causa Raíz | Solución Aplicada |
| --- | --- | --- |
| `AttributeError: DetectorParameters_create` | Cambio de API en OpenCV $\ge 4.7.0$. | Se implementó selector condicional con fallback a `cv2.aruco.DetectorParameters()` y `cv2.aruco.ArucoDetector`. |
| `ModuleNotFoundError: No module named 'paho'` | Instalación errónea del paquete `mqtt`. | Se reemplazó por el paquete oficial `paho-mqtt`. |
| `ZMQError: Cannot assign requested address` | El Hub intentaba hacer `bind` en la IP fija `192.168.10.1` (no asignada en la máquina local). | Se configuraron los sockets de enlace en comodín `tcp://*:5555` y `tcp://*:5556`. |
| Fallo de registro del Agente | El agente intentaba comunicarse con una IP externa inexistente. | Se configuraron `ip="127.0.0.1"` y `hub_ip="127.0.0.1"`. |

---

### 5. Protocolo de Ejecución

Para iniciar el entorno completo de prueba local:

0. **python env:**
source /mnt/data/dev/venvs/envInstrumentacionOptica/bin/activate

1. **Generar recursos previos (si no existen):**
```bash
python generar_calibracion.py
python generar_video_camara.py

```


2. **Terminal 1 — Iniciar el Hub central:**
```bash
python robotarium_hub_julio.py

```

*Salida esperada:*
```text
DEBUG:root:Listening to agents
INFO:root:Robotarium is waiting for new agents

```


3. **Terminal 2 — Iniciar el Agente de Visión:**
```bash
python visio_pos_agent_nuevo.py

```


*Salida esperada:*
* Carga de matrices y límites del tatami.
* Registro del agente en el Hub vía protocolo `hello`.
* Ventana de video `Robotarium Cenital - Integrado` con seguimiento de ArUco y obstáculos segmentados en tiempo real.



---

