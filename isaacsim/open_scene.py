"""Open the USD scene directly in Isaac Sim."""
import sys
sys.stdout.reconfigure(line_buffering=True)

try:
    from isaacsim import SimulationApp
except ImportError:
    from omni.isaac.kit import SimulationApp
sim_app = SimulationApp({"headless": False})

from omni.isaac.core import World
from omni.isaac.core.utils.stage import open_stage, get_current_stage
from pxr import UsdLux


USD_PATH = "/home/delivery/team5/isaacsim/0512_box_custom_mirobot.usda"

open_stage(usd_path=USD_PATH)

world = World(stage_units_in_meters=1.0)

stage = get_current_stage()
if not stage.GetPrimAtPath("/World/DomeLight").IsValid():
    _light = stage.DefinePrim("/World/DomeLight", "DomeLight")
    UsdLux.LightAPI(_light).CreateIntensityAttr(1000.0)

world.reset()

while sim_app.is_running():
    world.step(render=True)

sim_app.close()
