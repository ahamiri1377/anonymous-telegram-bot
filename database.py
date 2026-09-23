import sqlite3
import secrets

DB_NAME = "bot.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            anonymous_code TEXT UNIQUE NOT NULL,
            first_name TEXT,
            username TEXT
        )
    """)

    try:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN username TEXT"
        )
    except sqlite3.OperationalError:
        pass
    # Conversations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            conversation_id TEXT PRIMARY KEY,
            user_a INTEGER NOT NULL,
            user_b INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'active'
        )
    """)

    # Blocks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blocks (
            blocker_id INTEGER NOT NULL,
            blocked_id INTEGER NOT NULL,
            UNIQUE(blocker_id, blocked_id)
        )
    """)

    # Messages
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            message_id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            message_type TEXT NOT NULL,
            message_text TEXT,
            file_id TEXT,
            caption TEXT,
            status TEXT NOT NULL DEFAULT 'unread'
        )
    """)

    conn.commit()
    conn.close()


# =========================
# USERS
# =========================

def create_user(
    user_id,
    anonymous_code,
    first_name,
    username
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO users
        (user_id, anonymous_code, first_name, username)
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            anonymous_code,
            first_name,
            username
        )
    )

    conn.commit()
    conn.close()

def get_user_by_code(anonymous_code):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT user_id
        FROM users
        WHERE anonymous_code = ?
        """,
        (anonymous_code,)
    )

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None


def get_user_code(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT anonymous_code
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    )

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None


def get_user_name(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT first_name
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    )

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else "کاربر"


def get_username(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT username
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    )

    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]

    return None

# =========================
# CONVERSATIONS
# =========================

def create_conversation(user_a, user_b):
    conversation_id = secrets.token_urlsafe(12)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO conversations
        (conversation_id, user_a, user_b)
        VALUES (?, ?, ?)
        """,
        (conversation_id, user_a, user_b)
    )

    conn.commit()
    conn.close()

    return conversation_id


def get_conversation(conversation_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT conversation_id, user_a, user_b, status
        FROM conversations
        WHERE conversation_id = ?
        """,
        (conversation_id,)
    )

    result = cursor.fetchone()
    conn.close()

    return result


def close_conversation(conversation_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE conversations
        SET status = 'closed'
        WHERE conversation_id = ?
        """,
        (conversation_id,)
    )

    conn.commit()
    conn.close()


# =========================
# BLOCK
# =========================

def add_block(blocker_id, blocked_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO blocks
        (blocker_id, blocked_id)
        VALUES (?, ?)
        """,
        (blocker_id, blocked_id)
    )

    conn.commit()
    conn.close()


def is_blocked(user_a, user_b):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT 1
        FROM blocks
        WHERE blocker_id = ?
        AND blocked_id = ?
        """,
        (user_a, user_b)
    )

    result = cursor.fetchone()
    conn.close()

    return result is not None


# =========================
# MESSAGES
# =========================

def create_message(
    conversation_id,
    sender_id,
    receiver_id,
    message_type,
    message_text=None,
    file_id=None,
    caption=None
):
    message_id = secrets.token_urlsafe(12)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO messages
        (
            message_id,
            conversation_id,
            sender_id,
            receiver_id,
            message_type,
            message_text,
            file_id,
            caption,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'unread')
        """,
        (
            message_id,
            conversation_id,
            sender_id,
            receiver_id,
            message_type,
            message_text,
            file_id,
            caption
        )
    )

    conn.commit()
    conn.close()

    return message_id


def get_message(message_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            message_id,
            conversation_id,
            sender_id,
            receiver_id,
            message_type,
            message_text,
            file_id,
            caption,
            status
        FROM messages
        WHERE message_id = ?
        """,
        (message_id,)
    )

    result = cursor.fetchone()
    conn.close()

    return result


def mark_message_seen(message_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE messages
        SET status = 'seen'
        WHERE message_id = ?
        """,
        (message_id,)
    )

    conn.commit()
    conn.close()


def clear_blocks(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM blocks
        WHERE blocker_id = ?
        """,
        (user_id,)
    )

    conn.commit()
    conn.close()

def get_block_count(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM blocks
        WHERE blocker_id = ?
        """,
        (user_id,)
    )

    count = cursor.fetchone()[0]

    conn.close()

    return count