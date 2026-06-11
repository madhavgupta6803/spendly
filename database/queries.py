from datetime import datetime

from database.db import get_db


def get_user_by_id(user_id):
    conn = get_db()
    row = conn.execute(
        "SELECT name, email, created_at FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    member_since = datetime.strptime(row["created_at"][:10], "%Y-%m-%d").strftime("%B %Y")
    return {"name": row["name"], "email": row["email"], "member_since": member_since}


def get_summary_stats(user_id):
    # Implemented by Subagent 2
    pass


def get_recent_transactions(user_id, limit=10):
    # Implemented by Subagent 1
    pass


def get_category_breakdown(user_id):
    # Implemented by Subagent 3
    pass
