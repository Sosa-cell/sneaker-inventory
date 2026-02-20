import sqlite3
from pathlib import Path

# Define the project root and the path to the database file
ROOT_DIR = Path(__file__).resolve().parent.parent
DB_FILE = ROOT_DIR / 'sneakers.db'

def get_or_create_record(cursor, table, columns, values):
    """
    Generic function to get a record's ID if it exists, or create it and return the new ID.
    `columns` and `values` should be tuples.
    Example: get_or_create_record(cursor, 'Brands', ('name',), ('Nike',))
    """
    where_clause = " AND ".join([f"{col} = ?" for col in columns])
    cursor.execute(f"SELECT id FROM {table} WHERE {where_clause}", values)
    row = cursor.fetchone()

    if row:
        print(f"Found existing {table[:-1]}: '{values[0]}'")
        return row[0]
    else:
        placeholders = ", ".join(["?"] * len(columns))
        cursor.execute(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})", values)
        print(f"Added new {table[:-1]}: '{values[0]}'")
        return cursor.lastrowid

def get_numeric_input(prompt, input_type=float, required=False):
    """Continuously prompts user until a valid number is entered."""
    while True:
        try:
            value = input(prompt).strip()
            if not value:  # Handle empty input for optional fields
                if required:
                    print("Error: This field is required.")
                    continue
                return None
            return input_type(value)
        except (ValueError, TypeError):
            print(f"Invalid input. Please enter a valid number.")

def add_shoe_cli():
    """
    An interactive command-line interface to add a new sneaker to the inventory.
    """
    if not DB_FILE.exists():
        print(f"Error: Database not found at {DB_FILE}. Please run init_db.py first.")
        return

    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        print("--- Add a New Sneaker to Your Collection ---")

        # --- Step 1: Brand ---
        brand_name = input("Enter brand name (e.g., Nike): ").strip().title()
        brand_id = get_or_create_record(cursor, 'Brands', ('name',), (brand_name,))

        # --- Step 2: Silhouette ---
        silhouette_name = input("Enter silhouette (e.g., Air Jordan 4): ").strip()
        silhouette_id = get_or_create_record(cursor, 'Silhouettes', ('name', 'brand_id'), (silhouette_name, brand_id))

        # --- Step 3: Release ---
        release_name = input("Enter release name (e.g., Bred Reimagined): ").strip()
        cursor.execute("SELECT id FROM Releases WHERE name = ? AND silhouette_id = ?", (release_name, silhouette_id))
        release_row = cursor.fetchone()
        if release_row:
            release_id = release_row[0]
            print(f"Found existing release: '{release_name}'")
        else:
            print(f"Adding new release: '{release_name}'")
            sku = input("Enter SKU (optional): ").strip() or None
            release_year = get_numeric_input("Enter release year (optional): ", int)
            cursor.execute(
                "INSERT INTO Releases (name, silhouette_id, sku, release_year) VALUES (?, ?, ?, ?)",
                (release_name, silhouette_id, sku, release_year)
            )
            release_id = cursor.lastrowid

        # --- Step 4: Inventory Details ---
        print("\n--- Finally, enter the details of your specific pair ---")
        size = get_numeric_input("Enter size: ", required=True)
        condition = input("Enter condition (e.g., New, Used): ").strip()
        purchase_price = get_numeric_input("Enter purchase price: ")

        cursor.execute(
            "INSERT INTO Inventory (release_id, size, condition, purchase_price) VALUES (?, ?, ?, ?)",
            (release_id, size, condition, purchase_price)
        )

        conn.commit()
        print(f"\n✅ Success! '{brand_name} {silhouette_name} - {release_name}' has been added to your inventory.")

    except sqlite3.Error as e:
        print(f"\n❌ A database error occurred: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    add_shoe_cli()
