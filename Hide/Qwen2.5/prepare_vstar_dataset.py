# -*- coding: utf-8 -*-
"""下载官方 V*Bench (craigwu/vstar_bench) 并转换为 HiDe 仓库要求的 Vstar.json。

只下载论文用到的 191 个主评测样本（direct_attributes + relative_position）+ 标注，
跳过 GPT4V-hard / OCR 等无关子集。

用法（在 Hide/Qwen2.5 目录下）:
    python prepare_vstar_dataset.py
国内网络建议:
    $env:HF_ENDPOINT="https://hf-mirror.com"
"""
import os
import json
import time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ID = "craigwu/vstar_bench"
IMG_ROOT = os.path.join(HERE, "vstar_bench")
JSONL = os.path.join(IMG_ROOT, "test_questions.jsonl")
OUT_JSON = os.path.join(HERE, "Vstar.json")

ALLOW = ["test_questions.jsonl", "direct_attributes/*", "relative_position/*"]


def download():
    from huggingface_hub import snapshot_download
    print(f"[1/3] 下载 {REPO_ID} -> {IMG_ROOT}")
    last = None
    for attempt in range(1, 6):
        try:
            snapshot_download(
                repo_id=REPO_ID,
                repo_type="dataset",
                local_dir=IMG_ROOT,
                allow_patterns=ALLOW,
                max_workers=4,
            )
            break
        except Exception as e:
            last = e
            wait = 30 * attempt
            print(f"    第 {attempt} 次失败: {type(e).__name__}; {wait}s 后重试...")
            time.sleep(wait)
    else:
        raise last
    if not os.path.exists(JSONL):
        raise FileNotFoundError(f"未找到 {JSONL}，请检查下载是否完整")


def convert():
    print("[2/3] 转换标注为 Vstar.json")
    records = []
    with open(JSONL, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            records.append({
                "id": str(r["question_id"]),
                "question": r["text"],
                "labels": str(r["label"]).strip().upper(),
                "image_path": os.path.join("vstar_bench", r["image"]).replace("\\", "/"),
                "category": r["category"],
            })
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    return records


def verify(records):
    print("[3/3] 校验")
    cnt = Counter(r["category"] for r in records)
    print("  总样本数:", len(records), "（论文为 191）")
    for k, v in sorted(cnt.items()):
        print(f"  {k}: {v}")
    missing = [r["image_path"] for r in records
               if not os.path.exists(os.path.join(HERE, r["image_path"].replace('/', os.sep)))]
    bad_label = [r["id"] for r in records if r["labels"] not in ("A", "B", "C", "D")]
    print("  缺失图片数:", len(missing), "| 非法答案数:", len(bad_label))
    if missing:
        print("  前几个缺失图片:", missing[:5])
    print("  输出:", OUT_JSON)


if __name__ == "__main__":
    if not os.path.exists(JSONL):
        download()
    records = convert()
    verify(records)
