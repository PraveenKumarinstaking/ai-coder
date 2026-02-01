# ERP-Grade Agentic AI Task Management System

An enterprise-ready task and workflow management system featuring autonomous AI agents for prioritization, risk assessment, and real-time monitoring.

## 🚀 Key Features

- **Autonomous AI Agents**: Six specialized agents (Planning, Risk, Notification, Escalation, etc.) that manage tasks automatically.
- **Real-Time Updates**: System-wide WebSocket integration ensures that dashboard stats, notifications, and logs update instantly across all users.
- **Direct Messaging**: Role-agnostic messaging system allowing any user to send targeted notifications or system-wide broadcasts.
- **AI-Powered Insights**: Real-time task priority scoring and risk assessment with visual indicators.
- **Comprehensive Audit Logs**: Every action is tracked and visible in a live timeline.
- **Enterprise UI**: Sleek Glassmorphism design with professional role-based dashboards.

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python), SQLAlchemy, SQLite, APScheduler, WebSockets.
- **Frontend**: React (Vite), CSS3 (Vanilla), Chart.js.
- **Deployment**: Docker, Docker Compose, Nginx.

## 🚦 Quick Start

### Using Docker (Recommended)
```bash
docker-compose up --build -d
```
- **Frontend**: http://localhost
- **Backend**: http://localhost:8000

### Manual Setup
Refer to the [Deployment Guide](./deployment_guide.md) for detailed local setup instructions.

## 📂 Project Structure

- `/backend`: FastAPI application, models, agents, and database.
- `/frontend`: React source code, components, and assets.
- `docker-compose.yml`: Container orchestration for production.
- `inspect_db.py`: CLI utility for database inspection.

## 🔐 Demo Credentials
- **Admin**: `admin@erp.com` / `admin123`
- **Manager**: `manager@erp.com` / `manager123`
- **User**: `user@erp.com` / `user123`
