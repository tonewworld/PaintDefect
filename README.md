# 基于机器学习的漆面缺陷检测系统

本项目实现了一个基于 **Python + OpenCV + SVM** 的漆面缺陷智能检测系统，用于识别汽车 / 家电等产品漆面上的划痕、气泡、污点等表面缺陷。系统提供从 **模型训练 → 云端推理服务 → Web 前端演示 → 端云协同与性能评估** 的完整闭环。

> 课程背景：软件体系结构 / 边缘计算 / 端云协同实验项目。

---

## 功能概述

- **自动缺陷检测**：对输入图像进行预处理、特征提取并用 SVM 分类，判断是否存在漆面缺陷。
- **轻量级特征 + SVM**：通过手工设计的低维特征（Hu 矩 + 轮廓 + 纹理统计等）实现高效分类，适合在资源有限设备上部署。
- **Web 演示界面**：基于 Flask + HTML/JS 实现上传图片、查看预测结果与耗时的可视化页面。
- **端云协同模式**：
  - `full_remote`：整图上传，云端完成预处理 + 特征 + 分类。
  - `classify_only`：端侧完成预处理和特征提取，仅上传特征向量，云端只做分类。
  - `auto`：服务器根据历史耗时与当前 CPU/文件大小给出推荐模式（不强制切换）。
- **性能与并发分析**：提供脚本对不同分区模式和并发度进行基准测试与可视化。

---

## 技术栈

- **后端 / 服务端**
  - Python 3
  - Flask：HTTP API & Web 服务
  - OpenCV：图像处理与（推理侧）SVM 模型加载
  - scikit-learn：训练阶段的 SVM 建模与评估

- **前端**
  - HTML / CSS
  - JavaScript（可扩展为使用 OpenCV.js 在浏览器端做特征提取）

- **机器学习**
  - 算法：SVM（RBF 核）
  - 特征：Hu 不变矩、轮廓形状特征、区域占比、强度统计等

---

## 仓库结构

```text
PaintDefect/
├── app.py                     # Flask Web 服务，暴露 / 和 /predict /classify 等接口
├── train.py                   # 模型训练脚本：预处理、特征提取、SVM 训练
├── inference.py               # 推理引擎：加载模型并执行预测
├── test_model.py              # 对训练好的模型进行离线测试
├── benchmark.py               # 单接口基准测试（端到端耗时）
├── benchmark_classify_only.py # classify_only 模式并发测试脚本
├── benchmark_concurrent.py    # full_remote 模式并发测试脚本
├── summarize_concurrency.py   # 并发测试结果汇总
├── analyze_mobile_logs.py     # 移动端性能日志分析
├── visualize_logs.py          # 性能数据可视化（图表）
├── mobile_perf_logs.json      # 示例移动端端到端性能日志
├── summary.json               # 性能汇总 JSON
├── summary.csv                # 性能汇总 CSV
├── model/                     # 训练好的 SVM 模型（如 svm_defect.xml）
├── static/                    # 前端静态文件（JS/CSS/上传文件等）
│   └── uploads/               # 服务端保存上传图片（运行时创建）
├── templates/
│   └── index.html             # Web UI：上传图片、选择模式、展示结果
├── output/                    # 基准测试与可视化输出目录
├── requirements.txt           # Python 依赖
├── README.md                  # 本说明文档
├── MIDTERM_REPORT.md          # 中期报告（课程文档）
└── EXPERIMENT_PLAN.md         # 实验方案（课程文档）
```

> 实际数据集目录（如 `dataset/train`、`dataset/valid`）不会包含在仓库中，需要根据下文说明自行准备。

---

## 数据集说明

- **数据来源**：通用表面瑕疵集合（适配漆面缺陷场景）
- **样本规模**：约 575 张训练图片
- **图像尺寸**：512 × 512 像素
- **标注格式**：YOLO 格式（每张图片对应 `.txt` 标注文件）

> 如需复现训练流程，请按自己的数据格式做适配或参考 `train.py` 中的加载逻辑。  
> 若你有自己的工业场景数据，可将其整理为统一尺寸灰度/彩色图像，并在 `train.py` 中配置路径与标签规则。

---

## 安装与运行

### 1. 克隆仓库

```bash
git clone https://github.com/tonewworld/PaintDefect.git
cd PaintDefect
```

### 2. 创建并激活虚拟环境（推荐）

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
# source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 准备数据集（用于重新训练）

建议目录结构示例：

```text
PaintDefect/
├── dataset/
│   ├── train/    # 训练集
│   └── valid/    # 验证/测试集
└── ...
```

要求：

- `dataset/train`、`dataset/valid` 中包含 `.png` / `.jpg` 等图像文件
- 若使用 YOLO 标注，则需保证每张图片有对应的 `.txt` 标签文件
- 具体路径与标签读取逻辑可在 `train.py` 中调整

---

## 模型训练与测试

### 1. 启动训练

```bash
python train.py
```

训练脚本主要步骤：

- 遍历数据集目录，读取图像并统一缩放到 `512×512`
- 预处理：
  - 灰度化
  - 自适应阈值 + Canny 边缘检测
  - 按位或融合 + 椭圆核开运算去噪
- 特征提取：
  - 7 维 Hu 不变矩（对数 + 符号变换）
  - 轮廓面积、周长、数量、面积占比等
  - 缺陷区域占比与强度统计
- 使用 SVM（RBF 核）训练，并输出精度、召回率、F1 值等指标
- 保存模型到 `model/svm_defect.xml`

> 在给定数据集上，目前实验准确率约为 **88.4%**。

### 2. 测试已有模型

```bash
python test_model.py
```

该脚本会加载 `model/svm_defect.xml`，对指定测试集进行预测并输出统计结果。

---

## 启动 Web 服务

训练完成或已有模型后，可以直接启动 Web 服务：

```bash
python app.py
```

默认访问地址：

- 本地浏览器打开：[http://127.0.0.1:5000](http://127.0.0.1:5000)

功能：

- 上传单张图片进行缺陷检测
- 选择 `mode`（full_remote / classify_only / auto）
- 显示预测结果与各阶段耗时（预处理 / 特征 / 预测 / 总耗时）

---

## API 接口说明

### 1. `/predict` – 上传图片进行预测

- **方法**：`POST`
- **Content-Type**：`multipart/form-data`
- **参数**：
  - `file`：图像文件
  - `mode`（可选）：`full_remote` / `classify_only` / `auto`，默认 `full_remote`

示例：

```bash
curl -X POST http://127.0.0.1:5000/predict \
  -F "file=@dataset/train/sample.png" \
  -F "mode=full_remote"
```

响应示例：

```json
{
  "label": "defect",
  "score": 0.92,
  "mode": "full_remote",
  "timing": {
    "preprocess_ms": 25.4,
    "feature_ms": 13.2,
    "predict_ms": 2.3,
    "total_ms": 41.7,
    "endpoint_ms": 68.9
  },
  "advisory": {
    "recommended_mode": "classify_only",
    "reason": "avg_file=712345, cpu=62.3, avg_server=271.5"
  }
}
```

说明：

- `label` / `score`：分类结果与置信度（示例字段，具体以实现为准）。
- `timing.*_ms`：服务器端各阶段耗时（毫秒）。
- `endpoint_ms`：整个 HTTP 请求在服务器端的端到端耗时。
- `advisory`：当客户端传 `mode=auto` 时，服务端会给出推荐模式与原因（当前实现 **不强制切换** 执行模式）。

### 2. `/classify` – 上传特征向量进行分类

- **方法**：`POST`
- **Content-Type**：`application/json`
- **请求体**：

```json
{
  "features": [0.1, 0.2, 0.3, ..., 1.5]
}
```

示例：

```bash
curl -X POST http://127.0.0.1:5000/classify \
  -H "Content-Type: application/json" \
  -d '{"features": [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1,1.1,1.2,1.3,1.4,1.5]}'
```

响应示例：

```json
{
  "label": "defect",
  "score": 0.88,
  "mode": "classify_only",
  "timing": { "predict_ms": 2.1 }
}
```

---

## 分区模式与端云协同

系统支持三种主要模式，用于研究“端侧 vs 云端”计算分工：

| 模式          | 描述                               | 适用场景                               |
| ------------- | ---------------------------------- | -------------------------------------- |
| `full_remote` | 整图上传，云端执行完整流水线       | 端侧算力有限或网络较好                 |
| `classify_only` | 端侧完成预处理与特征提取，仅上传特征 | 希望减少上传体积、端侧具备一定算力     |
| `auto`        | 服务端根据 CPU/文件大小/历史耗时给出推荐 | 用于演示简单的动态卸载策略与自适应能力 |

当前版本中：

- `classify_only` 已在服务端实现 `/classify` 接口与并发测试脚本，但端侧真实特征提取逻辑需要在移动端或 Web 前端配合开发。
- `auto` 仅返回建议（`advisory.recommended_mode`），不会强制修改当前请求的执行模式，方便前端渐进接入。

---

## 性能与并发测试

### 1. 基本基准测试

```bash
python benchmark.py \
  --server http://127.0.0.1:5000 \
  --images dataset/train \
  --modes full_remote auto \
  --repeat 3 \
  --limit 5
```

输出示例（JSON）：

```json
{
  "full_remote": {"count": 15, "avg_ms": 210.4, "median_ms": 205.8, "min_ms": 180.2, "max_ms": 260.9},
  "auto":        {"count": 15, "avg_ms": 212.7, "median_ms": 207.3, "min_ms": 181.5, "max_ms": 265.1}
}
```

### 2. 并发压测与模式对比

- `full_remote` 模式并发压测：

```bash
python benchmark_concurrent.py \
  --server http://127.0.0.1:5000 \
  --images dataset/train \
  --concurrency 1 5 10 \
  --duration 30 \
  --mode full_remote \
  --out full_remote_conc.json
```

- `classify_only` 模式并发压测（先本地提取特征，再 POST `/classify`）：

```bash
python benchmark_classify_only.py \
  --server http://127.0.0.1:5000 \
  --images dataset/train \
  --concurrency 1 5 10 \
  --duration 30 \
  --limit 50 \
  --out classify_only_conc.json
```

- 汇总并可视化：

```bash
python summarize_concurrency.py \
  --files full_remote_conc.json classify_only_conc.json \
  --outdir output/conc
```

将生成：

- `output/conc/conc_summary.csv`
- `output/conc/rps_vs_concurrency.png`
- `output/conc/p90_vs_concurrency.png`

---

## 移动端端到端性能分析

仓库中包含：

- `mobile_perf_logs.json`：移动端（浏览器 / App）采集的端到端日志
- `analyze_mobile_logs.py`、`visualize_logs.py`：用于生成端到端时延与时间分解图

示意结论：

- `full_remote`：上传耗时占比较高，对网络带宽与 RTT 较敏感。
- `classify_only`：本地特征提取略增加端侧 CPU 开销，但显著减少上传体积和总体时延。
- 可进一步通过调整图像压缩质量、分辨率与批处理策略优化端到端体验。

---

## 后续扩展方向

- **模型升级**：引入轻量级 CNN（如 MobileNet / ShuffleNet）进行对比实验，替换或补充现有手工特征 + SVM。
- **更智能的分区策略**：基于历史日志训练简单回归 / 强化学习模型，动态选择 full_remote / classify_only。
- **端侧实现强化**：
  - 使用 OpenCV.js / WebAssembly 在浏览器端实现特征提取。
  - 在移动端原生 App 中集成本地预处理与特征计算模块。
- **上传优化**：尝试只上传增量特征、压缩后的特征或多帧聚合等方式，进一步降低带宽占用。

---

## 许可证

本项目主要用于学习与研究目的。若需在生产环境中使用或二次开发，请根据实际情况选择合适的开源许可证并补充到仓库中。
