**基于机器学习的智能漆面缺陷检测系统 — 中期报告**

**项目概述**:

- **课题名称**: 基于机器学习的智能漆面缺陷检测系统
- **目标**: 构建端云协同的漆面缺陷检测原型，使用 OpenCV 做预处理与特征提取，使用 SVM 做分类，提供可运行的训练与推理脚本，并评估性能。

**一、研究背景与意义**:

- 本项目目标替代/辅助人工目视检测，提升检测效率与一致性，降低人力成本，具有明显工程与经济价值（详见作业文档中的背景部分）。

**二、研究目标与当前实现映射**:

- **实现自动化检测**: 已实现批量训练与单张图像推理流程。
  - 代码位置: `train.py`（训练与特征工程）、`inference.py`（推理接口与特征提取）。
- **保证高准确率（目标>85%）**: 当前实现基于传统特征+SVM的原型，提供训练/评估（`train.py` 中打印训练与测试准确率和分类报告）。
- **支持实时处理（<3s/张）**: `inference.py` 的 `predict_single(..., with_timing=True)` 会返回耗时分解，可用于评估是否满足实时性要求。实际响应时间与机器性能与图片尺寸相关。
- **友好交互**: 已实现云端脚本与基准测试脚本用于验证（`benchmark.py`, `benchmark_classify_only.py`）；移动端 App 尚在规划中（未实现）。
- **可扩展架构**: 代码结构模块化——`inference.py` 封装检测器，`train.py` 封装训练流程，推理与训练使用相同的特征提取函数，便于未来替换为深度模型。

**三、主要内容与对应实现文件**:

- **系统总体架构（移动端 + 云端）**: 项目仓库中侧重云端原型实现；移动端为后续任务。
  - 相关文件: `app.py`（预期提供 REST API, 仓库含该文件用于后续集成）、`inference.py`（云端推理模块）、`benchmark*.py`（性能验证脚本）。
- **核心检测算法**:
  - 图像预处理: `enhanced_preprocess` 在 `train.py` 与 `inference.py` 中实现（自适应阈值 + Canny 边缘 + 形态学处理）。
  - 特征提取: `extract_robust_features` 实现 Hu 矩、轮廓统计、纹理与梯度特征等多维特征。
  - 分类器: SVM（scikit-learn 训练在 `train.py`，并把模型也以 OpenCV SVM 格式保存到 `model/svm_defect.xml`）。
- **动态计算划分策略（S0-S3）**: 目前为设计目标，仓库中尚未实现该策略（将在后续集成移动端与策略器模块）。

**四、关键模块说明（代码要点）**:

- `train.py`:
  - 功能: 加载 `dataset/train` 下图片与同名 `.txt` 标签（存在则视为缺陷），包含数据平衡（上采样）、特征提取、使用 scikit-learn 的 `svm.SVC` 训练，并使用 OpenCV 的 SVM 保存为 `model/svm_defect.xml`。
  - 入口: 在 `if __name__ == "__main__"` 中创建 `model/` 目录并调用 `PaintDefectTrainer().train_model()`。
- `inference.py`:
  - 功能: 封装 `PaintDefectDetector`，加载 `model/svm_defect.xml`，提供 `predict_single`（单图预测并可返回耗时细分）、`classify_features`（接受客户端提取的特征直接分类）和 `predict_batch`。
- `benchmark.py` / `benchmark_classify_only.py`:
  - 功能: 向后端发送图片或特征，收集延迟并输出统计（平均/中位/最小/最大/分位数），用于性能验证与对比不同模式。
- `analyze_mobile_logs.py` / `visualize_logs.py`:
  - 功能: 分析前端导出的性能日志并生成统计（`summary.json`, `summary.csv`），以及绘制基本图表（`output/figs`）。

**六、当前已知结果与评价**:

- 代码已实现从图像预处理、特征提取到 SVM 训练与推理的端到端原型。
- `inference.py` 中提供的耗时分解可直接用于验证“单张图片 < 3s”的目标；在常见台式机/服务器上，特征提取+SVM 推理通常远低于 3s，但在低功耗移动端需进一步优化与量化测试。

**七、未完成项与下一步计划**:

- 未完成项:

  - 移动端 App（图像采集、端侧预处理与特征提取）尚未实现。
  - 动态计算划分策略（S0-S3）尚处于设计阶段，需实现策略器并与 `inference.py` / 客户端特征提取接口协同。
  - 精度評估：需準備標注更完整的数据集并做交叉验证以确认是否达到 >85% 指标。
- 下一步 (短期 2 周内建议):

  1. 将 `predict_single` 与 `classify_features` 封装为 Flask/FastAPI 的 REST endpoint（若 `app.py` 未实现则优先实现）。
  2. 实现简单的移动端/模拟客户端脚本（Python）进行端侧特征提取并调用 `/classify`，验证端云划分。
  3. 设计并实现一个基础版的动态划分策略模块（根据模拟网络延迟与设备性能选择 S0-S3），集成到基准测试流程中。
