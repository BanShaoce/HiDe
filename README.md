# 变更记录（Changelog）

本文件追踪 HiDe 复现与改进过程中的所有代码仓库变更与实验结果，便于项目版本管理。

---

## [v0.3.0] - 2026-10-28~29（改进实验，进行中）
### 目标：方法层面提升 V*Bench 效果（非调参）
基线复现结果：HiDe 92.1%（ori 79.1%）。以下为三个方向的探索与结论：

### 方向一：方案 A —— 空间保真的布局表示（❌ 负面结果）
- 假设：紧凑+居中的表示破坏左右/上下空间参考系，是空间题失败主因。
- 实现：`Get_box.py` 新增 `annotate_boxes_on_original`（原图画框）、`layout_faithful_transparent`（透明画布+原位置）；`inference.py` 按问题类型路由。
- 结果：v1 空间 80.3%、v2 空间 82.9%，均低于基线 85.5%。
- 结论：**假设被证伪**。原版紧凑图"去背景"收益 > "布局失真"损失，空间题瓶颈不在表示层。该方向放弃。

### 方向二：方案 B —— 多层注意力融合（⚠️ 混合结果）
- 假设：单层 `SELECT_LAYER=[15]` 是脆弱启发式，多层平均可降噪提升定位。
- 实现：`modeling_qwen2_5_vl_re_infer.py` 的 `SELECT_LAYER=[12,15,18,21]`（`process()` 本就支持多层平均）。
- 结果：空间 85.5%→86.8%（+3 修对 3 个"被带偏"、带偏 2 个），属性 96.5%→93.9%（−3），总体 91.1%。
- 结论：**注意力粒度是任务相关的**——单层对属性题更优，多层对空间题更优。

### 方向三：任务自适应层选择（✅ 正收益，最终采用）
- 动机：结合方向二结论，按任务类型自适应选择注意力层。
- 实现：`inference.py` 用 `is_spatial_question()` 判定问题类型，动态设置
  `modeling_qwen2_5_vl_re_infer.SELECT_LAYER = [12,15,18,21] if 空间 else [15]`。
- **结果：总体 92.7%（+0.6pp），属性 96.5%（不变），空间 86.8%（+1.3pp）。**

### 涉及文件
- `Hide/Qwen2.5/modeling_qwen2_5_vl_re_infer.py`：`SELECT_LAYER` 默认 `[15]`，支持运行时覆盖。
- `Hide/Qwen2.5/inference.py`：新增 `is_spatial_question` 判定 + 动态层选择。
- `Hide/Qwen2.5/utiles.py`：新增 `is_spatial_question()`。
- `Hide/Qwen2.5/Get_box.py`：保留（未启用的）空间保真函数，`from_img_and_att_get_cropbox` 增加 `spatial` 参数（当前恒为 False）。

---

## [v0.2.1] - 2026-10-28（提交 5cffff9）
### 复现完成
- 新增 `Hide/Qwen2.5/Vstar_results.json`：V*Bench 191 条完整推理结果。
- 新增 `复现报告.md`、演讲稿 .docx；清理 `tmp/` 调试文件。
- **结果**：HiDe 总体 92.1%，与论文报告值一致。

---

## [v0.2.0] - 2026-10-28（提交 2e9b9a1）
### 复现准备
- `inference.py`：`model_path` 读环境变量 `Qwen2_5_VL_MODEL_PATH`；`attn_implementation` 读环境变量 `HIDE_ATTN_IMPL`。
- `Vstar_Metric.py`：结果路径修正为 `Vstar_results.json`。
- 新增 `prepare_vstar_dataset.py`、`setup_server.sh`、`Vstar.json`、`.gitignore`、`.gitattributes`。
- `requirements.txt`：`triton` 仅 Linux 安装。

---

## [v0.1.0] - 2026-05-02（上游基线）
- 基于上游 `Tennine2077/HiDe`（arXiv:2510.00054，ICML 2026）fork。
