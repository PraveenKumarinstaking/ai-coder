import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import './Header.css';

export default function Header() {
    const { user } = useAuth();
    const [unreadCount, setUnreadCount] = useState(0);

    useEffect(() => {
        const fetchUnreadCount = async () => {
            try {
                const data = await api.getUnreadCount();
                setUnreadCount(data.unread_count);
            } catch (error) {
                console.error('Error fetching unread count:', error);
            }
        };

        fetchUnreadCount();
        const interval = setInterval(fetchUnreadCount, 30000); // Poll every 30 seconds

        return () => clearInterval(interval);
    }, []);

    return (
        <header className="header">
            <div className="header-left">
                <h2 className="page-greeting">
                    Welcome back, <span>{user?.name?.split(' ')[0] || 'User'}</span>!
                </h2>
            </div>

            <div className="header-right">
                <Link to="/notifications" className="notification-btn">
                    <span className="notification-icon">🔔</span>
                    {unreadCount > 0 && (
                        <span className="notification-badge">{unreadCount}</span>
                    )}
                </Link>

                <div className="header-user">
                    <div className="header-avatar">
                        {user?.name?.charAt(0).toUpperCase() || 'U'}
                    </div>
                    <span className="header-role">{user?.role}</span>
                </div>
            </div>
        </header>
    );
}
