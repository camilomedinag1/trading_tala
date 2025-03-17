from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import random
import time
import threading

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuración de SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'supersecretkey'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Modelo de Usuario
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    balance = db.Column(db.Float, default=10000.0)  # Dinero del usuario
    stocks = db.Column(db.JSON, default={})  # Acciones compradas

with app.app_context():
    db.create_all()

# Datos simulados de una acción
stock_data = {"symbol": "AAPL", "price": 150.0}

# Simulación de cambios de precio
def generate_stock_prices():
    while True:
        stock_data["price"] += random.uniform(-1, 1)
        socketio.emit("stock_price", stock_data)
        time.sleep(1)

threading.Thread(target=generate_stock_prices, daemon=True).start()

# Endpoint para obtener información de la acción
@app.route("/api/stock/info", methods=["GET"])
def get_stock_info():
    return jsonify(stock_data)

# Endpoint para comprar acciones
@app.route("/api/stock/buy", methods=["POST"])
@jwt_required()
def buy_stock():
    data = request.json
    username = get_jwt_identity()
    quantity = int(data.get("quantity", 1))

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"message": "Usuario no encontrado"}), 404

    total_cost = stock_data["price"] * quantity
    if user.balance < total_cost:
        return jsonify({"message": "Saldo insuficiente"}), 400

    user.balance -= total_cost
    user.stocks[stock_data["symbol"]] = user.stocks.get(stock_data["symbol"], 0) + quantity
    db.session.commit()

    return jsonify({"message": "Compra exitosa", "balance": user.balance, "stocks": user.stocks})

# Endpoint para vender acciones
@app.route("/api/stock/sell", methods=["POST"])
@jwt_required()
def sell_stock():
    data = request.json
    username = get_jwt_identity()
    quantity = int(data.get("quantity", 1))

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"message": "Usuario no encontrado"}), 404

    if stock_data["symbol"] not in user.stocks or user.stocks[stock_data["symbol"]] < quantity:
        return jsonify({"message": "No tienes suficientes acciones para vender"}), 400

    user.stocks[stock_data["symbol"]] -= quantity
    user.balance += stock_data["price"] * quantity
    db.session.commit()

    return jsonify({"message": "Venta exitosa", "balance": user.balance, "stocks": user.stocks})

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
