import argparse
import json
import os
import matplotlib.pyplot as plt

"""
汇总并发压测结果：输入一个或多个 JSON（benchmark_concurrent.py / benchmark_classify_only.py 输出），
生成 CSV 对比表和两张图：RPS vs 并发、P90 延迟 vs 并发。

示例：
  python summarize_concurrency.py --files full_remote_conc.json classify_only_conc.json --outdir output/conc
"""


def load_results(paths):
    datasets = []
    for p in paths:
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # data: list of {concurrency, rps, latency_stats{p90_ms,...}, mode}
        if isinstance(data, dict):
            data = [data]
        # 推断数据集名
        label = os.path.splitext(os.path.basename(p))[0]
        mode = None
        rows = []
        for row in data:
            mode = row.get('mode', mode)
            rows.append({
                'concurrency': row.get('concurrency'),
                'rps': row.get('rps'),
                'avg_ms': (row.get('latency_stats') or {}).get('avg_ms'),
                'p90_ms': (row.get('latency_stats') or {}).get('p90_ms'),
                'p99_ms': (row.get('latency_stats') or {}).get('p99_ms'),
            })
        datasets.append({'label': f"{mode or label}", 'rows': rows})
    return datasets


def write_csv(datasets, out_csv):
    with open(out_csv, 'w', encoding='utf-8') as f:
        f.write('dataset,concurrency,rps,avg_ms,p90_ms,p99_ms\n')
        for ds in datasets:
            for r in ds['rows']:
                f.write(f"{ds['label']},{r['concurrency']},{r['rps']},{r['avg_ms']},{r['p90_ms']},{r['p99_ms']}\n")


def plot(datasets, outdir):
    os.makedirs(outdir, exist_ok=True)
    # RPS vs 并发
    plt.figure(figsize=(8,5))
    for ds in datasets:
        xs = [r['concurrency'] for r in ds['rows']]
        ys = [r['rps'] for r in ds['rows']]
        plt.plot(xs, ys, marker='o', label=ds['label'])
    plt.xlabel('Concurrency')
    plt.ylabel('RPS')
    plt.title('Throughput vs Concurrency')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, 'rps_vs_concurrency.png'))
    plt.close()

    # P90 vs 并发
    plt.figure(figsize=(8,5))
    for ds in datasets:
        xs = [r['concurrency'] for r in ds['rows']]
        ys = [r['p90_ms'] for r in ds['rows']]
        plt.plot(xs, ys, marker='o', label=ds['label'])
    plt.xlabel('Concurrency')
    plt.ylabel('P90 Latency (ms)')
    plt.title('P90 Latency vs Concurrency')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, 'p90_vs_concurrency.png'))
    plt.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--files', nargs='+', required=True, help='并发结果 JSON 列表')
    ap.add_argument('--outdir', default='output/conc')
    ap.add_argument('--csv', default='conc_summary.csv')
    args = ap.parse_args()

    datasets = load_results(args.files)
    os.makedirs(args.outdir, exist_ok=True)
    out_csv = os.path.join(args.outdir, args.csv)
    write_csv(datasets, out_csv)
    plot(datasets, args.outdir)
    print('Wrote CSV:', out_csv)
    print('Saved figures: rps_vs_concurrency.png, p90_vs_concurrency.png in', args.outdir)


if __name__ == '__main__':
    main()