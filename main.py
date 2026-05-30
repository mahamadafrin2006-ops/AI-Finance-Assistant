from auth import register, login
from transactions import (
    add_transaction,
    view_transactions,
    view_balance,
    delete_transaction,
    update_transaction,
    ask_ai,
    show_expense_chart,
    show_income_expense_chart,
    monthly_report,
    export_to_csv,
    set_budget
)
from database import create_tables
create_tables()
logged_in = False
current_user = None
while True:
    print("\n==============================")
    print("   AI FINANCE ASSISTANT")
    print("==============================")
    print("1. Register")
    print("2. Login")
    print("3. Add Transaction")
    print("4. View Transactions")
    print("5. View Balance")
    print("6. Delete Transaction")
    print("7. Update Transaction")
    print("8. Ask AI Assistant")
    print("9. Expense Pie Chart")
    print("10. Income vs Expense Chart")
    print("11. Monthly Report")
    print("12. Export Report (CSV)")
    print("13. Set Budget")
    print("14. Logout")
    print("15. Exit")
    choice = input("Enter your choice: ")
    if not choice.isdigit():
        print("Invalid input. Please enter a number.")
        continue

    # ---------------- AUTH ----------------

    if choice == "1":
        register()

    elif choice == "2":
        user = login()
        if user:
            print("Login successful!")
            logged_in = True
            current_user = user
        else:
            print("Login failed")

    # ---------------- TRANSACTIONS ----------------

    elif choice == "3":
        if logged_in:
            add_transaction(current_user[0])
        else:
            print("Please login first!")

    elif choice == "4":
        if logged_in:
            view_transactions(current_user[0])
        else:
            print("Please login first!")

    elif choice == "5":
        if logged_in:
            view_balance(current_user[0])
        else:
            print("Please login first!")

    elif choice == "6":
        if logged_in:
            delete_transaction(current_user[0])
        else:
            print("Please login first!")

    elif choice == "7":
        if logged_in:
            update_transaction(current_user[0])
        else:
            print("Please login first!")

    # ---------------- AI ----------------

    elif choice == "8":
        if logged_in:
            query = input("Ask your finance assistant: ")
            ask_ai(current_user[0],query)
        else:
            print("Please login first!")

    # ---------------- VISUALS ----------------

    elif choice == "9":
        if logged_in:
            show_expense_chart(current_user[0])
        else:
            print("Please login first!")

    elif choice == "10":
        if logged_in:
            show_income_expense_chart(current_user[0])
        else:
            print("Please login first!")

    # ---------------- REPORTS ----------------

    elif choice == "11":
        if logged_in:
            monthly_report(current_user[0])
        else:
            print("Please login first!")

    elif choice == "12":
        if logged_in:
            export_to_csv(current_user[0])
        else:
            print("Please login first!")

    elif choice == "13":
        if logged_in:
            set_budget(current_user[0])
        else:
            print("Please login first!")

    # ---------------- EXIT ----------------

    elif choice == "14":
        logged_in = False
        current_user = None
        print("Logged out successfully")

    elif choice == "15":
        print("Goodbye!")
        break

    else:
        print("Invalid choice")