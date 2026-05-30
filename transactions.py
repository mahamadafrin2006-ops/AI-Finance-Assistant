from datetime import datetime
import sqlite3
def add_transaction(user_id):
    transaction_type = input("Enter Type (Income/Expense): ").strip().lower()
    if transaction_type not in ["income", "expense"]:
        print("Invalid type. Please enter Income or Expense.")
        return
    category = input("Enter Category: ").strip().lower()
    try:
        amount = float(input("Enter Amount: "))
    except ValueError:
        print("Invalid amount entered")
        return
    date = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    # ---------------- INSERT TRANSACTION ----------------
    cursor.execute("""
    INSERT INTO transactions (user_id, type, category, amount, date)
    VALUES (?, ?, ?, ?, ?)
    """, (user_id, transaction_type, category, amount, date))
    conn.commit()
    if transaction_type == "expense":
        cursor.execute("""
        SELECT limit_amount FROM budgets WHERE category=? AND user_id=?
        """, (category,user_id))
        budget = cursor.fetchone()
        if budget:
            limit_amount = budget[0]
            cursor.execute("""
            SELECT SUM(amount) FROM transactions
            WHERE category=? AND type='expense' AND user_id=?
            """, (category,user_id))
            total_spent = cursor.fetchone()[0] or 0
            if total_spent > limit_amount:
                print("\n⚠ WARNING: Budget Exceeded!")
                print("Category:", category)
                print("Limit:", limit_amount)
                print("Spent:", total_spent)
    conn.close()
    print("Transaction Added Successfully")

def view_transactions(user_id):
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM transactions WHERE user_id=?",
        (user_id,)
    )
    data = cursor.fetchall()
    conn.close()
    print("\nTransactions:\n")
    for row in data:
        print("ID:", row[0])
        print("Type:", row[1])
        print("Category:", row[2])
        print("Amount:", row[3])
        print("Date:",row[4])
        print("----------------------")

def view_balance(user_id):
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT type, category, amount FROM transactions WHERE user_id=?",
        (user_id,)
    )
    data = cursor.fetchall()
    conn.close()
    income = 0
    expense = 0
    category_spending = {}
    for row in data:
        t_type = row[0]
        category = row[1]
        amount = row[2]
        if t_type.lower() == "income":
            income += amount
        elif t_type.lower() == "expense":
            expense += amount
            # category tracking
            if category in category_spending:
                category_spending[category] += amount
            else:
                category_spending[category] = amount
    balance = income - expense
    print("\n===== FINANCIAL REPORT =====")
    print("Total Income:", income)
    print("Total Expense:", expense)
    print("Net Balance:", balance)
    print("\n--- Category Spending ---")
    for cat, amt in category_spending.items():
        print(cat, ":", amt)

def delete_transaction(user_id):
    transaction_id = input("Enter Transaction ID to Delete: ")
    confirm = input("Are you sure? (yes/no): ").lower()
    if confirm != "yes":
        print("Deletion Cancelled")
        return
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM transactions WHERE id=? AND user_id=?",
        (transaction_id,user_id)
    )
    conn.commit()
    conn.close()
    print("Transaction Deleted Successfully")

def update_transaction(user_id):
    transaction_id = input("Enter Transaction ID to Update: ")
    new_type = input("Enter New Type (Income/Expense): ").strip().lower()
    if new_type not in ["income", "expense"]:
        print("Invalid type. Please enter Income or Expense.")
        return
    new_category = input("Enter New Category: ").strip().lower()
    try:
        new_amount = float(input("Enter Amount: "))
    except ValueError:
        print("Invalid amount entered")
        return
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE transactions
    SET type = ?, category = ?, amount = ?
    WHERE id = ? AND user_id = ?
    """, (new_type, new_category, new_amount, transaction_id, user_id))
    conn.commit()
    conn.close()
    print("Transaction Updated Successfully")

def ask_ai(user_id, query):
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT type, category, amount FROM transactions WHERE user_id=?",
        (user_id,)
    )
    data = cursor.fetchall()
    conn.close()
    query = query.lower()
    income = 0
    expense = 0
    category_map = {}
    for t_type, category, amount in data:
        if t_type.lower() == "income":
            income += amount
        else:
            expense += amount
            category_map[category] = category_map.get(category, 0) + amount
    balance = income - expense
    # -------- SMART RESPONSES --------
    if "balance" in query:
        print(f"Your current balance is ₹{balance}")
    elif "income" in query:
        print(f"Total income is ₹{income}")
    elif "expense" in query:
        print(f"Total expense is ₹{expense}")
    elif "save" in query or "suggest" in query:
        if expense > income:
            print("You are spending more than you earn. Reduce expenses.")
        else:
            print("You are financially stable. You can increase savings.")
    elif "food" in query:
        print(f"You spent ₹{category_map.get('food', 0)} on Food")
    elif "travel" in query:
        print(f"You spent ₹{category_map.get('travel', 0)} on Travel")
    else:
        found = False
        for cat, amt in category_map.items():
            if cat.lower() in query:
                print(f"You spent ₹{amt} on {cat}")
                found = True
        if not found:
            print("Try asking: balance, income, expense, food, or savings advice")

def show_expense_chart(user_id):
    import sqlite3
    import matplotlib.pyplot as plt
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT category, amount, type FROM transactions WHERE user_id=?",
        (user_id,)
    )
    data = cursor.fetchall()
    conn.close()
    category_totals = {}
    for category, amount, t_type in data:
        # normalize EVERYTHING
        t_type = t_type.strip().lower()
        category = category.strip().title()
        if t_type == "expense":
            category_totals[category] = category_totals.get(category, 0) + amount
    if not category_totals:
        print("No expense data available for chart")
        return
    plt.figure()
    plt.pie(
        category_totals.values(),
        labels=category_totals.keys(),
        autopct="%1.1f%%"
    )
    plt.title("Expense Breakdown")
    plt.show()

def monthly_report(user_id):
    import sqlite3
    month = input("Enter month (YYYY-MM): ")
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    cursor.execute("""
    SELECT type, category, amount, date FROM transactions
    WHERE date LIKE ? AND user_id = ?
    """, (month + "%", user_id))
    data = cursor.fetchall()
    conn.close()
    income = 0
    expense = 0
    category_totals = {}
    for t_type, category, amount, date in data:
        if t_type.lower() == "income":
            income += amount
        else:
            expense += amount
            category_totals[category] = category_totals.get(category, 0) + amount
    print("\n===== MONTHLY REPORT =====")
    print("Month:", month)
    print("Income:", income)
    print("Expense:", expense)
    print("Savings:", income - expense)
    # category breakdown
    print("\n--- Category Breakdown ---")
    for cat, amt in category_totals.items():
        print(cat, ":", amt)

def show_income_expense_chart(user_id):
    import sqlite3
    import matplotlib.pyplot as plt
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT type, amount FROM transactions WHERE user_id=?",
        (user_id,)
    )
    data = cursor.fetchall()
    conn.close()
    income = 0
    expense = 0
    for t_type, amount in data:
        if t_type.lower() == "income":
            income += amount
        else:
            expense += amount
    labels = ["Income", "Expense"]
    values = [income, expense]
    plt.bar(labels, values)
    plt.title("Income vs Expense")
    plt.ylabel("Amount")
    plt.show()

def export_to_csv(user_id):
    import csv
    import sqlite3
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM transactions WHERE user_id=?",
        (user_id,)
    )
    data = cursor.fetchall()
    conn.close()
    with open("finance_report.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Type", "Category", "Amount", "Date"])
        writer.writerows(data)
    print("Report exported successfully")

def set_budget(user_id):
    category = input("Enter Category (e.g. food, travel): ").strip().lower()
    limit_amount = float(input("Enter Budget Limit: "))
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    # If budget already exists, update it
    cursor.execute("""
    SELECT id FROM budgets WHERE category=? AND user_id=?
    """, (category,user_id))
    existing = cursor.fetchone()
    if existing:
        cursor.execute("""
        UPDATE budgets
        SET limit_amount=?
        WHERE category=? AND user_id=?
        """, (limit_amount, category,user_id))
    else:
        cursor.execute("""
        INSERT INTO budgets (user_id, category, limit_amount)
        VALUES (?, ?, ?)
        """, (user_id, category, limit_amount))
    conn.commit()
    conn.close()
    print("Budget set successfully!")