import json
import streamlit as st
from datetime import datetime

# ---------- File Names ----------
SALES_FILE = "sales_records.json"
INVENTORY_FILE = "inventory.json"

STORE_LOCATIONS = [
    "1 E Penn Sq",
    "5600 Germantown Ave",
    "2644 Germantown Ave"
]

# ---------- Admin Credentials ----------
ADMIN_CREDENTIALS = {"admin": "1234"}  # Change this password

# ---------- Helper Functions ----------
def load_json(filename, default):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return default

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def load_sales():
    return load_json(SALES_FILE, [])

def save_sales(sales):
    save_json(SALES_FILE, sales)

def load_inventory():
    return load_json(INVENTORY_FILE, {store: {} for store in STORE_LOCATIONS})

def save_inventory(inventory):
    save_json(INVENTORY_FILE, inventory)

def reduce_inventory(store, product, qty):
    inventory = load_inventory()
    if store not in inventory or product not in inventory[store]:
        st.error(f"Product {product} not found in inventory at {store}.")
        return False
    if inventory[store][product]["quantity"] < qty:
        st.error(f"Not enough stock for {product}. Available: {inventory[store][product]['quantity']}")
        return False
    inventory[store][product]["quantity"] -= qty
    save_inventory(inventory)
    return True

def calculate_totals(sales):
    return {
        "cost": sum(sum(item["cost"] * item["quantity"] for item in s["items"]) for s in sales),
        "sold": sum(sum(item["sold"] * item["quantity"] for item in s["items"]) for s in sales),
        "acc": sum(sum((item["sold"] - item["cost"]) * item["quantity"] for item in s["items"]) for s in sales),
        "cash": sum(sum(item["sold"] * item["quantity"] for item in s["items"]) for s in sales if s["payment_method"] == "Cash"),
        "card": sum(sum(item["sold"] * item["quantity"] for item in s["items"]) for s in sales if s["payment_method"] == "Card")
    }

def show_totals(title, totals):
    st.write(
        f"**{title}** | Cost: ${totals['cost']:.2f} | Sold: ${totals['sold']:.2f} | "
        f"Acc: ${totals['acc']:.2f} | Cash: ${totals['cash']:.2f} | Card: ${totals['card']:.2f}"
    )

# ---------- Streamlit App ----------
st.set_page_config(page_title="Total Wireless App", layout="wide")

st.title("📱 Total Wireless Sales & Inventory App by PBarua")

# ---------- Employee Login ----------
st.sidebar.header("🔑 Login")
employee = st.sidebar.text_input("Employee Name", value="").strip()
password = st.sidebar.text_input("Password", type="password")

is_admin = employee in ADMIN_CREDENTIALS and password == ADMIN_CREDENTIALS[employee]

if not employee:
    st.sidebar.warning("Enter your name to continue")
    st.stop()

st.sidebar.success(f"Logged in as {employee}")

menu = st.sidebar.radio("Menu", ["Add Sale", "Inventory", "Reports"])

# ---------- Add Sale (Multiple Products) ----------
if menu == "Add Sale":
    st.header("➕ Add Sale")

    store = st.selectbox("Select Store", STORE_LOCATIONS)
    inventory = load_inventory()

    if store not in inventory or not inventory[store]:
        st.warning("No products available in this store inventory.")
        st.stop()

    sale_items = []
    available_products = list(inventory[store].keys())

    num_items = st.number_input("Number of Products in this Sale", 1, 10, 1)

    for i in range(num_items):
        st.subheader(f"Product {i+1}")
        product = st.selectbox(f"Select Product {i+1}", available_products, key=f"prod_{i}")
        qty = st.number_input(f"Quantity for {product}", 1, 100, 1, key=f"qty_{i}")

        cost_price = inventory[store][product]["cost"]
        sold_price = st.number_input(f"Sold Price for {product}", 0.0, 10000.0, cost_price, key=f"sold_{i}")

        sale_items.append({
            "product": product,
            "quantity": qty,
            "cost": cost_price,
            "sold": sold_price
        })

    payment_method = st.selectbox("Payment Method", ["Cash", "Card"])

    if st.button("💾 Save Sale"):
        # Validate stock
        for item in sale_items:
            if not reduce_inventory(store, item["product"], item["quantity"]):
                st.stop()

        sales = load_sales()
        sales.append({
            "employee": employee,
            "store": store,
            "date": datetime.now().strftime("%m/%d/%Y %H:%M"),
            "items": sale_items,
            "payment_method": payment_method
        })
        save_sales(sales)
        st.success("✅ Sale saved successfully!")

# The rest of the code (Reports, Inventory Management, Admin Panel) will be updated to support multi-product sales and full product management
