from flask import Flask, jsonify, request
from flask_httpauth import HTTPBasicAuth
import json
import os
import sqlite3

app = Flask(__name__)
auth = HTTPBasicAuth()

# вибір методу аутентифікації (dict, file, sqlite) та зберігання (dict, file, sqlite)
AUTH_METHOD = 'file'
STORAGE_METHOD = 'file'

# користувачі dict
users_dict = {
    "admin": "password123"
}

# функції file
def load_users_from_file():
    if os.path.exists('users.json'):
        with open('users.json') as f:
            return json.load(f)
    return {}

# функції sqlite
def get_user_from_db(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    return user[0] if user else None

# перевірка користувача
@auth.verify_password
def verify_password(username, password):
    if AUTH_METHOD == 'dict':
        return username in users_dict and users_dict[username] == password
    elif AUTH_METHOD == 'file':
        users = load_users_from_file()
        return username in users and users[username] == password
    elif AUTH_METHOD == 'sqlite':
        pwd = get_user_from_db(username)
        return pwd and pwd == password
    return False

# зберігання фруктів dict
fruits_dict = {}

# функції для STORAGE_METHOD = 'file'
DATA_FILE = 'fruits.json'

def load_fruits_from_file():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as file:
            return json.load(file)
    return {}

def save_fruits_to_file(fruits):
    with open(DATA_FILE, 'w') as file:
        json.dump(fruits, file, indent=4)

# функції для STORAGE_METHOD = 'sqlite'
def init_fruits_db():
    conn = sqlite3.connect('fruits.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS fruits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    weight REAL NOT NULL,
                    price REAL NOT NULL,
                    color TEXT NOT NULL)''')
    conn.commit()
    conn.close()

def get_fruits_from_db():
    conn = sqlite3.connect('fruits.db')
    c = conn.cursor()
    c.execute("SELECT * FROM fruits")
    fruits = c.fetchall()
    conn.close()
    return [{"id": fruit[0], "name": fruit[1], "weight": fruit[2], "price": fruit[3], "color": fruit[4]} for fruit in fruits]

def add_fruit_to_db(name, weight, price, color):
    conn = sqlite3.connect('fruits.db')
    c = conn.cursor()
    c.execute("INSERT INTO fruits (name, weight, price, color) VALUES (?, ?, ?, ?)", (name, weight, price, color))
    conn.commit()
    conn.close()

def update_fruit_in_db(id, name, weight, price, color):
    conn = sqlite3.connect('fruits.db')
    c = conn.cursor()
    c.execute("UPDATE fruits SET name = ?, weight = ?, price = ?, color = ? WHERE id = ?", (name, weight, price, color, id))
    conn.commit()
    conn.close()

def delete_fruit_from_db(id):
    conn = sqlite3.connect('fruits.db')
    c = conn.cursor()
    c.execute("DELETE FROM fruits WHERE id = ?", (id,))
    conn.commit()
    conn.close()

# ендпоінт для отримання всіх фруктів або додавання нового
@app.route('/fruits', methods=['GET', 'POST'])
@auth.login_required
def handle_fruits():
    if STORAGE_METHOD == 'dict':
        if request.method == 'GET':
            return jsonify(fruits_dict)
        elif request.method == 'POST':
            new_fruit = request.json
            fruit_id = str(len(fruits_dict) + 1)
            fruits_dict[fruit_id] = {
                "name": new_fruit.get("name"),
                "weight": new_fruit.get("weight"),
                "price": new_fruit.get("price"),
                "color": new_fruit.get("color")
            }
            return jsonify({"message": "Фрукт успішно доданий."}), 201

    elif STORAGE_METHOD == 'file':
        fruits = load_fruits_from_file()
        if request.method == 'GET':
            return jsonify(fruits)
        elif request.method == 'POST':
            new_fruit = request.json
            fruit_id = str(len(fruits) + 1)
            fruits[fruit_id] = {
                "name": new_fruit.get("name"),
                "weight": new_fruit.get("weight"),
                "price": new_fruit.get("price"),
                "color": new_fruit.get("color")
            }
            save_fruits_to_file(fruits)
            return jsonify({"message": "Фрукт успішно доданий."}), 201

    elif STORAGE_METHOD == 'sqlite':
        if request.method == 'GET':
            fruits = get_fruits_from_db()
            return jsonify(fruits)
        elif request.method == 'POST':
            new_fruit = request.json
            add_fruit_to_db(new_fruit.get("name"), new_fruit.get("weight"), new_fruit.get("price"), new_fruit.get("color"))
            return jsonify({"message": "Фрукт успішно доданий."}), 201

# ендпоінт для отримання, оновлення або видалення конкретного фрукта
@app.route('/fruits/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@auth.login_required
def handle_fruit(id):
    if STORAGE_METHOD == 'dict':
        fruit = fruits_dict.get(str(id))
        if not fruit:
            return jsonify({"error": "Фрукт не знайдено."}), 404

        if request.method == 'GET':
            return jsonify(fruit)
        elif request.method == 'PUT':
            fruits_dict[str(id)].update(request.json)
            return jsonify({"message": "Фрукт успішно оновлено."})
        elif request.method == 'DELETE':
            del fruits_dict[str(id)]
            return jsonify({"message": "Фрукт успішно видалено."})

    elif STORAGE_METHOD == 'file':
        fruits = load_fruits_from_file()
        fruit = fruits.get(str(id))
        if not fruit:
            return jsonify({"error": "Фрукт не знайдено."}), 404

        if request.method == 'GET':
            return jsonify(fruit)
        elif request.method == 'PUT':
            fruits[str(id)].update(request.json)
            save_fruits_to_file(fruits)
            return jsonify({"message": "Фрукт успішно оновлено."})
        elif request.method == 'DELETE':
            del fruits[str(id)]
            save_fruits_to_file(fruits)
            return jsonify({"message": "Фрукт успішно видалено."})

    elif STORAGE_METHOD == 'sqlite':
        if request.method == 'GET':
            fruits = get_fruits_from_db()
            fruit = next((fruit for fruit in fruits if fruit['id'] == id), None)
            if not fruit:
                return jsonify({"error": "Фрукт не знайдено."}), 404
            return jsonify(fruit)
        elif request.method == 'PUT':
            updated_data = request.json
            update_fruit_in_db(id, updated_data.get("name"), updated_data.get("weight"), updated_data.get("price"), updated_data.get("color"))
            return jsonify({"message": "Фрукт успішно оновлено."})
        elif request.method == 'DELETE':
            delete_fruit_from_db(id)
            return jsonify({"message": "Фрукт успішно видалено."})

if __name__ == '__main__':
    if AUTH_METHOD == 'sqlite':
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
        c.execute("INSERT OR IGNORE INTO users (username, password) VALUES ('nure', 'nurepass')")
        conn.commit()
        conn.close()

    if STORAGE_METHOD == 'sqlite':
        init_fruits_db()

    app.run(debug=True, port=8888)