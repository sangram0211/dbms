# Personal Expense Tracker (DBMS Mini-Project)

A complete, modern, academic-grade **Database Management System (DBMS)** project inspired by [EbeyJoeRegi/Personal-Expense-Tracker](https://github.com/EbeyJoeRegi/Personal-Expense-Tracker), engineered with a production-ready **MySQL** relational database schema, database triggers, views, stored procedures, 3NF normalization, and interactive visual analytics.

![DBMS Project](https://img.shields.io/badge/DBMS-MySQL%20%7C%20SQLite-blue.svg)
![Python](https://img.shields.io/badge/Python-3.9+-green.svg)
![Flask](https://img.shields.io/badge/Framework-Flask%203-lightgrey.svg)
![UI](https://img.shields.io/badge/Frontend-Bootstrap%205%20%2B%20Chart.js-purple.svg)

---

## 🌟 Key Features

1. **User Authentication & Isolation:**
   - Multi-user support with secure PBKDF2 password hashing.
   - Per-user expense tracking and isolation.

2. **Full Relational Schema (3NF Normalized):**
   - Entities: `users`, `categories`, `payment_methods`, `expenses`, `budgets`, `expense_audit_logs`.
   - Referential integrity constraints (`ON DELETE CASCADE`, `ON DELETE RESTRICT`).
   - Atomic attributes, indexed queries, and check constraints (`CHECK(amount > 0)`).

3. **Database Triggers (Automated Audit Trails):**
   - `trg_after_expense_insert`: Automatically logs new expense creations into `expense_audit_logs`.
   - `trg_after_expense_update`: Captures before/after values on modifications.
   - `trg_after_expense_delete`: Archives deleted transactions at the database engine level.

4. **Database Views:**
   - `vw_expense_details`: Joins expenses with category and payment metadata.
   - `vw_monthly_category_summary`: Aggregates transactions and total spending per user, month, year, and category.
   - `vw_budget_status`: Joins budgets with actual expenditure to compute remaining amount and percentage utilized.

5. **Visual Analytics & Interactive Charts:**
   - **Category Spending Distribution** (Interactive Doughnut Chart).
   - **Annual 12-Month Spending Trend** (Bar + Line overlay).
   - **Payment Methods Breakdown** (Pie Chart).
   - **Daily Spending Velocity** (Day-by-day bar chart).
   - **Top 5 Single Largest Expenses** ranking table.

6. **Budget Management & Warning Alerts:**
   - Set monthly category spending caps.
   - Visual progress bars with color-coded warnings (Normal < 80%, Warning 80–99%, Danger ≥ 100%).

7. **Data Export & Seed Demo Generator:**
   - Export filtered transactions directly to CSV.
   - One-click "Load Demo Data" button to instantly populate realistic expenses for viva/demo presentation.

8. **Dual-Engine Architecture (MySQL + Zero-Config SQLite Fallback):**
   - Connects directly to **MySQL** (XAMPP / Homebrew / Docker).
   - If MySQL is not running, seamlessly falls back to local SQLite with identical schema and triggers so the application works out-of-the-box.

---

## 📂 Project Structure

```
DBMS/
├── app.py                      # Core Flask web application and API endpoints
├── database/
│   ├── db.py                   # Dual-engine connection manager (MySQL + SQLite)
│   ├── schema.sql              # Standard MySQL 8.0 DDL, Triggers, Views & Procedures
│   └── sqlite_schema.sql       # SQLite equivalent schema with triggers & views
├── templates/                  # Responsive Jinja2 HTML templates
│   ├── base.html               # Master layout with navbar & engine indicator
│   ├── login.html              # Authentication sign-in page
│   ├── register.html           # User registration page
│   ├── dashboard.html          # Financial KPI overview & quick charts
│   ├── expenses.html           # Filterable expense list with Add/Edit/Delete modals
│   ├── analytics.html          # Comprehensive Chart.js visual analytics
│   ├── budgets.html            # Category budget thresholds & progress bars
│   ├── categories.html         # Custom category manager
│   ├── audit_logs.html         # Live DBMS Trigger audit execution history
│   └── dbms_docs.html          # Interactive ER Diagram & viva submission guide
├── DBMS_PROJECT_REPORT.md      # Academic report (ER Diagram, 3NF Proof, Viva Q&A)
├── requirements.txt            # Python dependencies
├── start.sh                    # One-command startup script
├── test_app.py                 # Automated test suite (Triggers, CRUD, Views)
├── .env.example                # Sample environment configuration
└── README.md                   # Project documentation
```

---

## 🚀 Quick Start Guide

### 1. Run Directly (Out-of-the-box)

The project includes an automatic virtual environment and zero-config engine fallback:

```bash
# Make sure you are in the project folder
cd DBMS

# Run the startup script
./start.sh
```

Or run manually:

```bash
# Activate virtual environment
source venv/bin/activate

# Start Flask server
python3 app.py
```

Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

### 2. Connect to MySQL (e.g., XAMPP, Workbench, or Homebrew)

1. **Start your MySQL server** (e.g. from XAMPP Control Panel or terminal).
2. **Import the SQL schema:**
   - Using terminal:
     ```bash
     mysql -u root -p < database/schema.sql
     ```
   - Or open **phpMyAdmin** (`http://localhost/phpmyadmin`), click **Import**, select `database/schema.sql`, and run.
3. **Configure your `.env` file:**
   ```ini
   DB_ENGINE=mysql
   DB_HOST=127.0.0.1
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=
   DB_NAME=expense_tracker_db
   ```
4. **Restart the app:**
   ```bash
   ./venv/bin/python3 app.py
   ```
   The top navbar badge will display `RDBMS: MYSQL`!

---

## 🧪 Running Automated Tests

Run the test suite to verify database connection, CRUD operations, and trigger executions:

```bash
./venv/bin/python3 test_app.py
```

Expected output:
```text
[TEST] Active Database Engine: sqlite (or mysql)
[TEST] Trigger INSERT verified: Log ID 1 for Expense #1
[TEST] Trigger UPDATE verified: Old=85.5 -> New=95.0
[TEST] Trigger DELETE verified: Logged deletion of #1
[TEST] Visual Analytics & Charts page loaded successfully
[TEST] Budgets page loaded successfully
[TEST] Trigger Audit Logs page loaded successfully
[TEST] CSV Export generated successfully
[TEST] DBMS Docs & Viva page loaded successfully
Ran 4 tests in 2.082s ... OK
```

---

## 🎓 Academic Submission & Viva Guide

For your academic project submission, refer to [DBMS_PROJECT_REPORT.md](file:///Users/sangram/Documents/New%20folder/My%20Codes/DBMS/DBMS_PROJECT_REPORT.md) or visit the `/dbms-docs` page in the running app for:
- Complete Entity-Relationship (ER) diagram in Mermaid.
- Relational Schema representation with PK and FK notations.
- 1NF, 2NF, and 3NF normalization justifications.
- Stored procedures, views, and trigger definitions.
- Viva / Oral Examination questions and answers.
