# SENTINEL: SmolVLA-Based Robotic Security Inspection System

SENTINEL is a university research project that prototypes an automated airport security inspection workflow using object detection, SmolVLA-based robot manipulation, dual SO-101 robot arms, and a real-time dashboard.

The system scans objects placed in a tray, detects hazardous items, and uses robot arms to isolate the hazardous objects inside a containment box.

## System Overview

```text
Tray image
   -> Object detection
   -> Hazard decision
   -> SmolVLA Skill 1: Open containment box
   -> SmolVLA Skill 2: Move hazardous object into the box
   -> SmolVLA Skill 3: Close containment box
   -> Real-time dashboard
```

The project was designed as a modular system. Instead of treating the whole task as one long action, the process was divided into scanning, decision-making, and three robot manipulation skills.

## Main Task

The target scenario is an airport security tray inspection task.

The system detects five object classes:

- Battery
- Explosive
- Key Ring
- Tape
- Tissue

Battery and Explosive are treated as hazardous objects. When a hazardous object is detected, the robot performs a containment sequence using three SmolVLA-based skills.

## SmolVLA Skill Design

### Skill 1: Open the Box

The robot opens the containment box before removing hazardous objects.

### Skill 2: Remove Hazardous Object

The robot picks up the detected hazardous object and places it into the containment box.

### Skill 3: Close the Box

After the hazardous object is isolated, the robot closes the containment box.

Splitting the task into three skills made the system easier to train, test, and debug. Each skill could be checked separately before being connected into the full inspection flow.

## System Components

### Object Detection

YOLO was used to detect objects in the tray. The detection result is used to decide whether the robot should start the containment sequence.

The YOLO model was trained on five object classes and reached about 97% detection performance.

### Robot Manipulation

SmolVLA was used for robot manipulation. The project used SO-101 robot arms and camera observations to perform the box-opening, hazardous-object removal, and box-closing tasks.

### Dashboard

The dashboard shows the state of the system during the inspection process.

It displays:

- Top camera view
- Wrist camera view
- Detected objects
- Hazard status
- Current system step
- Robot task progress

## Hardware and Tools

- Dual SO-101 robot arms
- Top camera
- Wrist camera
- YOLO
- SmolVLA
- LeRobot-based robot learning workflow
- Web dashboard
- Isaac Sim for simulation setup and visualization

## Project Scope

This project is a research prototype.

- It was not deployed in a real airport.
- It is not a certified safety system.
- Reinforcement learning was considered during planning, but the final project used SmolVLA.
- Isaac Sim was used for simulation setup and visualization, not as a completed sim-to-real training system.

## Project Context

This project was developed during the 2026 Spring semester at Kookmin University as a four-person team project. The goal was to connect AI perception, robot learning, physical robot control, and real-time monitoring into one working prototype.
