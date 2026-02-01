import { useState, useEffect } from 'react';
import { api } from '../api/client';
import './Notifications.css';

export default function Notifications() {
    const [notifications, setNotifications] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('all');

    useEffect(() => {
        fetchNotifications();
    }, []);

    useEffect(() => {
        const socket = new WebSocket('ws://localhost:8000/ws');

        socket.onmessage = (event) => {
            const message = JSON.parse(event.data);
            if (message.type === 'NOTIFICATION_UPDATE') {
                const updatedNotif = message.data;
                setNotifications(prev => {
                    // Check if notification is for us or broadcast
                    // Simple logic: if it exists, update it; if not, add it
                    const exists = prev.find(n => n.id === updatedNotif.id);
                    if (exists) {
                        return prev.map(n => n.id === updatedNotif.id ? updatedNotif : n);
                    } else {
                        return [updatedNotif, ...prev.slice(0, 49)];
                    }
                });
            } else if (message.type === 'NOTIFICATION_DELETE') {
                const deletedId = message.data.id;
                setNotifications(prev => prev.filter(n => n.id !== deletedId));
            }
        };

        socket.onerror = (error) => {
            console.error('Notifications WebSocket error:', error);
        };

        return () => {
            socket.close();
        };
    }, []);

    const fetchNotifications = async () => {
        try {
            const data = await api.getNotifications();
            setNotifications(data);
        } catch (error) {
            console.error('Error fetching notifications:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleMarkRead = async (ids) => {
        try {
            await api.markNotificationsRead(ids);
            setNotifications(prev =>
                prev.map(n => ids.includes(n.id) ? { ...n, is_read: true } : n)
            );
        } catch (error) {
            console.error('Error marking notifications read:', error);
        }
    };

    const handleMarkAllRead = async () => {
        try {
            await api.markAllNotificationsRead();
            setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
        } catch (error) {
            console.error('Error marking all read:', error);
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm('Are you sure you want to delete this notification?')) return;
        try {
            await api.deleteNotification(id);
            setNotifications(prev => prev.filter(n => n.id !== id));
        } catch (error) {
            console.error('Error deleting notification:', error);
            alert('Failed to delete notification');
        }
    };

    const getIcon = (type) => {
        switch (type) {
            case 'reminder': return '🔔';
            case 'escalation': return '🚨';
            case 'alert': return '⚠️';
            default: return '📬';
        }
    };

    const getTypeClass = (type) => {
        switch (type) {
            case 'escalation': return 'danger';
            case 'alert': return 'warning';
            case 'reminder': return 'info';
            default: return 'primary';
        }
    };

    const formatTime = (dateString) => {
        const date = new Date(dateString);
        const now = new Date();
        const diff = (now - date) / 1000;

        if (diff < 60) return 'Just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return date.toLocaleDateString();
    };

    const filteredNotifications = notifications.filter(n => {
        if (filter === 'unread') return !n.is_read;
        if (filter === 'read') return n.is_read;
        return true;
    });

    const unreadCount = notifications.filter(n => !n.is_read).length;

    const [showCompose, setShowCompose] = useState(false);
    const [newMessage, setNewMessage] = useState({
        message: '',
        type: 'alert',
        channel: 'desktop',
        recipient_email: ''
    });
    const [users, setUsers] = useState([]);

    useEffect(() => {
        if (showCompose) {
            fetchUsers();
        }
    }, [showCompose]);

    const fetchUsers = async () => {
        try {
            const data = await api.getUsers();
            setUsers(data);
        } catch (error) {
            console.error('Error fetching users:', error);
        }
    };

    const handleSend = async (e) => {
        e.preventDefault();
        try {
            const payload = { ...newMessage };
            if (!payload.recipient_email) delete payload.recipient_email;

            await api.sendBroadcastNotification(payload);
            setShowCompose(false);
            setNewMessage({ message: '', type: 'alert', channel: 'desktop', recipient_email: '' });
            fetchNotifications();
            alert(`Message sent to ${payload.recipient_email ? payload.recipient_email : 'all users'}!`);
        } catch (error) {
            console.error('Error sending message:', error);
            alert('Failed to send message');
        }
    };

    if (loading) {
        return <div className="loading"><div className="spinner"></div></div>;
    }

    return (
        <div className="notifications-page">
            <div className="page-header">
                <h1>Notifications</h1>
                <p>Stay updated with task reminders and AI alerts</p>
            </div>

            <div className="glass-card">
                <div className="notifications-toolbar">
                    <div className="filter-tabs">
                        <button
                            className={`tab ${filter === 'all' ? 'active' : ''}`}
                            onClick={() => setFilter('all')}
                        >
                            All ({notifications.length})
                        </button>
                        <button
                            className={`tab ${filter === 'unread' ? 'active' : ''}`}
                            onClick={() => setFilter('unread')}
                        >
                            Unread ({unreadCount})
                        </button>
                        <button
                            className={`tab ${filter === 'read' ? 'active' : ''}`}
                            onClick={() => setFilter('read')}
                        >
                            Read
                        </button>
                    </div>

                    <div className="toolbar-actions">
                        <button className="btn btn-primary" onClick={() => setShowCompose(true)}>
                            📢 Send Message
                        </button>
                        {unreadCount > 0 && (
                            <button className="btn btn-secondary" onClick={handleMarkAllRead}>
                                ✅ Mark All Read
                            </button>
                        )}
                    </div>
                </div>

                {showCompose && (
                    <div className="modal-overlay">
                        <div className="modal-content glass-card">
                            <h2>Send Message</h2>
                            <form onSubmit={handleSend}>
                                <div className="form-group">
                                    <label>Recipient</label>
                                    <select
                                        value={newMessage.recipient_email}
                                        onChange={(e) => setNewMessage({ ...newMessage, recipient_email: e.target.value })}
                                    >
                                        <option value="">All Users (Broadcast)</option>
                                        {users.map(user => (
                                            <option key={user.id} value={user.email}>
                                                {user.name} ({user.email})
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label>Message</label>
                                    <textarea
                                        value={newMessage.message}
                                        onChange={(e) => setNewMessage({ ...newMessage, message: e.target.value })}
                                        required
                                        placeholder="Enter notification message..."
                                    />
                                </div>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label>Type</label>
                                        <select
                                            value={newMessage.type}
                                            onChange={(e) => setNewMessage({ ...newMessage, type: e.target.value })}
                                        >
                                            <option value="alert">Alert ⚠️</option>
                                            <option value="reminder">Reminder 🔔</option>
                                            <option value="escalation">Escalation 🚨</option>
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label>Channel</label>
                                        <select
                                            value={newMessage.channel}
                                            onChange={(e) => setNewMessage({ ...newMessage, channel: e.target.value })}
                                        >
                                            <option value="desktop">Desktop</option>
                                            <option value="email">Email</option>
                                            <option value="both">Both</option>
                                        </select>
                                    </div>
                                </div>
                                <div className="modal-actions">
                                    <button type="button" className="btn btn-secondary" onClick={() => setShowCompose(false)}>Cancel</button>
                                    <button type="submit" className="btn btn-primary">Send to All</button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}

                {filteredNotifications.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-state-icon">🔔</div>
                        <p>No notifications</p>
                    </div>
                ) : (
                    <div className="notifications-list">
                        {filteredNotifications.map(notification => (
                            <div
                                key={notification.id}
                                className={`notification-item ${!notification.is_read ? 'unread' : ''}`}
                            >
                                <div className={`notification-icon ${getTypeClass(notification.type)}`}>
                                    {getIcon(notification.type)}
                                </div>
                                <div className="notification-content">
                                    <p className="notification-message">{notification.message}</p>
                                    <div className="notification-meta">
                                        <span className={`badge badge-${getTypeClass(notification.type)}`}>
                                            {notification.type}
                                        </span>
                                        <span className="notification-channel">
                                            {notification.channel === 'email' ? '📧' : '🖥️'} {notification.channel}
                                        </span>
                                        <span className="notification-time">
                                            {formatTime(notification.created_at)}
                                        </span>
                                    </div>
                                </div>
                                <div className="notification-actions">
                                    {!notification.is_read && (
                                        <button
                                            className="action-btn mark-read"
                                            onClick={() => handleMarkRead([notification.id])}
                                            title="Mark as read"
                                        >
                                            ✅
                                        </button>
                                    )}
                                    <button
                                        className="action-btn delete-btn"
                                        onClick={() => handleDelete(notification.id)}
                                        title="Delete notification"
                                    >
                                        🗑️
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
