# train.py
import cv2
import numpy as np
import os
import glob
from sklearn import svm
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pandas as pd

class PaintDefectTrainer:
    def __init__(self, img_size=(512, 512)):
        self.img_size = img_size
        
    def enhanced_preprocess(self, img_path):
        """增强的预处理"""
        img = cv2.imread(img_path)
        if img is None:
            return None, None
        
        img = cv2.resize(img, self.img_size)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 多种阈值方法组合
        binary1 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                       cv2.THRESH_BINARY_INV, 15, 8)
        
        edges = cv2.Canny(gray, 50, 150)
        combined = cv2.bitwise_or(binary1, edges)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        cleaned = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel, iterations=1)
        
        return gray, cleaned
    
    def extract_robust_features(self, gray, mask):
        """提取更鲁棒的特征"""
        features = []
        
        # 1. 基础形状特征
        moments = cv2.moments(mask)
        hu_moments = cv2.HuMoments(moments).flatten()
        
        for h in hu_moments[:7]:
            if h != 0:
                features.append(-np.copysign(np.log10(abs(h)), h))
            else:
                features.append(0)
        
        # 2. 轮廓分析
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if cnts:
            cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:3]
            
            total_area = 0
            total_perimeter = 0
            max_area = 0
            contour_count = 0
            
            for cnt in cnts:
                area = cv2.contourArea(cnt)
                if area < 10:
                    continue
                    
                perimeter = cv2.arcLength(cnt, True)
                total_area += area
                total_perimeter += perimeter
                max_area = max(max_area, area)
                contour_count += 1
            
            if contour_count > 0:
                features.append(total_area * 1e-4)
                features.append(max_area * 1e-4)
                features.append(total_area / (self.img_size[0] * self.img_size[1]))
                features.append(contour_count)
                features.append(total_perimeter * 1e-2)
            else:
                features.extend([0, 0, 0, 0, 0])
        else:
            features.extend([0, 0, 0, 0, 0])
        
        # 3. 纹理特征
        defect_ratio = np.count_nonzero(mask) / (mask.shape[0] * mask.shape[1])
        features.append(defect_ratio)
        
        # 4. 统计特征
        features.append(np.mean(mask) / 255.0)
        features.append(np.std(mask) / 255.0)
        
        # 5. 梯度特征
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(sobelx**2 + sobely**2)
        features.append(np.mean(gradient_magnitude) * 1e-3)
        
        return np.array(features)
    
    def create_balanced_dataset(self):
        """创建平衡的数据集"""
        X, y, paths = [], [], []
        train_dir = "dataset/train"
        
        defect_files = []
        normal_files = []
        
        # 分类文件
        for file in glob.glob(os.path.join(train_dir, "*.png")):
            base_name = os.path.splitext(os.path.basename(file))[0]
            label_path = os.path.join(train_dir, f"{base_name}.txt")
            
            if os.path.exists(label_path) and os.path.getsize(label_path) > 0:
                defect_files.append(file)
            else:
                normal_files.append(file)
        
        print(f"原始数据 - 缺陷: {len(defect_files)}, 正常: {len(normal_files)}")
        
        # 平衡采样（上采样缺陷样本）
        if len(defect_files) < len(normal_files):
            # 重复缺陷样本直到数量相当
            repeat_times = len(normal_files) // len(defect_files)
            remainder = len(normal_files) % len(defect_files)
            
            balanced_defect = defect_files * repeat_times + defect_files[:remainder]
        else:
            balanced_defect = defect_files
        
        print(f"平衡后 - 缺陷: {len(balanced_defect)}, 正常: {len(normal_files)}")
        
        # 处理缺陷样本
        for file in balanced_defect:
            gray, mask = self.enhanced_preprocess(file)
            if gray is not None:
                features = self.extract_robust_features(gray, mask)
                X.append(features)
                y.append(1)  # 缺陷
                paths.append(os.path.basename(file))
        
        # 处理正常样本
        for file in normal_files:
            gray, mask = self.enhanced_preprocess(file)
            if gray is not None:
                features = self.extract_robust_features(gray, mask)
                X.append(features)
                y.append(0)  # 正常
                paths.append(os.path.basename(file))
        
        return np.array(X), np.array(y), paths
    
    def train_model(self):
        """训练模型"""
        print("开始训练漆面缺陷检测模型...")
        
        X, y, paths = self.create_balanced_dataset()
        print(f"训练数据形状: X={X.shape}, y={y.shape}")
        print(f"标签分布: 缺陷={sum(y==1)}, 正常={sum(y==0)}")
        
        # 分割训练测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # 训练SVM
        clf = svm.SVC(
            kernel='rbf',
            gamma='scale',
            class_weight='balanced',
            probability=True,
            random_state=42
        )
        
        clf.fit(X_train, y_train)
        
        # 评估
        train_score = clf.score(X_train, y_train)
        test_score = clf.score(X_test, y_test)
        
        print(f"\n=== 训练结果 ===")
        print(f"训练准确率: {train_score:.3f}")
        print(f"测试准确率: {test_score:.3f}")
        
        y_pred = clf.predict(X_test)
        print("\n详细分类报告:")
        print(classification_report(y_test, y_pred, target_names=['正常', '缺陷']))
        
        # 保存模型
        model = cv2.ml.SVM_create()
        model.setType(cv2.ml.SVM_C_SVC)
        model.setKernel(cv2.ml.SVM_RBF)
        model.train(X.astype(np.float32), cv2.ml.ROW_SAMPLE, y.astype(np.int32))
        model.save("model/svm_defect.xml")
        
        print(f"\n模型已保存: model/svm_defect.xml")
        print(f"特征维度: {X.shape[1]}")
        
        return clf

if __name__ == "__main__":
    # 创建模型目录
    os.makedirs("model", exist_ok=True)
    
    # 训练模型
    trainer = PaintDefectTrainer()
    trainer.train_model()