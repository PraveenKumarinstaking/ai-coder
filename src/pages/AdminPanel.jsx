import { useState, useEffect } from 'react';
import { api } from '../api/client';
import './AdminPanel.css';

export default function AdminPanel() {
    const [users, setUsers] = useState([]);
    const [agents, setAgents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [editUser, setEditUser] = useState(null);
    const [formData, setFormData] = useState({ name: '', email: '', password: '', role: 'user' });

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [usersData, agentsData] = await Promise.all([
                api.getUsers(),
                api.getAgentStatus()
            ]);
            setUsers(usersData);
            setAgents(agentsData);
        } catch (error) {
            console.error('Error fetching admin data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateUser = async (e) => {
        e.preventDefault();
        try {
            await api.register(formData);
            setShowModal(false);
            setFormData({ name: '', email: '', password: '', role: 'user' });
            fetchData();
        } catch (error) {
            alert(error.message);
        }
    };

    const handleUpdateRole = async (userId, newRole) => {
        try {
            await api.updateUser(userId, { role: newRole });
            fetchData();
        } catch (error) {
            alert(error.message);
        }
    };

    const handleDeleteUser = async (userId) => {
        if (window.confirm('Are you sure you want to delete this user?')) {
            try {
                await api.deleteUser(userId);
                fetchData();
            } catch (error) {
                alert(error.message);
            }
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'running': return 'success';
            case 'error': return 'danger';
            case 'stopped': return 'warning';
            default: return 'info';
        }
    };

    const formatDate = (dateString) => {
        if (!dateString) return 'Never';
        return new Date(dateString).toLocaleString();
    };

    if (loading) {
        return <div className="loading"><div className="spinner"></div></div>;
    }

    return (
        <div className="admin-panel">
            <div className="page-header">
                <h1>Admin Panel</h1>
                <p>Manage users, roles, and monitor AI agents</p>
            </div>

            {/* Agent Status */}
            <div className="glass-card">
                <div className="section-header">
                    <h3>🤖 AI Agent Status</h3>
                </div>
                <div className="agents-grid">
                    {agents.map(agent => (
                        <div key={agent.id} className="agent-card">
                            <div className="agent-header">
                                <span className="agent-name">{agent.agent_name}</span>
                                <span className={`badge badge-${getStatusColor(agent.status)}`}>
                                    {agent.status}
                                </span>
                            </div>
                            <div className="agent-stats">
                                <div className="agent-stat">
                                    <span className="stat-label">Last Run</span>
                                    <span className="stat-value">{formatDate(agent.last_run)}</span>
                                </div>
                                <div className="agent-stat">
                                    <span className="stat-label">Tasks Processed</span>
                                    <span className="stat-value">{agent.tasks_processed}</span>
                                </div>
                                <div className="agent-stat">
                                    <span className="stat-label">Errors</span>
                                    <span className={`stat-value ${agent.errors_count > 0 ? 'error' : ''}`}>
                                        {agent.errors_count}
                                    </span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* User Management */}
            <div className="glass-card">
                <div className="section-header">
                    <h3>👥 User Management</h3>
                    <button className="btn btn-primary" onClick={() => setShowModal(true)}>
                        ➕ Add User
                    </button>
                </div>

                <table className="data-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Role</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {users.map(user => (
                            <tr key={user.id}>
                                <td>
                                    <div className="user-info-cell">
                                        <div className="user-avatar-sm">
                                            {user.name.charAt(0).toUpperCase()}
                                        </div>
                                        {user.name}
                                    </div>
                                </td>
                                <td>{user.email}</td>
                                <td>
                                    <select
                                        className="role-select"
                                        value={user.role}
                                        onChange={(e) => handleUpdateRole(user.id, e.target.value)}
                                    >
                                        <option value="user">User</option>
                                        <option value="manager">Manager</option>
                                        <option value="admin">Admin</option>
                                    </select>
                                </td>
                                <td>
                                    <span className={`badge ${user.is_active ? 'badge-success' : 'badge-danger'}`}>
                                        {user.is_active ? 'Active' : 'Inactive'}
                                    </span>
                                </td>
                                <td>
                                    <button
                                        className="btn btn-danger btn-sm"
                                        onClick={() => handleDeleteUser(user.id)}
                                    >
                                        Delete
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Create User Modal */}
            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal glass-card" onClick={e => e.stopPropagation()}>
                        <h3>Create New User</h3>
                        <form onSubmit={handleCreateUser}>
                            <div className="form-group">
                                <label className="form-label">Name</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    value={formData.name}
                                    onChange={e => setFormData(prev => ({ ...prev, name: e.target.value }))}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Email</label>
                                <input
                                    type="email"
                                    className="form-input"
                                    value={formData.email}
                                    onChange={e => setFormData(prev => ({ ...prev, email: e.target.value }))}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Password</label>
                                <input
                                    type="password"
                                    className="form-input"
                                    value={formData.password}
                                    onChange={e => setFormData(prev => ({ ...prev, password: e.target.value }))}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Role</label>
                                <select
                                    className="form-select"
                                    value={formData.role}
                                    onChange={e => setFormData(prev => ({ ...prev, role: e.target.value }))}
                                >
                                    <option value="user">User</option>
                                    <option value="manager">Manager</option>
                                    <option value="admin">Admin</option>
                                </select>
                            </div>
                            <div className="modal-actions">
                                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>
                                    Cancel
                                </button>
                                <button type="submit" className="btn btn-primary">
                                    Create User
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
