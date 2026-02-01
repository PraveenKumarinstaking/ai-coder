import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute, PublicRoute } from './components/RouteGuards';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Tasks from './pages/Tasks';
import CreateTask from './pages/CreateTask';
import TaskDetail from './pages/TaskDetail';
import ManagerDashboard from './pages/ManagerDashboard';
import Notifications from './pages/Notifications';
import AuditLogs from './pages/AuditLogs';
import AdminPanel from './pages/AdminPanel';
import './index.css';

export default function App() {
    return (
        <AuthProvider>
            <BrowserRouter>
                <Routes>
                    {/* Public Routes */}
                    <Route
                        path="/login"
                        element={
                            <PublicRoute>
                                <Login />
                            </PublicRoute>
                        }
                    />

                    {/* Protected Routes */}
                    <Route
                        element={
                            <ProtectedRoute>
                                <Layout />
                            </ProtectedRoute>
                        }
                    >
                        <Route path="/dashboard" element={<Dashboard />} />
                        <Route path="/tasks" element={<Tasks />} />
                        <Route path="/tasks/:id" element={<TaskDetail />} />
                        <Route path="/create-task" element={<CreateTask />} />
                        <Route path="/notifications" element={<Notifications />} />
                        <Route path="/audit-logs" element={<AuditLogs />} />

                        {/* Manager Routes */}
                        <Route
                            path="/manager"
                            element={
                                <ProtectedRoute allowedRoles={['admin', 'manager']}>
                                    <ManagerDashboard />
                                </ProtectedRoute>
                            }
                        />

                        {/* Admin Routes */}
                        <Route
                            path="/admin"
                            element={
                                <ProtectedRoute allowedRoles={['admin']}>
                                    <AdminPanel />
                                </ProtectedRoute>
                            }
                        />
                    </Route>

                    {/* Default redirect */}
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                    <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Routes>
            </BrowserRouter>
        </AuthProvider>
    );
}
