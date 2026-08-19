# 🤖🛰️ Robotarium Ecosystem: Distributed Low-Latency Multi-Agent Testbed

## 📋 Descripción del Proyecto

**Robotarium Ecosystem** es una plataforma modular, distribuida y de baja latencia diseñada para la orquestación, telemetría y control autónomo de flotas de micro-robots móviles en entornos de pruebas cerrados. El sistema unifica la percepción espacial mediante **visión cenital global con homografía en memoria RAM** y desacopla la comunicación mediante una arquitectura híbrida basada en **ZeroMQ** y **MQTT**.

---

## 🏛️ Orígenes y Atribución Académica

Este repositorio y su arquitectura amplían, refactorizan y optimizan la infraestructura original del **Robotarium** desarrollada en el **Departamento de Arquitectura de Computadores y Automática (DACyA)** de la Universidad Complutense de Madrid (UCM), en estrecha colaboración con las líneas de investigación del grupo **ISCAR** (*Systems Engineering, Control, Automation and Robotics*).

* **Línea Base Original:** Banco de pruebas experimental del DACyA / UCM para el estudio de control de robots móviles, sistemas multi-agente (*MAS*) y validación de algoritmos de navegación sin GPS mediante sensores virtuales cenitales.
* **Evolución y Rediseño Actual:** Optimización del pipeline de visión computacional (eliminación de cuellos de botella por transporte de vídeo Base64 en red), incorporación de una máquina de estados finitos (FSM) segura entre hilos con *watchdogs* de desconexión y estandarización de tópicos de telemetría individualizada por agente.

---

## 🏗️ Arquitectura del Sistema

El ecosistema opera dividiendo las responsabilidades en capas estrictamente desacopladas para garantizar determinismo y tiempos de respuesta inferiores a $30\text{ ms}$:

1. **Percepción Cenital Integrada (`vision_pos_agent.py`):** Captura flujos de vídeo de múltiples cámaras, aplica un proceso de costura (*stitching*) mediante una matriz de homografía $3 \times 3$ almacenada localmente (`homography_matrix.npy`), detecta marcadores ArUco y transforma píxeles a centímetros reales utilizando los límites del tatami (`tatami_config.json`). Todo el procesamiento ocurre en RAM, publicando directamente la posición y orientación de cada agente en tópicos individuales `{robot_id}/pos`.
2. **Orquestación Central (`robotarium_hub.py`):** Actúa como el *broker* central de red gestionando conexiones mediante sockets ZeroMQ (`PUB/SUB` y `REP/REQ`). Un único *event loop* (`zmq.Poller`) multiplexa de forma eficiente la retransmisión de datos de toda la flota.
3. **Control Autónomo y FSM (`agent_billar.py` / `agent_bounce.py`):** Clientes de misión inteligentes que gestionan la evasión de paredes y límites espaciales mediante una Máquina de Estados Finitos segura basada en colas thread-safe (`command_queue`), integrando sistemas de seguridad ante la pérdida temporal de telemetría (*watchdog* de $2.5\text{ s}$).

---

## 📊 Diagrama de Secuencia de la Arquitectura Integrada

A continuación se detalla el flujo completo de interacción entre los subsistemas, incluyendo los bucles de percepción, odometría, despacho seguro mediante cola y la máquina de estados con *watchdogs*:

![Arquitectura Integrada del Robotarium](docs/ArquitecturaCompletaRobotariumVisionUnificada.svg)
```plantuml
@startuml
title Arquitectura Integrada Completa Robotarium
autonumber

skinparam BoxPadding 10
skinparam ParticipantPadding 10

box "Percepcion Cenital" #LightBlue
participant "Camaras Cenitales\n(Cap A & B)" as Cams
participant "vision_pos_agent.py\n(VisionPosDevice)" as VisPos
end box

box "Orquestacion Red" #LightGray
participant "RobotariumHub\n(ZMQ Broker)" as Hub
end box

box "Control Autonomo" #LightYellow
participant "agent_billar.py\n(BouncerRobot FSM)" as Bouncer
participant "Thread: Command Queue\n(Despachador ZMQ)" as Dispatcher
end box

box "Robot Fisico (Robot ID 6)" #LightPink
participant "Raspberry Pi\n(Onboard ZMQ Agent)" as RPi
participant "Arduino MKR/Nano\n(Low-Level Hardware)" as Arduino
end box

== 1. Inicializacion y Suscripciones ==
Bouncer -> Hub: Suscripcion a topicos ZMQ:\n(6/pos, arena/boundaries, agent/6/feedback, agent/6/wheel)
Hub -> Bouncer: Forwarding data [topic: "arena/boundaries"]
Bouncer -> Bouncer: Actualiza boundaries, x_min, x_max, y_min, y_max

== 2. Bucle de Percepcion Cenital (RAM y Direct Transformation) ==
Cams -> VisPos: Captura fotogramas RGB (Cap A y B)
VisPos -> VisPos: Homografia (homography_matrix.npy) + Stitching en RAM
VisPos -> VisPos: Deteccion ArUco (DICT_4X4_50)
VisPos -> VisPos: Transforma Pixeles a cm Reales (M_pixel_to_real)
VisPos -> Hub: ZMQ PUB [topic: "6/pos"]\n(Payload: x, y, yaw, timestamp)
Hub -> Bouncer: Forwarding data [topic: "6/pos"]
Bouncer -> Bouncer: on_pos_received(): Actualiza pos, estimate y last_vision_time \nActualiza last_pos_time

== 3. Bucle de Feedback de Hardware y Odometria ==
Arduino -> RPi: Lectura Encoders / Serial
RPi -> Hub: ZMQ PUB [topic: "agent/6/wheel"]\n(Payload: Wleft, Wright)
Hub -> Bouncer: Forwarding data [topic: "agent/6/wheel"]
Bouncer -> Bouncer: on_odom_received(): Calcula cinematica diferencial (dx, dy, dtheta), last_odom_time

== 4. Bucle de Control FSM y Watchdogs (~20 Hz) ==
Bouncer -> Bouncer: Calcula time_since_vision = ahora - last_pos_time\nCalcula time_since_odom = ahora - last_odom_time

alt status == "ESPERANDO POSICION INICIAL"
    Bouncer -> Bouncer: Esperando primer paquete de vision
    Bouncer -> Dispatcher: command_queue.put({v: 0.0, w: 0.0})
    Dispatcher -> Dispatcher: command_queue.get()
    Dispatcher -> Hub: ZMQ PUB [topic: "agent/6/move"] {v: 0.0, w: 0.0}
    Hub -> RPi: Transmite orden de parada
    RPi -> Arduino: Mantener motores detenidos

else Watchdog Timeout (time_since_vision > 2.5s AND time_since_odom > 2.5s)
    Bouncer -> Bouncer: SISTEMA DESCONECTADO (Watchdog Timeout)
    Bouncer -> Dispatcher: command_queue.put({v: 0.0, w: 0.0})
    Dispatcher -> Dispatcher: command_queue.get()
    Dispatcher -> Hub: ZMQ PUB [topic: "agent/6/move"] {v: 0.0, w: 0.0}
    Hub -> RPi: Orden de parada de emergencia
    RPi -> Arduino: Aplicar freno de seguridad via Serial

else Telemetria Valida (Ejecucion Normal FSM)
    group Estado: AVANZA
        Bouncer -> Bouncer: get_distance_to_wall(x, y, theta)\n(dist_frontal, pared)
        alt dist_frontal >= danger_distance
            Bouncer -> Dispatcher: command_queue.put({v: self.v, w: 0.0})
            Dispatcher -> Dispatcher: command_queue.get()
            Dispatcher -> Hub: ZMQ PUB [topic: "agent/6/move"] {v: self.v, w: 0.0}
            Hub -> RPi: Transmite orden de movimiento
            RPi -> Arduino: Envia comando motor via Serial
        else dist_frontal < danger_distance
            Bouncer -> Bouncer: Transicion FSM a PARANDO_PARA_GIRAR\nstop_start_time = ahora
            Bouncer -> Dispatcher: command_queue.put({v: 0.0, w: 0.0})
            Dispatcher -> Dispatcher: command_queue.get()
            Dispatcher -> Hub: ZMQ PUB [topic: "agent/6/move"] {v: 0.0, w: 0.0}
            Hub -> RPi: Orden de freno
            RPi -> Arduino: Aplicar freno de seguridad via Serial
        end
    end
    
    group Estado: PARANDO_PARA_GIRAR
        alt (ahora - stop_start_time) >= stop_duration (Robot estabilizado)
            Bouncer -> Bouncer: Transicion FSM a GIRANDO
        else En espera
            Bouncer -> Bouncer: Mantiene parada fisica
        end
    
    group Estado: GIRANDO / ESPERANDO_GIRO
        Bouncer -> Bouncer: Transicion FSM a GIRANDO
        Bouncer -> Dispatcher: command_queue.put{ang: 180.0}
        Dispatcher -> Dispatcher: command_queue.get()
        Dispatcher -> Hub: ZMQ PUB [topic: "agent/6/turn"] {ang: 180.0}
        Hub -> RPi: Orden de giro
        RPi -> Arduino: Inicia rutina de giro sobre el propio eje
        Bouncer -> Bouncer: Transicion FSM a ESPERANDO_GIRO
        
        Arduino -> RPi: Giro de 180 grados completado
        RPi -> Hub: ZMQ PUB [topic: "agent/6/feedback"] {status: done, op: turn}
        Hub -> Bouncer: Forwarding feedback
        Bouncer -> Bouncer: giro_terminado = True -> Reanuda FSM a AVANZA
    end
end

@enduml

```

---

## 🚀 Guía de Despliegue Rápido

1. **Instalación de Dependencias:**
```bash
pip install pyzmq paho-mqtt opencv-python numpy

```


2. **Orden de Ejecución de Nodos en el Laboratorio:**
* **Paso 1:** Iniciar el orquestador central de red:
```bash
python3 robotarium_hub.py

```


* **Paso 2:** Iniciar el sistema unificado de visión y posicionamiento:
```bash
python3 vision_pos_agent.py --no-gui

```


* **Paso 3:** Lanzar el cliente autónomo de navegación para el robot objetivo:
```bash
python3 agent_billar.py

```





---

## 🧠 Roadmap: Inclusión de IA Avanzada (Próximamente)

*Este apartado se encuentra en fase de diseño estratégico y definición de especificaciones técnicas:*

* **Percepción Dinámica por Edge AI:** Sustitución o refuerzo del seguimiento por ArUco mediante modelos ligeros de detección de objetos en el borde (YOLOv11-Nano / ByteTrack) para la identificación de blancos móviles y dinámicos en entornos sin GPS (*GPS-Denied*).
* **Planificación Multi-Agente con GNN y CBF:** Evolución de la navegación reactiva hacia un planificador global basado en Redes Neuronales de Grafos (GNN) y Funciones de Barrera de Control (*Control Barrier Functions - CBF*) para la optimización de flotas de alta densidad y prevención de bloqueos mutuos (*deadlocks*).
* **Autonomía Compartida y Teleoperación con Retardo:** Integración de un árbitro inteligente (`twist_mux`) capaz de combinar mandos remotos con simulación de latencia espacial y anulación autónoma ante riesgos inminentes de colisión.
