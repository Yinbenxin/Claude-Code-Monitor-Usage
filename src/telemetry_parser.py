"""
Claude Code Telemetry Parser
解析 Claude Code 的遥测数据并提取使用情况信息
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict


class TelemetryParser:
    """解析 Claude Code telemetry 数据"""

    def __init__(self, claude_dir: Optional[str] = None):
        """
        初始化解析器

        Args:
            claude_dir: Claude 配置目录路径，默认为 ~/.claude
        """
        if claude_dir is None:
            claude_dir = os.path.expanduser("~/.claude")

        self.claude_dir = Path(claude_dir)
        self.telemetry_dir = self.claude_dir / "telemetry"

        if not self.telemetry_dir.exists():
            raise FileNotFoundError(f"Telemetry directory not found: {self.telemetry_dir}")

    def parse_telemetry_files(self, hours: Optional[int] = None) -> List[Dict]:
        """
        解析所有遥测文件

        Args:
            hours: 只返回最近N小时的数据，None表示所有数据

        Returns:
            包含所有事件的列表
        """
        events = []
        cutoff_time = None

        if hours:
            cutoff_time = datetime.now() - timedelta(hours=hours)

        # 遍历所有JSON文件
        for file_path in self.telemetry_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                # 文件是JSONL格式（每行一个JSON对象）
                for line in content.strip().split('\n'):
                    if not line.strip():
                        continue

                    try:
                        event = json.loads(line)

                        # 提取时间戳并过滤
                        if cutoff_time:
                            timestamp_str = event.get('event_data', {}).get('client_timestamp')
                            if timestamp_str:
                                event_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                                if event_time.replace(tzinfo=None) < cutoff_time:
                                    continue

                        events.append(event)
                    except json.JSONDecodeError:
                        continue

            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue

        return events

    def extract_usage_data(self, events: List[Dict]) -> List[Dict]:
        """
        从事件中提取使用数据

        Returns:
            使用数据列表，每个包含 tokens, cost, model 等信息
        """
        usage_data = []

        for event in events:
            event_data = event.get('event_data', {})
            event_name = event_data.get('event_name')

            # 只处理 API 成功事件
            if event_name != 'tengu_api_success':
                continue

            metadata_str = event_data.get('additional_metadata', '{}')
            try:
                metadata = json.loads(metadata_str)
            except json.JSONDecodeError:
                continue

            # 提取使用信息
            usage_info = {
                'timestamp': event_data.get('client_timestamp'),
                'model': event_data.get('model', 'unknown'),
                'session_id': event_data.get('session_id'),
                'input_tokens': metadata.get('inputTokens', 0),
                'output_tokens': metadata.get('outputTokens', 0),
                'cached_input_tokens': metadata.get('cachedInputTokens', 0),
                'uncached_input_tokens': metadata.get('uncachedInputTokens', 0),
                'cost_usd': metadata.get('costUSD', 0.0),
                'duration_ms': metadata.get('durationMs', 0),
                'stop_reason': metadata.get('stop_reason', 'unknown'),
                'message_count': metadata.get('messageCount', 0),
            }

            usage_data.append(usage_info)

        return usage_data

    def aggregate_by_time_period(self, usage_data: List[Dict], period: str = 'day') -> Dict:
        """
        按时间段聚合数据

        Args:
            usage_data: 使用数据列表
            period: 'hour', 'day', 'week', 'month'

        Returns:
            聚合后的数据字典
        """
        aggregated = defaultdict(lambda: {
            'input_tokens': 0,
            'output_tokens': 0,
            'cached_input_tokens': 0,
            'total_cost': 0.0,
            'request_count': 0,
            'models': set()
        })

        for item in usage_data:
            timestamp_str = item.get('timestamp')
            if not timestamp_str:
                continue

            try:
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                dt = dt.replace(tzinfo=None)

                # 根据周期确定key
                if period == 'hour':
                    key = dt.strftime('%Y-%m-%d %H:00')
                elif period == 'day':
                    key = dt.strftime('%Y-%m-%d')
                elif period == 'week':
                    key = f"{dt.year}-W{dt.isocalendar()[1]:02d}"
                elif period == 'month':
                    key = dt.strftime('%Y-%m')
                else:
                    key = dt.strftime('%Y-%m-%d')

                # 聚合数据
                aggregated[key]['input_tokens'] += item['input_tokens']
                aggregated[key]['output_tokens'] += item['output_tokens']
                aggregated[key]['cached_input_tokens'] += item['cached_input_tokens']
                aggregated[key]['total_cost'] += item['cost_usd']
                aggregated[key]['request_count'] += 1
                aggregated[key]['models'].add(item['model'])

            except Exception as e:
                continue

        # 转换 sets 为 lists 以便 JSON 序列化
        result = {}
        for key, value in aggregated.items():
            value['models'] = list(value['models'])
            result[key] = value

        return dict(sorted(result.items()))

    def get_total_stats(self, usage_data: List[Dict]) -> Dict:
        """
        获取总体统计信息

        Returns:
            总体统计字典
        """
        if not usage_data:
            return {
                'total_input_tokens': 0,
                'total_output_tokens': 0,
                'total_cached_tokens': 0,
                'total_cost': 0.0,
                'total_requests': 0,
                'unique_sessions': 0,
                'models_used': []
            }

        total_input = sum(item['input_tokens'] for item in usage_data)
        total_output = sum(item['output_tokens'] for item in usage_data)
        total_cached = sum(item['cached_input_tokens'] for item in usage_data)
        total_cost = sum(item['cost_usd'] for item in usage_data)
        unique_sessions = len(set(item['session_id'] for item in usage_data if item.get('session_id')))
        models = list(set(item['model'] for item in usage_data))

        return {
            'total_input_tokens': total_input,
            'total_output_tokens': total_output,
            'total_cached_tokens': total_cached,
            'total_tokens': total_input + total_output,
            'total_cost': round(total_cost, 4),
            'total_requests': len(usage_data),
            'unique_sessions': unique_sessions,
            'models_used': models,
            'avg_cost_per_request': round(total_cost / len(usage_data), 6) if usage_data else 0
        }

    def get_model_breakdown(self, usage_data: List[Dict]) -> Dict[str, Dict]:
        """
        按模型分解统计

        Returns:
            每个模型的统计信息
        """
        model_stats = defaultdict(lambda: {
            'input_tokens': 0,
            'output_tokens': 0,
            'cached_tokens': 0,
            'cost': 0.0,
            'requests': 0
        })

        for item in usage_data:
            model = item['model']
            model_stats[model]['input_tokens'] += item['input_tokens']
            model_stats[model]['output_tokens'] += item['output_tokens']
            model_stats[model]['cached_tokens'] += item['cached_input_tokens']
            model_stats[model]['cost'] += item['cost_usd']
            model_stats[model]['requests'] += 1

        # 四舍五入 cost
        for model in model_stats:
            model_stats[model]['cost'] = round(model_stats[model]['cost'], 4)

        return dict(model_stats)


if __name__ == '__main__':
    # 测试代码
    parser = TelemetryParser()

    print("📊 Claude Code Usage Monitor - Test")
    print("=" * 60)

    # 获取最近24小时的数据
    events = parser.parse_telemetry_files(hours=24)
    print(f"\n✓ 找到 {len(events)} 个事件（最近24小时）")

    # 提取使用数据
    usage_data = parser.extract_usage_data(events)
    print(f"✓ 提取 {len(usage_data)} 条使用记录")

    # 总体统计
    stats = parser.get_total_stats(usage_data)
    print(f"\n📈 总体统计:")
    print(f"  - 总请求数: {stats['total_requests']}")
    print(f"  - 总输入tokens: {stats['total_input_tokens']:,}")
    print(f"  - 总输出tokens: {stats['total_output_tokens']:,}")
    print(f"  - 缓存tokens: {stats['total_cached_tokens']:,}")
    print(f"  - 总花费: ${stats['total_cost']:.4f}")
    print(f"  - 平均每次请求: ${stats['avg_cost_per_request']:.6f}")

    # 模型分解
    model_breakdown = parser.get_model_breakdown(usage_data)
    print(f"\n🤖 按模型统计:")
    for model, data in model_breakdown.items():
        print(f"  {model}:")
        print(f"    - 请求数: {data['requests']}")
        print(f"    - 花费: ${data['cost']:.4f}")

    # 按天聚合
    daily = parser.aggregate_by_time_period(usage_data, 'day')
    print(f"\n📅 每日统计:")
    for date, data in list(daily.items())[-7:]:  # 最近7天
        print(f"  {date}: ${data['total_cost']:.4f} ({data['request_count']} 次请求)")
