import streamlit as st
import psycopg2
import pandas as pd
import os
import requests
import time

# --- הגדרות ---
st.set_page_config(page_title="ניהול מכולת הזוג", layout="wide", page_icon="🛒")

# --- הגדרות מערכת (כאן משנים דברים!) ---
# 1. כתובת הבוט ב-Render (וודא שזו הכתובת הנכונה שלך!)
BOT_URL = os.environ.get("BOT_URL", "https://minimarket-ocfq.onrender.com")

# 2. סיסמאות (חייבות להיות תואמות ל-app.py)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "12345")       # לכניסה לאתר
INTERNAL_SECRET = os.environ.get("INTERNAL_SECRET", "idan12345") # לתקשורת עם הבוט
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# --- עיצוב מקצועי ורציני ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    h1 { color: #2c3e50; text-align: center; font-weight: 700; padding: 20px 0; border-bottom: 3px solid #3498db; margin-bottom: 30px; }
    h2, h3 { color: #34495e; font-weight: 600; }
    .stButton > button { background-color: #3498db; color: white; border: none; border-radius: 6px; padding: 10px 24px; font-weight: 600; transition: all 0.2s; }
    .stButton > button:hover { background-color: #2980b9; box-shadow: 0 4px 8px rgba(52, 152, 219, 0.3); }
    .stSuccess { background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
    .stError { background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
    .login-container { background-color: white; border-radius: 8px; padding: 40px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border: 1px solid #e1e8ed; }
    .metric-card { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- פונקציות ---
def get_db_connection():
    return psycopg2.connect(os.environ.get("DB_URL"))

def notify_customer(phone, message):
    """שולח הודעה ללקוח דרך הבוט בצורה מאובטחת"""
    try:
        # ניקוי מספר הטלפון
        clean_phone = str(phone).replace("WhatsApp:", "").replace("טלפון:", "").replace("-", "").replace(" ", "").replace("|", "").strip()
        if "טלפון:" in str(phone):
            clean_phone = str(phone).split("טלפון:")[-1].split("|")[0].strip()
        
        # שימוש במפתח האבטחה (X-Secret) שתואם ל-app.py
        headers = {"X-Secret": INTERNAL_SECRET}
        
        response = requests.post(
            f"{BOT_URL}/send_update", 
            json={"phone": clean_phone, "message": message},
            headers=headers,
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"שגיאה בשליחת הודעה: {e}")
        return False

# --- מסך התחברות ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center;'>🔐 כניסה למערכת ניהול</h2>", unsafe_allow_html=True)
        password = st.text_input("סיסמת מנהל:", type="password", placeholder="הזן סיסמה...")
        if st.button("כניסה למערכת", use_container_width=True):
            if password == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.success("התחברת בהצלחה!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("סיסמה שגויה!")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- כפתור התנתקות ---
col_space, col_logout = st.columns([6, 1])
with col_logout:
    if st.button("🚪 התנתק", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# --- כותרת ראשית ---
st.markdown("<h1>🛒 מכולת הזוג - דשבורד ניהול</h1>", unsafe_allow_html=True)

# --- טאבים ראשיים ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📦 ממתינות לאישור", 
    "✅ היסטוריה ומאושרות", 
    "❌ מבוטלות", 
    "🏪 ניהול מלאי", 
    "📊 דוחות וסטטיסטיקה"
])

try:
    # --- טאב 1: הזמנות ממתינות ---
    with tab1:
        st.markdown("### ⏳ הזמנות חדשות לטיפול")
        
        conn = get_db_connection()
        pending_df = pd.read_sql("""
            SELECT id, customer_name, items, total_price, address, created_at 
            FROM orders WHERE status = 'ממתין לאישור' ORDER BY created_at DESC
        """, conn)
        conn.close()
        
        if not pending_df.empty:
            st.dataframe(
                pending_df,
                use_container_width=True,
                column_config={
                    "id": st.column_config.NumberColumn("מס׳", width="small"),
                    "customer_name": "לקוח",
                    "items": "מוצרים",
                    "total_price": st.column_config.NumberColumn("סה״כ", format="₪%.2f"),
                    "address": "פרטים",
                    "created_at": st.column_config.DatetimeColumn("התקבל ב", format="DD/MM HH:mm")
                }
            )
            
            st.warning("⚠️ יש לטפל בהזמנה אחת בכל פעם")
            col1, col2, col3 = st.columns([1, 2, 2])
            
            with col1:
                order_id = st.number_input("בחר מס׳ הזמנה:", min_value=1, step=1)
            
            with col2:
                delivery_time = st.text_input("זמן הגעה משוער:", value="25 דקות")
            
            with col3:
                st.write("") # מרווח
                st.write("") 
                b_col1, b_col2 = st.columns(2)
                with b_col1:
                    if st.button("✅ אשר ושלח הודעה", type="primary", use_container_width=True):
                        # בדיקה שההזמנה קיימת
                        row = pending_df[pending_df['id'] == order_id]
                        if not row.empty:
                            conn = get_db_connection()
                            cur = conn.cursor()
                            cur.execute("UPDATE orders SET status='אושר', delivery_time=%s, approved_at=NOW() WHERE id=%s", (delivery_time, order_id))
                            conn.commit()
                            conn.close()
                            
                            # שליחת וואטסאפ
                            cust_name = row.iloc[0]['customer_name']
                            items_txt = row.iloc[0]['items']
                            phone_addr = row.iloc[0]['address'] # הטלפון בתוך שדה הכתובת
                            
                            msg = f"היי {cust_name}! 👋\nההזמנה שלך (#{order_id}) אושרה ויצאה להכנה.\n🛒 מוצרים: {items_txt}\n🛵 זמן משוער: {delivery_time}.\nתודה!"
                            
                            if notify_customer(phone_addr, msg):
                                st.balloons()
                                st.success(f"הזמנה {order_id} אושרה ונשלחה הודעה!")
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error("ההזמנה אושרה בדאטהבייס, אבל נכשלה שליחת ההודעה לבוט.")
                        else:
                            st.error("מספר הזמנה לא נמצא ברשימה.")
                
                with b_col2:
                    if st.button("❌ בטל", type="secondary", use_container_width=True):
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute("UPDATE orders SET status='בוטל' WHERE id=%s", (order_id,))
                        conn.commit()
                        conn.close()
                        st.info("ההזמנה הועברה למבוטלות.")
                        time.sleep(1)
                        st.rerun()
        else:
            st.info("🎉 אין הזמנות חדשות כרגע. הכל מטופל!")

    # --- טאב 2: מאושרות ---
    with tab2:
        st.markdown("### ✅ היסטוריית הזמנות שאושרו")
        conn = get_db_connection()
        approved_df = pd.read_sql("SELECT * FROM orders WHERE status = 'אושר' ORDER BY created_at DESC", conn)
        conn.close()
        
        if not approved_df.empty:
            st.dataframe(approved_df, use_container_width=True)
            with st.expander("🗑️ מחיקת הזמנה ישנה (לצמיתות)"):
                del_id = st.number_input("מספר הזמנה למחיקה:", min_value=1, step=1, key="del_app")
                if st.button("מחק לצמיתות"):
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute("DELETE FROM orders WHERE id=%s", (del_id,))
                    conn.commit()
                    conn.close()
                    st.success("נמחק.")
                    time.sleep(1)
                    st.rerun()
        else:
            st.info("עדיין אין הזמנות מאושרות.")

    # --- טאב 3: מבוטלות ---
    with tab3:
        st.markdown("### ❌ הזמנות שבוטלו")
        conn = get_db_connection()
        canc_df = pd.read_sql("SELECT * FROM orders WHERE status = 'בוטל' ORDER BY created_at DESC", conn)
        conn.close()
        
        if not canc_df.empty:
            st.dataframe(canc_df, use_container_width=True)
        else:
            st.info("אין הזמנות מבוטלות.")

    # --- טאב 4: ניהול מלאי ---
    with tab4:
        st.markdown("### 🏪 ניהול מוצרים במלאי")
        conn = get_db_connection()
        products_df = pd.read_sql("SELECT * FROM products ORDER BY name", conn)
        conn.close()
        
        col_list, col_add = st.columns([2, 1])
        
        with col_list:
            st.dataframe(products_df, use_container_width=True, height=400)
            
        with col_add:
            st.markdown("#### ➕ הוספת מוצר")
            with st.form("add_prod"):
                p_name = st.text_input("שם מוצר")
                p_price = st.number_input("מחיר", min_value=0.0, step=0.5)
                p_stock = st.number_input("מלאי התחלתי", min_value=0, step=1, value=10)
                if st.form_submit_button("הוסף למלאי"):
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute("INSERT INTO products (name, price, stock) VALUES (%s, %s, %s)", (p_name, p_price, p_stock))
                    conn.commit()
                    conn.close()
                    st.success("נוסף בהצלחה!")
                    time.sleep(1)
                    st.rerun()
            
            st.markdown("#### 🗑️/✏️ עריכה")
            edit_id = st.number_input("ID מוצר לעריכה/מחיקה:", step=1)
            c1, c2 = st.columns(2)
            if c1.button("🗑️ מחק מוצר"):
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("DELETE FROM products WHERE id=%s", (edit_id,))
                conn.commit()
                conn.close()
                st.rerun()
            
            new_price_val = c2.number_input("מחיר חדש:", step=0.5, key="np")
            if c2.button("עדכן מחיר"):
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("UPDATE products SET price=%s WHERE id=%s", (new_price_val, edit_id))
                conn.commit()
                conn.close()
                st.rerun()

    # --- טאב 5: סטטיסטיקה ---
    with tab5:
        st.markdown("### 📊 סיכום נתונים")
        conn = get_db_connection()
        try:
            total_income = pd.read_sql("SELECT SUM(total_price) FROM orders WHERE status='אושר'", conn).iloc[0,0]
            total_orders = pd.read_sql("SELECT COUNT(*) FROM orders WHERE status='אושר'", conn).iloc[0,0]
            pending_count = pd.read_sql("SELECT COUNT(*) FROM orders WHERE status='ממתין לאישור'", conn).iloc[0,0]
        except:
            total_income, total_orders, pending_count = 0, 0, 0
        conn.close()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("💰 סה\"כ הכנסות", f"₪{total_income or 0:,.2f}")
        m2.metric("📦 הזמנות שבוצעו", total_orders)
        m3.metric("⏳ ממתינות כרגע", pending_count)
        
        if st.button("🔄 רענן נתונים"):
            st.rerun()

except Exception as e:
    st.error(f"שגיאת מערכת: {e}")
