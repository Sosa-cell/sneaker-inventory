import sqlite3
from pathlib import Path

# Define the project root and the path to the database file
ROOT_DIR = Path(__file__).resolve().parent.parent
DB_FILE = ROOT_DIR / 'sneakers.db'

def format_currency(value):
    """
    Formats a numeric value into a standard currency string ($1,234.56).
    Returns '$0.00' if the value is None.
    """
    if value is None:
        return "$0.00"
    return f"${value:,.2f}"

def calculate_and_print_stats():
    """
    Connects to the database to calculate and print portfolio statistics.
    """
    if not DB_FILE.exists():
        print(f"Error: Database file not found at {DB_FILE}")
        print("Please run 'init_db.py' and 'seed_data.py' first.")
        return

    try:
        # Connect to the database in read-only mode
        db_uri = f'{DB_FILE.as_uri()}?mode=ro'
        conn = sqlite3.connect(db_uri, uri=True)
        cursor = conn.cursor()

        # --- 1. Calculate Total Collection Value ---
        cursor.execute("SELECT SUM(purchase_price) FROM Inventory")
        total_value = cursor.fetchone()[0]

        print("--- Portfolio Value ---")
        print(f"Total Investment: {format_currency(total_value)}")
        print("-" * 25)

        # --- 2. Calculate Value Breakdown by Brand ---
        breakdown_query = """
        SELECT
            b.name AS brand_name,
            SUM(i.purchase_price) AS brand_total
        FROM
            Inventory i
        INNER JOIN
            Releases r ON i.release_id = r.id
        INNER JOIN
            Silhouettes s ON r.silhouette_id = s.id
        INNER JOIN
            Brands b ON s.brand_id = b.id
        WHERE
            i.purchase_price IS NOT NULL
        GROUP BY
            brand_name
        ORDER BY
            brand_total DESC;
        """
        cursor.execute(breakdown_query)
        brand_breakdown = cursor.fetchall()

        print("--- Investment by Brand ---")
        if not brand_breakdown:
            print("No data available for brand breakdown.")
        else:
            for brand, total in brand_breakdown:
                print(f"{brand:<15} {format_currency(total)}")

    except sqlite3.Error as e:
        print(f"A database error occurred: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == '__main__':
    calculate_and_print_stats()
