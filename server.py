from flask import Flask, jsonify, request, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
# ВАЖНО: Секретный ключ нужен для шифрования Cookie (сессий). 
app.secret_key = os.environ.get('SECRET_KEY')
CORS(app, supports_credentials=True) # Разрешаем браузеру передавать куки

conn = sqlite3.connect('tasks.db', check_same_thread=False)
cursor = conn.cursor()

# 1. Таблица пользователей
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
''')

# 2. Таблица задач (теперь с привязкой к user_id)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        text TEXT NOT NULL,
        status TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
''')
conn.commit()


# --- АВТОРИЗАЦИЯ ---

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Введите логин и пароль"}), 400

    hashed_pw = generate_password_hash(password)
    
    try:
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, hashed_pw))
        conn.commit()
        return jsonify({"message": "Успешно зарегистрирован"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Пользователь уже существует"}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone() # user = (id, username, password_hash)

    # Проверяем, существует ли юзер и совпадает ли пароль с хэшем
    if user and check_password_hash(user[2], password):
        session['user_id'] = user[0] # Записываем ID в сессию
        return jsonify({"message": "Успешный вход"}), 200
    
    return jsonify({"error": "Неверный логин или пароль"}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None) # Удаляем ID из сессии
    return jsonify({"message": "Вы вышли"}), 200

# Проверка: залогинен ли пользователь (нужно для JS)
@app.route('/api/me', methods=['GET'])
def get_me():
    if 'user_id' in session:
        return jsonify({"logged_in": True, "user_id": session['user_id']}), 200
    return jsonify({"logged_in": False}), 401


# --- ЗАДАЧИ (ТЕПЕРЬ ЗАЩИЩЕННЫЕ) ---

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Доступ запрещен"}), 401

    # Берем задачи ТОЛЬКО этого пользователя!
    cursor.execute('SELECT id, text, status FROM tasks WHERE user_id = ?', (user_id,))
    rows = cursor.fetchall()
    tasks = [{"id": r[0], "text": r[1], "status": r[2]} for r in rows]
    return jsonify(tasks)

@app.route('/api/tasks', methods=['POST'])
def add_task():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Доступ запрещен"}), 401

    data = request.json
    # Сохраняем задачу и привязываем к user_id
    cursor.execute(
        'INSERT INTO tasks (id, text, status, user_id) VALUES (?, ?, ?, ?)',
        (data['id'], data['text'], data['status'], user_id)
    )
    conn.commit()
    return jsonify({"message": "Задача добавлена!"}), 201

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Доступ запрещен"}), 401

    # Удаляем только если задача принадлежит этому юзеру!
    cursor.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?', (task_id, user_id))
    conn.commit()
    return jsonify({"message": "Задача удалена"}), 200

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Доступ запрещен"}), 401

    data = request.json

    if 'status' in data:
        cursor.execute('UPDATE tasks SET status = ? WHERE id = ? AND user_id = ?', (data['status'], task_id, user_id))
    if 'text' in data:
        cursor.execute('UPDATE tasks SET text = ? WHERE id = ? AND user_id = ?', (data['text'], task_id, user_id))

    conn.commit()
    return jsonify({"message": "Задача обновлена"}), 200


if __name__ == '__main__':
    app.run(debug=True)