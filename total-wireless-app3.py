import streamlit as st
from datetime import datetime

# ---------- Constants ----------
STORE_LOCATIONS = [
    "1 E Penn Sq",
    "5600 Germantown Ave",
    "2644 Germantown Ave"
]

ADMIN_CREDENTIALS = {"admin": "1234"}  # Change this password

# ---------- Session State Initialization ----------
if 'sales' not in st.session_state:
    st.session_state.sales = []

if 'inventory' not in st.session_state:
    st.session_state.inventory = {store: {} for store in STORE_LOCATIONS}

if 'products' not in st.session_state:
    # products dict: store -> product -> {"cost": float}
    st.session_state.products = {store: {} for store in STORE_LOCATIONS}

# ---------- Helper Functions ----------
def load_sales():
    return st.session_state.sales

def save_sales(sales):
    st.session_state.sales = sales

def load_inventory():
    return st.session_state.inventory

def save_inventory(inventory):
    st.session_state.inventory = inventory

def load_products():
    return st.session_state.products

def save_products(products):
    st.session_state.products = products

def reduce_inventory(store, product, qty):
    inventory = load_inventory()
    if store not in inventory or product not in inventory[store]:
        st.error(f"Product '{product}' not found in inventory at {store}.")
        return False
    if inventory[store][product] < qty:
        st.error(f"Not enough stock for '{product}'. Available: {inventory[store][product]}")
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

# ---------- Streamlit App Setup ----------
st.set_page_config(page_title="Total Wireless App", layout="wide")
st.title("📱 Total Wireless Sales & Inventory App by PBarua")

# ---------- Employee Login ----------
st.sidebar.header("🔑 Login")
employee = st.sidebar.text_input("Employee Name", "").strip()
password = st.sidebar.text_input("Password", type="password")

is_admin = employee in ADMIN_CREDENTIALS and password == ADMIN_CREDENTIALS.get(employee, "")

if not employee:
    st.sidebar.warning("Enter your name to continue")
    st.stop()

st.sidebar.success(f"Logged in as {employee}")

menu = st.sidebar.radio("Menu", ["Add Sale", "Inventory", "Reports"])

# ---------- Add Sale ----------
if menu == "Add Sale":
    st.header("➕ Add Sale")

    store = st.selectbox("Select Store", STORE_LOCATIONS)

    products_for_store = load_products().get(store, {})
    inventory_for_store = load_inventory().get(store, {})

    sale_type = st.radio("Sale Type", ["Phone Sale", "Bill Payment", "Custom Items + Phone"])

    if sale_type == "Bill Payment":
        # Bill payment sale (single)
        product = "Bill Payment"
        qty = 1
        cost = 0.0
        sold = st.number_input("Payment Amount ($)", 0.0, 100000.0, 0.0)
        payment_method = st.selectbox("Payment Method", ["Cash", "Card"])

        if st.button("💾 Save Sale"):
            acc = sold - cost
            sales = load_sales()
            sales.append({
                "employee": employee,
                "store": store,
                "date": datetime.now().strftime("%m/%d/%Y %H:%M"),
                "type": sale_type,
                "products": [{"name": product, "quantity": qty, "cost": cost, "sold": sold}],
                "cost": cost,
                "sold": sold,
                "acc": acc,
                "payment_method": payment_method
            })
            save_sales(sales)
            st.success("✅ Bill payment saved successfully!")

    else:
        # Phone Sale or Phone + Custom Items
        st.write("Select products and quantities:")

        products_selected = []
        total_cost = 0.0
        total_sold = 0.0

        # Allow multiple products selection from inventory for that store
        for product_name, product_cost in products_for_store.items():
            available_qty = inventory_for_store.get(product_name, 0)
            if available_qty > 0:
                qty = st.number_input(f"{product_name} (Available: {available_qty})", 0, available_qty, 0)
                if qty > 0:
                    sold_price = st.number_input(f"Sold Price for {product_name} (per unit)", 0.0, 100000.0, float(product_cost))
                    products_selected.append({"name": product_name, "quantity": qty, "cost": product_cost * qty, "sold": sold_price * qty})
                    total_cost += product_cost * qty
                    total_sold += sold_price * qty

        # Add custom product if sale_type == "Custom Items + Phone"
        if sale_type == "Custom Items + Phone":
            st.subheader("Add Custom Products")
            custom_product_name = st.text_input("Custom Product Name")
            custom_qty = st.number_input("Custom Product Quantity", 0, 1000, 0)
            custom_cost = st.number_input("Custom Product Cost Price ($)", 0.0, 100000.0, 0.0)
            custom_sold = st.number_input("Custom Product Sold Price ($)", 0.0, 100000.0, 0.0)

            if custom_product_name.strip() and custom_qty > 0:
                products_selected.append({
                    "name": custom_product_name.strip(),
                    "quantity": custom_qty,
                    "cost": custom_cost * custom_qty,
                    "sold": custom_sold * custom_qty
                })
                total_cost += custom_cost * custom_qty
                total_sold += custom_sold * custom_qty

        payment_method = st.selectbox("Payment Method", ["Cash", "Card"])

        if st.button("💾 Save Sale"):
            if not products_selected:
                st.error("Select at least one product with quantity greater than zero.")
            else:
                # Check inventory for each product and reduce
                inventory_ok = True
                for item in products_selected:
                    name = item["name"]
                    qty = item["quantity"]
                    if name != "Bill Payment":  # Bill payment no inventory change
                        if not reduce_inventory(store, name, qty):
                            inventory_ok = False
                            break
                if not inventory_ok:
                    st.stop()

                acc = total_sold - total_cost
                sales = load_sales()
                sales.append({
                    "employee": employee,
                    "store": store,
                    "date": datetime.now().strftime("%m/%d/%Y %H:%M"),
                    "type": sale_type,
                    "products": products_selected,
                    "cost": total_cost,
                    "sold": total_sold,
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
    products = load_products()

    st.subheader("Current Inventory")
    if inventory.get(store):
        inv_list = [{"Product": p, "Quantity": q, "Cost Price": products.get(store, {}).get(p, 0.0)} for p, q in inventory[store].items()]
        st.table(inv_list)
    else:
        st.info("No inventory found for this store.")

    st.subheader("➕ Add / Update Inventory")

    new_product = st.text_input("Product Name", key="inv_product")
    qty_add = st.number_input("Quantity to Add", 1, 500, 1)
    cost_price = st.number_input("Cost Price ($)", 0.0, 100000.0, 0.0)

    if st.button("Update Inventory"):
        if new_product.strip():
            # Update inventory quantity
            current_qty = inventory.get(store, {}).get(new_product.strip(), 0)
            if store not in inventory:
                inventory[store] = {}
            inventory[store][new_product.strip()] = current_qty + qty_add
            save_inventory(inventory)

            # Update product cost price
            if store not in products:
                products[store] = {}
            products[store][new_product.strip()] = cost_price
            save_products(products)

            st.success(f"✅ '{new_product}' updated. New quantity: {inventory[store][new_product.strip()]}, Cost Price: ${cost_price:.2f}")
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
        st.table(format_sales_for_display(sales))

    elif report_type == "By Store":
        store = st.selectbox("Select Store", STORE_LOCATIONS)
        filtered = [s for s in sales if s["store"] == store]
        totals = calculate_totals(filtered)
        show_totals(store, totals)
        st.table(format_sales_for_display(filtered))

    elif report_type == "By Employee":
        employees = list(set(s["employee"] for s in sales))
        emp = st.selectbox("Select Employee", employees)
        filtered = [s for s in sales if s["employee"] == emp]
        totals = calculate_totals(filtered)
        show_totals(emp, totals)
        st.table(format_sales_for_display(filtered))

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
            "Modify Sale Record",
            "Manage Products"
        ]
    )

    # Helper to format sales with multiple products nicely
    def format_sales_for_display(sales_list):
        display_list = []
        for sale in sales_list:
            products_desc = ", ".join([f"{p['name']} (x{p['quantity']})" for p in sale.get("products", [])])
            display_list.append({
                "Employee": sale["employee"],
                "Store": sale["store"],
                "Date": sale["date"],
                "Type": sale["type"],
                "Products": products_desc,
                "Cost": sale["cost"],
                "Sold": sale["sold"],
                "Profit": sale["acc"],
                "Payment": sale["payment_method"],
            })
        return display_list

    # View All Sales
    if admin_action == "View All Sales":
        st.subheader("📄 All Sales Records (Admin View)")
        sales = load_sales()
        if sales:
            st.table(format_sales_for_display(sales))
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
                save_products({store: {} for store in STORE_LOCATIONS})
                st.sidebar.success("✅ All inventory and products have been reset!")
                st.experimental_rerun()

    # Delete Specific Sale
    elif admin_action == "Delete Specific Sale":
        sales = load_sales()
        if sales:
            options = [
                f"{i+1}. {s['date']} | {s['employee']} | {s['store']} | {', '.join([p['name'] for p in s['products']])} | ${s['sold']}"
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
                f"{i+1}. {s['date']} | {s['employee']} | {s['store']} | {', '.join([p['name'] for p in s['products']])} | ${s['sold']}"
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

            # Editable list of products in sale
            edited_products = []
            st.write("Edit Products in Sale:")
            for i, prod in enumerate(selected_sale["products"]):
                col1, col2, col3, col4 = st.columns([4,2,2,2])
                with col1:
                    name = st.text_input(f"Product Name #{i+1}", value=prod["name"], key=f"prod_name_{i}")
                with col2:
                    qty = st.number_input(f"Quantity #{i+1}", min_value=1, max_value=10000, value=prod["quantity"], key=f"prod_qty_{i}")
                with col3:
                    cost = st.number_input(f"Cost Price (total) #{i+1}", min_value=0.0, max_value=1000000.0, value=prod["cost"], key=f"prod_cost_{i}")
                with col4:
                    sold = st.number_input(f"Sold Price (total) #{i+1}", min_value=0.0, max_value=1000000.0, value=prod["sold"], key=f"prod_sold_{i}")

                edited_products.append({"name": name.strip(), "quantity": qty, "cost": cost, "sold": sold})

            # Option to add a new product
            if st.checkbox("Add New Product to this Sale"):
                new_prod_name = st.text_input("New Product Name", key="new_prod_name")
                new_prod_qty = st.number_input("New Product Quantity", min_value=1, max_value=10000, value=1, key="new_prod_qty")
                new_prod_cost = st.number_input("New Product Cost Price (total)", min_value=0.0, max_value=1000000.0, value=0.0, key="new_prod_cost")
                new_prod_sold = st.number_input("New Product Sold Price (total)", min_value=0.0, max_value=1000000.0, value=0.0, key="new_prod_sold")

                if new_prod_name.strip() != "":
                    edited_products.append({
                        "name": new_prod_name.strip(),
                        "quantity": new_prod_qty,
                        "cost": new_prod_cost,
                        "sold": new_prod_sold
                    })

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
                # Validate
                valid = True
                for p in edited_products:
                    if p["quantity"] < 1:
                        st.error(f"Quantity for product '{p['name']}' must be at least 1.")
                        valid = False
                    if p["cost"] < 0 or p["sold"] < 0:
                        st.error(f"Cost and Sold price must be non-negative for product '{p['name']}'.")
                        valid = False

                if not valid:
                    st.stop()

                total_cost = sum(p["cost"] for p in edited_products)
                total_sold = sum(p["sold"] for p in edited_products)

                sales_list = load_sales()
                orig_index = sales_list.index(selected_sale)
                sales_list[orig_index] = {
                    "employee": new_employee.strip(),
                    "store": new_store,
                    "date": combined_datetime,
                    "type": selected_sale["type"],
                    "products": edited_products,
                    "cost": total_cost,
                    "sold": total_sold,
                    "acc": total_sold - total_cost,
                    "payment_method": new_payment
                }
                save_sales(sales_list)
                st.success("✅ Sale record updated successfully!")
                st.experimental_rerun()

        else:
            st.info("No sales records to modify.")

    # Manage Products
    elif admin_action == "Manage Products":
        st.subheader("🛠️ Manage Products")

        products = load_products()

        store = st.selectbox("Select Store", STORE_LOCATIONS, key="product_manage_store")

        store_products = products.get(store, {})

        if store_products:
            st.write(f"Current products and cost prices in {store}:")
            for p_name, p_cost in store_products.items():
                col1, col2, col3 = st.columns([5, 3, 2])
                with col1:
                    new_name = st.text_input(f"Product Name ({p_name})", value=p_name, key=f"prod_name_edit_{p_name}")
                with col2:
                    new_cost = st.number_input(f"Cost Price ($) for {p_name}", min_value=0.0, max_value=1000000.0, value=p_cost, key=f"prod_cost_edit_{p_name}")
                with col3:
                    if st.button(f"Delete {p_name}", key=f"delete_prod_{p_name}"):
                        del products[store][p_name]
                        save_products(products)
                        st.experimental_rerun()

                # Rename product if changed
                if new_name.strip() != p_name:
                    # Rename key safely
                    products[store][new_name.strip()] = products[store].pop(p_name)
                    save_products(products)
                    st.experimental_rerun()

                # Update cost price if changed
                if products[store][new_name.strip()] != new_cost:
                    products[store][new_name.strip()] = new_cost
                    save_products(products)
                    st.experimental_rerun()
        else:
            st.info("No products found for this store.")

        st.markdown("---")
        st.subheader("Add New Product")

        new_prod_name = st.text_input("New Product Name", key="new_prod_add_name")
        new_prod_cost = st.number_input("New Product Cost Price ($)", 0.0, 100000.0, 0.0, key="new_prod_add_cost")

        if st.button("Add Product"):
            if new_prod_name.strip() == "":
                st.error("Product name cannot be empty.")
            elif new_prod_name.strip() in products.get(store, {}):
                st.error("Product already exists.")
            else:
                if store not in products:
                    products[store] = {}
                products[store][new_prod_name.strip()] = new_prod_cost
                save_products(products)
                st.success(f"Product '{new_prod_name.strip()}' added with cost price ${new_prod_cost:.2f}")
                st.experimental_rerun()

