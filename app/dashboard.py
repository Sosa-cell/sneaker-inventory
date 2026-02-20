import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path

# --- Page & Database Configuration ---
st.set_page_config(page_title="Mooncake's Vault", layout="wide", page_icon="")
ROOT_DIR = Path(__file__).resolve().parent.parent
DB_FILE = ROOT_DIR / 'sneakers.db'

# --- UI/CSS Overrides ---
st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        /* Import Google Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

        html, body, [class*="css"]  {
            font-family: 'Inter', sans-serif;
        }
        
        /* Navbar-like header styling */
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 15px;
            color: white;
            margin-bottom: 2rem;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
        .main-header h1 {
            font-weight: 700;
            color: white !important;
        }
        
        /* Metric Cards */
        [data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.9rem;
            color: #64748b;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.8rem;
            color: #1e293b;
            font-weight: 700;
        }

        /* Buttons */
        .stButton button {
            background-color: #4f46e5;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 0.5rem 1rem;
            font-weight: 600;
            transition: all 0.2s;
        }
        .stButton button:hover {
            background-color: #4338ca;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
    </style>
""", unsafe_allow_html=True)

# --- Database Functions ---

def run_query(query, params=(), fetch=None):
    """A generic function to run SQL queries."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            if fetch == 'one':
                return cursor.fetchone()
            if fetch == 'all':
                return cursor.fetchall()
            return cursor.lastrowid
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return None

def check_and_migrate_schema():
    """Ensures the database schema is up to date."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(Silhouettes)")
            columns = [info[1] for info in cursor.fetchall()]
            if 'genre' not in columns:
                cursor.execute("ALTER TABLE Silhouettes ADD COLUMN genre TEXT")
    except Exception:
        pass

def load_data(category_id):
    """Loads all inventory data into a pandas DataFrame."""
    query = """
    SELECT
        i.id,
        b.name AS "Brand",
        s.name AS "Silhouette",
        s.genre AS "Genre",
        r.name AS "Release",
        i.size AS "Size",
        i.condition AS "Condition",
        i.purchase_price AS "Price",
        i.status AS "Status"
    FROM Inventory i
    JOIN Releases r ON i.release_id = r.id
    JOIN Silhouettes s ON r.silhouette_id = s.id
    JOIN Brands b ON s.brand_id = b.id
    WHERE b.category_id = ?
    ORDER BY i.id DESC;
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            df = pd.read_sql_query(query, conn, params=(category_id,), index_col='id')
        return df
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return pd.DataFrame()

# --- Main App ---
# Title removed here to be placed dynamically later

# Initialize DB if it doesn't exist
if not DB_FILE.exists():
    import init_db
    init_db.main()
    if not DB_FILE.exists():
        st.error("Failed to initialize database. Check console logs.")
        st.stop()
    st.rerun()

# Run migration check
check_and_migrate_schema()

# --- Sidebar: Category Management ---
st.sidebar.header("🗃️ Collections")

# Fetch Categories
try:
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM Categories")
        cats = cursor.fetchall()
except sqlite3.OperationalError:
    cats = None

if cats is None:
    st.warning("Database schema mismatch detected. Re-initializing database...")
    import init_db
    init_db.main()
    st.rerun()

if not cats:
    run_query("INSERT INTO Categories (name) VALUES ('Sneakers')")
    cats = run_query("SELECT id, name FROM Categories", fetch='all')

cat_map = {name: id for id, name in cats}
selected_cat_name = st.sidebar.selectbox("Select Category", list(cat_map.keys()))
selected_cat_id = cat_map[selected_cat_name]

# Add New Category
with st.sidebar.expander("✨ Create New Category"):
    with st.form("add_category_form", clear_on_submit=True):
        new_cat_name = st.text_input("Category Name (e.g. Vinyls)").strip()
        submitted = st.form_submit_button("Create Category")

        if submitted:
            if new_cat_name:
                if new_cat_name in cat_map:
                    st.warning(f"Category '{new_cat_name}' already exists.")
                elif run_query("INSERT INTO Categories (name) VALUES (?)", (new_cat_name,)) is not None:
                    st.rerun()
            else:
                st.warning("Please enter a name.")

# Delete Category
with st.sidebar.expander("⛔ Delete Category"):
    st.warning(f"This will delete '{selected_cat_name}' and hide its items.")
    if st.button("Confirm Delete"):
        run_query("DELETE FROM Categories WHERE id = ?", (selected_cat_id,))
        st.rerun()

# Dynamic Labels based on Category
SHOW_GENRE = False
SHOW_SIZE = True
if "vinyl" in selected_cat_name.lower():
    LBL_BRAND, LBL_SIL, LBL_REL = "Artist", "Album", "Pressing"
    SHOW_GENRE = True
    SHOW_SIZE = False
elif "book" in selected_cat_name.lower():
    LBL_BRAND, LBL_SIL, LBL_REL = "Author", "Book Title", "Edition"
else:
    LBL_BRAND, LBL_SIL, LBL_REL = "Brand", "Silhouette", "Release"

# --- Custom Header ---
st.markdown(f"""
    <div class="main-header">
        <h1 class="display-4"> Mooncake's Vault</h1>
        <p class="lead" style="opacity: 0.9;">Tracking your <strong>{selected_cat_name}</strong> collection.</p>
    </div>
""", unsafe_allow_html=True)

# Create Tabs
tab_dashboard, tab_add, tab_edit = st.tabs([f"📈 {selected_cat_name} Stats", "📥 Add Item", "🔧 Manage Items"])

# Load data for all tabs
df = load_data(selected_cat_id)

# Rename columns for display based on dynamic labels
display_df = df.rename(columns={"Brand": LBL_BRAND, "Silhouette": LBL_SIL, "Release": LBL_REL})

# --- Dashboard Tab ---
with tab_dashboard:
    if display_df.empty:
        st.info(f"Your {selected_cat_name} inventory is empty. Add an item to get started.")
    else:
        st.header("Collection Overview")
        # Top Metrics
        total_pairs = len(df)
        total_value = df[df['Status'] != 'Sold']['Price'].sum()
        avg_price = df['Price'].mean()
        max_price = df['Price'].max()

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Pairs", f"{total_pairs}")
        m2.metric("Total Value (Unsold)", f"${total_value:,.2f}")
        m3.metric("Average Price", f"${avg_price:,.2f}")
        m4.metric("Highest Price", f"${max_price:,.2f}")
        
        st.markdown("---")

        c1, c2 = st.columns([1, 2])
        # Bar Chart
        with c1:
            if SHOW_GENRE:
                chart_group = st.radio("Group Value By:", [LBL_BRAND, "Genre"], horizontal=True)
            else:
                chart_group = LBL_BRAND
            
            if chart_group == "Genre":
                # Handle missing genres for older items
                display_df["Genre"] = display_df["Genre"].fillna("Unknown")
            
            st.subheader(f"Value by {chart_group}")
            chart_data = display_df.groupby(chart_group)["Price"].sum()
            st.bar_chart(chart_data)
        # Full Dataframe
        with c2:
            st.subheader("Full Inventory")
            if not SHOW_GENRE and "Genre" in display_df.columns:
                display_df = display_df.drop(columns=["Genre"])
            if not SHOW_SIZE and "Size" in display_df.columns:
                display_df = display_df.drop(columns=["Size"])
            st.dataframe(display_df, use_container_width=True, hide_index=True)

# --- Add Shoe Tab ---
with tab_add:
    st.header(f"Add to {selected_cat_name}")
    with st.form("add_form", clear_on_submit=True):
        brand = st.text_input(LBL_BRAND)
        silhouette = st.text_input(LBL_SIL)
        if SHOW_GENRE:
            genre = st.text_input("Genre")
        else:
            genre = None
        release = st.text_input(f"{LBL_REL} / Variant")
        if SHOW_SIZE:
            size = st.number_input("Size", step=0.5)
        else:
            size = None
        condition = st.selectbox("Condition", ["New", "Used", "Deadstock"])
        price = st.number_input("Purchase Price", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("Add Item")

        if submitted:
            if not all([brand, silhouette, release]):
                st.warning("Please fill in all fields.")
            else:
                brand_id = run_query("INSERT OR IGNORE INTO Brands (name, category_id) VALUES (?, ?);", (brand, selected_cat_id))
                brand_id = run_query("SELECT id FROM Brands WHERE name=? AND category_id=?", (brand, selected_cat_id), fetch='one')[0]

                sil_id = run_query("INSERT OR IGNORE INTO Silhouettes (name, brand_id, genre) VALUES (?,?,?);", (silhouette, brand_id, genre))
                sil_id = run_query("SELECT id FROM Silhouettes WHERE name=? AND brand_id=?", (silhouette, brand_id), fetch='one')[0]

                rel_id = run_query("INSERT OR IGNORE INTO Releases (name, silhouette_id) VALUES (?,?);", (release, sil_id))
                rel_id = run_query("SELECT id FROM Releases WHERE name=? AND silhouette_id=?", (release, sil_id), fetch='one')[0]
                
                run_query(
                    "INSERT INTO Inventory (release_id, size, condition, purchase_price, status) VALUES (?,?,?,?,?)",
                    (rel_id, size, condition, price, 'In Stock')
                )
                st.success("Item added successfully!")
                st.rerun()

# --- Edit / Delete Tab ---
with tab_edit:
    st.header("Manage Existing Inventory")
    if display_df.empty:
        st.info("No items to manage.")
    else:
        # Create a mapping from a display string to the inventory ID
        shoe_options = {f'{idx}: {row[LBL_BRAND]} {row[LBL_SIL]} - {row[LBL_REL]}': idx for idx, row in display_df.iterrows()}
        selected_key = st.selectbox("Select an item to manage", options=shoe_options.keys())
        selected_id = shoe_options[selected_key]
        
        shoe_data = df.loc[selected_id]

        st.markdown("---")
        
        # Edit Form
        st.subheader("Edit Details")
        with st.form("edit_form"):
            if SHOW_GENRE:
                current_genre = shoe_data["Genre"] if shoe_data["Genre"] else ""
                new_genre = st.text_input("Genre", value=current_genre)
            else:
                new_genre = shoe_data["Genre"]
            
            new_price = st.number_input("Price", value=shoe_data["Price"], format="%.2f")
            
            conditions = ["New", "Used", "Deadstock"]
            cond_index = conditions.index(shoe_data["Condition"]) if shoe_data["Condition"] in conditions else 0
            new_condition = st.selectbox("Condition", conditions, index=cond_index)
            
            statuses = ["In Stock", "For Sale", "Sold"]
            stat_index = statuses.index(shoe_data["Status"]) if shoe_data["Status"] in statuses else 0
            new_status = st.selectbox("Status", statuses, index=stat_index)
            
            update_submitted = st.form_submit_button("Update Item")

            if update_submitted:
                run_query(
                    "UPDATE Inventory SET purchase_price=?, condition=?, status=? WHERE id=?",
                    (new_price, new_condition, new_status, selected_id)
                )
                
                # Update Genre in Silhouettes table
                run_query(
                    """
                    UPDATE Silhouettes 
                    SET genre = ? 
                    WHERE id = (
                        SELECT r.silhouette_id 
                        FROM Releases r 
                        JOIN Inventory i ON r.id = i.release_id 
                        WHERE i.id = ?)
                    """,
                    (new_genre, selected_id)
                )
                st.success("Item details updated!")
                st.rerun()

        st.markdown("---")

        # Delete Section
        st.subheader("Delete Item")
        st.error("Warning: This action is permanent and cannot be undone.")
        if st.button("Delete Permanently"):
            run_query("DELETE FROM Inventory WHERE id=?", (selected_id,))
            st.success("Item has been deleted from the database.")
            st.rerun()