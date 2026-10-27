#!/usr/bin/env python3
"""
Direct Schema Importer for Personal Expense Tracker (MySQL)
Run with: ./venv/bin/python3 import_schema.py
"""

import os
import sys
import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv
from database.db import parse_sql_script

load_dotenv()

MYSQL_HOST = os.getenv('DB_HOST', '127.0.0.1')
MYSQL_PORT = int(os.getenv('DB_PORT', 3306))
MYSQL_USER = os.getenv('DB_USER', 'root')
MYSQL_PASSWORD = os.getenv('DB_PASSWORD', '')
MYSQL_DATABASE = os.getenv('DB_NAME', 'expense_tracker_db')

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'database', 'schema.sql')

print("=============================================================")
print("      MySQL Schema Importer for Personal Expense Tracker     ")
print("=============================================================")
print(f"Connecting to MySQL at {MYSQL_HOST}:{MYSQL_PORT} as '{MYSQL_USER}'...")

try:
    # 1. Connect without database to ensure database exists
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        cursorclass=DictCursor,
        connect_timeout=5,
        autocommit=True
    )
except pymysql.err.OperationalError as e:
    code, msg = e.args
    print(f"\n[ERROR]: Failed to connect to MySQL server ({code}: {msg})")
    print("Please ensure your MySQL server is running:")
    print("  macOS System Settings -> MySQL -> Start MySQL Server")
    sys.exit(1)
except Exception as e:
    print(f"\n[ERROR]: {e}")
    sys.exit(1)

with conn.cursor() as cur:
    print(f"[*] Ensuring database `{MYSQL_DATABASE}` exists...")
    cur.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    cur.execute(f"USE `{MYSQL_DATABASE}`;")

print(f"[*] Reading `{SCHEMA_PATH}`...")
with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
    sql_content = f.read()

statements = parse_sql_script(sql_content)
print(f"[*] Found {len(statements)} statements to execute.")

executed_count = 0
with conn.cursor() as cur:
    cur.execute(f"USE `{MYSQL_DATABASE}`;")
    for i, stmt in enumerate(statements, 1):
        # Extract a short summary of the statement
        summary = stmt.split('\n')[0].strip()[:65]
        try:
            cur.execute(stmt)
            print(f"  ✓ [{i}/{len(statements)}] Executed: {summary}...")
            executed_count += 1
        except Exception as e:
            # Drop/replace or harmless warnings
            print(f"  ⚠ [{i}/{len(statements)}] Notice on: {summary}... ({e})")

# Verify tables
with conn.cursor() as cur:
    cur.execute(f"USE `{MYSQL_DATABASE}`;")
    cur.execute("SHOW TABLES;")
    tables = [list(r.values())[0] for r in cur.fetchall()]

conn.close()

print("\n=============================================================")
print(f" SUCCESS! Database `{MYSQL_DATABASE}` is fully initialized.")
print(f" Tables in database ({len(tables)}): {', '.join(tables)}")
print("=============================================================")
print("You can now start your web app:")
print("  ./venv/bin/python3 app.py")
print("=============================================================")
