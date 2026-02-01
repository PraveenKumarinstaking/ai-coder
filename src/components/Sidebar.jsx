import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Sidebar.css';

export default function Sidebar() {
    const { user, logout, isManager, isAdmin } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const menuItems = [
        { path: '/dashboard', icon: '🏠', label: 'Dashboard' },
        { path: '/tasks', icon: '📋', label: 'My Tasks' },
        { path: '/create-task', icon: '➕', label: 'Create Task' },
    ];

    if (isManager()) {
        menuItems.push({ path: '/manager', icon: '📊', label: 'Manager Panel' });
    }

    menuItems.push(
        { path: '/notifications', icon: '🔔', label: 'Notifications' },
        { path: '/audit-logs', icon: '📜', label: 'Audit Logs' }
    );

    if (isAdmin()) {
        menuItems.push({ path: '/admin', icon: '⚙️', label: 'Admin Panel' });
    }

    return (
        <aside className="sidebar">
            <div className="sidebar-header">
                <div className="logo">
                    <span className="logo-icon">🤖</span>
                    <div className="logo-text">
                        <span className="logo-title">ERP AI</span>
                        <span className="logo-subtitle">Task System</span>
                    </div>
                </div>
            </div>

            <nav className="sidebar-nav">
                <ul className="nav-list">
                    {menuItems.map((item) => (
                        <li key={item.path}>
                            <NavLink
                                to={item.path}
                                className={({ isActive }) =>
                                    `nav-link ${isActive ? 'active' : ''}`
                                }
                            >
                                <span className="nav-icon">{item.icon}</span>
                                <span className="nav-label">{item.label}</span>
                            </NavLink>
                        </li>
                    ))}
                </ul>
            </nav>

            <div className="sidebar-footer">
                <div className="user-info">
                    <div className="user-avatar">
                        {user?.name?.charAt(0).toUpperCase() || 'U'}
                    </div>
                    <div className="user-details">
                        <span className="user-name">{user?.name || 'User'}</span>
                        <span className="user-role">{user?.role || 'user'}</span>
                    </div>
                </div>
                <button className="logout-btn" onClick={handleLogout}>
                    🚪 Logout
                </button>
            </div>
        </aside>
    );
}
