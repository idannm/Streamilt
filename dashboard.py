import streamlit as st
import psycopg2
import pandas as pd
import os
import requests
import time

# --- 1. הגדרות ועיצוב ---
st.set_page_config(
    page_title="ניהול מכולת - הזוג",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# משתני סביבה
DB_URL = os.environ.get("DB_URL")
# וודא שהכתובת הזו נכונה (הכתובת של הבוט ב-Render)
BOT_URL = "https://minimarket-ocfq.onrender.com" 
INTERNAL_SECRET = os.environ.get("INTERNAL_SECRET", "123")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "12345")

# עיצוב CSS מלא ומושקע
st.markdown("""
    <style>
    /* רקע ופונטים */
    .stApp {
        background-color: #f0f2f6;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* כותרות */
    h1 { color: #2c3e50; text-align: center; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
    h2, h3 { color: #34495e; }
    
    /* כרטיסי מידע */
    div[data-testid="stMetric"] {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    /* טבלאות */
    div[data-testid="stDataFrame"] {
        background-color: white;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    /* כפתורים */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: 0.3s;
    }
    
    /* תיבת התחברות */
    .login-container {
        max-width: 400px;
        margin: auto;
        padding: 40px;
        background: white;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. פונקציות עזר ---
def get_db_connection():
    return psycopg2.connect(DB_URL)

def notify_customer(phone, message):
    """שליחת הודעה ללקוח דרך השרת של הבוט"""
    try:
        # ניקוי אגרסיבי של מספר הטלפון
        clean_phone = str(phone).replace("WhatsApp:", "").replace("טלפון:", "").replace("-", "").replace(" ", "").replace("|", "").strip()
        
        # לפעמים המספר מוחבא בתוך הכתובת, ננסה לחלץ אותו
        if ":" in clean_phone:
            clean_phone = clean_phone.split(":")[-1].strip()
            
        if clean_phone.startswith("0"): 
            clean_phone = "972" + clean_phone[1:]
            
        # שליחה עם המפתח הסודי
        response = requests.post(
            f"{BOT_URL}/send_update", 
            json={"phone": clean_phone, "message": message},
            headers={"X-Internal-Secret": INTERNAL_SECRET},
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"שגיאת תקשורת עם הבוט: {e}")
        return False

# --- 3. מסך כניסה (Login) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='login-container'><h2>🔐 כניסה למערכת</h2><p>הזן סיסמת ניהול</p></div>", unsafe_allow_html=True)
        password = st.text_input("סיסמה:", type="password")
        if st.button("כניסה", use_container_width=True, type="primary"):
            if password == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.success("התחברת בהצלחה!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("סיסמה שגויה!")
    st.stop()

# --- 4. הממשק הראשי ---
st.title("🛒 מערכת ניהול - מכולת הזוג")

# כפתור התנתקות צף בצד
with st.sidebar:
    st.write(f"מחובר כמנהל")
    if st.button("🚪 התנתק"):
        st.session_state.logged_in = False
        st.rerun()

# טאבים
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📦 הזמנות לטיפול", 
    "✅ היסטוריה", 
    "❌ מבוטלות",
    "🏪 ניהול מלאי",
    "📊 דוחות"
])

# --- טאב 1: הזמנות לטיפול (הליבה) ---
with tab1:
    st.subheader("הזמנות חדשות שממתינות לאישור")
    
    if st.button("🔄 רענן רשימה"):
        st.rerun()

    conn = get_db_connection()
    # שולפים רק את מה שממתין לאישור
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
                "id": st.column_config.NumberColumn("מס' הזמנה", format="%d"),
                "customer_name": "שם הלקוח",
                "items": "פירוט הזמנה",
                "address": "כתובת וטלפון",
                "created_at": st.column_config.DatetimeColumn("התקבל ב-", format="DD/MM HH:mm")
            }
        )
        
        st.markdown("---")
        st.markdown("### 🎯 פעולות על הזמנה")
        
        # בחירת הזמנה לטיפול
        selected_order_id = st.selectbox("בחר מספר הזמנה לטיפול:", pending_df['id'].tolist())
        
        # מציאת השורה הרלוונטית
        order_row = pending_df[pending_df['id'] == selected_order_id].iloc[0]
        
        col_approve, col_cancel = st.columns(2)
        
        # --- צד ימין: אישור הזמנה ---
        with col_approve:
            st.success("✅ אישור הזמנה")
            # השדה שביקשת: זמן הגעה
            delivery_time = st.text_input("זמן הגעה משוער:", value="20-30 דקות", help="הודעה זו תישלח ללקוח")
            
            if st.button("אשר ושלח הודעה ללקוח", type="primary", use_container_width=True):
                conn = get_db_connection()
                cur = conn.cursor()
                # עדכון הסטטוס והזמן בדאטהבייס
                cur.execute("UPDATE orders SET status = 'אושר', delivery_time = %s, approved_at = NOW() WHERE id = %s", (delivery_time, int(selected_order_id)))
                conn.commit()
                conn.close()
                
                # שליחת ההודעה המשופרת ללקוח
                msg = f"שלום {order_row['customer_name']}! 👋\nההזמנה שלך (#{selected_order_id}) אושרה! ✅\n🛒 המוצרים: {order_row['items']}\n🛵 זמן הגעה משוער: {delivery_time}.\nתודה שבחרתם בנו!"
                
                if notify_customer(order_row['address'], msg):
                    st.success("ההזמנה אושרה והודעה נשלחה!")
                else:
                    st.warning("ההזמנה אושרה ביומן, אך שליחת ההודעה נכשלה.")
                
                time.sleep(1.5)
                st.rerun()

        # --- צד שמאל: ביטול הזמנה ---
        with col_cancel:
            st.error("❌ ביטול הזמנה")
            # הרשימה שביקשת + אופציה ל"אחר"
            reasons = ["חוסר במלאי", "כתובת לא ברורה/מחוץ לאזור", "הלקוח לא עונה", "בקשת הלקוח", "אחר"]
            reason_selection = st.selectbox("סיבת הביטול:", reasons)
            
            final_reason = reason_selection
            # אם בחר "אחר", פותחים שדה טקסט חופשי
            if reason_selection == "אחר":
                final_reason = st.text_input("פרט את סיבת הביטול:")
            
            if st.button("בטל הזמנה ועדכן את הלקוח", type="secondary", use_container_width=True):
                if final_reason:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute("UPDATE orders SET status = 'בוטל', cancellation_reason = %s WHERE id = %s", (final_reason, int(selected_order_id)))
                    conn.commit()
                    conn.close()
                    
                    # הודעת הביטול ללקוח
                    msg = f"שלום {order_row['customer_name']}.\nלצערנו, ההזמנה (#{selected_order_id}) בוטלה. ❌\nסיבה: {final_reason}.\nניתן ליצור איתנו קשר לפרטים נוספים."
                    
                    notify_customer(order_row['address'], msg)
                    st.error("ההזמנה בוטלה והודעה נשלחה.")
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.warning("חובה לכתוב סיבת ביטול (אם בחרת 'אחר').")

    else:
        st.info("אין הזמנות חדשות כרגע 🎉")

# --- טאב 2: היסטוריה ---
with tab2:
    st.subheader("הזמנות שאושרו")
    if st.button("רענן היסטוריה"): st.rerun()
    conn = get_db_connection()
    df = pd.read_sql("SELECT id, customer_name, items, delivery_time, approved_at FROM orders WHERE status = 'אושר' ORDER BY approved_at DESC LIMIT 50", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)

# --- טאב 3: מבוטלות ---
with tab3:
    st.subheader("הזמנות שבוטלו")
    conn = get_db_connection()
    df = pd.read_sql("SELECT id, customer_name, items, cancellation_reason, created_at FROM orders WHERE status = 'בוטל' ORDER BY created_at DESC LIMIT 50", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)

# --- טאב 4: ניהול מלאי ---
with tab4:
    st.subheader("ניהול מוצרים")
    
    # הוספת מוצר חדש
    with st.expander("➕ הוסף מוצר חדש"):
        c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
        new_name = c1.text_input("שם")
        new_price = c2.number_input("מחיר", min_value=0.0)
        new_stock = c3.number_input("מלאי", min_value=0, step=1)
        if c4.button("הוסף"):
            if new_name:
                conn = get_db_connection(); cur = conn.cursor()
                cur.execute("INSERT INTO products (name, price, stock) VALUES (%s, %s, %s)", (new_name, new_price, new_stock))
                conn.commit(); conn.close()
                st.success("נוסף!"); time.sleep(1); st.rerun()

    # טבלת עריכה מהירה
    conn = get_db_connection()
    df_products = pd.read_sql("SELECT id, name, price, stock FROM products ORDER BY name", conn)
    conn.close()
    
    edited_df = st.data_editor(df_products, num_rows="dynamic", key="inventory_editor")
    
    if st.button("💾 שמור שינויים במלאי"):
        conn = get_db_connection(); cur = conn.cursor()
        for i, row in edited_df.iterrows():
            # עדכון פשוט לפי ID
            cur.execute("UPDATE products SET name=%s, price=%s, stock=%s WHERE id=%s", (row['name'], row['price'], row['stock'], row['id']))
        conn.commit(); conn.close()
        st.success("המלאי עודכן בהצלחה!"); time.sleep(1); st.rerun()

# --- טאב 5: דוחות ---
with tab5:
    st.subheader("נתונים כלליים")
    conn = get_db_connection()
    c1, c2, c3 = st.columns(3)
    c1.metric("סה״כ הזמנות", pd.read_sql("SELECT COUNT(*) FROM orders", conn).iloc[0,0])
    c2.metric("הכנסות (משוער)", f"₪{pd.read_sql('SELECT SUM(total_price) FROM orders WHERE status=\'אושר\'', conn).iloc[0,0] or 0}")
    c3.metric("בוטלו", pd.read_sql("SELECT COUNT(*) FROM orders WHERE status=\'בוטל\'", conn).iloc[0,0])
    conn.close()
