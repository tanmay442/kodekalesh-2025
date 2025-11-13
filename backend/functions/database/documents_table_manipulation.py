# documents_manager.py

import sqlite3
import uuid
import os
from datetime import datetime
from backend.DataBase.database_init import create_documents_table

DB_FILE = "justicelink.db"

def add_document_record(case_id, uploader_id, file_name, storage_path):
    # Adds a document record with current timestamp
    try:
        doc_id = str(uuid.uuid4())
        uploaded_at_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Generate table name based on case_id
        suffix = ''.join(c for c in str(case_id) if c.isalnum() or c == '_')
        if not suffix:
            suffix = 'default'
        table_name = f"Documents_{suffix}"

        # Ensure the table exists using the imported function
        create_documents_table(conn, case_id)

        # Insert the document record
        sql = f"""
        INSERT INTO {table_name} (doc_id, case_id, uploader_id, file_name, storage_path, uploaded_at)
        VALUES (?, ?, ?, ?, ?, ?);
        """
        cursor.execute(sql, (doc_id, case_id, uploader_id, file_name, storage_path, uploaded_at_timestamp))
        conn.commit()
        print(f"Document record '{file_name}' added successfully.")
        return doc_id
    except sqlite3.IntegrityError:
        print("Error: Could not add document. Ensure case_id and uploader_id exist.")
        return None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        if conn:
            conn.close()


def get_documents_for_case(case_id):
    # Retrieves all documents linked to a specific case
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        sql = "SELECT * FROM Documents WHERE case_id = ? ORDER BY uploaded_at;"
        cursor.execute(sql, (case_id,))
        documents = [dict(row) for row in cursor.fetchall()]
        return documents
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    finally:
        if conn:
            conn.close()


def delete_document_record(doc_id):
    # Deletes a document record and its physical file
    storage_path_to_delete = None
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        cursor.execute("SELECT storage_path FROM Documents WHERE doc_id = ?;", (doc_id,))
        result = cursor.fetchone()
        if result:
            storage_path_to_delete = result['storage_path']

        sql = "DELETE FROM Documents WHERE doc_id = ?;"
        cursor.execute(sql, (doc_id,))
        deleted_rows = cursor.rowcount
        conn.commit()

        if deleted_rows > 0 and storage_path_to_delete and os.path.exists(storage_path_to_delete):
            os.remove(storage_path_to_delete)
            print(f"Document record {doc_id} and physical file deleted.")
            return True
        elif deleted_rows > 0:
            print(f"Document record {doc_id} deleted. Physical file not found.")
            return True
        return False
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()


