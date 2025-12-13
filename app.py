# app.py
from flask import Flask, render_template, request, jsonify
import os
import psutil
from inference import PaintDefectDetector
import time
from collections import deque

app = Flask(__name__)

# 初始化检测器
try:
    detector = PaintDefectDetector("model/svm_defect.xml")
    print("✅ 模型加载成功")
except Exception as e:
    print(f"❌ 模型加载失败: {e}")
    detector = None

# 用于自动策略的历史窗口
recent_server_total = deque(maxlen=50)
recent_file_sizes = deque(maxlen=50)

# 创建必要的目录
os.makedirs('static/uploads', exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if detector is None:
        return jsonify({'error': '模型未加载，请先训练模型'})

    mode = request.form.get('mode', 'full_remote')  # full_remote | classify_only | auto

    advisory = {}
    if mode == 'auto':
        cpu = psutil.cpu_percent(interval=0.05)
        file_size = int(request.headers.get('Content-Length', 0))
        recent_file_sizes.append(file_size)
        avg_file = sum(recent_file_sizes)/len(recent_file_sizes) if recent_file_sizes else file_size
        avg_server = sum(recent_server_total)/len(recent_server_total) if recent_server_total else 0
        # 规则：如果平均文件 > 600KB 且 CPU > 70 或 服务器总耗时均值 > 250ms 则建议 classify_only
        if ((avg_file > 600_000 and cpu > 55) or (avg_server > 250)):
            advisory['recommended_mode'] = 'classify_only'
            advisory['reason'] = f"avg_file={avg_file:.0f}, cpu={cpu:.1f}, avg_server={avg_server:.1f}"
            # 暂不强制修改执行模式，仍做 full_remote，客户端可根据 recommended_mode 决定是否改走特征路径
            mode = 'full_remote'
        else:
            advisory['recommended_mode'] = 'full_remote'
            advisory['reason'] = f"avg_file={avg_file:.0f}, cpu={cpu:.1f}, avg_server={avg_server:.1f}"

    if mode in ('full_remote'):
        if 'file' not in request.files:
            return jsonify({'error': '没有选择文件'})
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'})
        filename = file.filename
        upload_path = os.path.join('static/uploads', filename)
        file.save(upload_path)
        try:
            start = time.perf_counter()
            result = detector.predict_single(upload_path, with_timing=True)
            end = time.perf_counter()
            result['mode'] = mode
            result['timing']['endpoint_ms'] = (end - start) * 1000
            # 记录总耗时用于 auto 策略
            recent_server_total.append(result['timing'].get('total_ms', result['timing'].get('predict_ms', 0)))
            if advisory:
                result['advisory'] = advisory
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': f'预测失败: {str(e)}', 'mode': mode, 'advisory': advisory})
    elif mode == 'classify_only':
        # 接收客户端已经提取的特征
        data = request.get_json(silent=True)
        if not data or 'features' not in data:
            return jsonify({'error': '需要提供 features 数组', 'mode': mode})
        feats = data['features']
        try:
            start = time.perf_counter()
            result = detector.classify_features(feats)
            end = time.perf_counter()
            result['mode'] = mode
            result['timing'] = {'predict_ms': (end - start) * 1000}
            recent_server_total.append(result['timing']['predict_ms'])
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': f'分类失败: {str(e)}', 'mode': mode})
    else:
        return jsonify({'error': f'不支持的模式: {mode}'})
@app.route('/decision', methods=['POST'])
def decision():
    """根据元数据（文件大小、客户端阶段耗时等）返回建议模式"""
    data = request.get_json(silent=True) or {}
    file_size = data.get('file_size', 0)
    cpu = psutil.cpu_percent(interval=0.05)
    avg_server = sum(recent_server_total)/len(recent_server_total) if recent_server_total else 0
    avg_file = sum(recent_file_sizes)/len(recent_file_sizes) if recent_file_sizes else file_size
    if ((avg_file > 600_000 and cpu > 55) or (avg_server > 250)):
        rec = 'classify_only'
    else:
        rec = 'full_remote'
    return jsonify({
        'recommended_mode': rec,
        'cpu': cpu,
        'avg_server_ms': avg_server,
        'avg_file_size': avg_file,
        'window_lengths': {'server': len(recent_server_total), 'file': len(recent_file_sizes)}
    })

@app.route('/classify', methods=['POST'])
def classify_only():
    """备用端点: 仅分类特征"""
    if detector is None:
        return jsonify({'error': '模型未加载'})
    data = request.get_json(silent=True)
    if not data or 'features' not in data:
        return jsonify({'error': '需要提供 features 数组'})
    feats = data['features']
    try:
        start = time.perf_counter()
        result = detector.classify_features(feats)
        end = time.perf_counter()
        result['timing'] = {'predict_ms': (end - start) * 1000}
        result['mode'] = 'classify_only'
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'分类失败: {str(e)}'})

if __name__ == '__main__':
    print("漆面缺陷检测系统启动中...")
    print("访问 http://<本机局域网IP>:5000 使用系统 (例如 http://192.168.1.10:5000)")
    # 监听 0.0.0.0 以便同一局域网手机访问
    app.run(debug=True, host='0.0.0.0', port=5000)