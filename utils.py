import qrcode
import os
import streamlit as st
from PIL import Image

# Replace with your Streamlit Cloud app URL
APP_BASE_URL = "https://qr-menu-app-ngt9iyrw92m3rknxc85nqm.streamlit.app"

def generate_qr(table_id, show_in_streamlit=True):
    """
    Generate and optionally display a QR code for the given table ID.

    Args:
        table_id (str): The table identifier.
        show_in_streamlit (bool): Whether to display the QR code in the Streamlit app.

    Returns:
        str: Path to the saved QR code image.
    """
    # Construct the URL to encode, including the table_id as a query parameter
    url = f"{APP_BASE_URL}/?table_id={table_id}"

    # Generate the QR code
    qr_img = qrcode.make(url)

    # Ensure the directory exists for storing QR codes
    os.makedirs("qr_codes", exist_ok=True)
    file_path = os.path.join("qr_codes", f"{table_id}.png")
    qr_img.save(file_path)

    # Optionally display in Streamlit
    if show_in_streamlit:
        st.image(Image.open(file_path), caption=f"Scan to Order at Table {table_id}", use_container_width=True)
        st.code(url, language="markdown")

    return file_path  # Return path so it can be reused (e.g., in Admin panel)
