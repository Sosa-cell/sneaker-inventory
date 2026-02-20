import sqlite3
from pathlib import Path

# Define the script's directory and the project's root directory
# The script is in /app, so the root is one level up.
ROOT_DIR = Path(__file__).resolve().parent.parent
DB_FILE = ROOT_DIR / 'sneakers.db'

def main():
    """
    Initializes a new SQLite database with the updated schema.
    It will overwrite the database if it already exists.
    """
    schema_sql = """
    DROP TABLE IF EXISTS Inventory;
    DROP TABLE IF EXISTS Releases;
    DROP TABLE IF EXISTS Silhouettes;
    DROP TABLE IF EXISTS Brands;
    DROP TABLE IF EXISTS Categories;

    CREATE TABLE Categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );

    CREATE TABLE Brands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        FOREIGN KEY (category_id) REFERENCES Categories (id)
    );

    CREATE TABLE Silhouettes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        genre TEXT,
        FOREIGN KEY (brand_id) REFERENCES Brands (id)
    );

    CREATE TABLE Releases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        silhouette_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        sku TEXT,
        release_year INTEGER,
        FOREIGN KEY (silhouette_id) REFERENCES Silhouettes (id)
    );

    CREATE TABLE Inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        release_id INTEGER NOT NULL,
        size REAL,
        condition TEXT,
        purchase_price REAL,
        status TEXT DEFAULT 'In Stock',
        FOREIGN KEY (release_id) REFERENCES Releases (id)
    );

    INSERT INTO Categories (name) VALUES ('Sneakers');
    """

    try:
        # Note: We do not unlink (delete) the file here because it might be locked
        # by the running dashboard. The DROP TABLE commands above handle the cleanup.

        # Create a connection to the database file (this creates the file)
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Execute the entire schema script
        cursor.executescript(schema_sql)

        # Commit the changes and close the connection
        conn.commit()
        conn.close()

        print('Database initialized successfully.')

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    main()
