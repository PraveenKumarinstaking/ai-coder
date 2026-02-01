import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import './Tasks.css';

export default function Tasks() {
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState({ status: '', priority: '' });

    useEffect(() => {
        fetchTasks();
    }, []);

    const fetchTasks = async () => {
        try {
            const data = await api.getMyTasks();
            setTasks(data);
        } catch (error) {
            console.error('Error fetching tasks:', error);
        } finally {
            setLoading(false);
        }
    };

    const getConfidenceClass = (score) => {
        if (score >= 70) return 'high';
        if (score >= 40) return 'medium';
        return 'low';
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    };

    const filteredTasks = tasks.filter(task => {
        if (filter.status && task.status !== filter.status) return false;
        if (filter.priority && task.priority !== filter.priority) return false;
        return true;
    });

    if (loading) {
        return <div className="loading"><div className="spinner"></div></div>;
    }

    return (
        <div className="tasks-page">
            <div className="page-header">
                <h1>My Tasks</h1>
                <p>View and manage all your assigned tasks</p>
            </div>

            <div className="glass-card">
                <div className="tasks-toolbar">
                    <div className="filters">
                        <select
                            className="form-select filter-select"
                            value={filter.status}
                            onChange={(e) => setFilter(prev => ({ ...prev, status: e.target.value }))}
                        >
                            <option value="">All Status</option>
                            <option value="pending">Pending</option>
                            <option value="in_progress">In Progress</option>
                            <option value="completed">Completed</option>
                            <option value="overdue">Overdue</option>
                        </select>

                        <select
                            className="form-select filter-select"
                            value={filter.priority}
                            onChange={(e) => setFilter(prev => ({ ...prev, priority: e.target.value }))}
                        >
                            <option value="">All Priority</option>
                            <option value="low">Low</option>
                            <option value="medium">Medium</option>
                            <option value="high">High</option>
                            <option value="critical">Critical</option>
                        </select>
                    </div>

                    <Link to="/create-task" className="btn btn-primary">
                        ➕ Create Task
                    </Link>
                </div>

                {filteredTasks.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-state-icon">📋</div>
                        <p>No tasks found</p>
                    </div>
                ) : (
                    <div className="tasks-grid">
                        {filteredTasks.map(task => (
                            <Link key={task.id} to={`/tasks/${task.id}`} className="task-card glass-card">
                                <div className="task-header">
                                    <span className={`badge priority-${task.priority}`}>
                                        {task.priority}
                                    </span>
                                    <span className={`badge badge-${task.status === 'completed' ? 'success' : task.status === 'in_progress' ? 'info' : 'warning'}`}>
                                        {task.status.replace('_', ' ')}
                                    </span>
                                </div>

                                <h3 className="task-title">{task.title}</h3>
                                <p className="task-desc">{task.description?.slice(0, 100) || 'No description'}</p>

                                <div className="task-meta">
                                    <div className="meta-item">
                                        <span className="meta-icon">📅</span>
                                        <span>{formatDate(task.due_date)}</span>
                                    </div>
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
                                </div>
                            </Link>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
