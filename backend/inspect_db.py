from database import SessionLocal
from models import User, Task, Notification, AuditLog, AgentStatus
import sys

def inspect_database():
    db = SessionLocal()
    try:
        # 1. Users (Login info)
        print("\n=== SYSTEM USERS (Login Credentials) ===")
        users = db.query(User).all()
        user_data = []
        for u in users:
            user_data.append([u.id, u.name, u.email, u.role, u.is_active])
        print(tabulate_data(["ID", "Name", "Email", "Role", "Active"], user_data))

        # 2. Tasks
        print("\n=== RECENT TASKS ===")
        tasks = db.query(Task).order_by(Task.created_at.desc()).limit(5).all()
        task_data = []
        for t in tasks:
            task_data.append([t.id, t.title[:20], t.priority, t.status, t.assigned_to])
        print(tabulate_data(["ID", "Title", "Priority", "Status", "Assignee ID"], task_data))

        # 3. Notifications
        print("\n=== RECENT NOTIFICATIONS ===")
        notifs = db.query(Notification).order_by(Notification.created_at.desc()).limit(5).all()
        notif_data = []
        for n in notifs:
            notif_data.append([n.id, n.type, n.message[:30], n.user_id, n.is_read])
        print(tabulate_data(["ID", "Type", "Message", "User ID", "Read"], notif_data))

        # 4. Agent Status
        print("\n=== AI AGENT STATUS ===")
        agents = db.query(AgentStatus).all()
        agent_data = []
        for a in agents:
            agent_data.append([a.agent_name, a.status, a.tasks_processed, a.last_run])
        print(tabulate_data(["Agent", "Status", "Tasks", "Last Run"], agent_data))

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

def tabulate_data(headers, rows):
    """Simple manual tabulation if tabulate isn't available"""
    try:
        from tabulate import tabulate
        return tabulate(rows, headers=headers, tablefmt="grid")
    except ImportError:
        # Manual formatting
        header_line = " | ".join(headers)
        separator = "-" * len(header_line)
        output = [header_line, separator]
        for row in rows:
            output.append(" | ".join(str(item) for item in row))
        return "\n".join(output)

if __name__ == "__main__":
    inspect_database()
