-- =====================================================================
-- DATABASE SCHEMA: Personal Expense Tracker (SQLite Local Engine)
-- Provides full compatibility with MySQL schema logic (Views, Triggers)
-- =====================================================================

PRAGMA foreign_keys = ON;

-- 1. Table: users
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    currency TEXT DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Table: categories
CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NULL,
    name TEXT NOT NULL,
    icon TEXT DEFAULT 'bi-tag',
    color TEXT DEFAULT '#6c757d',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 3. Table: payment_methods
CREATE TABLE IF NOT EXISTS payment_methods (
    payment_method_id INTEGER PRIMARY KEY AUTOINCREMENT,
    method_name TEXT NOT NULL UNIQUE,
    icon TEXT DEFAULT 'bi-wallet2'
);

-- 4. Table: expenses
CREATE TABLE IF NOT EXISTS expenses (
    expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    payment_method_id INTEGER NOT NULL,
    amount REAL NOT NULL CHECK(amount > 0),
    expense_date TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE RESTRICT,
    FOREIGN KEY (payment_method_id) REFERENCES payment_methods(payment_method_id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_expenses_user_date ON expenses(user_id, expense_date);
CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category_id);

-- 5. Table: budgets
CREATE TABLE IF NOT EXISTS budgets (
    budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    month INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
    year INTEGER NOT NULL CHECK(year >= 2000),
    monthly_limit REAL NOT NULL CHECK(monthly_limit > 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, category_id, month, year),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE
);

-- 6. Table: expense_audit_logs (Triggers Showcase)
CREATE TABLE IF NOT EXISTS expense_audit_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    old_amount REAL NULL,
    new_amount REAL NULL,
    action_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details TEXT NULL
);

-- 7. TRIGGERS
CREATE TRIGGER IF NOT EXISTS trg_after_expense_insert
AFTER INSERT ON expenses
BEGIN
    INSERT INTO expense_audit_logs (expense_id, user_id, action, old_amount, new_amount, details)
    VALUES (NEW.expense_id, NEW.user_id, 'INSERT', NULL, NEW.amount, 'Created expense: ' || NEW.description);
END;

CREATE TRIGGER IF NOT EXISTS trg_after_expense_update
AFTER UPDATE ON expenses
BEGIN
    INSERT INTO expense_audit_logs (expense_id, user_id, action, old_amount, new_amount, details)
    VALUES (NEW.expense_id, NEW.user_id, 'UPDATE', OLD.amount, NEW.amount, 'Updated expense: ' || NEW.description);
END;

CREATE TRIGGER IF NOT EXISTS trg_after_expense_delete
AFTER DELETE ON expenses
BEGIN
    INSERT INTO expense_audit_logs (expense_id, user_id, action, old_amount, new_amount, details)
    VALUES (OLD.expense_id, OLD.user_id, 'DELETE', OLD.amount, NULL, 'Deleted expense: ' || OLD.description);
END;

-- 8. VIEWS
CREATE VIEW IF NOT EXISTS vw_expense_details AS
SELECT 
    e.expense_id,
    e.user_id,
    e.amount,
    e.expense_date,
    e.description,
    c.category_id,
    c.name AS category_name,
    c.icon AS category_icon,
    c.color AS category_color,
    p.payment_method_id,
    p.method_name AS payment_method,
    p.icon AS payment_icon,
    e.created_at
FROM expenses e
JOIN categories c ON e.category_id = c.category_id
JOIN payment_methods p ON e.payment_method_id = p.payment_method_id;

CREATE VIEW IF NOT EXISTS vw_monthly_category_summary AS
SELECT 
    e.user_id,
    CAST(strftime('%Y', e.expense_date) AS INTEGER) AS expense_year,
    CAST(strftime('%m', e.expense_date) AS INTEGER) AS expense_month,
    c.category_id,
    c.name AS category_name,
    c.color AS category_color,
    COUNT(e.expense_id) AS total_transactions,
    ROUND(SUM(e.amount), 2) AS total_spent
FROM expenses e
JOIN categories c ON e.category_id = c.category_id
GROUP BY e.user_id, expense_year, expense_month, c.category_id, c.name, c.color;

CREATE VIEW IF NOT EXISTS vw_budget_status AS
SELECT 
    b.budget_id,
    b.user_id,
    b.category_id,
    c.name AS category_name,
    c.color AS category_color,
    b.month,
    b.year,
    b.monthly_limit,
    COALESCE(SUM(e.amount), 0.0) AS spent_amount,
    ROUND(b.monthly_limit - COALESCE(SUM(e.amount), 0.0), 2) AS remaining_amount,
    ROUND((COALESCE(SUM(e.amount), 0.0) / b.monthly_limit) * 100, 2) AS percentage_used
FROM budgets b
JOIN categories c ON b.category_id = c.category_id
LEFT JOIN expenses e ON e.user_id = b.user_id 
    AND e.category_id = b.category_id
    AND CAST(strftime('%m', e.expense_date) AS INTEGER) = b.month
    AND CAST(strftime('%Y', e.expense_date) AS INTEGER) = b.year
GROUP BY b.budget_id, b.user_id, b.category_id, c.name, c.color, b.month, b.year, b.monthly_limit;

-- 9. Initial Seed Data
INSERT OR IGNORE INTO payment_methods (payment_method_id, method_name, icon) VALUES
(1, 'Cash', 'bi-cash'),
(2, 'Credit Card', 'bi-credit-card'),
(3, 'Debit Card', 'bi-credit-card-2-front'),
(4, 'UPI / Online Transfer', 'bi-phone'),
(5, 'Net Banking', 'bi-bank');

INSERT OR IGNORE INTO categories (category_id, user_id, name, icon, color) VALUES
(1, NULL, 'Food & Dining', 'bi-cup-hot', '#FF5733'),
(2, NULL, 'Transportation', 'bi-car-front', '#33A8FF'),
(3, NULL, 'Shopping & Retail', 'bi-bag-check', '#9B59B6'),
(4, NULL, 'Entertainment', 'bi-film', '#F1C40F'),
(5, NULL, 'Utilities & Bills', 'bi-lightning-charge', '#2ECC71'),
(6, NULL, 'Healthcare', 'bi-heart-pulse', '#E74C3C'),
(7, NULL, 'Education', 'bi-book', '#34495E'),
(8, NULL, 'Travel', 'bi-airplane', '#1ABC9C'),
(9, NULL, 'Groceries', 'bi-cart', '#E67E22'),
(10, NULL, 'Miscellaneous', 'bi-three-dots', '#95A5A6');
