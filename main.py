from flask import Flask, request, jsonify, render_template
import pymysql
pymysql.install_as_MySQLdb()

from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity
)
import os

app = Flask(__name__)

# ================= CONFIG =================
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '@ttar29'
app.config['MYSQL_DB'] = 'taskdb'
app.config['JWT_SECRET_KEY'] = 'super_secret_key_123'

mysql = MySQL(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# ================= HOME =================
@app.route('/')
def home():
    return render_template('index.html')

# ================= REGISTER =================
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", 
                (username, hashed_password))
    mysql.connection.commit()
    cur.close()

    return jsonify({"msg": "User registered successfully"})

# ================= LOGIN =================
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cur.fetchone()
    cur.close()

    if user and bcrypt.check_password_hash(user[2], password):
        access_token = create_access_token(identity=str(user[0]))
        return jsonify(access_token=access_token)

    return jsonify({"msg": "Invalid credentials"}), 401

# ================= ADD TASK =================
@app.route('/tasks', methods=['POST'])
@jwt_required()
def add_task():
    user_id = get_jwt_identity()
    data = request.get_json()

    title = data.get('title')
    description = data.get('description')

    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO tasks (title, description, status, user_id) VALUES (%s, %s, %s, %s)",
        (title, description, "Pending", user_id)
    )
    mysql.connection.commit()
    cur.close()

    return jsonify({"msg": "Task added"})

# ================= GET TASKS =================
@app.route('/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    user_id = get_jwt_identity()

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, title, description, status FROM tasks WHERE user_id=%s", (user_id,))
    tasks = cur.fetchall()
    cur.close()

    task_list = []
    for task in tasks:
        task_list.append({
            "id": task[0],
            "title": task[1],
            "description": task[2],
            "status": task[3]
        })

    return jsonify(task_list)

# ================= UPDATE TASK =================
@app.route('/tasks/<int:id>', methods=['PUT'])
@jwt_required()
def update_task(id):
    user_id = get_jwt_identity()
    data = request.get_json()
    status = data.get('status')

    cur = mysql.connection.cursor()
    cur.execute(
        "UPDATE tasks SET status=%s WHERE id=%s AND user_id=%s",
        (status, id, user_id)
    )
    mysql.connection.commit()
    cur.close()

    return jsonify({"msg": "Task updated"})

# ================= DELETE TASK =================
@app.route('/tasks/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_task(id):
    user_id = get_jwt_identity()

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM tasks WHERE id=%s AND user_id=%s", (id, user_id))
    mysql.connection.commit()
    cur.close()

    return jsonify({"msg": "Task deleted"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
