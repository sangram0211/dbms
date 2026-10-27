import os
import csv
import io
import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, 
    url_for, flash, session, jsonify, Response, send_file
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

from database.db import (
    query_db, execute_db, init_db, get_active_engine, 
    MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, MYSQL_USER
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_dev_secret_key_12345')

# Initialize DB on first load
with app.app_context():
    init_db()

CURRENCY_SYMBOLS = {
    'INR': '₹',
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
    'CAD': '$',
    'AUD': '$',
    'JPY': '¥',
}

# ---------------------------------------------------------------------
# Context Processors & Template Filters
# ---------------------------------------------------------------------
@app.context_processor
def inject_global_data():
    engine_name = get_active_engine().upper()
    user_id = session.get('user_id')
    user_cats = []
    user_pms = []
    curr_code = session.get('currency')

    if user_id:
        try:
            user_cats = query_db("""
                SELECT * FROM categories
                WHERE user_id IS NULL OR user_id = %s
                ORDER BY name ASC
            """, (user_id,))
            user_pms = query_db("SELECT * FROM payment_methods ORDER BY method_name ASC")
            
            # If currency not yet in session, read from DB
            if not curr_code:
                u_row = query_db("SELECT currency FROM users WHERE user_id = %s", (user_id,), one=True)
                if u_row and u_row.get('currency'):
                    curr_code = u_row['currency']
                    session['currency'] = curr_code
        except Exception:
            pass

    if not curr_code:
        curr_code = 'INR'

    curr_symbol = CURRENCY_SYMBOLS.get(curr_code, '₹')

    from database.db import get_mysql_last_error
    mysql_err = get_mysql_last_error()

    return {
        'now': datetime.datetime.now(),
        'today_date': datetime.date.today().strftime('%Y-%m-%d'),
        'active_engine': engine_name,
        'mysql_offline_error': mysql_err,
        'currency_code': curr_code,
        'currency_symbol': curr_symbol,
        'global_categories': user_cats,
        'global_payment_methods': user_pms,
        'categories': user_cats,
        'payment_methods': user_pms,
        'db_meta': {
            'engine': engine_name,
            'host': MYSQL_HOST,
            'port': MYSQL_PORT,
            'database': MYSQL_DATABASE,
            'user': MYSQL_USER
        }
    }

@app.template_filter('format_currency')
def format_currency(val, symbol=None):
    if symbol is None:
        curr_code = session.get('currency', 'INR')
        symbol = CURRENCY_SYMBOLS.get(curr_code, '₹')
    try:
        return f"{symbol}{float(val):,.2f}"
    except (ValueError, TypeError):
        return f"{symbol}0.00"

# ---------------------------------------------------------------------
# Auth Decorator
# ---------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ---------------------------------------------------------------------
# Authentication Routes
# ---------------------------------------------------------------------
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Please provide both username and password.', 'danger')
            return render_template('login.html')

        user = query_db(
            "SELECT * FROM users WHERE username = %s OR email = %s", 
            (username, username), 
            one=True
        )

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['currency'] = user.get('currency', 'USD')
            flash(f"Welcome back, {user['full_name']}!", 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username/email or password.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        currency = request.form.get('currency', 'USD').strip()

        if not full_name or not username or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('register.html')

        # Check existing user
        existing = query_db(
            "SELECT user_id FROM users WHERE username = %s OR email = %s",
            (username, email),
            one=True
        )
        if existing:
            flash('Username or Email already registered. Please log in or use another.', 'warning')
            return render_template('register.html')

        pwd_hash = generate_password_hash(password, method='pbkdf2:sha256')
        res = execute_db(
            "INSERT INTO users (username, email, password_hash, full_name, currency) VALUES (%s, %s, %s, %s, %s)",
            (username, email, pwd_hash, full_name, currency)
        )

        user_id = res['lastrowid']
        session['user_id'] = user_id
        session['username'] = username
        session['full_name'] = full_name
        session['currency'] = currency

        flash('Registration successful! Welcome to your Personal Expense Tracker.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been safely logged out.', 'info')
    return redirect(url_for('login'))

# ---------------------------------------------------------------------
# Dashboard Route
# ---------------------------------------------------------------------
@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    today = datetime.date.today()
    cur_year = today.year
    cur_month = today.month

    # KPI 1: Total spent this month
    this_month_spent = query_db("""
        SELECT COALESCE(SUM(amount), 0.0) AS total
        FROM expenses
        WHERE user_id = %s 
          AND YEAR(expense_date) = %s
          AND MONTH(expense_date) = %s
    """, (user_id, cur_year, cur_month), one=True)['total']

    # KPI 2: Today's spend
    today_spent = query_db("""
        SELECT COALESCE(SUM(amount), 0.0) AS total
        FROM expenses
        WHERE user_id = %s AND expense_date = %s
    """, (user_id, str(today)), one=True)['total']

    # KPI 3: Total year to date
    year_spent = query_db("""
        SELECT COALESCE(SUM(amount), 0.0) AS total
        FROM expenses
        WHERE user_id = %s AND YEAR(expense_date) = %s
    """, (user_id, cur_year), one=True)['total']

    # KPI 4: Total transactions
    total_tx = query_db("""
        SELECT COUNT(expense_id) AS cnt
        FROM expenses
        WHERE user_id = %s
    """, (user_id,), one=True)['cnt']

    # Recent 6 expenses (using View vw_expense_details)
    recent_expenses = query_db("""
        SELECT * FROM vw_expense_details
        WHERE user_id = %s
        ORDER BY expense_date DESC, expense_id DESC
        LIMIT 6
    """, (user_id,))

    # Category Breakdown for this month (using View vw_monthly_category_summary)
    category_summary = query_db("""
        SELECT category_name, category_color, total_spent, total_transactions
        FROM vw_monthly_category_summary
        WHERE user_id = %s AND expense_year = %s AND expense_month = %s
        ORDER BY total_spent DESC
    """, (user_id, cur_year, cur_month))

    # Budgets Status & Warnings (using View vw_budget_status)
    budget_alerts = query_db("""
        SELECT * FROM vw_budget_status
        WHERE user_id = %s AND year = %s AND month = %s
        ORDER BY percentage_used DESC
    """, (user_id, cur_year, cur_month))

    # Payment Methods & Categories for Quick-Add Modal
    categories = query_db("""
        SELECT * FROM categories
        WHERE user_id IS NULL OR user_id = %s
        ORDER BY name ASC
    """, (user_id,))

    payment_methods = query_db("SELECT * FROM payment_methods ORDER BY method_name ASC")

    return render_template(
        'dashboard.html',
        this_month_spent=this_month_spent,
        today_spent=today_spent,
        year_spent=year_spent,
        total_tx=total_tx,
        recent_expenses=recent_expenses,
        category_summary=category_summary,
        budget_alerts=budget_alerts,
        categories=categories,
        payment_methods=payment_methods,
        today_date=str(today)
    )

# ---------------------------------------------------------------------
# Expenses CRUD & Filtering
# ---------------------------------------------------------------------
@app.route('/expenses')
@login_required
def expenses():
    user_id = session['user_id']
    category_filter = request.args.get('category', '').strip()
    payment_filter = request.args.get('payment', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    search = request.args.get('search', '').strip()

    query = "SELECT * FROM vw_expense_details WHERE user_id = %s"
    params = [user_id]

    if category_filter:
        query += " AND category_id = %s"
        params.append(category_filter)

    if payment_filter:
        query += " AND payment_method_id = %s"
        params.append(payment_filter)

    if start_date:
        query += " AND expense_date >= %s"
        params.append(start_date)

    if end_date:
        query += " AND expense_date <= %s"
        params.append(end_date)

    if search:
        query += " AND (description LIKE %s OR category_name LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY expense_date DESC, expense_id DESC"

    expense_list = query_db(query, tuple(params))
    total_filtered_amount = sum(float(item['amount']) for item in expense_list)

    categories = query_db(
        "SELECT * FROM categories WHERE user_id IS NULL OR user_id = %s ORDER BY name ASC",
        (user_id,)
    )
    payment_methods = query_db("SELECT * FROM payment_methods ORDER BY method_name ASC")

    return render_template(
        'expenses.html',
        expenses=expense_list,
        total_amount=total_filtered_amount,
        categories=categories,
        payment_methods=payment_methods,
        selected_category=category_filter,
        selected_payment=payment_filter,
        start_date=start_date,
        end_date=end_date,
        search=search,
        today_date=str(datetime.date.today())
    )

@app.route('/expenses/add', methods=['POST'])
@login_required
def add_expense():
    user_id = session['user_id']
    try:
        amount_raw = request.form.get('amount', '').strip()
        category_id_raw = request.form.get('category_id', '').strip()
        payment_method_id_raw = request.form.get('payment_method_id', '').strip()
        expense_date = request.form.get('expense_date', '').strip() or str(datetime.date.today())
        description = request.form.get('description', '').strip()

        if not amount_raw or not category_id_raw or not payment_method_id_raw or not description:
            flash('Please fill in all required fields (Amount, Category, Payment Method, Description).', 'warning')
            return redirect(request.referrer or url_for('expenses'))

        try:
            amount = float(amount_raw)
        except ValueError:
            flash('Amount must be a valid number.', 'danger')
            return redirect(request.referrer or url_for('expenses'))

        if amount <= 0:
            flash('Expense amount must be greater than zero.', 'danger')
            return redirect(request.referrer or url_for('expenses'))

        category_id = int(category_id_raw)
        payment_method_id = int(payment_method_id_raw)

        execute_db("""
            INSERT INTO expenses (user_id, category_id, payment_method_id, amount, expense_date, description)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, category_id, payment_method_id, amount, expense_date, description))

        flash(f'Expense of ${amount:.2f} logged successfully! (Trigger generated audit log)', 'success')
    except Exception as e:
        flash(f'Failed to add expense: {e}', 'danger')

    return redirect(request.referrer or url_for('expenses'))

@app.route('/expenses/edit/<int:expense_id>', methods=['POST'])
@login_required
def edit_expense(expense_id):
    user_id = session['user_id']
    try:
        # Verify ownership
        existing = query_db(
            "SELECT * FROM expenses WHERE expense_id = %s AND user_id = %s",
            (expense_id, user_id),
            one=True
        )
        if not existing:
            flash('Expense not found or unauthorized access.', 'danger')
            return redirect(url_for('expenses'))

        amount = float(request.form.get('amount', 0))
        category_id = int(request.form.get('category_id'))
        payment_method_id = int(request.form.get('payment_method_id'))
        expense_date = request.form.get('expense_date')
        description = request.form.get('description', '').strip()

        if amount <= 0 or not description:
            flash('Invalid amount or description.', 'danger')
            return redirect(url_for('expenses'))

        execute_db("""
            UPDATE expenses 
            SET category_id = %s, payment_method_id = %s, amount = %s, expense_date = %s, description = %s
            WHERE expense_id = %s AND user_id = %s
        """, (category_id, payment_method_id, amount, expense_date, description, expense_id, user_id))

        flash('Expense record updated successfully. (Audit log updated via Trigger)', 'success')
    except Exception as e:
        flash(f'Failed to update expense: {e}', 'danger')

    return redirect(url_for('expenses'))

@app.route('/expenses/delete/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    user_id = session['user_id']
    try:
        res = execute_db(
            "DELETE FROM expenses WHERE expense_id = %s AND user_id = %s",
            (expense_id, user_id)
        )
        if res['rowcount'] > 0:
            flash('Expense record deleted. (Audit log archived via Trigger)', 'info')
        else:
            flash('Expense not found or unauthorized.', 'warning')
    except Exception as e:
        flash(f'Failed to delete expense: {e}', 'danger')

    return redirect(request.referrer or url_for('expenses'))

# ---------------------------------------------------------------------
# Budget Management
# ---------------------------------------------------------------------
@app.route('/budgets', methods=['GET', 'POST'])
@login_required
def budgets():
    user_id = session['user_id']
    today = datetime.date.today()
    selected_month = int(request.args.get('month', today.month))
    selected_year = int(request.args.get('year', today.year))

    if request.method == 'POST':
        category_id = int(request.form.get('category_id'))
        month = int(request.form.get('month'))
        year = int(request.form.get('year'))
        limit = float(request.form.get('monthly_limit', 0))

        if limit <= 0:
            flash('Budget limit must be greater than zero.', 'danger')
        else:
            # Check if budget exists for this month/year/category
            existing = query_db("""
                SELECT budget_id FROM budgets
                WHERE user_id = %s AND category_id = %s AND month = %s AND year = %s
            """, (user_id, category_id, month, year), one=True)

            if existing:
                execute_db("""
                    UPDATE budgets SET monthly_limit = %s
                    WHERE budget_id = %s
                """, (limit, existing['budget_id']))
                flash('Budget limit updated successfully!', 'success')
            else:
                execute_db("""
                    INSERT INTO budgets (user_id, category_id, month, year, monthly_limit)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, category_id, month, year, limit))
                flash('New budget set successfully!', 'success')

        return redirect(url_for('budgets', month=month, year=year))

    budget_list = query_db("""
        SELECT * FROM vw_budget_status
        WHERE user_id = %s AND month = %s AND year = %s
        ORDER BY percentage_used DESC
    """, (user_id, selected_month, selected_year))

    categories = query_db(
        "SELECT * FROM categories WHERE user_id IS NULL OR user_id = %s ORDER BY name ASC",
        (user_id,)
    )

    total_budget = sum(float(b['monthly_limit']) for b in budget_list)
    total_spent_in_budgets = sum(float(b['spent_amount']) for b in budget_list)

    return render_template(
        'budgets.html',
        budgets=budget_list,
        categories=categories,
        selected_month=selected_month,
        selected_year=selected_year,
        total_budget=total_budget,
        total_spent=total_spent_in_budgets
    )

@app.route('/budgets/delete/<int:budget_id>', methods=['POST'])
@login_required
def delete_budget(budget_id):
    user_id = session['user_id']
    execute_db("DELETE FROM budgets WHERE budget_id = %s AND user_id = %s", (budget_id, user_id))
    flash('Budget deleted successfully.', 'info')
    return redirect(request.referrer or url_for('budgets'))

# ---------------------------------------------------------------------
# Categories Management
# ---------------------------------------------------------------------
@app.route('/categories', methods=['GET', 'POST'])
@login_required
def categories():
    user_id = session['user_id']

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        color = request.form.get('color', '#6c757d').strip()
        icon = request.form.get('icon', 'bi-tag').strip()

        if not name:
            flash('Category name is required.', 'danger')
        else:
            execute_db("""
                INSERT INTO categories (user_id, name, icon, color)
                VALUES (%s, %s, %s, %s)
            """, (user_id, name, icon, color))
            flash(f"Custom category '{name}' created successfully!", 'success')
        return redirect(url_for('categories'))

    user_categories = query_db("""
        SELECT c.*, COUNT(e.expense_id) AS usage_count
        FROM categories c
        LEFT JOIN expenses e ON c.category_id = e.category_id AND e.user_id = %s
        WHERE c.user_id IS NULL OR c.user_id = %s
        GROUP BY c.category_id, c.user_id, c.name, c.icon, c.color, c.created_at
        ORDER BY c.user_id IS NULL ASC, c.name ASC
    """, (user_id, user_id))

    return render_template('categories.html', categories=user_categories)

@app.route('/categories/delete/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    user_id = session['user_id']
    # Check if category is user custom
    cat = query_db("SELECT * FROM categories WHERE category_id = %s", (category_id,), one=True)
    if not cat or cat['user_id'] != user_id:
        flash('Default categories cannot be deleted, or unauthorized.', 'danger')
        return redirect(url_for('categories'))

    # Check if it has expenses
    expenses_count = query_db(
        "SELECT COUNT(*) AS cnt FROM expenses WHERE category_id = %s", 
        (category_id,), 
        one=True
    )['cnt']

    if expenses_count > 0:
        flash(f'Cannot delete category: {expenses_count} expense record(s) are linked to it (Foreign Key RESTRICT rule).', 'warning')
    else:
        execute_db("DELETE FROM categories WHERE category_id = %s AND user_id = %s", (category_id, user_id))
        flash('Category deleted successfully.', 'info')

    return redirect(url_for('categories'))

# ---------------------------------------------------------------------
# Visual Analytics & Charts
# ---------------------------------------------------------------------
@app.route('/analytics')
@login_required
def analytics():
    user_id = session['user_id']
    today = datetime.date.today()
    selected_year = int(request.args.get('year', today.year))
    selected_month = int(request.args.get('month', today.month))

    # 1. Category Breakdown for selected month (Views query)
    category_data = query_db("""
        SELECT category_name, category_color, total_spent, total_transactions
        FROM vw_monthly_category_summary
        WHERE user_id = %s AND expense_year = %s AND expense_month = %s
        ORDER BY total_spent DESC
    """, (user_id, selected_year, selected_month))

    # 2. Monthly Trend for the whole year (Aggregated query)
    if get_active_engine() == 'sqlite':
        monthly_trend = query_db("""
            SELECT 
                CAST(strftime('%m', expense_date) AS INTEGER) AS month_num,
                ROUND(SUM(amount), 2) AS total_spent,
                COUNT(expense_id) AS total_count
            FROM expenses
            WHERE user_id = %s AND CAST(strftime('%Y', expense_date) AS INTEGER) = %s
            GROUP BY month_num
            ORDER BY month_num ASC
        """, (user_id, selected_year))
    else:
        monthly_trend = query_db("""
            SELECT 
                MONTH(expense_date) AS month_num,
                ROUND(SUM(amount), 2) AS total_spent,
                COUNT(expense_id) AS total_count
            FROM expenses
            WHERE user_id = %s AND YEAR(expense_date) = %s
            GROUP BY MONTH(expense_date)
            ORDER BY month_num ASC
        """, (user_id, selected_year))

    # 3. Payment Method Distribution
    payment_data = query_db("""
        SELECT p.method_name, COUNT(e.expense_id) as tx_count, ROUND(SUM(e.amount), 2) as total_spent
        FROM expenses e
        JOIN payment_methods p ON e.payment_method_id = p.payment_method_id
        WHERE e.user_id = %s
        GROUP BY p.method_name
        ORDER BY total_spent DESC
    """, (user_id,))

    # 4. Daily Spending Timeline for selected month
    if get_active_engine() == 'sqlite':
        daily_trend = query_db("""
            SELECT expense_date, ROUND(SUM(amount), 2) as daily_total
            FROM expenses
            WHERE user_id = %s 
              AND CAST(strftime('%Y', expense_date) AS INTEGER) = %s
              AND CAST(strftime('%m', expense_date) AS INTEGER) = %s
            GROUP BY expense_date
            ORDER BY expense_date ASC
        """, (user_id, selected_year, selected_month))
    else:
        daily_trend = query_db("""
            SELECT expense_date, ROUND(SUM(amount), 2) as daily_total
            FROM expenses
            WHERE user_id = %s 
              AND YEAR(expense_date) = %s
              AND MONTH(expense_date) = %s
            GROUP BY expense_date
            ORDER BY expense_date ASC
        """, (user_id, selected_year, selected_month))

    # 5. Top 5 Single Expenses
    top_expenses = query_db("""
        SELECT * FROM vw_expense_details
        WHERE user_id = %s
        ORDER BY amount DESC
        LIMIT 5
    """, (user_id,))

    return render_template(
        'analytics.html',
        selected_year=selected_year,
        selected_month=selected_month,
        category_data=category_data,
        monthly_trend=monthly_trend,
        payment_data=payment_data,
        daily_trend=daily_trend,
        top_expenses=top_expenses
    )

# ---------------------------------------------------------------------
# DBMS Triggers Showcase: Audit Logs
# ---------------------------------------------------------------------
@app.route('/audit-logs')
@login_required
def audit_logs():
    user_id = session['user_id']
    logs = query_db("""
        SELECT * FROM expense_audit_logs
        WHERE user_id = %s
        ORDER BY log_id DESC
        LIMIT 100
    """, (user_id,))
    return render_template('audit_logs.html', logs=logs)

# ---------------------------------------------------------------------
# DBMS Architecture & Schema Showcase (Viva / Documentation)
# ---------------------------------------------------------------------
@app.route('/dbms-docs')
def dbms_docs():
    return render_template('dbms_docs.html')

# ---------------------------------------------------------------------
# CSV Export Route
# ---------------------------------------------------------------------
@app.route('/export/csv')
@login_required
def export_csv():
    user_id = session['user_id']
    expenses_data = query_db("""
        SELECT 
            expense_id,
            expense_date,
            category_name,
            payment_method,
            amount,
            description,
            created_at
        FROM vw_expense_details
        WHERE user_id = %s
        ORDER BY expense_date DESC
    """, (user_id,))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Expense ID', 'Date', 'Category', 'Payment Method', 'Amount ($)', 'Description', 'Logged At'])

    for exp in expenses_data:
        writer.writerow([
            exp['expense_id'],
            exp['expense_date'],
            exp['category_name'],
            exp['payment_method'],
            f"{exp['amount']:.2f}",
            exp['description'],
            exp['created_at']
        ])

    filename = f"expenses_export_{datetime.date.today().strftime('%Y%m%d')}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )

@app.route('/download/pdf')
def download_pdf():
    pdf_path = os.path.join(os.path.dirname(__file__), 'DBMS_Project_Report.pdf')
    if not os.path.exists(pdf_path):
        from generate_pdf import build_pdf
        build_pdf()
    return send_file(
        pdf_path,
        as_attachment=True,
        download_name="DBMS_Personal_Expense_Tracker_Report.pdf",
        mimetype="application/pdf"
    )

# ---------------------------------------------------------------------
# Seed Realistic Demo Data (One-click button)
# ---------------------------------------------------------------------
@app.route('/seed-demo', methods=['POST'])
@login_required
def seed_demo():
    user_id = session['user_id']
    today = datetime.date.today()
    curr = session.get('currency', 'INR')
    
    # 1. Clean previous demo records for this user so they do not multiply
    execute_db("DELETE FROM expenses WHERE user_id = %s", (user_id,))
    execute_db("DELETE FROM budgets WHERE user_id = %s", (user_id,))

    if curr == 'INR':
        sample_records = [
            # (category_id, payment_method_id, amount, offset_days, description)
            (1, 4, 380.00, 0, 'Chai & Snacks at Chaayos via UPI'),
            (9, 4, 2850.00, 1, 'Blinkit / Zepto Quick Grocery Delivery'),
            (2, 4, 450.00, 2, 'Uber Cab to Tech Park'),
            (5, 5, 2350.00, 3, 'Electricity Bill (MSEDCL) via Net Banking'),
            (4, 2, 950.00, 4, 'PVR IMAX Movie Tickets & Popcorn'),
            (1, 4, 1450.00, 5, 'Family Dinner at Barbeque Nation'),
            (3, 2, 3499.00, 7, 'ZARA Linen Casual Shirt (Credit Card)'),
            (6, 4, 620.00, 8, 'Apollo Pharmacy Medicines & Vitamins'),
            (2, 1, 1800.00, 10, 'Petrol Refill at Indian Oil (Cash)'),
            (8, 2, 8500.00, 14, 'Lonavala Weekend Resort Booking'),
            (1, 4, 320.00, 16, 'Swiggy Biryani Lunch Delivery'),
            (9, 2, 4750.00, 18, 'Monthly DMart Grocery Haul'),
            (7, 4, 2999.00, 22, 'Online Full-Stack DBMS Bootcamp Course'),
            (4, 3, 799.00, 25, 'Netflix & Spotify Premium Subscriptions'),
            (5, 4, 999.00, 28, 'JioFiber High-Speed Home WiFi Bill'),
            (1, 1, 450.00, 32, 'Dosa & Filter Coffee Breakfast (Cash)'),
            (2, 4, 750.00, 35, 'Ola Outstation Cab Ride'),
            (9, 4, 3200.00, 40, 'Pantry Staples & Dry Fruits Store'),
            (5, 5, 1850.00, 45, 'Gas Cylinder (Indane) & Water Bill'),
            (3, 2, 4200.00, 50, 'Nike Running Shoes & Sportswear'),
        ]

        budgets_to_seed = [
            (1, 10000.00),  # Food & Dining
            (9, 14000.00),  # Groceries
            (2, 5000.00),   # Transportation
            (5, 7000.00),   # Utilities
            (4, 4000.00),   # Entertainment
            (3, 8000.00),   # Shopping & Retail
        ]
    else:
        sample_records = [
            (1, 1, 14.50, 0, 'Starbucks Coffee & Croissant'),
            (9, 2, 85.20, 1, 'Whole Foods Grocery Run'),
            (2, 4, 25.00, 2, 'Uber ride to Downtown Office'),
            (5, 5, 120.00, 3, 'Electricity & Power Bill'),
            (4, 2, 32.00, 4, 'IMAX Movie Tickets with Snacks'),
            (1, 4, 45.80, 5, 'Dinner at Italian Bistro'),
            (3, 2, 65.00, 7, 'Winter Jacket purchase'),
            (6, 3, 40.00, 8, 'Pharmacy Prescription'),
            (2, 1, 35.00, 10, 'Gasoline Refill'),
            (8, 2, 210.00, 14, 'Weekend Getaway Airbnb'),
            (1, 4, 18.25, 16, 'Sushi Bento Lunch'),
            (9, 2, 92.40, 18, 'Weekly Groceries & Supplies'),
            (7, 4, 50.00, 22, 'Online DBMS Certification Course'),
            (4, 3, 19.99, 25, 'Streaming Subscriptions (Netflix + Spotify)'),
            (1, 1, 28.50, 32, 'Lunch buffet with colleagues'),
            (2, 4, 42.00, 35, 'Airport Shuttle Taxi'),
            (9, 2, 115.60, 40, 'Monthly Pantry Supplies'),
            (5, 5, 80.00, 45, 'High-speed Fiber Internet Bill'),
            (3, 2, 140.00, 50, 'Running Shoes & Sports Gear'),
        ]

        budgets_to_seed = [
            (1, 250.00),
            (9, 300.00),
            (2, 120.00),
            (4, 80.00),
            (5, 200.00),
        ]

    for cat_id, pay_id, amount, offset_days, desc in sample_records:
        date_val = str(today - datetime.timedelta(days=offset_days))
        execute_db("""
            INSERT INTO expenses (user_id, category_id, payment_method_id, amount, expense_date, description)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, cat_id, pay_id, amount, date_val, desc))

    # Add sample budgets for current month
    cur_month = today.month
    cur_year = today.year
    for cat_id, limit in budgets_to_seed:
        execute_db("""
            INSERT INTO budgets (user_id, category_id, month, year, monthly_limit)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, cat_id, cur_month, cur_year, limit))

    flash('Realistic Rupee (₹) demo expenses and monthly budgets loaded successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/expenses/clear-all', methods=['POST'])
@login_required
def clear_all_expenses():
    user_id = session['user_id']
    execute_db("DELETE FROM expenses WHERE user_id = %s", (user_id,))
    execute_db("DELETE FROM budgets WHERE user_id = %s", (user_id,))
    flash('All your recorded expenses and budgets have been wiped cleanly.', 'info')
    return redirect(url_for('expenses'))

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5050))
    app.run(host='0.0.0.0', port=port, debug=True)
