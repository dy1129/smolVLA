#!/usr/bin/env bash
set -euo pipefail

# SmolVLA fine-tuning on SO-101 pick-and-place demos
#
# Pretrained base: lerobot/smolvla_base (HuggingFace Hub)
# Freezes vision encoder, trains action expert + state projection
#
# Usage:
#   ./scripts/train.sh

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
  --dataset.image_transforms.max_num_transforms=3 \
  --dataset.image_transforms.random_order=true \
  --dataset.video_backend=pyav \
  --batch_size=16 \
  --steps=40000 \
  --save_freq=2000 \
  --save_checkpoint=true \
  --eval_freq=0 \
  --log_freq=100 \
  --num_workers=4 \
  --output_dir="${OUTPUT_DIR}" \
  --job_name="${JOB_NAME}" \
  --wandb.enable=false \
  "$@"
