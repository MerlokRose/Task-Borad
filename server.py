from flask import Flask, jsonify, request, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

# Настройки для работы в интернете (куки)
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True

# Разрешаем CORS только для твоего сайта на Netlify
CORS(app, supports_credentials=True, origins=["https://merloktask-board.netlify.app"])

DATABASE_URL = os.environ.get('DATABASE_URL')

# Функция для создания нового соединения (решает проблему разрыва)
def get_db_connection():
    url = urlparse(DATABASE_URL)
    return psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )

# Создаем таблицы при старте (один раз)
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id BIGINT PRIMARY KEY,
            text TEXT NOT NULL,
            status TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

init_db()

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Введите логин и пароль"}), 400

    hashed_pw = generate_password_hash(password)
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, hashed_pw))
        conn.commit()
        return jsonify({"message": "Успешно зарегистрирован"}), 201
    except psycopg2.IntegrityError:
        conn.rollback()
        return jsonify({"error": "Пользователь уже существует"}), 400
    finally:
        cur.close()
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cur.fetchone()
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            return jsonify({"message": "Успешный вход"}), 200
        return jsonify({"error": "Неверный логин или пароль"}), 401
    finally:
        cur.close()
        conn.close()

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({"message": "Вы вышли"}), 200

@app.route('/api/me', methods=['GET'])
def get_me():
    if 'user_id' in session:
        return jsonify({"logged_in": True, "user_id": session['user_id']}), 200
    return jsonify({"logged_in": False}), 401

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Доступ запрещен"}), 401

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT id, text, status FROM tasks WHERE user_id = %s', (user_id,))
        rows = cur.fetchall()
        tasks = [{"id": r[0], "text": r[1], "status": r[2]} for r in rows]
        return jsonify(tasks)
    finally:
        cur.close()
        conn.close()

@app.route('/api/tasks', methods=['POST'])
def add_task():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Доступ запрещен"}), 401

    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            'INSERT INTO tasks (id, text, status, user_id) VALUES (%s, %s, %s, %s)',
            (data['id'], data['text'], data['status'], user_id)
        )
        conn.commit()
        return jsonify({"message": "Задача добавлена!"}), 201
    finally:
        cur.close()
        conn.close()

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Доступ запрещен"}), 401

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('DELETE FROM tasks WHERE id = %s AND user_id = %s', (task_id, user_id))
        conn.commit()
        return jsonify({"message": "Задача удалена"}), 200
    finally:
        cur.close()
        conn.close()

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Доступ запрещен"}), 401

    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if 'status' in data:
            cur.execute('UPDATE tasks SET status = %s WHERE id = %s AND user_id = %s', (data['status'], task_id, user_id))
        if 'text' in data:
            cur.execute('UPDATE tasks SET text = %s WHERE id = %s AND user_id = %s', (data['text'], task_id, user_id))
        conn.commit()
        return jsonify({"message": "Задача обновлена"}), 200
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)