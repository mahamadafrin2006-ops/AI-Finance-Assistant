import sqlite3
def create_tables():
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    # ---------------- USERS TABLE ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)
    # ---------------- TRANSACTIONS TABLE ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT,
        category TEXT,
        amount REAL,
        date DATE,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    # ---------------- BUDGETS TABLE ----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        category TEXT,
        limit_amount REAL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    # ---------------- INDEXES ----------------
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_budgets_user ON budgets(user_id)")
    conn.commit()
    conn.close()
    print("Database Tables Created Successfully")
