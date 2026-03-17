# 项目结构说明

```
Claude-Code-Usage-Monitor/
│
├── app.py                    # Flask Web 应用主文件
├── monitor.py                # CLI 命令行工具
├── start.sh                  # 快速启动脚本
├── requirements.txt          # Python 依赖列表
│
├── src/                      # 源代码目录
│   ├── __init__.py
│   └── telemetry_parser.py  # 遥测数据解析器
│
├── templates/                # HTML 模板
│   └── index.html           # 主页面模板
│
├── static/                   # 静态资源
│   ├── css/
│   │   └── style.css        # 样式表
│   └── js/
│       └── app.js           # 前端 JavaScript
│
├── data/                     # 数据目录
│   └── budget.json          # 预算配置（自动生成）
│
├── README.md                 # 项目说明文档
├── QUICKSTART.md            # 快速开始指南
├── LICENSE                   # MIT 许可证
└── .gitignore               # Git 忽略文件
```

## 核心文件说明

### app.py
Flask Web 应用，提供以下功能：
- RESTful API 端点
- 数据聚合和统计
- 预算管理
- Web 界面服务

主要 API 端点：
- `/api/stats/total` - 总体统计
- `/api/stats/models` - 模型统计
- `/api/stats/timeline` - 时间线数据
- `/api/stats/recent` - 最近请求
- `/api/budget` - 预算管理
- `/api/budget/check` - 预算检查

### monitor.py
命令行工具，提供快速的统计查询功能。

支持的命令：
- 查看所有时间统计
- 查看指定时间范围统计
- 查看最近请求记录

### src/telemetry_parser.py
核心解析器，负责：
- 读取 `~/.claude/telemetry/` 目录
- 解析 JSONL 格式的遥测文件
- 提取使用数据（tokens, cost, model 等）
- 按时间段聚合数据
- 生成统计报告

主要类和方法：
- `TelemetryParser` - 主解析类
  - `parse_telemetry_files()` - 解析文件
  - `extract_usage_data()` - 提取数据
  - `aggregate_by_time_period()` - 时间聚合
  - `get_total_stats()` - 总体统计
  - `get_model_breakdown()` - 模型分解

### templates/index.html
主页面模板，包含：
- 响应式布局
- 统计卡片
- 预算进度条
- 图表容器
- 数据表格
- 预算设置模态框

### static/css/style.css
样式表，使用暗色主题，包含：
- 现代化 UI 设计
- 响应式网格布局
- 动画效果
- 图表样式
- 表格样式

### static/js/app.js
前端逻辑，包含：
- 数据获取和刷新
- Chart.js 图表渲染
- 预算管理
- 模态框控制
- 自动刷新机制

## 数据流

```
~/.claude/telemetry/*.json
         ↓
  TelemetryParser
         ↓
    [解析和聚合]
         ↓
   ┌─────┴─────┐
   ↓           ↓
Flask API    CLI Tool
   ↓
Web Frontend
   ↓
  浏览器
```

## 扩展开发

### 添加新的统计类型

1. 在 `telemetry_parser.py` 中添加新方法
2. 在 `app.py` 中创建新的 API 端点
3. 在 `app.js` 中添加数据获取逻辑
4. 在 `index.html` 中添加显示区域

### 添加新的图表

1. 在 `index.html` 中添加 canvas 元素
2. 在 `app.js` 中创建 Chart.js 实例
3. 调用 API 获取数据并渲染

### 自定义预算周期

修改 `app.py` 中的 `api_budget_check()` 函数，添加新的时间周期计算逻辑。
