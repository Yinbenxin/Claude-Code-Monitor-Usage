// Claude Code Usage Monitor - 前端JavaScript

class UsageMonitor {
    constructor() {
        this.costChart = null;
        this.modelChart = null;
        this.refreshInterval = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadData();
        this.loadBudget();
        this.checkBudget();

        // 每30秒自动刷新
        this.refreshInterval = setInterval(() => {
            this.loadData();
            this.checkBudget();
        }, 30000);
    }

    setupEventListeners() {
        // 刷新按钮
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.loadData();
            this.checkBudget();
        });

        // 时间范围选择
        document.getElementById('timeRange').addEventListener('change', () => {
            this.loadData();
            this.checkBudget();
        });

        // 预算设置
        const modal = document.getElementById('budgetModal');
        const btn = document.getElementById('budgetSettingsBtn');
        const span = document.getElementsByClassName('close')[0];
        const cancelBtn = document.getElementById('cancelBtn');

        btn.onclick = () => {
            this.loadBudget();
            modal.style.display = 'block';
        };

        span.onclick = () => {
            modal.style.display = 'none';
        };

        cancelBtn.onclick = () => {
            modal.style.display = 'none';
        };

        window.onclick = (event) => {
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        };

        // 预算表单提交
        document.getElementById('budgetForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveBudget();
        });
    }

    getTimeRangeParam() {
        const value = document.getElementById('timeRange').value;
        return value ? `?hours=${value}` : '';
    }

    async loadData() {
        const params = this.getTimeRangeParam();

        try {
            // 加载总体统计
            await this.loadTotalStats(params);

            // 加载模型统计
            await this.loadModelStats(params);

            // 加载时间线数据
            await this.loadTimelineStats(params);

            // 加载最近请求
            await this.loadRecentRequests(params);

            // 更新时间
            document.getElementById('lastUpdate').textContent = new Date().toLocaleString('zh-CN');
        } catch (error) {
            console.error('加载数据失败:', error);
            this.showError('加载数据失败，请稍后重试');
        }
    }

    async loadTotalStats(params) {
        const response = await fetch(`/api/stats/total${params}`);
        const result = await response.json();

        if (result.success) {
            const data = result.data;

            document.getElementById('totalCost').textContent = `$${data.total_cost.toFixed(4)}`;
            document.getElementById('totalTokens').textContent = this.formatNumber(data.total_tokens);
            document.getElementById('totalRequests').textContent = this.formatNumber(data.total_requests);
            document.getElementById('avgCost').textContent = `$${data.avg_cost_per_request.toFixed(6)}`;
        }
    }

    async loadModelStats(params) {
        const response = await fetch(`/api/stats/models${params}`);
        const result = await response.json();

        if (result.success) {
            const data = result.data;
            this.updateModelTable(data);
            this.updateModelChart(data);
        }
    }

    async loadTimelineStats(params) {
        const period = this.getTimelinePeriod();
        const response = await fetch(`/api/stats/timeline${params}&period=${period}`);
        const result = await response.json();

        if (result.success) {
            const data = result.data;
            this.updateCostChart(data);
        }
    }

    async loadRecentRequests(params) {
        const response = await fetch(`/api/stats/recent${params}&limit=20`);
        const result = await response.json();

        if (result.success) {
            const data = result.data;
            this.updateRecentTable(data);
        }
    }

    getTimelinePeriod() {
        const hours = document.getElementById('timeRange').value;
        if (!hours || hours >= 720) return 'week';
        if (hours >= 168) return 'day';
        if (hours >= 48) return 'day';
        return 'hour';
    }

    updateModelTable(data) {
        const tbody = document.getElementById('modelTableBody');

        if (Object.keys(data).length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">暂无数据</td></tr>';
            return;
        }

        const rows = Object.entries(data).map(([model, stats]) => `
            <tr>
                <td><strong>${this.formatModelName(model)}</strong></td>
                <td>${this.formatNumber(stats.requests)}</td>
                <td>${this.formatNumber(stats.input_tokens)}</td>
                <td>${this.formatNumber(stats.output_tokens)}</td>
                <td>${this.formatNumber(stats.cached_tokens)}</td>
                <td><strong>$${stats.cost.toFixed(4)}</strong></td>
            </tr>
        `).join('');

        tbody.innerHTML = rows;
    }

    updateRecentTable(data) {
        const tbody = document.getElementById('recentTableBody');

        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="loading">暂无数据</td></tr>';
            return;
        }

        const rows = data.map(item => `
            <tr>
                <td>${this.formatTimestamp(item.timestamp)}</td>
                <td>${this.formatModelName(item.model)}</td>
                <td>${this.formatNumber(item.input_tokens)}</td>
                <td>${this.formatNumber(item.output_tokens)}</td>
                <td>$${item.cost_usd.toFixed(6)}</td>
            </tr>
        `).join('');

        tbody.innerHTML = rows;
    }

    updateCostChart(data) {
        const ctx = document.getElementById('costChart').getContext('2d');

        const labels = Object.keys(data);
        const costs = labels.map(key => data[key].total_cost);
        const requests = labels.map(key => data[key].request_count);

        if (this.costChart) {
            this.costChart.destroy();
        }

        this.costChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '花费 (USD)',
                        data: costs,
                        borderColor: '#d97706',
                        backgroundColor: 'rgba(217, 119, 6, 0.1)',
                        tension: 0.4,
                        fill: true,
                        yAxisID: 'y'
                    },
                    {
                        label: '请求次数',
                        data: requests,
                        borderColor: '#059669',
                        backgroundColor: 'rgba(5, 150, 105, 0.1)',
                        tension: 0.4,
                        fill: true,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        labels: {
                            color: '#cbd5e1'
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: '#f1f5f9',
                        bodyColor: '#cbd5e1',
                        borderColor: '#475569',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#cbd5e1' },
                        grid: { color: '#334155' }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        ticks: {
                            color: '#cbd5e1',
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        },
                        grid: { color: '#334155' }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        ticks: { color: '#cbd5e1' },
                        grid: { drawOnChartArea: false }
                    }
                }
            }
        });
    }

    updateModelChart(data) {
        const ctx = document.getElementById('modelChart').getContext('2d');

        const models = Object.keys(data);
        const costs = models.map(model => data[model].cost);
        const colors = this.generateColors(models.length);

        if (this.modelChart) {
            this.modelChart.destroy();
        }

        this.modelChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: models.map(m => this.formatModelName(m)),
                datasets: [{
                    data: costs,
                    backgroundColor: colors,
                    borderColor: '#1e293b',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#cbd5e1',
                            padding: 15
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: '#f1f5f9',
                        bodyColor: '#cbd5e1',
                        borderColor: '#475569',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                return label + ': $' + value.toFixed(4);
                            }
                        }
                    }
                }
            }
        });
    }

    async loadBudget() {
        try {
            const response = await fetch('/api/budget');
            const result = await response.json();

            if (result.success) {
                const config = result.data;
                document.getElementById('dailyLimit').value = config.daily_limit;
                document.getElementById('weeklyLimit').value = config.weekly_limit;
                document.getElementById('monthlyLimit').value = config.monthly_limit;
                document.getElementById('alertThreshold').value = (config.alert_threshold * 100).toFixed(0);
            }
        } catch (error) {
            console.error('加载预算配置失败:', error);
        }
    }

    async saveBudget() {
        const config = {
            daily_limit: parseFloat(document.getElementById('dailyLimit').value),
            weekly_limit: parseFloat(document.getElementById('weeklyLimit').value),
            monthly_limit: parseFloat(document.getElementById('monthlyLimit').value),
            alert_threshold: parseFloat(document.getElementById('alertThreshold').value) / 100
        };

        try {
            const response = await fetch('/api/budget', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });

            const result = await response.json();

            if (result.success) {
                document.getElementById('budgetModal').style.display = 'none';
                this.checkBudget();
                this.showSuccess('预算设置已保存');
            }
        } catch (error) {
            console.error('保存预算配置失败:', error);
            this.showError('保存失败，请重试');
        }
    }

    async checkBudget() {
        try {
            const response = await fetch('/api/budget/check');
            const result = await response.json();

            if (result.success) {
                const data = result.data;

                // 更新进度条
                this.updateBudgetProgress('daily', data.daily);
                this.updateBudgetProgress('weekly', data.weekly);
                this.updateBudgetProgress('monthly', data.monthly);

                // 显示警告
                this.showAlerts(data.alerts);
            }
        } catch (error) {
            console.error('检查预算失败:', error);
        }
    }

    updateBudgetProgress(period, data) {
        const progressEl = document.getElementById(`${period}Progress`);
        const textEl = document.getElementById(`${period}BudgetText`);

        const percent = Math.min(data.percent, 100);
        progressEl.style.width = percent + '%';

        if (percent >= 100) {
            progressEl.className = 'progress-fill warning';
        } else if (percent >= 80) {
            progressEl.className = 'progress-fill warning';
        } else {
            progressEl.className = 'progress-fill';
        }

        textEl.textContent = `$${data.cost.toFixed(2)} / $${data.limit.toFixed(2)}`;
    }

    showAlerts(alerts) {
        const container = document.getElementById('alertsContainer');

        if (alerts.length === 0) {
            container.innerHTML = '';
            return;
        }

        const alertsHtml = alerts.map(alert => `
            <div class="alert ${alert.type}">
                <span>⚠️</span>
                <div>
                    <strong>${alert.message}</strong>
                    <p>当前: $${alert.cost.toFixed(2)} / 限额: $${alert.limit.toFixed(2)}</p>
                </div>
            </div>
        `).join('');

        container.innerHTML = alertsHtml;
    }

    // 工具方法
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(2) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(2) + 'K';
        }
        return num.toLocaleString('en-US');
    }

    formatModelName(model) {
        const shortNames = {
            'claude-opus-4-6': 'Opus 4.6',
            'claude-sonnet-4-6': 'Sonnet 4.6',
            'claude-sonnet-4-5-20250929': 'Sonnet 4.5',
            'claude-haiku-4-5-20251001': 'Haiku 4.5'
        };
        return shortNames[model] || model;
    }

    formatTimestamp(timestamp) {
        if (!timestamp) return '--';
        const date = new Date(timestamp);
        return date.toLocaleString('zh-CN', {
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    generateColors(count) {
        const colors = [
            '#d97706', '#059669', '#3b82f6', '#8b5cf6',
            '#ec4899', '#f59e0b', '#10b981', '#6366f1'
        ];
        return colors.slice(0, count);
    }

    showSuccess(message) {
        // 简单的成功提示
        const alert = document.createElement('div');
        alert.className = 'alert';
        alert.style.cssText = 'position:fixed;top:20px;right:20px;z-index:2000;background:#10b981;color:white;padding:1rem 2rem;border-radius:0.5rem;';
        alert.textContent = '✓ ' + message;
        document.body.appendChild(alert);

        setTimeout(() => {
            alert.remove();
        }, 3000);
    }

    showError(message) {
        const alert = document.createElement('div');
        alert.className = 'alert';
        alert.style.cssText = 'position:fixed;top:20px;right:20px;z-index:2000;background:#dc2626;color:white;padding:1rem 2rem;border-radius:0.5rem;';
        alert.textContent = '✗ ' + message;
        document.body.appendChild(alert);

        setTimeout(() => {
            alert.remove();
        }, 3000);
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new UsageMonitor();
});
