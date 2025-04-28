import streamlit as st
from utils import generate_qr  # Only import generate_qr here
from database import get_menu_items, place_order, get_orders, update_order_status, add_menu_item, update_menu_item_status, initialize_db
from auth import login_admin
from datetime import datetime
import pytz  # Import timezone

# Initialize database
initialize_db()

# Streamlit page config
st.set_page_config(page_title="Ruchi Adda Restaurant - QR Menu App", layout="wide")

# Navigation menu
menu = ["Homepage", "Customer View", "Admin Panel"]

# Initialize session state for 'choice' if not already initialized
if "choice" not in st.session_state:
    st.session_state.choice = menu[0]  # Set default to the first menu option

# Sidebar navigation
choice = st.sidebar.selectbox("Navigate", menu, index=menu.index(st.session_state.choice))

# Update session state when the choice is changed
st.session_state.choice = choice

# ---------------- HOMEPAGE ----------------
if choice == "Homepage":
    st.title("Welcome to Ruchi Adda Restaurant")
    st.subheader("A delightful experience with our delicious meals")
    st.image("https://via.placeholder.com/800x400.png?text=Ruchi+Adda+Restaurant", use_container_width=True)
    st.write("Select 'Customer View' to view the menu.")

# ---------------- CUSTOMER VIEW ----------------
elif choice == "Customer View":
    st.header("📱 Customer Menu")

    # Set timezone
    local_timezone = pytz.timezone('Asia/Kolkata')  # Indian time

    # Get the current time in local timezone
    now = datetime.now(local_timezone)
    current_hour = now.hour
    formatted_time = now.strftime("%I:%M %p")  # 12-hour format

    # Display Current Time
    st.markdown(f"### 🕒 Current Time: **{formatted_time}**")

    # Display Restaurant Timings
    st.markdown("""
    ### 🍽️ Restaurant Timings:
    - **Breakfast**: 07:00 AM — 11:00 AM
    - **Lunch**: 12:00 PM — 04:00 PM
    - **Dinner**: 05:00 PM — 10:00 PM
    """)

    menu_section = ""

    if 7 <= current_hour < 11:
        menu_section = "Breakfast"
    elif 12 <= current_hour < 16:
        menu_section = "Lunch"
    elif 17 <= current_hour < 22:
        menu_section = "Dinner"
    else:
        st.warning("🚫 The restaurant is closed. Please come back during operational hours.")
        st.stop()

    # Inform about available Menu
    st.success(f"✅ Now Serving: **{menu_section}** Menu")

    # Fetch the menu items
    all_items = get_menu_items(respect_time=False)  # Fetch all items
    items = [item for item in all_items if item['category'] == menu_section and item['status'] == 'Available']

    selected_items = []

    if items:
        for item in items:
            st.image(item['image_url'], width=100, use_container_width=False)
            if st.checkbox(f"{item['name']} - ₹{item['price']}", key=f"{item['id']}"):
                selected_items.append(item)
    else:
        st.warning(f"No **{menu_section}** items available currently. Please check back later!")

    special_instructions = st.text_area("Special Instructions")

    if st.button("Place Order"):
        if selected_items:
            place_order(table_id="CustomerTable", items=selected_items, instructions=special_instructions)
            st.success("✅ Order placed successfully!")
        else:
            st.warning("⚠️ Please select at least one item to order.")

# ---------------- ADMIN PANEL ----------------
elif choice == "Admin Panel":
    if login_admin():
        st.success("✅ Logged in as Admin")

        # Admin's Restaurant Dashboard
        st.header("Restaurant Dashboard")

        # Fetch and manage orders
        orders = get_orders(status="Pending")

        if not orders:
            st.info("No pending orders yet.")
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
                st.error("⚠️ Please provide both Item Name and Image URL.")

        # Update Item Status
        st.subheader("🔄 Update Menu Item Status")
        item_id = st.number_input("Item ID", min_value=1, step=1)
        new_status = st.selectbox("New Status", ["Available", "Out of Stock"])

        if st.button("Update Status"):
            update_menu_item_status(item_id, new_status)
            st.success(f"✅ Item #{item_id} status updated to {new_status}.")
