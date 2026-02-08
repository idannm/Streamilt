import streamlit as st
import google.generativeai as genai
import psycopg2
import pandas as pd
import json
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

# עיצוב CSS יוקרתי (Dark Mode)
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #1e1e2f 0%, #252540 100%); color: white; }
    h1 { color: #ff6b6b !important; text-align: center; }
    h2, h3 { color: #feca57 !important; }
    .stDataFrame { background-color: rgba(255,255,255,0.05); border-radius: 10px; }
    .stButton>button { background-color: #ff6b6b; color: white; border-radius: 20px; border: none; }
    .stButton>button:hover { background-color: #ff4757; }
    .success-msg { color: #2ed573; font-weight: bold; padding: 10px; border: 1px solid #2ed573; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. חיבורים ומשתנים ---
DB_URL = os.environ.get("DB_URL")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
BOT_URL = "https://minimarket-ocfq.onrender.com"  # שנה לכתובת שלך!
INTERNAL_SECRET = os.environ.get("INTERNAL_SECRET", "123")

# חיבור ל-Gemini
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

def get_db_connection():
    return psycopg2.connect(DB_URL)

# --- 3. פונקציות עזר ---

def get_inventory_for_ai():
    """שליפת המלאי כטקסט עבור ה-AI"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT name, price FROM products WHERE stock > 0")
        items = cur.fetchall()
        conn.close()
        if items: return ", ".join([f"{i[0]} ({i[1]}₪)" for i in items])
        return "כרגע אין סחורה"
    except: return "שגיאה בטעינת מלאי"

def notify_customer(phone, message):
    """שליחת הודעת וואטסאפ ללקוח דרך הבוט"""
    try:
        clean_phone = str(phone).replace("WhatsApp:", "").replace(" ", "").replace("-", "").strip()
        if clean_phone.startswith("0"): clean_phone = "972" + clean_phone[1:]
        
        # שליחה עם הסיסמה הסודית
        res = requests.post(
            f"{BOT_URL}/send_update", 
            json={"phone": clean_phone, "message": message},
            headers={"X-Internal-Secret": INTERNAL_SECRET}
        )
        return res.status_code == 200
    except: return False

def save_order_from_chat(chat_text):
    """שימוש ב-Gemini כדי להמיר את השיחה להזמנה"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        נתח את השיחה וחלץ JSON תקין בלבד:
        {{ "name": "שם הלקוח", "phone": "טלפון", "address": "כתובת מלאה", "items": "פירוט מוצרים", "total": 0 }}
        השיחה: {chat_text}
        """
        response = model.generate_content(prompt)
        # ניקוי הטקסט כדי לקבל רק JSON
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO orders (customer_name, items, total_price, address, status) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (data.get('name'), data.get('items'), 0, f"{data.get('address')} | טלפון: {data.get('phone')}", 'ממתין לאישור')
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"שגיאה בשמירה: {e}")
        return False

# --- 4. מסך כניסה (Login) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<br><br><h1 style='color: white;'>🔒 כניסה למערכת</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        password = st.text_input("הכנס סיסמת מנהל:", type="password")
        if st.button("כנס למערכת"):
            if password == "12345":  # הסיסמה שלך
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("סיסמה שגויה")
    st.stop()

# --- 5. המערכת הראשית (טאבים) ---
st.title("🛒 דשבורד מכולת - הזוג")

tab1, tab2, tab3 = st.tabs(["📋 ניהול הזמנות", "📦 ניהול מלאי", "💬 צ'אט לקוחות (סימולציה)"])

# --- טאב 1: ניהול הזמנות ---
with tab1:
    st.header("הזמנות פתוחות")
    
    # כפתור רענון
    if st.button("🔄 רענן טבלה"):
        st.rerun()

    conn = get_db_connection()
    df = pd.read_sql("SELECT id, customer_name, items, status, address, created_at FROM orders ORDER BY created_at DESC", conn)
    conn.close()

    # טבלה אינטראקטיבית
    st.dataframe(df, use_container_width=True)

    st.divider()
    
    # אזור פעולות על הזמנה
    c1, c2 = st.columns(2)
    with c1:
        order_id = st.number_input("מספר הזמנה לטיפול:", min_value=1, step=1)
    with c2:
        delivery_time = st.text_input("זמן משוער:", "20 דקות")

    if st.button("✅ אשר הזמנה ושלח וואטסאפ ללקוח"):
        try:
            # משיכת פרטי ההזמנה
            row = df[df['id'] == order_id]
            if not row.empty:
                # עדכון סטטוס
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("UPDATE orders SET status = 'אושר' WHERE id = %s", (order_id,))
                conn.commit()
                conn.close()

                # שליחת הודעה
                # ננסה לחלץ טלפון מהשדה address או שנניח שהוא שמור שם
                raw_address = row.iloc[0]['address']
                # הנחה: הטלפון נמצא אחרי המילה "טלפון:" או בסוף המחרוזת
                # כאן אנחנו שולחים את כל הסטרינג לבוט שינסה לנקות אותו
                msg = f"היי {row.iloc[0]['customer_name']}! ההזמנה (#{order_id}) אושרה ויצאה לדרך. זמן משוער: {delivery_time}. תודה!"
                
                # חילוץ מספר הטלפון מתוך שדה הכתובת (אם שמרת אותו שם כפי שעשינו בקוד הבוט)
                phone_part = raw_address.split("טלפון:")[-1].strip() if "טלפון:" in raw_address else raw_address
                
                if notify_customer(phone_part, msg):
                    st.success(f"הזמנה {order_id} אושרה והודעה נשלחה!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("ההזמנה אושרה ביומן, אבל לא הצלחתי לשלוח וואטסאפ.")
            else:
                st.error("לא מצאתי הזמנה עם המספר הזה.")
        except Exception as e:
            st.error(f"שגיאה: {e}")

# --- טאב 2: ניהול מלאי ---
with tab2:
    st.header("עדכון מוצרים ומחירים")
    
    conn = get_db_connection()
    products_df = pd.read_sql("SELECT id, name, price, stock FROM products ORDER BY name", conn)
    conn.close()
    
    # טבלה עריכה (Data Editor)
    edited_df = st.data_editor(products_df, num_rows="dynamic", key="inventory_editor")
    
    if st.button("💾 שמור שינויים במלאי"):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            # לולאה לשמירת השינויים (פשוט מוחקים ומכניסים מחדש או מעדכנים - כאן נלך על פשוט)
            # בשיטות מתקדמות משתמשים ב-UPSERT, כאן נעשה עדכון לכל שורה ששונתה
            # לצורך הפשטות בקוד הזה: המשתמש צריך לעדכן ב-SQL או שנבנה לוגיקה מורכבת.
            # נעשה משהו פשוט: נעדכן מחירים ומלאי לפי ID
            
            for index, row in edited_df.iterrows():
                cur.execute(
                    "UPDATE products SET price = %s, stock = %s, name = %s WHERE id = %s",
                    (row['price'], row['stock'], row['name'], row['id'])
                )
                
            conn.commit()
            conn.close()
            st.success("המלאי עודכן בהצלחה!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"שגיאה בשמירה: {e}")

# --- טאב 3: צ'אט לקוחות (סימולציה) ---
with tab3:
    st.subheader("בדיקת הזמנה דרך האתר (כמו לקוח)")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("מה תרצו להזמין?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # לוגיקה של Gemini
        inventory = get_inventory_for_ai()
        
        # המרת היסטוריה
        gemini_hist = []
        for m in st.session_state.messages[:-1]:
            role = "model" if m["role"] == "assistant" else "user"
            gemini_hist.append({"role": role, "parts": [m["content"]]})
            
        model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=f"אתה מוכר במכולת. המלאי: {inventory}. כשלקוח נותן שם, כתובת ומוצרים, כתוב בסוף: FINALIZE_ORDER")
        chat = model.start_chat(history=gemini_hist)
        
        try:
            response = chat.send_message(prompt)
            bot_text = response.text
            
            with st.chat_message("assistant"):
                st.markdown(bot_text.replace("FINALIZE_ORDER", ""))
            
            st.session_state.messages.append({"role": "assistant", "content": bot_text})
            
            if "FINALIZE_ORDER" in bot_text:
                full_chat = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                if save_order_from_chat(full_chat):
                    st.balloons()
                    st.success("ההזמנה נשלחה למערכת בהצלחה!")
        except Exception as e:
            st.error(f"שגיאת AI: {e}")
