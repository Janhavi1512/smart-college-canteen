from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import sqlite3
import qrcode
import io
import base64
import uuid
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "smart-canteen-secret-key"

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "canteen.db")


# ----------------------------- DATABASE ------------------------------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS menu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        category TEXT,
        icon TEXT,
        available INTEGER DEFAULT 1,
        stock_qty INTEGER DEFAULT 50
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_code TEXT UNIQUE NOT NULL,
        customer_name TEXT,
        items_json TEXT NOT NULL,
        total_amount REAL NOT NULL,
        status TEXT DEFAULT 'placed',
        payment_status TEXT DEFAULT 'unpaid',
        payment_mode TEXT,
        created_at TEXT NOT NULL
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        menu_id INTEGER,
        item_name TEXT,
        customer_name TEXT,
        rating INTEGER NOT NULL,
        comment TEXT,
        created_at TEXT NOT NULL
    )""")

    conn.commit()

    c.execute("SELECT COUNT(*) FROM menu")
    if c.fetchone()[0] == 0:
        sample = [
            ("Veg Thali", "Rice, dal, sabzi, roti & salad", 60.0, "Meals", "🍛", 1, 30),
            ("Paneer Butter Masala", "Served with 2 tandoori rotis", 90.0, "Meals", "🍲", 1, 20),
            ("Masala Dosa", "Crispy dosa with chutney & sambar", 50.0, "South Indian", "🥞", 1, 15),
            ("Samosa (2 pcs)", "Crispy fried samosas with chutney", 20.0, "Snacks", "🥟", 1, 40),
            ("Veg Sandwich", "Grilled sandwich with fresh veggies", 35.0, "Snacks", "🥪", 1, 25),
            ("Cold Coffee", "Chilled coffee topped with ice cream", 40.0, "Beverages", "🥤", 1, 30),
            ("Masala Chai", "Hot spiced Indian tea", 15.0, "Beverages", "☕", 1, 50),
            ("Chole Bhature", "Spicy chickpea curry with fried bread", 55.0, "North Indian", "🍛", 0, 0),
            ("Fruit Salad", "Fresh seasonal mixed fruits", 30.0, "Healthy", "🥗", 1, 20),
            ("Veg Burger", "Served with crispy fries", 65.0, "Snacks", "🍔", 1, 18),
        ]
        c.executemany(
            "INSERT INTO menu (name, description, price, category, icon, available, stock_qty) VALUES (?,?,?,?,?,?,?)",
            sample,
        )
        conn.commit()

    conn.close()


# ----------------------------- HELPERS --------------------------------------

def generate_qr_base64(data: str) -> str:
    """Generate a QR code for `data` and return it as a base64 PNG string."""
    qr = qrcode.QRCode(box_size=8, border=3)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def new_order_code() -> str:
    return "SCC-" + uuid.uuid4().hex[:8].upper()


# ----------------------------- CUSTOMER ROUTES -------------------------------

@app.route("/")
def home():
    conn = get_db()
    items = conn.execute("SELECT * FROM menu ORDER BY category, name").fetchall()
    conn.close()
    categories = sorted(set(i["category"] for i in items))
    return render_template("index.html", items=items, categories=categories)


@app.route("/api/menu")
def api_menu():
    conn = get_db()
    items = conn.execute("SELECT * FROM menu ORDER BY category, name").fetchall()
    conn.close()
    return jsonify([dict(i) for i in items])


@app.route("/order", methods=["POST"])
def place_order():
    data = request.get_json(force=True)
    customer_name = (data.get("customer_name") or "Guest").strip()
    cart = data.get("cart") or []

    if not cart:
        return jsonify({"error": "Cart is empty"}), 400

    conn = get_db()
    c = conn.cursor()

    order_items = []
    total = 0.0

    for entry in cart:
        item = c.execute("SELECT * FROM menu WHERE id = ?", (entry["id"],)).fetchone()
        if not item:
            continue
        qty = max(1, int(entry.get("qty", 1)))
        if not item["available"] or item["stock_qty"] < qty:
            conn.close()
            return jsonify({"error": f'"{item["name"]}" is not available in the requested quantity'}), 400
        subtotal = round(item["price"] * qty, 2)
        total += subtotal
        order_items.append({
            "id": item["id"],
            "name": item["name"],
            "price": item["price"],
            "qty": qty,
            "subtotal": subtotal,
        })

    if not order_items:
        conn.close()
        return jsonify({"error": "No valid items in cart"}), 400

    # Decrement stock
    for oi in order_items:
        c.execute("UPDATE menu SET stock_qty = stock_qty - ? WHERE id = ?", (oi["qty"], oi["id"]))
        c.execute("UPDATE menu SET available = 0 WHERE id = ? AND stock_qty <= 0", (oi["id"],))

    order_code = new_order_code()
    created_at = datetime.now().strftime("%d %b %Y, %I:%M %p")

    c.execute(
        "INSERT INTO orders (order_code, customer_name, items_json, total_amount, status, payment_status, created_at) "
        "VALUES (?, ?, ?, ?, 'placed', 'unpaid', ?)",
        (order_code, customer_name, json.dumps(order_items), round(total, 2), created_at),
    )
    conn.commit()
    conn.close()

    return jsonify({"order_code": order_code, "redirect": url_for("receipt", order_code=order_code)})


@app.route("/receipt/<order_code>")
def receipt(order_code):
    conn = get_db()
    order = conn.execute("SELECT * FROM orders WHERE order_code = ?", (order_code,)).fetchone()
    conn.close()

    if not order:
        return "Order not found", 404

    items = json.loads(order["items_json"])
    qr_b64 = generate_qr_base64(order_code)

    return render_template("receipt.html", order=order, items=items, qr_b64=qr_b64)


@app.route("/api/order_status/<order_code>")
def api_order_status(order_code):
    conn = get_db()
    order = conn.execute("SELECT * FROM orders WHERE order_code = ?", (order_code,)).fetchone()
    conn.close()
    if not order:
        return jsonify({"error": "not found"}), 404
    return jsonify({"status": order["status"], "payment_status": order["payment_status"]})


# ----------------------------- COUNTER (STAFF) ROUTES -------------------------

@app.route("/counter")
def counter():
    return render_template("counter.html")


@app.route("/api/counter/lookup", methods=["POST"])
def counter_lookup():
    data = request.get_json(force=True)
    order_code = (data.get("order_code") or "").strip().upper()

    conn = get_db()
    order = conn.execute("SELECT * FROM orders WHERE order_code = ?", (order_code,)).fetchone()
    conn.close()

    if not order:
        return jsonify({"error": "No order found with this receipt code"}), 404

    items = json.loads(order["items_json"])
    return jsonify({
        "order_code": order["order_code"],
        "customer_name": order["customer_name"],
        "items": items,
        "total_amount": order["total_amount"],
        "status": order["status"],
        "payment_status": order["payment_status"],
        "created_at": order["created_at"],
    })


@app.route("/api/counter/pay", methods=["POST"])
def counter_pay():
    data = request.get_json(force=True)
    order_code = (data.get("order_code") or "").strip().upper()
    payment_mode = data.get("payment_mode", "cash")

    conn = get_db()
    order = conn.execute("SELECT * FROM orders WHERE order_code = ?", (order_code,)).fetchone()
    if not order:
        conn.close()
        return jsonify({"error": "Order not found"}), 404

    if order["payment_status"] == "paid":
        conn.close()
        return jsonify({"error": "This order has already been paid & served"}), 400

    conn.execute(
        "UPDATE orders SET payment_status = 'paid', status = 'completed', payment_mode = ? WHERE order_code = ?",
        (payment_mode, order_code),
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})


# ----------------------------- REVIEWS ----------------------------------------

@app.route("/reviews")
def reviews_page():
    conn = get_db()
    items = conn.execute("SELECT id, name FROM menu ORDER BY name").fetchall()
    reviews = conn.execute(
        "SELECT r.*, m.name as menu_name FROM reviews r LEFT JOIN menu m ON r.menu_id = m.id "
        "ORDER BY r.id DESC"
    ).fetchall()
    conn.close()
    return render_template("reviews.html", items=items, reviews=reviews)


@app.route("/api/reviews", methods=["POST"])
def add_review():
    data = request.get_json(force=True)
    menu_id = data.get("menu_id")
    rating = int(data.get("rating", 0))
    comment = (data.get("comment") or "").strip()
    customer_name = (data.get("customer_name") or "Anonymous").strip()

    if rating < 1 or rating > 5:
        return jsonify({"error": "Rating must be between 1 and 5"}), 400

    conn = get_db()
    item = conn.execute("SELECT name FROM menu WHERE id = ?", (menu_id,)).fetchone()
    item_name = item["name"] if item else "General"

    conn.execute(
        "INSERT INTO reviews (menu_id, item_name, customer_name, rating, comment, created_at) VALUES (?,?,?,?,?,?)",
        (menu_id, item_name, customer_name, rating, comment, datetime.now().strftime("%d %b %Y, %I:%M %p")),
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})


# ----------------------------- ADMIN (simple, no login) ------------------------

@app.route("/admin")
def admin():
    conn = get_db()
    items = conn.execute("SELECT * FROM menu ORDER BY category, name").fetchall()
    orders = conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    return render_template("admin.html", items=items, orders=orders)


@app.route("/api/admin/toggle_availability", methods=["POST"])
def toggle_availability():
    data = request.get_json(force=True)
    menu_id = data.get("id")
    conn = get_db()
    item = conn.execute("SELECT * FROM menu WHERE id = ?", (menu_id,)).fetchone()
    if not item:
        conn.close()
        return jsonify({"error": "Item not found"}), 404
    new_val = 0 if item["available"] else 1
    conn.execute("UPDATE menu SET available = ? WHERE id = ?", (new_val, menu_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "available": new_val})


@app.route("/api/admin/update_stock", methods=["POST"])
def update_stock():
    data = request.get_json(force=True)
    menu_id = data.get("id")
    stock_qty = max(0, int(data.get("stock_qty", 0)))
    conn = get_db()
    conn.execute(
        "UPDATE menu SET stock_qty = ?, available = ? WHERE id = ?",
        (stock_qty, 1 if stock_qty > 0 else 0, menu_id),
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})


init_db()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
