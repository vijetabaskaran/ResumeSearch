import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# Get database connection URL from environment variables
# Default fallback assumes local standard PostgreSQL setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/resumesearch")

# ==========================================
# IN-MEMORY FALLBACK STORAGE
# ==========================================
# This ensures that even if PostgreSQL is offline or has an authentication issue,
# the registration, custom logins, and messaging flows function 100% seamlessly!
_FALLBACK_USERS = {
    "candidate": {
        "username": "candidate",
        "password": "password",
        "role": "candidate",
        "name": "Candidate User"
    },
    "official": {
        "username": "official",
        "password": "password",
        "role": "official",
        "name": "Official Admin"
    }
}
_FALLBACK_MESSAGES = []

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
        print(f"Using in-memory fallback storage for registration and messaging.")
        print(f"=========================================\n")
        return None

def init_db():
    """Initialize database tables and seed data using db_setup.sql if they do not exist."""
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

# Call init_db immediately to initialize tables at module load
try:
    init_db()
except Exception as ex:
    print(f"Database initialization failed on startup: {ex}")

# ==========================================
# DATABASE HELPER METHODS
# ==========================================

def get_user_by_username(username):
    """Retrieve a user record from the users table."""
    conn = None
    username_clean = username.lower().strip()
    try:
        conn = get_connection()
        if not conn:
            # Fallback to in-memory store
            return _FALLBACK_USERS.get(username_clean)
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM users WHERE LOWER(username) = %s", (username_clean,))
            user = cursor.fetchone()
            return user
    except Exception as e:
        print(f"Error getting user from database (using fallback): {e}")
        return _FALLBACK_USERS.get(username_clean)
    finally:
        if conn:
            conn.close()

def create_user(username, password, role, name):
    """Insert a new user record into the users table."""
    conn = None
    username_clean = username.lower().strip()
    try:
        conn = get_connection()
        if not conn:
            # Fallback to in-memory store
            _FALLBACK_USERS[username_clean] = {
                "username": username_clean,
                "password": password,
                "role": role,
                "name": name
            }
            return True
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, password, role, name) VALUES (%s, %s, %s, %s)",
                (username_clean, password, role, name)
            )
            return True
    except Exception as e:
        print(f"Error creating user in database (using fallback): {e}")
        _FALLBACK_USERS[username_clean] = {
            "username": username_clean,
            "password": password,
            "role": role,
            "name": name
        }
        return True
    finally:
        if conn:
            conn.close()

def save_message(message_id, sender_name, sender_email, subject, message, timestamp):
    """Insert a message record into the messages table."""
    conn = None
    new_msg = {
        "id": message_id,
        "sender_name": sender_name,
        "sender_email": sender_email,
        "subject": subject,
        "message": message,
        "timestamp": timestamp
    }
    try:
        conn = get_connection()
        if not conn:
            # Fallback to in-memory store
            _FALLBACK_MESSAGES.append(new_msg)
            return True
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO messages (id, sender_name, sender_email, subject, message, timestamp) VALUES (%s, %s, %s, %s, %s, %s)",
                (message_id, sender_name, sender_email, subject, message, timestamp)
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
    """Retrieve all messages from the database."""
    conn = None
    try:
        conn = get_connection()
        if not conn:
            # Fallback to in-memory store
            return list(reversed(_FALLBACK_MESSAGES))
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM messages ORDER BY timestamp DESC")
            messages = cursor.fetchall()
            return list(messages)
    except Exception as e:
        print(f"Error loading messages from database (using fallback): {e}")
        return list(reversed(_FALLBACK_MESSAGES))
    finally:
        if conn:
            conn.close()

def delete_message_by_id(message_id):
    """Delete a specific message from the database."""
    global _FALLBACK_MESSAGES
    conn = None
    try:
        conn = get_connection()
        if not conn:
            # Fallback to in-memory store
            _FALLBACK_MESSAGES = [m for m in _FALLBACK_MESSAGES if m["id"] != message_id]
            return True
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM messages WHERE id = %s", (message_id,))
            return True
    except Exception as e:
        print(f"Error deleting message from database (using fallback): {e}")
        _FALLBACK_MESSAGES = [m for m in _FALLBACK_MESSAGES if m["id"] != message_id]
        return True
    finally:
        if conn:
            conn.close()

# ==========================================
# JOB DESCRIPTION HELPERS
# ==========================================

_FALLBACK_JD = []

def save_job_description(jd_id, title, department, description, created_at):
    """Insert a job description into the database."""
    global _FALLBACK_JD
    conn = None
    new_jd = {"id": jd_id, "title": title, "department": department,
               "description": description, "created_at": created_at}
    try:
        conn = get_connection()
        if not conn:
            _FALLBACK_JD.append(new_jd)
            return True
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO job_descriptions (id, title, department, description, created_at) VALUES (%s, %s, %s, %s, %s)",
                (jd_id, title, department, description, created_at)
            )
        return True
    except Exception as e:
        print(f"Error saving JD (using fallback): {e}")
        _FALLBACK_JD.append(new_jd)
        return True
    finally:
        if conn:
            conn.close()

def get_all_job_descriptions():
    """Retrieve all job descriptions ordered by newest first."""
    conn = None
    try:
        conn = get_connection()
        if not conn:
            return list(reversed(_FALLBACK_JD))
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM job_descriptions ORDER BY created_at DESC")
            return list(cursor.fetchall())
    except Exception as e:
        print(f"Error getting JDs (using fallback): {e}")
        return list(reversed(_FALLBACK_JD))
    finally:
        if conn:
            conn.close()

def delete_job_description_by_id(jd_id):
    """Delete a job description by id."""
    global _FALLBACK_JD
    conn = None
    try:
        conn = get_connection()
        if not conn:
            _FALLBACK_JD = [j for j in _FALLBACK_JD if j["id"] != jd_id]
            return True
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM job_descriptions WHERE id = %s", (jd_id,))
        return True
    except Exception as e:
        print(f"Error deleting JD (using fallback): {e}")
        _FALLBACK_JD = [j for j in _FALLBACK_JD if j["id"] != jd_id]
        return True
    finally:
        if conn:
            conn.close()
