import sqlite3
from pathlib import Path

# Define the project root and the path to the database file
ROOT_DIR = Path(__file__).resolve().parent.parent
DB_FILE = ROOT_DIR / 'sneakers.db'

def view_all_inventory():
    """
    Connects to the database and prints a formatted list of all inventory items.
    """
    if not DB_FILE.exists():
        print(f"Error: Database file not found at {DB_FILE}")
        print("Please run 'init_db.py' and optionally 'seed_data.py' first.")
        return

    try:
        # Connect to the database in read-only mode for safety
        db_uri = f'{DB_FILE.as_uri()}?mode=ro'
        conn = sqlite3.connect(db_uri, uri=True)
        conn.row_factory = sqlite3.Row  # Access columns by name
        cursor = conn.cursor()

        # SQL query to join the four tables
        query = """
        SELECT
            b.name AS brand,
            s.name AS silhouette,
            r.name AS release_name,
            i.size,
            i.purchase_price
        FROM
            Inventory i
        INNER JOIN
            Releases r ON i.release_id = r.id
        INNER JOIN
            Silhouettes s ON r.silhouette_id = s.id
        INNER JOIN
            Brands b ON s.brand_id = b.id
        ORDER BY
            brand, silhouette, release_name;
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        if not rows:
            print("Your inventory is currently empty.")
            return

        print("--- Your Sneaker Inventory ---")
        for row in rows:
            # Format the price to ensure two decimal places, handle if it's None
            price_str = f"{row['purchase_price']:.2f}" if row['purchase_price'] is not None else "0.00"

            # Build and print the final formatted string
            output_string = (
                f"{row['brand']} {row['silhouette']} - {row['release_name']} "
                f"(Size: {row['size']}) - ${price_str}"
            )
            print(output_string)

    except sqlite3.OperationalError as e:
        print(f"A database error occurred: {e}")
        print("Please ensure the database has been initialized correctly with 'init_db.py'.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == '__main__':
    view_all_inventory()
