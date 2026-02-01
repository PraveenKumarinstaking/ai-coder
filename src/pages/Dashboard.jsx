import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import './Dashboard.css';

export default function Dashboard() {
    const [stats, setStats] = useState(null);
    const [tasks, setTasks] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchDashboardData();
    }, []);

    useEffect(() => {
        const socket = new WebSocket('ws://localhost:8000/ws');

        socket.onmessage = (event) => {
            const message = JSON.parse(event.data);
            if (message.type === 'TASK_UPDATE' || message.type === 'TASK_DELETE' || message.type === 'NOTIFICATION_UPDATE') {
                // For simplicity, refetch all dashboard data when any relevant change occurs
                // This ensures stats and task lists are always in sync
                fetchDashboardData();
            }
        };

        socket.onerror = (error) => {
            console.error('Dashboard WebSocket error:', error);
        };

        return () => {
            socket.close();
        };
    }, []);

    const fetchDashboardData = async () => {
        try {
            const [statsData, tasksData] = await Promise.all([
                api.getDashboardStats(),
                api.getMyTasks()
            ]);

            setStats(statsData);
            setTasks(tasksData);

            // Generate alerts from low confidence tasks
            const lowConfidenceTasks = tasksData.filter(t => t.confidence_score < 40);
            setAlerts(lowConfidenceTasks.map(t => ({
                type: 'warning',
                message: `Task "${t.title}" has low confidence score (${t.confidence_score.toFixed(0)}%)`
            })));

        } catch (error) {
            console.error('Error fetching dashboard data:', error);
        } finally {
            setLoading(false);
        }
    };

    const getConfidenceClass = (score) => {
        if (score >= 70) return 'high';
        if (score >= 40) return 'medium';
        return 'low';
    };

    const getPriorityClass = (priority) => {
        return `priority-${priority}`;
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric'
        });
    };

    if (loading) {
        return (
            <div className="loading">
                <div className="spinner"></div>
            </div>
        );
    }

    return (
        <div className="dashboard">
            <div className="page-header">
                <h1>My Dashboard</h1>
                <p>Track your tasks and monitor AI-powered insights</p>
            </div>

            {/* Stats Cards */}
            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-icon">📋</div>
                    <div className="stat-value">{stats?.total_tasks || 0}</div>
                    <div className="stat-label">Total Tasks</div>
                </div>
                <div className="stat-card">
                    <div className="stat-icon">🔄</div>
                    <div className="stat-value">{stats?.in_progress || 0}</div>
                    <div className="stat-label">In Progress</div>
                </div>
                <div className="stat-card success">
                    <div className="stat-icon">✅</div>
                    <div className="stat-value">{stats?.completed || 0}</div>
                    <div className="stat-label">Completed</div>
                </div>
                <div className="stat-card danger">
                    <div className="stat-icon">⚠️</div>
                    <div className="stat-value">{stats?.high_risk || 0}</div>
                    <div className="stat-label">High Risk</div>
                </div>
            </div>

            {/* AI Alerts */}
            {alerts.length > 0 && (
                <div className="glass-card alerts-panel">
                    <h3 className="panel-title">🤖 AI Alerts</h3>
                    {alerts.map((alert, index) => (
                        <div key={index} className={`alert alert-${alert.type}`}>
                            <span className="alert-icon">⚠️</span>
                            <div className="alert-content">
                                <span className="alert-message">{alert.message}</span>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Tasks Table */}
            <div className="glass-card">
                <div className="panel-header">
                    <h3 className="panel-title">📋 My Tasks</h3>
                    <Link to="/create-task" className="btn btn-primary btn-sm">
                        ➕ Create Task
                    </Link>
                </div>

                {tasks.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-state-icon">📭</div>
                        <p>No tasks assigned to you yet</p>
                        <Link to="/create-task" className="btn btn-primary">Create Your First Task</Link>
                    </div>
                ) : (
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Task</th>
                                <th>Priority</th>
                                <th>Due Date</th>
                                <th>Confidence</th>
                                <th>Status</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {tasks.map((task) => (
                                <tr key={task.id}>
                                    <td>
                                        <Link to={`/tasks/${task.id}`} className="task-link">
                                            {task.title}
                                        </Link>
                                    </td>
                                    <td>
                                        <span className={`badge ${getPriorityClass(task.priority)}`}>
                                            {task.priority}
                                        </span>
                                    </td>
                                    <td>{formatDate(task.due_date)}</td>
                                    <td>
                                        <div className="confidence-score">
                                            <div className="confidence-bar">
                                                <div
                                                    className={`confidence-fill ${getConfidenceClass(task.confidence_score)}`}
                                                    style={{ width: `${task.confidence_score}%` }}
                                                ></div>
                                            </div>
                                            <span className={`confidence-value ${getConfidenceClass(task.confidence_score)}`}>
                                                {task.confidence_score.toFixed(0)}%
                                            </span>
                                        </div>
                                    </td>
                                    <td>
                                        <span className={`badge badge-${task.status === 'completed' ? 'success' : task.status === 'in_progress' ? 'info' : 'warning'}`}>
                                            {task.status.replace('_', ' ')}
                                        </span>
                                    </td>
                                    <td>
                                        <Link to={`/tasks/${task.id}`} className="btn btn-secondary btn-sm">
                                            View
                                        </Link>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
}
