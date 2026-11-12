"""Inventory Management System - short version (Python + SQLite)"""
import sqlite3
from datetime import date

db = sqlite3.connect("inventory.db")
db.executescript("""
CREATE TABLE IF NOT EXISTS Suppliers(supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_name TEXT, phone TEXT, email TEXT, address TEXT);
CREATE TABLE IF NOT EXISTS Products(product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, category TEXT, price REAL, quantity INTEGER DEFAULT 0,
    reorder_level INTEGER DEFAULT 5, supplier_id INTEGER);
CREATE TABLE IF NOT EXISTS Sales(sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_date TEXT, product_id INTEGER, quantity_sold INTEGER, unit_price REAL, total_amount REAL);
CREATE TABLE IF NOT EXISTS Stock_Transactions(transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER, transaction_type TEXT, quantity INTEGER, transaction_date TEXT);
""")


def show(rows):
    for r in rows:
        print("  ", *r, sep=" | ")
    if not rows:
        print("   (no records)")


def add_supplier():
    db.execute("INSERT INTO Suppliers(supplier_name,phone,email,address) VALUES(?,?,?,?)",
               (input("Name: "), input("Phone: "), input("Email: "), input("Address: ")))
    db.commit()


def add_product():
    cur = db.execute(
        "INSERT INTO Products(name,category,price,quantity,reorder_level,supplier_id) VALUES(?,?,?,?,?,?)",
        (input("Name: "), input("Category: "), float(input("Price: ")),
         int(input("Quantity: ")), int(input("Reorder level: ")), int(input("Supplier ID: ") or 0) or None))
    db.commit()
    print("Product ID:", cur.lastrowid)


def receive_stock():
    pid, qty = int(input("Product ID: ")), int(input("Quantity received: "))
    db.execute("UPDATE Products SET quantity=quantity+? WHERE product_id=?", (qty, pid))
    db.execute("INSERT INTO Stock_Transactions(product_id,transaction_type,quantity,transaction_date) "
               "VALUES(?,'RECEIVED',?,?)", (pid, qty, str(date.today())))
    db.commit()
    print("Stock updated.")


def sell():
    pid, qty = int(input("Product ID: ")), int(input("Quantity sold: "))
    row = db.execute("SELECT price,quantity FROM Products WHERE product_id=?", (pid,)).fetchone()
    if not row:
        return print("Product not found.")
    price, available = row
    if qty > available:
        return print(f"Rejected: only {available} in stock.")
    today = str(date.today())
    db.execute("INSERT INTO Sales(sale_date,product_id,quantity_sold,unit_price,total_amount) "
               "VALUES(?,?,?,?,?)", (today, pid, qty, price, price * qty))
    db.execute("UPDATE Products SET quantity=quantity-? WHERE product_id=?", (qty, pid))
    db.execute("INSERT INTO Stock_Transactions(product_id,transaction_type,quantity,transaction_date) "
               "VALUES(?,'ISSUED',?,?)", (pid, qty, today))
    db.commit()
    print(f"Sale saved. Total = {price * qty:.2f}, stock left = {available - qty}")


MENU = {
    "1": ("Add supplier", add_supplier),
    "2": ("Add product", add_product),
    "3": ("View products", lambda: show(db.execute(
        "SELECT product_id,name,category,price,quantity,reorder_level FROM Products").fetchall())),
    "4": ("Receive stock", receive_stock),
    "5": ("Record sale", sell),
    "6": ("Low-stock report", lambda: show(db.execute(
        "SELECT product_id,name,quantity,reorder_level FROM Products WHERE quantity<=reorder_level").fetchall())),
    "7": ("Sales report", lambda: show(db.execute(
        "SELECT sale_id,sale_date,product_id,quantity_sold,total_amount FROM Sales").fetchall())),
}

while True:
    print("\n--- INVENTORY MANAGEMENT SYSTEM ---")
    for k, (label, _) in MENU.items():
        print(f"{k}. {label}")
    print("0. Exit")
    choice = input("Choose: ").strip()
    if choice == "0":
        break
    if choice in MENU:
        try:
            MENU[choice][1]()
        except ValueError:
            print("Invalid input.")
    else:
        print("Invalid choice.")
