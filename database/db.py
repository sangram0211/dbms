import os
import sqlite3
import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv

load_dotenv()

DB_ENGINE = os.getenv('DB_ENGINE', 'auto').lower() # 'mysql', 'sqlite', or 'auto'
MYSQL_HOST = os.getenv('DB_HOST', '127.0.0.1')
MYSQL_PORT = int(os.getenv('DB_PORT', 3306))
MYSQL_USER = os.getenv('DB_USER', 'root')
MYSQL_PASSWORD = os.getenv('DB_PASSWORD', '')
MYSQL_DATABASE = os.getenv('DB_NAME', 'expense_tracker_db')

SQLITE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'expense_tracker.db')

ACTIVE_ENGINE = None
MYSQL_LAST_ERROR = None

def test_mysql_connection():
    """Test connecting to MySQL and return (success, message)."""
    global MYSQL_LAST_ERROR
    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            cursorclass=DictCursor,
            connect_timeout=3
        )
        with conn.cursor() as cur:
            cur.execute("SELECT VERSION() AS ver;")
            row = cur.fetchone()
            ver = row['ver'] if row else 'Unknown'
        conn.close()
        MYSQL_LAST_ERROR = None
        return True, f"Connected to MySQL {ver}"
    except Exception as e:
        MYSQL_LAST_ERROR = str(e)
        return False, str(e)

def get_mysql_connection(create_db_if_missing=True):
    """Attempt connecting to MySQL. Optionally creates database if not exists."""
    global MYSQL_LAST_ERROR
    if create_db_if_missing:
        try:
            temp_conn = pymysql.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                cursorclass=DictCursor,
                connect_timeout=3
            )
            with temp_conn.cursor() as cur:
                cur.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            temp_conn.close()
        except Exception as e:
            MYSQL_LAST_ERROR = str(e)
            raise e

    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            cursorclass=DictCursor,
            connect_timeout=3,
            autocommit=True
        )
        MYSQL_LAST_ERROR = None
        return conn
    except Exception as e:
        MYSQL_LAST_ERROR = str(e)
        raise e

def _sqlite_year(val):
    if not val:
        return None
    try:
        return int(str(val)[:4])
    except (ValueError, TypeError):
        return None

def _sqlite_month(val):
    if not val:
        return None
    try:
        return int(str(val)[5:7])
    except (ValueError, TypeError):
        return None

def get_sqlite_connection():
    """Connect to SQLite with row factory, foreign keys, and MySQL date helpers."""
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.create_function("YEAR", 1, _sqlite_year)
    conn.create_function("MONTH", 1, _sqlite_month)
    return conn

def determine_engine():
    global ACTIVE_ENGINE
    if DB_ENGINE == 'sqlite':
        ACTIVE_ENGINE = 'sqlite'
        return ACTIVE_ENGINE

    if DB_ENGINE == 'mysql':
        try:
            conn = get_mysql_connection()
            conn.close()
            ACTIVE_ENGINE = 'mysql'
            return ACTIVE_ENGINE
        except Exception as e:
            raise RuntimeError(f"Configured DB_ENGINE is 'mysql' but connection failed: {e}")

    # 'auto' mode: try MySQL first, fallback to SQLite
    try:
        conn = get_mysql_connection()
        conn.close()
        ACTIVE_ENGINE = 'mysql'
    except Exception:
        ACTIVE_ENGINE = 'sqlite'
    return ACTIVE_ENGINE

def get_mysql_last_error():
    global MYSQL_LAST_ERROR
    return MYSQL_LAST_ERROR

def get_active_engine():
    global ACTIVE_ENGINE
    if ACTIVE_ENGINE is None:
        determine_engine()
    return ACTIVE_ENGINE

def get_db():
    engine = get_active_engine()
    if engine == 'mysql':
        return get_mysql_connection(create_db_if_missing=False)
    else:
        return get_sqlite_connection()

def normalize_query_for_engine(query, engine):
    """Adapt query syntax between MySQL and SQLite if necessary."""
    if engine == 'sqlite':
        # Replace MySQL parameter placeholder %s with SQLite placeholder ?
        # Be careful not to replace strftime format strings like '%Y'
        parts = query.split("'%")
        normalized = []
        for i, part in enumerate(parts):
            if i == 0:
                normalized.append(part.replace('%s', '?'))
            else:
                # restore format strings
                sub = part.split("%'")
                if len(sub) == 2:
                    normalized.append("'" + "%" + sub[0] + "%'" + sub[1].replace('%s', '?'))
                else:
                    normalized.append("'" + "%" + part.replace('%s', '?'))
        query = "".join(normalized)
    return query

def query_db(query, args=(), one=False):
    """Execute a SELECT query and return dictionary records."""
    engine = get_active_engine()
    conn = get_db()
    try:
        norm_query = normalize_query_for_engine(query, engine)
        if engine == 'mysql':
            with conn.cursor() as cur:
                cur.execute(norm_query, args)
                rows = cur.fetchall()
                return (rows[0] if rows else None) if one else rows
        else:
            cur = conn.cursor()
            cur.execute(norm_query, args)
            rows = [dict(row) for row in cur.fetchall()]
            return (rows[0] if rows else None) if one else rows
    finally:
        conn.close()

def execute_db(query, args=()):
    """Execute an INSERT, UPDATE, or DELETE query and return lastrowid and affected rows."""
    engine = get_active_engine()
    conn = get_db()
    try:
        norm_query = normalize_query_for_engine(query, engine)
        if engine == 'mysql':
            with conn.cursor() as cur:
                affected = cur.execute(norm_query, args)
                last_id = cur.lastrowid
                return {'lastrowid': last_id, 'rowcount': affected}
        else:
            cur = conn.cursor()
            cur.execute(norm_query, args)
            conn.commit()
            return {'lastrowid': cur.lastrowid, 'rowcount': cur.rowcount}
    finally:
        conn.close()

def parse_sql_script(content):
    """Accurately parses SQL scripts with DELIMITER $$ statements (for triggers and stored procedures)."""
    statements = []
    current_stmt = []
    delimiter = ';'
    for line in content.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith('--') or trimmed.startswith('/*'):
            continue
        if trimmed.upper().startswith('DELIMITER'):
            parts = trimmed.split()
            if len(parts) >= 2:
                delimiter = parts[1]
            continue
        current_stmt.append(line)
        if trimmed.endswith(delimiter):
            full_stmt = '\n'.join(current_stmt)
            idx = full_stmt.rfind(delimiter)
            full_stmt = full_stmt[:idx]
            if full_stmt.strip():
                statements.append(full_stmt.strip())
            current_stmt = []
            
    if current_stmt and '\n'.join(current_stmt).strip():
        statements.append('\n'.join(current_stmt).strip())
    return statements

def init_db():
    """Initializes tables and seeds schema for active engine."""
    engine = get_active_engine()
    base_dir = os.path.dirname(__file__)
    
    if engine == 'mysql':
        schema_file = os.path.join(base_dir, 'schema.sql')
        conn = get_mysql_connection(create_db_if_missing=True)
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                content = f.read()
            statements = parse_sql_script(content)
            with conn.cursor() as cur:
                for stmt in statements:
                    try:
                        cur.execute(stmt)
                    except Exception as e:
                        # Log or ignore benign errors (e.g. trigger already exists)
                        print(f"[MySQL Init Warning]: {e} on statement: {stmt[:60]}...")
        finally:
            conn.close()
    else:
        schema_file = os.path.join(base_dir, 'sqlite_schema.sql')
        conn = get_sqlite_connection()
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                content = f.read()
            conn.executescript(content)
            conn.commit()
        finally:
            conn.close()
