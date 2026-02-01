import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { api } from '../api/client';
import './TaskDetail.css';

export default function TaskDetail() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [task, setTask] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchTask();
    }, [id]);

    const fetchTask = async () => {
        try {
            const data = await api.getTask(id);
            setTask(data);
        } catch (error) {
            setError(error.message);
        } finally {
            setLoading(false);
        }
    };

    const handleStatusChange = async (newStatus) => {
        try {
            await api.updateTaskStatus(id, newStatus);
            fetchTask();
        } catch (error) {
            setError(error.message);
        }
    };

    const handleDelete = async () => {
        if (window.confirm('Are you sure you want to delete this task?')) {
            try {
                await api.deleteTask(id);
                navigate('/tasks');
            } catch (error) {
                setError(error.message);
            }
        }
    };

    const getConfidenceClass = (score) => {
        if (score >= 70) return 'high';
        if (score >= 40) return 'medium';
        return 'low';
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    };

    if (loading) {
        return <div className="loading"><div className="spinner"></div></div>;
    }

    if (error || !task) {
        return (
            <div className="glass-card">
                <div className="alert alert-danger">
                    <span className="alert-icon">❌</span>
                    <div className="alert-content">
                        <span className="alert-message">{error || 'Task not found'}</span>
                    </div>
                </div>
                <Link to="/tasks" className="btn btn-secondary">← Back to Tasks</Link>
            </div>
        );
    }

    return (
        <div className="task-detail">
            <div className="detail-header">
                <Link to="/tasks" className="back-link">← Back to Tasks</Link>
                <div className="detail-actions">
                    <button className="btn btn-secondary" onClick={() => navigate(`/edit-task/${id}`)}>
                        ✏️ Edit
                    </button>
                    <button className="btn btn-danger" onClick={handleDelete}>
                        🗑️ Delete
                    </button>
                </div>
            </div>

            <div className="glass-card detail-card">
                <div className="detail-top">
                    <h1 className="detail-title">{task.title}</h1>
                    <div className="detail-badges">
                        <span className={`badge priority-${task.priority}`}>
                            {task.priority}
                        </span>
                        <span className={`badge badge-${task.status === 'completed' ? 'success' : task.status === 'in_progress' ? 'info' : 'warning'}`}>
                            {task.status.replace('_', ' ')}
                        </span>
                        {task.is_escalated && (
                            <span className="badge badge-danger">🚨 Escalated</span>
                        )}
                    </div>
                </div>

                <div className="detail-grid">
                    <div className="detail-section">
                        <h3>📋 Details</h3>
                        <div className="detail-item">
                            <label>Description</label>
                            <p>{task.description || 'No description provided'}</p>
                        </div>
                        <div className="detail-item">
                            <label>Due Date</label>
                            <p>{formatDate(task.due_date)}</p>
                        </div>
                        <div className="detail-item">
                            <label>Assigned To</label>
                            <p>{task.assignee?.name || 'Unknown'}</p>
                        </div>
                        <div className="detail-item">
                            <label>Created By</label>
                            <p>{task.creator?.name || 'Unknown'}</p>
                        </div>
                    </div>

                    <div className="detail-section">
                        <h3>🤖 AI Insights</h3>
                        <div className="ai-metrics">
                            <div className="metric">
                                <label>Confidence Score</label>
                                <div className="confidence-large">
                                    <div className="confidence-bar large">
                                        <div
                                            className={`confidence-fill ${getConfidenceClass(task.confidence_score)}`}
                                            style={{ width: `${task.confidence_score}%` }}
                                        ></div>
                                    </div>
                                    <span className={`confidence-value large ${getConfidenceClass(task.confidence_score)}`}>
                                        {task.confidence_score.toFixed(0)}%
                                    </span>
                                </div>
                            </div>
                            <div className="metric">
                                <label>Priority Score</label>
                                <span className="metric-value">{task.priority_score.toFixed(0)}</span>
                            </div>
                        </div>

                        {task.confidence_score < 40 && (
                            <div className="alert alert-warning">
                                <span className="alert-icon">⚠️</span>
                                <div className="alert-content">
                                    <span className="alert-title">Low Confidence Detected</span>
                                    <span className="alert-message">This task may be at risk of missing its deadline.</span>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {task.dependencies && task.dependencies.length > 0 && (
                    <div className="detail-section full">
                        <h3>🔗 Dependencies</h3>
                        <div className="dependencies-list">
                            {task.dependencies.map(dep => (
                                <div key={dep.id} className="dependency-item">
                                    <span className="dep-status">
                                        {dep.status === 'completed' ? '✅' : '⏳'}
                                    </span>
                                    <Link to={`/tasks/${dep.id}`}>{dep.title}</Link>
                                    <span className={`badge badge-${dep.status === 'completed' ? 'success' : 'warning'}`}>
                                        {dep.status}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                <div className="detail-section full">
                    <h3>🎯 Quick Actions</h3>
                    <div className="status-buttons">
                        {task.status !== 'in_progress' && task.status !== 'completed' && (
                            <button
                                className="btn btn-primary"
                                onClick={() => handleStatusChange('in_progress')}
                            >
                                🚀 Start Working
                            </button>
                        )}
                        {task.status !== 'completed' && (
                            <button
                                className="btn btn-success"
                                onClick={() => handleStatusChange('completed')}
                            >
                                ✅ Mark Complete
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
