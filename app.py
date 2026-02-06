import streamlit as st
from groq import Groq
import psycopg2
import pandas as pd
from datetime import datetime
import json
import re
import requests
import os 
# --- הגדרות עמוד ---
st.set_page_config(
    page_title="מיני מארקט הזוג",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- עיצוב מתקדם ---
st.markdown("""
    <style>
    /* עיצוב כללי */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    
    /* כותרת ראשית */
    .main-title {
        text-align: center;
        color: #f0f0f0;
        font-size: 3.5rem;
        font-weight: 800;
        margin-bottom: 10px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        padding: 20px;
        background: linear-gradient(90deg, #ff6b6b, #feca57);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .subtitle {
        text-align: center;
        color: #a0a0a0;
        font-size: 1.2rem;
        margin-bottom: 30px;
    }
    
    /* תיבת צ'אט */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* הודעות משתמש */
    .stChatMessage[data-testid="user-message"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
    }
    
    /* הודעות בוט */
    .stChatMessage[data-testid="assistant-message"] {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border: none;
    }
    
    /* שדה קלט */
    .stChatInputContainer {
        position: fixed;
        bottom: 20px;
        background: rgba(22, 33, 62, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 25px;
        padding: 15px;
        border: 2px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 -5px 20px rgba(0,0,0,0.3);
    }
    
    /* כפתורים */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 30px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    
    /* כרטיסי הזמנות */
    .order-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
    }
    
    .order-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        border-color: rgba(102, 126, 234, 0.5);
    }
    
    /* טאבים */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        color: #a0a0a0;
        font-weight: 600;
        padding: 12px 25px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
    }
    
    /* סיידבר */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-right: 2px solid rgba(255, 255, 255, 0.1);
    }
    
    /* טקסט */
    h1, h2, h3, p, label, .stMarkdown {
        color: #f0f0f0 !important;
    }
    
    /* טבלאות */
    .dataframe {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        color: #f0f0f0;
    }
    
    /* אינפוטים */
    .stTextInput > div > div > input {
        background-color: white !important;
        border: 2px solid rgba(102, 126, 234, 0.5) !important;
        border-radius: 10px;
        color: #000000 !important;
        padding: 12px;
        font-weight: 500;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
    }
    
    .stNumberInput > div > div > input {
        background-color: white !important;
        border: 2px solid rgba(102, 126, 234, 0.5) !important;
        border-radius: 10px;
        color: #000000 !important;
        padding: 12px;
        font-weight: 500;
    }
    
    /* תיבת הצ'אט */
    .stChatInput > div > div > input {
        background-color: white !important;
        color: #000000 !important;
        font-weight: 500;
    }
    
    /* הודעות הצלחה */
    .stSuccess {
        background-color: rgba(46, 213, 115, 0.1);
        border: 1px solid #2ed573;
        border-radius: 10px;
        color: #2ed573;
    }
    
    /* הודעות שגיאה */
    .stError {
        background-color: rgba(255, 71, 87, 0.1);
        border: 1px solid #ff4757;
        border-radius: 10px;
        color: #ff4757;
    }
    
    /* מרווח תחתון לצ'אט */
    .main .block-container {
        padding-bottom: 150px;
    }
    </style>
""", unsafe_allow_html=True)

# --- חיבורים ---
@st.cache_resource
def init_connections():
    # כאן אנחנו לא רושמים את הכתובת האמיתית! 
    # המערכת תיקח אותה אוטומטית מה-Advanced Settings
    try:
       def init_connections():
    # זה ימשוך את הנתונים מה-Environment Variables שהגדרת ב-Render
    DB_URL = os.environ.get("DB_URL")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    return DB_URL, GROQ_API_KEY

DB_URL, GROQ_API_KEY = init_connections()

# אתחול הלקוח של Groq
if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)

def get_db_connection():
    return psycopg2.connect(DB_URL)

def send_whatsapp_notification(phone_number, message):
    """שליחת הודעה לוואטסאפ של הלקוח"""
    try:
        # נקרא ל-API של הבוט
        response = requests.post(
            "http://localhost:5000/send_update",  # או הכתובת של השרת שלך
            json={
                "phone": phone_number,
                "message": message
            },
            timeout=5
        )
        return response.status_code == 200
    except:
        # אם הבוט לא רץ - לא נורא
        return False

def run_query(query, params=None):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"❌ שגיאה בביצוע השאילתה: {e}")
        return False

def validate_phone(phone):
    """בדיקת תקינות מספר טלפון ישראלי"""
    # הסרת רווחים ומקפים
    phone = phone.replace(" ", "").replace("-", "")
    
    # בדיקה שהמספר מכיל רק ספרות
    if not phone.isdigit():
        return False, "מספר הטלפון חייב להכיל רק ספרות"
    
    # בדיקת אורך (10 ספרות או 9 ספרות)
    if len(phone) == 10 and phone.startswith("0"):
        return True, phone
    elif len(phone) == 9:
        return True, "0" + phone
    else:
        return False, "מספר טלפון ישראלי חייב להכיל 10 ספרות (מתחיל ב-0) או 9 ספרות"

def validate_address(address):
    """בדיקת תקינות כתובת"""
    if len(address) < 5:
        return False, "הכתובת קצרה מדי. נא להזין רחוב ומספר בית"
    
    # בדיקה שיש לפחות אות וספרה
    has_letter = any(c.isalpha() for c in address)
    has_number = any(c.isdigit() for c in address)
    
    if not has_letter or not has_number:
        return False, "נא להזין כתובת מלאה הכוללת שם רחוב ומספר בית"
    
    return True, address

def validate_name(name):
    """בדיקת תקינות שם"""
    if len(name) < 2:
        return False, "השם קצר מדי"
    
    # בדיקה שיש לפחות שתי מילים (שם פרטי ושם משפחה)
    words = name.split()
    if len(words) < 2:
        return False, "נא להזין שם מלא (שם פרטי ושם משפחה)"
    
    # בדיקה שכל מילה מכילה לפחות 2 תווים
    if any(len(word) < 2 for word in words):
        return False, "כל חלק בשם חייב להכיל לפחות 2 תווים"
    
    return True, name

def save_order_to_db(chat_history):
    """שמירת הזמנה למסד הנתונים עם ולידציה"""
    prompt = f"""
    קרא את השיחה הבאה וחלץ את המידע הבא בדיוק:
    
    {chat_history}
    
    החזר JSON בפורמט הזה בדיוק (ללא טקסט נוסף):
    {{
        "name": "שם הלקוח המלא",
        "phone": "מספר הטלפון",
        "address": "הכתובת המלאה",
        "items": "רשימת כל המוצרים שהוזמנו",
        "total": הסכום_הכולל_כמספר
    }}
    
    חשוב: אם חסר מידע, השאר ריק אבל החזר JSON תקני.
    """
    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "אתה מחלץ מידע מדויק. החזר רק JSON תקין, ללא הסבר או טקסט נוסף."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        ).choices[0].message.content.strip()
        
        # חילוץ JSON
        if "{" in res and "}" in res:
            res = res[res.find("{"):res.rfind("}")+1]
            data = json.loads(res)
            
            # חילוץ ערכים
            name = str(data.get('name', '')).strip()
            phone = str(data.get('phone', '')).strip()
            address = str(data.get('address', '')).strip()
            items = str(data.get('items', '')).strip()
            total = float(data.get('total', 0))
            
            # ולידציה של כל השדות
            errors = []
            
            # בדיקת שם
            name_valid, name_msg = validate_name(name)
            if not name_valid:
                errors.append(f"❌ שם: {name_msg}")
            
            # בדיקת טלפון
            phone_valid, phone_msg = validate_phone(phone)
            if not phone_valid:
                errors.append(f"❌ טלפון: {phone_msg}")
            else:
                phone = phone_msg  # עדכון למספר מתוקן
            
            # בדיקת כתובת
            address_valid, address_msg = validate_address(address)
            if not address_valid:
                errors.append(f"❌ כתובת: {address_msg}")
            
            # בדיקת פריטים
            if not items or len(items) < 3:
                errors.append("❌ פריטים: לא נמצאו פריטים בהזמנה")
            
            # בדיקת סכום
            if total <= 0:
                errors.append("❌ סכום: הסכום חייב להיות גדול מ-0")
            
            # אם יש שגיאות - הצגתן
            if errors:
                st.error("⚠️ יש בעיות בפרטי ההזמנה:")
                for error in errors:
                    st.warning(error)
                st.info("💡 בבקשה תקן את הפרטים הבאים ונסה שוב")
                return False
            
            # אם הכל תקין - שמירה למסד נתונים
            full_info = f"{address} | טלפון: {phone}"
            
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO orders (customer_name, items, total_price, address, status) VALUES (%s, %s, %s, %s, %s)",
                (name, items, total, full_info, 'ממתין לאישור')
            )
            order_id = cur.lastrowid
            conn.commit()
            cur.close()
            conn.close()
            
            # שמירת מזהה ההזמנה בסשן
            st.session_state.current_order_id = order_id
            return True
            
    except Exception as e:
        st.error(f"❌ שגיאה בשמירת ההזמנה: {e}")
        return False
    return False

def update_order_in_db(order_id, chat_history):
    """עדכון הזמנה קיימת עם ולידציה"""
    prompt = f"""
    חלץ מהשיחה המעודכנת JSON:
    {chat_history}
    
    פורמט: {{"name": "שם", "phone": "טלפון", "address": "כתובת", "items": "מוצרים", "total": מספר}}
    """
    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Return ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        ).choices[0].message.content.strip()
        
        if "{" in res:
            res = res[res.find("{"):res.rfind("}")+1]
            data = json.loads(res)
            
            name = str(data.get('name', 'לקוח'))
            phone = str(data.get('phone', ''))
            address = str(data.get('address', ''))
            items = str(data.get('items', ''))
            total = float(data.get('total', 0))
            
            # ולידציה
            errors = []
            
            name_valid, name_msg = validate_name(name)
            if not name_valid:
                errors.append(f"❌ שם: {name_msg}")
            
            phone_valid, phone_msg = validate_phone(phone)
            if not phone_valid:
                errors.append(f"❌ טלפון: {phone_msg}")
            else:
                phone = phone_msg
            
            address_valid, address_msg = validate_address(address)
            if not address_valid:
                errors.append(f"❌ כתובת: {address_msg}")
            
            if errors:
                for error in errors:
                    st.warning(error)
                return False
            
            full_info = f"{address} | טלפון: {phone}"
            
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "UPDATE orders SET customer_name=%s, items=%s, total_price=%s, address=%s WHERE id=%s AND status='ממתין לאישור'",
                (name, items, total, full_info, order_id)
            )
            conn.commit()
            cur.close()
            conn.close()
            return True
    except Exception as e:
        print(f"Error updating order: {e}")
        return False
    return False

# --- ממשק משתמש ---
# שם העסק מותאם אישית
if 'store_name' not in st.session_state:
    st.session_state.store_name = "המכולת של הצדיק"

st.markdown(f'<h1 class="main-title">🛒 {st.session_state.store_name}</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">ברוכים הבאים למכולת הכי נחמדה בעיר! 🌟</p>', unsafe_allow_html=True)

# --- סיידבר לניהול ---
with st.sidebar:
    st.markdown("### 🔐 כניסת מנהל")
    
    # בדיקה אם יש סיסמה שמורה
    if 'remembered_password' not in st.session_state:
        st.session_state.remembered_password = None
    
    # אם יש סיסמה שמורה, השתמש בה
    if st.session_state.remembered_password:
        admin_password = st.session_state.remembered_password
        st.success("✅ מחובר אוטומטית")
        if st.button("🚪 התנתק"):
            st.session_state.remembered_password = None
            st.rerun()
    else:
        admin_password = st.text_input("סיסמה", type="password", key="admin_pass")
        remember_me = st.checkbox("💾 זכור אותי")
        
        if admin_password == "12345" and remember_me:
            st.session_state.remembered_password = "12345"
    
    if admin_password == "12345":
        st.success("✅ התחברת בהצלחה!")
        
        admin_section = st.radio(
            "בחר מה לנהל:",
            ["📦 ניהול הזמנות", "🏪 ניהול מלאי"],
            label_visibility="collapsed"
        )
        
        if admin_section == "📦 ניהול הזמנות":
            st.markdown("---")
            st.markdown("### 📋 מצב הזמנות")
            
            try:
                conn = get_db_connection()
                orders = pd.read_sql_query(
                    "SELECT * FROM orders ORDER BY created_at DESC LIMIT 30",
                    conn
                )
                conn.close()
                
                if not orders.empty:
                    # טאבים לסינון הזמנות
                    tab1, tab2, tab3 = st.tabs(["🔴 ממתינות", "✅ יצאו לדרך", "⭕ מבוטלות"])
                    
                    with tab1:
                        pending = orders[orders['status'] == 'ממתין לאישור']
                        if not pending.empty:
                            st.markdown(f"#### 📦 {len(pending)} הזמנות חדשות")
                            for i, row in pending.iterrows():
                                with st.expander(f"📦 {row['customer_name']}", expanded=True):
                                    st.markdown(f"**🛒 פריטים:** {row['items']}")
                                    st.markdown(f"**💰 סה״כ:** ₪{row['total_price']}")
                                    st.markdown(f"**📍 פרטים:** {row['address']}")
                                    st.markdown(f"**📅 הוזמן:** {row['created_at']}")
                                    
                                    delivery_time = st.text_input(
                                        "⏰ זמן הגעה משוער:",
                                        key=f"time_{row['id']}",
                                        placeholder="לדוגמה: 14:00"
                                    )
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if st.button("✅ אשר הזמנה", key=f"approve_{row['id']}", use_container_width=True):
                                            if delivery_time:
                                                if run_query(
                                                    "UPDATE orders SET status='אושר', approved_at=%s, delivery_time=%s WHERE id=%s",
                                                    (datetime.now(), delivery_time, row['id'])
                                                ):
                                                    st.success(f"✅ ההזמנה אושרה! זמן הגעה: {delivery_time}")
                                                    
                                                    # שליחת הודעה לוואטסאפ
                                                    whatsapp_phone = None
                                                    if "WhatsApp:" in row['address']:
                                                        whatsapp_phone = row['address'].split("WhatsApp:")[-1].strip()
                                                    
                                                    if whatsapp_phone:
                                                        whatsapp_msg = f"🎉 שלום {row['customer_name']}!\n\nההזמנה שלך אושרה!\n⏰ זמן הגעה משוער: {delivery_time}\n\n✨ ההזמנה בהכנה ובדרך אליך!"
                                                        if send_whatsapp_notification(whatsapp_phone, whatsapp_msg):
                                                            st.info("📱 הלקוח קיבל הודעה בוואטסאפ")
                                                    
                                                    st.rerun()
                                            else:
                                                st.error("⚠️ נא להזין זמן הגעה")
                                    
                                    with col2:
                                        if st.button("❌ בטל הזמנה", key=f"cancel_btn_{row['id']}", use_container_width=True):
                                            st.session_state[f'canceling_{row["id"]}'] = True
                                            st.rerun()
                                    
                                    # אם לחצו על ביטול - הצג טופס סיבה
                                    if st.session_state.get(f'canceling_{row["id"]}', False):
                                        st.markdown("---")
                                        st.markdown("### 📝 סיבת הביטול")
                                        
                                        cancel_reason = st.radio(
                                            "בחר סיבה:",
                                            ["חוסר במלאי", "טעות בהזמנה", "בקשת לקוח", "אחר"],
                                            key=f"reason_{row['id']}"
                                        )
                                        
                                        custom_reason = ""
                                        if cancel_reason == "אחר":
                                            custom_reason = st.text_area(
                                                "פרט את הסיבה:",
                                                key=f"custom_reason_{row['id']}",
                                                placeholder="כתוב כאן..."
                                            )
                                        
                                        col_confirm, col_back = st.columns(2)
                                        with col_confirm:
                                            if st.button("✔️ אשר ביטול", key=f"confirm_cancel_{row['id']}", use_container_width=True):
                                                final_reason = custom_reason if cancel_reason == "אחר" else cancel_reason
                                                
                                                if cancel_reason == "אחר" and not custom_reason:
                                                    st.error("⚠️ נא להזין סיבה")
                                                else:
                                                    # שמירת סיבת הביטול במסד נתונים
                                                    if run_query(
                                                        "UPDATE orders SET status='בוטל', cancellation_reason=%s WHERE id=%s",
                                                        (final_reason, row['id'])
                                                    ):
                                                        # שליחת הודעה ללקוח מיד
                                                        if cancel_reason == "חוסר במלאי":
                                                            notification_msg = f"שלום {row['customer_name']}, מצטערים אבל יש לנו חוסר במלאי עבור ההזמנה שלך. סיבה: {final_reason}. האם תרצה להזמין משהו אחר במקום? 😊"
                                                        else:
                                                            notification_msg = f"שלום {row['customer_name']}, ההזמנה שלך בוטלה. סיבה: {final_reason}"
                                                        
                                                        run_query(
                                                            "INSERT INTO customer_notifications (order_id, message, created_at) VALUES (%s, %s, %s)",
                                                            (row['id'], notification_msg, datetime.now())
                                                        )
                                                        
                                                        # שליחת הודעה לוואטסאפ
                                                        whatsapp_phone = None
                                                        if "WhatsApp:" in row['address']:
                                                            whatsapp_phone = row['address'].split("WhatsApp:")[-1].strip()
                                                        
                                                        if whatsapp_phone:
                                                            if send_whatsapp_notification(whatsapp_phone, notification_msg):
                                                                st.info("📱 הלקוח קיבל הודעה בוואטסאפ")
                                                        
                                                        st.success(f"✅ ההזמנה בוטלה והלקוח קיבל הודעה: {final_reason}")
                                                        del st.session_state[f'canceling_{row["id"]}']
                                                        st.rerun()
                                        
                                        with col_back:
                                            if st.button("⬅️ חזור", key=f"back_cancel_{row['id']}", use_container_width=True):
                                                del st.session_state[f'canceling_{row["id"]}']
                                                st.rerun()
                        else:
                            st.info("📭 אין הזמנות ממתינות")
                    
                    with tab2:
                        approved = orders[orders['status'] == 'אושר']
                        if not approved.empty:
                            st.markdown(f"#### 🚚 {len(approved)} הזמנות בדרך")
                            for i, row in approved.iterrows():
                                with st.expander(f"✅ {row['customer_name']} - זמן הגעה: {row['delivery_time']}"):
                                    st.markdown(f"**🛒 פריטים:** {row['items']}")
                                    st.markdown(f"**💰 סה״כ:** ₪{row['total_price']}")
                                    st.markdown(f"**📍 פרטים:** {row['address']}")
                                    st.markdown(f"**📅 הוזמן:** {row['created_at']}")
                                    st.markdown(f"**✅ אושר:** {row['approved_at']}")
                                    st.markdown(f"**⏰ זמן הגעה:** {row['delivery_time']}")
                        else:
                            st.info("📭 אין הזמנות בדרך")
                    
                    with tab3:
                        canceled = orders[orders['status'] == 'בוטל']
                        if not canceled.empty:
                            st.markdown(f"#### ⭕ {len(canceled)} הזמנות מבוטלות")
                            for i, row in canceled.iterrows():
                                reason = row.get('cancellation_reason', 'לא צוין')
                                with st.expander(f"⭕ {row['customer_name']} - {reason}"):
                                    st.markdown(f"**🛒 פריטים:** {row['items']}")
                                    st.markdown(f"**💰 סה״כ:** ₪{row['total_price']}")
                                    st.markdown(f"**📍 פרטים:** {row['address']}")
                                    st.markdown(f"**📅 הוזמן:** {row['created_at']}")
                                    st.markdown(f"**❌ סיבת ביטול:** {reason}")
                                    
                                    st.markdown("---")
                                    
                                    # כפתור מחיקה בלבן
                                    st.markdown("""
                                        <style>
                                        div[data-testid*="stButton"] button[kind="secondary"] {
                                            background: white !important;
                                            color: #1a1a2e !important;
                                            border: 2px solid #ddd !important;
                                            font-weight: 600 !important;
                                        }
                                        div[data-testid*="stButton"] button[kind="secondary"]:hover {
                                            background: #f0f0f0 !important;
                                            border-color: #ff4757 !important;
                                            color: #ff4757 !important;
                                        }
                                        </style>
                                    """, unsafe_allow_html=True)
                                    
                                    if st.button("🗑️ מחק הזמנה לצמיתות", key=f"delete_order_{row['id']}", use_container_width=True, type="secondary"):
                                        # אישור מחיקה
                                        st.session_state[f'confirm_delete_{row["id"]}'] = True
                                        st.rerun()
                                    
                                    # אם לחצו על מחיקה - הצג אישור
                                    if st.session_state.get(f'confirm_delete_{row["id"]}', False):
                                        st.warning("⚠️ האם אתה בטוח שברצונך למחוק הזמנה זו לצמיתות?")
                                        st.info("פעולה זו אינה ניתנת לביטול!")
                                        
                                        col_yes, col_no = st.columns(2)
                                        with col_yes:
                                            if st.button("✔️ כן, מחק", key=f"yes_delete_{row['id']}", use_container_width=True):
                                                # מחיקת ההזמנה
                                                conn = get_db_connection()
                                                cur = conn.cursor()
                                                
                                                # מחיקת הודעות קשורות
                                                cur.execute("DELETE FROM customer_notifications WHERE order_id = %s", (row['id'],))
                                                
                                                # מחיקת ההזמנה
                                                cur.execute("DELETE FROM orders WHERE id = %s", (row['id'],))
                                                
                                                conn.commit()
                                                cur.close()
                                                conn.close()
                                                
                                                st.success(f"✅ ההזמנה של {row['customer_name']} נמחקה לצמיתות")
                                                del st.session_state[f'confirm_delete_{row["id"]}']
                                                st.rerun()
                                        
                                        with col_no:
                                            if st.button("❌ לא, בטל", key=f"no_delete_{row['id']}", use_container_width=True):
                                                del st.session_state[f'confirm_delete_{row["id"]}']
                                                st.rerun()
                        else:
                            st.info("אין הזמנות מבוטלות")
                    
                    # סטטיסטיקות
                    st.markdown("---")
                    st.markdown("### 📊 סטטיסטיקות")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("⏳ ממתינות", len(orders[orders['status'] == 'ממתין לאישור']))
                    with col2:
                        st.metric("✅ יצאו לדרך", len(orders[orders['status'] == 'אושר']))
                    with col3:
                        st.metric("⭕ מבוטלות", len(orders[orders['status'] == 'בוטל']))
                        
                else:
                    st.info("📭 אין הזמנות כרגע")
                    
            except Exception as e:
                st.error(f"❌ שגיאה בטעינת הזמנות: {e}")
        
        elif admin_section == "🏪 ניהול מלאי":
            st.markdown("---")
            st.markdown("### 📦 מלאי נוכחי")
            
            # סרגל חיפוש
            search_term = st.text_input("🔍 חפש מוצר...", placeholder="הקלד שם מוצר לחיפוש", key="search_product")
            
            try:
                conn = get_db_connection()
                if search_term:
                    # חיפוש עם LIKE
                    inventory = pd.read_sql_query(
                        "SELECT id, name, price, stock FROM products WHERE name ILIKE %s ORDER BY name",
                        conn,
                        params=(f"%{search_term}%",)
                    )
                else:
                    inventory = pd.read_sql_query(
                        "SELECT id, name, price, stock FROM products ORDER BY name",
                        conn
                    )
                conn.close()
                
                if not inventory.empty:
                    # הצגת תוצאות חיפוש
                    if search_term:
                        st.info(f"🔍 נמצאו {len(inventory)} מוצרים המכילים '{search_term}'")
                    
                    st.markdown("""
                    <div style='background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
                    """, unsafe_allow_html=True)
                    
                    header_cols = st.columns([3, 1.5, 1.5, 1, 1])
                    with header_cols[0]:
                        st.markdown("**📦 שם המוצר**")
                    with header_cols[1]:
                        st.markdown("**💰 מחיר**")
                    with header_cols[2]:
                        st.markdown("**📊 מלאי**")
                    with header_cols[3]:
                        st.markdown("**✏️**")
                    with header_cols[4]:
                        st.markdown("**🗑️**")
                    
                    st.markdown("---")
                    
                    for idx, row in inventory.iterrows():
                        cols = st.columns([3, 1.5, 1.5, 1, 1])
                        
                        with cols[0]:
                            st.markdown(f"**{row['name']}**")
                        with cols[1]:
                            st.markdown(f"₪{row['price']}")
                        with cols[2]:
                            if row['stock'] == 0:
                                st.markdown(f"🔴 **{row['stock']}**")
                            elif row['stock'] < 5:
                                st.markdown(f"🟡 **{row['stock']}**")
                            else:
                                st.markdown(f"🟢 **{row['stock']}**")
                        with cols[3]:
                            if st.button("✏️", key=f"edit_{row['id']}", use_container_width=True):
                                st.session_state.editing_product = {
                                    'id': row['id'],
                                    'name': row['name'],
                                    'price': float(row['price']),
                                    'stock': int(row['stock'])
                                }
                                st.rerun()
                        with cols[4]:
                            if st.button("🗑️", key=f"delete_{row['id']}", use_container_width=True):
                                conn = get_db_connection()
                                cur = conn.cursor()
                                cur.execute("DELETE FROM products WHERE id = %s", (row['id'],))
                                conn.commit()
                                cur.close()
                                conn.close()
                                st.success(f"✅ המוצר '{row['name']}' נמחק!")
                                st.rerun()
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.markdown("---")
                    
                    if hasattr(st.session_state, 'editing_product') and st.session_state.editing_product:
                        st.markdown("### ✏️ עריכת מוצר")
                        product = st.session_state.editing_product
                        
                        product_name = st.text_input("📦 שם המוצר", value=product['name'], key="edit_name")
                        col1, col2 = st.columns(2)
                        with col1:
                            product_price = st.number_input("💰 מחיר (₪)", min_value=0.0, step=0.5, value=product['price'], key="edit_price")
                        with col2:
                            product_stock = st.number_input("📊 כמות במלאי", min_value=0, step=1, value=product['stock'], key="edit_stock")
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.button("💾 שמור שינויים", use_container_width=True, type="primary"):
                                if product_name and product_price >= 0:
                                    conn = get_db_connection()
                                    cur = conn.cursor()
                                    cur.execute(
                                        "UPDATE products SET name = %s, price = %s, stock = %s WHERE id = %s",
                                        (product_name, product_price, product_stock, product['id'])
                                    )
                                    conn.commit()
                                    cur.close()
                                    conn.close()
                                    st.success(f"✅ המוצר '{product_name}' עודכן!")
                                    del st.session_state.editing_product
                                    st.rerun()
                                else:
                                    st.error("⚠️ נא למלא את כל הפרטים")
                        
                        with col_cancel:
                            if st.button("❌ ביטול", use_container_width=True):
                                del st.session_state.editing_product
                                st.rerun()
                    else:
                        st.markdown("### ➕ הוסף מוצר חדש")
                        
                        product_name = st.text_input("📦 שם המוצר", placeholder="לדוגמה: חלב")
                        col1, col2 = st.columns(2)
                        with col1:
                            product_price = st.number_input("💰 מחיר (₪)", min_value=0.0, step=0.5, value=0.0)
                        with col2:
                            product_stock = st.number_input("📊 כמות במלאי", min_value=0, step=1, value=0)
                        
                        # מניעת לחיצה כפולה
                        if 'adding_product' not in st.session_state:
                            st.session_state.adding_product = False
                        
                        if st.button("💾 הוסף מוצר", use_container_width=True, type="primary", disabled=st.session_state.adding_product):
                            if product_name and product_price > 0:
                                st.session_state.adding_product = True
                                conn = get_db_connection()
                                cur = conn.cursor()
                                cur.execute("SELECT id FROM products WHERE name = %s", (product_name,))
                                existing = cur.fetchone()
                                
                                if existing:
                                    st.error(f"⚠️ המוצר '{product_name}' כבר קיים!")
                                    st.session_state.adding_product = False
                                else:
                                    cur.execute(
                                        "INSERT INTO products (name, price, stock) VALUES (%s, %s, %s)",
                                        (product_name, product_price, product_stock)
                                    )
                                    conn.commit()
                                    st.success(f"✅ המוצר '{product_name}' נוסף!")
                                    st.session_state.adding_product = False
                                
                                cur.close()
                                conn.close()
                                st.rerun()
                            else:
                                st.error("⚠️ נא למלא שם ומחיר")
                else:
                    if search_term:
                        st.warning(f"❌ לא נמצאו מוצרים המכילים '{search_term}'")
                        st.info("💡 נסה לחפש במילים אחרות או נקה את החיפוש")
                    else:
                        st.info("📭 אין מוצרים במלאי")
                    st.markdown("---")
                    st.markdown("### ➕ הוסף מוצר ראשון")
                    
                    product_name = st.text_input("📦 שם המוצר", placeholder="לדוגמה: חלב")
                    col1, col2 = st.columns(2)
                    with col1:
                        product_price = st.number_input("💰 מחיר (₪)", min_value=0.0, step=0.5)
                    with col2:
                        product_stock = st.number_input("📊 כמות במלאי", min_value=0, step=1)
                    
                    # מניעת לחיצה כפולה
                    if 'adding_first_product' not in st.session_state:
                        st.session_state.adding_first_product = False
                    
                    if st.button("💾 הוסף מוצר", use_container_width=True, type="primary", disabled=st.session_state.adding_first_product):
                        if product_name and product_price > 0:
                            st.session_state.adding_first_product = True
                            conn = get_db_connection()
                            cur = conn.cursor()
                            cur.execute(
                                "INSERT INTO products (name, price, stock) VALUES (%s, %s, %s)",
                                (product_name, product_price, product_stock)
                            )
                            conn.commit()
                            cur.close()
                            conn.close()
                            st.success(f"✅ המוצר '{product_name}' נוסף!")
                            st.session_state.adding_first_product = False
                            st.rerun()
                        else:
                            st.error("⚠️ נא למלא שם ומחיר")
                    
            except Exception as e:
                st.error(f"❌ שגיאה בטעינת המלאי: {e}")
    
    elif admin_password and admin_password != "12345":
        st.error("❌ סיסמה שגויה")

# --- צ'אט הזמנות ---
st.markdown("---")
st.markdown("### 💬 בואו נזמין!")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.current_order_id = None
    st.session_state.order_pending = False

# בדיקת סטטוס הזמנה
if hasattr(st.session_state, 'current_order_id') and st.session_state.current_order_id:
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT status, delivery_time, cancellation_reason FROM orders WHERE id=%s",
            (st.session_state.current_order_id,)
        )
        result = cur.fetchone()
        
        cur.execute(
            "SELECT message FROM customer_notifications WHERE order_id=%s ORDER BY created_at DESC LIMIT 1",
            (st.session_state.current_order_id,)
        )
        notification = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if result:
            if result[0] == 'אושר':
                st.success(f"🎉 ההזמנה שלך אושרה! המשלוח יגיע בשעה: {result[1]}")
                st.info("✨ ההזמנה בהכנה ובדרך אליך!")
                
                if st.button("🔄 התחל הזמנה חדשה"):
                    st.session_state.messages = []
                    st.session_state.current_order_id = None
                    st.session_state.order_pending = False
                    st.rerun()
            
            elif result[0] == 'בוטל':
                reason = result[2] if result[2] else "לא צוין"
                st.error(f"😔 ההזמנה שלך בוטלה")
                
                if notification:
                    st.info(notification[0])
                else:
                    st.info(f"סיבת הביטול: {reason}")
                
                if reason == "חוסר במלאי":
                    st.markdown("---")
                    st.markdown("### 🔄 תרצה להזמין משהו אחר?")
                    
                    try:
                        conn = get_db_connection()
                        available_products = pd.read_sql_query(
                            "SELECT name, price FROM products WHERE stock > 0 ORDER BY name",
                            conn
                        )
                        conn.close()
                        
                        if not available_products.empty:
                            st.markdown("**המוצרים הזמינים עכשיו:**")
                            for _, prod in available_products.iterrows():
                                st.markdown(f"• {prod['name']} - ₪{prod['price']}")
                    except:
                        pass
                
                if st.button("🔄 התחל הזמנה חדשה", key="new_order_after_cancel"):
                    st.session_state.messages = []
                    st.session_state.current_order_id = None
                    st.session_state.order_pending = False
                    st.rerun()
    except:
        pass

# טעינת מלאי
try:
    conn = get_db_connection()
    inventory_df = pd.read_sql_query(
        "SELECT name, price FROM products WHERE stock > 0 ORDER BY name",
        conn
    )
    conn.close()
    
    if not inventory_df.empty:
        inventory_list = []
        for _, row in inventory_df.iterrows():
            inventory_list.append(f"• {row['name']} - ₪{row['price']}")
        inventory_info = "\n".join(inventory_list)
    else:
        inventory_info = "אין מוצרים זמינים כרגע"
except:
    inventory_info = "שגיאה בטעינת המלאי"

# הצגת היסטוריית שיחה
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# קלט משתמש
if prompt := st.chat_input("הקלד כאן את ההזמנה שלך... 🛒"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    system_prompt = f"""
אתה עוזר חמוד ונחמד במכולת '{st.session_state.store_name}'. תמיד תהיה חביב, סבלני ועוזר.

המוצרים שיש לנו במכולת:
{inventory_info}

איך להתנהג:
1. תהיה טבעי ונחמד, כמו חבר
2. כשלקוח שואל על מחיר - ספר לו ישר
3. כשלקוח מזמין מוצר - ספר מחיר ושאל אם רוצה עוד
4. אם מוצר לא קיים - תגיד "מצטער, אין לנו את זה. יש לנו [הצע חלופה]"
5. כשלקוח אומר "זה הכל" - תן סיכום ובקש פרטים
6. השתמש בעברית פשוטה, ללא קיצורים

חשוב מאוד - בקש פרטים מלאים:
- שם מלא (שם פרטי ושם משפחה)
- מספר טלפון ישראלי (10 ספרות)
- כתובת מלאה (רחוב ומספר בית)

דוגמאות:
לקוח: "כמה עולה לחם?"
אתה: "לחם עולה 8.5 ש״ח 🍞"

לקוח: "אני רוצה חלב"
אתה: "בטח! חלב זה 6 ש״ח 🥛 רוצה להוסיף עוד משהו?"

לקוח: "זה הכל"
אתה: "מעולה! 
🛒 הזמנת: חלב
💰 סה״כ: 6 ש״ח

עכשיו רק צריך ממך:
👤 שם מלא (שם פרטי ושם משפחה)
📱 מספר טלפון (10 ספרות)
📍 כתובת מלאה למשלוח (רחוב ומספר בית)"

חשוב:
- אל תכתוב מה אתה חושב או מתכנן
- דבר ישירות ובפשטות
- רק אחרי שיש לך שם מלא, טלפון תקין וכתובת מלאה - כתוב בסוף: FINALIZE_ORDER
- אם חסרים פרטים או שהם לא מלאים - בקש אותם שוב
"""
    
    try:
        with st.spinner("⏳ מכין תשובה..."):
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt}
                ] + st.session_state.messages,
                temperature=0.7,
                max_tokens=800
            ).choices[0].message.content
        
        if "FINALIZE_ORDER" in response:
            clean_response = response.replace("FINALIZE_ORDER", "").strip()
            
            with st.chat_message("assistant"):
                st.markdown(clean_response)
            
            st.session_state.messages.append({"role": "assistant", "content": clean_response})
            
            history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
            
            with st.spinner("💾 שומר את ההזמנה..."):
                if hasattr(st.session_state, 'current_order_id') and st.session_state.current_order_id:
                    if update_order_in_db(st.session_state.current_order_id, history):
                        st.info("✏️ ההזמנה עודכנה בהצלחה!")
                        st.session_state.order_pending = True
                    else:
                        st.warning("⚠️ לא ניתן לעדכן - ייתכן שההזמנה כבר אושרה")
                else:
                    if save_order_to_db(history):
                        st.success("🎉 ההזמנה נשלחה בהצלחה!")
                        st.info("⏳ ההזמנה שלך ממתינה לאישור המנהל.")
                        st.session_state.order_pending = True
        else:
            with st.chat_message("assistant"):
                st.markdown(response)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            
    except Exception as e:
        st.error(f"❌ שגיאה בתקשורת: {e}")

# --- פוטר ---
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; color: #a0a0a0; padding: 20px;'>
        <p>🛒 {st.session_state.store_name} | שירות לקוחות מעולה בכל שעה</p>
        <p style='font-size: 0.9rem;'>🔒 כל ההזמנות מאובטחות ומוגנות</p>
    </div>
    """,
    unsafe_allow_html=True
)
