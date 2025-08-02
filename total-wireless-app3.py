import json
import streamlit as st
from datetime import datetime

# ---------- File Names ----------
SALES_FILE = "sales_records.json"
INVENTORY_FILE = "inventory.json"

STORE_LOCATIONS = [
    "1 E Penn Sq",
    "5600 Germantion Ave",
    "2644 Germantion Ave"
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
    if inventory[store][product] < qty:
        st.error(f"Not enough stock for {product}. Available: {inventory[store][product]}")
        return False
    inventory[store][product] -= qty
    save_inventory(inventory)
    return True

def calculate_totals(sales):
    return {
        "cost": sum(s["cost"] for s in sales),
        "sold": sum(s["sold"] for s in sales),
        "acc": sum(s["acc"] for s in sales),
        "cash": sum(s["sold"] for s in sales if s["payment_method"] == "Cash"),
        "card": sum(s["sold"] for s in sales if s["payment_method"] == "Card")
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

# ---------- Add Sale ----------
if menu == "Add Sale":
    st.header("➕ Add Sale")

    store = st.selectbox("Select Store", STORE_LOCATIONS)
    sale_type = st.radio("Sale Type", ["Phone Sale", "Bill Payment"])

    if sale_type == "Phone Sale":
        product = st.text_input("Product Name")
        qty = st.number_input("Quantity", 1, 100, 1)
    else:
        product = "Bill Payment"
        qty = 1

    cost = st.number_input("Cost Price ($)", 0.0, 10000.0, 0.0)
    sold = st.number_input("Sold Price ($)", 0.0, 10000.0, 0.0)
    payment_method = st.selectbox("Payment Method", ["Cash", "Card"])

    if st.button("💾 Save Sale"):
        if not product.strip():
            st.error("Product name cannot be empty.")
        else:
            if sale_type == "Phone Sale" and not reduce_inventory(store, product.strip(), qty):
                st.stop()

            acc = sold - cost
            sales = load_sales()
            sales.append({
                "employee": employee,
                "store": store,
                "date": datetime.now().strftime("%m/%d/%Y %H:%M"),
                "type": sale_type,
                "product": product.strip(),
                "quantity": qty,
                "cost": cost,
                "sold": sold,
                "acc": acc,
                "payment_method": payment_method
            })
            save_sales(sales)
            st.success("✅ Sale saved successfully!")

# ---------- Inventory ----------
elif menu == "Inventory":
    st.header("📦 Inventory Management")

    store = st.selectbox("Select Store", STORE_LOCATIONS, key="inv_store")
    inventory = load_inventory()

    st.subheader("Current Inventory")
    if inventory.get(store):
        st.table([{"Product": p, "Quantity": q} for p, q in inventory[store].items()])
    else:
        st.info("No inventory found for this store.")

    st.subheader("➕ Add / Update Inventory")
    new_product = st.text_input("Product Name", key="inv_product")
    qty_add = st.number_input("Quantity to Add", 1, 500, 1)

    if st.button("Update Inventory"):
        if new_product.strip():
            current_qty = inventory.get(store, {}).get(new_product.strip(), 0)
            if store not in inventory:
                inventory[store] = {}
            inventory[store][new_product.strip()] = current_qty + qty_add
            save_inventory(inventory)
            st.success(f"✅ {new_product} updated. New quantity: {inventory[store][new_product.strip()]}")
        else:
            st.error("Enter a valid product name")

# ---------- Reports ----------
elif menu == "Reports":
    st.header("📊 Sales Reports")

    sales = load_sales()
    if not sales:
        st.info("No sales data available.")
        st.stop()

    report_type = st.radio("Report Type", ["All Stores", "By Store", "By Employee"])

    if report_type == "All Stores":
        totals = calculate_totals(sales)
        show_totals("ALL STORES", totals)
        st.table(sales)

    elif report_type == "By Store":
        store = st.selectbox("Select Store", STORE_LOCATIONS)
        filtered = [s for s in sales if s["store"] == store]
        totals = calculate_totals(filtered)
        show_totals(store, totals)
        st.table(filtered)

    elif report_type == "By Employee":
        employees = list(set(s["employee"] for s in sales))
        emp = st.selectbox("Select Employee", employees)
        filtered = [s for s in sales if s["employee"] == emp]
        totals = calculate_totals(filtered)
        show_totals(emp, totals)
        st.table(filtered)

# ---------- Admin Panel ----------
if is_admin:
    st.sidebar.markdown("### ⚙️ Admin Panel")
    admin_action = st.sidebar.radio(
        "Admin Actions",
        [
            "None",
            "View All Sales",
            "Delete All Sales",
            "Delete All Inventory",
            "Delete Specific Sale",
            "Modify Sale Record"
        ]
    )

    # View All Sales
    if admin_action == "View All Sales":
        st.subheader("📄 All Sales Records (Admin View)")
        sales = load_sales()
        if sales:
            st.table(sales)
        else:
            st.info("No sales records found.")

    # Delete All Sales
    elif admin_action == "Delete All Sales":
        with st.sidebar.form(key="delete_all_sales_form"):
            if st.form_submit_button("⚠️ Reset All Sales Data"):
                save_sales([])
                st.sidebar.success("✅ All sales data has been reset!")
                st.experimental_rerun()

    # Delete All Inventory
    elif admin_action == "Delete All Inventory":
        with st.sidebar.form(key="delete_all_inventory_form"):
            if st.form_submit_button("⚠️ Reset All Inventory Data"):
                save_inventory({store: {} for store in STORE_LOCATIONS})
                st.sidebar.success("✅ All inventory has been reset!")
                st.experimental_rerun()

    # Delete Specific Sale
    elif admin_action == "Delete Specific Sale":
        sales = load_sales()
        if sales:
            options = [
                f"{i+1}. {s['date']} | {s['employee']} | {s['store']} | {s['product']} | ${s['sold']}"
                for i, s in enumerate(sales)
            ]
            if 'selected_sale_to_delete' not in st.session_state:
                st.session_state.selected_sale_to_delete = options[0]
            choice = st.sidebar.selectbox("Select Sale to Delete", options, key="sale_delete_select", index=options.index(st.session_state.selected_sale_to_delete))
            st.session_state.selected_sale_to_delete = choice
            index = options.index(choice)

            with st.sidebar.form(key="delete_specific_sale_form"):
                if st.form_submit_button("🗑 Delete Selected Sale"):
                    del sales[index]
                    save_sales(sales)
                    st.sidebar.success("✅ Sale deleted successfully!")
                    st.experimental_rerun()
        else:
            st.sidebar.info("No sales records to delete.")

    # Modify Sale Record
    elif admin_action == "Modify Sale Record":
        sales = load_sales()
        if sales:
            show_all = st.sidebar.checkbox("Show all sales (not just today)", value=False)

            if not show_all:
                today_str = datetime.now().strftime("%m/%d/%Y")
                filtered_sales = [s for s in sales if s["date"].startswith(today_str)]
            else:
                filtered_sales = sales

            if not filtered_sales:
                st.info("No sales records found for the selected filter.")
                st.stop()

            options = [
                f"{i+1}. {s['date']} | {s['employee']} | {s['store']} | {s['product']} | ${s['sold']}"
                for i, s in enumerate(filtered_sales)
            ]

            if 'selected_sale_to_modify' not in st.session_state or st.session_state.get('last_sales_count', 0) != len(filtered_sales):
                st.session_state.selected_sale_to_modify = options[0]
                st.session_state.last_sales_count = len(filtered_sales)

            choice = st.sidebar.selectbox("Select Sale to Modify", options, key="sale_modify_select", index=options.index(st.session_state.selected_sale_to_modify))
            st.session_state.selected_sale_to_modify = choice
            index = options.index(choice)
            selected_sale = filtered_sales[index]

            st.subheader("✏️ Modify Sale Record")

            new_employee = st.text_input("Employee", value=selected_sale["employee"])
            new_store = st.selectbox("Store", STORE_LOCATIONS, index=STORE_LOCATIONS.index(selected_sale["store"]))
            new_product = st.text_input("Product", value=selected_sale["product"])
            new_quantity = st.number_input("Quantity", 1, 1000, selected_sale["quantity"])
            new_cost = st.number_input("Cost Price ($)", 0.0, 100000.0, selected_sale["cost"])
            new_sold = st.number_input("Sold Price ($)", 0.0, 100000.0, selected_sale["sold"])
            new_payment = st.selectbox(
                "Payment Method",
                ["Cash", "Card"],
                index=0 if selected_sale["payment_method"] == "Cash" else 1
            )

            # Parse existing date/time string into datetime object
            try:
                dt = datetime.strptime(selected_sale["date"], "%m/%d/%Y %H:%M")
            except Exception:
                dt = datetime.now()

            new_date = st.date_input("Sale Date", dt.date())
            new_time = st.time_input("Sale Time", dt.time())

            combined_datetime = datetime.combine(new_date, new_time).strftime("%m/%d/%Y %H:%M")

            if st.button("💾 Save Changes"):
                # Validation
                if new_quantity < 1:
                    st.error("Quantity must be at least 1.")
                elif new_cost < 0 or new_sold < 0:
                    st.error("Cost and Sold price must be non-negative.")
                elif new_sold < new_cost:
                    st.warning("Sold price is less than cost price; profit will be negative.")
                    # Allowed but warn
                else:
                    # Update original sales list, not just filtered
                    orig_index = sales.index(selected_sale)
                    sales[orig_index] = {
                        "employee": new_employee.strip(),
                        "store": new_store,
                        "date": combined_datetime,
                        "type": selected_sale["type"],
                        "product": new_product.strip(),
                        "quantity": new_quantity,
                        "cost": new_cost,
                        "sold": new_sold,
                        "acc": new_sold - new_cost,
                        "payment_method": new_payment
                    }
                    save_sales(sales)
                    st.success("✅ Sale record updated successfully!")
                    st.experimental_rerun()
        else:
            st.info("No sales records to modify.")
