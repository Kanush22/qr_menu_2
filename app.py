import streamlit as st
from utils import generate_qr  # Only import generate_qr here
from database import get_menu_items, place_order, get_orders, update_order_status, add_menu_item, update_menu_item_status, initialize_db  # Import initialize_db
from auth import login_admin
from datetime import datetime

# Initialize database
initialize_db()

# Streamlit page config
st.set_page_config(page_title="Nekko Upahar - QR Menu App", layout="wide")

# Navigation menu
menu = ["Homepage", "Customer View", "Admin Panel"]
choice = st.sidebar.selectbox("Navigate", menu)

# ---------------- HOMEPAGE ----------------
if choice == "Homepage":
    st.title("Welcome to Nekko Upahar")
    st.subheader("A delightful experience with our delicious meals")
    st.image("https://via.placeholder.com/800x400.png?text=Nekko+Upahar+Restaurant", use_container_width=True)
    st.write("Select 'Customer View' to view the menu.")

# ---------------- CUSTOMER VIEW ----------------
elif choice == "Customer View":
    st.header("📱 Customer Menu")

    # Get the current time and decide the menu section
    current_time = datetime.now().hour
    menu_section = ""

    # Debugging the current hour
    st.write(f"Current hour: {current_time}")  # Debugging line

    if 7 <= current_time < 11:
        menu_section = "Breakfast"
    elif 12 <= current_time < 16:
        menu_section = "Lunch"
    elif 17 <= current_time < 22:
        menu_section = "Dinner"
    else:
        st.warning("🚫 The restaurant is closed. Please come back during operational hours.")
        st.stop()

    st.write(f"🍽️ **{menu_section} Menu** (Available from {7 if menu_section == 'Breakfast' else 12 if menu_section == 'Lunch' else 17} - {11 if menu_section == 'Breakfast' else 16 if menu_section == 'Lunch' else 22} hrs)")

    # Fetch the menu items for the specific time slot (Breakfast, Lunch, Dinner)
    items = get_menu_items(respect_time=True)  # Ensure respect_time is True to filter by the current meal category

    # Debugging to check fetched items
    st.write(f"Fetched {len(items)} items for the current time.")  # More accurate debug message

    selected_items = []

    if items:
        for item in items:
            st.image(item['image_url'], width=100, use_container_width=False) # explicitly set to False or remove
            if st.checkbox(f"{item['name']} - ₹{item['price']}", key=f"{item['id']}"):
                selected_items.append(item)
    else:
        st.warning("No menu items available at this time.")

    special_instructions = st.text_area("Special Instructions")

    if st.button("Place Order"):
        if selected_items:
            place_order(table_id="CustomerTable", items=selected_items, instructions=special_instructions)
            st.success("✅ Order placed!")
        else:
            st.warning("Please select at least one item to order.")

# ---------------- ADMIN PANEL ----------------
elif choice == "Admin Panel":
    if login_admin():
        st.success("✅ Logged in as Admin")

        # Admin's Restaurant Dashboard
        st.header("Restaurant Dashboard")

        # Fetch and manage orders
        orders = get_orders(status="Pending")

        if not orders:
            st.info("No orders yet.")
        else:
            for order in orders:
                with st.expander(f"Order #{order['id']} | Table {order['table_id']}"):
                    st.markdown(f"**Items**: {order['items']}")
                    st.markdown(f"**Instructions**: {order['instructions']}")
                    st.markdown(f"**Status**: {order['status']}")
                    st.markdown(f"**Time**: {order['timestamp']}")

                    if st.button("Mark as Served", key=f"serve_{order['id']}"):
                        update_order_status(order['id'], "Served")
                        st.success(f"✅ Order #{order['id']} marked as Served")

        # Manage menu items (Add new items or update status)
        st.subheader("Manage Menu Items")

        # Add Menu Item
        name = st.text_input("Item Name")
        price = st.number_input("Price (₹)", min_value=0.0)
        image_url = st.text_input("Image URL")
        category = st.selectbox("Category", ["Breakfast", "Lunch", "Dinner"])
        status = st.selectbox("Status", ["Available", "Out of Stock"])

        if st.button("Add Menu Item"):
            if name and image_url:
                add_menu_item(name, price, image_url, category, status)
                st.success(f"✅ '{name}' added to {category} menu.")
            else:
                st.error("Please provide name and image URL.")

        # Update Item Status
        st.subheader("🔄 Update Menu Item Status")
        item_id = st.number_input("Item ID", min_value=1, step=1)
        new_status = st.selectbox("New Status", ["Available", "Out of Stock"])

        if st.button("Update Status"):
            update_menu_item_status(item_id, new_status)
            st.success(f"✅ Item #{item_id} status updated to {new_status}.")

        # Generate QR Code for tables
        st.subheader("📎 Generate QR Code for Table")
        qr_table_id = st.text_input("Enter Table ID to generate QR Code")
        if st.button("Generate QR Code"):
            if qr_table_id.strip():
                qr_image_path = generate_qr(qr_table_id, show_in_streamlit=False)
                st.image(qr_image_path, caption=f"QR Code for Table {qr_table_id}", use_container_width=True)
                st.success("✅ QR Code generated successfully!")
            else:
                st.error("Please enter a valid Table ID.")