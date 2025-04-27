import sqlite3
import streamlit as st

DB_PATH = "menu.db"

def authenticate_user(username, password):
    """
    Authenticate a user from the database.
    Returns user details (username, role) if valid, else None.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT username, role FROM users WHERE username=? AND password=?", (username, password))
    user = cur.fetchone()
    conn.close()
    return user

def login_panel():
    """
    Unified login panel. Supports admin or staff login.
    Stores session state if authenticated.
    """
    st.subheader("🔐 Admin / Staff Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = authenticate_user(username, password)
        if user:
            st.success(f"✅ Logged in as {user[0]} ({user[1]})")
            st.session_state['user'] = user[0]
            st.session_state['role'] = user[1]
            return True
        else:
            st.error("❌ Invalid credentials")
            return False
    return False

def login_admin():
    """
    Shortcut for checking if the current session user is admin.
    """
    if 'role' in st.session_state and st.session_state['role'] == 'admin':
        return True
    else:
        return login_panel()
