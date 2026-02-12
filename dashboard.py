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

# --- 2. עיצוב מודרני ונגיש ---
st.markdown("""
    <style>
    /* רקע מודרני עם גרדיאנט עדין */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: #e0e0e0;
    }
    
    /* כותרות מעוצבות */
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 700;
        text-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }
    
    /* טבלאות מודרניות */
    div[data-testid="stDataFrame"] {
        background: linear-gradient(135deg, #252540 0%, #2d2d44 100%);
        border: 1px solid #404060;
        border-radius: 15px;
        padding: 15px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    
    /* טקסט בטבלה */
    div[data-testid="stDataFrame"] p {
        color: white;
    }
    
    /* כפתורים ראשיים - גרדיאנט מרשים */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        transition: all 0.3s ease;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        font-size: 16px;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    
    /* כפתור אישור - ירוק */
    .approve-btn button {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%) !important;
        box-shadow: 0 4px 15px rgba(56, 239, 125, 0.4) !important;
    }
    .approve-btn button:hover {
        background: linear-gradient(135deg, #38ef7d 0%, #11998e 100%) !important;
        box-shadow: 0 6px 20px rgba(56, 239, 125, 0.6) !important;
    }
    
    /* כפתור ביטול - אדום */
    .cancel-btn button {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%) !important;
        box-shadow: 0 4px 15px rgba(235, 51, 73, 0.4) !important;
    }
    .cancel-btn button:hover {
        background: linear-gradient(135deg, #f45c43 0%, #eb3349 100%) !important;
        box-shadow: 0 6px 20px rgba(235, 51, 73, 0.6) !important;
    }
    
    /* כפתור מחיקה - כתום */
    .delete-btn button {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important;
        box-shadow: 0 4px 15px rgba(245, 87, 108, 0.4) !important;
        font-size: 14px !important;
        padding: 0.5rem 1rem !important;
    }
    .delete-btn button:hover {
        background: linear-gradient(135deg, #f5576c 0%, #f093fb 100%) !important;
        box-shadow: 0 6px 20px rgba(245, 87, 108, 0.6) !important;
    }
    
    /* כפתור רענון - כחול */
    .refresh-btn button {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%) !important;
        box-shadow: 0 4px 15px rgba(79, 172, 254, 0.4) !important;
    }
    .refresh-btn button:hover {
        background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%) !important;
        box-shadow: 0 6px 20px rgba(79, 172, 254, 0.6) !important;
    }
    
    /* שדות קלט מודרניים */
    .stTextInput>div>div>input, 
    .stSelectbox>div>div>select,
    .stNumberInput>div>div>input {
        background-color: #2d2d44 !important;
        color: #ffffff !important;
        border: 2px solid #404060 !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput>div>div>input:focus,
    .stSelectbox>div>div>select:focus,
    .stNumberInput>div>div>input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2) !important;
        background-color: #353555 !important;
    }
    
    /* תוויות שדות */
    .stTextInput>label, 
    .stSelectbox>label,
    .stNumberInput>label {
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        margin-bottom: 8px !important;
    }
    
    /* תיבת התחברות מעוצבת */
    .login-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 50px;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 20px 60px rgba(102, 126, 234, 0.4);
    }
    
    /* התראת הזמנה חדשה - אנימציה מרשימה */
    .new-order-alert {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 25px 40px;
        border-radius: 15px;
        text-align: center;
        font-size: 26px;
        font-weight: 700;
        margin: 25px 0;
        animation: pulse 1.5s ease-in-out infinite;
        box-shadow: 0 8px 30px rgba(245, 87, 108, 0.5);
    }
    
    @keyframes pulse {
        0%, 100% { 
            transform: scale(1); 
            box-shadow: 0 8px 30px rgba(245, 87, 108, 0.5);
        }
        50% { 
            transform: scale(1.03); 
            box-shadow: 0 12px 40px rgba(245, 87, 108, 0.7);
        }
    }
    
    /* כרטיס הזמנה מודרני */
    .order-card {
        background: linear-gradient(135deg, #2d2d44 0%, #3a3a5a 100%);
        border: 2px solid #505070;
        border-radius: 15px;
        padding: 25px;
        margin: 20px 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
    }
    
    .order-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 35px rgba(0,0,0,0.4);
    }
    
    .order-card h3 {
        color: #667eea !important;
        margin-bottom: 20px;
        font-size: 22px;
    }
    
    .order-card p {
        margin: 12px 0;
        font-size: 16px;
        line-height: 1.6;
    }
    
    /* אזור פעולות */
    .action-section {
        background: linear-gradient(135deg, #252540 0%, #2d2d50 100%);
        border-radius: 15px;
        padding: 30px;
        margin: 20px 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.2);
    }
    
    /* Tabs מעוצבים */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: linear-gradient(135deg, #252540 0%, #2d2d50 100%);
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #353555;
        color: white;
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
        border: 2px solid transparent;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #404070;
        border-color: #667eea;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-color: #667eea;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* הודעות מערכת מעוצבות */
    .stSuccess {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        border-radius: 10px;
        padding: 15px;
        border: none;
    }
    
    .stError {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        border-radius: 10px;
        padding: 15px;
        border: none;
    }
    
    .stInfo {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        border-radius: 10px;
        padding: 15px;
        border: none;
    }
    
    /* כרטיסי מטריקה */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }
    
    /* חוצץ מעוצב */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
        margin: 30px 0;
    }
    
    /* אזור ריק מעוצב */
    .empty-state {
        text-align: center;
        padding: 80px 40px;
        background: linear-gradient(135deg, #252540 0%, #2d2d50 100%);
        border-radius: 20px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.2);
    }
    
    .empty-state h2 {
        color: #4facfe !important;
        font-size: 32px;
        margin-bottom: 15px;
    }
    
    .empty-state p {
        font-size: 20px;
        color: #a0a0c0;
    }
    
    /* כפתור קטן בתוך כרטיס */
    .inline-delete-btn button {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important;
        padding: 8px 16px !important;
        font-size: 13px !important;
        border-radius: 8px !important;
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

def delete_order(order_id):
    """מחיקת הזמנה מהמערכת"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM orders WHERE id = %s", (int(order_id),))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"שגיאה במחיקה: {e}")
        return False

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
st.title("🛒 מערכת ניהול מכולת מתקדמת")

# כפתורי ניווט עליונים
col_header1, col_header2, col_header3 = st.columns([5, 2, 1])

with col_header2:
    st.markdown("<div class='refresh-btn'>", unsafe_allow_html=True)
    if st.button("🔄 רענן נתונים", use_container_width=True, key="top_refresh"): 
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with col_header3:
    if st.button("🚪 התנתק", use_container_width=True): 
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
    st.markdown(f"### 📦 הזמנות חדשות - {current_order_count} ממתינות")
    
    conn = get_db_connection()
    pending_df = pd.read_sql(
        "SELECT id, customer_name, items, address, created_at FROM orders WHERE status = 'ממתין לאישור' ORDER BY created_at DESC", 
        conn
    )
    conn.close()

    if not pending_df.empty:
        # לולאה על כל הזמנה - כל הזמנה בכרטיס משלה
        for idx, row in pending_df.iterrows():
            oid = row['id']
            
            # כרטיס הזמנה עם פרטים וכפתורי פעולה
            st.markdown(f"""
                <div class='order-card'>
                    <h3>📋 הזמנה #{oid}</h3>
                    <p><strong>👤 לקוח:</strong> {row['customer_name']}</p>
                    <p><strong>🛒 מוצרים:</strong> {row['items']}</p>
                    <p><strong>📍 פרטים:</strong> {row['address']}</p>
                    <p><strong>🕐 נכנסה:</strong> {row['created_at'].strftime('%d/%m/%Y %H:%M:%S')}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # שורת פעולות עבור ההזמנה הזו
            col_time, col_approve, col_cancel, col_delete = st.columns([2, 2, 2, 1])
            
            with col_time:
                time_est = st.text_input(
                    "⏱️ זמן הגעה", 
                    value="20 דקות",
                    key=f"time_{oid}",
                    label_visibility="collapsed",
                    placeholder="לדוגמה: 20 דקות"
                )
            
            with col_approve:
                st.markdown("<div class='approve-btn'>", unsafe_allow_html=True)
                if st.button("✅ אשר ושלח", use_container_width=True, key=f"approve_{oid}"):
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
                            st.success("✅ ההזמנה אושרה!")
                        else:
                            st.warning("⚠️ ההזמנה אושרה, אך ההודעה נכשלה.")
                        
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("הזן זמן הגעה")
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col_cancel:
                st.markdown("<div class='cancel-btn'>", unsafe_allow_html=True)
                if st.button("❌ בטל", use_container_width=True, key=f"cancel_{oid}"):
                    st.session_state[f'show_cancel_{oid}'] = True
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col_delete:
                st.markdown("<div class='delete-btn'>", unsafe_allow_html=True)
                if st.button("🗑️", use_container_width=True, key=f"delete_{oid}", help="מחק הזמנה"):
                    if delete_order(oid):
                        st.success(f"🗑️ הזמנה #{oid} נמחקה")
                        time.sleep(1)
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            
            # תיבת ביטול מורחבת (אם נלחץ על כפתור ביטול)
            if st.session_state.get(f'show_cancel_{oid}', False):
                with st.container():
                    st.markdown("---")
                    st.markdown("#### 🔴 ביטול הזמנה")
                    
                    col_reason, col_confirm = st.columns([3, 1])
                    
                    with col_reason:
                        reason = st.selectbox(
                            "סיבת הביטול:", 
                            ["חוסר במלאי", "כתובת שגויה", "לקוח לא זמין", "אחר"],
                            key=f"reason_select_{oid}"
                        )
                        
                        if reason == "אחר":
                            custom_reason = st.text_input(
                                "פרט את הסיבה:", 
                                key=f"custom_reason_{oid}",
                                placeholder="הסבר קצר ללקוח"
                            )
                            final_reason = custom_reason if custom_reason else "לא צוינה סיבה"
                        else:
                            final_reason = reason
                    
                    with col_confirm:
                        st.markdown("<div class='cancel-btn'>", unsafe_allow_html=True)
                        if st.button("אשר ביטול", key=f"confirm_cancel_{oid}", use_container_width=True):
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
                            
                            st.error("❌ ההזמנה בוטלה")
                            st.session_state[f'show_cancel_{oid}'] = False
                            time.sleep(1.5)
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("---")
    else:
        st.markdown("""
            <div class='empty-state'>
                <h2>🎉 כל הכבוד!</h2>
                <p>אין הזמנות חדשות כרגע. הכל טופל! 😊</p>
            </div>
        """, unsafe_allow_html=True)

# --- טאב 2: היסטוריה ---
with tab2:
    st.markdown("### ✅ הזמנות שאושרו")
    
    conn = get_db_connection()
    approved_df = pd.read_sql(
        "SELECT id, customer_name, items, delivery_time, approved_at FROM orders WHERE status='אושר' ORDER BY approved_at DESC LIMIT 50", 
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
        
        st.markdown("---")
        st.markdown("#### 🗑️ מחיקת הזמנות מאושרות")
        
        # בחירת הזמנה למחיקה
        col_select, col_delete_btn = st.columns([3, 1])
        
        with col_select:
            delete_id = st.selectbox(
                "בחר הזמנה למחיקה:",
                approved_df['id'].tolist(),
                format_func=lambda x: f"הזמנה #{x} - {approved_df[approved_df['id']==x].iloc[0]['customer_name']} - {approved_df[approved_df['id']==x].iloc[0]['approved_at'].strftime('%d/%m %H:%M')}"
            )
        
        with col_delete_btn:
            st.markdown("<div class='delete-btn'>", unsafe_allow_html=True)
            if st.button("🗑️ מחק הזמנה", use_container_width=True, key="delete_approved"):
                if delete_order(delete_id):
                    st.success(f"🗑️ הזמנה #{delete_id} נמחקה מההיסטוריה")
                    time.sleep(1.5)
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        
    else:
        st.markdown("""
            <div class='empty-state'>
                <h2>📋 אין עדיין היסטוריה</h2>
                <p>הזמנות שאושרו יופיעו כאן</p>
            </div>
        """, unsafe_allow_html=True)

# --- טאב 3: מבוטלות ---
with tab3:
    st.markdown("### ❌ הזמנות מבוטלות")
    
    conn = get_db_connection()
    cancelled_df = pd.read_sql(
        "SELECT id, customer_name, items, cancellation_reason, created_at FROM orders WHERE status='בוטל' ORDER BY created_at DESC LIMIT 50", 
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
        
        st.markdown("---")
        st.markdown("#### 🗑️ מחיקת הזמנות מבוטלות")
        
        # בחירת הזמנה למחיקה
        col_select_c, col_delete_btn_c = st.columns([3, 1])
        
        with col_select_c:
            delete_id_c = st.selectbox(
                "בחר הזמנה למחיקה:",
                cancelled_df['id'].tolist(),
                format_func=lambda x: f"הזמנה #{x} - {cancelled_df[cancelled_df['id']==x].iloc[0]['customer_name']} - {cancelled_df[cancelled_df['id']==x].iloc[0]['cancellation_reason']}"
            )
        
        with col_delete_btn_c:
            st.markdown("<div class='delete-btn'>", unsafe_allow_html=True)
            if st.button("🗑️ מחק לצמיתות", use_container_width=True, key="delete_cancelled"):
                if delete_order(delete_id_c):
                    st.success(f"🗑️ הזמנה #{delete_id_c} נמחקה לצמיתות")
                    time.sleep(1.5)
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class='empty-state'>
                <h2>✨ אין הזמנות מבוטלות</h2>
                <p>כל ההזמנות מטופלות כראוי 👍</p>
            </div>
        """, unsafe_allow_html=True)

# --- טאב 4: מלאי ---
with tab4:
    st.markdown("### 📦 ניהול מוצרים ומלאי")
    
    # תת-טאבים: רשימת מוצרים | הוספת מוצר חדש
    subtab1, subtab2 = st.tabs(["📋 רשימת מוצרים", "➕ הוסף מוצר חדש"])
    
    # תת-טאב 1: רשימת מוצרים
    with subtab1:
        conn = get_db_connection()
        df_p = pd.read_sql("SELECT id, name, price, stock FROM products ORDER BY name", conn)
        conn.close()
        
        if not df_p.empty:
            # הצגת כל מוצר בכרטיס עם אפשרות עריכה ומחיקה
            st.markdown("#### 🛍️ המוצרים שלך")
            
            for idx, product in df_p.iterrows():
                pid = product['id']
                
                # כרטיס מוצר
                with st.container():
                    st.markdown(f"""
                        <div class='order-card' style='margin: 15px 0;'>
                            <h3 style='color: #667eea !important;'>{product['name']}</h3>
                            <p><strong>💰 מחיר:</strong> ₪{product['price']:.2f}</p>
                            <p><strong>📦 מלאי:</strong> {product['stock']} יחידות</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # שורת פעולות
                    col_edit_name, col_edit_price, col_edit_stock, col_save, col_delete = st.columns([2, 1.5, 1.5, 1, 1])
                    
                    with col_edit_name:
                        new_name = st.text_input(
                            "שם המוצר",
                            value=product['name'],
                            key=f"name_{pid}",
                            label_visibility="collapsed",
                            placeholder="שם מוצר"
                        )
                    
                    with col_edit_price:
                        new_price = st.number_input(
                            "מחיר",
                            value=float(product['price']),
                            min_value=0.0,
                            step=0.5,
                            key=f"price_{pid}",
                            label_visibility="collapsed",
                            format="%.2f"
                        )
                    
                    with col_edit_stock:
                        new_stock = st.number_input(
                            "מלאי",
                            value=int(product['stock']),
                            min_value=0,
                            step=1,
                            key=f"stock_{pid}",
                            label_visibility="collapsed"
                        )
                    
                    with col_save:
                        st.markdown("<div class='approve-btn'>", unsafe_allow_html=True)
                        if st.button("💾", key=f"save_{pid}", use_container_width=True, help="שמור שינויים"):
                            try:
                                conn = get_db_connection()
                                cur = conn.cursor()
                                cur.execute(
                                    "UPDATE products SET name=%s, price=%s, stock=%s WHERE id=%s",
                                    (new_name, new_price, new_stock, pid)
                                )
                                conn.commit()
                                conn.close()
                                st.success(f"✅ המוצר '{new_name}' עודכן!")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ שגיאה: {e}")
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    with col_delete:
                        st.markdown("<div class='delete-btn'>", unsafe_allow_html=True)
                        if st.button("🗑️", key=f"del_{pid}", use_container_width=True, help="מחק מוצר"):
                            try:
                                conn = get_db_connection()
                                cur = conn.cursor()
                                cur.execute("DELETE FROM products WHERE id=%s", (pid,))
                                conn.commit()
                                conn.close()
                                st.success(f"🗑️ המוצר '{product['name']}' נמחק!")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ שגיאה במחיקה: {e}")
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    st.markdown("---")
        else:
            st.markdown("""
                <div class='empty-state'>
                    <h2>📦 אין מוצרים במלאי</h2>
                    <p>לחץ על 'הוסף מוצר חדש' כדי להתחיל</p>
                </div>
            """, unsafe_allow_html=True)
    
    # תת-טאב 2: הוספת מוצר חדש
    with subtab2:
        st.markdown("#### ➕ הוסף מוצר חדש למלאי")
        
        with st.form("add_product_form", clear_on_submit=True):
            st.markdown("<div class='action-section'>", unsafe_allow_html=True)
            
            col_name, col_price, col_stock = st.columns([3, 2, 2])
            
            with col_name:
                product_name = st.text_input(
                    "🏷️ שם המוצר",
                    placeholder="לדוגמה: חלב 3% ליטר",
                    help="הזן שם ברור ומפורט למוצר"
                )
            
            with col_price:
                product_price = st.number_input(
                    "💰 מחיר (₪)",
                    min_value=0.0,
                    step=0.5,
                    format="%.2f",
                    help="מחיר ליחידה"
                )
            
            with col_stock:
                product_stock = st.number_input(
                    "📦 כמות במלאי",
                    min_value=0,
                    step=1,
                    value=0,
                    help="כמה יחידות יש במלאי"
                )
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # כפתור הוספה
            st.markdown("<div class='approve-btn'>", unsafe_allow_html=True)
            submit = st.form_submit_button("➕ הוסף מוצר למערכת", use_container_width=True, type="primary")
            st.markdown("</div>", unsafe_allow_html=True)
            
            if submit:
                if not product_name:
                    st.error("❌ חובה להזין שם מוצר!")
                elif product_price <= 0:
                    st.error("❌ המחיר חייב להיות גדול מ-0!")
                else:
                    try:
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute(
                            "INSERT INTO products (name, price, stock) VALUES (%s, %s, %s)",
                            (product_name, product_price, product_stock)
                        )
                        conn.commit()
                        conn.close()
                        
                        st.success(f"✅ המוצר '{product_name}' נוסף בהצלחה!")
                        st.balloons()
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ שגיאה בהוספת מוצר: {e}")
        
        # תצוגה מקדימה של המוצרים הקיימים
        st.markdown("---")
        st.markdown("#### 👀 תצוגה מהירה - מוצרים קיימים")
        
        conn = get_db_connection()
        preview_df = pd.read_sql("SELECT name, price, stock FROM products ORDER BY name LIMIT 10", conn)
        conn.close()
        
        if not preview_df.empty:
            st.dataframe(
                preview_df,
                use_container_width=True,
                column_config={
                    "name": "שם המוצר",
                    "price": st.column_config.NumberColumn("מחיר (₪)", format="%.2f"),
                    "stock": st.column_config.NumberColumn("מלאי", format="%d")
                },
                hide_index=True
            )
        else:
            st.info("אין עדיין מוצרים במערכת")

# --- Footer ---
st.markdown("---")
st.markdown("""
    <div style='text-align: center; padding: 20px; color: #a0a0c0;'>
        <p>🛒 מערכת ניהול מכולת מתקדמת | גרסה 2.0</p>
    </div>
""", unsafe_allow_html=True)
