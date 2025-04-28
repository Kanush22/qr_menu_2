import streamlit as st
from utils import generate_qr
from database import get_menu_items, place_order, get_orders, update_order_status, add_menu_item, update_menu_item_status, initialize_db
from auth import login_admin
from datetime import datetime
import pytz

# Initialize database
initialize_db()

# Streamlit page config
st.set_page_config(page_title="Ruchi Adda Restaurant - QR Menu App", layout="wide")

# Navigation menu
menu = ["Homepage", "Customer View", "Admin Panel"]

# Initialize session state for 'choice'
if "choice" not in st.session_state:
    st.session_state.choice = menu[0]

# Sidebar navigation
choice = st.sidebar.selectbox("Navigate", menu, index=menu.index(st.session_state.choice))
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
    now = datetime.now(local_timezone)
    formatted_time = now.strftime("%I:%M %p")

    # Display time
    st.markdown(f"### 🕒 Current Time: **{formatted_time}**")

    # Restaurant timings
    st.markdown("""
    ### 🍽️ Restaurant Timings:
    - **Breakfast**: 07:00 AM — 11:00 AM
    - **Lunch**: 12:00 PM — 04:00 PM
    - **Dinner**: 05:00 PM — 10:00 PM
    """)

    # Determine current menu section
    current_hour = now.hour
    menu_section = None
    if 7 <= current_hour < 11:
        menu_section = "Breakfast"
    elif 12 <= current_hour < 16:
        menu_section = "Lunch"
    elif 17 <= current_hour < 22:
        menu_section = "Dinner"
    else:
        st.warning("🚫 The restaurant is currently closed. Please visit during operating hours!")
        st.stop()

    st.success(f"✅ Now Serving: **{menu_section}** Menu")
    st.write(f"**DEBUG - Menu Section:** {menu_section}")  # DEBUG

    # Fetch all menu items
    all_items = get_menu_items()
    st.write(f"**DEBUG - All Items Fetched:** {all_items}")  # DEBUG

    # Filter items for the current time and availability
    available_items = []
    if all_items:
        for item in all_items:
            st.write(f"**DEBUG - Item Category:** {item.get('category')}, **Available:** {item.get('available')}") # DEBUG - Corrected key to 'available'
            if item.get('category') == menu_section and item.get('available') == 1: # Corrected check to 'available' == 1
                available_items.append(item)

    st.write(f"**DEBUG - Available Items (after filter):** {available_items}")  # DEBUG

    selected_items = []

    if available_items:
        st.subheader("📝 Select Items to Order:")
        for item in available_items:
            with st.container():
                st.image(item.get('image_url', 'https://via.placeholder.com/150'), width=120)
                if st.checkbox(f"{item.get('name', 'Unnamed Item')} - ₹{item.get('price', 0)}", key=f"item_{item.get('id')}"):
                    selected_items.append(item)
    else:
        st.warning(f"No **{menu_section}** items available right now.")
        st.info("Admins: Please add menu items under 'Admin Panel'!")

    st.markdown("---")

    # Table number input
    table_id = st.text_input("Enter Your Table Number", placeholder="Eg: T1, T2...")

    # Special instructions
    special_instructions = st.text_area("Special Instructions (optional)")

    if st.button("Place Order"):
        if not table_id.strip():
            st.error("⚠️ Please enter your Table Number.")
        elif not selected_items:
            st.error("⚠️ Please select at least one item to order.")
        else:
            place_order(table_id=table_id.strip(), items=selected_items, instructions=special_instructions)
            st.success(f"✅ Order placed successfully from **Table {table_id.strip()}**!")

# ---------------- ADMIN PANEL ----------------
elif choice == "Admin Panel":
    if login_admin():
        st.success("✅ Logged in as Admin")

        st.header("🍴 Restaurant Dashboard")

        # Orders
        st.subheader("📦 Pending Orders")
        pending_orders = get_orders(status="Pending")

        if pending_orders:
            for order in pending_orders:
                with st.expander(f"Order #{order.get('id')} | Table {order.get('table_id')}"):
                    st.markdown(f"**Items**: {order.get('items')}")
                    st.markdown(f"**Instructions**: {order.get('instructions')}")
                    st.markdown(f"**Status**: {order.get('status')}")
                    st.markdown(f"**Time**: {order.get('timestamp')}")

                    if st.button("Mark as Served", key=f"serve_{order.get('id')}"):
                        update_order_status(order['id'], "Served")
                        st.success(f"✅ Order #{order.get('id')} marked as Served!")
        else:
            st.info("No pending orders.")

        st.markdown("---")

        # Add menu item
        st.subheader("➕ Add New Menu Item")
        name = st.text_input("Item Name")
        price = st.number_input("Price (₹)", min_value=1.0, step=1.0)
        image_url = st.text_input("Image URL")
        category = st.selectbox("Category", ["Breakfast", "Lunch", "Dinner"])
        status = st.selectbox("Status", ["Available", "Out of Stock"])

        if st.button("Add Menu Item"):
            if name and image_url:
                add_menu_item(name=name, price=price, image_url=image_url, category=category, status=status)
                st.success(f"✅ '{name}' added successfully!")
            else:
                st.error("⚠️ Please provide both Name and Image URL.")

        st.markdown("---")

        # Update item status
        st.subheader("🔄 Update Menu Item Status")
        item_id = st.number_input("Item ID", min_value=1, step=1)
        new_status = st.selectbox("New Status for Item", ["Available", "Out of Stock"])

        if st.button("Update Item Status"):
            update_menu_item_status(item_id=item_id, new_status=new_status)
            st.success(f"✅ Item ID {item_id} updated to {new_status}.")