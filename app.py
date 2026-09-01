import os
from datetime import datetime, date
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from models import db, User, Income, Expense, Budget

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-key-change-in-production"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'finance.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

INCOME_SOURCES = ["Salary", "Freelance", "Business", "Investment", "Gift", "Other"]
EXPENSE_CATEGORIES = ["Food", "Rent", "Transport", "Utilities", "Healthcare", "Entertainment", "Shopping", "Education", "Other"]


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def current_user():
    uid = session.get("user_id")
    return db.session.get(User, uid) if uid else None


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# ---------- Auth ----------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Fill in all fields to continue.", "error")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "error")
            return render_template("register.html")

        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        budget = Budget(user_id=user.id, monthly_amount=0)
        db.session.add(budget)
        db.session.commit()

        session["user_id"] = user.id
        flash("Account created. Welcome in.", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))

        flash("That email or password doesn't match our records.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- Dashboard ----------

@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    total_income = sum(i.amount for i in user.incomes)
    total_expense = sum(e.amount for e in user.expenses)
    savings = total_income - total_expense

    budget = user.budget
    budget_amount = budget.monthly_amount if budget else 0
    budget_used_pct = round((total_expense / budget_amount) * 100, 1) if budget_amount > 0 else 0

    recent = []
    for i in user.incomes:
        recent.append({"category": i.source, "date": i.date, "amount": i.amount, "type": "income"})
    for e in user.expenses:
        recent.append({"category": e.category, "date": e.date, "amount": e.amount, "type": "expense"})
    recent.sort(key=lambda x: x["date"], reverse=True)
    recent = recent[:6]

    return render_template(
        "dashboard.html",
        user=user,
        total_income=total_income,
        total_expense=total_expense,
        savings=savings,
        budget_amount=budget_amount,
        budget_used_pct=budget_used_pct,
        recent=recent,
    )


# ---------- Income ----------

@app.route("/add_income", methods=["GET", "POST"])
@login_required
def add_income():
    if request.method == "POST":
        try:
            amount = float(request.form.get("amount", 0))
        except ValueError:
            amount = 0
        source = request.form.get("source", "Other")
        date_str = request.form.get("date")
        description = request.form.get("description", "")

        entry_date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date.today()

        income = Income(
            user_id=session["user_id"],
            amount=amount,
            source=source,
            date=entry_date,
            description=description,
        )
        db.session.add(income)
        db.session.commit()
        flash("Income saved.", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_income.html", sources=INCOME_SOURCES, today=date.today().isoformat())


# ---------- Expense ----------

@app.route("/add_expense", methods=["GET", "POST"])
@login_required
def add_expense():
    if request.method == "POST":
        try:
            amount = float(request.form.get("amount", 0))
        except ValueError:
            amount = 0
        category = request.form.get("category", "Other")
        date_str = request.form.get("date")
        description = request.form.get("description", "")

        entry_date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date.today()

        expense = Expense(
            user_id=session["user_id"],
            amount=amount,
            category=category,
            date=entry_date,
            description=description,
        )
        db.session.add(expense)
        db.session.commit()
        flash("Expense saved.", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_expense.html", categories=EXPENSE_CATEGORIES, today=date.today().isoformat())


# ---------- Budget ----------

@app.route("/set_budget", methods=["GET", "POST"])
@login_required
def set_budget():
    user = current_user()
    budget = user.budget
    if not budget:
        budget = Budget(user_id=user.id, monthly_amount=0)
        db.session.add(budget)
        db.session.commit()

    if request.method == "POST":
        try:
            amount = float(request.form.get("monthly_amount", 0))
        except ValueError:
            amount = 0
        budget.monthly_amount = amount
        db.session.commit()
        flash("Budget updated.", "success")
        return redirect(url_for("set_budget"))

    total_expense = sum(e.amount for e in user.expenses)
    exceeded = budget.monthly_amount > 0 and total_expense > budget.monthly_amount

    return render_template(
        "budget.html",
        budget=budget,
        total_expense=total_expense,
        exceeded=exceeded,
    )


# ---------- Reports ----------

@app.route("/reports")
@login_required
def reports():
    user = current_user()
    total_income = sum(i.amount for i in user.incomes)
    total_expense = sum(e.amount for e in user.expenses)
    savings = total_income - total_expense

    category_totals = {}
    for e in user.expenses:
        category_totals[e.category] = category_totals.get(e.category, 0) + e.amount

    return render_template(
        "reports.html",
        total_income=total_income,
        total_expense=total_expense,
        savings=savings,
        category_labels=list(category_totals.keys()),
        category_values=list(category_totals.values()),
    )


if __name__ == "__main__":
    app.run(debug=True)
