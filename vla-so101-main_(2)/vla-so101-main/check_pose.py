import torch
import numpy as np

# 확인하고 싶은 포즈 데이터
pose = [0.0, -104.66, 96.09, 48.92, 90.0]
joints = ["Base (허리 회전)", "Shoulder (어깨)", "Elbow (팔꿈치)", "Wrist (손목)", "Gripper (집게)"]

print("\n" + "="*40)
print("      SO-ARM 101 관절 자세 분석")
print("="*40)

for name, angle in zip(joints, pose):
    status = ""
    if name == "Base (허리 회전)":
        status = "정면 응시" if angle == 0 else ("좌측" if angle > 0 else "우측")
    elif name == "Gripper (집게)":
        status = "중간 열림/닫힘 상태"
    
    print(f"📍 {name:<15} : {angle:>8.2f}°  {status}")

print("-"*40)
print("💡 분석 결과: 허리는 정면이고 팔을 앞으로 굽힌 '작업 준비' 자세입니다.")
print("="*40 + "\n")
