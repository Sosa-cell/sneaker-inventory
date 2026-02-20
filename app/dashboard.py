import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- Page & Database Configuration ---
st.set_page_config(page_title="Mooncake's Vault", layout="wide", page_icon="👟")

# --- Login System ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def check_login():
    """Simple username/password check against secrets."""
    user = st.session_state.username
    pwd = st.session_state.password
    
    # Check if users are defined in secrets
    if "users" in st.secrets:
        if user in st.secrets["users"] and st.secrets["users"][user] == pwd:
            st.session_state.authenticated = True
            st.session_state.logged_in_user = user
            del st.session_state.password  # Clean up
            del st.session_state.username
        else:
            st.error("😕 Incorrect username or password")
    else:
        st.warning("No users defined in secrets.toml. Please set up [users] section.")

if not st.session_state.authenticated:
    st.markdown("## 🔐 Mooncake's Vault Login")
    st.text_input("Username", key="username")
    st.text_input("Password", type="password", key="password")
    st.button("Log In", on_click=check_login)
    st.stop()  # Stop execution here until logged in

# --- UI/CSS Overrides ---
st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        /* Import Google Font */
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

        html, body, [class*="css"]  {
            font-family: 'Poppins', sans-serif;
            color: #2d3436;
        }
        
        .stApp {
            background-image: linear-gradient(to top, #a8edea 0%, #fed6e3 100%);
        }
        
        /* Navbar-like header styling */
        .main-header {
            background-color: rgba(255, 255, 255, 0.6);
            backdrop-filter: blur(10px);
            padding: 2rem;
            border-radius: 20px;
            border: 2px solid rgba(255, 255, 255, 0.5);
            color: #2d3436;
            margin-bottom: 2rem;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
            text-align: center;
        }
        .main-header h1 {
            font-weight: 700;
            color: #6c5ce7;
            letter-spacing: -1px;
        }
        .main-header p {
            color: #636e72;
            font-size: 1.1rem;
        }
        
        /* Metric Cards */
        [data-testid="stMetric"] {
            background-color: rgba(255, 255, 255, 0.7);
            border: none;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            transition: transform 0.2s;
        }
        [data-testid="stMetric"]:hover {
            transform: scale(1.05);
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.9rem;
            color: #636e72;
            font-weight: 600;
        }
        [data-testid="stMetricValue"] {
            font-size: 2rem;
            color: #2d3436;
            font-weight: 700;
        }

        /* Buttons */
        .stButton button {
            background-image: linear-gradient(to right, #6c5ce7 0%, #a29bfe 51%, #6c5ce7 100%);
            background-size: 200% auto;
            color: white;
            border-radius: 50px;
            border: none;
            padding: 0.6rem 1.5rem;
            font-weight: 600;
            transition: 0.5s;
            box-shadow: 0 4px 15px 0 rgba(108, 92, 231, 0.35);
        }
        .stButton button:hover {
            background-position: right center;
            color: #fff;
            transform: translateY(-2px);
        }
    </style>
""", unsafe_allow_html=True)

# --- Google Sheets Connection ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    """Loads the inventory from Google Sheets."""
    try:
        # Try loading "Inventory" worksheet, fallback to first sheet if missing
        try:
            df = conn.read(worksheet="Inventory", ttl=0)
        except Exception:
            df = conn.read(ttl=0)

        # Ensure standard columns exist if sheet is new
        required_cols = ["Owner", "Category", "Brand", "Silhouette", "Genre", "Release", "Size", "Condition", "Price", "Status"]
        
        # Normalize columns (strip spaces)
        df.columns = df.columns.str.strip()
        
        # Ensure all required columns exist (add missing ones)
        for col in required_cols:
            if col not in df.columns:
                df[col] = None

        # Backfill Owner if missing (migration helper: claims existing data for current user)
        df["Owner"] = df["Owner"].fillna(st.session_state.logged_in_user)
            
        # Drop completely empty rows
        df = df.dropna(how="all")
        return df
    except Exception as e:
        # Show errors (like Auth or Permission issues)
        st.error(f"⚠️ Error loading data: {e}")
        
        return pd.DataFrame(columns=["Owner", "Category", "Brand", "Silhouette", "Genre", "Release", "Size", "Condition", "Price", "Status"])

def save_data(df):
    """Saves the dataframe back to Google Sheets."""
    try:
        try:
            conn.update(worksheet="Inventory", data=df)
        except Exception:
            # Fallback to default sheet if "Inventory" doesn't exist
            conn.update(data=df)
            
        st.cache_data.clear() # Clear cache to force reload on next action
        return True
    except Exception as e:
        st.error(f"Failed to save data: {e}")
        return False

# --- Main App ---

# Load Data
df = get_data()

# Filter data for the current logged-in user (View Layer)
user_df = df[df["Owner"] == st.session_state.logged_in_user]

# --- Sidebar: Category Management ---
st.sidebar.header("🗃️ Collections")

# Get unique categories from the user's data only
if not user_df.empty and "Category" in user_df.columns:
    existing_categories = sorted(user_df["Category"].dropna().unique().tolist())
else:
    existing_categories = ["Sneakers"]

selected_cat_name = st.sidebar.selectbox("Select Category", existing_categories)

# --- Sidebar: Developer Tools ---
with st.sidebar.expander("🔧 Developer Tools"):
    if st.button("Load Dummy Data"):
        dummy_data = [
            {"Owner": st.session_state.logged_in_user, "Category": "Sneakers", "Brand": "Nike", "Silhouette": "Air Jordan 1", "Genre": None, "Release": "Chicago Lost & Found", "Size": 10.5, "Condition": "New", "Price": 180.00, "Status": "In Stock"},
            {"Owner": st.session_state.logged_in_user, "Category": "Sneakers", "Brand": "Adidas", "Silhouette": "Yeezy Boost 350", "Genre": None, "Release": "Turtle Dove", "Size": 10.0, "Condition": "Used", "Price": 250.00, "Status": "In Stock"},
            {"Owner": st.session_state.logged_in_user, "Category": "Sneakers", "Brand": "New Balance", "Silhouette": "990v3", "Genre": None, "Release": "Teddy Santis Marblehead", "Size": 11.0, "Condition": "New", "Price": 210.00, "Status": "In Stock"},
            {"Owner": st.session_state.logged_in_user, "Category": "Vinyls", "Brand": "Pink Floyd", "Silhouette": "Dark Side of the Moon", "Genre": "Rock", "Release": "1973 UK Pressing", "Size": None, "Condition": "Good", "Price": 45.00, "Status": "In Stock"},
            {"Owner": st.session_state.logged_in_user, "Category": "Vinyls", "Brand": "Kendrick Lamar", "Silhouette": "DAMN.", "Genre": "Hip Hop", "Release": "Collector Edition", "Size": None, "Condition": "New", "Price": 35.00, "Status": "In Stock"},
            {"Owner": st.session_state.logged_in_user, "Category": "Books", "Brand": "J.R.R. Tolkien", "Silhouette": "The Hobbit", "Genre": "Fantasy", "Release": "75th Anniversary", "Size": None, "Condition": "New", "Price": 15.00, "Status": "In Stock"}
        ]
        dummy_df = pd.DataFrame(dummy_data)
        
        # Concatenate with existing data if it exists
        if not df.empty:
            updated_df = pd.concat([df, dummy_df], ignore_index=True)
        else:
            updated_df = dummy_df
            
        st.write("Saving the following data...", updated_df) # Preview data
        if save_data(updated_df):
            st.success("Dummy data loaded!")
            st.balloons()
            # Removed st.rerun() so you can see the success message and any errors
            # Click "Rerun" in the top right manually if needed

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
        <h1 class="display-4">🚀 Mooncake's Vault</h1>
        <p class="lead">Tracking your <strong>{selected_cat_name}</strong> collection.</p>
    </div>
""", unsafe_allow_html=True)

# Create Tabs
tab_dashboard, tab_add, tab_edit = st.tabs([f"📈 {selected_cat_name} Stats", "📥 Add Item", "🔧 Manage Items"])

# Filter data for the selected category
cat_df = user_df[user_df["Category"] == selected_cat_name].copy()

# Rename columns for display
display_df = cat_df.rename(columns={"Brand": LBL_BRAND, "Silhouette": LBL_SIL, "Release": LBL_REL})

# --- Dashboard Tab ---
with tab_dashboard:
    if display_df.empty:
        st.info(f"Your {selected_cat_name} inventory is empty. Add an item to get started.")
    else:
        st.header("Collection Overview")
        
        total_pairs = len(cat_df)
        total_value = cat_df[cat_df['Status'] != 'Sold']['Price'].sum()
        avg_price = cat_df['Price'].mean()
        max_price = cat_df['Price'].max()

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
        # Allow user to type a new category or use the current one
        category_input = st.text_input("Category", value=selected_cat_name)
        
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
                # Create new row
                new_row = pd.DataFrame([{
                    "Owner": st.session_state.logged_in_user,
                    "Category": category_input,
                    "Brand": brand,
                    "Silhouette": silhouette,
                    "Genre": genre,
                    "Release": release,
                    "Size": size,
                    "Condition": condition,
                    "Price": price,
                    "Status": "In Stock"
                }])
                
                # Append and Save
                updated_df = pd.concat([df, new_row], ignore_index=True)
                if save_data(updated_df):
                    st.success("Item added successfully!")
                    st.balloons()
                    st.rerun()

# --- Edit / Delete Tab ---
with tab_edit:
    st.header("Manage Existing Inventory")
    if display_df.empty:
        st.info("No items to manage.")
    else:
        # Create a mapping from a display string to the inventory ID
        shoe_options = {f'{idx}: {row["Brand"]} {row["Silhouette"]} - {row["Release"]}': idx for idx, row in cat_df.iterrows()}
        selected_key = st.selectbox("Select an item to manage", options=shoe_options.keys())
        selected_id = shoe_options[selected_key]
        
        shoe_data = cat_df.loc[selected_id]

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
                # Update specific fields in the main dataframe
                df.at[selected_id, "Genre"] = new_genre
                df.at[selected_id, "Price"] = new_price
                df.at[selected_id, "Condition"] = new_condition
                df.at[selected_id, "Status"] = new_status
                
                if save_data(df):
                    st.success("Item details updated!")
                    st.balloons()
                    st.rerun()

        st.markdown("---")

        # Delete Section
        st.subheader("Delete Item")
        st.error("Warning: This action is permanent and cannot be undone.")
        if st.button("Delete Permanently"):
            df = df.drop(selected_id)
            if save_data(df):
                st.success("Item has been deleted from the database.")
                st.rerun()