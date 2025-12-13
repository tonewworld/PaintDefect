import json
import argparse
import os
import matplotlib.pyplot as plt

"""将 analyze_mobile_logs.py 的 summary.json 或原始 mobile_perf_logs.json 转换为图表.
示例:
    python visualize_logs.py --summary summary.json --outdir output/figs
输出:
  - bar_end_to_end.png : 各分组平均端到端耗时条形图
  - stacked_time_breakdown.png : 客户端 vs 服务器平均耗时堆叠
  - network_vs_upload.png : 上传大小 vs 网络耗时散点
"""

def load_summary(path):
    with open(path,'r',encoding='utf-8') as f:
        return json.load(f)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--summary', required=True, help='summary.json 文件')
    ap.add_argument('--outdir', default='output/figs')
    args = ap.parse_args()

    data = load_summary(args.summary)
    os.makedirs(args.outdir, exist_ok=True)

    groups = []
    for k,v in data.items():
        end_stats = v.get('end_to_end_stats',{})
        client_stats = v.get('client_total_stats',{})
        server_stats = v.get('server_total_stats',{})
        groups.append({
            'key': k,
            'mode': v.get('mode'),
            'resize': v.get('resize_target'),
            'network': v.get('network_type'),
            'end_avg': end_stats.get('avg',0),
            'client_avg': client_stats.get('avg',0),
            'server_avg': server_stats.get('avg',0),
            'samples': v.get('samples',0)
        })

    if not groups:
        print('No groups to visualize.')
        return

    # 条形图: 分组(模式|尺寸) vs end_avg
    labels = [g['key'] for g in groups]
    end_values = [g['end_avg'] for g in groups]
    plt.figure(figsize=(max(10,len(labels)*0.6),6))
    plt.bar(labels, end_values, color='steelblue')
    plt.xticks(rotation=60, ha='right')
    plt.ylabel('Avg End-to-End (ms)')
    plt.title('Average End-to-End Latency by Group')
    plt.tight_layout()
    plt.savefig(os.path.join(args.outdir,'bar_end_to_end.png'))
    plt.close()

    # 堆叠图: 客户端 vs 服务器耗时
    plt.figure(figsize=(max(10,len(labels)*0.6),6))
    client_vals = [g['client_avg'] for g in groups]
    server_vals = [g['server_avg'] for g in groups]
    plt.bar(labels, client_vals, label='Client', color='#8ecae6')
    plt.bar(labels, server_vals, bottom=client_vals, label='Server', color='#ffb703')
    plt.xticks(rotation=60, ha='right')
    plt.ylabel('Avg Latency (ms)')
    plt.title('Client vs Server Average Latency (Stacked)')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(args.outdir,'stacked_time_breakdown.png'))
    plt.close()

    # 散点图: 上传大小 vs 网络耗时 (需要原始日志另处理; 这里使用 summary 无法提供)
    # 若扩展: 可以允许传原始日志文件; 暂留占位说明.
    print('Created figures: bar_end_to_end.png, stacked_time_breakdown.png')

if __name__ == '__main__':
    main()