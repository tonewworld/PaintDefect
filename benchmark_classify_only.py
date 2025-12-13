import argparse
import json
import os
import threading
import time
import queue
import requests

# 使用本地提取的特征并发 POST /classify，评估 classify_only 模式吞吐与延迟
# 示例：
#   python benchmark_classify_only.py --server http://127.0.0.1:5000 --images dataset/train --concurrency 1 5 10 --duration 30 --limit 50 --out classify_only_conc.json

def load_image_paths(path, limit=50):
    imgs = []
    for root, _, files in os.walk(path):
        for fn in files:
            if fn.lower().endswith(('.png','.jpg','.jpeg')):
                imgs.append(os.path.join(root, fn))
                if len(imgs) >= limit:
                    return imgs
    return imgs

def extract_features_batch_py(image_paths):
    # 直接调用项目的 Python 推理模块进行特征提取，避免重复实现
    # 仅用于离线准备特征，不依赖服务器
    from inference import PaintDefectDetector
    det = PaintDefectDetector("model/svm_defect.xml")
    feats = []
    names = []
    for p in image_paths:
        gray, mask = det.enhanced_preprocess(p)
        if gray is None:
            continue
        f = det.extract_robust_features(gray, mask)
        feats.append(f.tolist())
        names.append(os.path.basename(p))
    return names, feats

def worker(stop_event, server, names, features, results_q):
    idx = 0
    url = server.rstrip('/') + '/classify'
    while not stop_event.is_set():
        i = idx % len(features)
        idx += 1
        payload = {"features": features[i], "name": names[i]}
        try:
            start = time.perf_counter()
            r = requests.post(url, json=payload, timeout=30)
            end = time.perf_counter()
            ok = (r.status_code == 200)
            results_q.put(((end - start) * 1000, ok))
        except Exception:
            results_q.put((None, False))

def percentile(sorted_list, p):
    if not sorted_list:
        return None
    idx = int(p/100 * (len(sorted_list)-1))
    return sorted_list[idx]

def summarize(latencies):
    if not latencies:
        return {}
    s = sorted(latencies)
    import statistics
    return {
        'count': len(s),
        'avg_ms': statistics.mean(s),
        'median_ms': statistics.median(s),
        'p90_ms': percentile(s, 90),
        'p99_ms': percentile(s, 99),
        'min_ms': s[0],
        'max_ms': s[-1]
    }

def run_once(conc, duration, server, names, features):
    stop_event = threading.Event()
    q = queue.Queue()
    threads = []
    for _ in range(conc):
        t = threading.Thread(target=worker, args=(stop_event, server, names, features, q))
        t.start()
        threads.append(t)
    start = time.time()
    while time.time() - start < duration:
        time.sleep(0.5)
    stop_event.set()
    for t in threads:
        t.join()
    succ = 0
    fail = 0
    lat = []
    while not q.empty():
        l, ok = q.get()
        if ok and l is not None:
            succ += 1
            lat.append(l)
        else:
            fail += 1
    elapsed = time.time() - start
    rps = succ / elapsed if elapsed > 0 else 0
    return {
        'concurrency': conc,
        'duration_s': duration,
        'mode': 'classify_only',
        'success': succ,
        'fail': fail,
        'rps': rps,
        'latency_stats': summarize(lat)
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--server', required=True)
    ap.add_argument('--images', required=True)
    ap.add_argument('--concurrency', nargs='+', type=int, default=[1,5,10])
    ap.add_argument('--duration', type=int, default=30)
    ap.add_argument('--limit', type=int, default=50, help='最大图片数用于生成特征集')
    ap.add_argument('--out', default='classify_only_conc.json')
    args = ap.parse_args()

    image_paths = load_image_paths(args.images, args.limit)
    if not image_paths:
        print('No images found.')
        return
    print(f'Preparing features from {len(image_paths)} images ...')
    names, feats = extract_features_batch_py(image_paths)
    if not feats:
        print('No features extracted.')
        return

    all_results = []
    for c in args.concurrency:
        print(f'Running classify_only concurrency={c} duration={args.duration}s ...')
        res = run_once(c, args.duration, args.server, names, feats)
        print(res)
        all_results.append(res)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print('Saved:', args.out)

if __name__ == '__main__':
    main()