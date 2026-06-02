#!/usr/bin/env bash
set -euo pipefail

# SmolVLA fine-tuning for bomb pick-and-place task

export RUST_LOG=error

DATASET="kmg0620/so101_bomb_pick_place_v1"
OUTPUT_DIR="outputs/train/smolvla_so101_bomb"
JOB_NAME="smolvla_so101_bomb"

exec uv run python scripts/train.py \
  --policy.path=lerobot/smolvla_base \
  --policy.device=cuda \
  --policy.push_to_hub=false \
  --dataset.repo_id="${DATASET}" \
  --dataset.image_transforms.enable=true \
  --dataset.video_backend=pyav \
  --batch_size=64 \
  --steps=20000 \
  --save_freq=5000 \
  --save_checkpoint=true \
  --eval_freq=0 \
  --log_freq=100 \
  --num_workers=4 \
  --output_dir="${OUTPUT_DIR}" \
  --job_name="${JOB_NAME}" \
  --wandb.enable=false \
  "$@"
