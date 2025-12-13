# inference.py
import cv2
import numpy as np
import os
import glob
import time

class PaintDefectDetector:
    def __init__(self, model_path="model/svm_defect.xml", img_size=(512, 512)):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")
        
        self.model = cv2.ml.SVM_load(model_path)
        self.img_size = img_size
        print(f"✅ 模型加载成功，输入尺寸: {img_size}")
        
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
    
    def predict_single(self, img_path, with_timing=False):
        """预测单张图片，可选返回时间分解"""
        t0 = time.perf_counter()
        gray, mask = self.enhanced_preprocess(img_path)
        if gray is None:
            return {'error': '无法读取图片'}
        t1 = time.perf_counter()

        features = self.extract_robust_features(gray, mask)
        t2 = time.perf_counter()
        features = features.reshape(1, -1).astype(np.float32)
        _, result = self.model.predict(features)
        prediction = int(result[0, 0])
        t3 = time.perf_counter()

        resp = {
            'prediction': prediction,
            'confidence': '缺陷' if prediction == 1 else '正常',
            'image_name': os.path.basename(img_path)
        }
        if with_timing:
            resp['timing'] = {
                'preprocess_ms': (t1 - t0) * 1000,
                'feature_ms': (t2 - t1) * 1000,
                'predict_ms': (t3 - t2) * 1000,
                'total_ms': (t3 - t0) * 1000
            }
        return resp

    def classify_features(self, features_array):
        """仅对由客户端/其他节点提取的特征进行分类。features_array: list/np.array"""
        feats = np.array(features_array, dtype=np.float32).reshape(1, -1)
        _, result = self.model.predict(feats)
        prediction = int(result[0, 0])
        return {
            'prediction': prediction,
            'confidence': '缺陷' if prediction == 1 else '正常'
        }
    
    def predict_batch(self, image_dir):
        """批量预测"""
        results = []
        for img_path in glob.glob(os.path.join(image_dir, "*.png")) + \
                      glob.glob(os.path.join(image_dir, "*.jpg")):
            result = self.predict_single(img_path)
            if result is not None and 'error' not in result:
                results.append(result)
        return results

# 使用示例
if __name__ == "__main__":
    detector = PaintDefectDetector("model/svm_defect.xml")
    
    # 单张图片预测
    result = detector.predict_single("test_image.png", with_timing=True)
    print(f"检测结果: {result}")