from flask import Flask, request, jsonify
from flask_cors import CORS
from db import  create_database
import re

db , cursor = create_database()

app = Flask(__name__)
CORS(app,supports_credentials=True )

def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_cnic(cnic):
    pattern = r'^\d{5}\d{7}\d{1}$'
    return re.match(pattern, cnic) is not None

def check_email_exists(email, exclude_id=None):
    if exclude_id:
        cursor.execute("SELECT id FROM users WHERE email = ? AND id != ?", (email, exclude_id))
    else:
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    return cursor.fetchone() is not None

def check_cnic_exists(cnic, exclude_id=None):
    if exclude_id:
        cursor.execute("SELECT id FROM users WHERE cnic = ? AND id != ?", (cnic, exclude_id))
    else:
        cursor.execute("SELECT id FROM users WHERE cnic = ?", (cnic,))
    return cursor.fetchone() is not None

@app.route('/users', methods=['GET'])
def get_users():
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    return jsonify(users)

@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    cursor.execute("SELECT * FROM users WHERE id = ?", (id,))
    user = cursor.fetchone()
    return jsonify(user) if user else jsonify({"error": "User not found"}), 404

@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    
    errors = {}
    
    if not validate_email(data['email']):
        errors['email'] = "Invalid email format"
    elif check_email_exists(data['email']):
        errors['email'] = "Email already exists"
        
    if not validate_cnic(data['cnic']):
        errors['cnic'] = "Invalid CNIC format (use: xxxxxxxxxxxxx)"
    elif check_cnic_exists(data['cnic']):
        errors['cnic'] = "CNIC already exists"
    
    if not data['name'].strip():
        errors['name'] = "Name is required"
        
    if not data['pass'].strip():
        errors['pass'] = "Password is required"
    
    if errors:
        return jsonify({"errors": errors}), 400
        
    cursor.execute("INSERT INTO users (name, cnic, pass, ref_name, remarks, email) VALUES (?, ?, ?, ?, ?, ?)",
                   (data['name'], data['cnic'], data['pass'], data['ref_name'], data['remarks'], data['email']))
    db.commit()
    return jsonify({"message": "User added successfully"}), 201

@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    data = request.json
    
    errors = {}
    
    if not validate_email(data['email']):
        errors['email'] = "Invalid email format"
    elif check_email_exists(data['email'], id):
        errors['email'] = "Email already exists"
        
    if not validate_cnic(data['cnic']):
        errors['cnic'] = "Invalid CNIC format (use: xxxxxxxxxxxxx)"
    elif check_cnic_exists(data['cnic'], id):
        errors['cnic'] = "CNIC already exists"
    
    if not data['name'].strip():
        errors['name'] = "Name is required"
        
    if not data['pass'].strip():
        errors['pass'] = "Password is required"
    
    if errors:
        return jsonify({"errors": errors}), 400
        
    cursor.execute("UPDATE users SET name = ?, cnic = ?, pass = ?, ref_name = ?, remarks = ?, email = ? WHERE id = ?",
                   (data['name'], data['cnic'], data['pass'], data['ref_name'], data['remarks'], data['email'], id))
    db.commit()
    return jsonify({"message": "User updated successfully"})


@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    cursor.execute("DELETE FROM users WHERE id = ?", (id,))
    db.commit()
    return jsonify({"message": "User deleted successfully"})

if __name__ == '__main__':
    app.run(debug=True,host= '0.0.0.0', port=5500)