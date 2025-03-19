import os
import json
import time
import threading
import hashlib
import requests
import random
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_socketio import SocketIO

app = Flask(__name__)
app.secret_key = "super_secret_key"  # Change this for production
CORS(app, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*")

DATA_FILE = "stock_data.json"
USERS_FILE = "users.json"

# Global mode and API settings
MODE = "simulation"  # default mode is simulation
REALTIME_API_KEY = None
REALTIME_API_URL = None

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    return {"balance": 10000.0, "stocks": {}}

def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file)

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as file:
            return json.load(file)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as file:
        json.dump(users, file)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Global stock data; initial price is set to 150.
stock_data = {"symbol": "AAPL", "price": 150.0}

def fetch_real_stock_price():
    global REALTIME_API_KEY, REALTIME_API_URL
    if not REALTIME_API_KEY or not REALTIME_API_URL:
        return None
    try:
        url = f"{REALTIME_API_URL}/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey={REALTIME_API_KEY}"
        response = requests.get(url)
        data = response.json()
        if "Global Quote" in data and "05. price" in data["Global Quote"]:
            price = float(data["Global Quote"]["05. price"])
            return price
    except Exception as e:
        print("Error fetching real stock price:", e)
    return None

def generate_stock_prices():
    global MODE, stock_data
    while True:
        if MODE == "real-time":
            real_price = fetch_real_stock_price()
            if real_price is not None:
                stock_data["price"] = real_price
                socketio.emit("stock_price", stock_data)
            else:
                print("Failed to fetch real stock price, keeping previous value")
        else:
            # Simulation mode: update price with a random walk
            stock_data["price"] += random.uniform(-1, 1)
            socketio.emit("stock_price", stock_data)
        time.sleep(2)  # Update every 60 seconds

threading.Thread(target=generate_stock_prices, daemon=True).start()

@app.route("/api/register", methods=["POST"])
def register():
    users = load_users()
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    if username in users:
        return jsonify({"message": "User already exists"}), 400

    users[username] = {
        "password": hash_password(password),
        "balance": 10000.0,
        "stocks": {}
    }
    save_users(users)
    return jsonify({"message": "User registered successfully"}), 201

@app.route("/api/login", methods=["POST"])
def login():
    global MODE, REALTIME_API_KEY, REALTIME_API_URL
    users = load_users()
    data = request.json
    username = data.get("username")
    password = data.get("password")
    mode = data.get("mode", "simulation")  # default is simulation

    if username not in users or users[username]["password"] != hash_password(password):
        return jsonify({"message": "Invalid credentials"}), 401

    # If real-time mode is selected, require API key and API URL.
    if mode == "real-time":
        apiKey = data.get("apiKey")
        apiUrl = data.get("apiUrl")
        if not apiKey or not apiUrl:
            return jsonify({"message": "For real-time mode, API key and API URL are required"}), 400
        MODE = "real-time"
        REALTIME_API_KEY = apiKey
        REALTIME_API_URL = apiUrl
    else:
        MODE = "simulation"

    session["username"] = username
    session["mode"] = mode
    return jsonify({
        "message": "Login successful",
        "balance": users[username]["balance"],
        "stocks": users[username]["stocks"]
    })

@app.route("/api/logout", methods=["POST"])
def logout():
    session.pop("username", None)
    session.pop("mode", None)
    return jsonify({"message": "Logged out"}), 200

def require_login():
    if "username" not in session:
        return jsonify({"message": "Unauthorized"}), 401
    return None

@app.route("/api/stock/info", methods=["GET"])
def get_stock_info():
    return jsonify(stock_data)

@app.route("/api/stock/buy", methods=["POST"])
def buy_stock():
    auth_error = require_login()
    if auth_error:
        return auth_error

    users = load_users()
    username = session["username"]
    user_data = users[username]
    quantity = 1
    total_cost = stock_data["price"] * quantity

    if user_data["balance"] < total_cost:
        return jsonify({"message": "Insufficient balance"}), 400

    user_data["balance"] -= total_cost
    user_data["stocks"][stock_data["symbol"]] = user_data["stocks"].get(stock_data["symbol"], 0) + quantity
    users[username] = user_data
    save_users(users)

    return jsonify({
        "message": "Purchase successful",
        "balance": user_data["balance"],
        "stocks": user_data["stocks"]
    })

@app.route("/api/stock/sell", methods=["POST"])
def sell_stock():
    auth_error = require_login()
    if auth_error:
        return auth_error

    users = load_users()
    username = session["username"]
    user_data = users[username]
    quantity = 1

    if user_data["stocks"].get(stock_data["symbol"], 0) < quantity:
        return jsonify({"message": "Not enough stocks to sell"}), 400

    user_data["stocks"][stock_data["symbol"]] -= quantity
    user_data["balance"] += stock_data["price"] * quantity
    users[username] = user_data
    save_users(users)

    return jsonify({
        "message": "Sale successful",
        "balance": user_data["balance"],
        "stocks": user_data["stocks"]
    })

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)

