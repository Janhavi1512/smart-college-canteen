🍽️ Smart College Canteen

A web-based canteen ordering system for college students. Students browse the menu, place an order online and get an instant receipt with a unique order code and QR code. At the counter, staff scan the QR code (or type the code) to confirm payment and complete the order. An admin page lets the canteen manage menu availability and stock.

🔗 Live demo: https://smart-college-canteen.onrender.com

The demo runs on a free hosting plan, so the first load may take up to a minute while the server wakes up.

📌 Problem

Long queues at college canteens waste students' break time, and staff have no easy way to track orders or stock. This project lets students order in advance and pay at the counter using a QR receipt, so the counter only has to verify the order and collect payment.

✨ Features

For students

Browse the menu by category (Beverages, Healthy, Meals, North Indian, Snacks, South Indian)
See live stock and availability for every item
Add items to a cart, enter a name and place an order
Get a receipt with a unique order code (SCC-XXXXXXXX) and a QR code
Receipt page checks the order status automatically every 5 seconds
Rate (1–5 stars) and review menu items

For counter staff

Scan the receipt QR code with the device camera, or enter the order code manually
View the order details and total, then mark it as paid (cash, etc.) and completed
Already-paid orders are blocked from being paid twice

For admin

Turn menu items on or off
Update stock quantity (an item is marked unavailable automatically when stock reaches 0)
View the 50 most recent orders

System behaviour

Stock is checked when an order is placed, and quantities are deducted automatically
Items become unavailable when their stock runs out
Sample menu of 10 items is created automatically on first run
🛠️ Tech Stack
Layer	Technology
Backend	Python, Flask
Database	SQLite
Frontend	HTML, CSS, JavaScript
QR code generation	qrcode + Pillow
QR code scanning	html5-qrcode (browser camera)
Deployment	Gunicorn, Render
🗄️ Database

Three tables in SQLite:

menu: id, name, description, price, category, icon, available, stock_qty
orders: id, order_code, customer_name, items_json, total_amount, status, payment_status, payment_mode, created_at
reviews: id, menu_id, item_name, customer_name, rating, comment, created_at
🔌 Routes and API
Route	Method	Purpose
/	GET	Menu page
/api/menu	GET	Menu items as JSON
/order	POST	Place an order (validates stock, deducts quantities)
/receipt/<order_code>	GET	Receipt page with QR code
/api/order_status/<order_code>	GET	Order and payment status
/counter	GET	Counter page (scan / enter code)
/api/counter/lookup	POST	Find an order by its code
/api/counter/pay	POST	Mark an order as paid and completed
/reviews	GET	Reviews page
/api/reviews	POST	Submit a rating and review
/admin	GET	Admin page
/api/admin/toggle_availability	POST	Turn an item on or off
/api/admin/update_stock	POST	Update stock quantity
📁 Project Structure
smart-college-canteen/
│
├── app.py                # Flask app, routes and database setup
├── requirements.txt      # Python dependencies
├── Procfile              # Gunicorn start command for deployment
│
├── templates/
│   ├── base.html
│   ├── index.html        # Menu and cart
│   ├── receipt.html      # Receipt with QR code
│   ├── counter.html      # Counter / payment page
│   ├── reviews.html
│   └── admin.html
│
├── static/
│   ├── css/style.css
│   └── js/script.js
│
└── images/               # Screenshots used in this README
▶️ How to Run Locally
Clone the repository
bash
   git clone https://github.com/Janhavi1512/smart-college-canteen.git
   cd smart-college-canteen
Create a virtual environment
bash
   python -m venv venv
Activate it
bash
   # Windows
   venv\Scripts\activate
   # macOS / Linux
   source venv/bin/activate
Install dependencies
bash
   pip install -r requirements.txt
Start the app
bash
   python app.py
Open http://localhost:5000

The database (canteen.db) and the sample menu are created automatically on the first run.

🔄 How It Works
Student browses menu → adds items to cart → places order
        ↓
Stock is checked and deducted → order saved with unique code
        ↓
Receipt with QR code is shown to the student
        ↓
Counter staff scan the QR / enter the code
        ↓
Order is verified → payment recorded → order marked completed
⚠️ Current Limitations
The /admin and /counter pages do not have a login yet, so they are open to anyone who knows the URL.
SQLite on a free hosting plan may lose data when the server restarts.
Stock is checked and deducted in separate steps, so two orders placed at exactly the same moment could oversell an item.
The secret key is set in the code instead of an environment variable.
🚀 Future Improvements
Login for admin and counter staff
Online payments (UPI)
Move to a hosted database such as PostgreSQL
Order history for students
Sales and popular-item reports for the canteen
Add or edit menu items from the admin page
