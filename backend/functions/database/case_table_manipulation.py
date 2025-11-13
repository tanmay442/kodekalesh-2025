# cases_manager.py

import sqlite3
import uuid
from datetime import datetime

DB_FILE = "backend/DataBase/database.db"

def create_case(case_name, creator_id):
    # Creates a new case with default status 'Open' and current timestamp
    try:
        case_id = str(uuid.uuid4())
        status = 'Open'
        created_at_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        sql = """
        INSERT INTO Cases (case_id, case_name, creator_id, status, created_at) 
        VALUES (?, ?, ?, ?, ?);
        """
        cursor.execute(sql, (case_id, case_name, creator_id, status, created_at_timestamp))
        conn.commit()
        print(f"Case '{case_name}' created successfully with ID: {case_id}")
        return case_id
    except sqlite3.IntegrityError:
        print(f"Error: Could not create case. The creator_id '{creator_id}' may not exist.")
        return None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if conn:
            conn.close()


def get_case_by_id(case_id):
    # Retrieves case details by ID
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        sql = "SELECT * FROM Cases WHERE case_id = ?;"
        cursor.execute(sql, (case_id,))
        case_row = cursor.fetchone()
        return dict(case_row) if case_row else None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if conn:
            conn.close()


def update_case_status(case_id, new_status):
    # Updates case status
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        sql = "UPDATE Cases SET status = ? WHERE case_id = ?;"
        cursor.execute(sql, (new_status, case_id))
        updated_rows = cursor.rowcount
        conn.commit()
        return updated_rows > 0
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()


def delete_case(case_id):
    # Deletes a case if no documents are linked
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        sql = "DELETE FROM Cases WHERE case_id = ?;"
        cursor.execute(sql, (case_id,))
        deleted_rows = cursor.rowcount
        conn.commit()
        return deleted_rows > 0
    except sqlite3.IntegrityError:
        print(f"Error: Cannot delete case {case_id} as it still has documents.")
        return False
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()


def list_all_cases():
    # Lists all cases in descending order of creation
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        sql = "SELECT case_id, case_name, status, created_at FROM Cases ORDER BY created_at DESC;"
        cursor.execute(sql)
        cases = [dict(row) for row in cursor.fetchall()]
        return cases
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if conn:
            conn.close()


