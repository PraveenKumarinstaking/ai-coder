import { useState, useEffect } from 'react';
import { api } from '../api/client';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    LineElement,
    PointElement,
    ArcElement,
    Title,
    Tooltip,
    Legend
} from 'chart.js';
import { Bar, Line, Pie } from 'react-chartjs-2';
import './ManagerDashboard.css';

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    LineElement,
    PointElement,
    ArcElement,
    Title,
    Tooltip,
    Legend
);

export default function ManagerDashboard() {
    const [stats, setStats] = useState(null);
    const [highRiskTasks, setHighRiskTasks] = useState([]);
    const [overdueTasks, setOverdueTasks] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [statsData, highRisk, overdue] = await Promise.all([
                api.getManagerStats(),
                api.getHighRiskTasks(),
                api.getOverdueTasks()
            ]);
            setStats(statsData);
            setHighRiskTasks(highRisk);
            setOverdueTasks(overdue);
        } catch (error) {
            console.error('Error fetching manager data:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return <div className="loading"><div className="spinner"></div></div>;
    }

    // Chart data
    const tasksPerUserData = {
        labels: Object.keys(stats?.tasks_per_user || {}),
        datasets: [{
            label: 'Tasks',
            data: Object.values(stats?.tasks_per_user || {}),
            backgroundColor: 'rgba(99, 102, 241, 0.7)',
            borderColor: 'rgba(99, 102, 241, 1)',
            borderWidth: 1,
            borderRadius: 8
        }]
    };

    const completionTrendData = {
        labels: (stats?.completion_trend || []).map(d => d.date),
        datasets: [{
            label: 'Completed Tasks',
            data: (stats?.completion_trend || []).map(d => d.completed),
            borderColor: 'rgba(16, 185, 129, 1)',
            backgroundColor: 'rgba(16, 185, 129, 0.2)',
            fill: true,
            tension: 0.4
        }]
    };

    const statusDistData = {
        labels: Object.keys(stats?.status_distribution || {}).map(s => s.replace('_', ' ')),
        datasets: [{
            data: Object.values(stats?.status_distribution || {}),
            backgroundColor: [
                'rgba(245, 158, 11, 0.8)',
                'rgba(59, 130, 246, 0.8)',
                'rgba(16, 185, 129, 0.8)',
                'rgba(239, 68, 68, 0.8)',
                'rgba(168, 85, 247, 0.8)'
            ],
            borderWidth: 0
        }]
    };

    const chartOptions = {
        responsive: true,
        plugins: {
            legend: {
                labels: { color: '#94a3b8' }
            }
        },
        scales: {
            x: {
                ticks: { color: '#64748b' },
                grid: { color: 'rgba(255,255,255,0.05)' }
            },
            y: {
                ticks: { color: '#64748b' },
                grid: { color: 'rgba(255,255,255,0.05)' }
            }
        }
    };

    const pieOptions = {
        responsive: true,
        plugins: {
            legend: {
                position: 'bottom',
                labels: { color: '#94a3b8' }
            }
        }
    };

    return (
        <div className="manager-dashboard">
            <div className="page-header">
                <h1>Manager Dashboard</h1>
                <p>Team overview with AI-powered insights</p>
            </div>

            {/* Stats Cards */}
            <div className="stats-grid">
                <div className="stat-card danger">
                    <div className="stat-icon">⏰</div>
                    <div className="stat-value">{stats?.overdue_tasks || 0}</div>
                    <div className="stat-label">Overdue Tasks</div>
                </div>
                <div className="stat-card warning">
                    <div className="stat-icon">⚠️</div>
                    <div className="stat-value">{stats?.high_risk_tasks || 0}</div>
                    <div className="stat-label">High Risk Tasks</div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon">👥</div>
                    <div className="stat-value">{stats?.overloaded_users || 0}</div>
                    <div className="stat-label">Overloaded Users</div>
                </div>
                <div className="stat-card success">
                    <div className="stat-icon">📊</div>
                    <div className="stat-value">{stats?.total_tasks || 0}</div>
                    <div className="stat-label">Total Tasks</div>
                </div>
            </div>

            {/* Bottleneck Alert */}
            {overdueTasks.length > 0 && (
                <div className="glass-card bottleneck-panel">
                    <h3>🚨 Workflow Bottlenecks</h3>
                    {overdueTasks.slice(0, 3).map(task => (
                        <div key={task.id} className="alert alert-danger">
                            <span className="alert-icon">⏲️</span>
                            <div className="alert-content">
                                <span className="alert-title">Task "{task.title}" is overdue</span>
                                <span className="alert-message">Assigned to: {task.assignee?.name}</span>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Charts */}
            <div className="charts-grid">
                <div className="chart-container">
                    <h3 className="chart-title">📊 Tasks per User</h3>
                    <Bar data={tasksPerUserData} options={chartOptions} />
                </div>
                <div className="chart-container">
                    <h3 className="chart-title">📈 Completion Trend</h3>
                    <Line data={completionTrendData} options={chartOptions} />
                </div>
                <div className="chart-container">
                    <h3 className="chart-title">🎯 Status Distribution</h3>
                    <Pie data={statusDistData} options={pieOptions} />
                </div>
            </div>

            {/* High Risk Tasks Table */}
            {highRiskTasks.length > 0 && (
                <div className="glass-card">
                    <h3 className="panel-title">⚠️ High-Risk Tasks</h3>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Task</th>
                                <th>Assigned To</th>
                                <th>Confidence</th>
                                <th>Due</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {highRiskTasks.map(task => (
                                <tr key={task.id}>
                                    <td>{task.title}</td>
                                    <td>{task.assignee?.name || 'Unknown'}</td>
                                    <td>
                                        <span className="confidence-value low">
                                            {task.confidence_score.toFixed(0)}%
                                        </span>
                                    </td>
                                    <td>{new Date(task.due_date).toLocaleDateString()}</td>
                                    <td>
                                        <span className={`badge badge-${task.is_escalated ? 'danger' : 'warning'}`}>
                                            {task.is_escalated ? '🚨 Escalated' : task.status}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
