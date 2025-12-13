import json
import argparse
import statistics
import os
from collections import defaultdict

"""分析前端导出的 mobile_perf_logs.json 日志文件，生成统计结果。
使用:
    python analyze_mobile_logs.py --input mobile_perf_logs.json --out summary.json --csv summary.csv
分组维度: 模式(mode)、压缩目标(resize_target)、网络类型(effectiveType)
统计字段: client_total_ms, server_total_ms(或predict_ms), end_to_end_ms, network_ms
"""

def p90(values):
    if not values:
        return None
    idx = int(0.9 * (len(values) - 1))
    return sorted(values)[idx]

def stats(values):
    if not values:
        return {}
    return {
        'count': len(values),
        'avg': statistics.mean(values),
        'median': statistics.median(values),
        'p90': p90(values),
        'min': min(values),
        'max': max(values),
        'std': statistics.pstdev(values) if len(values) > 1 else 0.0
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--out', default='summary.json')
    ap.add_argument('--csv', default='summary.csv')
    args = ap.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        logs = json.load(f)
    if not isinstance(logs, list):
        raise ValueError('日志文件格式错误，需为数组')

    groups = defaultdict(list)
    for entry in logs:
        mode = entry.get('mode', 'unknown')
        resize_target = entry.get('client_meta', {}).get('resize_target', 'none')
        net_type = entry.get('network_info', {}).get('effectiveType', 'unknown')
        key = (mode, resize_target, net_type)
        groups[key].append(entry)

    summary = {}
    rows = []
    for (mode, resize_target, net_type), entries in groups.items():
        client_total = []
        server_total = []
        network_ms = []
        end_to_end = []
        for e in entries:
            ct = e.get('client_timing', {})
            st = e.get('server_timing', {})
            client_ms = ct.get('total_client_ms')
            # server total 取 total_ms 或 predict_ms
            server_ms = st.get('total_ms', st.get('predict_ms'))
            net = ct.get('network_ms')
            if client_ms is not None:
                client_total.append(client_ms)
            if server_ms is not None:
                server_total.append(server_ms)
            if client_ms is not None and server_ms is not None:
                end_to_end.append(client_ms + server_ms)
            if net is not None:
                network_ms.append(net)

        summary_key = f"{mode}|{resize_target}|{net_type}"
        summary[summary_key] = {
            'mode': mode,
            'resize_target': resize_target,
            'network_type': net_type,
            'samples': len(entries),
            'client_total_stats': stats(client_total),
            'server_total_stats': stats(server_total),
            'network_ms_stats': stats(network_ms),
            'end_to_end_stats': stats(end_to_end)
        }
        rows.append([
            mode,
            resize_target,
            net_type,
            len(entries),
            summary[summary_key]['client_total_stats'].get('avg'),
            summary[summary_key]['server_total_stats'].get('avg'),
            summary[summary_key]['end_to_end_stats'].get('avg'),
            summary[summary_key]['end_to_end_stats'].get('p90')
        ])

    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"写入统计 JSON: {args.out}")

    # 写 CSV
    with open(args.csv, 'w', encoding='utf-8') as f:
        f.write('mode,resize_target,network_type,samples,avg_client_ms,avg_server_ms,avg_end_to_end_ms,p90_end_to_end_ms\n')
        for r in rows:
            f.write(','.join(str(x) for x in r) + '\n')
    print(f"写入统计 CSV: {args.csv}")

if __name__ == '__main__':
    main()