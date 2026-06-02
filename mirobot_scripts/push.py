
"""호밍 → 단계적 후진 → 하강 → 전진 → J5 위로 90도 → 호밍"""
import glob, time
from wlkata_mirobot import WlkataMirobot

port = sorted(glob.glob('/dev/ttyUSB*'))[0]
arm = WlkataMirobot(portname=port)


def safe_pose():
    """pose 읽기 실패 시 재시도"""
    for _ in range(3):
        try:
            return arm.pose
        except Exception:
            time.sleep(1)
    return None


print("=== 호밍 ===")
arm.home()
time.sleep(2)
p = safe_pose()
print(f"호밍 후: x={p.x:.1f}, z={p.z:.1f}")

print("\n=== 단계적 후진 (10mm씩 -70mm) ===")
for i in range(7):
    target = p.x - 10 * (i + 1)
    arm.set_tool_pose(x=target, y=p.y, z=p.z)
    time.sleep(0.1)
    actual = safe_pose()
    print(f"  명령 x={target:.0f} → 실제 x={actual.x:.1f}")

p2 = safe_pose()
print(f"\n후진 완료: x={p2.x:.1f}")

print("\n=== 하강 (-150mm) ===")
arm.set_tool_pose(x=p2.x, y=p2.y, z=p2.z - 150)
time.sleep(2)
p3 = safe_pose()
print(f"하강 후: x={p3.x:.1f}, z={p3.z:.1f}")

print("\n=== 전진 (x=290) ===")
arm.set_tool_pose(x=290, y=p3.y, z=p3.z)
time.sleep(2)
p4 = safe_pose()
print(f"전진 후: x={p4.x:.1f}")

print("\n=== J5 위로 90도 회전 ===")
arm.set_joint_angle({5: -90})
time.sleep(2)

print("\n=== 호밍 복귀 ===")
arm.home()
print("✅ 완료")

