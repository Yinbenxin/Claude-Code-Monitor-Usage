"""
Claude Code Usage Monitor - Flask Web Application
实时监控 Claude Code 的使用情况和花销
"""

from flask import Flask, render_template, jsonify, request
from pathlib import Path
import os
import sys
import json
from datetime import datetime, timedelta

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from telemetry_parser import TelemetryParser

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# 全局配置
BUDGET_FILE = Path(__file__).parent / 'data' / 'budget.json'
BUDGET_FILE.parent.mkdir(exist_ok=True)


def load_budget_config():
    """加载预算配置"""
    if BUDGET_FILE.exists():
        with open(BUDGET_FILE, 'r') as f:
            return json.load(f)
    return {
        'daily_limit': 10.0,
        'weekly_limit': 50.0,
        'monthly_limit': 200.0,
        'alert_threshold': 0.8  # 80% 时发出警告
    }


def save_budget_config(config):
    """保存预算配置"""
    with open(BUDGET_FILE, 'w') as f:
        json.dump(config, f, indent=2)


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/stats/total')
def api_stats_total():
    """获取总体统计信息"""
    try:
        parser = TelemetryParser()

        # 获取时间范围参数
        hours = request.args.get('hours', type=int)

        events = parser.parse_telemetry_files(hours=hours)
        usage_data = parser.extract_usage_data(events)
        stats = parser.get_total_stats(usage_data)

        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats/models')
def api_stats_models():
    """获取按模型分解的统计"""
    try:
        parser = TelemetryParser()

        hours = request.args.get('hours', type=int)

        events = parser.parse_telemetry_files(hours=hours)
        usage_data = parser.extract_usage_data(events)
        model_breakdown = parser.get_model_breakdown(usage_data)

        return jsonify({
            'success': True,
            'data': model_breakdown
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats/timeline')
def api_stats_timeline():
    """获取时间线统计"""
    try:
        parser = TelemetryParser()

        hours = request.args.get('hours', type=int)
        period = request.args.get('period', 'day')  # hour, day, week, month

        events = parser.parse_telemetry_files(hours=hours)
        usage_data = parser.extract_usage_data(events)
        timeline = parser.aggregate_by_time_period(usage_data, period)

        return jsonify({
            'success': True,
            'data': timeline
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats/recent')
def api_stats_recent():
    """获取最近的请求记录"""
    try:
        parser = TelemetryParser()

        limit = request.args.get('limit', 20, type=int)
        hours = request.args.get('hours', 24, type=int)

        events = parser.parse_telemetry_files(hours=hours)
        usage_data = parser.extract_usage_data(events)

        # 按时间排序并限制数量
        usage_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        recent = usage_data[:limit]

        return jsonify({
            'success': True,
            'data': recent
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/budget', methods=['GET', 'POST'])
def api_budget():
    """预算配置API"""
    if request.method == 'GET':
        try:
            config = load_budget_config()
            return jsonify({
                'success': True,
                'data': config
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    elif request.method == 'POST':
        try:
            config = request.get_json()
            save_budget_config(config)
            return jsonify({
                'success': True,
                'data': config
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


@app.route('/api/budget/check')
def api_budget_check():
    """检查预算使用情况"""
    try:
        parser = TelemetryParser()
        config = load_budget_config()

        # 获取不同时间段的数据
        now = datetime.now()

        # 今日数据
        daily_events = parser.parse_telemetry_files(hours=24)
        daily_usage = parser.extract_usage_data(daily_events)
        daily_stats = parser.get_total_stats(daily_usage)

        # 本周数据
        weekly_events = parser.parse_telemetry_files(hours=24 * 7)
        weekly_usage = parser.extract_usage_data(weekly_events)
        weekly_stats = parser.get_total_stats(weekly_usage)

        # 本月数据
        monthly_events = parser.parse_telemetry_files(hours=24 * 30)
        monthly_usage = parser.extract_usage_data(monthly_events)
        monthly_stats = parser.get_total_stats(monthly_usage)

        # 计算使用百分比
        daily_percent = (daily_stats['total_cost'] / config['daily_limit']) * 100 if config['daily_limit'] > 0 else 0
        weekly_percent = (weekly_stats['total_cost'] / config['weekly_limit']) * 100 if config['weekly_limit'] > 0 else 0
        monthly_percent = (monthly_stats['total_cost'] / config['monthly_limit']) * 100 if config['monthly_limit'] > 0 else 0

        # 检查是否需要警告
        threshold = config.get('alert_threshold', 0.8) * 100
        alerts = []

        if daily_percent >= threshold:
            alerts.append({
                'type': 'warning',
                'period': 'daily',
                'message': f'今日花费已达预算的 {daily_percent:.1f}%',
                'cost': daily_stats['total_cost'],
                'limit': config['daily_limit']
            })

        if weekly_percent >= threshold:
            alerts.append({
                'type': 'warning',
                'period': 'weekly',
                'message': f'本周花费已达预算的 {weekly_percent:.1f}%',
                'cost': weekly_stats['total_cost'],
                'limit': config['weekly_limit']
            })

        if monthly_percent >= threshold:
            alerts.append({
                'type': 'warning',
                'period': 'monthly',
                'message': f'本月花费已达预算的 {monthly_percent:.1f}%',
                'cost': monthly_stats['total_cost'],
                'limit': config['monthly_limit']
            })

        return jsonify({
            'success': True,
            'data': {
                'daily': {
                    'cost': daily_stats['total_cost'],
                    'limit': config['daily_limit'],
                    'percent': round(daily_percent, 2)
                },
                'weekly': {
                    'cost': weekly_stats['total_cost'],
                    'limit': config['weekly_limit'],
                    'percent': round(weekly_percent, 2)
                },
                'monthly': {
                    'cost': monthly_stats['total_cost'],
                    'limit': config['monthly_limit'],
                    'percent': round(monthly_percent, 2)
                },
                'alerts': alerts
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health')
def health():
    """健康检查"""
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    print("🚀 Claude Code Usage Monitor Starting...")
    print("=" * 60)
    print("📊 访问 http://localhost:5050 查看监控面板")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=5050)
