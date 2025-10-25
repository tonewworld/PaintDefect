#  漆面缺陷检测系统

##  项目简介

漆面缺陷检测系统是一个基于机器学习的智能检测工具，能够自动识别漆面表面的各种缺陷，如划痕、气泡、污点等。系统采用计算机视觉技术和支持向量机(SVM)算法，实现高效准确的缺陷检测。

###  主要特性
-  **智能检测**: 自动识别漆面缺陷
-  **快速处理**: 实时检测，响应迅速  
-  **高准确率**: 基于机器学习算法
-  **Web界面**: 友好的用户交互界面
-  **可视化结果**: 直观展示检测过程

##  系统架构

### 技术栈
- **后端**: Python + Flask
- **机器学习**: OpenCV + scikit-learn
- **前端**: HTML + CSS + JavaScript
- **算法**: SVM (支持向量机)

### 核心模块
- `train.py` - 模型训练脚本
- `inference.py` - 推理检测模块
- `app.py` - Web应用入口
- `test_model.py` - 模型测试工具

##  数据集下载

### 数据集信息
- **数据来源**: [通用瑕疵集合]
- **图片数量**: 575张训练图片
- **图片尺寸**: 512×512像素
- **标注格式**: YOLO格式 (.txt文件)

### 下载地址
 [点击下载漆面缺陷数据集](  https://gitcode.com/open-source-toolkit/1ce67  )


##  快速开始

### 环境要求
- Python 3.8+
- OpenCV 4.5+
- scikit-learn 1.0+
- Flask 2.0+

### 安装步骤

1. **克隆项目**
   
```markdown
`git clone https://github.com/tonewworld/PaintDefect.git`
`cd PaintDefect`
```

2. **安装依赖**

```markdown
`pip install -r requirements.txt`
```

4. **准备数据集**

下载数据集并解压到 dataset/train/

确保包含 .png 图片和对应的 .txt 标注文件

最终目录结构：
PaintDefect/
├── .gitignore
├── dataset/
│ ├── train/
│ └── valid/
├── model/
├── output/
├── static/
│ └── uploads/
├── test_images/
├── templates/
├── app.py
├── inference.py
├── train.py
├── test_model.py
├── requirements.txt
└── README.md

4. **运行训练脚本**

```markdown
`python train.py`
```

训练参数
图片尺寸: 512×512

特征维度: 15维

算法: SVM with RBF kernel

数据平衡: 自动上采样

5. **启动服务**

```markdown
`python app.py`
```
本地端口:http://127.0.0.1:5000

