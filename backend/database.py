import os
import uuid
import bcrypt
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Get database connection URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:psqlpassword@localhost:5432/resumesearch")
DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "official").lower().strip()
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "Official@121")
DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "official@idealtechlabs.com")

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
# No default accounts — all users must register.

_FALLBACK_USERS = {
    DEFAULT_ADMIN_USERNAME: {
        "id": str(uuid.uuid4()),
        "username": DEFAULT_ADMIN_USERNAME,
        "email": DEFAULT_ADMIN_EMAIL,
        "password": hash_password(DEFAULT_ADMIN_PASSWORD),
        "role": "official",
        "name": "Official Admin",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "is_deleted": False,
        "deleted_at": None
    }
}
_FALLBACK_MESSAGES = []
_FALLBACK_REPLIES = []
_FALLBACK_JD = []
_FALLBACK_ACTIVITIES = []

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
    """Initialize database tables using db_setup.sql."""
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
            cursor.execute(
                """
                INSERT INTO users (username, email, password, role, name)
                VALUES (%s, %s, %s, 'official', 'Official Admin')
                ON CONFLICT (username) DO UPDATE
                SET email = EXCLUDED.email,
                    password = EXCLUDED.password,
                    role = 'official',
                    name = 'Official Admin',
                    is_deleted = FALSE,
                    deleted_at = NULL,
                    updated_at = NOW()
                """,
                (
                    DEFAULT_ADMIN_USERNAME,
                    DEFAULT_ADMIN_EMAIL,
                    hash_password(DEFAULT_ADMIN_PASSWORD)
                )
            )
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

def create_user(username, password, role, name, email=""):
    """Insert a new user with a bcrypt-hashed password and email."""
    conn = None
    username_clean = username.lower().strip()
    hashed = hash_password(password)
    try:
        conn = get_connection()
        if not conn:
            _FALLBACK_USERS[username_clean] = {
                "id": str(uuid.uuid4()),
                "username": username_clean,
                "email": email,
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
                "INSERT INTO users (username, email, password, role, name) VALUES (%s, %s, %s, %s, %s)",
                (username_clean, email, hashed, role, name)
            )
            return True
    except Exception as e:
        print(f"Error creating user in database (using fallback): {e}")
        _FALLBACK_USERS[username_clean] = {
            "id": str(uuid.uuid4()),
            "username": username_clean,
            "email": email,
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

def save_message(sender_name, sender_email, subject, message, sender_username=""):
    """Insert a message record. ID and timestamps are handled by the DB."""
    conn = None
    fallback_id = str(uuid.uuid4())
    new_msg = {
        "id": fallback_id,
        "sender_name": sender_name,
        "sender_email": sender_email,
        "sender_username": sender_username,
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
                "INSERT INTO messages (sender_name, sender_email, sender_username, subject, message) VALUES (%s, %s, %s, %s, %s)",
                (sender_name, sender_email, sender_username, subject, message)
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
# REPLY HELPERS
# ==========================================

def save_reply(message_id, sender_username, reply_text, is_faq: bool = False):
    """Insert a reply to a specific message. Returns the reply ID or None.
    
    Args:
        message_id: UUID of the original candidate message.
        sender_username: Username of the official sending the reply.
        reply_text: The reply content.
        is_faq: If True, this Q&A pair is published to the public FAQ section.
    """
    conn = None
    fallback_id = str(uuid.uuid4())
    new_reply = {
        "id": fallback_id,
        "message_id": message_id,
        "sender_username": sender_username,
        "reply_text": reply_text,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "is_deleted": False,
        "is_faq": is_faq
    }
    try:
        conn = get_connection()
        if not conn:
            _FALLBACK_REPLIES.append(new_reply)
            return fallback_id
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO replies (message_id, sender_username, reply_text, is_faq) VALUES (%s, %s, %s, %s) RETURNING id",
                (message_id, sender_username, reply_text, is_faq)
            )
            row = cursor.fetchone()
            return str(row[0]) if row else fallback_id
    except Exception as e:
        print(f"Error saving reply (using fallback): {e}")
        _FALLBACK_REPLIES.append(new_reply)
        return fallback_id
    finally:
        if conn:
            conn.close()

def get_replies_for_user(username):
    """Retrieve all replies directed to messages sent by a specific candidate username."""
    conn = None
    username_clean = username.lower().strip()
    try:
        conn = get_connection()
        if not conn:
            # Fallback: find message IDs for this user, then find replies
            user_msg_ids = {m["id"] for m in _FALLBACK_MESSAGES
                           if m.get("sender_username", "").lower() == username_clean
                           and not m.get("is_deleted", False)}
            replies = [r for r in _FALLBACK_REPLIES
                       if r["message_id"] in user_msg_ids and not r.get("is_deleted", False)]
            return list(reversed(replies))
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT r.*, m.subject AS original_subject, m.message AS original_message
                FROM replies r
                JOIN messages m ON r.message_id = m.id
                WHERE LOWER(m.sender_username) = %s
                  AND r.is_deleted = FALSE
                  AND m.is_deleted = FALSE
                ORDER BY r.created_at DESC
                """,
                (username_clean,)
            )
            return _serialize_rows(cursor.fetchall())
    except Exception as e:
        print(f"Error getting replies for user (using fallback): {e}")
        user_msg_ids = {m["id"] for m in _FALLBACK_MESSAGES
                       if m.get("sender_username", "").lower() == username_clean
                       and not m.get("is_deleted", False)}
        replies = [r for r in _FALLBACK_REPLIES
                   if r["message_id"] in user_msg_ids and not r.get("is_deleted", False)]
        return list(reversed(replies))
    finally:
        if conn:
            conn.close()

def get_replies_for_message(message_id):
    """Retrieve all non-deleted replies for a specific message."""
    conn = None
    try:
        conn = get_connection()
        if not conn:
            replies = [r for r in _FALLBACK_REPLIES
                       if r["message_id"] == message_id and not r.get("is_deleted", False)]
            return replies
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM replies WHERE message_id = %s AND is_deleted = FALSE ORDER BY created_at ASC",
                (message_id,)
            )
            return _serialize_rows(cursor.fetchall())
    except Exception as e:
        print(f"Error getting replies for message (using fallback): {e}")
        replies = [r for r in _FALLBACK_REPLIES
                   if r["message_id"] == message_id and not r.get("is_deleted", False)]
        return replies
    finally:
        if conn:
            conn.close()

def get_faq_entries():
    """Retrieve all public FAQ entries (replies marked is_faq=TRUE), newest first.
    
    Returns a list of dicts containing:
        - id, reply_text, sender_username, created_at (from replies)
        - original_subject, original_message (from the joined messages row)
    This endpoint is intentionally public — no auth required.
    """
    conn = None
    try:
        conn = get_connection()
        if not conn:
            # In-memory fallback: join replies + messages manually
            faq_entries = []
            for r in _FALLBACK_REPLIES:
                if r.get("is_faq") and not r.get("is_deleted", False):
                    # Find the original message
                    orig = next(
                        (m for m in _FALLBACK_MESSAGES
                         if m["id"] == r["message_id"] and not m.get("is_deleted", False)),
                        None
                    )
                    entry = dict(r)
                    entry["original_subject"] = orig["subject"] if orig else ""
                    entry["original_message"] = orig["message"] if orig else ""
                    faq_entries.append(entry)
            return list(reversed(faq_entries))
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT
                    r.id,
                    r.reply_text,
                    r.sender_username,
                    r.created_at,
                    r.is_faq,
                    m.subject  AS original_subject,
                    m.message  AS original_message
                FROM replies r
                JOIN messages m ON r.message_id = m.id
                WHERE r.is_faq = TRUE
                  AND r.is_deleted = FALSE
                  AND m.is_deleted = FALSE
                ORDER BY r.created_at DESC
                """
            )
            return _serialize_rows(cursor.fetchall())
    except Exception as e:
        print(f"Error getting FAQ entries (using fallback): {e}")
        # Fallback on DB error
        faq_entries = []
        for r in _FALLBACK_REPLIES:
            if r.get("is_faq") and not r.get("is_deleted", False):
                orig = next(
                    (m for m in _FALLBACK_MESSAGES
                     if m["id"] == r["message_id"] and not m.get("is_deleted", False)),
                    None
                )
                entry = dict(r)
                entry["original_subject"] = orig["subject"] if orig else ""
                entry["original_message"] = orig["message"] if orig else ""
                faq_entries.append(entry)
        return list(reversed(faq_entries))
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

# ==========================================
# ACTIVITY LOG HELPERS
# ==========================================

def log_activity(activity_type: str, message: str, performed_by: str = "system") -> None:
    """Append a recruitment activity record. Silently swallows all errors so
    this call never interrupts the caller's main operation."""
    conn = None
    try:
        conn = get_connection()
        if not conn:
            _FALLBACK_ACTIVITIES.append({
                "id": str(uuid.uuid4()),
                "activity_type": activity_type,
                "message": message,
                "performed_by": performed_by,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            return
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO activities (activity_type, message, performed_by) VALUES (%s, %s, %s)",
                (activity_type, message, performed_by)
            )
    except Exception as e:
        print(f"[Activity Log Warning] Could not write activity '{activity_type}': {e}")
        try:
            _FALLBACK_ACTIVITIES.append({
                "id": str(uuid.uuid4()),
                "activity_type": activity_type,
                "message": message,
                "performed_by": performed_by,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception:
            pass
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def get_recent_activities(limit: int = 10) -> list:
    """Retrieve the most recent recruitment activities, newest first."""
    conn = None
    try:
        conn = get_connection()
        if not conn:
            return list(reversed(_FALLBACK_ACTIVITIES))[:limit]
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM activities ORDER BY created_at DESC LIMIT %s",
                (limit,)
            )
            return _serialize_rows(cursor.fetchall())
    except Exception as e:
        print(f"Error fetching recent activities (using fallback): {e}")
        return list(reversed(_FALLBACK_ACTIVITIES))[:limit]
    finally:
        if conn:
            conn.close()


def delete_faq_by_id(faq_id: str) -> bool:
    """Unpublish a FAQ entry: sets is_faq=FALSE and is_deleted=TRUE on the reply.
    The reply remains visible to the original candidate via their private feed
    but is removed from the public GET /api/faq endpoint."""
    conn = None
    try:
        conn = get_connection()
        if not conn:
            for r in _FALLBACK_REPLIES:
                if r["id"] == faq_id:
                    r["is_faq"] = False
                    r["is_deleted"] = True
            return True
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE replies SET is_faq = FALSE, is_deleted = TRUE WHERE id = %s",
                (faq_id,)
            )
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Error unpublishing FAQ (using fallback): {e}")
        for r in _FALLBACK_REPLIES:
            if r["id"] == faq_id:
                r["is_faq"] = False
                r["is_deleted"] = True
        return True
    finally:
        if conn:
            conn.close()
