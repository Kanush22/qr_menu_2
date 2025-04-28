import sqlite3
from datetime import datetime, time
from typing import List, Optional, Dict, Any
import pytz

# ---------------- CONSTANTS ----------------
DB_NAME = "menu.db"
TIMEZONE = "Asia/Kolkata"

# ---------------- HELPER FUNCTIONS ----------------
def fetch_all(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Execute a SELECT query and return a list of dictionary rows."""
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute(query, params)]

def execute_query(query: str, params: tuple = ()) -> None:
    """Execute a query that modifies data."""
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(query, params)
        conn.commit()

# ---------------- TIME-BASED CATEGORY DETERMINATION ----------------
def get_current_meal_category() -> Optional[str]:
    """Determine the current meal category based on time of day."""
    now_utc = datetime.now(pytz.utc)
    current_time = now_utc.astimezone(pytz.timezone(TIMEZONE)).time()

    restaurant_timings = get_restaurant_timings()
    meal_timings = get_meal_timings()

    try:
        open_time = datetime.strptime(restaurant_timings.get('open_time', '07:00 AM'), '%I:%M %p').time()
        close_time = datetime.strptime(restaurant_timings.get('close_time', '10:00 PM'), '%I:%M %p').time()
    except ValueError:
        print("⚠️ Error parsing restaurant open/close times. Defaulting to 7:00 AM - 10:00 PM.")
        open_time, close_time = time(7, 0), time(22, 0)

    if current_time < open_time or current_time >= close_time:
        return None

    try:
        breakfast_start = datetime.strptime(meal_timings.get('breakfast_start', '07:00 AM'), '%I:%M %p').time()
        breakfast_end = datetime.strptime(meal_timings.get('breakfast_end', '11:30 AM'), '%I:%M %p').time()
        lunch_start = datetime.strptime(meal_timings.get('lunch_start', '11:30 AM'), '%I:%M %p').time()
        lunch_end = datetime.strptime(meal_timings.get('lunch_end', '04:00 PM'), '%I:%M %p').time()
        dinner_start = datetime.strptime(meal_timings.get('dinner_start', '04:00 PM'), '%I:%M %p').time()
        dinner_end = datetime.strptime(meal_timings.get('dinner_end', '10:00 PM'), '%I:%M %p').time()
    except ValueError:
        print("⚠️ Error parsing meal timings. Defaulting to standard periods.")
        breakfast_start, breakfast_end = time(7, 0), time(11, 30)
        lunch_start, lunch_end = time(11, 30), time(16, 0)
        dinner_start, dinner_end = time(16, 0), time(22, 0)

    if breakfast_start <= current_time < breakfast_end:
        return "Breakfast"
    elif lunch_start <= current_time < lunch_end:
        return "Lunch"
    elif dinner_start <= current_time < dinner_end:
        return "Dinner"
    return None

# ---------------- MENU MANAGEMENT ----------------
def get_menu_items(respect_time: bool = True) -> List[Dict[str, Any]]:
    """Fetch menu items based on the current meal time."""
    category = get_current_meal_category() if respect_time else None
    if respect_time and not category:
        print("Restaurant is currently closed.")
        return []

    query = "SELECT * FROM menu WHERE available = 1"
    params = ()
    if category:
        query += " AND category = ?"
        params = (category,)

    menu_items = fetch_all(query, params)
    print(f"Fetched {len(menu_items)} menu items{' for ' + category if category else ''}.")
    return menu_items

def add_menu_item(name: str, price: float, image_url: str, category: str, status: str, description: str = "") -> None:
    """Add a new menu item."""
    available = 1 if status == "Available" else 0
    execute_query(
        "INSERT INTO menu (category, name, description, price, image_url, available) VALUES (?, ?, ?, ?, ?, ?)",
        (category, name, description, price, image_url, available),
    )

def update_menu_item_status(item_id: int, new_status: str) -> None:
    """Update the availability of a menu item."""
    available = 1 if new_status == "Available" else 0
    execute_query("UPDATE menu SET available = ? WHERE id = ?", (available, item_id))

# ---------------- ORDER MANAGEMENT ----------------
def place_order(table_id: str, items: List[Dict[str, Any]], instructions: str) -> None:
    """Place a new customer order."""
    item_names = ", ".join([item['name'] for item in items])
    now_utc = datetime.now(pytz.utc)
    timestamp = now_utc.astimezone(pytz.timezone(TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S")

    execute_query(
        "INSERT INTO orders (table_id, items, instructions, status, timestamp) VALUES (?, ?, ?, ?, ?)",
        (table_id, item_names, instructions, "Pending", timestamp),
    )

def get_orders(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch all orders, optionally filtered by status."""
    query = "SELECT * FROM orders"
    params = ()
    if status:
        query += " WHERE status = ?"
        params = (status,)
    query += " ORDER BY timestamp DESC"
    return fetch_all(query, params)

def update_order_status(order_id: int, new_status: str) -> None:
    """Update the status of an order."""
    execute_query("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))

# ---------------- TIMING MANAGEMENT ----------------
def get_restaurant_timings() -> Dict[str, Any]:
    """Fetch restaurant open/close timings."""
    timings = fetch_all("SELECT * FROM timings WHERE id = 1")
    return timings[0] if timings else {}

def update_restaurant_timings(open_time: str, close_time: str) -> None:
    """Update restaurant open/close timings."""
    execute_query(
        "UPDATE timings SET open_time = ?, close_time = ? WHERE id = 1",
        (open_time, close_time),
    )

def get_meal_timings() -> Dict[str, Any]:
    """Fetch meal time periods."""
    timings = fetch_all("SELECT * FROM meal_timings WHERE id = 1")
    return timings[0] if timings else {}

def update_meal_timings(
    breakfast_start: str, breakfast_end: str,
    lunch_start: str, lunch_end: str,
    dinner_start: str, dinner_end: str,
) -> None:
    """Update meal timings."""
    execute_query(
        """UPDATE meal_timings SET
            breakfast_start = ?, breakfast_end = ?,
            lunch_start = ?, lunch_end = ?,
            dinner_start = ?, dinner_end = ?
            WHERE id = 1""",
        (breakfast_start, breakfast_end, lunch_start, lunch_end, dinner_start, dinner_end),
    )

# ---------------- DATABASE INITIALIZATION ----------------
def initialize_db() -> None:
    """Initialize database and seed with default values."""
    schema = """
    CREATE TABLE IF NOT EXISTS menu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        image_url TEXT,
        available INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_id TEXT NOT NULL,
        items TEXT NOT NULL,
        instructions TEXT,
        status TEXT DEFAULT 'Pending',
        timestamp TEXT
    );
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'staff'))
    );
    CREATE TABLE IF NOT EXISTS timings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        open_time TEXT NOT NULL,
        close_time TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS meal_timings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        breakfast_start TEXT NOT NULL,
        breakfast_end TEXT NOT NULL,
        lunch_start TEXT NOT NULL,
        lunch_end TEXT NOT NULL,
        dinner_start TEXT NOT NULL,
        dinner_end TEXT NOT NULL
    );
    """

    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.executescript(schema)

        # Set default open time to 7:00 AM
        if not fetch_all("SELECT * FROM timings WHERE id = 1"):
            c.execute("INSERT INTO timings (open_time, close_time) VALUES (?, ?)", ('07:00 AM', '10:00 PM'))
        else:
            c.execute("UPDATE timings SET open_time = ? WHERE id = 1", ('07:00 AM',))

        # Set default breakfast start time to 7:00 AM
        if not fetch_all("SELECT * FROM meal_timings WHERE id = 1"):
            c.execute(
                """INSERT INTO meal_timings
                    (breakfast_start, breakfast_end, lunch_start, lunch_end, dinner_start, dinner_end)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                ('07:00 AM', '11:30 AM', '11:30 AM', '04:00 PM', '04:00 PM', '10:00 PM')
            )
        else:
            c.execute("UPDATE meal_timings SET breakfast_start = ? WHERE id = 1", ('07:00 AM',))

        if not fetch_all("SELECT * FROM users WHERE username = 'admin'"):
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('admin', '1234', 'admin'))

        if not fetch_all("SELECT * FROM menu LIMIT 1"):
            seed_menu_items(c)

        conn.commit()
    print("✅ Database initialized.")

def seed_menu_items(c: sqlite3.Cursor) -> None:
    """Insert default menu items if menu table is empty."""
    menu_items = [
        ("Breakfast", "Masala Dosa", "", 50, "https://i.imgur.com/z9b1ulR.jpg", "Available"),
        ("Breakfast", "Idli Vada Sambar", "", 40, "https://i.imgur.com/xsOvSBZ.jpg", "Available"),
        ("Breakfast", "Upma", "", 30, "https://i.imgur.com/DqOcHzo.jpg", "Available"),
        ("Breakfast", "Medu Vada", "", 35, "https://i.imgur.com/YvRaEzV.jpg", "Available"),
        ("Breakfast", "Pongal", "", 45, "https://i.imgur.com/j2CcoBt.jpg", "Available"),
        ("Breakfast", "Rava Kesari", "", 25, "https://i.imgur.com/xK9HOVF.jpg", "Available"),
        ("Breakfast", "Poori Kurma", "", 50, "https://i.imgur.com/PEQ5r5N.jpg", "Available"),
        ("Breakfast", "Uttapam", "", 40, "https://i.imgur.com/MzN7cWS.jpg", "Available"),
        ("Lunch", "Vegetable Biryani", "", 80, "https://i.imgur.com/zUrr0Pi.jpg", "Available"),
        ("Lunch", "Paneer Butter Masala", "", 90, "https://i.imgur.com/WpS6Y5L.jpg", "Available"),
        ("Lunch", "Chole Bhature", "", 75, "https://i.imgur.com/J67G7bq.jpg", "Available"),
        ("Lunch", "Dal Tadka", "", 60, "https://i.imgur.com/zvHRh6T.jpg", "Available"),
        ("Lunch", "Aloo Paratha", "", 50, "https://i.imgur.com/M61r4nT.jpg", "Available"),
        ("Dinner", "Paneer Tikka", "", 120, "https://i.imgur.com/jzUlGQo.jpg", "Available"),
        ("Dinner", "Tandoori Roti", "", 30, "https://i.imgur.com/hOtcjZh.jpg", "Available"),
        ("Dinner", "Butter Naan", "", 35, "https://i.imgur.com/TLNNu6I.jpg", "Available"),
        ("Dinner", "Mushroom Masala", "", 100, "https://i.imgur.com/RoJhAN0.jpg", "Available"),
        ("Dinner", "Pasta Alfredo", "", 150, "https://i.imgur.com/lZpgyke.jpg", "Available"),
    ]

    for category, name, description, price, image_url, status in menu_items:
        available = 1 if status == "Available" else 0
        c.execute(
            "INSERT INTO menu (category, name, description, price, image_url, available) VALUES (?, ?, ?, ?, ?, ?)",
            (category, name, description, price, image_url, available)
        )
    print("✅ Seed menu items added.")


# ---------------- MAIN ----------------
if __name__ == "__main__":
    initialize_db()

    print("\n-- Available Menu Items at Current Time --")
    current_category = get_current_meal_category()
    now = datetime.now(pytz.timezone(TIMEZONE)).strftime('%I:%M %p')
    print(f"Current time ({TIMEZONE}): {now}, Category: {current_category or 'Closed'}")

    if current_category:
        items = get_menu_items()
        for item in items:
            print(f"- {item['name']} | ₹{item['price']}")
    else:
        print("Restaurant is currently closed.")