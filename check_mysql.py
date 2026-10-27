#!/usr/bin/env python3
"""
MySQL Diagnostic & Connection Doctor for Personal Expense Tracker
Run with: ./venv/bin/python3 check_mysql.py
"""

import os
import sys
import socket
import pymysql
from dotenv import load_dotenv

load_dotenv()

MYSQL_HOST = os.getenv('DB_HOST', '127.0.0.1')
MYSQL_PORT = int(os.getenv('DB_PORT', 3306))
MYSQL_USER = os.getenv('DB_USER', 'root')
MYSQL_PASSWORD = os.getenv('DB_PASSWORD', '')
MYSQL_DATABASE = os.getenv('DB_NAME', 'expense_tracker_db')

print("=============================================================")
print("         MySQL Database Connection Diagnostic Doctor         ")
print("=============================================================")
print(f"Target Configuration:")
print(f"  Host     : {MYSQL_HOST}")
print(f"  Port     : {MYSQL_PORT}")
print(f"  User     : {MYSQL_USER}")
print(f"  Password : {'[SET]' if MYSQL_PASSWORD else '[EMPTY / NONE]'}")
print(f"  Database : {MYSQL_DATABASE}")
print("-------------------------------------------------------------")

# Step 1: Check port reachability
print("\n[Step 1] Checking if MySQL port is accepting connections...")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(2)
try:
    res = sock.connect_ex((MYSQL_HOST, MYSQL_PORT))
    if res == 0:
        print(f"  ==> Port {MYSQL_PORT} on {MYSQL_HOST} is OPEN! MySQL service is actively running.")
        port_open = True
    else:
        print(f"  ==> Port {MYSQL_PORT} is CLOSED (Error Code: {res}).")
        port_open = False
finally:
    sock.close()

if not port_open:
    print("\n[DIAGNOSIS]: Your MySQL Server is currently STOPPED.")
    print("-------------------------------------------------------------")
    print("How to start MySQL on your Mac:")
    print("  1. Graphical:")
    print("     Open macOS 'System Settings' -> scroll down left sidebar to 'MySQL' -> click 'Start MySQL Server'")
    print("  2. Terminal command:")
    print("     sudo /usr/local/mysql/support-files/mysql.server start")
    print("-------------------------------------------------------------")
    sys.exit(1)

# Step 2: Check MySQL Authentication
print("\n[Step 2] Testing MySQL user credentials & handshake...")
try:
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        connect_timeout=3
    )
    with conn.cursor() as cur:
        cur.execute("SELECT VERSION() AS ver, CURRENT_USER() AS usr;")
        row = cur.fetchone()
        version = row[0] if row else 'Unknown'
        user_conn = row[1] if row else MYSQL_USER
    conn.close()
    print(f"  ==> SUCCESS! Connected as '{user_conn}' to MySQL Version: {version}")
except pymysql.err.OperationalError as e:
    err_code, err_msg = e.args
    print(f"  ==> FAILED with OperationalError [{err_code}]: {err_msg}")
    if err_code == 1045:
        print("\n[DIAGNOSIS]: Access Denied - Root password issue!")
        print("  Your MySQL server is running, but the password in .env does not match.")
        print("  Update your '.env' file with the correct password:")
        print("     DB_PASSWORD=your_actual_mysql_password")
    sys.exit(1)
except Exception as e:
    print(f"  ==> Connection failed: {e}")
    sys.exit(1)

# Step 3: Check/Create Database & Tables
print(f"\n[Step 3] Verifying database '{MYSQL_DATABASE}'...")
try:
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        connect_timeout=3
    )
    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` CHARACTER SET utf8mb4;")
        cur.execute(f"USE `{MYSQL_DATABASE}`;")
        cur.execute("SHOW TABLES;")
        tables = [t[0] for t in cur.fetchall()]
    conn.close()
    print(f"  ==> Database '{MYSQL_DATABASE}' exists! Tables found ({len(tables)}): {', '.join(tables) if tables else 'None yet (will auto-populate on app start)'}")
except Exception as e:
    print(f"  ==> Database check failed: {e}")
    sys.exit(1)

print("\n=============================================================")
print(" ALL CHECKS PASSED! MySQL is 100% ready to use.")
print(" You can set DB_ENGINE=mysql in .env and start the app.")
print("=============================================================")
