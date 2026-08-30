# 🤖🛰️ Robotarium-AI-Core: Plataforma Distribuida de Percepción Cenital, Control Multi-Agente e Inteligencia Artificial

Plataforma modular distribuida de alto rendimiento y baja latencia para la orquestación, telemetría, simulación y control autónomo de flotas de micro-robots móviles en entornos cerrados (*testbed*). El sistema integra percepción cenital global procesada íntegramente en memoria RAM, mensajería asíncrona desacoplada mediante **ZeroMQ** (con pasarela **MQTT**) y una nueva capa de **Inteligencia Artificial** para segmentación visual dinámica, simulación en Gemelo Digital y navegación reactiva/predictiva.

---

## 🏛️ Origen y Contexto Académico

Este proyecto evoluciona la infraestructura del **Robotarium**, concebido originalmente en el **Departamento de Arquitectura de Computadores y Automática (DACyA)** de la **Universidad Complutense de Madrid (UCM)**.

* **Línea Base Académica:** Banco de pruebas experimental para el estudio de Sistemas Multi-Agente (*MAS*), validación de algoritmos de navegación en entornos sin cobertura satelital (*GPS-Denied*) y control cooperativo mediante sensores virtuales cenitales.
* **Evolución Actual (IA-Core):** Integración de agentes de visión artificial basados en IA (`AIPositionAgent`) y gemelo digital para pruebas.

---

## 🏗️ Arquitectura General del Sistema

El ecosistema desacopla sus responsabilidades en cuatro capas principales que interactúan mediante patrones de publicación/suscripción (*PUB/SUB*) y petición/respuesta (*REQ/REP*), logrando latencias de respuesta en bucle cerrado inferiores a $30\text{ ms}$:

1. **Percepción Cenital en RAM (`clients/PositionAgent/`):** Captura síncrona de vídeo desde dos cámaras cenitales sobre el tatami ($419 \times 140\text{ cm}$). Aplica una matriz de homografía $3 \times 3$ (`homography_matrix.npy`), detecta marcadores ArUco (`DICT_4X4_50`) y transforma coordenadas de píxeles a centímetros reales del plano (`tatami_config.json`, $M_{\text{pixel\_to\_real}}$) sin saturar la red local con vídeo en crudo.
2. **Orquestación Central de Red (`hub/`):** Broker central ZeroMQ que gestiona el registro dinámico de agentes (puerto `5555` REQ/REP) y retransmite de forma atómica y no bloqueante (*Zero-Copy*) toda la telemetría agregada mediante `zmq.Poller` (puerto `5556` PUB).
3. **Control Autónomo y FSM (`clients/BounceRobot/`):** Máquina de Estados Finitos que fusiona la posición absoluta cenital con la odometría de los motores. Dispone de un despachador en hilo independiente (`command_queue`) y un *Watchdog* de desconexión ($>2.5\text{ s}$) que frena de emergencia el robot si se interrumpe la telemetría.
4. **Hardware Embebido a Bordo (`firmware/` y Raspberry Pi):** La Raspberry Pi ejecuta un nodo cliente ZeroMQ que recibe comandos de movimiento y reporta encoders, comunicándose por interfaz serie con el microcontrolador (Arduino MKR / Nano), el cual ejecuta el lazo cerrado PID de los motores.

---

## 📊 Diagrama de Arquitectura Integrada

El siguiente diagrama detalla la interacción temporal, el flujo de tópicos ZeroMQ y las transiciones de la FSM entre todos los módulos del sistema:

![Arquitectura Integrada del Robotarium](docs/ArquitecturaCompletaRobotariumVisionUnificada.svg)

---

## 👁️🤖 Incorporación de Agentes de Visión con IA (`AIPositionAgent`)

El módulo `AIPositionAgent/` amplía la percepción clásica incorporando técnicas de visión artificial avanzada y simulación sintética sin alterar la estabilidad del broker central:


```

┌────────────────────────────────────────────────────────────────────────┐
│                   AIPositionAgent / ai_pos_agent.py                    │
│  • Segmentación Adaptativa (HSV / Umbralización Dinámica)             │
│  • Extracción de Contornos Poligonales de Obstáculos                   │
│  • Proyección Métrica a cm Reales mediante Matriz de Homografía        │
└───────────────────────────────────┬────────────────────────────────────┘
│ ZMQ PUB (topic: "arena/obstacles")
▼
┌────────────────────────────────────────────────────────────────────────┐
│                   ORQUESTACIÓN & NAVEGACIÓN REACTIVA                   │
│  • Broker ZMQ (robotarium_hub.py) redistribuye geometrías             │
│  • FSM / Planificador calcula campos de potencial repulsivos          │
│  • Evasión proactiva de siluetas dinámicas en tiempo real              │
└────────────────────────────────────────────────────────────────────────┘

```

### 1. Detección y Segmentación Dinámica (`ai_pos_agent.py`)
* **Segmentación en Espacio de Color:** Aisla siluetas de contraste colocadas sobre el tatami mediante filtros de color HSV y umbralización adaptativa en tiempo real.
* **Proyección Métrica Poligonal:** Convierte los contornos detectados en píxeles a coordenadas métricas reales $[X_{\text{cm}}, Y_{\text{cm}}]$ utilizando la homografía del tatami.
* **Publicación Táctica:** Emite las geometrías en el tópico `arena/obstacles`, permitiendo que los agentes de control calculen distancias de seguridad y desvíos antes del contacto físico.

### 2. Gemelo Digital y Simulación Cenital (`ai_pos_agent_sim.py`)
* **Generador de Escenarios en Memoria:** Renderiza sintéticamente el tatami virtual ($1280 \times 720\text{ px}$), simulando ruido de sensor, fluctuaciones de iluminación, movimiento de robots y obstáculos dinámicos.
* **Validación en Bucle Cerrado:** El gemelo digital inyecta los datos directamente al `RobotariumHub`, permitiendo verificar algoritmos de evasión y control FSM sin requerir la presencia física en el laboratorio.

---

## 📂 Estructura del Repositorio

```text
robotarium-ai-core/
├── LICENSE
├── README.md
├── requirements.txt
├── config/                               # Calibración espacial y matrices de transformación
│   ├── homography_matrix.npy             # Matriz 3x3 para costura de perspectiva inter-cámaras
│   └── tatami_config.json                # Dimensiones útiles (419x140 cm) y matriz M_pixel_to_real
├── firmware/                             # Código C/C++ de bajo nivel para Arduino (MKR / Nano)
├── hub/                                  # Orquestación Central
│   └── robotarium_hub.py                 # Broker ZeroMQ multipuerto (REQ/REP 5555 y PUB/SUB 5556)
├── clients/                              # Nodos y agentes clientes desacoplados
│   ├── agent.py                          # Clase base abstracta de comunicaciones ZeroMQ
│   ├── logger_config.py                  # Formato unificado de logs del sistema
│   ├── PositionAgent/                    # Percepción cenital clásica
│   │   └── visio_pos_agent.py            # Captura unificada, homografía y tracking ArUco en RAM
│   ├── AIPositionAgent/                  # Capa de Percepción IA y Simulación
│   │   ├── ai_pos_agent.py               # Segmentación de siluetas y publicación de obstáculos
│   │   └── ai_pos_agent_sim.py           # Gemelo Digital para simulación cenital en RAM
│   ├── BounceRobot/                      # Control reactivo autónomo
│   │   └── agent_billar.py               # FSM de navegación con watchdog y evasión de límites
│   ├── RemoteControl/                    # Teleoperación y registro experimental
│   │   └── remote_control_agent.py       # Control manual con mando/teclado y logger CSV
│   └── CalibrationTools/                 # Herramientas de calibración offline
│       ├── calibration_stitching.py      # Calibrador de homografía entre cámaras A y B
│       ├── calibration2.py               # Utilidad de alineación de encuadres
│       └── tatami_calibrator.py          # Calibrador interactivo de límites de la pista
└── docs/                                 # Documentación técnica y diagramas
    └── ArquitecturaCompletaRobotariumVisionUnificada.svg

```

---

## 🌐 Registro de Red y Tópicos ZeroMQ

| Tópico / Canal | Protocolo | Emisor | Receptor | Descripción del Payload |
| --- | --- | --- | --- | --- |
| `tcp://*:5555` | ZMQ REP/REQ | Agentes | Hub | *Handshake* inicial de registro (`{"hello": "tcp://ip:port"}`).

 |
| `tcp://*:5556` | ZMQ PUB | Hub | Suscriptores | Retransmisión multiplexada de toda la telemetría.

 |
| `{id}/pos` (Ej: `6/pos`) | ZMQ PUB/SUB | PositionAgent | Hub / FSM | Pose métrica: `{"x": cm, "y": cm, "yaw": rad, "timestamp": t}`.

 |
| `arena/boundaries` | ZMQ PUB/SUB | PositionAgent / Hub | FSM | Esquinas del tatami ($419 \times 140\text{ cm}$).

 |
| `arena/obstacles` | ZMQ PUB/SUB | AIPositionAgent | Hub / FSM | Obstáculos: `{"obstacles": [{"id": 1, "center": [x, y], "radius": r}]}`.

 |
| `agent/{id}/move` | ZMQ PUB/SUB | FSM / Teleop | Robot (RPi) | Consignas de velocidad: `{"v": linear_m_s, "w": angular_rad_s}`.

 |
| `agent/{id}/turn` | ZMQ PUB/SUB | FSM | Robot (RPi) | Giro angular sobre eje: `{"ang": 180.0}`.

 |
| `agent/{id}/wheel` | ZMQ PUB/SUB | Robot (RPi) | FSM | Odometría de ruedas: `{"Wleft": ticks_l, "Wright": ticks_r}`.

 |
| `agent/{id}/feedback` | ZMQ PUB/SUB | Robot (RPi) | FSM | Confirmación de maniobra: `{"status": "done", "op": "turn"}`.

 |

---

## 🚀 Instalación y Puesta en Marcha

### 1. Requisitos e Instalación de Dependencias

```bash
# Clonar el repositorio
git clone [https://github.com/tu-usuario/robotarium-ai-core.git](https://github.com/tu-usuario/robotarium-ai-core.git)
cd robotarium-ai-core

# Crear y activar el entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

```

### 2. Secuencia de Ejecución en Laboratorio

Para garantizar el correcto *handshake* y evitar bloqueos de *watchdog*, iniciar los terminales en este orden:

```bash
# Terminal 1: Orquestador Central ZMQ
python3 hub/robotarium_hub.py

# Terminal 2: Sistema de Percepción Cenital Unificada (Producción)
python3 clients/PositionAgent/visio_pos_agent.py --no-gui

# Terminal 3: Agente de Percepción IA (Detección de siluetas)
python3 clients/AIPositionAgent/ai_pos_agent.py

# Terminal 4: Control Autónomo FSM (Robot ID 6)
python3 clients/BounceRobot/agent_billar.py --robot-id 6

```

*(Para ejecutar en modo simulación virtual, ejecutar `python3 clients/AIPositionAgent/ai_pos_agent_sim.py` en lugar de la Terminal 2)*.

---

## 🔮 Roadmap: Líneas de Desarrollo Futuras con IA

* **Inferencia Edge AI Optimizada:** Sustitución o refuerzo del tracking clásico con modelos YOLOv11-Nano y ByteTrack exportados a TensorRT/ONNX para seguimiento multiobjeto en tiempo real.


* **Planificación Multi-Agente con GNN y CBF:** Implementación de Redes Neuronales de Grafos (*Graph Neural Networks*) combinadas con Funciones de Barrera de Control (*Control Barrier Functions*) para garantizar colisión cero y evitar bloqueos mutuos en flotas densas.


* **Pasarela Estándar a ROS2:** Integración de un puente ZeroMQ-ROS2 (`ros2_zmq_bridge`) para interoperabilidad con herramientas estándar como Nav2 y RViz.


* **Autonomía Compartida con Compensación de Latencia:** Controlador adaptativo con predictores de trayectoria para teleoperación en enlaces con retardo severo.



---
