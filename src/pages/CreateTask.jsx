import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import './CreateTask.css';

export default function CreateTask() {
    const navigate = useNavigate();
    const [users, setUsers] = useState([]);
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const [formData, setFormData] = useState({
        title: '',
        description: '',
        priority: 'medium',
        due_date: '',
        assigned_to: '',
        dependency_ids: []
    });

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [usersData, tasksData] = await Promise.all([
                api.getUsers(),
                api.getTasks()
            ]);
            setUsers(usersData);
            setTasks(tasksData.filter(t => t.status !== 'completed'));
        } catch (error) {
            console.error('Error fetching data:', error);
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleDependencyChange = (e) => {
        const options = e.target.options;
        const selected = [];
        for (let i = 0; i < options.length; i++) {
            if (options[i].selected) {
                selected.push(parseInt(options[i].value));
            }
        }
        setFormData(prev => ({ ...prev, dependency_ids: selected }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        setLoading(true);

        try {
            // Format the due date properly
            const taskData = {
                ...formData,
                assigned_to: parseInt(formData.assigned_to),
                due_date: new Date(formData.due_date).toISOString()
            };

            await api.createTask(taskData);
            setSuccess('Task created successfully! AI agents will calculate priority and confidence scores.');

            setTimeout(() => {
                navigate('/dashboard');
            }, 2000);
        } catch (error) {
            setError(error.message);
        } finally {
            setLoading(false);
        }
    };

    // Get tomorrow's date as minimum
    const getMinDate = () => {
        const today = new Date();
        today.setDate(today.getDate() + 1);
        return today.toISOString().split('T')[0];
    };

    return (
        <div className="create-task">
            <div className="page-header">
                <h1>Create New Task</h1>
                <p>Create a task and let AI agents handle prioritization</p>
            </div>

            <div className="glass-card form-card">
                <form onSubmit={handleSubmit}>
                    {error && (
                        <div className="alert alert-danger">
                            <span className="alert-icon">❌</span>
                            <div className="alert-content">
                                <span className="alert-message">{error}</span>
                            </div>
                        </div>
                    )}

                    {success && (
                        <div className="alert alert-success">
                            <span className="alert-icon">✅</span>
                            <div className="alert-content">
                                <span className="alert-message">{success}</span>
                            </div>
                        </div>
                    )}

                    <div className="form-grid">
                        <div className="form-group">
                            <label className="form-label">Task Title *</label>
                            <input
                                type="text"
                                name="title"
                                className="form-input"
                                value={formData.title}
                                onChange={handleChange}
                                placeholder="Enter task title"
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label className="form-label">Priority *</label>
                            <select
                                name="priority"
                                className="form-select"
                                value={formData.priority}
                                onChange={handleChange}
                            >
                                <option value="low">🟢 Low</option>
                                <option value="medium">🟡 Medium</option>
                                <option value="high">🔴 High</option>
                                <option value="critical">🟣 Critical</option>
                            </select>
                        </div>

                        <div className="form-group full-width">
                            <label className="form-label">Description</label>
                            <textarea
                                name="description"
                                className="form-textarea"
                                value={formData.description}
                                onChange={handleChange}
                                placeholder="Enter task description"
                                rows="4"
                            />
                        </div>

                        <div className="form-group">
                            <label className="form-label">Due Date *</label>
                            <input
                                type="date"
                                name="due_date"
                                className="form-input"
                                value={formData.due_date}
                                onChange={handleChange}
                                min={getMinDate()}
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label className="form-label">Assign To *</label>
                            <select
                                name="assigned_to"
                                className="form-select"
                                value={formData.assigned_to}
                                onChange={handleChange}
                                required
                            >
                                <option value="">Select user</option>
                                {users.map(user => (
                                    <option key={user.id} value={user.id}>
                                        {user.name} ({user.role})
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="form-group full-width">
                            <label className="form-label">Dependencies (Optional)</label>
                            <select
                                multiple
                                className="form-select multi-select"
                                value={formData.dependency_ids}
                                onChange={handleDependencyChange}
                            >
                                {tasks.map(task => (
                                    <option key={task.id} value={task.id}>
                                        {task.title}
                                    </option>
                                ))}
                            </select>
                            <small className="form-hint">Hold Ctrl/Cmd to select multiple tasks this depends on</small>
                        </div>
                    </div>

                    <div className="form-actions">
                        <button
                            type="button"
                            className="btn btn-secondary"
                            onClick={() => navigate('/dashboard')}
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            className="btn btn-primary"
                            disabled={loading}
                        >
                            {loading ? 'Creating...' : '➕ Create Task'}
                        </button>
                    </div>
                </form>

                <div className="ai-info">
                    <h4>🤖 AI Will Automatically:</h4>
                    <ul>
                        <li>Calculate priority score based on urgency and dependencies</li>
                        <li>Generate confidence score for task completion</li>
                        <li>Schedule reminder notifications</li>
                        <li>Monitor for risks and escalate if needed</li>
                    </ul>
                </div>
            </div>
        </div>
    );
}
