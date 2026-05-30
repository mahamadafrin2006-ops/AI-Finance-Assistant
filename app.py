import csv
import hashlib
import io
import os
import sqlite3
from datetime import datetime

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from database import create_tables

app = Flask(__name__)
app.secret_key = os.urandom(24)

create_tables()


def get_db():
    conn = sqlite3.connect("finance.db")
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def get_user(username):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


def login_required():
    return session.get("user_id") is not None


def get_transactions(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC, id DESC",
        (user_id,),
    )
    transactions = cursor.fetchall()
    conn.close()
    return transactions


def get_budget(user_id, category):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM budgets WHERE user_id = ? AND category = ?",
        (user_id, category.lower()),
    )
    budget = cursor.fetchone()
    conn.close()
    return budget


def get_budget_summary(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT category, limit_amount FROM budgets WHERE user_id = ?",
        (user_id,),
    )
    budgets = cursor.fetchall()
    conn.close()
    return budgets


def get_financial_summary(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT type, category, amount FROM transactions WHERE user_id = ?",
        (user_id,),
    )
    data = cursor.fetchall()
    conn.close()

    income = 0.0
    expense = 0.0
    category_breakdown = {}

    for item in data:
        t_type = item["type"].strip().lower()
        category = item["category"].strip().title()
        amount = float(item["amount"])
        if t_type == "income":
            income += amount
        else:
            expense += amount
            category_breakdown[category] = category_breakdown.get(category, 0.0) + amount

    balance = income - expense
    return {
        "income": income,
        "expense": expense,
        "balance": balance,
        "category_breakdown": category_breakdown,
    }


def get_monthly_report(user_id, month):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT type, category, amount FROM transactions WHERE date LIKE ? AND user_id = ?",
        (month + "%", user_id),
    )
    data = cursor.fetchall()
    conn.close()

    income = 0.0
    expense = 0.0
    category_breakdown = {}

    for item in data:
        t_type = item["type"].strip().lower()
        category = item["category"].strip().title()
        amount = float(item["amount"])
        if t_type == "income":
            income += amount
        else:
            expense += amount
            category_breakdown[category] = category_breakdown.get(category, 0.0) + amount

    return {
        "month": month,
        "income": income,
        "expense": expense,
        "savings": income - expense,
        "category_breakdown": category_breakdown,
    }


def ask_ai_response(user_id, query):
    summary = get_financial_summary(user_id)
    balance = summary["balance"]
    income = summary["income"]
    expense = summary["expense"]
    category_map = {k.lower(): v for k, v in summary["category_breakdown"].items()}

    query_text = query.lower()
    if "balance" in query_text:
        return f"Your current balance is ₹{balance:.2f}."
    if "income" in query_text:
        return f"Total income is ₹{income:.2f}."
    if "expense" in query_text:
        return f"Total expense is ₹{expense:.2f}."
    if "save" in query_text or "suggest" in query_text:
        if expense > income:
            return "You are spending more than you earn. Consider reducing discretionary expenses."
        return "Your finances look stable. You can increase savings or invest more."
    for category, amount in category_map.items():
        if category in query_text:
            return f"You spent ₹{amount:.2f} on {category.title()}."
    return "Try asking about balance, income, expense, savings advice, or a specific category."


@app.route("/")
def dashboard():
    if not login_required():
        return redirect(url_for("login"))

    user_id = session["user_id"]
    user = get_user_by_id(user_id)
    summary = get_financial_summary(user_id)
    budgets = get_budget_summary(user_id)
    warnings = []

    for budget in budgets:
        category = budget["category"].strip().lower()
        limit_amount = float(budget["limit_amount"])
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = 'expense' AND category = ?",
            (user_id, category),
        )
        total_spent = float(cursor.fetchone()[0] or 0.0)
        conn.close()
        if total_spent > limit_amount:
            warnings.append(
                {
                    "category": category.title(),
                    "limit": limit_amount,
                    "spent": total_spent,
                }
            )

    return render_template(
        "dashboard.html",
        user=user,
        summary=summary,
        warnings=warnings,
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.")
            return redirect(url_for("register"))

        existing = get_user(username)
        if existing:
            flash("Username already exists.")
            return redirect(url_for("register"))

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hash_password(password)),
        )
        conn.commit()
        conn.close()
        flash("Registration successful, please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_user(username)

        if not user or user["password"] != hash_password(password):
            flash("Invalid username or password.")
            return redirect(url_for("login"))

        session["user_id"] = user["id"]
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/transactions", methods=["GET", "POST"])
def transactions_view():
    if not login_required():
        return redirect(url_for("login"))

    user_id = session["user_id"]
    if request.method == "POST":
        t_type = request.form.get("type", "").strip().lower()
        category = request.form.get("category", "").strip().lower()
        amount = request.form.get("amount", "")

        if t_type not in ["income", "expense"]:
            flash("Type must be Income or Expense.")
            return redirect(url_for("transactions_view"))

        try:
            amount_value = float(amount)
        except ValueError:
            flash("Enter a valid amount.")
            return redirect(url_for("transactions_view"))

        date = datetime.now().strftime("%Y-%m-%d")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO transactions (user_id, type, category, amount, date) VALUES (?, ?, ?, ?, ?)",
            (user_id, t_type, category, amount_value, date),
        )
        conn.commit()
        conn.close()
        flash("Transaction added successfully.")
        return redirect(url_for("transactions_view"))

    transactions = get_transactions(user_id)
    return render_template("transactions.html", transactions=transactions)


@app.route("/transactions/<int:transaction_id>/delete")
def delete_transaction(transaction_id):
    if not login_required():
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM transactions WHERE id = ? AND user_id = ?",
        (transaction_id, user_id),
    )
    conn.commit()
    conn.close()
    flash("Transaction deleted successfully.")
    return redirect(url_for("transactions_view"))


@app.route("/transactions/<int:transaction_id>/update", methods=["GET", "POST"])
def update_transaction(transaction_id):
    if not login_required():
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM transactions WHERE id = ? AND user_id = ?",
        (transaction_id, user_id),
    )
    transaction = cursor.fetchone()

    if not transaction:
        conn.close()
        flash("Transaction not found.")
        return redirect(url_for("transactions_view"))

    if request.method == "POST":
        t_type = request.form.get("type", "").strip().lower()
        category = request.form.get("category", "").strip().lower()
        amount = request.form.get("amount", "")

        if t_type not in ["income", "expense"]:
            flash("Type must be Income or Expense.")
            return redirect(url_for("update_transaction", transaction_id=transaction_id))

        try:
            amount_value = float(amount)
        except ValueError:
            flash("Enter a valid amount.")
            return redirect(url_for("update_transaction", transaction_id=transaction_id))

        cursor.execute(
            "UPDATE transactions SET type = ?, category = ?, amount = ? WHERE id = ? AND user_id = ?",
            (t_type, category, amount_value, transaction_id, user_id),
        )
        conn.commit()
        conn.close()
        flash("Transaction updated successfully.")
        return redirect(url_for("transactions_view"))

    transactions = get_transactions(user_id)
    conn.close()
    return render_template("transactions.html", transactions=transactions, transaction=transaction)


@app.route("/budget", methods=["GET", "POST"])
def budget_page():
    if not login_required():
        return redirect(url_for("login"))

    user_id = session["user_id"]
    if request.method == "POST":
        category = request.form.get("category", "").strip().lower()
        limit_amount = request.form.get("limit_amount", "")

        if not category or not limit_amount:
            flash("Category and limit amount are required.")
            return redirect(url_for("budget_page"))

        try:
            limit_value = float(limit_amount)
        except ValueError:
            flash("Enter a valid budget limit.")
            return redirect(url_for("budget_page"))

        existing = get_budget(user_id, category)
        conn = get_db()
        cursor = conn.cursor()
        if existing:
            cursor.execute(
                "UPDATE budgets SET limit_amount = ? WHERE user_id = ? AND category = ?",
                (limit_value, user_id, category),
            )
        else:
            cursor.execute(
                "INSERT INTO budgets (user_id, category, limit_amount) VALUES (?, ?, ?)",
                (user_id, category, limit_value),
            )
        conn.commit()
        conn.close()
        flash("Budget saved successfully.")
        return redirect(url_for("budget_page"))

    budgets = get_budget_summary(user_id)
    return render_template("budget.html", budgets=budgets)


@app.route("/ask", methods=["GET", "POST"])
def ask_ai():
    if not login_required():
        return redirect(url_for("login"))

    answer = None
    if request.method == "POST":
        query = request.form.get("query", "").strip()
        if query:
            answer = ask_ai_response(session["user_id"], query)
        else:
            flash("Enter a question for the assistant.")

    return render_template("ask_ai.html", answer=answer)


@app.route("/export")
def export_csv():
    if not login_required():
        return redirect(url_for("login"))

    user_id = session["user_id"]
    transactions = get_transactions(user_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Type", "Category", "Amount", "Date"])
    for item in transactions:
        writer.writerow([item["id"], item["type"], item["category"], item["amount"], item["date"]])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        as_attachment=True,
        download_name="finance_report.csv",
        mimetype="text/csv",
    )


@app.route("/report", methods=["GET", "POST"])
def report_page():
    if not login_required():
        return redirect(url_for("login"))

    report = None
    if request.method == "POST":
        month = request.form.get("month", "").strip()
        if month:
            report = get_monthly_report(session["user_id"], month)
        else:
            flash("Enter a month in YYYY-MM format.")

    return render_template("report.html", report=report)


if __name__ == "__main__":
    app.run(debug=True)
