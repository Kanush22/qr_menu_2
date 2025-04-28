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
    local_timezone = pytz.timezone('Asia/Kolkata')

    # Get the current time
    now = datetime.now(local_timezone)
    current_hour = now.hour
    formatted_time = now.strftime("%I:%M %p")  # 12-hour format

    st.markdown(f"### 🕒 Current Time: **{formatted_time}**")

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

    st.success(f"✅ Now Serving: **{menu_section}** Menu")

    # Fetch all menu items
    all_items = get_menu_items(respect_time=False)

    # Handle missing keys safely
    items = [
        item for item in all_items
        if item.get('category') == menu_section and item.get('status') == 'Available'
    ]

    selected_items = []

    if items:
        for item in items:
            st.image(item.get('image_url', 'https://via.placeholder.com/100'), width=100, use_container_width=False)
            if st.checkbox(f"{item.get('name', 'Unknown Item')} - ₹{item.get('price', 0)}", key=f"{item.get('id', 'unknown')}"):
                selected_items.append(item)
    else:
        st.warning(f"No **{menu_section}** items available currently. Please check back later!")

    st.markdown("---")

    # NEW: Customer Table Input
    table_id = st.text_input("Enter Your Table Number", placeholder="e.g., T5 or Table 7")

    special_instructions = st.text_area("Special Instructions (Optional)")

    if st.button("Place Order"):
        if not table_id.strip():
            st.error("⚠️ Please enter your Table Number before placing an order.")
        elif selected_items:
            place_order(table_id=table_id.strip(), items=selected_items, instructions=special_instructions)
            st.success(f"✅ Order placed successfully from **Table {table_id.strip()}**!")
        else:
            st.warning("⚠️ Please select at least one item to order.")

# ---------------- ADMIN PANEL ----------------
elif choice == "Admin Panel":
    if login_admin():
        st.success("✅ Logged in as Admin")

        st.header("Restaurant Dashboard")

        # Fetch orders
        orders = get_orders(status="Pending")

        if not orders:
            st.info("No pending orders yet.")
        else:
            for order in orders:
                with st.expander(f"Order #{order.get('id', 'Unknown')} | Table {order.get('table_id', 'Unknown')}"):
                    st.markdown(f"**Items**: {order.get('items', 'No items')}")
                    st.markdown(f"**Instructions**: {order.get('instructions', 'No instructions')}")
                    st.markdown(f"**Status**: {order.get('status', 'Unknown')}")
                    st.markdown(f"**Time**: {order.get('timestamp', 'Unknown time')}")

                    if st.button("Mark as Served", key=f"serve_{order.get('id', '')}"):
                        update_order_status(order['id'], "Served")
                        st.success(f"✅ Order #{order.get('id', '')} marked as Served")

        st.markdown("---")

        # Manage Menu Items
        st.subheader("Manage Menu Items")

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
