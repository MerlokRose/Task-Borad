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

# НАСТРОЙКИ ДЛЯ РАБОТЫ В ИНТЕРНЕТЕ (Куки)
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True

# Разрешаем CORS для всех (потом можешь заменить '*' на ссылку твоего сайта от Netlify)
CORS(app, supports_credentials=True, origins=["https://aesthetic-praline-fef347.netlify.app"]) 

app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True

# Подключение к PostgreSQL (Neon)
# Если базы нет локально, используется DATABASE_URL из настроек Render
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    # Локальная заглушка, если ты запускаешь у себя на компе без облачной базы
    DATABASE_URL = 'postgresql://user:password@localhost:5432/tasksdb'

url = urlparse(DATABASE_URL)
conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)
cursor = conn.cursor()

# 1. Таблица пользователей (SERIAL вместо AUTOINCREMENT)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
''')

# 2. Таблица задач (id теперь BIGINT, так как мы передаем Date.now())
cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id BIGINT PRIMARY KEY,
        text TEXT NOT NULL,
        status TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')
conn.commit()

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Введите логин и пароль"}), 400

    hashed_pw = generate_password_hash(password)
    
    try:
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, hashed_pw))
        conn.commit()
        return jsonify({"message": "Успешно зарегистрирован"}), 201
    except psycopg2.IntegrityError:
        conn.rollback() # Откатываем транзакцию при ошибке
        return jsonify({"error": "Пользователь уже существует"}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
    user = cursor.fetchone()

    if user and check_password_hash(user[2], password):
        session['user_id'] = user[0]
        return jsonify({"message": "Успешный вход"}), 200
    
    return jsonify({"error": "Неверный логин или пароль"}), 401

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

    cursor.execute('SELECT id, text, status FROM tasks WHERE user_id = %s', (user_id,))
    rows = cursor.fetchall()
    tasks = [{"id": r[0], "text": r[1], "status": r[2]} for r in rows]
    return jsonify(tasks)

@app.route('/api/tasks', methods=['POST'])
def add_task():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Доступ запрещен"}), 401

    data = request.json
    cursor.execute(
        'INSERT INTO tasks (id, text, status, user_id) VALUES (%s, %s, %s, %s)',
        (data['id'], data['text'], data['status'], user_id)
    )
    conn.commit()
    return jsonify({"message": "Задача добавлена!"}), 201

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Доступ запрещен"}), 401

    cursor.execute('DELETE FROM tasks WHERE id = %s AND user_id = %s', (task_id, user_id))
    conn.commit()
    return jsonify({"message": "Задача удалена"}), 200

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Доступ запрещен"}), 401

    data = request.json
    if 'status' in data:
        cursor.execute('UPDATE tasks SET status = %s WHERE id = %s AND user_id = %s', (data['status'], task_id, user_id))
    if 'text' in data:
        cursor.execute('UPDATE tasks SET text = %s WHERE id = %s AND user_id = %s', (data['text'], task_id, user_id))

    conn.commit()
    return jsonify({"message": "Задача обновлена"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)