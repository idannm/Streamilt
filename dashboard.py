import streamlit as st
import psycopg2
import pandas as pd
import os
import requests
import time

# הגדרות עיצוב
st.set_page_config(page_title="ניהול מכולת", layout="wide")
st.markdown("<h1 style='text-align: center;'>🛒 ניהול הזמנות</h1>", unsafe_allow_html=True)

# כתובת הבוט שלך ב-Render (חשוב לעדכן!)
# תחליף את הכתובת הזו בכתובת האמיתית של הבוט שלך ב-Render
BOT_URL = "https://your-app-name.onrender.com" 

# חיבור למסד נתונים
def get_db_connection():
    return psycopg2.connect(os.environ.get("DB_URL"))

def notify_customer(phone, message):
    """שליחת הודעה ללקוח דרך השרת של הבוט"""
    try:
        # אם המספר שמור ב-DB בלי קידומת בינלאומית, נוודא שהפורמט נכון
        clean_phone = phone.replace("WhatsApp: ", "").strip()
        
        res = requests.post(f"{BOT_URL}/send_update", json={
            "phone": clean_phone,
            "message": message
        })
        return res.status_code == 200
    except Exception as e:
        st.error(f"שגיאה בשליחת הודעה: {e}")
        return False

# --- תצוגת הזמנות ---
try:
    conn = get_db_connection()
    # שליפת ההזמנות החדשות ביותר קודם
    query = "SELECT id, customer_name, items, total_price, status, address, created_at FROM orders ORDER BY created_at DESC"
    df = pd.read_sql(query, conn)
    conn.close()

    # הצגת טבלה ראשית
    st.dataframe(df)

    st.divider()
    
    # --- אזור אישור הזמנות ---
    st.subheader("📝 טיפול בהזמנה")
    
    col1, col2 = st.columns(2)
    
    with col1:
        order_id_to_process = st.number_input("הכנס מספר הזמנה (ID) לאישור:", min_value=1, step=1)
        
    with col2:
        delivery_time = st.text_input("זמן הגעה משוער (למשל: 20 דקות):", "20 דקות")

    if st.button("✅ אשר הזמנה ושלח הודעה ללקוח"):
        # 1. שליפת פרטי הלקוח מההזמנה
        selected_order = df[df['id'] == order_id_to_process]
        
        if not selected_order.empty:
            customer_phone = str(selected_order.iloc[0]['address']).split("טלפון:")[-1].strip()
            # אם המספר לא נמצא בכתובת, מנסים מהשם או משדה אחר (תלוי איך שמרת)
            # בקוד הבוט החדש שמרנו את הטלפון בתוך שדה הכתובת, אז זה יעבוד.

            # 2. עדכון סטטוס בדאטהבייס
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("UPDATE orders SET status = 'אושר' WHERE id = %s", (order_id_to_process,))
            conn.commit()
            conn.close()
            
            # 3. שליחת הודעה
            msg_text = f"שלום! ההזמנה שלך (#{order_id_to_process}) אושרה ויצאה לדרך! 🛵\nזמן משוער: {delivery_time}."
            
            if notify_customer(customer_phone, msg_text):
                st.success(f"הזמנה {order_id_to_process} אושרה והודעה נשלחה ללקוח!")
                time.sleep(2)
                st.rerun() # רענון הדף
            else:
                st.error("ההזמנה עודכנה ב-DB, אבל נכשלה שליחת הוואטסאפ.")
        else:
            st.warning("מספר הזמנה לא נמצא.")

except Exception as e:
    st.error(f"שגיאה כללית: {e}")
