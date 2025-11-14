# Case Management System

A Flask-based web application for managing legal cases, documents, and user permissions in a secure, role-based environment.

## Overview

This system allows legal professionals (advocates, judges, government agencies, and private intelligence firms) to collaborate on cases. It features user authentication, case creation and management, document uploads/downloads, and granular permission controls.

## Features

- **User Authentication**: Secure registration and login with bcrypt password hashing
- **Role-Based Access Control**: Four user roles with different permissions
- **Case Management**: Create, view, and update case statuses
- **Document Management**: Upload and download case-related documents
- **Permission System**: Granular access control per case (view_only, upload_only, sudo)
- **User Search**: Find users by email for collaboration
- **Session Management**: Secure session-based authentication

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Authentication**: bcrypt for password hashing, Flask sessions
- **File Storage**: Local filesystem with secure filename generation
- **Frontend**: React (separate frontend directory)

## Installation and Setup

1. **Prerequisites**:
   - Python 3.7+
   - Node.js (for frontend)

2. **Backend Setup**:
   ```bash
   cd backend
   pip install -r requirements.txt
   python DataBase/database_init.py  # Initialize database
   python app/app.py  # Run backend on port 5001
   ```

3. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Database Initialization**:
   Run `python backend/DataBase/database_init.py` to create the necessary tables.

## Database Schema

### Users Table
- `user_id` (TEXT PRIMARY KEY): Unique user identifier
- `email` (TEXT UNIQUE): User's email address
- `hashed_password` (TEXT): bcrypt-hashed password
- `full_name` (TEXT): User's full name
- `role` (TEXT): User role (advocate, judge, government_agency, private_intel)
- `created_at` (TIMESTAMP): Account creation timestamp

### Cases Table
- `case_id` (TEXT PRIMARY KEY): Unique case identifier
- `case_name` (TEXT): Name of the case
- `status` (TEXT): Case status (default: 'Open')
- `creator_id` (TEXT): ID of the user who created the case
- `created_at` (TIMESTAMP): Case creation timestamp

### Documents Table
- `doc_id` (TEXT PRIMARY KEY): Unique document identifier
- `case_id` (TEXT): Associated case ID
- `uploader_id` (TEXT): ID of the user who uploaded the document
- `file_name` (TEXT): Original filename
- `storage_path` (TEXT UNIQUE): Secure storage path
- `uploaded_at` (TIMESTAMP): Upload timestamp

### Permissions Tables
Dynamic tables created per case: `CaseAccessPermissions_{case_id}`
- `case_id` (TEXT): Case identifier
- `user_id` (TEXT): User with access
- `access_level` (TEXT): Permission level (view_only, upload_only, sudo)

## API Endpoints

### Authentication
- `POST /api/register`: Register a new user
- `POST /api/login`: User login
- `POST /api/logout`: User logout
- `GET /api/session`: Check current session

### Users
- `GET /api/user/<user_id>`: Get user details
- `GET /api/users/search?email=<query>`: Search users by email

### Cases
- `POST /api/cases`: Create a new case (judges/advocates only)
- `GET /api/cases`: Get user's accessible cases
- `GET /api/case/<case_id>`: Get case details
- `PUT /api/case/<case_id>/status`: Update case status

### Permissions
- `GET /api/case/<case_id>/permissions`: Get case permissions
- `POST /api/case/<case_id>/grant-access`: Grant user access to case

### Documents
- `GET /api/case/<case_id>/documents`: Get case documents
- `POST /api/case/<case_id>/upload`: Upload document to case
- `GET /api/document/<doc_id>/download`: Download document

## Code Structure and Functions

### backend/app/app.py

Main Flask application with all API routes.

**Key Functions:**
- `row_to_dict(row)`: Converts SQLite Row objects to dictionaries for JSON responses
- `login_required(f)`: Decorator that requires user authentication for routes
- Authentication routes: `register()`, `login()`, `logout()`, `check_session()`
- User routes: `get_user(user_id)`, `search_users()`
- Case routes: `create_case()`, `get_cases()`, `get_case(case_id)`, `update_case_status(case_id)`
- Permission routes: `get_case_permissions(case_id)`, `grant_case_access(case_id)`
- Document routes: `get_documents(case_id)`, `upload_document(case_id)`, `download_document(doc_id)`

### backend/functions/database/user_manager.py

Handles all user-related database operations.

**Functions:**
- `get_db_connection()`: Creates SQLite connection with Row factory
- `create_user(email, password, full_name, role)`: Creates new user with hashed password, returns user_id or None if email exists
- `find_user_by_email(email)`: Retrieves user by email
- `find_user_by_id(user_id)`: Retrieves user by ID (excludes password)
- `verify_password(stored_hash, provided_password)`: Verifies password against hash
- `search_users_by_email(email_query)`: Searches users by partial email match (limited to 10 results)

### backend/functions/database/cases_manager.py

Manages case-related database operations.

**Functions:**
- `get_db_connection()`: Creates SQLite connection with Row factory
- `create_case(case_name, creator_id)`: Creates new case, generates UUID, grants creator sudo access, returns case_id
- `get_all_cases()`: Retrieves all cases ordered by creation date (descending)
- `get_user_cases(user_id)`: Gets cases user has access to by querying permission tables
- `get_case_by_id(case_id)`: Retrieves single case by ID
- `update_case_status(case_id, status)`: Updates case status, returns success boolean

### backend/functions/database/document_manager.py

Handles document-related database operations.

**Functions:**
- `get_db_connection()`: Creates SQLite connection
- `add_document(case_id, uploader_id, file_name, storage_path)`: Adds document record, generates UUID, returns doc_id
- `get_case_documents(case_id)`: Retrieves all documents for a case ordered by upload date
- `get_document_by_id(doc_id)`: Retrieves single document by ID

### backend/functions/database/permissions_manager.py

Manages case access permissions with dynamic tables.

**Functions:**
- `get_db_connection()`: Creates SQLite connection with Row factory
- `sanitize_case_id(case_id)`: Removes hyphens for valid table names
- `get_permissions_table_name(case_id)`: Generates table name for case permissions
- `create_permissions_table(case_id)`: Creates permission table for case if it doesn't exist
- `grant_access(case_id, user_id, access_level)`: Grants or updates user access, creates table if needed
- `check_access(case_id, user_id)`: Checks if user has any access to case
- `get_user_access_level(case_id, user_id)`: Gets specific access level for user on case
- `get_case_permissions(case_id)`: Gets all permissions for case with user details

### backend/DataBase/database_init.py

Database initialization script.

**Functions:**
- `create_tables()`: Creates Users, Cases, and Documents tables with proper constraints and foreign keys

## How It Works

1. **User Registration/Login**: Users register with email, password, name, and role. Passwords are hashed with bcrypt. Sessions maintain authentication state.

2. **Case Creation**: Authorized users (judges/advocates) create cases. Creator automatically gets sudo permissions. Each case gets a unique UUID.

3. **Permission Management**: Each case has its own permission table. Users can be granted view_only, upload_only, or sudo access. Judges and sudo users can grant permissions.

4. **Document Handling**: Users with upload permissions can upload files. Files are stored with secure, unique filenames (timestamp + case_id + user_id + original_name). Database tracks metadata.

5. **Access Control**: All routes check user authentication and permissions. Judges see all cases; others see only accessible ones. Document access requires case access.

6. **Security**: Passwords hashed, filenames secured, session-based auth, role and permission checks on all operations.

## Security Considerations

- Passwords are hashed with bcrypt
- File uploads use secure filename generation
- Session-based authentication with secret key
- Role-based and permission-based access control
- SQL injection prevention with parameterized queries
- Foreign key constraints and data validation

## Development Notes

- Database path is constructed relative to script locations
- Upload folder is created automatically if it doesn't exist
- SQLite Row factory used for dict-like access to results
- Dynamic permission tables allow flexible per-case access control
- UUIDs used for all primary keys to prevent enumeration attacks