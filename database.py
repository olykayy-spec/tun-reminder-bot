import sqlite3

conn = sqlite3.connect("tasks.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    task TEXT,
    done INTEGER DEFAULT 0
)
""")

conn.commit()

def add_task(user_id, task):
    cursor.execute(
        "INSERT INTO tasks (user_id, task) VALUES (?, ?)",
        (user_id, task)
    )
    conn.commit()

def get_tasks(user_id):
    cursor.execute(
        "SELECT id, task FROM tasks WHERE user_id=? AND done=0",
        (user_id,)
    )
    return cursor.fetchall()

def mark_done(task_id):
    cursor.execute(
        "UPDATE tasks SET done=1 WHERE id=?",
        (task_id,)
    )
    conn.commit()
