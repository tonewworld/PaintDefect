# test_model.py
import cv2
import numpy as np
import os
import glob
from inference import PaintDefectDetector

def comprehensive_test():
    """全面测试模型性能"""
    print("=== 漆面缺陷检测模型测试 ===")
    
    # 加载模型
    model_path = "model/svm_defect.xml"
    if not os.path.exists(model_path):
        print("❌ 模型文件不存在，请先运行 train.py 训练模型")
        return
    
    detector = PaintDefectDetector()
    
    # 测试训练集中的图片
    train_dir = "dataset/train"
    test_results = []
    
    print("正在测试训练集图片...")
    for file in os.listdir(train_dir):
        if file.endswith('.png'):
            img_path = os.path.join(train_dir, file)
            base_name = os.path.splitext(file)[0]
            label_path = os.path.join(train_dir, f"{base_name}.txt")
            
            # 真实标签
            true_label = 1 if os.path.exists(label_path) and os.path.getsize(label_path) > 0 else 0
            
            # 预测
            result = detector.predict_single(img_path)
            if 'prediction' in result:
                pred_label = result['prediction']
                
                test_results.append({
                    'file': file,
                    'true_label': true_label,
                    'pred_label': pred_label,
                    'correct': true_label == pred_label
                })
    
    # 分析结果
    if test_results:
        total = len(test_results)
        correct = sum(1 for r in test_results if r['correct'])
        
        # 按类别统计
        defect_results = [r for r in test_results if r['true_label'] == 1]
        normal_results = [r for r in test_results if r['true_label'] == 0]
        
        defect_correct = sum(1 for r in defect_results if r['correct'])
        normal_correct = sum(1 for r in normal_results if r['correct'])
        
        print(f"\n=== 测试结果汇总 ===")
        print(f"总测试图片: {total}")
        print(f"总体准确率: {correct}/{total} = {correct/total:.3f}")
        
        if defect_results:
            print(f"缺陷检测: {defect_correct}/{len(defect_results)} = {defect_correct/len(defect_results):.3f}")
        if normal_results:
            print(f"正常检测: {normal_correct}/{len(normal_results)} = {normal_correct/len(normal_results):.3f}")
        
        # 显示错误案例
        wrong_predictions = [r for r in test_results if not r['correct']]
        if wrong_predictions:
            print(f"\n=== 错误预测案例 (前10个) ===")
            for i, result in enumerate(wrong_predictions[:10]):
                true_type = "缺陷" if result['true_label'] == 1 else "正常"
                pred_type = "缺陷" if result['pred_label'] == 1 else "正常"
                print(f"❌ {result['file']}: 真实={true_type}, 预测={pred_type}")
        
        # 显示正确案例
        correct_predictions = [r for r in test_results if r['correct']]
        if correct_predictions:
            print(f"\n=== 正确预测案例 (前5个) ===")
            for i, result in enumerate(correct_predictions[:5]):
                true_type = "缺陷" if result['true_label'] == 1 else "正常"
                print(f"✅ {result['file']}: {true_type}")

def test_single_image(image_path):
    """测试单张图片"""
    print(f"\n=== 单张图片测试: {os.path.basename(image_path)} ===")
    
    model_path = "model/svm_defect.xml"
    if not os.path.exists(model_path):
        print("❌ 模型文件不存在")
        return
    
    detector = PaintDefectDetector()
    
    # 预测
    result = detector.predict_single(image_path)
    if 'prediction' in result:
        print(f"预测结果: {'🔴 缺陷' if result['prediction'] == 1 else '🟢 正常'}")
        
        # 检查真实标签
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        label_path = os.path.join(os.path.dirname(image_path), f"{base_name}.txt")
        if os.path.exists(label_path):
            with open(label_path, 'r') as f:
                content = f.read().strip()
            true_label = 1 if content else 0
            print(f"真实标签: {'缺陷' if true_label == 1 else '正常'} (txt内容: '{content}')")
            print(f"{'✅' if result['prediction'] == true_label else '❌'} 预测{'正确' if result['prediction'] == true_label else '错误'}")
        else:
            print(f"真实标签: 正常 (无txt文件)")
            print(f"{'✅' if result['prediction'] == 0 else '❌'} 预测{'正确' if result['prediction'] == 0 else '错误'}")
        
        return result['prediction']
    else:
        print(f"❌ 预测失败: {result}")
        return None

def test_custom_images():
    """测试自定义图片"""
    print("\n=== 自定义图片测试 ===")
    
    # 创建测试目录
    test_dir = "test_images"
    os.makedirs(test_dir, exist_ok=True)
    
    # 检查是否有测试图片
    test_files = glob.glob(os.path.join(test_dir, "*.png")) + glob.glob(os.path.join(test_dir, "*.jpg"))
    
    if not test_files:
        print(f"请在 {test_dir} 目录中放置要测试的图片")
        print("支持的格式: PNG, JPG")
        return
    
    print(f"找到 {len(test_files)} 张测试图片")
    
    detector = PaintDefectDetector()
    
    for img_path in test_files:
        result = test_single_image(img_path)

if __name__ == "__main__":
    # 全面测试
    comprehensive_test()
    
    # 测试单张训练集图片
    sample_image = "dataset/train/0576.PNG"
    if os.path.exists(sample_image):
        test_single_image(sample_image)
    
    # 测试自定义图片
    test_custom_images()