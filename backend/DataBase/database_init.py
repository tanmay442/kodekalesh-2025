# initialize_db.py

import sqlite3

DB_FILE = "backend/DataBase/database.db"


# --- Individual Table Creation Functions ---

def create_users_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            user_id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("Users table ready.")


def create_cases_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Cases (
            case_id TEXT PRIMARY KEY,
            case_name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Open',
            creator_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (creator_id) REFERENCES Users (user_id)
        );
    """)
    print("Cases table ready.")


def create_documents_table(conn,case_id_for_naming):
    cursor = conn.cursor()
    # sanitize the case id fragment to safe identifier characters (alphanumeric and underscore)
    suffix = ''.join(c for c in str(case_id_for_naming) if c.isalnum() or c == '_')
    if not suffix:
        suffix = 'default'
    table_name = f"Documents_{suffix}"
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            doc_id TEXT PRIMARY KEY,
            case_id TEXT NOT NULL,
            uploader_id TEXT NOT NULL,
            file_name TEXT NOT NULL,
            storage_path TEXT UNIQUE NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES Cases (case_id),
            FOREIGN KEY (uploader_id) REFERENCES Users (user_id)
        );
    """)
    print("Documents table ready.")


def create_case_access_permissions_table(conn,case_id_for_naming):
    cursor = conn.cursor()
    # sanitize the case id fragment to safe identifier characters (alphanumeric and underscore)
    suffix = ''.join(c for c in str(case_id_for_naming) if c.isalnum() or c == '_')
    if not suffix:
        suffix = 'default'
    table_name = f"CaseAccessPermissions_{suffix}"
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            case_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            access_level TEXT NOT NULL,
            FOREIGN KEY (case_id) REFERENCES Cases (case_id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE,
            UNIQUE (case_id, user_id)
        );
    """)
    print("CaseAccessPermissions table ready.")





# --- Main Orchestration Function ---

def create_database():
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        print("Connected to SQLite database.")
        conn.execute("PRAGMA foreign_keys = ON;")

        # Create all tables
        create_users_table(conn)
        create_cases_table(conn)
        #create_documents_table(conn)
        #create_case_access_permissions_table(conn)
       

        conn.commit()
        print("All tables created successfully.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
            print("SQLite connection closed.")


if __name__ == '__main__':
    create_database()
