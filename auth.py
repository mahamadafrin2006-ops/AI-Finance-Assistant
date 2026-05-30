import sqlite3
import hashlib
# ---------------- REGISTER ----------------
def register():
    username = input("Enter Username: ")
    password = input("Enter Password: ")
    # 🔐 HASH PASSWORD
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (username, hashed_password)
    )
    conn.commit()
    conn.close()
    print("Registration Successful")
# ---------------- LOGIN ----------------
def login():
    username = input("Enter Username: ")
    password = input("Enter Password: ")
    # 🔐 HASH INPUT PASSWORD
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, hashed_password)
    )
    user = cursor.fetchone()
    conn.close()
    if user:
        return user
    else:
        return None