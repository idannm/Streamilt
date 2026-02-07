import streamlit as st
from groq import Groq
import psycopg2
import pandas as pd
from datetime import datetime
import json
import os
import time

# --- הגדרות עמוד ---
st.set_page_config(
    page_title="מיני מארקט הזוג",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- עיצוב ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    
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
    
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .stChatMessage[data-testid="user-message"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
    }
    
    .stChatMessage[data-testid="assistant-message"] {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border: none;
    }
    
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
    
    .css-1d391kg, [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-right: 2px solid rgba(255, 255, 255, 0.1);
    }
    
    h1, h2, h3, p, label, .stMarkdown {
        color: #f0f0f0 !important;
    }
    
    .dataframe {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        color: #f0f0f0;
    }
    
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
    
    .stChatInput > div > div > input {
        background-color: white !important;
        color: #000000 !important;
        font-weight: 500;
    }
    
    .stSuccess {
        background-color: rgba(46, 213, 115, 0.1);
        border: 1px solid #2ed573;
        border-radius: 10px;
        color: #2ed573;
    }
    
    .stError {
        background-color: rgba(255, 71, 87, 0.1);
        border: 1px solid #ff4757;
        border-radius: 10px;
        color: #ff4757;
    }
    
    .main .block-container {
        padding-bottom: 150px;
    }
    
    /* עיצוב כרטיס הזמנה */
    .user-order-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border: 2px solid rgba(102, 126, 234, 0.3);
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# --- חיבורים ---
@st.cache_resource
def init_connections():
    DB_URL = os.environ.get("DB_URL")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    return DB_URL, GROQ_API_KEY

DB_URL, GROQ_API_KEY = init_connections()

if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)
else:
    st.error("❌ חסר GROQ_API_KEY")
    st.stop()

def get_db_connection():
    return psycopg2.connect(DB_URL)

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
        st.error(f"❌ שגיאה: {e}")
        return False

def validate_phone(phone):
    phone = phone.replace(" ", "").replace("-", "")
    if not phone.isdigit():
        return False, "מספר הטלפון חייב להכיל רק ספרות"
    if len(phone) == 10 and phone.startswith("0"):
        return True, phone
    elif len(phone) == 9:
        return True, "0" + phone
    else:
        return False, "מספר טלפון ישראלי חייב להכיל 10 ספרות"

def validate_address(address):
    if len(address) < 5:
        return False, "הכתובת קצרה מדי"
    has_letter = any(c.isalpha() for c in address)
    has_number = any(c.isdigit() for c in address)
    if not has_letter or not has_number:
        return False, "נא להזין כתובת מלאה"
    return True, address

def validate_name(name):
    if len(name) < 2:
        return False, "השם קצר מדי"
    words = name.split()
    if len(words) < 2:
        return False, "נא להזין שם מלא"
    if any(len(word) < 2 for word in words):
        return False, "כל חלק בשם חייב להכיל לפחות 2 תווים"
    return True, name

def save_order_to_db(chat_history):
    prompt = f"""
    קרא את השיחה וחלץ:
    {chat_history}
    
    JSON: {{"name": "שם מלא", "phone": "טלפון", "address": "כתובת", "items": "מוצרים", "total": מספר}}
    """
    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "החזר רק JSON תקין."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        ).choices[0].message.content.strip()
        
        if "{" in res and "}" in res:
            res = res[res.find("{"):res.rfind("}")+1]
            data = json.loads(res)
            
            name = str(data.get('name', '')).strip()
            phone = str(data.get('phone', '')).strip()
            address = str(data.get('address', '')).strip()
            items = str(data.get('items', '')).strip()
            total = float(data.get('total', 0))
            
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
            
            if not items or len(items) < 3:
                errors.append("❌ פריטים: לא נמצאו")
            
            if total <= 0:
                errors.append("❌ סכום: חייב להיות גדול מ-0")
            
            if errors:
                st.error("⚠️ בעיות בהזמנה:")
                for error in errors:
                    st.warning(error)
                st.info("💡 תקן את הפרטים")
                return False
            
            full_info = f"{address} | טלפון: {phone}"
            
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO orders (customer_name, items, total_price, address, status) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (name, items, total, full_info, 'ממתין לאישור')
            )
            order_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            
            st.session_state.current_order_id = order_id
            st.session_state.user_phone = phone
            st.session_state.user_name = name
            return True
            
    except Exception as e:
        st.error(f"❌ שגיאה: {e}")
        return False
    return False

# --- ממשק ---
if 'store_name' not in st.session_state:
    st.session_state.store_name = "המכולת של הצדיק"

st.markdown(f'<h1 class="main-title">🛒 {st.session_state.store_name}</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">ברוכים הבאים! 🌟</p>', unsafe_allow_html=True)

# --- סיידבר ---
with st.sidebar:
    # בדיקה אם זה מנהל או משתמש רגיל
    st.markdown("### 🔐 כניסת מנהל")
    
    if 'remembered_password' not in st.session_state:
        st.session_state.remembered_password = None
    
    if st.session_state.remembered_password:
        admin_password = st.session_state.remembered_password
        st.success("✅ מנהל")
        if st.button("🚪 התנתק"):
            st.session_state.remembered_password = None
            st.rerun()
    else:
        admin_password = st.text_input("סיסמה", type="password", key="admin_pass")
        remember_me = st.checkbox("💾 זכור")
        
        if admin_password == "12345" and remember_me:
            st.session_state.remembered_password = "12345"
    
    # אם מנהל - הצג ניהול
    if admin_password == "12345":
        st.success("✅ מחובר!")
        
        admin_section = st.radio(
            "בחר:",
            ["📦 הזמנות", "🏪 מלאי"],
            label_visibility="collapsed"
        )
        
        if admin_section == "📦 הזמנות":
            st.markdown("---")
            st.markdown("### 📋 הזמנות")
            
            # רענון אוטומטי
            if st.button("🔄 רענן"):
                st.rerun()
            
            try:
                conn = get_db_connection()
                orders = pd.read_sql_query(
                    "SELECT * FROM orders ORDER BY created_at DESC LIMIT 50",
                    conn
                )
                conn.close()
                
                if not orders.empty:
                    tab1, tab2, tab3 = st.tabs(["🔴 ממתינות", "✅ מאושרות", "⭕ מבוטלות"])
                    
                    with tab1:
                        pending = orders[orders['status'] == 'ממתין לאישור']
                        if not pending.empty:
                            st.markdown(f"#### {len(pending)} הזמנות")
                            for i, row in pending.iterrows():
                                with st.expander(f"📦 {row['customer_name']}", expanded=True):
                                    st.markdown(f"**🛒 {row['items']}**")
                                    st.markdown(f"**💰 ₪{row['total_price']}**")
                                    st.markdown(f"**📍 {row['address']}**")
                                    st.markdown(f"**📅 {row['created_at']}**")
                                    
                                    delivery_time = st.text_input(
                                        "⏰ זמן הגעה:",
                                        key=f"time_{row['id']}",
                                        placeholder="14:00"
                                    )
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if st.button("✅ אשר", key=f"app_{row['id']}", use_container_width=True):
                                            if delivery_time:
                                                if run_query(
                                                    "UPDATE orders SET status='אושר', approved_at=%s, delivery_time=%s WHERE id=%s",
                                                    (datetime.now(), delivery_time, row['id'])
                                                ):
                                                    st.success("✅ אושר!")
                                                    st.rerun()
                                            else:
                                                st.error("⚠️ הזן זמן")
                                    
                                    with col2:
                                        if st.button("❌ בטל", key=f"can_{row['id']}", use_container_width=True):
                                            if run_query(
                                                "UPDATE orders SET status='בוטל', cancellation_reason=%s WHERE id=%s",
                                                ("בוטל על ידי המנהל", row['id'])
                                            ):
                                                st.success("❌ בוטל")
                                                st.rerun()
                        else:
                            st.info("📭 אין ממתינות")
                    
                    with tab2:
                        approved = orders[orders['status'] == 'אושר']
                        if not approved.empty:
                            st.markdown(f"#### {len(approved)} מאושרות")
                            for i, row in approved.iterrows():
                                with st.expander(f"✅ {row['customer_name']} - {row['delivery_time']}"):
                                    st.markdown(f"**🛒 {row['items']}**")
                                    st.markdown(f"**💰 ₪{row['total_price']}**")
                                    st.markdown(f"**📍 {row['address']}**")
                                    st.markdown(f"**⏰ {row['delivery_time']}**")
                                    
                                    if st.button("🗑️ מחק", key=f"del_app_{row['id']}", use_container_width=True):
                                        conn = get_db_connection()
                                        cur = conn.cursor()
                                        cur.execute("DELETE FROM orders WHERE id = %s", (row['id'],))
                                        conn.commit()
                                        cur.close()
                                        conn.close()
                                        st.success("✅ נמחק")
                                        st.rerun()
                        else:
                            st.info("📭 אין מאושרות")
                    
                    with tab3:
                        canceled = orders[orders['status'] == 'בוטל']
                        if not canceled.empty:
                            st.markdown(f"#### {len(canceled)} מבוטלות")
                            for i, row in canceled.iterrows():
                                with st.expander(f"⭕ {row['customer_name']}"):
                                    st.markdown(f"**🛒 {row['items']}**")
                                    st.markdown(f"**💰 ₪{row['total_price']}**")
                                    
                                    if st.button("🗑️ מחק", key=f"del_can_{row['id']}", use_container_width=True):
                                        conn = get_db_connection()
                                        cur = conn.cursor()
                                        cur.execute("DELETE FROM customer_notifications WHERE order_id = %s", (row['id'],))
                                        cur.execute("DELETE FROM orders WHERE id = %s", (row['id'],))
                                        conn.commit()
                                        cur.close()
                                        conn.close()
                                        st.success("✅ נמחק")
                                        st.rerun()
                        else:
                            st.info("אין מבוטלות")
                        
                else:
                    st.info("📭 אין הזמנות")
                    
            except Exception as e:
                st.error(f"❌ שגיאה: {e}")
        
        elif admin_section == "🏪 מלאי":
            st.markdown("---")
            st.markdown("### 📦 מלאי")
            
            try:
                conn = get_db_connection()
                inventory = pd.read_sql_query(
                    "SELECT id, name, price, stock FROM products ORDER BY name",
                    conn
                )
                conn.close()
                
                if not inventory.empty:
                    for idx, row in inventory.iterrows():
                        cols = st.columns([3, 1.5, 1.5, 1])
                        
                        with cols[0]:
                            st.markdown(f"**{row['name']}**")
                        with cols[1]:
                            st.markdown(f"₪{row['price']}")
                        with cols[2]:
                            if row['stock'] == 0:
                                st.markdown(f"🔴 {row['stock']}")
                            elif row['stock'] < 5:
                                st.markdown(f"🟡 {row['stock']}")
                            else:
                                st.markdown(f"🟢 {row['stock']}")
                        with cols[3]:
                            if st.button("🗑️", key=f"del_{row['id']}", use_container_width=True):
                                conn = get_db_connection()
                                cur = conn.cursor()
                                cur.execute("DELETE FROM products WHERE id = %s", (row['id'],))
                                conn.commit()
                                cur.close()
                                conn.close()
                                st.success("✅ נמחק")
                                st.rerun()
                    
                    st.markdown("---")
                    st.markdown("### ➕ הוסף")
                    
                    name = st.text_input("📦 שם", placeholder="חלב")
                    col1, col2 = st.columns(2)
                    with col1:
                        price = st.number_input("💰 מחיר", min_value=0.0, step=0.5, value=0.0)
                    with col2:
                        stock = st.number_input("📊 מלאי", min_value=0, step=1, value=0)
                    
                    if st.button("💾 הוסף", use_container_width=True, type="primary"):
                        if name and price > 0:
                            conn = get_db_connection()
                            cur = conn.cursor()
                            cur.execute(
                                "INSERT INTO products (name, price, stock) VALUES (%s, %s, %s)",
                                (name, price, stock)
                            )
                            conn.commit()
                            cur.close()
                            conn.close()
                            st.success("✅ נוסף!")
                            st.rerun()
                        else:
                            st.error("⚠️ מלא שם ומחיר")
                else:
                    st.info("📭 אין מוצרים")
                    
            except Exception as e:
                st.error(f"❌ שגיאה: {e}")
    
    # אם משתמש רגיל - הצג את ההזמנות שלו
    elif 'user_phone' in st.session_state and st.session_state.user_phone:
        st.markdown("---")
        st.markdown("### 📦 ההזמנות שלי")
        
        # רענון אוטומטי כל 5 שניות
        placeholder = st.empty()
        
        try:
            conn = get_db_connection()
            user_orders = pd.read_sql_query(
                "SELECT * FROM orders WHERE address LIKE %s ORDER BY created_at DESC LIMIT 10",
                conn,
                params=(f"%{st.session_state.user_phone}%",)
            )
            conn.close()
            
            if not user_orders.empty:
                for i, order in user_orders.iterrows():
                    if order['status'] == 'אושר':
                        st.markdown(f"""
                        <div class='user-order-card'>
                        <h4>✅ הזמנה #{order['id']} - אושרה!</h4>
                        <p><strong>🛒 {order['items']}</strong></p>
                        <p><strong>💰 ₪{order['total_price']}</strong></p>
                        <p><strong>⏰ הגעה: {order['delivery_time']}</strong></p>
                        <p style='color: #2ed573;'>✨ ההזמנה בדרך אליך!</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button(f"🗑️ מחק הזמנה #{order['id']}", key=f"user_del_{order['id']}"):
                            conn = get_db_connection()
                            cur = conn.cursor()
                            cur.execute("DELETE FROM orders WHERE id = %s", (order['id'],))
                            conn.commit()
                            cur.close()
                            conn.close()
                            st.success("✅ נמחק")
                            st.rerun()
                    
                    elif order['status'] == 'ממתין לאישור':
                        st.info(f"⏳ הזמנה #{order['id']} ממתינה לאישור המנהל")
                    
                    elif order['status'] == 'בוטל':
                        reason = order.get('cancellation_reason', 'לא צוין')
                        st.error(f"❌ הזמנה #{order['id']} בוטלה - {reason}")
            else:
                st.info("אין הזמנות")
                
            # רענון אוטומטי
            if st.button("🔄 רענן הזמנות"):
                st.rerun()
                
        except Exception as e:
            st.error(f"שגיאה: {e}")

# --- צ'אט ---
st.markdown("---")
st.markdown("### 💬 בואו נזמין!")

if "messages" not in st.session_state:
    st.session_state.messages = []

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
        inventory_info = "אין מוצרים זמינים"
except:
    inventory_info = "שגיאה"

# הצגת שיחה
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# קלט
if prompt := st.chat_input("הקלד הזמנה... 🛒"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    system_prompt = f"""
אתה עוזר במכולת '{st.session_state.store_name}'.

מוצרים:
{inventory_info}

הנחיות:
1. היה חביב
2. כשלקוח שואל מחיר - ספר ישר
3. כשמזמין - ספר מחיר ושאל אם רוצה עוד
4. אם אין מוצר - הצע חלופה
5. "זה הכל" - סכם ובקש:
   - שם מלא (שם + משפחה)
   - טלפון (10 ספרות)
   - כתובת (רחוב + מספר)

רק כשיש הכל - כתוב בסוף: FINALIZE_ORDER
"""
    
    try:
        with st.spinner("⏳ מכין..."):
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
            
            with st.spinner("💾 שומר..."):
                if save_order_to_db(history):
                    st.success("🎉 ההזמנה נשלחה!")
                    st.info("⏳ ממתין לאישור - תקבל עדכון בצד!")
                    time.sleep(1)
                    st.rerun()
        else:
            with st.chat_message("assistant"):
                st.markdown(response)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            
    except Exception as e:
        st.error(f"❌ שגיאה: {e}")

# פוטר
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; color: #a0a0a0; padding: 20px;'>
        <p>🛒 {st.session_state.store_name}</p>
    </div>
    """,
    unsafe_allow_html=True
)
