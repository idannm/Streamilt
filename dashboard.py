import streamlit as st
import psycopg2
import pandas as pd
import os
import requests
import time
# אם אתה משתמש ב-Groq בדשבורד עצמו (למשל לסיכום הזמנות), תצטרך לייבא אותו:
# from groq import Groq 

# --- הגדרות ---
st.set_page_config(page_title="ניהול מכולת הזוג", layout="wide", page_icon="🛒")

# 👇👇👇 אבטחה: מושכים את המפתח מההגדרות של השרת במקום לכתוב אותו כאן 👇👇👇
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
# אם נצטרך להשתמש ב-AI בעתיד בדשבורד, נשתמש במשתנה הזה

# כתובת הבוט (מושך מהשרת, או משתמש בברירת מחדל אם לא קיים)
BOT_URL = os.environ.get("BOT_URL", "https://minimarket-ocfq.onrender.com")

# סיסמה לכניסה לאתר הניהול
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "12345") 
# טיפ: גם את הסיסמה עדיף לשמור ב-Render ולא בקוד!

# --- עיצוב מתקדם ---
st.markdown("""
    <style>
    /* רקע כללי */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    h1 {
        color: #ffffff !important;
        text-align: center;
        font-weight: 800;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        padding: 20px;
    }
    h2, h3, p, label, .stMarkdown {
        color: #ffffff !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 15px 35px;
        font-weight: 700;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(245, 87, 108, 0.4);
        width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(245, 87, 108, 0.6);
    }
    .dataframe {
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-radius: 12px;
        overflow: hidden;
    }
    .login-container {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 40px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }
    .stMetric {
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .stMetric [data-testid="stMetricValue"] {
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- פונקציות ---
def get_db_connection():
    return psycopg2.connect(os.environ.get("DB_URL"))

def notify_customer(phone, message):
    """שליחת בקשה לבוט כדי שישלח הודעה ללקוח"""
    try:
        clean_phone = str(phone).replace("WhatsApp:", "").replace("טלפון:", "").replace("-", "").replace(" ", "").replace("|", "").strip()
        if "טלפון:" in str(phone):
            clean_phone = str(phone).split("טלפון:")[-1].split("|")[0].strip()
        
        print(f"🔄 מנסה לשלוח ל: {clean_phone} דרך {BOT_URL}")
        
        # המפתח הסודי לאבטחה
        headers = {"X-Secret": "idan12345"}
        
        response = requests.post(
            f"{BOT_URL}/send_update", 
            json={"phone": clean_phone, "message": message},
            headers=headers,
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"❌ שגיאת תקשורת עם הבוט: {e}")
        return False

# --- מסך התחברות (Login) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1>🔐 כניסה למערכת ניהול</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        st.markdown("### 👋 שלום מנהל!")
        password = st.text_input("סיסמה:", type="password", placeholder="הכנס סיסמה...")
        if st.button("🚀 כניסה למערכת"):
            if password == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.success("✅ התחברת בהצלחה!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ סיסמה שגויה!")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- כפתור התנתקות ---
col_logout1, col_logout2 = st.columns([6, 1])
with col_logout2:
    if st.button("🚪 התנתק"):
        st.session_state.logged_in = False
        st.rerun()

# --- המערכת עצמה ---
st.markdown("<h1>🛒 מכולת הזוג - ניהול הזמנות</h1>", unsafe_allow_html=True)

try:
    conn = get_db_connection()
    # שליפת 100 ההזמנות האחרונות
    query = """
        SELECT id, customer_name, items, total_price, status, address, created_at, delivery_time
        FROM orders 
        ORDER BY created_at DESC
        LIMIT 100
    """
    df = pd.read_sql(query, conn)
    conn.close()

    tab1, tab2, tab3, tab4 = st.tabs(["🔴 ממתינות לאישור", "✅ הזמנות מאושרות", "📊 כל ההזמנות", "📈 סטטיסטיקות"])
    
    # --- טאב 1: ממתינות ---
    with tab1:
        st.markdown("### 🔴 הזמנות ממתינות לאישור")
        pending_df = df[df['status'] == 'ממתין לאישור']
        
        if not pending_df.empty:
            st.dataframe(
                pending_df[['id', 'customer_name', 'items', 'total_price', 'address', 'created_at']], 
                use_container_width=True,
                column_config={
                    "id": "מס׳", "customer_name": "שם לקוח", "items": "מוצרים",
                    "total_price": st.column_config.NumberColumn("סה״כ", format="₪%.2f"),
                    "address": "כתובת וטלפון",
                    "created_at": st.column_config.DatetimeColumn("תאריך", format="DD/MM/YYYY HH:mm")
                }
            )
            st.divider()
            
            # אישור הזמנה
            col_input, col_time, col_btn = st.columns([2, 3, 2])
            with col_input:
                order_id = st.number_input("מספר הזמנה:", min_value=1, step=1, key="approve_order_id")
            with col_time:
                delivery_time = st.text_input("זמן הגעה משוער:", value="20 דקות", key="delivery_time")
            with col_btn:
                st.write("")
                st.write("")
                if st.button("✅ אשר ושלח הודעה"):
                    order_row = pending_df[pending_df['id'] == order_id]
                    if not order_row.empty:
                        customer_name = order_row.iloc[0]['customer_name']
                        items = order_row.iloc[0]['items']
                        full_address = str(order_row.iloc[0]['address'])
                        
                        if "טלפון:" in full_address:
                            phone = full_address.split("טלפון:")[-1].split("|")[0].strip()
                        else:
                            phone = full_address
                        
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute(
                            "UPDATE orders SET status = 'אושר', delivery_time = %s, approved_at = NOW() WHERE id = %s", 
                            (delivery_time, order_id)
                        )
                        conn.commit()
                        conn.close()
                        
                        msg = f"""🎉 שלום {customer_name}!
ההזמנה שלך אושרה ויצאה לדרך! 🛵
📦 הזמנה #{order_id}
🛒 פריטים: {items}
⏰ זמן הגעה משוער: {delivery_time}
תודה שקניתם במכולת הזוג! 🙏"""
                        
                        if notify_customer(phone, msg):
                            st.success(f"✅ הזמנה #{order_id} אושרה והודעה נשלחה!")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.warning("⚠️ אושר ב-DB, אך נכשל בוואטסאפ.")
                    else:
                        st.error("❌ מספר הזמנה לא נמצא.")
        else:
            st.info("📭 אין הזמנות ממתינות")

    # --- טאב 2: מאושרות ---
    with tab2:
        st.markdown("### ✅ הזמנות מאושרות")
        approved_df = df[df['status'] == 'אושר']
        if not approved_df.empty:
            st.dataframe(
                approved_df[['id', 'customer_name', 'items', 'total_price', 'delivery_time', 'created_at']], 
                use_container_width=True
            )
            st.divider()
            col_del1, col_del2 = st.columns([3, 1])
            with col_del1:
                delete_id = st.number_input("מחיקת הזמנה:", min_value=1, step=1, key="del_id")
            with col_del2:
                st.write("")
                st.write("")
                if st.button("🗑️ מחק"):
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute("DELETE FROM orders WHERE id = %s AND status = 'אושר'", (delete_id,))
                    conn.commit()
                    conn.close()
                    st.success("נמחק!")
                    time.sleep(1)
                    st.rerun()
        else:
            st.info("📭 אין הזמנות מאושרות")

    # --- טאב 3: הכל ---
    with tab3:
        st.dataframe(df, use_container_width=True)

    # --- טאב 4: סטטיסטיקות ---
    with tab4:
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("📦 סה״כ", len(df))
        with col2: st.metric("⏳ ממתינות", len(df[df['status'] == 'ממתין לאישור']))
        with col3: st.metric("✅ מאושרות", len(df[df['status'] == 'אושר']))
        with col4: st.metric("❌ מבוטלות", len(df[df['status'] == 'בוטל']))

    st.divider()
    if st.button("🔄 רענן נתונים"):
        st.rerun()

except Exception as e:
    st.error(f"❌ שגיאה: {e}")
