#!/bin/bash
# =====================================================================
# Personal Expense Tracker - Startup Script
# =====================================================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
fi

echo "=========================================================="
echo " Starting Personal Expense Tracker (DBMS Mini-Project)..."
echo " Open your browser at: http://127.0.0.1:5050"
echo "=========================================================="

./venv/bin/python3 app.py
