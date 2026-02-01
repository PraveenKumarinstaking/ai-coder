import { useState, useEffect } from 'react';
import { api } from '../api/client';
import './AuditLogs.css';

export default function AuditLogs() {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState({ action: '', entity_type: '', days: 7 });

    useEffect(() => {
        fetchLogs();
    }, [filter]);

    useEffect(() => {
        const socket = new WebSocket('ws://localhost:8000/ws');

        socket.onmessage = (event) => {
            const message = JSON.parse(event.data);
            if (message.type === 'AUDIT_LOG') {
                const newLog = message.data;

                // Only add if it matches current entity_type filter
                if (!filter.entity_type || newLog.entity_type === filter.entity_type) {
                    setLogs(prevLogs => [newLog, ...prevLogs.slice(0, 99)]);
                }
            }
        };

        socket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        return () => {
            socket.close();
        };
    }, [filter.entity_type]);

    const fetchLogs = async () => {
        try {
            const data = await api.getAuditLogs(filter);
            setLogs(data);
        } catch (error) {
            console.error('Error fetching audit logs:', error);
        } finally {
            setLoading(false);
        }
    };

    const formatTime = (dateString) => {
        return new Date(dateString).toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getActionIcon = (action) => {
        if (action.includes('created')) return '➕';
        if (action.includes('deleted')) return '🗑️';
        if (action.includes('updated') || action.includes('changed')) return '✏️';
        if (action.includes('login')) return '🔐';
        if (action.includes('escalated')) return '🚨';
        if (action.includes('risk')) return '⚠️';
        return '📋';
    };

    if (loading) {
        return <div className="loading"><div className="spinner"></div></div>;
    }

    return (
        <div className="audit-logs-page">
            <div className="page-header">
                <h1>Audit Logs</h1>
                <p>Track all actions and AI agent activities</p>
            </div>

            <div className="glass-card">
                <div className="audit-toolbar">
                    <div className="filters">
                        <select
                            className="form-select filter-select"
                            value={filter.entity_type}
                            onChange={(e) => setFilter(prev => ({ ...prev, entity_type: e.target.value }))}
                        >
                            <option value="">All Entities</option>
                            <option value="task">Tasks</option>
                            <option value="user">Users</option>
                            <option value="notification">Notifications</option>
                        </select>

                        <select
                            className="form-select filter-select"
                            value={filter.days}
                            onChange={(e) => setFilter(prev => ({ ...prev, days: parseInt(e.target.value) }))}
                        >
                            <option value="1">Last 24 hours</option>
                            <option value="7">Last 7 days</option>
                            <option value="30">Last 30 days</option>
                        </select>
                    </div>

                    <div className="log-count">
                        {logs.length} entries found
                    </div>
                </div>

                {logs.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-state-icon">📜</div>
                        <p>No audit logs found</p>
                    </div>
                ) : (
                    <div className="logs-timeline">
                        {logs.map((log) => (
                            <div key={log.id} className="log-entry">
                                <div className="log-icon">
                                    {getActionIcon(log.action)}
                                </div>
                                <div className="log-content">
                                    <div className="log-header">
                                        <span className="log-action">{log.action.replace(/_/g, ' ')}</span>
                                        {log.agent_involved && (
                                            <span className="badge badge-primary">
                                                🤖 {log.agent_involved}
                                            </span>
                                        )}
                                    </div>
                                    <p className="log-details">{log.details}</p>
                                    <div className="log-meta">
                                        <span className="log-user">
                                            👤 {log.user?.name || 'System'}
                                        </span>
                                        <span className="badge badge-info">{log.entity_type}</span>
                                        <span className="log-time">{formatTime(log.timestamp)}</span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
