import streamlit as st
import psycopg2
import pandas as pd
import os
import requests
import time
from datetime import datetime

# --- 1. הגדרות ---
st.set_page_config(page_title="ניהול מכולת - הזוג", page_icon="🛒", layout="wide", initial_sidebar_state="collapsed")

# משתני סביבה
DB_URL = os.environ.get("DB_URL")
BOT_URL = "https://minimarket-ocfq.onrender.com" 
INTERNAL_SECRET = os.environ.get("INTERNAL_SECRET", "123")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "12345")

# --- 2. עיצוב כהה (Dark Mode) משופר ---
st.markdown("""
    <style>
    /* רקע ראשי כהה */
    .stApp {
        background-color: #1a1a2e;
        color: #e0e0e0;
    }
    
    /* כותרות */
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 700;
    }
    
    /* טבלאות וכרטיסים */
    div[data-testid="stDataFrame"], div[data-testid="stMetric"] {
        background-color: #252540;
        border: 1px solid #303050;
        border-radius: 10px;
        padding: 10px;
    }
    
    /* טקסט בתוך טבלה */
    div[data-testid="stDataFrame"] p {
        color: white;
    }
    
    /* כפתורים */
    .stButton>button {
        background-color: #ff6b6b;
        color: white;
        border: none;
        border-radius: 8px;
        transition: 0.3s;
        font-weight: 600;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #ff4757;
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(255, 107, 107, 0.4);
    }
    
    /* שדות קלט - עיצוב משופר לקריאות */
    .stTextInput>div>div>input, 
    .stSelectbox>div>div>select,
    .stNumberInput>div>div>input {
        background-color: #303050 !important;
        color: #ffffff !important;
        border: 2px solid #404060 !important;
        border-radius: 8px !important;
        padding: 10px !important;
        font-size: 16px !important;
    }
    
    .stTextInput>div>div>input:focus,
    .stSelectbox>div>div>select:focus,
    .stNumberInput>div>div>input:focus {
        border-color: #ff6b6b !important;
        box-shadow: 0 0 0 2px rgba(255, 107, 107, 0.2) !important;
    }
    
    /* תוויות של שדות */
    .stTextInput>label, 
    .stSelectbox>label,
    .stNumberInput>label {
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        margin-bottom: 8px !important;
    }
    
    /* תיבת התחברות */
    .login-box {
        background: #252540;
        padding: 40px;
        border-radius: 15px;
        text-align: center;
        border: 1px solid #404060;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    
    /* התראת הזמנה חדשה */
    .new-order-alert {
        background: linear-gradient(135deg, #ff6b6b 0%, #ff4757 100%);
        color: white;
        padding: 20px 30px;
        border-radius: 12px;
        text-align: center;
        font-size: 24px;
        font-weight: 700;
        margin: 20px 0;
        animation: pulse 2s infinite;
        box-shadow: 0 4px 20px rgba(255, 107, 107, 0.5);
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.02); }
    }
    
    /* כרטיס הזמנה */
    .order-card {
        background: #2d2d44;
        border: 2px solid #404060;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
    }
    
    .order-card h3 {
        color: #ff6b6b !important;
        margin-bottom: 15px;
    }
    
    /* אזור פעולות */
    .action-section {
        background: #252540;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    
    /* Tabs עיצוב */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #252540;
        padding: 10px;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #303050;
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #ff6b6b;
    }
    
    /* Data Editor */
    .stDataFrame input {
        background-color: #303050 !important;
        color: white !important;
        border: 1px solid #404060 !important;
    }
    
    /* כפתור רענון מיוחד */
    .refresh-btn button {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%) !important;
    }
    
    .refresh-btn button:hover {
        background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%) !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. פונקציות עזר ---
def get_db_connection():
    return psycopg2.connect(DB_URL)

def extract_phone_id(address_field):
    """חילוץ חכם של מזהה הוואטסאפ מהכתובת"""
    try:
        if "WA_ID:" in str(address_field):
            return str(address_field).split("WA_ID:")[-1].strip()
        
        clean = str(address_field).replace("WhatsApp:", "").replace("טלפון:", "").replace("-", "").strip()
        if ":" in clean: clean = clean.split(":")[-1].strip()
        if clean.startswith("0"): clean = "972" + clean[1:]
        return clean
    except:
        return None

def notify_customer(full_address_field, message):
    """שליחת הודעה ללקוח"""
    try:
        phone_id = extract_phone_id(full_address_field)
        
        if not phone_id:
            st.error("לא הצלחתי לחלץ מספר טלפון מההזמנה")
            return False
            
        response = requests.post(
            f"{BOT_URL}/send_update", 
            json={"phone": phone_id, "message": message},
            headers={"X-Internal-Secret": INTERNAL_SECRET},
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"שגיאת תקשורת: {e}")
        return False

def check_new_orders():
    """בדיקה אם יש הזמנות חדשות"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM orders WHERE status = 'ממתין לאישור'")
        count = cur.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

# --- 4. התחברות ---
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False
if 'last_order_count' not in st.session_state:
    st.session_state.last_order_count = 0

if not st.session_state.logged_in:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<div class='login-box'><h2>🔐 כניסה למנהל</h2></div>", unsafe_allow_html=True)
        pwd = st.text_input("סיסמה", type="password", key="login_pwd")
        if st.button("כניסה", use_container_width=True):
            if pwd == ADMIN_PASSWORD: 
                st.session_state.logged_in = True
                st.rerun()
            else: 
                st.error("סיסמה שגויה")
    st.stop()

# --- 5. ממשק ראשי ---
st.title("🛒 ניהול מכולת - ממשק כהה")

# כפתור התנתקות
col_logout1, col_logout2 = st.columns([6, 1])
with col_logout2:
    if st.button("🚪 התנתק"): 
        st.session_state.logged_in = False
        st.rerun()

# בדיקת הזמנות חדשות
current_order_count = check_new_orders()

# התראה על הזמנה חדשה
if current_order_count > st.session_state.last_order_count and st.session_state.last_order_count > 0:
    st.markdown(f"""
        <div class='new-order-alert'>
            🔔 נכנסה הזמנה חדשה! ({current_order_count} הזמנות ממתינות)
        </div>
    """, unsafe_allow_html=True)
    st.balloons()

st.session_state.last_order_count = current_order_count

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📦 הזמנות לטיפול", "✅ היסטוריה", "❌ מבוטלות", "🏪 מלאי"])

# --- טאב 1: הזמנות לטיפול ---
with tab1:
    col_header1, col_header2 = st.columns([3, 1])
    
    with col_header1:
        st.subheader(f"הזמנות חדשות ({current_order_count})")
    
    with col_header2:
        st.markdown("<div class='refresh-btn'>", unsafe_allow_html=True)
        if st.button("🔄 רענן עכשיו", use_container_width=True): 
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    conn = get_db_connection()
    pending_df = pd.read_sql(
        "SELECT id, customer_name, items, address, created_at FROM orders WHERE status = 'ממתין לאישור' ORDER BY created_at DESC", 
        conn
    )
    conn.close()

    if not pending_df.empty:
        # הצגת הטבלה
        st.dataframe(
            pending_df,
            use_container_width=True,
            column_config={
                "id": st.column_config.NumberColumn("מס'", format="%d"),
                "customer_name": "לקוח",
                "items": "מוצרים",
                "address": "פרטים וטלפון",
                "created_at": st.column_config.DatetimeColumn("שעה", format="HH:mm DD/MM")
            },
            hide_index=True
        )
        
        st.divider()
        
        # אזור פעולות
        st.markdown("<div class='action-section'>", unsafe_allow_html=True)
        st.markdown("### 🎯 פעולות על הזמנה")
        
        # בחירת הזמנה
        oid = st.selectbox(
            "בחר הזמנה לטיפול:", 
            pending_df['id'].tolist(),
            format_func=lambda x: f"הזמנה #{x} - {pending_df[pending_df['id']==x].iloc[0]['customer_name']}"
        )
        
        row = pending_df[pending_df['id'] == oid].iloc[0]
        
        # כרטיס פרטי הזמנה
        st.markdown(f"""
            <div class='order-card'>
                <h3>📋 פרטי הזמנה #{oid}</h3>
                <p><strong>👤 לקוח:</strong> {row['customer_name']}</p>
                <p><strong>🛒 מוצרים:</strong> {row['items']}</p>
                <p><strong>📍 פרטים:</strong> {row['address']}</p>
                <p><strong>🕐 נכנסה:</strong> {row['created_at'].strftime('%H:%M:%S')}</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # פעולות - אישור וביטול
        c_app, c_can = st.columns(2)
        
        # אישור
        with c_app:
            st.success("### ✅ אישור הזמנה")
            time_est = st.text_input(
                "זמן הגעה משוער:", 
                value="20 דקות",
                key=f"time_est_{oid}",
                help="למשל: 20 דקות, חצי שעה, 45 דקות"
            )
            
            if st.button("✅ אשר ושלח וואטסאפ", use_container_width=True, type="primary"):
                if time_est:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE orders SET status='אושר', delivery_time=%s, approved_at=NOW() WHERE id=%s", 
                        (time_est, int(oid))
                    )
                    conn.commit()
                    conn.close()
                    
                    msg = f"היי {row['customer_name']}! ההזמנה (#{oid}) אושרה ✅\n🛒 מוצרים: {row['items']}\n🛵 זמן הגעה משוער: {time_est}.\nתודה!"
                    
                    if notify_customer(row['address'], msg):
                        st.success("✅ ההזמנה אושרה והודעה נשלחה ללקוח!")
                    else:
                        st.warning("⚠️ ההזמנה אושרה, אך ההודעה נכשלה.")
                    
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("אנא הזן זמן הגעה משוער")
        
        # ביטול
        with c_can:
            st.error("### ❌ ביטול הזמנה")
            
            reason = st.selectbox(
                "סיבת הביטול:", 
                ["חוסר במלאי", "כתובת שגויה", "לקוח לא זמין", "אחר"],
                key=f"reason_{oid}"
            )
            
            custom_reason = ""
            if reason == "אחר":
                custom_reason = st.text_input(
                    "פרט את הסיבה:", 
                    key=f"custom_reason_{oid}",
                    help="הסבר קצר ללקוח"
                )
            
            final_reason = custom_reason if reason == "אחר" else reason
            
            if st.button("❌ בטל הזמנה", use_container_width=True, type="secondary"):
                if final_reason:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE orders SET status='בוטל', cancellation_reason=%s WHERE id=%s", 
                        (final_reason, int(oid))
                    )
                    conn.commit()
                    conn.close()
                    
                    msg = f"היי {row['customer_name']}, ההזמנה (#{oid}) בוטלה ❌\nסיבה: {final_reason}.\nמצטערים על אי הנוחות."
                    notify_customer(row['address'], msg)
                    
                    st.error("❌ ההזמנה בוטלה והלקוח קיבל הודעה.")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("אנא הזן סיבת ביטול")
    else:
        st.markdown("""
            <div style='text-align: center; padding: 60px 20px; background: #252540; border-radius: 15px;'>
                <h2 style='color: #4facfe;'>🎉 אין הזמנות חדשות</h2>
                <p style='font-size: 18px; color: #a0a0a0;'>הכל טופל! ניתן לנוח רגע 😊</p>
            </div>
        """, unsafe_allow_html=True)

# --- טאב 2: היסטוריה ---
with tab2:
    st.subheader("📜 הזמנות שאושרו")
    conn = get_db_connection()
    approved_df = pd.read_sql(
        "SELECT id, customer_name, items, delivery_time, approved_at FROM orders WHERE status='אושר' ORDER BY approved_at DESC LIMIT 20", 
        conn
    )
    conn.close()
    
    if not approved_df.empty:
        st.dataframe(
            approved_df, 
            use_container_width=True,
            column_config={
                "id": st.column_config.NumberColumn("מס'", format="%d"),
                "customer_name": "לקוח",
                "items": "מוצרים",
                "delivery_time": "זמן משלוח",
                "approved_at": st.column_config.DatetimeColumn("אושר בשעה", format="DD/MM/YYYY HH:mm")
            },
            hide_index=True
        )
    else:
        st.info("אין עדיין הזמנות שאושרו")

# --- טאב 3: מבוטלות ---
with tab3:
    st.subheader("🚫 הזמנות מבוטלות")
    conn = get_db_connection()
    cancelled_df = pd.read_sql(
        "SELECT id, customer_name, items, cancellation_reason, created_at FROM orders WHERE status='בוטל' ORDER BY created_at DESC LIMIT 20", 
        conn
    )
    conn.close()
    
    if not cancelled_df.empty:
        st.dataframe(
            cancelled_df, 
            use_container_width=True,
            column_config={
                "id": st.column_config.NumberColumn("מס'", format="%d"),
                "customer_name": "לקוח",
                "items": "מוצרים",
                "cancellation_reason": "סיבת ביטול",
                "created_at": st.column_config.DatetimeColumn("תאריך", format="DD/MM/YYYY HH:mm")
            },
            hide_index=True
        )
    else:
        st.info("אין הזמנות מבוטלות")

# --- טאב 4: מלאי ---
with tab4:
    st.subheader("📦 ניהול מוצרים ומלאי")
    
    conn = get_db_connection()
    df_p = pd.read_sql("SELECT id, name, price, stock FROM products ORDER BY name", conn)
    conn.close()
    
    st.info("💡 ניתן לערוך ישירות בטבלה - שם, מחיר, מלאי")
    
    edited = st.data_editor(
        df_p, 
        num_rows="dynamic", 
        key="edit_inv",
        use_container_width=True,
        column_config={
            "id": st.column_config.NumberColumn("מס'", disabled=True),
            "name": st.column_config.TextColumn("שם מוצר", required=True),
            "price": st.column_config.NumberColumn("מחיר (₪)", format="%.2f", required=True),
            "stock": st.column_config.NumberColumn("מלאי", format="%d", required=True)
        }
    )
    
    if st.button("💾 שמור שינויים במלאי", type="primary", use_container_width=True):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            for i, r in edited.iterrows():
                if pd.notna(r['id']):  # רק עדכון של שורות קיימות
                    cur.execute(
                        "UPDATE products SET name=%s, price=%s, stock=%s WHERE id=%s", 
                        (r['name'], float(r['price']), int(r['stock']), int(r['id']))
                    )
            conn.commit()
            conn.close()
            st.success("✅ השינויים נשמרו בהצלחה!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"❌ שגיאה בשמירה: {e}")

# --- רענון אוטומטי (אופציונלי) ---
# הסר את ההערה אם אתה רוצה רענון אוטומטי כל 30 שניות
# time.sleep(30)
# st.rerun()
