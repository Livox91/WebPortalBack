import base64
from logging import log
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from db import  create_database_user , create_database_file
import re
import io


db_file , cursor_file = create_database_file()

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
    db_user , cursor_user = create_database_user()
    if exclude_id:
        cursor_user.execute("SELECT id FROM users WHERE email = ? AND id != ?", (email, exclude_id))
    else:
        cursor_user.execute("SELECT id FROM users WHERE email = ?", (email,))
    
    res = cursor_user.fetchone()
    db_user.close()
    return res is not None

def check_cnic_exists(cnic, exclude_id=None):
    db_user , cursor_user = create_database_user()
    if exclude_id:
        cursor_user.execute("SELECT id FROM users WHERE cnic = ? AND id != ?", (cnic, exclude_id))
    else:
        cursor_user.execute("SELECT id FROM users WHERE cnic = ?", (cnic,))
    res = cursor_user.fetchone()
    db_user.close()

    return res is not None

@app.route('/users', methods=['GET'])
def get_users():
    db_user , cursor_user = create_database_user()
    cursor_user.execute("SELECT * FROM users")
    users = cursor_user.fetchall()
    
    column_names = [desc[0] for desc in cursor_user.description]
    users_list = []
    
    for row in users:
        user_dict = {}
        for col_name, value in zip(column_names, row):
            if isinstance(value, bytes):    
                user_dict[col_name] = base64.b64encode(value).decode('utf-8')  
            else:
                user_dict[col_name] = value
        users_list.append(user_dict)
    db_user.close()
    return jsonify(users_list)

@app.route('/users', methods=['POST'])
def create_user():
    db_user , cursor_user = create_database_user()
    data = request.form
    
    errors = {}
    
    if not validate_email(data['email']):
        errors['email'] = "Invalid email format"
    elif check_email_exists(data['email']):
        errors['email'] = "Email already exists"
        
    if not validate_cnic(data['cnic']):
        errors['cnic'] = "Invalid CNIC format (use: XXXXXXXXXXXXX)"
    elif check_cnic_exists(data['cnic']):
        errors['cnic'] = "CNIC already exists"
    
    if not data['name'].strip():
        errors['name'] = "Name is required"
        
    if not data['pass'].strip():
        errors['pass'] = "Password is required"
    
    if errors:
        return jsonify({"errors": errors}), 400
        
    cursor_user.execute("INSERT INTO users (name, cnic, pass, ref_name, remarks, email , phno  ) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (data['name'], data['cnic'], data['pass'], data['ref_name'], data['remarks'], data['email'], data['phno']))
    db_user.commit()
    db_user.close()
    return jsonify({"message": "User added successfully"}), 201

@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    db_user , cursor_user = create_database_user()
    data = request.form
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
        
    cursor_user.execute("UPDATE users SET name = ?, cnic = ?, pass = ?, ref_name = ?, remarks = ?, email = ?, phno = ? WHERE id = ?",
                   (data['name'], data['cnic'], data['pass'], data['ref_name'], data['remarks'], data['email'], data['phno'], id))
    db_user.commit()
    db_user.close()
    return jsonify({"message": "User updated successfully"})

@app.route('/users/<string:cnic>', methods=['GET'])
def get_user(cnic):
    db_user , cursor_user = create_database_user()
    cursor_user.execute("SELECT * FROM users WHERE cnic = ?", (cnic,))
    user = cursor_user.fetchone()
    
    if user:
        column_names = [desc[0] for desc in cursor_user.description]
        user_dict = {}
        for col_name, value in zip(column_names, user):
            if isinstance(value, bytes):
                user_dict[col_name] = base64.b64encode(value).decode('utf-8')  
            else:
                user_dict[col_name] = value
        db_user.close()
        return jsonify(user_dict)
    else:
        db_user.close()
        return jsonify({"error": "User not found"}), 404
    
# User And File Cursor In This One
@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    db_user , cursor_user = create_database_user()
    db_file , cursor_file = create_database_file()
    
    cursor_user.execute("DELETE FROM users WHERE id = ?", (id,))
    cursor_file.execute("DELETE FROM files WHERE id = ?", (id,))
    db_user.commit()
    db_file.commit()
    db_user.close()
    db_file.close()
    return jsonify({"message": "User deleted successfully"})


@app.route('/users/<int:id>/files/<string:name>', methods=['GET'])
def get_file(id, name):
    
    db_file , cursor_file = create_database_file()
    cursor_file.execute('SELECT file_data FROM files WHERE id = ? AND name = ?' , (id, name))
    file = cursor_file.fetchone()
    
    if not file :
        return jsonify({'message': 'File not found'}), 404

    db_file.close()
    return send_file(io.BytesIO(file[0]), download_name=name, as_attachment=True)


@app.route('/users/<int:id>/files/', methods=['POST'])
def create_file(id):
    db_file , cursor_file = create_database_file()
    files = request.files
    
    cursor_file.execute('INSERT INTO files (id , name , file_data ) VALUES ( ? , ? , ? )', (id, files['file_data'].filename , files['file_data'].read() ) )
    db_file.commit()
    db_file.close()
    return jsonify({"message": "File added successfully"}), 201


@app.route('/users/<int:id>/files/<string:name>',methods=['DELETE'])
def delete_file(id , name):
    db_file , cursor_file = create_database_file()
    
    cursor_file.execute('DELETE FROM files WHERE id = ? AND name = ?' , (id, name ))
    db_file.commit()
    db_file.close()
    return jsonify({"message": "File deleted successfully"})

@app.route('/users/<int:id>/files/' , methods=['GET'])
def get_files(id):
    db_file , cursor_file = create_database_file()
    cursor_file.execute('SELECT * FROM files WHERE id = ?' , (id,))
    files = cursor_file.fetchall()

    column_names = [desc[0] for desc in cursor_file.description]
    file_list = []
    
    for row in files: 
        user_dict = {}
        for col_name, value in zip(column_names, row):
            if isinstance(value, bytes):    
                user_dict[col_name] = base64.b64encode(value).decode('utf-8')  
            else:
                user_dict[col_name] = value
        file_list.append(user_dict)
    db_file.close()
    return jsonify(file_list)


if __name__ == '__main__':
    app.run(debug=True,host= '0.0.0.0', port=5500)