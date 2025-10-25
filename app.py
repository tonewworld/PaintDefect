# app.py
from flask import Flask, render_template, request, jsonify
import os
from inference import PaintDefectDetector

app = Flask(__name__)

# 初始化检测器
try:
    detector = PaintDefectDetector("model/svm_defect.xml")
    print("✅ 模型加载成功")
except Exception as e:
    print(f"❌ 模型加载失败: {e}")
    detector = None

# 创建必要的目录
os.makedirs('static/uploads', exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if detector is None:
        return jsonify({'error': '模型未加载，请先训练模型'})
    
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'})
    
    if file:
        # 保存上传的图片
        filename = file.filename
        upload_path = os.path.join('static/uploads', filename)
        file.save(upload_path)
        
        try:
            # 进行预测
            result = detector.predict_single(upload_path)
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': f'预测失败: {str(e)}'})

if __name__ == '__main__':
    print("漆面缺陷检测系统启动中...")
    print("访问 http://127.0.0.1:5000 使用系统")
    app.run(debug=True, host='127.0.0.1', port=5000)