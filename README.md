# Personal Finance Manager

A Flask + SQLite web app to track income, expenses, budgets, and view reports.

## Features
- User registration & login (passwords hashed, not stored in plain text)
- Dashboard with Total Income, Total Expense, Savings, and Budget Used
- Add Income (amount, source, date, description)
- Add Expense (amount, category, date, description)
- Monthly budget with an over-budget warning
- Reports page with Income vs Expense and Expenses by Category charts

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the app:
   ```
   python app.py
   ```

3. Open your browser at `http://127.0.0.1:5000`

The database (`finance.db`) is created automatically on first run — no manual setup needed.

## Project Structure
```
personal_finance_dashboard/
├── app.py                 # Flask routes
├── models.py               # SQLAlchemy models (User, Income, Expense, Budget)
├── requirements.txt
├── static/
│   └── css/style.css
└── templates/
    ├── base.html            # shared sidebar layout
    ├── register.html
    ├── login.html
    ├── dashboard.html
    ├── add_income.html
    ├── add_expense.html
    ├── budget.html
    └── reports.html
```

## Deploying to Render (free, for your portfolio)

1. Push this project to a GitHub repo.
2. Go to [render.com](https://render.com) → sign in with GitHub → **New +** → **Web Service**.
3. Select your repo. Render should auto-detect Python.
4. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Click **Create Web Service**. You'll get a live URL like `https://your-app.onrender.com`.

Notes:
- The free tier spins down after inactivity, so the first load after idle time can take ~30-50 seconds — that's normal, not a bug.
- SQLite resets on each redeploy on Render's free tier. For a portfolio demo this is usually fine; for persistent data, swap in Render's free PostgreSQL add-on later.

## Ideas to extend
- Edit/delete individual transactions
- Filter transactions by date range or category
- Export reports to CSV/PDF
- Recurring transactions (e.g. monthly rent)
- Multiple budgets per category instead of one overall budget
