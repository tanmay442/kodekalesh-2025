# user_manager.py

import sqlite3
import uuid
import bcrypt
from datetime import datetime

DB_FILE = "backend/DataBase/database.db"

def create_user(email, password, full_name, role):
    # Creates a new user with a hashed password
    try:
        user_id = str(uuid.uuid4())
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        sql = """
        INSERT INTO Users (user_id, email, hashed_password, full_name, role)
        VALUES (?, ?, ?, ?, ?);
        """
        cursor.execute(sql, (user_id, email, hashed_password.decode('utf-8'), full_name, role))
        conn.commit()
        print(f"User '{full_name}' created successfully with ID: {user_id}")
        return user_id
    except sqlite3.IntegrityError:
        print(f"Error: A user with the email '{email}' already exists.")
        return None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if conn:
            conn.close()


def get_user_by_id(user_id):
    # Retrieves user details by ID and formats timestamp
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        sql = "SELECT user_id, email, full_name, role, created_at FROM Users WHERE user_id = ?;"
        cursor.execute(sql, (user_id,))
        user_row = cursor.fetchone()
        if user_row:
            user_dict = dict(user_row)
            ts_from_db = datetime.strptime(user_dict['created_at'], '%Y-%m-%d %H:%M:%S')
            user_dict['created_at_formatted'] = ts_from_db.strftime('%B %d, %Y at %I:%M %p')
            return user_dict
        else:
            return None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if conn:
            conn.close()


def update_user(user_id, full_name=None, password=None):
    # Updates user's name and/or password
    if not full_name and not password:
        print("No update information provided.")
        return False

    updates, params = [], []
    if full_name:
        updates.append("full_name = ?")
        params.append(full_name)
    if password:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        updates.append("hashed_password = ?")
        params.append(hashed_password.decode('utf-8'))
    params.append(user_id)

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        sql = f"UPDATE Users SET {', '.join(updates)} WHERE user_id = ?;"
        cursor.execute(sql, tuple(params))
        updated_rows = cursor.rowcount
        conn.commit()
        if updated_rows > 0:
            print(f"User {user_id} updated successfully.")
            return True
        else:
            print(f"User {user_id} not found or no changes made.")
            return False
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()


def delete_user(user_id):
    # Deletes user and related records via cascade
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        sql = "DELETE FROM Users WHERE user_id = ?;"
        cursor.execute(sql, (user_id,))
        deleted_rows = cursor.rowcount
        conn.commit()
        if deleted_rows > 0:
            print(f"User {user_id} and all associated permissions deleted successfully.")
            return True
        else:
            print(f"User {user_id} not found.")
            return False
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()


def verify_user_password(email, password):
    # Verifies user password during login
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        sql = "SELECT hashed_password FROM Users WHERE email = ?;"
        cursor.execute(sql, (email,))
        result = cursor.fetchone()
        if result:
            stored_hash = result[0].encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                return True
        return False
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()


