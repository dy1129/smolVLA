"""SO-ARM101 keyboard joint teleop in Isaac Sim.

Each key controls one joint by ±. SPACE prints (and remembers) the current pose
so you can copy-paste it into the auto pick code later.

Controls
--------
  Q / A : shoulder_pan   + / -
  W / S : shoulder_lift  + / -
  E / D : elbow_flex     + / -
  R / F : wrist_flex     + / -
  T / G : wrist_roll     + / -
  Y / H : gripper open / close
  SPACE : save current joint pose (printed in degrees)
  P     : print all saved poses
  ESC   : quit
"""
import sys, numpy as np

sys.stdout.reconfigure(line_buffering=True)

try:
    from isaacsim import SimulationApp
except ImportError:
    from omni.isaac.kit import SimulationApp
sim_app = SimulationApp({"headless": False})

import carb
import omni.appwindow
from omni.isaac.core import World
from omni.isaac.core.articulations import Articulation
from omni.isaac.core.utils.stage import add_reference_to_stage, get_current_stage
from pxr import UsdLux


# ── config ────────────────────────────────────────────────────────────────
USD_PATH   = "/home/delivery/team5/isaacsim/0512_box_custom.usda"
SCENE_ROOT = "/World/Scene"
ROBOT_PRIM = f"{SCENE_ROOT}/so101_robot_1"  # 1번 팔
STEP_DEG   = 0.7   # per-frame angle step (degrees). Lower = smoother but slower
GRIP_STEP_DEG = 1.5

# Joint index in articulation (URDF order):
# 0: shoulder_pan, 1: shoulder_lift, 2: elbow_flex,
# 3: wrist_flex, 4: wrist_roll, 5: gripper
KI = carb.input.KeyboardInput
KEY_TO_JOINT = {
    KI.Q: (0, +1), KI.A: (0, -1),
    KI.W: (1, +1), KI.S: (1, -1),
    KI.E: (2, +1), KI.D: (2, -1),
    KI.R: (3, +1), KI.F: (3, -1),
    KI.T: (4, +1), KI.G: (4, -1),
    KI.Y: (5, +1), KI.H: (5, -1),
}


# ── stage + robot ─────────────────────────────────────────────────────────
world = World(stage_units_in_meters=1.0)
add_reference_to_stage(usd_path=USD_PATH, prim_path=SCENE_ROOT)

stage = get_current_stage()

# Dome light so the scene isn't pitch black
_light = stage.DefinePrim("/World/DomeLight", "DomeLight")
UsdLux.LightAPI(_light).CreateIntensityAttr(1000.0)

robot = Articulation(prim_path=ROBOT_PRIM, name="r1")
world.scene.add(robot)
world.reset()

# Move to a safe upright starting pose so the arm doesn't smash into objects on reset
SAFE_POSE_DEG = np.array([0.0, -90.0, 90.0, 0.0, 0.0, 0.0])
init_q = robot.get_joint_positions().copy()
init_q[:6] = np.deg2rad(SAFE_POSE_DEG)
robot.set_joint_positions(init_q)
print(f"Initial pose (deg): {SAFE_POSE_DEG.tolist()}")

# Let physics settle for a moment
for _ in range(10):
    world.step(render=True)


# ── keyboard ──────────────────────────────────────────────────────────────
app_window = omni.appwindow.get_default_app_window()
keyboard = app_window.get_keyboard()
inp = carb.input.acquire_input_interface()

saved_poses = []
running = True

def on_keyboard_event(event):
    """Fired once per key press (not per frame). Use for SPACE / P / ESC."""
    global running
    if event.type != carb.input.KeyboardEventType.KEY_PRESS:
        return
    if event.input == KI.SPACE:
        q_deg = np.degrees(robot.get_joint_positions())[:6]
        saved_poses.append(q_deg.copy())
        print(f"\n[#{len(saved_poses)}] joints (deg) = "
              f"[{', '.join(f'{x:7.2f}' for x in q_deg)}]\n")
    elif event.input == KI.P:
        print("\n=== Saved poses so far ===")
        for i, p in enumerate(saved_poses, 1):
            print(f"  pose_{i} = np.array([{', '.join(f'{x:.2f}' for x in p)}])  # deg")
        print()
    elif event.input == KI.ESCAPE:
        running = False
        print("[esc] quitting")

sub = inp.subscribe_to_keyboard_events(keyboard, on_keyboard_event)


# ── help ──────────────────────────────────────────────────────────────────
print("""
╔══════════════════════════════════════════════════════════════════╗
║  SO-ARM101 keyboard teleop                                       ║
║                                                                  ║
║   Q/A  shoulder_pan ±    W/S  shoulder_lift ±                   ║
║   E/D  elbow_flex   ±    R/F  wrist_flex    ±                   ║
║   T/G  wrist_roll   ±    Y/H  gripper open/close                ║
║                                                                  ║
║   SPACE  save current pose                                       ║
║   P      print all saved poses                                   ║
║   ESC    quit                                                    ║
║                                                                  ║
║   NOTE: focus the Isaac Sim viewport for keys to register        ║
╚══════════════════════════════════════════════════════════════════╝
""")


# ── main loop ─────────────────────────────────────────────────────────────
step_rad = np.deg2rad(STEP_DEG)
grip_step_rad = np.deg2rad(GRIP_STEP_DEG)

while sim_app.is_running() and running:
    q = robot.get_joint_positions().copy()

    for key, (joint_idx, direction) in KEY_TO_JOINT.items():
        if inp.get_keyboard_value(keyboard, key) > 0:
            step = grip_step_rad if joint_idx == 5 else step_rad
            q[joint_idx] += direction * step

    robot.set_joint_positions(q)
    world.step(render=True)

# Final dump of saved poses
if saved_poses:
    print("\n=== Final saved poses ===")
    for i, p in enumerate(saved_poses, 1):
        print(f"  pose_{i} = np.array([{', '.join(f'{x:.2f}' for x in p)}])  # deg")
    print()

sim_app.close()
