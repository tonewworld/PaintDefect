## 移动端与云端协同实验方案 (Part A/B/C)

### 目标
评估漆面缺陷检测工作流在不同分区模式、网络条件与图片尺寸下的端到端时延构成，分析影响因素并验证动态分区策略的有效性。

### 应用阶段划分
1. 客户端: 摄像/选择 -> (可选) 压缩重采样 -> 上传
2. 服务端: 预处理 preprocess -> 特征提取 feature -> 分类 predict -> 端点包装 endpoint
3. 返回与渲染: 响应解析 + 结果展示

### 分区模式
| 模式 | 描述 | 上传内容 | 期望收益 |
|------|------|----------|----------|
| full_remote | 服务端完整流水线 | 原始或压缩图像 | 客户端简单，适合好网络 |
| classify_only | 客户端提取特征，仅服务器分类 | 特征向量 (后续实现) | 减少传输，降低延迟 |
| auto | 简易策略基于 CPU & 文件大小 | 原始或压缩图像 | 演示动态决策 |

### 采集指标
客户端：`capture_ms`, `compress_ms`, `network_ms`, `response_parse_ms`, `total_client_ms`, 原始/上传文件大小 (KB), 网络信息 (effectiveType, downlink, rtt)。
服务端：`preprocess_ms`, `feature_ms`, `predict_ms`, `total_ms`, `endpoint_ms`。
综合：`end_to_end_ms = total_client_ms + server.total_ms` (或具体阶段相加)。

### 设备与网络
设备：至少两种手机 (中端/高端)。
网络：Wi-Fi、4G/5G、热点/限速 (如模拟 1Mbps)。

### 图片维度与压缩策略
原始分辨率 (若 >1024 宽则记录)、重采样到 1024 / 512 / 256 三种。记录压缩耗时与大小变化。

### 实验设计
1. 固定模式 full_remote，变化网络类型与分辨率。
2. 比较 full_remote 与 auto 在不同文件大小下的差异。
3. 后续实现 classify_only 后，对比上传大小与时延缩减百分比。
4. 统计每组下 P50、P90、最大、最小与标准差。

### 数据记录
前端导出 `mobile_perf_logs.json`。脚本 `benchmark.py` 批量测服务器基线。汇总时按字段清洗：
```json
{
  "device": "PhoneA",
  "network": "wifi",
  "entries": [ ... front-end logs ... ],
  "summary": {
    "full_remote": {"avg_end_to_end_ms": 210.4, "p90": 250.1},
    "auto": {"avg_end_to_end_ms": 208.7, "p90": 248.2}
  }
}
```

### 分析方法
1. 绘制条形图: 模式 vs 平均耗时。
2. 分段堆叠: 客户端捕获+网络+服务器阶段占比。
3. 相关性: 上传大小 vs 网络耗时 (散点拟合)。
4. 策略收益: (full_remote_avg - classify_only_avg)/full_remote_avg。

### 动态分区扩展 (后续)
策略输入：`upload_size`, `recent_network_ms_avg`, `server_cpu`, `queue_length`。
决策输出：选择模式或调整压缩级别。可用简单规则或训练分类器 (特征 -> 模式)。

### 风险与控制
1. 后端冷启动影响第一次请求：预热一个空图片请求。
2. 网络统计波动：每组样本数量 >= 15。
3. 设备后台任务干扰：测试前清理后台应用。

### 判定 Part A 完成标准
具备手机拍照 → 上传 → 接收 → 时延分解；存在真实手机测试日志 ≥3 网络场景；README/报告含结论和分析。

### 判定 Part B 完成标准
有多模式测试对比表；明确影响因素 (网络、尺寸、CPU、分区模式)；有图或表证明差异。

### 判定 Part C 完成标准
提供自动决策原型 (auto)；展示若干场景下决策与耗时对比；提出改进策略路线图。
