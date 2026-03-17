#!/usr/bin/env python3
"""
Claude Code Usage Monitor - CLI Tool
命令行工具，快速查看 Claude Code 使用情况
"""

import sys
import os
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from telemetry_parser import TelemetryParser
import argparse


def print_header(text):
    """打印标题"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def print_stats(parser, hours=None):
    """打印统计信息"""
    events = parser.parse_telemetry_files(hours=hours)
    usage_data = parser.extract_usage_data(events)

    if not usage_data:
        print("❌ 没有找到使用数据")
        return

    # 总体统计
    stats = parser.get_total_stats(usage_data)

    print_header("📊 Claude Code 使用统计")

    time_desc = f"最近{hours}小时" if hours else "所有时间"
    print(f"📅 时间范围: {time_desc}")
    print(f"📝 总请求数: {stats['total_requests']:,}")
    print(f"💬 唯一会话: {stats['unique_sessions']}")
    print(f"\n📊 Tokens 使用:")
    print(f"  ├─ 输入 Tokens:  {stats['total_input_tokens']:,}")
    print(f"  ├─ 输出 Tokens:  {stats['total_output_tokens']:,}")
    print(f"  ├─ 缓存 Tokens:  {stats['total_cached_tokens']:,}")
    print(f"  └─ 总计:        {stats['total_tokens']:,}")
    print(f"\n💰 花费统计:")
    print(f"  ├─ 总花费:      ${stats['total_cost']:.4f}")
    print(f"  └─ 平均每次:    ${stats['avg_cost_per_request']:.6f}")

    # 模型分解
    model_breakdown = parser.get_model_breakdown(usage_data)
    print(f"\n🤖 模型使用分布:")
    for model, data in model_breakdown.items():
        model_short = model.split('-')[-1] if '-' in model else model
        print(f"\n  {model}")
        print(f"    ├─ 请求数:      {data['requests']:,}")
        print(f"    ├─ 输入 Tokens:  {data['input_tokens']:,}")
        print(f"    ├─ 输出 Tokens:  {data['output_tokens']:,}")
        print(f"    └─ 花费:        ${data['cost']:.4f}")

    # 按天聚合
    if hours is None or hours >= 48:
        daily = parser.aggregate_by_time_period(usage_data, 'day')
        recent_days = list(daily.items())[-7:]  # 最近7天

        if recent_days:
            print(f"\n📅 每日统计 (最近7天):")
            print(f"{'日期':<12} {'请求数':>8} {'花费':>12}")
            print("-" * 35)
            for date, data in recent_days:
                print(f"{date:<12} {data['request_count']:>8} ${data['total_cost']:>10.4f}")


def print_recent(parser, limit=10):
    """打印最近的请求"""
    events = parser.parse_telemetry_files(hours=24)
    usage_data = parser.extract_usage_data(events)

    if not usage_data:
        print("❌ 没有找到最近的请求数据")
        return

    usage_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    recent = usage_data[:limit]

    print_header(f"⏱️ 最近 {len(recent)} 条请求")

    print(f"{'时间':<20} {'模型':<20} {'输入':>10} {'输出':>10} {'花费':>10}")
    print("-" * 75)

    for item in recent:
        timestamp = item.get('timestamp', '')
        if timestamp:
            from datetime import datetime
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime('%m-%d %H:%M:%S')
        else:
            time_str = '--'

        model_short = item['model'].split('-')[-1] if '-' in item['model'] else item['model']

        print(f"{time_str:<20} {model_short:<20} "
              f"{item['input_tokens']:>10,} {item['output_tokens']:>10,} "
              f"${item['cost_usd']:>9.6f}")


def main():
    parser_arg = argparse.ArgumentParser(
        description='Claude Code Usage Monitor - 命令行工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                    # 查看所有时间的统计
  %(prog)s -t 24              # 查看最近24小时的统计
  %(prog)s -r                 # 查看最近的请求
  %(prog)s -r -n 20           # 查看最近20条请求
        """
    )

    parser_arg.add_argument(
        '-t', '--hours',
        type=int,
        help='只显示最近N小时的数据'
    )

    parser_arg.add_argument(
        '-r', '--recent',
        action='store_true',
        help='显示最近的请求记录'
    )

    parser_arg.add_argument(
        '-n', '--limit',
        type=int,
        default=10,
        help='显示的最近请求数量 (默认: 10)'
    )

    args = parser_arg.parse_args()

    try:
        parser = TelemetryParser()

        if args.recent:
            print_recent(parser, limit=args.limit)
        else:
            print_stats(parser, hours=args.hours)

        print()  # 空行

    except FileNotFoundError as e:
        print(f"❌ 错误: {e}")
        print("\n请确保 Claude Code 已安装并运行过至少一次。")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
