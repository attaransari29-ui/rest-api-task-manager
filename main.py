from flask import Flask, request, jsonify, render_template
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity
)
import pymysql
import os

app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = "super_secret_key"

bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# ================= DATABASE CONNECTION =================
def get_db():
    return pymysql.connect(
        host=os.environ.get("MYSQLHOST"),
        user=os.environ.get("MYSQLUSER"),
        password=os.environ.get("MYSQLPASSWORD"),
        database=os.environ.get("MYSQLDATABASE"),
        port=int(os.environ.get("MYSQLPORT", 3306)),
        cursorclass=pymysql.cursors.DictCursor
    )

# ================= HOME =================
@app.route("/")
def home():
    return render_template("index.html")

# ================= REGISTER =================
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data["username"]
    password = data["password"]

    hashed = bcrypt.generate_password_hash(password).decode("utf-8")

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO users (username, password) VALUES (%s, %s)",
        (username, hashed),
    )
    db.commit()
    db.close()

    return jsonify({"msg": "User registered successfully"})

# ================= LOGIN =================
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data["username"]
    password = data["password"]

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cursor.fetchone()
    db.close()

    if user and bcrypt.check_password_hash(user["password"], password):
        token = create_access_token(identity=user["id"])
        return jsonify(access_token=token)

    return jsonify({"msg": "Invalid credentials"}), 401

# ================= ADD TASK =================
@app.route("/tasks", methods=["POST"])
@jwt_required()
def add_task():
    user_id = get_jwt_identity()
    data = request.get_json()

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, description, status, user_id) VALUES (%s, %s, %s, %s)",
        (data["title"], data["description"], "Pending", user_id),
    )
    db.commit()
    db.close()

    return jsonify({"msg": "Task added"})

# ================= GET TASKS =================
@app.route("/tasks", methods=["GET"])
@jwt_required()
def get_tasks():
    user_id = get_jwt_identity()

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, title, description, status FROM tasks WHERE user_id=%s",
        (user_id,),
    )
    tasks = cursor.fetchall()
    db.close()

    return jsonify(tasks)

# ================= UPDATE TASK =================
@app.route("/tasks/<int:id>", methods=["PUT"])
@jwt_required()
def update_task(id):
    user_id = get_jwt_identity()
    data = request.get_json()

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE tasks SET status=%s WHERE id=%s AND user_id=%s",
        (data["status"], id, user_id),
    )
    db.commit()
    db.close()

    return jsonify({"msg": "Task updated"})

# ================= DELETE TASK =================
@app.route("/tasks/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_task(id):
    user_id = get_jwt_identity()

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "DELETE FROM tasks WHERE id=%s AND user_id=%s",
        (id, user_id),
    )
    db.commit()
    db.close()

    return jsonify({"msg": "Task deleted"})

# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
