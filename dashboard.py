import streamlit as st
import psycopg2
import pandas as pd
import os
import requests
import time

# הגדרות עיצוב
st.set_page_config(page_title="ניהול מכולת", layout="wide")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}
h1, h2, h3, p, label, .stMarkdown {
    color: #f0f0f0 !important;
}
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 12px 30px;
    font-weight: 600;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>🛒 ניהול הזמנות</h1>", unsafe_allow_html=True)

# כתובת הבוט שלך ב-Render (חשוב לעדכן!)
BOT_URL = os.environ.get("BOT_URL", "https://your-whatsapp-bot.onrender.com")

# חיבור למסד נתונים
def get_db_connection():
    return psycopg2.connect(os.environ.get("DB_URL"))

def notify_customer(phone, message):
    """שליחת הודעה ללקוח דרך השרת של הבוט"""
    try:
        # ניקוי המספר
        clean_phone = phone.replace("WhatsApp: ", "").replace("טלפון:", "").replace("|", "").strip()
        
        # אם המספר מתחיל בטלפון, נחלץ אותו
        if "טלפון:" in phone:
            clean_phone = phone.split("טלפון:")[-1].strip()
        
        print(f"שולח הודעה ל: {clean_phone}")
        
        res = requests.post(f"{BOT_URL}/send_update", json={
            "phone": clean_phone,
            "message": message
        }, timeout=10)
        
        return res.status_code == 200
    except Exception as e:
        st.error(f"שגיאה בשליחת הודעה: {e}")
        return False

# --- תצוגת הזמנות ---
try:
    conn = get_db_connection()
    
    # טאבים לסינון
    tab1, tab2, tab3 = st.tabs(["🔴 ממתינות לאישור", "✅ הזמנות מאושרות", "📊 כל ההזמנות"])
    
    with tab1:
        st.subheader("הזמנות ממתינות")
        
        # שליפת הזמנות ממתינות
        query_pending = """
            SELECT id, customer_name, items, total_price, status, address, created_at, delivery_time 
            FROM orders 
            WHERE status = 'ממתין לאישור'
            ORDER BY created_at DESC
        """
        df_pending = pd.read_sql(query_pending, conn)
        
        if not df_pending.empty:
            st.dataframe(df_pending, use_container_width=True)
            
            st.divider()
            
            # --- אזור אישור הזמנות ---
            st.subheader("📝 אשר הזמנה")
            
            col1, col2 = st.columns(2)
            
            with col1:
                order_id_to_process = st.number_input(
                    "הכנס מספר הזמנה (ID) לאישור:", 
                    min_value=1, 
                    step=1,
                    key="approve_order_id"
                )
                
            with col2:
                delivery_time = st.text_input(
                    "זמן הגעה משוער:", 
                    "20 דקות",
                    key="delivery_time_input"
                )
            
            if st.button("✅ אשר הזמנה ושלח הודעה ללקוח", type="primary"):
                # שליפת פרטי הלקוח מההזמנה
                selected_order = df_pending[df_pending['id'] == order_id_to_process]
                
                if not selected_order.empty:
                    # חילוץ מספר טלפון מהכתובת
                    address_field = str(selected_order.iloc[0]['address'])
                    customer_name = str(selected_order.iloc[0]['customer_name'])
                    items = str(selected_order.iloc[0]['items'])
                    
                    # נסיון לחלץ טלפון
                    customer_phone = ""
                    if "טלפון:" in address_field:
                        customer_phone = address_field.split("טלפון:")[-1].split("|")[0].strip()
                    elif "WhatsApp:" in address_field:
                        customer_phone = address_field.split("WhatsApp:")[-1].strip()
                    
                    if customer_phone:
                        # עדכון סטטוס בדאטהבייס
                        cur = conn.cursor()
                        cur.execute(
                            "UPDATE orders SET status = 'אושר', delivery_time = %s, approved_at = NOW() WHERE id = %s", 
                            (delivery_time, order_id_to_process)
                        )
                        conn.commit()
                        cur.close()
                        
                        # שליחת הודעה
                        msg_text = f"""🎉 שלום {customer_name}!

ההזמנה שלך אושרה ויצאה לדרך! 🛵

📦 הזמנה #{order_id_to_process}
🛒 פריטים: {items}
⏰ זמן הגעה משוער: {delivery_time}

✨ ההזמנה בהכנה ובדרך אליך!

תודה שבחרת בנו 🙏"""
                        
                        if notify_customer(customer_phone, msg_text):
                            st.success(f"✅ הזמנה {order_id_to_process} אושרה והודעה נשלחה ללקוח!")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.warning("⚠️ ההזמנה עודכנה ב-DB, אבל נכשלה שליחת הוואטסאפ.")
                            st.info(f"מספר הטלפון שניסינו: {customer_phone}")
                    else:
                        st.error("❌ לא נמצא מספר טלפון בהזמנה!")
                        st.info(f"שדה כתובת: {address_field}")
                else:
                    st.warning("⚠️ מספר הזמנה לא נמצא ברשימת ההמתנה.")
        else:
            st.info("📭 אין הזמנות ממתינות לאישור")
    
    with tab2:
        st.subheader("הזמנות מאושרות")
        
        # שליפת הזמנות מאושרות
        query_approved = """
            SELECT id, customer_name, items, total_price, status, address, created_at, approved_at, delivery_time 
            FROM orders 
            WHERE status = 'אושר'
            ORDER BY approved_at DESC
        """
        df_approved = pd.read_sql(query_approved, conn)
        
        if not df_approved.empty:
            st.dataframe(df_approved, use_container_width=True)
            
            st.divider()
            
            # מחיקת הזמנה מאושרת
            st.subheader("🗑️ מחק הזמנה מאושרת")
            delete_order_id = st.number_input(
                "הכנס מספר הזמנה למחיקה:", 
                min_value=1, 
                step=1,
                key="delete_approved_order_id"
            )
            
            if st.button("🗑️ מחק הזמנה", type="secondary"):
                cur = conn.cursor()
                cur.execute("DELETE FROM orders WHERE id = %s AND status = 'אושר'", (delete_order_id,))
                conn.commit()
                cur.close()
                st.success(f"✅ הזמנה {delete_order_id} נמחקה!")
                time.sleep(1)
                st.rerun()
        else:
            st.info("📭 אין הזמנות מאושרות")
    
    with tab3:
        st.subheader("כל ההזמנות")
        
        # שליפת כל ההזמנות
        query_all = """
            SELECT id, customer_name, items, total_price, status, address, created_at, approved_at, delivery_time, cancellation_reason
            FROM orders 
            ORDER BY created_at DESC
            LIMIT 100
        """
        df_all = pd.read_sql(query_all, conn)
        
        if not df_all.empty:
            st.dataframe(df_all, use_container_width=True)
            
            # סטטיסטיקות
            st.divider()
            st.subheader("📊 סטטיסטיקות")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_orders = len(df_all)
                st.metric("📦 סה\"כ הזמנות", total_orders)
            
            with col2:
                pending_orders = len(df_all[df_all['status'] == 'ממתין לאישור'])
                st.metric("⏳ ממתינות", pending_orders)
            
            with col3:
                approved_orders = len(df_all[df_all['status'] == 'אושר'])
                st.metric("✅ מאושרות", approved_orders)
            
            with col4:
                canceled_orders = len(df_all[df_all['status'] == 'בוטל'])
                st.metric("❌ מבוטלות", canceled_orders)
            
            # הכנסות
            st.divider()
            total_revenue = df_all[df_all['status'] == 'אושר']['total_price'].sum()
            st.metric("💰 סה\"כ הכנסות מהזמנות מאושרות", f"₪{total_revenue:.2f}")
        else:
            st.info("📭 אין הזמנות במערכת")
    
    conn.close()
    
    # כפתור רענון
    st.divider()
    if st.button("🔄 רענן נתונים"):
        st.rerun()

except Exception as e:
    st.error(f"❌ שגיאה כללית: {e}")
    import traceback
    st.code(traceback.format_exc())
