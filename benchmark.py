import argparse
import time
import os
import json
import statistics
import requests

"""简单基准脚本: 发送图片到服务端不同模式, 收集时延
用法示例:
    python benchmark.py --server http://127.0.0.1:5000 --images dataset/train --modes full_remote auto --repeat 3
输出: 每模式下统计的平均/中位/最大/最小总耗时(ms)
"""

def send_image(server_url, image_path, mode):
    with open(image_path, 'rb') as f:
        files = {'file': (os.path.basename(image_path), f, 'image/jpeg')}
        data = {'mode': mode}
        start = time.perf_counter()
        resp = requests.post(server_url.rstrip('/') + '/predict', files=files, data=data, timeout=60)
        end = time.perf_counter()
    latency_ms = (end - start) * 1000
    try:
        j = resp.json()
    except Exception:
        j = {'error': 'invalid json'}
    return latency_ms, j

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', default='http://127.0.0.1:5000')
    parser.add_argument('--images', required=True, help='图片目录')
    parser.add_argument('--modes', nargs='+', default=['full_remote', 'auto'])
    parser.add_argument('--repeat', type=int, default=3)
    parser.add_argument('--limit', type=int, default=10, help='最多使用的图片数量')
    parser.add_argument('--ext', nargs='+', default=['.png', '.jpg', '.jpeg'])
    args = parser.parse_args()

    # 收集图片
    image_files = []
    for root, _, files in os.walk(args.images):
        for fn in files:
            if any(fn.lower().endswith(e) for e in args.ext):
                image_files.append(os.path.join(root, fn))
            if len(image_files) >= args.limit:
                break
        if len(image_files) >= args.limit:
            break

    if not image_files:
        print('未找到图片')
        return

    results = {}
    for mode in args.modes:
        latencies = []
        stage_samples = []
        print(f'模式: {mode}')
        for img in image_files:
            for _ in range(args.repeat):
                l, payload = send_image(args.server, img, mode)
                latencies.append(l)
                timing = payload.get('timing') if isinstance(payload, dict) else None
                if timing:
                    stage_samples.append(timing.get('total_ms', timing.get('predict_ms', l)))
                print(f'  {os.path.basename(img)} -> {l:.2f} ms' + (' (total stage: {:.2f} ms)'.format(stage_samples[-1]) if stage_samples else ''))
        if latencies:
            results[mode] = {
                'count': len(latencies),
                'avg_ms': statistics.mean(latencies),
                'median_ms': statistics.median(latencies),
                'min_ms': min(latencies),
                'max_ms': max(latencies)
            }

    print('\n=== 汇总 ===')
    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()