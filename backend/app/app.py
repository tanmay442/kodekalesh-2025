import os
import sys
from flask import Flask, jsonify, request, session, send_from_directory
from functools import wraps
import time
from werkzeug.utils import secure_filename

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from functions.database import user_manager, cases_manager, document_manager, permissions_manager

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuration
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Helper to convert sqlite3.Row to dict
def row_to_dict(row):
    if row is None:
        return None
    return dict(row)

# Decorator for private routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

# === AUTHENTICATION ROUTES ===

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    role = data.get('role')

    if not all([email, password, full_name, role]):
        return jsonify({"error": "Missing required fields"}), 400
    
    if role not in ['advocate', 'judge', 'government_agency', 'private_intel']:
        return jsonify({"error": "Invalid role"}), 400

    user_id = user_manager.create_user(email, password, full_name, role)

    if user_id:
        return jsonify({"message": "User created successfully", "user_id": user_id}), 201
    else:
        return jsonify({"error": "User with this email already exists"}), 409

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = user_manager.find_user_by_email(email)

    if user and user_manager.verify_password(user['hashed_password'], password):
        session['user_id'] = user['user_id']
        session['role'] = user['role']
        return jsonify({"message": "Login successful", "user": row_to_dict(user_manager.find_user_by_id(user['user_id']))}), 200
    else:
        return jsonify({"error": "Invalid email or password"}), 401

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    return jsonify({"message": "Logout successful"}), 200

@app.route('/api/session', methods=['GET'])
@login_required
def check_session():
    user = user_manager.find_user_by_id(session['user_id'])
    return jsonify({"user": row_to_dict(user)}), 200

# === USER ROUTES ===

@app.route('/api/user/<user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    user = user_manager.find_user_by_id(user_id)
    if user:
        return jsonify(row_to_dict(user)), 200
    return jsonify({"error": "User not found"}), 404

@app.route('/api/users/search', methods=['GET'])
@login_required
def search_users():
    email_query = request.args.get('email', '')
    if not email_query or len(email_query) < 3:
        return jsonify({"error": "Email query must be at least 3 characters long"}), 400
    
    users = user_manager.search_users_by_email(email_query)
    return jsonify([row_to_dict(user) for user in users]), 200

# === CASE ROUTES ===

@app.route('/api/cases', methods=['POST'])
@login_required
def create_case():
    user_role = session.get('role')
    if user_role not in ['judge', 'advocate']:
        return jsonify({"error": "You do not have permission to create a case"}), 403

    data = request.get_json()
    case_name = data.get('case_name')
    if not case_name:
        return jsonify({"error": "Case name is required"}), 400

    creator_id = session.get('user_id')
    case_id = cases_manager.create_case(case_name, creator_id)

    if case_id:
        return jsonify({"message": "Case created successfully", "case_id": case_id}), 201
    return jsonify({"error": "Failed to create case"}), 500

@app.route('/api/cases', methods=['GET'])
@login_required
def get_cases():
    user_id = session.get('user_id')
    user_role = session.get('role')

    if user_role == 'judge':
        cases = cases_manager.get_all_cases()
    else:
        cases = cases_manager.get_user_cases(user_id)
    
    return jsonify([row_to_dict(case) for case in cases]), 200

@app.route('/api/case/<case_id>', methods=['GET'])
@login_required
def get_case(case_id):
    user_id = session.get('user_id')
    user_role = session.get('role')

    if user_role != 'judge' and not permissions_manager.check_access(case_id, user_id):
        return jsonify({"error": "You do not have access to this case"}), 403

    case = cases_manager.get_case_by_id(case_id)
    if case:
        return jsonify(row_to_dict(case)), 200
    return jsonify({"error": "Case not found"}), 404

@app.route('/api/case/<case_id>/status', methods=['PUT'])
@login_required
def update_case_status(case_id):
    user_id = session.get('user_id')
    user_role = session.get('role')
    access_level = permissions_manager.get_user_access_level(case_id, user_id)

    if user_role not in ['judge', 'advocate'] or (user_role == 'advocate' and access_level not in ['sudo', 'view_only']):
        return jsonify({"error": "You do not have permission to update this case status"}), 403

    data = request.get_json()
    status = data.get('status')
    if not status:
        return jsonify({"error": "Status is required"}), 400

    if cases_manager.update_case_status(case_id, status):
        return jsonify({"message": "Case status updated successfully"}), 200
    return jsonify({"error": "Failed to update case status"}), 500

# === PERMISSIONS ROUTES ===

@app.route('/api/case/<case_id>/permissions', methods=['GET'])
@login_required
def get_case_permissions(case_id):
    user_id = session.get('user_id')
    user_role = session.get('role')

    if user_role != 'judge' and not permissions_manager.check_access(case_id, user_id):
        return jsonify({"error": "You do not have access to this case"}), 403

    permissions = permissions_manager.get_case_permissions(case_id)
    return jsonify([row_to_dict(p) for p in permissions]), 200

@app.route('/api/case/<case_id>/grant-access', methods=['POST'])
@login_required
def grant_case_access(case_id):
    granter_id = session.get('user_id')
    granter_role = session.get('role')
    access_level = permissions_manager.get_user_access_level(case_id, granter_id)

    if granter_role != 'judge' and access_level != 'sudo':
        return jsonify({"error": "You do not have permission to grant access to this case"}), 403

    data = request.get_json()
    target_user_id = data.get('user_id')
    target_access_level = data.get('access_level', 'view_only')

    if not target_user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    if target_access_level not in ['view_only', 'sudo', 'upload_only']:
        return jsonify({"error": "Invalid access level"}), 400

    if permissions_manager.grant_access(case_id, target_user_id, target_access_level):
        return jsonify({"message": "Access granted successfully"}), 200
    return jsonify({"error": "Failed to grant access"}), 500

# === DOCUMENT ROUTES ===

@app.route('/api/case/<case_id>/documents', methods=['GET'])
@login_required
def get_documents(case_id):
    user_id = session.get('user_id')
    user_role = session.get('role')

    if user_role != 'judge' and not permissions_manager.check_access(case_id, user_id):
        return jsonify({"error": "You do not have access to this case"}), 403

    documents = document_manager.get_case_documents(case_id)
    return jsonify([row_to_dict(doc) for doc in documents]), 200

@app.route('/api/case/<case_id>/upload', methods=['POST'])
@login_required
def upload_document(case_id):
    user_id = session.get('user_id')
    user_role = session.get('role')
    access_level = permissions_manager.get_user_access_level(case_id, user_id)

    if user_role != 'judge' and access_level not in ['sudo', 'upload_only']:
        return jsonify({"error": "You do not have permission to upload to this case"}), 403

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        original_filename = secure_filename(file.filename)
        # Generate a secure, unique filename
        timestamp = int(time.time())
        storage_filename = f"{timestamp}_{case_id}_{user_id}_{original_filename}"
        storage_path = os.path.join(app.config['UPLOAD_FOLDER'], storage_filename)
        
        file.save(storage_path)

        doc_id = document_manager.add_document(case_id, user_id, original_filename, storage_path)
        if doc_id:
            return jsonify({"message": "File uploaded successfully", "doc_id": doc_id}), 201
        else:
            # Clean up uploaded file if db insert fails
            os.remove(storage_path)
            return jsonify({"error": "Failed to save document record"}), 500

@app.route('/api/document/<doc_id>/download', methods=['GET'])
@login_required
def download_document(doc_id):
    user_id = session.get('user_id')
    user_role = session.get('role')

    document = document_manager.get_document_by_id(doc_id)
    if not document:
        return jsonify({"error": "Document not found"}), 404

    case_id = document['case_id']
    if user_role != 'judge' and not permissions_manager.check_access(case_id, user_id):
        return jsonify({"error": "You do not have permission to download this file"}), 403

    storage_path = document['storage_path']
    directory = os.path.dirname(storage_path)
    filename = os.path.basename(storage_path)
    
    return send_from_directory(directory, filename, as_attachment=True, attachment_filename=document['file_name'])

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True, port=5001) # Using port 5001 to avoid conflicts
