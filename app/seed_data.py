import sqlite3
from pathlib import Path

# Define the project root and the path to the database file
ROOT_DIR = Path(__file__).resolve().parent.parent
DB_FILE = ROOT_DIR / 'sneakers.db'

def seed_data():
    """
    Connects to the SQLite database and populates dummy data for all existing categories.
    """
    if not DB_FILE.exists():
        print(f"Error: Database file not found at {DB_FILE}")
        print("Please run the 'init_db.py' script first.")
        return

    # Sample data definitions
    SAMPLES = {
        'sneaker': [
            {'brand': 'Nike', 'sil': 'Air Jordan 1', 'rel': 'Chicago Lost & Found', 'sku': 'DZ5485-612', 'year': 2022, 'size': 10.5, 'cond': 'New', 'price': 180.00},
            {'brand': 'Adidas', 'sil': 'Yeezy Boost 350', 'rel': 'Turtle Dove', 'sku': 'AQ4832', 'year': 2015, 'size': 10.0, 'cond': 'Used', 'price': 250.00},
            {'brand': 'New Balance', 'sil': '990v3', 'rel': 'Teddy Santis Marblehead', 'sku': 'M990TG3', 'year': 2022, 'size': 11.0, 'cond': 'New', 'price': 210.00}
        ],
        'vinyl': [
            {'brand': 'Pink Floyd', 'sil': 'Dark Side of the Moon', 'genre': 'Rock', 'rel': '1973 UK Pressing', 'sku': 'SHVL 804', 'year': 1973, 'size': None, 'cond': 'Good', 'price': 45.00},
            {'brand': 'Kendrick Lamar', 'sil': 'DAMN.', 'genre': 'Hip Hop', 'rel': 'Collector Edition Clear Vinyl', 'sku': 'B0716861', 'year': 2017, 'size': None, 'cond': 'New', 'price': 35.00},
            {'brand': 'Miles Davis', 'sil': 'Kind of Blue', 'genre': 'Jazz', 'rel': 'Mobile Fidelity Sound Lab', 'sku': 'MFSL 2-45011', 'year': 2015, 'size': None, 'cond': 'New', 'price': 60.00}
        ],
        'book': [
            {'brand': 'J.R.R. Tolkien', 'sil': 'The Hobbit', 'genre': 'Fantasy', 'rel': '75th Anniversary Edition', 'sku': '978-0547928227', 'year': 2012, 'size': 1.0, 'cond': 'New', 'price': 15.00},
            {'brand': 'Frank Herbert', 'sil': 'Dune', 'genre': 'Sci-Fi', 'rel': 'Deluxe Edition', 'sku': '978-0441013593', 'year': 2019, 'size': 1.0, 'cond': 'New', 'price': 25.00}
        ],
        'default': [
            {'brand': 'Generic Brand', 'sil': 'Generic Model', 'genre': 'Miscellaneous', 'rel': 'Standard Issue', 'sku': '000', 'year': 2023, 'size': 1.0, 'cond': 'New', 'price': 10.00}
        ]
    }

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Get all categories
        cursor.execute("SELECT id, name FROM Categories")
        categories = cursor.fetchall()

        if not categories:
            print("No categories found. Please create a category first (or run init_db.py).")
            return

        print(f"Found {len(categories)} categories. Populating data...")

        for cat_id, cat_name in categories:
            # Determine which sample set to use based on category name
            cat_key = 'default'
            for key in SAMPLES:
                if key in cat_name.lower():
                    cat_key = key
                    break
            
            items_to_insert = SAMPLES[cat_key]
            print(f"  -> Populating '{cat_name}' with {len(items_to_insert)} items (Type: {cat_key})")

            for item in items_to_insert:
                # 1. Ensure Brand exists
                cursor.execute("SELECT id FROM Brands WHERE name = ? AND category_id = ?", (item['brand'], cat_id))
                row = cursor.fetchone()
                if row:
                    brand_id = row[0]
                else:
                    cursor.execute("INSERT INTO Brands (name, category_id) VALUES (?, ?)", (item['brand'], cat_id))
                    brand_id = cursor.lastrowid

                # 2. Ensure Silhouette exists
                cursor.execute("SELECT id FROM Silhouettes WHERE name = ? AND brand_id = ?", (item['sil'], brand_id))
                row = cursor.fetchone()
                if row:
                    sil_id = row[0]
                else:
                    cursor.execute("INSERT INTO Silhouettes (name, brand_id, genre) VALUES (?, ?, ?)", (item['sil'], brand_id, item.get('genre')))
                    sil_id = cursor.lastrowid

                # 3. Ensure Release exists
                cursor.execute("SELECT id FROM Releases WHERE name = ? AND silhouette_id = ?", (item['rel'], sil_id))
                row = cursor.fetchone()
                if row:
                    rel_id = row[0]
                else:
                    cursor.execute("INSERT INTO Releases (name, silhouette_id, sku, release_year) VALUES (?, ?, ?, ?)", 
                                   (item['rel'], sil_id, item['sku'], item['year']))
                    rel_id = cursor.lastrowid

                # 4. Insert Inventory Item (Always insert a new item)
                cursor.execute(
                    "INSERT INTO Inventory (release_id, size, condition, purchase_price, status) VALUES (?, ?, ?, ?, ?)",
                    (rel_id, item['size'], item['cond'], item['price'], 'In Stock')
                )

        conn.commit()
        print("\nDummy data population complete!")

    except sqlite3.Error as e:
        print(f"An error occurred with the database: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == '__main__':
    seed_data()
