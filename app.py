import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import hashlib
import random
import time
import base64
import os
from PIL import Image
import io

# Page config
st.set_page_config(
    page_title="🍕 Foodees -  Food Delivery",
    page_icon="🍕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for app look & mobile style
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Noto+Sans+Devanagari:wght@400;500;700&display=swap');
    
    * {
        font-family: 'Poppins', sans-serif;
    }
    .hindi-text {
        font-family: 'Noto Sans Devanagari', sans-serif;
    }

    /* Hide default Streamlit header & footer */
    header[data-testid="stHeader"] {
        display: none;
    }
    #MainMenu {
        visibility: hidden;
    }
    footer {
        visibility: hidden;
    }

    /* Sidebar hide */
    [data-testid="stSidebar"][aria-expanded="true"],
    [data-testid="stSidebar"][aria-expanded="false"] {
        display: none;
    }
    [data-testid="collapsedControl"] {
        display: none;
    }

    .main .block-container {
        padding-top: 4.5rem;
    }

    /* Gradient background */
    .stApp {
        background: linear-gradient(135deg, #00D084 0%, #FF6B35 50%, #00D084 100%);
        background-attachment: fixed;
    }
    
    /* Glassmorphism cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.25);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.18);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.2);
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(45deg, #00D084, #FF6B35);
        border: none;
        border-radius: 50px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        color: white;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 208, 132, 0.4);
    }
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(0, 208, 132, 0.6);
    }

    /* Top app bar (mobile app style) */
    .custom-appbar {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 56px;
        background: linear-gradient(90deg, #00D084, #FF6B35);
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 1rem;
        z-index: 999;
        box-shadow: 0 2px 8px rgba(0,0,0,0.25);
        color: white;
    }
    .custom-appbar-logo {
        font-weight: 700;
        font-size: 1.1rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .custom-appbar-logo span {
        font-size: 1.4rem;
    }
    .custom-appbar-menu {
        font-size: 1.4rem;
        cursor: pointer;
    }

    /* Responsive */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }

        .metric-card {
            margin: 0.4rem 0;
            padding: 0.8rem;
        }

        .stButton > button {
            width: 100%;
            padding: 0.9rem;
            font-size: 0.9rem;
        }

        h1, h2, h3 {
            font-size: 1.1rem;
        }

        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
        }

        .stDataFrame, .stDataFrame div[role="grid"] {
            overflow-x: auto;
        }
    }

    /* Icons using emojis */
    .icon { font-size: 2rem; margin-right: 0.5rem; }
    </style>
""", unsafe_allow_html=True)

# Custom top app bar (mobile-app style)
st.markdown("""
<div class="custom-appbar">
  <div class="custom-appbar-logo">
    <span>🍕</span>
    <div>Foodees</div>
  </div>
  <div class="custom-appbar-menu">☰</div>
</div>
""", unsafe_allow_html=True)

    /* Icons using emojis */
    .icon { font-size: 2rem; margin-right: 0.5rem; }
    </style>
""", unsafe_allow_html=True)

# Database
@st.cache_resource
def get_db():
    conn = sqlite3.connect('foodtiger.db', check_same_thread=False)
    c = conn.cursor()
    
    # Schema as specified
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT UNIQUE,
        password TEXT,
        role TEXT,
        name TEXT,
        status INTEGER DEFAULT 1
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS restaurants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER,
        name TEXT,
        banner_image TEXT,
        rating REAL DEFAULT 4.0,
        is_approved INTEGER DEFAULT 0,
        FOREIGN KEY(owner_id) REFERENCES users(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        restaurant_id INTEGER,
        name TEXT,
        hindi_name TEXT,
        price REAL,
        image_path TEXT,
        is_available INTEGER DEFAULT 1,
        FOREIGN KEY(restaurant_id) REFERENCES restaurants(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        restaurant_id INTEGER,
        delivery_id INTEGER,
        items_json TEXT,
        total REAL,
        status TEXT DEFAULT 'pending',
        tracking_id TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(customer_id) REFERENCES users(id),
        FOREIGN KEY(restaurant_id) REFERENCES restaurants(id),
        FOREIGN KEY(delivery_id) REFERENCES users(id)
    )''')
    
    conn.commit()
    
    # Sample data (users)
    sample_users = [
        (9876543210, hashlib.md5('admin123'.encode()).hexdigest(), 'superadmin', 'Super Admin'),
        (9876543211, hashlib.md5('rest123'.encode()).hexdigest(), 'restaurant', 'Restaurant Owner'),
        (9876543212, hashlib.md5('cust123'.encode()).hexdigest(), 'customer', 'Rahul Sharma'),
        (9876543213, hashlib.md5('del123'.encode()).hexdigest(), 'delivery', 'Delivery Boy 1'),
    ]
    c.executemany(
        "INSERT OR IGNORE INTO users (phone, password, role, name) VALUES (?, ?, ?, ?)",
        sample_users
    )
    
    # Sample restaurants (linked to owner_id = 2)
    sample_restaurants = [
        (2, 'Biryani House', 'biriyani_banner.jpg', 4.5, 1),
        (2, 'Pizza Corner', 'pizza_banner.jpg', 4.2, 1),
        (2, 'Chai Sutta Bar', 'chai_banner.jpg', 4.8, 0),
    ]
    c.executemany(
        "INSERT OR IGNORE INTO restaurants (owner_id, name, banner_image, rating, is_approved) VALUES (?, ?, ?, ?, ?)",
        sample_restaurants
    )
    
    # Sample menu
    sample_menu = [
        (1, 'Chicken Biryani', 'मुर्गा बिरयानी', 250, 'chicken_biryani.jpg'),
        (1, 'Veg Biryani', 'वेज बिरयानी', 180, 'veg_biryani.jpg'),
        (2, 'Margherita Pizza', 'मार्गेरिटा पिज्जा', 320, 'pizza.jpg'),
        (2, 'Pepperoni Pizza', 'पेपरनी पिज्जा', 380, 'pepperoni.jpg'),
    ]
    c.executemany(
        "INSERT OR IGNORE INTO menu_items (restaurant_id, name, hindi_name, price, image_path) VALUES (?, ?, ?, ?, ?)",
        sample_menu
    )
    
    # Sample orders
    for _ in range(20):
        c.execute(
            "INSERT INTO orders (customer_id, restaurant_id, delivery_id, items_json, total, tracking_id) VALUES (?, ?, ?, ?, ?, ?)",
            (3, random.choice([1, 2]), 4, '[{"name":"Biryani","qty":2}]', random.uniform(200, 500), f'TRACK{random.randint(1000,9999)}')
        )
    
    conn.commit()
    return conn

# Image directory
os.makedirs('images', exist_ok=True)

# Session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'cart' not in st.session_state:
    st.session_state.cart = []

# Helper functions
def hash_password(pwd: str) -> str:
    return hashlib.md5(pwd.encode()).hexdigest()

def load_image(path):
    if path and os.path.exists(path):
        return Image.open(path)
    return None

def save_image(uploaded_file, filename):
    path = f'images/{filename}'
    with open(path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return path

# Real-time polling
def auto_refresh():
    time.sleep(5)
    st.rerun()

# Main app
conn = get_db()

# Title
col1, col2 = st.columns([4,1])
with col1:
    st.title("🍕 FoodTiger - प्रोफेशनल फूड डिलीवरी ऐप")
with col2:
    if st.button("🔄 रिफ्रेश"):
        st.rerun()

st.markdown("---")

# LOGIN
if st.session_state.user is None:
    st.header("📱 लॉगिन करें")
    
    phone = st.text_input("📞 फोन नंबर", placeholder="9876543210")
    password = st.text_input("🔑 पासवर्ड", type="password")
    
    if st.button("🚀 लॉगिन", type="primary"):
        df = pd.read_sql(
            "SELECT * FROM users WHERE phone=? AND password=? AND status=1",
            conn,
            params=(phone, hash_password(password))
        )
        if not df.empty:
            st.session_state.user = df.iloc[0].to_dict()
            st.success(f"✅ स्वागत है, {st.session_state.user['name']}!")
            st.rerun()
        else:
            st.error("❌ गलत फोन या पासवर्ड!")
    
    st.info("**डेमो लॉगिन:**\\nSuper Admin: 9876543210/admin123\\nRestaurant: 9876543211/rest123\\nCustomer: 9876543212/cust123\\nDelivery: 9876543213/del123")
else:
    # Sidebar
    with st.sidebar:
        st.markdown(f"👤 **{st.session_state.user['name']}**")
        st.markdown(f"📱 {st.session_state.user['phone']}")
        role = st.session_state.user['role']
        if st.button("🚪 लॉगआउट"):
            st.session_state.user = None
            st.rerun()
        
        if st.button("🔄 5 सेकंड रिफ्रेश"):
            auto_refresh()
    
    # Role-based panels
    tab_headers = {
        'superadmin': ['📊 डैशबोर्ड', '🏪 रेस्टोरेंट्स', '🚚 डिलीवरी बॉय', '📋 ऑर्डर्स', '💰 पेमेंट्स'],
        'restaurant': ['🍽️ मेन्यू', '📦 ऑर्डर्स', '💰 सेल्स', '👤 प्रोफाइल'],
        'customer': ['🏠 होम', '🛒 कार्ट', '📱 ऑर्डर हिस्ट्री', '👤 प्रोफाइल'],
        'delivery': ['📦 उपलब्ध ऑर्डर्स', '🚚 एक्टिव डिलीवरी', '💰 कमाई']
    }
    
    tabs = st.tabs(tab_headers.get(role, ['पैनल']))
    
    # SUPER ADMIN PANEL
    if role == 'superadmin':
        with tabs[0]:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                today_orders = pd.read_sql(
                    "SELECT COUNT(*) FROM orders WHERE DATE(created_at)=DATE('now')",
                    conn
                ).iloc[0,0]
                st.markdown(f"""
                <div class="metric-card">
                    <h3>📦 आज के ऑर्डर्स</h3>
                    <h1 style='color:#00D084;'>{today_orders}</h1>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                month_orders = pd.read_sql(
                    "SELECT COUNT(*) FROM orders WHERE strftime('%Y-%m', created_at)=strftime('%Y-%m', 'now')",
                    conn
                ).iloc[0,0]
                st.markdown(f"""
                <div class="metric-card">
                    <h3>📅 महीने के ऑर्डर्स</h3>
                    <h1 style='color:#FF6B35;'>{month_orders}</h1>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                rests = pd.read_sql(
                    "SELECT COUNT(*) FROM restaurants WHERE is_approved=1",
                    conn
                ).iloc[0,0]
                st.markdown(f"""
                <div class="metric-card">
                    <h3>🏪 एक्टिव रेस्टोरेंट्स</h3>
                    <h1 style='color:#00D084;'>{rests}</h1>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                users_count = pd.read_sql(
                    "SELECT COUNT(*) FROM users WHERE role='customer'",
                    conn
                ).iloc[0,0]
                st.markdown(f"""
                <div class="metric-card">
                    <h3>👥 कस्टमर्स</h3>
                    <h1 style='color:#FF6B35;'>{users_count}</h1>
                </div>
                """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                df_orders = pd.read_sql(
                    "SELECT status, COUNT(*) as count FROM orders GROUP BY status",
                    conn
                )
                if not df_orders.empty:
                    fig_pie = px.pie(df_orders, names='status', values='count', title='ऑर्डर स्टेटस')
                    st.plotly_chart(fig_pie, use_container_width=True)
            with col2:
                df_rev = pd.read_sql(
                    "SELECT strftime('%Y-%m', created_at) as month, SUM(total) as revenue FROM orders GROUP BY month ORDER BY month",
                    conn
                )
                if not df_rev.empty:
                    fig_line = px.line(df_rev, x='month', y='revenue', title='रेवेन्यू ट्रेंड')
                    st.plotly_chart(fig_line, use_container_width=True)
        
        with tabs[1]:
            df_rests = pd.read_sql("SELECT * FROM restaurants", conn)
            st.dataframe(df_rests)
            st.subheader("✅ अप्रूव्ड रेस्टोरेंट")
            approved = df_rests[df_rests['is_approved'] == 1]
            st.dataframe(approved)
        
        with tabs[2]:
            df_del = pd.read_sql("SELECT * FROM users WHERE role='delivery'", conn)
            st.dataframe(df_del)
        
        with tabs[3]:
            df_orders = pd.read_sql("SELECT * FROM orders ORDER BY id DESC LIMIT 50", conn)
            st.dataframe(df_orders)
        
        with tabs[4]:
            st.info("💰 पेमेंट मैनेजमेंट - आने वाला फीचर")
    
    # RESTAURANT PANEL
    elif role == 'restaurant':
        rest_df = pd.read_sql(
            "SELECT id, name FROM restaurants WHERE owner_id=? AND is_approved=1",
            conn,
            params=(st.session_state.user['id'],)
        )
        if rest_df.empty:
            st.error("❌ आपका रेस्टोरेंट अभी अप्रूव नहीं है या मौजूद नहीं है।")
            st.stop()
        rest_id = int(rest_df.iloc[0]['id'])
        rest_name = rest_df.iloc[0]['name']
        
        with tabs[0]:
            st.header(f"🍽️ {rest_name} - मेन्यू")
            
            # FIXED FORM BLOCK
            with st.form("add_item"):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("नाम")
                    hindi_name = st.text_input("हिंदी नाम")
                    price = st.number_input("कीमत (₹)", min_value=10.0)
                with col2:
                    uploaded = st.file_uploader("फूड फोटो", type=['jpg', 'png'])
                    available = st.checkbox("उपलब्ध", value=True)
                
                submit_menu = st.form_submit_button("➕ जोड़ें")
                
                if submit_menu:
                    if not name:
                        st.error("नाम ज़रूरी है!")
                    else:
                        img_path = None
                        if uploaded:
                            img_path = save_image(uploaded, f"food_{int(time.time())}.jpg")
                        conn.execute(
                            "INSERT INTO menu_items (restaurant_id, name, hindi_name, price, image_path, is_available) VALUES (?, ?, ?, ?, ?, ?)",
                            (rest_id, name, hindi_name, price, img_path, 1 if available else 0)
                        )
                        conn.commit()
                        st.success("✅ जोड़ा गया!")
                        st.rerun()
            
            df_menu = pd.read_sql(
                "SELECT * FROM menu_items WHERE restaurant_id=? ORDER BY id DESC",
                conn,
                params=(rest_id,)
            )
            st.dataframe(df_menu)
            
            for idx, row in df_menu.iterrows():
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    img = load_image(row['image_path'])
                    if img:
                        st.image(img, width=150, caption=row['name'])
                    else:
                        st.write("🖼️")
                with col2:
                    st.markdown(f"**{row['hindi_name']}**")
                    st.caption(f"₹{row['price']}")
                with col3:
                    if st.button("🗑️ डिलीट", key=f"del_{row['id']}"):
                        conn.execute("DELETE FROM menu_items WHERE id=?", (row['id'],))
                        conn.commit()
                        st.rerun()
        
        with tabs[1]:
            df_orders = pd.read_sql(
                "SELECT * FROM orders WHERE restaurant_id=? ORDER BY id DESC",
                conn,
                params=(rest_id,)
            )
            for idx, order in df_orders.iterrows():
                with st.expander(f"📦 ऑर्डर #{order['id']} - ₹{order['total']} - {order['status']}"):
                    st.json(order['items_json'])
                    status_options = ['pending', 'preparing', 'ready', 'delivered']
                    current = order['status'] if order['status'] in status_options else 'pending'
                    new_status = st.selectbox(
                        "स्टेटस अपडेट",
                        status_options,
                        index=status_options.index(current),
                        key=f"status_{order['id']}"
                    )
                    if st.button("✅ अपडेट", key=f"update_{order['id']}"):
                        conn.execute(
                            "UPDATE orders SET status=? WHERE id=?",
                            (new_status, order['id'])
                        )
                        conn.commit()
                        st.success("✅ अपडेट!")
                        st.rerun()
        
        with tabs[2]:
            df_sales = pd.read_sql(
                "SELECT strftime('%Y-%m-%d', created_at) as date, SUM(total) as revenue FROM orders WHERE restaurant_id=? GROUP BY date",
                conn,
                params=(rest_id,)
            )
            st.dataframe(df_sales)
            if not df_sales.empty:
                fig = px.bar(df_sales, x='date', y='revenue', title="दैनिक सेल्स")
                st.plotly_chart(fig, use_container_width=True)
        
        with tabs[3]:
            st.info("🏪 रेस्टोरेंट प्रोफाइल - आने वाला फीचर")
    
    # CUSTOMER PANEL
    elif role == 'customer':
        with tabs[0]:
            st.header("🔥 वेलकम होम!")
            
            banners = ["50% ऑफ फर्स्ट ऑर्डर!", "फ्री डिलीवरी ऑन 3+ आइटम्स", "बिरयानी @ ₹99"]
            selected_banner = random.choice(banners)
            st.markdown(f"""
            <div class="metric-card" style='text-align:center; font-size:2rem; color:white;'>
                🎉 {selected_banner} 🎉
            </div>
            """, unsafe_allow_html=True)
            
            st.subheader("🏪 पॉपुलर रेस्टोरेंट्स")
            cols = st.columns(3)
            rest_samples = [
                {'name': 'Biryani House', 'rating': 4.5, 'time': '25 मिनट', 'offer': '20% ऑफ'},
                {'name': 'Pizza Corner', 'rating': 4.2, 'time': '30 मिनट', 'offer': '₹50 ऑफ'},
                {'name': 'Chai Sutta', 'rating': 4.8, 'time': '15 मिनट', 'offer': 'BOGO'}
            ]
            for i, rest in enumerate(rest_samples):
                with cols[i]:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>{rest['name']}</h3>
                        <p>⭐ {rest['rating']} | ⏱️ {rest['time']}</p>
                        <p style='color:#FF6B35; font-weight:bold;'>{rest['offer']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.subheader("🍕 ट्रेंडिंग फूड")
            food_samples = [
                ('Chicken Biryani', 'मुर्गा बिरयानी', 250),
                ('Pizza', 'पिज्जा', 320),
                ('Chai', 'चाय', 20)
            ]
            for food in food_samples:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{food[0]}** - {food[1]} - ₹{food[2]}")
                with col2:
                    if st.button("➕", key=f"add_{food[0]}"):
                        st.session_state.cart.append({'name': food[0], 'price': food[2], 'qty': 1})
                        st.rerun()
        
        with tabs[1]:
            if st.session_state.cart:
                st.subheader("🛒 शॉपिंग कार्ट")
                total = 0
                for item in st.session_state.cart:
                    st.write(f"{item['name']} x{item['qty']} - ₹{item['price'] * item['qty']}")
                    total += item['price'] * item['qty']
                
                st.markdown(f"**ग्रैंड टोटल: ₹{total}**")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ क्लियर कार्ट"):
                        st.session_state.cart = []
                        st.rerun()
                with col2:
                    if st.button("💳 चेकआउट"):
                        tracking = f'TRACK{random.randint(1000, 9999)}'
                        conn.execute(
                            "INSERT INTO orders (customer_id, restaurant_id, items_json, total, tracking_id) VALUES (?, ?, ?, ?, ?)",
                            (st.session_state.user['id'], 1, str(st.session_state.cart), total, tracking)
                        )
                        conn.commit()
                        st.success(f"✅ ऑर्डर प्लेस! ट्रैकिंग: {tracking}")
                        st.session_state.cart = []
                        st.rerun()
            else:
                st.info("🛒 आपका कार्ट खाली है!")
        
        with tabs[2]:
            df_myorders = pd.read_sql(
                "SELECT * FROM orders WHERE customer_id=? ORDER BY id DESC",
                conn,
                params=(st.session_state.user['id'],)
            )
            st.dataframe(df_myorders)
        
        with tabs[3]:
            st.info("👤 प्रोफाइल - एड्रेस मैनेजमेंट आने वाला")
    
    # DELIVERY PANEL
    elif role == 'delivery':
        with tabs[0]:
            df_avail = pd.read_sql(
                "SELECT * FROM orders WHERE delivery_id IS NULL AND status='ready' ORDER BY id DESC LIMIT 10",
                conn
            )
            if df_avail.empty:
                st.info("📦 अभी कोई ready ऑर्डर नहीं है।")
            for idx, order in df_avail.iterrows():
                with st.expander(f"📦 ऑर्डर #{order['id']} - ₹{order['total']}"):
                    st.json(order['items_json'])
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ एक्सेप्ट", key=f"accept_{order['id']}"):
                            conn.execute(
                                "UPDATE orders SET delivery_id=? WHERE id=?",
                                (st.session_state.user['id'], order['id'])
                            )
                            conn.commit()
                            st.success("✅ एक्सेप्टेड!")
                            st.rerun()
                    with col2:
                        st.caption("❌ रिजेक्ट (dummy)")
        
        with tabs[1]:
            df_active = pd.read_sql(
                """
                SELECT o.*, u.name as cust_name 
                FROM orders o 
                JOIN users u ON o.customer_id=u.id 
                WHERE o.delivery_id = ? AND o.status != 'delivered'
                """,
                conn,
                params=(st.session_state.user['id'],)
            )
            if df_active.empty:
                st.info("🚚 कोई एक्टिव डिलीवरी नहीं है।")
            for idx, order in df_active.iterrows():
                st.markdown(f"""
                <div class="metric-card">
                    <h3>📦 ऑर्डर #{order['id']} - {order['cust_name']}</h3>
                    <p>📱 9876******123 (मास्क्ड)</p>
                    <p>💰 ₹{order['total']}</p>
                    <p>📍 रेस्टोरेंट → कस्टमर (20km, ETA 25min)</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("📞 कॉल", key=f"call_{order['id']}"):
                        st.info("📞 कॉल सिमुलेशन - 9876******123")
                with col2:
                    if st.button("✅ डिलीवर", key=f"delivered_{order['id']}"):
                        conn.execute(
                            "UPDATE orders SET status='delivered' WHERE id=?",
                            (order['id'],)
                        )
                        conn.commit()
                        st.rerun()
                with col3:
                    fig = go.Figure(go.Scattermapbox(
                        lat=[26.4499, 26.4499],
                        lon=[80.3319, 80.3319],
                        mode='markers',
                        marker=go.scattermapbox.Marker(size=12, color=['green', 'red'])
                    ))
                    fig.update_layout(mapbox_style="open-street-map", mapbox=dict(zoom=10))
                    st.plotly_chart(fig, use_container_width=True, key=f"del_map_{order['id']}")
        
        with tabs[2]:
            earnings_df = pd.read_sql(
                """
                SELECT 
                    COUNT(*) as deliveries,
                    COALESCE(SUM(total*0.2), 0) as earnings
                FROM orders 
                WHERE delivery_id=? AND status='delivered'
                """,
                conn,
                params=(st.session_state.user['id'],)
            )
            if not earnings_df.empty:
                earnings = earnings_df.iloc[0]
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("🚚 कुल कमाई", f"₹{int(earnings['earnings'])}")
                with col2:
                    st.metric("📦 टोटल डिलीवरी", int(earnings['deliveries']))

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:rgba(255,255,255,0.8);'>🍕 Foodees - Sikariganj का सबसे तेज डिलीवरी ऐप | Made with ❤️ by foodees</p>",
    unsafe_allow_html=True
)
