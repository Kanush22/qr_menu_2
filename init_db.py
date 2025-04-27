import sqlite3

DB_NAME = "menu.db"

# Menu items categorized by meal types (Breakfast, Lunch, Dinner)
menu_items = [
    # Breakfast Items
    ("Breakfast", "Masala Dosa", 50, "https://i.imgur.com/z9b1ulR.jpg", "Available"),
    ("Breakfast", "Idli Vada Sambar", 40, "https://i.imgur.com/xsOvSBZ.jpg", "Available"),
    ("Breakfast", "Upma", 30, "https://i.imgur.com/DqOcHzo.jpg", "Available"),
    ("Breakfast", "Medu Vada", 35, "https://i.imgur.com/YvRaEzV.jpg", "Available"),
    ("Breakfast", "Pongal", 45, "https://i.imgur.com/j2CcoBt.jpg", "Available"),
    ("Breakfast", "Rava Kesari", 25, "https://i.imgur.com/xK9HOVF.jpg", "Available"),
    ("Breakfast", "Poori Kurma", 50, "https://i.imgur.com/PEQ5r5N.jpg", "Available"),
    ("Breakfast", "Uttapam", 40, "https://i.imgur.com/MzN7cWS.jpg", "Available"),

    # Lunch Items
    ("Lunch", "Vegetable Biryani", 80, "https://i.imgur.com/zUrr0Pi.jpg", "Available"),
    ("Lunch", "Paneer Butter Masala", 90, "https://i.imgur.com/WpS6Y5L.jpg", "Available"),
    ("Lunch", "Chole Bhature", 75, "https://i.imgur.com/J67G7bq.jpg", "Available"),
    ("Lunch", "Dal Tadka", 60, "https://i.imgur.com/zvHRh6T.jpg", "Available"),
    ("Lunch", "Aloo Paratha", 50, "https://i.imgur.com/M61r4nT.jpg", "Available"),

    # Dinner Items
    ("Dinner", "Paneer Tikka", 120, "https://i.imgur.com/jzUlGQo.jpg", "Available"),
    ("Dinner", "Tandoori Roti", 30, "https://i.imgur.com/hOtcjZh.jpg", "Available"),
    ("Dinner", "Butter Naan", 35, "https://i.imgur.com/TLNNu6I.jpg", "Available"),
    ("Dinner", "Mushroom Masala", 100, "https://i.imgur.com/RoJhAN0.jpg", "Available"),
    ("Dinner", "Pasta Alfredo", 150, "https://i.imgur.com/lZpgyke.jpg", "Available")
]

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
    status TEXT DEFAULT 'Received',
    timestamp TEXT
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'staff'))
);
"""

def initialize_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Ensure the 'menu' table exists before altering it
    c.execute('''CREATE TABLE IF NOT EXISTS menu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        image_url TEXT,
        available INTEGER DEFAULT 1
    )''')

    # Ensure the 'available' column exists in the 'menu' table
    c.execute('PRAGMA table_info(menu)')
    columns = [column[1] for column in c.fetchall()]
    if 'available' not in columns:
        c.execute('ALTER TABLE menu ADD COLUMN available INTEGER DEFAULT 1')
        print("✅ Added 'available' column to 'menu' table.")

    # Create orders table if not exists
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_id TEXT,
        items TEXT,
        instructions TEXT,
        status TEXT DEFAULT 'Received',
        timestamp TEXT
    )''')

    # Insert or update predefined menu items
    for item in menu_items:
        category, name, price, image_url, available = item
        
        # Check if the item already exists in the menu
        c.execute('SELECT id, price, available FROM menu WHERE name = ? AND category = ?', (name, category))
        existing_item = c.fetchone()
        
        if not existing_item:
            # If the item does not exist, insert it
            c.execute('INSERT INTO menu (category, name, price, image_url, available) VALUES (?, ?, ?, ?, ?)', item)
            print(f"✅ Added '{name}' to {category} menu.")
        else:
            # If the item exists, update the price and availability
            c.execute('UPDATE menu SET price = ?, available = ? WHERE id = ?', (price, available, existing_item[0]))
            print(f"✅ Updated '{name}' in {category} menu.")

    # Commit changes and close the connection
    conn.commit()
    conn.close()
