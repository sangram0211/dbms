import unittest
import json
from app import app
from database.db import get_active_engine, query_db

class ExpenseTrackerTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    @classmethod
    def setUpClass(cls):
        from database.db import execute_db
        # Ensure fresh state for test runner
        execute_db("DELETE FROM users WHERE username = 'student_dbms'")

    def test_01_db_engine(self):
        engine = get_active_engine()
        print(f"\n[TEST] Active Database Engine: {engine}")
        self.assertIn(engine, ['mysql', 'sqlite'])

    def test_02_register_and_login(self):
        # Register test user
        res = self.client.post('/register', data={
            'full_name': 'Test Student',
            'username': 'student_dbms',
            'email': 'student@university.edu',
            'password': 'password123',
            'currency': 'USD'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Financial Overview', res.data)

        # Logout
        res = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'safely logged out', res.data)

        # Login again
        res = self.client.post('/login', data={
            'username': 'student_dbms',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Financial Overview', res.data)

    def test_03_crud_and_triggers(self):
        # Login
        self.client.post('/login', data={
            'username': 'student_dbms',
            'password': 'password123'
        }, follow_redirects=True)

        # 1. Add expense
        res = self.client.post('/expenses/add', data={
            'amount': '85.50',
            'category_id': '1',
            'payment_method_id': '2',
            'expense_date': '2026-10-21',
            'description': 'Database Lab Textbook & Stationery'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Verify Trigger fired for INSERT
        logs = query_db("SELECT * FROM expense_audit_logs WHERE action = 'INSERT'")
        self.assertTrue(len(logs) > 0)
        exp_id = logs[-1]['expense_id']
        self.assertEqual(float(logs[-1]['new_amount']), 85.50)
        print(f"[TEST] Trigger INSERT verified: Log ID {logs[-1]['log_id']} for Expense #{exp_id}")

        # 2. Edit expense
        res = self.client.post(f'/expenses/edit/{exp_id}', data={
            'amount': '95.00',
            'category_id': '1',
            'payment_method_id': '2',
            'expense_date': '2026-10-21',
            'description': 'Database Lab Textbook & Advanced Reference'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Verify Trigger fired for UPDATE
        update_logs = query_db("SELECT * FROM expense_audit_logs WHERE action = 'UPDATE' AND expense_id = %s", (exp_id,))
        self.assertTrue(len(update_logs) > 0)
        self.assertEqual(float(update_logs[-1]['old_amount']), 85.50)
        self.assertEqual(float(update_logs[-1]['new_amount']), 95.00)
        print(f"[TEST] Trigger UPDATE verified: Old={update_logs[-1]['old_amount']} -> New={update_logs[-1]['new_amount']}")

        # 3. Delete expense
        res = self.client.post(f'/expenses/delete/{exp_id}', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Verify Trigger fired for DELETE
        del_logs = query_db("SELECT * FROM expense_audit_logs WHERE action = 'DELETE' AND expense_id = %s", (exp_id,))
        self.assertTrue(len(del_logs) > 0)
        self.assertEqual(float(del_logs[-1]['old_amount']), 95.00)
        print(f"[TEST] Trigger DELETE verified: Logged deletion of #{exp_id}")

    def test_04_pages_and_reports(self):
        self.client.post('/login', data={
            'username': 'student_dbms',
            'password': 'password123'
        }, follow_redirects=True)

        # Seed demo data
        res = self.client.post('/seed-demo', follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Check Analytics page
        res = self.client.get('/analytics')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Visual Analytics', res.data)
        self.assertIn(b'categoryChart', res.data)
        self.assertIn(b'monthlyTrendChart', res.data)
        print("[TEST] Visual Analytics & Charts page loaded successfully")

        # Check Budgets page
        res = self.client.get('/budgets')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Monthly Budgets', res.data)
        print("[TEST] Budgets page loaded successfully")

        # Check Audit logs page
        res = self.client.get('/audit-logs')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Database Trigger Audit Logs', res.data)
        print("[TEST] Trigger Audit Logs page loaded successfully")

        # Check CSV Export
        res = self.client.get('/export/csv')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, 'text/csv')
        print("[TEST] CSV Export generated successfully")

        # Check DBMS Documentation & ER Diagram page
        res = self.client.get('/dbms-docs')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'DBMS Architecture', res.data)
        print("[TEST] DBMS Docs & Viva page loaded successfully")

if __name__ == '__main__':
    unittest.main()
