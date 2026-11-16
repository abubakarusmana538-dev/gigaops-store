from flask import Flask, jsonify

app = Flask(__name__)

products = [
    {"id": 1, "name": "Laptop", "price": 55000},
    {"id": 2, "name": "Mobile", "price": 25000},
    {"id": 3, "name": "Keyboard", "price": 1500},
    {"id": 4, "name": "Monitor", "price": 12000},
]


@app.route("/products", methods=["GET"])
def get_products():
    return jsonify(products)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
