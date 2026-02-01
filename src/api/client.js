/**
 * API Client - Fetch wrapper with authentication
 */

const API_BASE = 'http://localhost:8000/api';

class ApiClient {
    constructor() {
        this.baseUrl = API_BASE;
    }

    getToken() {
        return localStorage.getItem('token');
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const token = this.getToken();

        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers,
            });

            // Handle 401 - Unauthorized
            if (response.status === 401) {
                localStorage.removeItem('token');
                localStorage.removeItem('user');
                window.location.href = '/login';
                throw new Error('Session expired. Please login again.');
            }

            // Handle other errors
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'An error occurred');
            }

            // Handle empty responses
            if (response.status === 204) {
                return null;
            }

            return response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Auth endpoints
    async login(email, password) {
        const response = await this.request('/users/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
        return response;
    }

    async register(userData) {
        return this.request('/users/register', {
            method: 'POST',
            body: JSON.stringify(userData),
        });
    }

    async getCurrentUser() {
        return this.request('/users/me');
    }

    // Users endpoints
    async getUsers() {
        return this.request('/users/');
    }

    async updateUser(userId, data) {
        return this.request(`/users/${userId}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    async deleteUser(userId) {
        return this.request(`/users/${userId}`, {
            method: 'DELETE',
        });
    }

    // Tasks endpoints
    async getTasks(filters = {}) {
        const params = new URLSearchParams(filters).toString();
        return this.request(`/tasks/${params ? `?${params}` : ''}`);
    }

    async getMyTasks() {
        return this.request('/tasks/my-tasks');
    }

    async getTask(taskId) {
        return this.request(`/tasks/${taskId}`);
    }

    async createTask(taskData) {
        return this.request('/tasks/', {
            method: 'POST',
            body: JSON.stringify(taskData),
        });
    }

    async updateTask(taskId, taskData) {
        return this.request(`/tasks/${taskId}`, {
            method: 'PUT',
            body: JSON.stringify(taskData),
        });
    }

    async updateTaskStatus(taskId, status) {
        return this.request(`/tasks/${taskId}/status`, {
            method: 'PATCH',
            body: JSON.stringify({ status }),
        });
    }

    async deleteTask(taskId) {
        return this.request(`/tasks/${taskId}`, {
            method: 'DELETE',
        });
    }

    async getDashboardStats() {
        return this.request('/tasks/dashboard-stats');
    }

    async getManagerStats() {
        return this.request('/tasks/manager-stats');
    }

    async getHighRiskTasks() {
        return this.request('/tasks/high-risk');
    }

    async getOverdueTasks() {
        return this.request('/tasks/overdue');
    }

    // Notifications endpoints
    async getNotifications(unreadOnly = false) {
        return this.request(`/notifications/?unread_only=${unreadOnly}`);
    }

    async getUnreadCount() {
        return this.request('/notifications/unread-count');
    }

    async markNotificationsRead(notificationIds) {
        return this.request('/notifications/mark-read', {
            method: 'POST',
            body: JSON.stringify({ notification_ids: notificationIds }),
        });
    }

    async markAllNotificationsRead() {
        return this.request('/notifications/mark-all-read', {
            method: 'POST',
        });
    }

    async sendBroadcastNotification(data) {
        return this.request('/notifications/send-to-all', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async deleteNotification(notificationId) {
        return this.request(`/notifications/${notificationId}`, {
            method: 'DELETE',
        });
    }

    // Audit endpoints
    async getAuditLogs(filters = {}) {
        const params = new URLSearchParams(filters).toString();
        return this.request(`/audit/${params ? `?${params}` : ''}`);
    }

    async getAgentActions(agentName = null) {
        const params = agentName ? `?agent_name=${agentName}` : '';
        return this.request(`/audit/agent-actions${params}`);
    }

    async getAgentStatus() {
        return this.request('/audit/agents/status');
    }

    // Health check
    async healthCheck() {
        return this.request('/health');
    }
}

export const api = new ApiClient();
export default api;
