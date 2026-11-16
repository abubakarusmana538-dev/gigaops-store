import os
import time

import mysql.connector
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "mysql")
DB_USER = os.getenv("DB_USER", "storeuser")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "storedb")
PRODUCT_URL = os.getenv("PRODUCT_URL", "http://product-service:5001")


def get_db():
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )


def initialize_db(retries=30, delay=5):
    """Create the orders table, waiting for MySQL to become available."""
    for _ in range(retries):
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    product_id INT NOT NULL,
                    product_name VARCHAR(100),
                    quantity INT NOT NULL,
                    total DECIMAL(10,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            db.commit()
            cursor.close()
            db.close()
            print("Database initialized", flush=True)
            return
        except Exception as e:  # noqa: BLE001
            print(f"Waiting for MySQL: {e}", flush=True)
            time.sleep(delay)
    raise RuntimeError("Unable to initialize database")


@app.route("/orders", methods=["POST"])
def create_order():
    data = request.get_json(silent=True) or {}
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)

    if not isinstance(product_id, int) or not isinstance(quantity, int):
        return jsonify({"error": "Invalid product ID or quantity"}), 400
    if quantity < 1:
        return jsonify({"error": "Quantity must be positive"}), 400

    try:
        response = requests.get(f"{PRODUCT_URL}/products", timeout=5)
        response.raise_for_status()
    except requests.RequestException as e:
        return jsonify({"error": f"Product service unavailable: {e}"}), 502

    product = next((p for p in response.json() if p["id"] == product_id), None)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    total = product["price"] * quantity

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO orders (product_id, product_name, quantity, total) "
        "VALUES (%s, %s, %s, %s)",
        (product_id, product["name"], quantity, total),
    )
    db.commit()
    order_id = cursor.lastrowid
    cursor.close()
    db.close()

    return (
        jsonify(
            {
                "message": "Order placed successfully",
                "order_id": order_id,
                "product": product["name"],
                "quantity": quantity,
                "total": total,
            }
        ),
        201,
    )


@app.route("/orders", methods=["GET"])
def get_orders():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orders ORDER BY id DESC")
    orders = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(orders)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    initialize_db()
    app.run(host="0.0.0.0", port=5002)
