"""Solve IK for box lid pickup. Run OUTSIDE Isaac Sim, in env_isaaclab.

    conda activate env_isaaclab
    python solve_pick_ik.py

This saves /tmp/pick_sequence.json which the in-sim script will read.
"""

import json
import math
import sys

import numpy as np

# === lerobot kinematics ===
from lerobot.model.kinematics import RobotKinematics

URDF = "/home/delivery/team5/telerobot/src/telerobot/simulation/SO101/so101_new_calib.urdf"

# Monkey patches for placo numpy-scalar bug
_orig_ik = RobotKinematics.inverse_kinematics
_orig_fk = RobotKinematics.forward_kinematics

def _ik_patched(self, current, desired, pos_w, ori_w):
    return _orig_ik(self, np.asarray(current, dtype=float),
                    np.asarray(desired, dtype=float),
                    float(pos_w), float(ori_w))

def _fk_patched(self, joint_pos):
    return _orig_fk(self, np.asarray(joint_pos, dtype=float))

RobotKinematics.inverse_kinematics = _ik_patched
RobotKinematics.forward_kinematics = _fk_patched

kin = RobotKinematics(urdf_path=URDF, target_frame_name="gripper_link")

# === Geometry (from our USD scene) ===
# robot_2 world pose: translate (-0.22, 0.30, 0.80), quat z-axis -90°
# BoxLidHandle world: (-0.22, -0.085, 0.935), height 3cm so top z=0.95

# Handle top in robot_2 base frame:
#   world delta = (0, -0.385, 0.15)
#   inverse rotation (z +90°): (x', y') = (-dy, dx) -> (0.385, 0)
#   -> handle in robot base = (0.385, 0.0, 0.15)
HANDLE_BASE = np.array([0.385, 0.0, 0.15])

APPROACH_Z_ABOVE = 0.05   # 5cm above handle top
GRASP_DZ_BELOW   = 0.005  # 0.5cm below handle top to ensure contact
LIFT_HEIGHT      = 0.12   # 12cm lift

GRIPPER_OPEN_DEG  = 0.0
GRIPPER_CLOSE_DEG = 35.0

# Initial guess: safe folded pose, in degrees
INITIAL_GUESS_DEG = np.array([0.0, -90.0, 90.0, 0.0, 0.0])


def pose_topdown(x, y, z):
    """Gripper +x points -z (down); gripper +z points +x (robot forward)."""
    T = np.eye(4)
    T[:3, :3] = np.array([
        [0, 1, 0],
        [0, 0, 1],
        [-1, 0, 0],
    ])
    T[:3, 3] = [x, y, z]
    return T


def main():
    hx, hy, hz = HANDLE_BASE
    waypoints = [
        ("approach", pose_topdown(hx, hy, hz + APPROACH_Z_ABOVE), GRIPPER_OPEN_DEG),
        ("descend",  pose_topdown(hx, hy, hz - GRASP_DZ_BELOW),   GRIPPER_OPEN_DEG),
        ("close",    pose_topdown(hx, hy, hz - GRASP_DZ_BELOW),   GRIPPER_CLOSE_DEG),
        ("lift",     pose_topdown(hx, hy, hz + LIFT_HEIGHT),      GRIPPER_CLOSE_DEG),
    ]

    guess = INITIAL_GUESS_DEG.copy()
    seq = []
    for name, ee_pose, grip in waypoints:
        sol = kin.inverse_kinematics(guess, ee_pose,
                                     position_weight=1.0,
                                     orientation_weight=0.5)
        sol = np.asarray(sol, dtype=float).tolist()
        print("  %-9s joints_deg=%s gripper=%.1f" % (name, sol, grip))
        seq.append({"name": name, "joints_deg": sol, "gripper_deg": grip})
        guess = np.array(sol)

    out = {
        "motor_names": ["shoulder_pan", "shoulder_lift", "elbow_flex",
                        "wrist_flex", "wrist_roll"],
        "waypoints": seq,
    }
    out_path = "/tmp/pick_sequence.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print("saved -> " + out_path)


if __name__ == "__main__":
    main()
