"""Move SO-ARM101 robot 1 to hover above the red sphere — minimal IK demo."""
import os, sys, numpy as np

# Force line buffering so print() output shows up in real time (Isaac Sim buffers stdout)
sys.stdout.reconfigure(line_buffering=True)

# Isaac Sim must boot before any omni.* imports
try:
    from isaacsim import SimulationApp
except ImportError:
    from omni.isaac.kit import SimulationApp
sim_app = SimulationApp({"headless": False})

from omni.isaac.core import World
from omni.isaac.core.articulations import Articulation
from omni.isaac.core.utils.stage import add_reference_to_stage, get_current_stage
from pxr import UsdGeom, UsdLux
from lerobot.model.kinematics import RobotKinematics


# ── monkey-patch: placo's set_joint refuses np.float64; wrap with float() ──
def _patched_ik(self, current_joint_pos, desired_ee_pose,
                position_weight=1.0, orientation_weight=0.01):
    current_joint_rad = np.deg2rad(current_joint_pos[: len(self.joint_names)])
    for i, joint_name in enumerate(self.joint_names):
        self.robot.set_joint(joint_name, float(current_joint_rad[i]))  # ← cast
    self.tip_frame.T_world_frame = desired_ee_pose
    self.tip_frame.configure(self.target_frame_name, "soft",
                             float(position_weight), float(orientation_weight))
    self.solver.solve(True)
    self.robot.update_kinematics()
    q_rad = [self.robot.get_joint(jn) for jn in self.joint_names]
    q_deg = np.rad2deg(q_rad)
    if len(current_joint_pos) > len(self.joint_names):
        result = np.zeros_like(current_joint_pos)
        result[: len(self.joint_names)] = q_deg
        result[len(self.joint_names):] = current_joint_pos[len(self.joint_names):]
        return result
    return q_deg

RobotKinematics.inverse_kinematics = _patched_ik


# Same numpy-scalar issue may bite forward_kinematics too
_orig_fk = RobotKinematics.forward_kinematics

def _patched_fk(self, joint_pos_deg):
    joint_pos_rad = np.deg2rad(joint_pos_deg[: len(self.joint_names)])
    for i, joint_name in enumerate(self.joint_names):
        self.robot.set_joint(joint_name, float(joint_pos_rad[i]))
    self.robot.update_kinematics()
    return np.array(self.robot.get_T_world_frame(self.target_frame_name))

RobotKinematics.forward_kinematics = _patched_fk


# ── config ────────────────────────────────────────────────────────────────
USD_PATH   = "/home/delivery/team5/isaacsim/0512_box_custom.usda"
URDF_PATH  = "/home/delivery/team5/telerobot/src/telerobot/simulation/SO101/so101_new_calib.urdf"
SCENE_ROOT = "/World/Scene"
ROBOT_PRIM = f"{SCENE_ROOT}/so101_robot_1"
TARGET_PRIM = f"{SCENE_ROOT}/Sphere_Red"

MOTOR_NAMES = ["shoulder_pan", "shoulder_lift", "elbow_flex",
               "wrist_flex", "wrist_roll", "gripper"]

# Robot 1 base pose in world (from USD)
BASE_POS  = np.array([-0.45, 0.30, 0.80])
BASE_QUAT = np.array([0.7071068, 0.0, 0.0, -0.7071068])  # (w,x,y,z), z-axis -90°


# ── helpers ───────────────────────────────────────────────────────────────
def quat_to_rot(q):
    w, x, y, z = q
    return np.array([
        [1-2*(y*y+z*z),   2*(x*y-z*w),     2*(x*z+y*w)],
        [2*(x*y+z*w),     1-2*(x*x+z*z),   2*(y*z-x*w)],
        [2*(x*z-y*w),     2*(y*z+x*w),     1-2*(x*x+y*y)],
    ])

BASE_R = quat_to_rot(BASE_QUAT)
world_to_base = lambda p: BASE_R.T @ (p - BASE_POS)

def world_pos(prim_path):
    prim = get_current_stage().GetPrimAtPath(prim_path)
    if not prim or not prim.IsValid():
        raise RuntimeError(f"prim not found: {prim_path}")
    m = UsdGeom.XformCache().GetLocalToWorldTransform(prim)
    return np.array(m.ExtractTranslation())


# ── stage + robot ─────────────────────────────────────────────────────────
world = World(stage_units_in_meters=1.0)
add_reference_to_stage(usd_path=USD_PATH, prim_path=SCENE_ROOT)

# Debug: show what's actually under /World/Scene
stage = get_current_stage()
print("\n=== children of", SCENE_ROOT, "===")
for c in stage.GetPrimAtPath(SCENE_ROOT).GetChildren():
    print(" ", c.GetPath(), c.GetTypeName())
print()

# Add a dome light so the scene isn't pitch black
_light = stage.DefinePrim("/World/DomeLight", "DomeLight")
UsdLux.LightAPI(_light).CreateIntensityAttr(1000.0)

robot = Articulation(prim_path=ROBOT_PRIM, name="r1")
world.scene.add(robot)
world.reset()


# ── IK solver (inline; no telerobot import) ───────────────────────────────
kin = RobotKinematics(
    urdf_path=URDF_PATH,
    target_frame_name="gripper_frame_link",
    joint_names=MOTOR_NAMES,
)
kin.solver.add_regularization_task(1e-3)

# Debug: where do the gripper frame's axes point at the all-zero pose?
zero_fk = kin.forward_kinematics(np.zeros(6))
print("\n=== Gripper frame at all-zero joints (in robot BASE frame) ===")
print(f"Position: {np.round(zero_fk[:3, 3], 4)}")
print(f"  gripper +x axis in base: {np.round(zero_fk[:3, 0], 3)}")
print(f"  gripper +y axis in base: {np.round(zero_fk[:3, 1], 3)}")
print(f"  gripper +z axis in base: {np.round(zero_fk[:3, 2], 3)}")
print()


# ── one-shot: hover 5 cm above red sphere ────────────────────────────────
sphere_w = world_pos(TARGET_PRIM)
print(f"[target] sphere world = {sphere_w}")


def make_top_down_pose(offset_world=(0, 0, 0)):
    """4×4 target pose in robot base frame, gripper pointing down.

    SO-ARM101 gripper_frame_link convention (from FK debug):
        gripper +x = forward (closing direction)
        gripper +y = between fingers
        gripper +z = perpendicular to fingers
    Top-down grasp: gripper +x → base -z (forward points down)
    """
    p_world = sphere_w + np.array(offset_world)
    p_base = world_to_base(p_world)
    pose = np.eye(4)
    pose[:3, 3] = p_base
    pose[:3, :3] = np.array([
        [0,  0, -1],
        [0, -1,  0],
        [-1, 0,  0],
    ])
    return pose


def go_to_ee_pose(target_pose, n_steps=80):
    """IK + interpolate in joint space, stepping the simulator."""
    q_start = robot.get_joint_positions().copy()
    q_deg_start = np.degrees(q_start[:6])
    q_new_deg = kin.inverse_kinematics(
        q_deg_start, target_pose,
        position_weight=1.0, orientation_weight=0.0,  # 위치만, 자세는 자유
    )
    q_target = q_start.copy()
    q_target[:6] = np.radians(q_new_deg[:6])
    print(f"  IK: target joints (deg) = {np.round(q_new_deg[:6], 2)}")

    for i in range(n_steps):
        alpha = (i + 1) / n_steps
        q_step = (1 - alpha) * q_start + alpha * q_target
        robot.set_joint_positions(q_step)
        world.step(render=True)


def set_gripper(value_rad, n_steps=30):
    """Open/close gripper while holding arm pose."""
    q_start = robot.get_joint_positions().copy()
    grip_start = q_start[5]
    for i in range(n_steps):
        alpha = (i + 1) / n_steps
        q = robot.get_joint_positions().copy()
        q[5] = (1 - alpha) * grip_start + alpha * value_rad
        robot.set_joint_positions(q)
        world.step(render=True)


def hold(n=30):
    for _ in range(n):
        world.step(render=True)


# Gripper open/close values (rad). Tune if it slips / over-closes.
GRIP_OPEN = 0.0
GRIP_CLOSED = 1.0  # ~57°. Try 0.5–1.3 if needed.

# Pick sequence ----------------------------------------------------------
print("Step 1/4: hover above sphere")
go_to_ee_pose(make_top_down_pose((0, 0, 0.05)), n_steps=100)
hold(20)

print("Step 2/4: open gripper")
set_gripper(GRIP_OPEN, n_steps=20)
hold(10)

print("Step 3/4: descend to sphere")
go_to_ee_pose(make_top_down_pose((0, 0, 0.0)), n_steps=60)
hold(20)

print("Step 4/4: close gripper + lift")
set_gripper(GRIP_CLOSED, n_steps=30)
hold(20)
go_to_ee_pose(make_top_down_pose((0, 0, 0.10)), n_steps=60)
hold(30)

print("Done. Holding for 60 frames then closing.")


# ── run sim ───────────────────────────────────────────────────────────────
for _ in range(60):
    world.step(render=True)
sim_app.close()
