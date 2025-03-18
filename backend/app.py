from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
import random
import time
import threading
import json
import os

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

DATA_FILE = "stock_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    return {"balance": 10000.0, "stocks": {}}

def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file)

stock_data = {"symbol": "AAPL", "price": 150.0}

def generate_stock_prices():
    while True:
        stock_data["price"] += random.uniform(-1, 1)
        socketio.emit("stock_price", stock_data)
        time.sleep(1)

threading.Thread(target=generate_stock_prices, daemon=True).start()

@app.route("/api/stock/info", methods=["GET"])
def get_stock_info():
    return jsonify(stock_data)

@app.route("/api/stock/buy", methods=["GET"])
def buy_stock():
    data = load_data()
    quantity = 1
    total_cost = stock_data["price"] * quantity
    
    if data["balance"] < total_cost:
        return jsonify({"message": "Insufficient balance"}), 400

    data["balance"] -= total_cost
    data["stocks"][stock_data["symbol"]] = data["stocks"].get(stock_data["symbol"], 0) + quantity
    save_data(data)

    return jsonify({"message": "Purchase successful", "balance": data["balance"], "stocks": data["stocks"]})

@app.route("/api/stock/sell", methods=["GET"])
def sell_stock():
    data = load_data()
    quantity = 1
    
    if stock_data["symbol"] not in data["stocks"] or data["stocks"][stock_data["symbol"]] < quantity:
        return jsonify({"message": "Not enough stocks to sell"}), 400

    data["stocks"][stock_data["symbol"]] -= quantity
    data["balance"] += stock_data["price"] * quantity
    save_data(data)

    return jsonify({"message": "Sale successful", "balance": data["balance"], "stocks": data["stocks"]})

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
