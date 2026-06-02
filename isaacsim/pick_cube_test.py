import asyncio
import numpy as np
import traceback
import omni

from omni.isaac.core import World
from omni.isaac.core.articulations import Articulation
from omni.isaac.core.utils.types import ArticulationAction

# ⚠️ 로봇 경로
ROBOT_PRIM_PATH = "/BoxEnv/so101_new_calib" 

async def manual_joint_movement():
    try:
        print("\n========================================")
        print("🚀 [시작] SO-101 로봇: 그리퍼 강제 닫기!! (안정적인 구조 적용) 🚀")
        print("========================================")
        
        # [안정화 핵심 1] 찌꺼기 World가 남아있다면 깔끔하게 지우고 새로 시작
        if World.instance() is not None:
            World.clear_instance()

        world = World(stage_units_in_meters=1.0)
        await world.initialize_simulation_context_async()
        
        # 1. 로봇 객체 생성 및 씬에 추가
        robot = Articulation(prim_path=ROBOT_PRIM_PATH, name="so101_robot")
        world.scene.add(robot)
        
        # [안정화 핵심 2] 안전한 초기화 순서: reset -> play -> initialize
        await world.reset_async()
        await world.play_async()
        robot.initialize()
        
        print(f"✅ 로봇 초기화 완벽! (관절 {robot.num_dof}개)")

        # [안정화 핵심 3] 아이작 심 UI 프레임과 동기화하는 가장 안전한 대기 함수
        async def step_frames(n=1):
            for _ in range(n):
                await omni.kit.app.get_app().next_update_async()

        # 부드러운 움직임 생성 함수
        async def move_slowly(target_angles, duration=3.0, fps=60):
            current_angles = robot.get_joint_positions()
            target_angles = np.array(target_angles, dtype=np.float32)
            
            if len(target_angles) != robot.num_dof:
                raise ValueError(
                    f"입력한 각도 개수({len(target_angles)})와 로봇 관절 개수({robot.num_dof})가 다릅니다!"
                )

            steps = max(1, int(duration * fps))
            
            for i in range(1, steps + 1):
                alpha = i / steps
                interpolated_angles = current_angles + (target_angles - current_angles) * alpha
                robot.apply_action(ArticulationAction(joint_positions=interpolated_angles))
                await step_frames(1) # 프레임 단위로 부드럽게 업데이트

        # 🔥 방향 완벽 반전! 마이너스가 닫는 거였어!! 🔥

        GRIPPER_OPEN = 1.0    # 쫙 벌림!
        GRIPPER_CLOSE = -0.15 # 꽉 물어버림! (URDF 최소 한계치 근처)

        # 💡 5번째 자리(손목)를 np.pi / 2 (90도)로 수정! 
        # 처음에 90도 꺾은 뒤, 2단계와 3단계에서도 똑같이 유지합니다.
        
        # 1단계: 처음에 손목 90도 딱 꺾고, Y축 맞춘 상태로 그대로 쭉 하강!
        target_angles_1 = np.array([-0.28, 1.66, -1.0, 1.3, np.pi / 2, GRIPPER_OPEN], dtype=np.float32)
        print("⏳ 1단계: 손목 90도 꺾고 위치 보정하며 하강 중...")
        await move_slowly(target_angles_1, duration=3.0)
        
        await step_frames(60) 
        
        # 2단계: 90도 꺾은 거 그대로 유지하고 쭉~ 닫기!!
        target_angles_2 = np.array([-0.28, 1.66, -1.0, 1.3, np.pi / 2, GRIPPER_CLOSE], dtype=np.float32)
        print("⏳ 2단계: 큐브 포착! 그리퍼 꽉 닫아!!!")
        await move_slowly(target_angles_2, duration=1.0)
        
        await step_frames(90)

        # 3단계: 90도 꺾고 쥔 상태 그대로 위로 복귀! 
        target_angles_3 = np.array([-0.28, 0.0, 0.0, 0.0, np.pi / 2, GRIPPER_CLOSE], dtype=np.float32)
        print("⏳ 3단계: 꽉 쥐고 올라간다!!")
        await move_slowly(target_angles_3, duration=3.0)

        print("🎉 끝!! 이번엔 에러 없이 완벽하게 닫힐 겁니다!")
        print("========================================\n")

    except Exception:
        print("\n🚨 에러 발생 🚨")
        print(traceback.format_exc()) 

# 스크립트 실행
asyncio.ensure_future(manual_joint_movement())
