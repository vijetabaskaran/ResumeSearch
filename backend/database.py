import os
import uuid
import bcrypt
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Get database connection URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/resumesearch")

# ==========================================
# PASSWORD HASHING UTILITIES
# ==========================================

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

# ==========================================
# IN-MEMORY FALLBACK STORAGE
# ==========================================
# Ensures the app works even if PostgreSQL is offline.

_DEMO_HASH = hash_password("password")

_FALLBACK_USERS = {
    "candidate": {
        "id": str(uuid.uuid4()),
        "username": "candidate",
        "password": _DEMO_HASH,
        "role": "candidate",
        "name": "Candidate User",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "is_deleted": False,
        "deleted_at": None
    },
    "official": {
        "id": str(uuid.uuid4()),
        "username": "official",
        "password": _DEMO_HASH,
        "role": "official",
        "name": "Official Admin",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "is_deleted": False,
        "deleted_at": None
    }
}
_FALLBACK_MESSAGES = []
_FALLBACK_JD = []

# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_connection():
    """Establish a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"\n=========================================")
        print(f"DATABASE CONNECTION WARNING:")
        print(f"Failed to connect to PostgreSQL using: {DATABASE_URL}")
        print(f"Details: {e}")
        print(f"Using in-memory fallback storage.")
        print(f"=========================================\n")
        return None

# ==========================================
# SERIALIZATION HELPERS
# ==========================================

def _serialize_row(row):
    """Convert a RealDictRow so UUID and datetime fields become JSON-safe strings."""
    if row is None:
        return None
    result = dict(row)
    for key, value in result.items():
        if isinstance(value, uuid.UUID):
            result[key] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.strftime("%Y-%m-%d %H:%M:%S")
    return result

def _serialize_rows(rows):
    """Serialize a list of RealDictRows."""
    return [_serialize_row(r) for r in rows]

# ==========================================
# DATABASE INITIALIZATION
# ==========================================

def init_db():
    """Initialize database tables and seed data using db_setup.sql."""
    print("Initializing PostgreSQL Database...")
    sql_file_path = os.path.join(os.path.dirname(__file__), "db_setup.sql")

    if not os.path.exists(sql_file_path):
        print(f"Warning: {sql_file_path} not found. Skipping auto DDL creation.")
        return

    try:
        conn = get_connection()
        if not conn:
            print("Database offline/unauthenticated. Skipping initialization.")
            return
        conn.autocommit = True
        with conn.cursor() as cursor:
            with open(sql_file_path, "r") as f:
                sql_script = f.read()
            cursor.execute(sql_script)
        conn.close()
        print("PostgreSQL Database initialized successfully.")
    except Exception as e:
        print(f"Error during database initialization: {e}")

# Call init_db immediately at module load
try:
    init_db()
except Exception as ex:
    print(f"Database initialization failed on startup: {ex}")

# ==========================================
# USER HELPERS
# ==========================================

def get_user_by_username(username):
    """Retrieve a non-deleted user record by username."""
    conn = None
    username_clean = username.lower().strip()
    try:
        conn = get_connection()
        if not conn:
            user = _FALLBACK_USERS.get(username_clean)
            if user and not user.get("is_deleted", False):
                return dict(user)
            return None
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE LOWER(username) = %s AND is_deleted = FALSE",
                (username_clean,)
            )
            user = cursor.fetchone()
            return _serialize_row(user)
    except Exception as e:
        print(f"Error getting user from database (using fallback): {e}")
        user = _FALLBACK_USERS.get(username_clean)
        if user and not user.get("is_deleted", False):
            return dict(user)
        return None
    finally:
        if conn:
            conn.close()

def create_user(username, password, role, name):
    """Insert a new user with a bcrypt-hashed password."""
    conn = None
    username_clean = username.lower().strip()
    hashed = hash_password(password)
    try:
        conn = get_connection()
        if not conn:
            _FALLBACK_USERS[username_clean] = {
                "id": str(uuid.uuid4()),
                "username": username_clean,
                "password": hashed,
                "role": role,
                "name": name,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "is_deleted": False,
                "deleted_at": None
            }
            return True
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, password, role, name) VALUES (%s, %s, %s, %s)",
                (username_clean, hashed, role, name)
            )
            return True
    except Exception as e:
        print(f"Error creating user in database (using fallback): {e}")
        _FALLBACK_USERS[username_clean] = {
            "id": str(uuid.uuid4()),
            "username": username_clean,
            "password": hashed,
            "role": role,
            "name": name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "is_deleted": False,
            "deleted_at": None
        }
        return True
    finally:
        if conn:
            conn.close()

# ==========================================
# MESSAGE HELPERS
# ==========================================

def save_message(sender_name, sender_email, subject, message):
    """Insert a message record. ID and timestamps are handled by the DB."""
    conn = None
    fallback_id = str(uuid.uuid4())
    new_msg = {
        "id": fallback_id,
        "sender_name": sender_name,
        "sender_email": sender_email,
        "subject": subject,
        "message": message,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "is_deleted": False,
        "deleted_at": None
    }
    try:
        conn = get_connection()
        if not conn:
            _FALLBACK_MESSAGES.append(new_msg)
            return True
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO messages (sender_name, sender_email, subject, message) VALUES (%s, %s, %s, %s)",
                (sender_name, sender_email, subject, message)
            )
            return True
    except Exception as e:
        print(f"Error saving message to database (using fallback): {e}")
        _FALLBACK_MESSAGES.append(new_msg)
        return True
    finally:
        if conn:
            conn.close()

def get_all_messages():
    """Retrieve all non-deleted messages, newest first."""
    conn = None
    try:
        conn = get_connection()
        if not conn:
            active = [m for m in _FALLBACK_MESSAGES if not m.get("is_deleted", False)]
            return list(reversed(active))
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM messages WHERE is_deleted = FALSE ORDER BY created_at DESC"
            )
            return _serialize_rows(cursor.fetchall())
    except Exception as e:
        print(f"Error loading messages from database (using fallback): {e}")
        active = [m for m in _FALLBACK_MESSAGES if not m.get("is_deleted", False)]
        return list(reversed(active))
    finally:
        if conn:
            conn.close()

def delete_message_by_id(message_id):
    """Soft-delete a message by setting is_deleted=TRUE and deleted_at=NOW()."""
    global _FALLBACK_MESSAGES
    conn = None
    try:
        conn = get_connection()
        if not conn:
            for m in _FALLBACK_MESSAGES:
                if m["id"] == message_id:
                    m["is_deleted"] = True
                    m["deleted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return True
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE messages SET is_deleted = TRUE, deleted_at = NOW(), updated_at = NOW() WHERE id = %s",
                (message_id,)
            )
            return True
    except Exception as e:
        print(f"Error soft-deleting message (using fallback): {e}")
        for m in _FALLBACK_MESSAGES:
            if m["id"] == message_id:
                m["is_deleted"] = True
                m["deleted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return True
    finally:
        if conn:
            conn.close()

# ==========================================
# JOB DESCRIPTION HELPERS
# ==========================================

def save_job_description(title, department, description):
    """Insert a job description. ID and timestamps are handled by the DB.
    Returns the new UUID as a string, or None on failure."""
    global _FALLBACK_JD
    conn = None
    fallback_id = str(uuid.uuid4())
    new_jd = {
        "id": fallback_id,
        "title": title,
        "department": department,
        "description": description,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "is_deleted": False,
        "deleted_at": None
    }
    try:
        conn = get_connection()
        if not conn:
            _FALLBACK_JD.append(new_jd)
            return fallback_id
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO job_descriptions (title, department, description) VALUES (%s, %s, %s) RETURNING id",
                (title, department, description)
            )
            row = cursor.fetchone()
            return str(row[0]) if row else fallback_id
    except Exception as e:
        print(f"Error saving JD (using fallback): {e}")
        _FALLBACK_JD.append(new_jd)
        return fallback_id
    finally:
        if conn:
            conn.close()

def get_all_job_descriptions():
    """Retrieve all non-deleted job descriptions, newest first."""
    conn = None
    try:
        conn = get_connection()
        if not conn:
            active = [j for j in _FALLBACK_JD if not j.get("is_deleted", False)]
            return list(reversed(active))
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM job_descriptions WHERE is_deleted = FALSE ORDER BY created_at DESC"
            )
            return _serialize_rows(cursor.fetchall())
    except Exception as e:
        print(f"Error getting JDs (using fallback): {e}")
        active = [j for j in _FALLBACK_JD if not j.get("is_deleted", False)]
        return list(reversed(active))
    finally:
        if conn:
            conn.close()

def delete_job_description_by_id(jd_id):
    """Soft-delete a job description by setting is_deleted=TRUE and deleted_at=NOW()."""
    global _FALLBACK_JD
    conn = None
    try:
        conn = get_connection()
        if not conn:
            for j in _FALLBACK_JD:
                if j["id"] == jd_id:
                    j["is_deleted"] = True
                    j["deleted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return True
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE job_descriptions SET is_deleted = TRUE, deleted_at = NOW(), updated_at = NOW() WHERE id = %s",
                (jd_id,)
            )
            return True
    except Exception as e:
        print(f"Error soft-deleting JD (using fallback): {e}")
        for j in _FALLBACK_JD:
            if j["id"] == jd_id:
                j["is_deleted"] = True
                j["deleted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return True
    finally:
        if conn:
            conn.close()
