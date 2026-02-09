import streamlit as st
import psycopg2
import pandas as pd
import os
import requests
import time

# --- 1. הגדרות עמוד ---
st.set_page_config(
    page_title="ניהול מכולת - הזוג",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. משתני סביבה ---
# וודא שהם מוגדרים ב-Render!
DB_URL = os.environ.get("DB_URL")
BOT_URL = "https://minimarket-ocfq.onrender.com" # שנה לכתובת שלך אם שונה
INTERNAL_SECRET = os.environ.get("INTERNAL_SECRET", "123")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "12345")

# --- 3. עיצוב בהיר ומודרני (CSS) ---
st.markdown("""
    <style>
    /* רקע כללי בהיר */
    .stApp {
        background-color: #f4f6f9;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* כותרות */
    h1, h2, h3 {
        color: #2c3e50 !important;
        font-weight: 700;
    }
    
    /* כרטיסים וקונטיינרים */
    div[data-testid="stMetric"], div.css-1r6slb0 {
        background-color: white;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border: 1px solid #e1e4e8;
    }
    
    /* טבלאות */
    div[data-testid="stDataFrame"] {
        background-color: white;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    /* כפתורים ראשיים */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    /* כותרת עליונה */
    .main-header {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        text-align: center;
        border-bottom: 3px solid #3498db;
    }
    
    /* מסך התחברות */
    .login-box {
        background: white;
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        text-align: center;
        border: 1px solid #e1e4e8;
    }
    
    /* טקסט רגיל */
    p, label, span {
        color: #34495e;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. פונקציות עזר ---
def get_db_connection():
    return psycopg2.connect(DB_URL)

def notify_customer(phone, message):
    """שולח בקשה לבוט כדי שישלח הודעת וואטסאפ ללקוח"""
    try:
        # ניקוי מספר הטלפון מתווים מיותרים
        clean_phone = str(phone).replace("WhatsApp:", "").replace("טלפון:", "").replace("-", "").replace(" ", "").replace("|", "").strip()
        
        # אם יש טקסט לפני המספר (כמו בכתובת), נחלץ רק את המספר
        # הנחה: המספר הוא הדבר האחרון או נמצא אחרי נקודתיים
        if ":" in clean_phone:
            clean_phone = clean_phone.split(":")[-1].strip()
            
        if clean_phone.startswith("0"): 
            clean_phone = "972" + clean_phone[1:]
            
        headers = {"X-Internal-Secret": INTERNAL_SECRET}
        response = requests.post(
            f"{BOT_URL}/send_update", 
            json={"phone": clean_phone, "message": message},
            headers=headers,
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Error notifying: {e}")
        return False

# --- 5. לוגיקת התחברות ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='login-box'><h2>🔐 כניסה למערכת</h2><p>מכולת הזוג - ממשק ניהול</p></div>", unsafe_allow_html=True)
        password = st.text_input("הזן סיסמת מנהל", type="password")
        if st.button("כניסה", use_container_width=True, type="primary"):
            if password == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("סיסמה שגויה!")
    st.stop()

# --- 6. כותרת ותפריט עליון ---
st.markdown("<div class='main-header'><h1>🛒 מערכת ניהול - מכולת הזוג</h1></div>", unsafe_allow_html=True)

if st.button("🚪 התנתק", key="logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- 7. טאבים ראשיים ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📦 הזמנות ממתינות", 
    "✅ הזמנות מאושרות", 
    "❌ הזמנות מבוטלות",
    "🏪 ניהול מלאי",
    "📊 סטטיסטיקות"
])

# מעטפת try-except ראשית למניעת קריסות
try:
    # --- טאב 1: הזמנות ממתינות ---
    with tab1:
        st.subheader("📦 הזמנות חדשות")
        
        if st.button("🔄 רענן נתונים", key="refresh_pending"):
            st.rerun()

        conn = get_db_connection()
        pending_df = pd.read_sql("""
            SELECT id, customer_name, items, address, created_at 
            FROM orders 
            WHERE status = 'ממתין לאישור' 
            ORDER BY created_at DESC
        """, conn)
        conn.close()

        if not pending_df.empty:
            # הצגת הטבלה
            st.dataframe(
                pending_df,
                use_container_width=True,
                column_config={
                    "id": st.column_config.NumberColumn("מס' הזמנה", width="small"),
                    "customer_name": "לקוח",
                    "items": "פירוט מוצרים",
                    "address": "כתובת וטלפון",
                    "created_at": st.column_config.DatetimeColumn("התקבל ב-", format="DD/MM HH:mm")
                }
            )
            
            st.markdown("---")
            
            # אזור פעולות (אישור / ביטול)
            c1, c2, c3 = st.columns([1, 2, 1])
            with c1:
                order_id = st.number_input("בחר מספר הזמנה לטיפול:", min_value=1, step=1)
            with c2:
                delivery_time = st.text_input("זמן משוער למשלוח:", "20 דקות")
            
            col_approve, col_cancel = st.columns(2)
            
            # כפתור אישור
            with col_approve:
                if st.button("✅ אשר הזמנה ושלח הודעה", use_container_width=True, type="primary"):
                    row = pending_df[pending_df['id'] == order_id]
                    if not row.empty:
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute("UPDATE orders SET status = 'אושר', total_price = 0, delivery_time = %s, approved_at = NOW() WHERE id = %s", (delivery_time, order_id))
                        conn.commit()
                        conn.close()
                        
                        # שליחת הודעה
                        full_addr = row.iloc[0]['address']
                        msg = f"היי {row.iloc[0]['customer_name']}, הזמנה #{order_id} אושרה! 🛵\nזמן משוער: {delivery_time}.\nתודה שקניתם במכולת הזוג!"
                        
                        if notify_customer(full_addr, msg):
                            st.success(f"הזמנה {order_id} אושרה והודעה נשלחה!")
                        else:
                            st.warning("ההזמנה אושרה ביומן, אבל לא נשלחה הודעה ללקוח.")
                        
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("מספר הזמנה לא נמצא ברשימה.")

            # כפתור ביטול
            with col_cancel:
                if st.button("❌ בטל הזמנה", use_container_width=True):
                    row = pending_df[pending_df['id'] == order_id]
                    if not row.empty:
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute("UPDATE orders SET status = 'בוטל', cancellation_reason = 'בוטל ע״י המנהל' WHERE id = %s", (order_id,))
                        conn.commit()
                        conn.close()
                        
                        full_addr = row.iloc[0]['address']
                        notify_customer(full_addr, f"שלום, הזמנה #{order_id} בוטלה עקב חוסר במלאי או בעיה אחרת. עמכם הסליחה.")
                        
                        st.error(f"הזמנה {order_id} בוטלה.")
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("לא נמצאה הזמנה.")
        else:
            st.info("אין הזמנות חדשות כרגע 🎉")

    # --- טאב 2: הזמנות מאושרות ---
    with tab2:
        st.subheader("✅ היסטוריית הזמנות שאושרו")
        if st.button("🔄 רענן", key="refresh_approved"): st.rerun()
        
        conn = get_db_connection()
        approved_df = pd.read_sql("SELECT id, customer_name, items, delivery_time, approved_at FROM orders WHERE status = 'אושר' ORDER BY approved_at DESC LIMIT 50", conn)
        conn.close()
        
        st.dataframe(approved_df, use_container_width=True)

    # --- טאב 3: הזמנות מבוטלות ---
    with tab3:
        st.subheader("❌ הזמנות שבוטלו")
        conn = get_db_connection()
        canceled_df = pd.read_sql("SELECT id, customer_name, items, cancellation_reason, created_at FROM orders WHERE status = 'בוטל' ORDER BY created_at DESC LIMIT 50", conn)
        conn.close()
        st.dataframe(canceled_df, use_container_width=True)

    # --- טאב 4: ניהול מלאי ---
    with tab4:
        st.subheader("🏪 ניהול מוצרים ומחירים")
        
        # חיפוש
        search = st.text_input("🔍 חיפוש מוצר:", placeholder="הקלד שם מוצר...")
        
        conn = get_db_connection()
        query = "SELECT id, name, price, stock FROM products"
        if search:
            query += f" WHERE name ILIKE '%%{search}%%'"
        query += " ORDER BY name"
        
        products_df = pd.read_sql(query, conn)
        conn.close()

        # הוספת מוצר חדש
        with st.expander("➕ הוספת מוצר חדש"):
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            with c1: new_name = st.text_input("שם מוצר")
            with c2: new_price = st.number_input("מחיר", min_value=0.0, step=0.5)
            with c3: new_stock = st.number_input("מלאי התחלתי", min_value=0, step=1, value=10)
            with c4: 
                st.write("")
                st.write("")
                if st.button("הוסף"):
                    if new_name:
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute("INSERT INTO products (name, price, stock) VALUES (%s, %s, %s)", (new_name, new_price, new_stock))
                        conn.commit()
                        conn.close()
                        st.success("נוסף!")
                        time.sleep(1)
                        st.rerun()

        st.markdown("### רשימת מוצרים")
        
        # הצגת מוצרים עם אפשרות עריכה
        for index, row in products_df.iterrows():
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 1, 1])
                
                # אם אנחנו במצב עריכה של השורה הזו
                if f"edit_mode_{row['id']}" in st.session_state and st.session_state[f"edit_mode_{row['id']}"]:
                    with c1: name_val = st.text_input("שם", value=row['name'], key=f"name_{row['id']}")
                    with c2: price_val = st.number_input("מחיר", value=float(row['price']), step=0.5, key=f"price_{row['id']}")
                    with c3: stock_val = st.number_input("מלאי", value=int(row['stock']), step=1, key=f"stock_{row['id']}")
                    with c4:
                        if st.button("💾", key=f"save_{row['id']}"):
                            conn = get_db_connection()
                            cur = conn.cursor()
                            cur.execute("UPDATE products SET name=%s, price=%s, stock=%s WHERE id=%s", (name_val, price_val, stock_val, row['id']))
                            conn.commit()
                            conn.close()
                            st.session_state[f"edit_mode_{row['id']}"] = False
                            st.rerun()
                    with c5:
                        if st.button("✖️", key=f"cancel_{row['id']}"):
                            st.session_state[f"edit_mode_{row['id']}"] = False
                            st.rerun()
                else:
                    # מצב תצוגה רגיל
                    with c1: st.write(f"**{row['name']}**")
                    with c2: st.write(f"₪{row['price']}")
                    with c3: 
                        color = "red" if row['stock'] == 0 else "green"
                        st.markdown(f":{color}[{row['stock']} יח']")
                    with c4:
                        if st.button("✏️", key=f"edit_btn_{row['id']}"):
                            st.session_state[f"edit_mode_{row['id']}"] = True
                            st.rerun()
                    with c5:
                        if st.button("🗑️", key=f"del_btn_{row['id']}"):
                            conn = get_db_connection()
                            cur = conn.cursor()
                            cur.execute("DELETE FROM products WHERE id=%s", (row['id'],))
                            conn.commit()
                            conn.close()
                            st.rerun()
                st.divider()

    # --- טאב 5: סטטיסטיקות ---
    with tab5:
        st.subheader("📊 נתונים כלליים")
        conn = get_db_connection()
        total_orders = pd.read_sql("SELECT COUNT(*) FROM orders", conn).iloc[0,0]
        pending_count = pd.read_sql("SELECT COUNT(*) FROM orders WHERE status='ממתין לאישור'", conn).iloc[0,0]
        approved_count = pd.read_sql("SELECT COUNT(*) FROM orders WHERE status='אושר'", conn).iloc[0,0]
        conn.close()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("סה״כ הזמנות", total_orders)
        c2.metric("ממתינות לטיפול", pending_count)
        c3.metric("הושלמו", approved_count)

except Exception as e:
    st.error(f"שגיאה במערכת: {e}")
