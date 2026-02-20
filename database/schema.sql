-- To enforce foreign key constraints in SQLite, run: PRAGMA foreign_keys = ON;

-- Table for Brands (e.g., Nike, Adidas)
CREATE TABLE Brands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- Table for Silhouettes (e.g., 'Air Jordan 1')
CREATE TABLE Silhouettes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (brand_id) REFERENCES Brands(id) ON DELETE CASCADE,
    UNIQUE (brand_id, name)
);

-- Table for Releases (e.g., 'Lost and Found')
CREATE TABLE Releases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    silhouette_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    sku TEXT,
    release_year INTEGER,
    FOREIGN KEY (silhouette_id) REFERENCES Silhouettes(id) ON DELETE CASCADE,
    UNIQUE (silhouette_id, name)
);

-- Table for Inventory
CREATE TABLE Inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    release_id INTEGER NOT NULL,
    size REAL NOT NULL,
    condition TEXT NOT NULL,
    purchase_price REAL,
    status TEXT NOT NULL DEFAULT 'In Stock',
    FOREIGN KEY (release_id) REFERENCES Releases(id) ON DELETE CASCADE
);
