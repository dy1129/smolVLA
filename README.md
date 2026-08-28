# SENTINEL: SmolVLA-Based Robotic Security Inspection

SENTINEL is a UROP project that combines object detection, Vision-Language-Action (VLA) policy learning, dual SO-101 robot arms, and a real-time dashboard to prototype an automated airport security inspection workflow.

The system detects objects in a tray, identifies hazardous items such as batteries and explosives, opens a containment box, removes the hazardous item with a SmolVLA-based manipulation policy, closes the box, and displays the full process through a web dashboard.

## Project Overview

This project was built as a modular robotics pipeline rather than a single end-to-end model.

```text
Top Camera
   -> YOLO Object Detection
   -> Hazard Decision
   -> Skill 1: Open containment box
   -> Skill 2: Remove hazardous item with SmolVLA
   -> Skill 3: Close containment box
   -> SENTINEL Web Dashboard
```

The task was divided into three sub-skills so that data collection, training, debugging, and execution could be handled step by step.

- **Skill 1**: Open the containment box
- **Skill 2**: Pick up a hazardous item and place it into the box
- **Skill 3**: Close the containment box

## Key Features

- Dual SO-101 robot arm setup
- VR teleoperation-based data collection
- SmolVLA fine-tuning for manipulation tasks
- YOLO-based tray object detection
- Hazard classification for Battery and Explosive objects
- WebSocket-based real-time dashboard
- Top-camera and wrist-camera monitoring
- State-machine based task orchestration
- Re-scan loop after each hazard removal

## My Contributions

- Integrated YOLO object detection, SmolVLA robot execution, and the SENTINEL dashboard into one workflow.
- Built the dashboard server flow: scan the tray, detect hazards, open the box, remove each hazard, scan again, and close the box.
- Connected top-camera and wrist-camera streams to the dashboard so the system state could be checked during the demo.
- Configured the dual SO-101 arms, camera settings, task prompts, and dataset paths for battery/explosive removal.
- Added reset logic for data recording so each episode could start from a stable robot pose.
- Modified the SmolVLA training wrapper so the training code could use the camera names in our dataset.
- Wrote helper scripts for dataset merging, robot diagnosis, and Isaac Sim trajectory replay.

## Simple Results

- YOLO detected 5 object classes with about 97% performance.
- SmolVLA was connected to the real robot arm for task execution.
- The dashboard displayed camera views, detection results, and robot progress in real time.

## System Components

### 1. Object Detection

The tray scene is scanned with a YOLO model trained to detect five object classes:

- Battery
- Explosive
- Key Ring
- Tape
- Tissue

Battery and Explosive are treated as hazardous objects. The dashboard waits until the expected objects are detected stably before moving to the decision stage.

YOLO was trained for 50 epochs and reached about 97% detection performance.

### 2. SmolVLA Manipulation

SmolVLA was used as the main robot learning approach for the manipulation policy. The project originally considered both reinforcement learning and VLA-based learning, but the final implementation focused on SmolVLA because it was more practical for the available project time and better aligned with recent robot learning workflows.

The manipulation task was divided into smaller skills instead of training one long-horizon policy at once. This made it easier to collect demonstrations, isolate failure points, and debug each part of the workflow.

### 3. Robot and Camera Setup

The robot configuration uses two SO-101 follower arms and two cameras.

- Left SO-101 arm
- Right SO-101 arm
- Top camera for tray-level object detection
- Wrist camera for manipulation observation
- 30 FPS control/recording setting
- 320 x 240 camera resolution in the project configuration

### 4. Dashboard

The SENTINEL dashboard visualizes the security inspection process in real time.

Displayed information includes:

- Top camera stream
- Wrist camera stream
- YOLO detection result
- Hazard status
- System flow log
- Current manipulation stage
- Scan / decision / skill execution state

The dashboard server uses WebSocket messages to send camera frames, scan results, logs, and state updates to the browser UI.

## Repository Structure

```text
.
├── isaacsim/                  # Isaac Sim scene and robot simulation assets
├── mirobot_scripts/           # Mirobot utility scripts
├── telerobot/                 # VR teleoperation, data recording, dashboard, and robot execution code
│   ├── config.yaml            # Dual-arm SO-101 configuration
│   ├── config_bomb.yaml       # Dataset/task configuration for explosive removal
│   ├── infer.py               # Direct SmolVLA inference runner
│   ├── merge_skill2_datasets.py
│   └── system/
│       ├── dashboard_server.py
│       ├── sentinel_kmu (2).html
│       └── yolo11_cards/
│           ├── weights/
│           └── results.csv
└── vla-so101-main_(2)/         # SmolVLA / LeRobot-based training and inference workspace
    └── vla-so101-main/
        ├── configs/
        ├── scripts/
        └── models/
```

## Example Commands

### Install telerobot dependencies

```bash
cd telerobot
poetry install
```

### Run VR teleoperation

```bash
poetry run telerobot -c config.yaml
```

### Record explosive-removal demonstrations

```bash
poetry run telerobot -c config_bomb.yaml
```

### Fine-tune SmolVLA for the bomb pick-and-place task

```bash
cd ../vla-so101-main_(2)/vla-so101-main
./scripts/train_bomb.sh
```

The training script fine-tunes `lerobot/smolvla_base` with:

- batch size: 64
- training steps: 20,000
- checkpoint save frequency: 5,000 steps
- image transforms enabled
- CUDA device

### Run the SENTINEL dashboard server

```bash
cd telerobot
poetry run python system/dashboard_server.py \
  --yolo system/yolo11_cards/weights/best.pt \
  --camera 4 \
  --ws-port 8765
```

With a robot configuration:

```bash
poetry run python system/dashboard_server.py \
  --yolo system/yolo11_cards/weights/best.pt \
  --camera 4 \
  --ws-port 8765 \
  --robot-config config.yaml
```

## Technical Notes

- YOLO is executed only at explicit scan stages so it does not compete continuously with the SmolVLA inference loop.
- Hazard removal is handled as a repeated loop: after one hazardous object is processed, the tray is scanned again.
- Skill 1 and Skill 3 can be executed through recorded trajectory replay.
- Skill 2 uses a direct SmolVLA runner for pick-and-place execution.
- The dashboard can fall back to mock skill execution when the robot is not connected.

## Scope and Limitations

This repository is a university research prototype.

- It is not an industrial safety-certified system.
- It was not deployed in an actual airport environment.
- Isaac Sim was used for simulation environment setup and visualization, not for a completed sim-to-real training claim.
- Reinforcement learning was considered during the project planning stage, but the final project focused on SmolVLA-based learning.
- The system is organized as a modular robotics pipeline, not as a single unified end-to-end VLA model.

## Project Context

This project was developed during the 2026 Spring semester as a four-person team project at Kookmin University. The implementation focused on connecting AI perception, robot policy learning, hardware control, and a real-time monitoring dashboard into one working prototype.
