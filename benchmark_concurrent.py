import argparse
import time
import os
import threading
import queue
import requests
import statistics

"""并发基准脚本
测量不同并发度下的吞吐量、平均/分位延迟，支持模式选择与图片目录。

示例:
  python benchmark_concurrent.py --server http://127.0.0.1:5000 --images dataset/train \
      --concurrency 5 10 --duration 30 --mode full_remote --resize none

输出: 每个并发度下的统计 (成功请求数、失败数、RPS、平均延迟、P50/P90/P99)。
"""

def load_images(path, limit=50):
    imgs = []
    for root, _, files in os.walk(path):
        for fn in files:
            if fn.lower().endswith(('.png','.jpg','.jpeg')):
                imgs.append(os.path.join(root, fn))
                if len(imgs) >= limit:
                    return imgs
    return imgs

def worker(stop_event, server, mode, resize, images, results_q):
    idx = 0
    while not stop_event.is_set():
        img_path = images[idx % len(images)]
        idx += 1
        try:
            with open(img_path, 'rb') as f:
                files = {'file': (os.path.basename(img_path), f, 'image/jpeg')}
                data = {'mode': mode}
                start = time.perf_counter()
                resp = requests.post(server.rstrip('/') + '/predict', files=files, data=data, timeout=30)
                end = time.perf_counter()
            latency = (end - start) * 1000
            ok = resp.status_code == 200
            results_q.put((latency, ok))
        except Exception:
            results_q.put((None, False))

def stats(latencies):
    if not latencies:
        return {}
    sl = sorted(latencies)
    def pct(p):
        if not sl: return None
        idx = int(p/100 * (len(sl)-1))
        return sl[idx]
    return {
        'count': len(sl),
        'avg_ms': statistics.mean(sl),
        'median_ms': statistics.median(sl),
        'p90_ms': pct(90),
        'p99_ms': pct(99),
        'min_ms': sl[0],
        'max_ms': sl[-1]
    }

def run_test(conc, duration, server, mode, resize, images):
    stop_event = threading.Event()
    results_q = queue.Queue()
    threads = []
    for _ in range(conc):
        t = threading.Thread(target=worker, args=(stop_event, server, mode, resize, images, results_q))
        t.start()
        threads.append(t)
    start = time.time()
    while time.time() - start < duration:
        time.sleep(0.5)
    stop_event.set()
    for t in threads:
        t.join()
    latencies = []
    success = 0
    fail = 0
    while not results_q.empty():
        latency, ok = results_q.get()
        if ok and latency is not None:
            latencies.append(latency)
            success += 1
        else:
            fail += 1
    elapsed = time.time() - start
    stat = stats(latencies)
    rps = success / elapsed if elapsed > 0 else 0
    return {
        'concurrency': conc,
        'duration_s': duration,
        'mode': mode,
        'resize': resize,
        'success': success,
        'fail': fail,
        'rps': rps,
        'latency_stats': stat
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--server', required=True)
    ap.add_argument('--images', required=True)
    ap.add_argument('--mode', default='full_remote')
    ap.add_argument('--resize', default='none')
    ap.add_argument('--concurrency', nargs='+', type=int, default=[1,5,10])
    ap.add_argument('--duration', type=int, default=20)
    ap.add_argument('--limit', type=int, default=20)
    ap.add_argument('--out', default='concurrent_results.json')
    args = ap.parse_args()

    images = load_images(args.images, limit=args.limit)
    if not images:
        print('No images found.')
        return

    import json
    all_results = []
    for c in args.concurrency:
        print(f'Running concurrency={c} duration={args.duration}s ...')
        res = run_test(c, args.duration, args.server, args.mode, args.resize, images)
        all_results.append(res)
        print(res)
    with open(args.out,'w',encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print('Saved:', args.out)

if __name__ == '__main__':
    main()