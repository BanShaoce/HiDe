#!/usr/bin/env bash
# HiDe 服务器一键搭建 + 推理（AutoDL / Linux）
# 用法: bash setup_server.sh
set -euo pipefail

cd "$(dirname "$0")/Hide/Qwen2.5"

echo "==> [1/6] 安装依赖（沿用镜像自带 torch，不重装）"
pip install -r ../../requirements.txt

echo "==> [2/6] 尝试安装 flash-attn（失败则自动回退 sdpa）"
if pip install flash-attn --no-build-isolation >/dev/null 2>&1; then
  export HIDE_ATTN_IMPL=flash_attention_2
  echo "    flash-attn OK -> flash_attention_2"
else
  export HIDE_ATTN_IMPL=sdpa
  echo "    flash-attn 失败 -> 回退 sdpa"
fi

MODEL_DIR="$PWD/Qwen2.5-VL-7B-Instruct"
export Qwen2_5_VL_MODEL_PATH="$MODEL_DIR"

echo "==> [3/6] 下载模型 Qwen2.5-VL-7B-Instruct（ModelScope 国内快）"
if [ -f "$MODEL_DIR/config.json" ]; then
  echo "    模型已存在，跳过"
else
  pip install modelscope
  modelscope download --model Qwen/Qwen2.5-VL-7B-Instruct --local_dir "$MODEL_DIR"
fi

echo "==> [4/6] 清理旧结果"
rm -f Vstar_results.json

echo "==> [5/6] 运行推理 cycle_infer.py"
python cycle_infer.py

echo "==> [6/6] 计算指标 Vstar_Metric.py"
python Vstar_Metric.py
