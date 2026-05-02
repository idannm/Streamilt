import streamlit as st
import psycopg2
import pandas as pd
import os
import requests
import time
from datetime import datetime, timedelta

# --- 1. הגדרות דף ---
st.set_`. זה נראה כמו אקסל יוקרתי ומאפשר לעדכן מחירים ומלאי ב-page_config(
    page_title="ניהול מכולת - הזוג", 
    page_icon="💰2 שניות.
4.  **דאשבורד סיכום:** הוספתי "מ", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# משבט על" בראש הדף עם נתונים על כמות הזמנות פתוחות ותלונות.תני סביבה
DB_URL = os.environ.get("DB_URL")
BOT_URL = "https://
5.  **רענון אוטומטי:** המערכת תבדוק הזמנות חדשות ברminimarket-ocfq.onrender.com" 
INTERNAL_SECRET = os.environ.get("INTERNAL_SECRET", "123")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "קע בלי שבעל הבית יצטרך ללחוץ על "רענן".

### הקוד המש12345")

# --- 2. עיצוב מתקדם (CSS) ---
stודרג:

```python
import streamlit as st
import psycopg2
import pandas as pd
import os
import requests
import time.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2
from datetime import datetime

# --- 1. הגדרות תצורה ---
st.set_page?family=Assistant:wght@300;400;700&display=swap');
    
    html_config(
    page_title="ניהול הזוג - Premium", 
    page_icon="👑, body, [class*="st-"] {
        font-family: 'Assistant', sans-serif;
        direction", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# מש: rtl;
        text-align: right;
    }

    .stApp {
        background: radialתני סביבה
DB_URL = os.environ.get("DB_URL")
BOT_URL = "https://minimarket-ocfq.onrender.com" 
INTERNAL_SECRET = os.environ-gradient(circle at top right, #1e293b, #0f172a);
        .get("INTERNAL_SECRET", "123")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "12345")
# מפתח אבטחה קטן לשמירת חיcolor: #f8fafc;
    }

    /* כרטיסי ניתוח נתונים (KPIs)בור
AUTH_TOKEN = "logged_in_success_88"

# --- 2. עיצוב */
    .kpi-card {
        background: rgba(255, 255, 255, CSS יוקרתי ---
st.markdown(f"""
    <style>
    @import url('https://fonts 0.05);
        border: 1px solid rgba(255, 255, 25.googleapis.com/css2?family=Assistant:wght@300;400;700&display5, 0.1);
        padding: 20px;
        border-radius: 15px;
=swap');
    
    html, body, [class*="css"] {{
        font-family:        text-align: center;
        box-shadow: 0 4px 6px rgba(0,  'Assistant', sans-serif;
        direction: rtl;
        text-align: right;
    }}

0, 0, 0.1);
    }
    .kpi-card h2 { color: #3    .stApp {{
        background: #0f172a; /* כחול כהה עמוק */8bdf8 !important; margin: 0; font-size: 2rem; }
    .kpi-card p
        color: #f1f5f9;
    }}
    
    /* כרטיסיות { color: #94a3b8; margin: 0; font-size: 1rem; }

    /* Metric */
    [data-testid="stMetricValue"] {{
        font-size: 32px;
         הודעה צפה להזמנה חדשה */
    .new-order-toast {
        position: fixed;
        topcolor: #38bdf8 !important;
    }}

    /* כרטיסי הזמנה יוקרתיים */
    .order-card {{
        background: rgba(30, 41, 59,: 20px;
        right: 20px;
        background: linear-gradient(1 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding35deg, #22c55e, #16a34a);
        padding: 15px 25px;
        border-radius: 10px;
        z-index: 1000;
        : 20px;
        margin-bottom: 15px;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
    }}
    .order-card:hover {{
        border-color: #38bdf8;
        transform: translateY(-2px);
    }}box-shadow: 0 10px 15px rgba(0,0,0,0.2

    /* כפתורים */
    .stButton>button {{
        border-radius: 12px;
        font);
        animation: slideIn 0.5s ease-out;
    }

    @keyframes slideIn {-weight: 700;
        letter-spacing: 0.5px;
        transition: all
        from { transform: translateX(100%); }
        to { transform: translateX(0); }
    } 0.2s;
    }}
    
    /* טאבים */
    .stTabs [data-baseweb="tab"] {{
        font-size: 18px;
        padding: 10px 2

    /* טבלאות ועיצוב כללי */
    .stDataFrame { border-radius: 15px0px;
    }}

    /* התראות צפות */
    .new-order-badge {{
        background: linear; overflow: hidden; }
    
    .stTabs [data-baseweb="tab"] {
        font-size: 18px;
        font-weight: bold;
        padding: 10px 20-gradient(90deg, #f43f5e, #fb7185);
        padding: 10px 20px;
        border-radius: 50px;
        fontpx;
    }

    /* עיצוב כפתורים */
    .stButton>button {
        border-weight: bold;
        text-align: center;
        margin-bottom: 20px;
        box-radius: 8px;
        transition: all 0.2s;
        border: none;
    }
-shadow: 0 4px 15px rgba(244, 63, 94, 0.    </style>
""", unsafe_allow_html=True)

# --- 3. פונקצי4);
    }}
    </style>
""", unsafe_allow_html=True)

# --- 3. פונקציות ליבה ---
def get_db_connection():
    return psycopg2.ות ליבה ---

def get_db_connection():
    return psycopg2.connect(DB_URL)

@stconnect(DB_URL)

def extract_phone_id(address_field):
    try:
        if.cache_data(ttl=60) # שומר נתונים ל-60 שניות כדי לא לה "WA_ID:" in str(address_field): return str(address_field).split("WA_ID:")[-1].strip()
        clean = str(address_field).replace("WhatsApp:", "").replace("טלפון:", "").replace("-", "").strip()
        if ":" in clean: clean = clean.split(":")[-1].strip()
        ifעמיס על ה-DB
def get_stats():
    try:
        conn = get_db_connection()
 clean.startswith("0"): clean = "972" + clean[1:]
        return clean
    except: return None

def notify_customer(full_address_field, message):
    try:
                cur = conn.cursor()
        # הזמנות היום
        cur.execute("SELECT COUNT(*) FROM orders WHERE created_at >= CURRENT_DATE")
        today_count = cur.fetchone()[0]
        # תלונות פתוחותphone_id = extract_phone_id(full_address_field)
        if not phone_id: return False
        response = requests.post(
            f"{BOT_URL}/send_update", 
            json={"phone":
        cur.execute("SELECT COUNT(*) FROM complaints WHERE status = 'פתוח'")
        open_compl phone_id, "message": message},
            headers={"X-Internal-Secret": INTERNAL_SECRET},
            timeout=10
        )
        return response.status_code == 200
    exceptaints = cur.fetchone()[0]
        # מלאי נמוך (פחות מ-5 יחידות)
        cur.execute("SELECT COUNT(*) FROM products WHERE stock < 5")
        low_stock: return False

# --- 4. מנגנון התחברות חכם (לא מתנתק) ---
# בדיקת "זכור אותי" דרך ה-URL
query_params = st.query_params
if "auth = cur.fetchone()[0]
        conn.close()
        return today_count, open_complaints, low_stock
    except:
        return 0, 0, 0

def notify_customer(full_address_" in query_params and query_params["auth"] == AUTH_TOKEN:
    st.session_state.logged_in = True

if 'logged_in' not in st.session_state:
    st.session_field, message):
    try:
        # חילוץ מספר טלפון (לוגיקה קstate.logged_in = False

if not st.session_state.logged_in:
    cols = st.columns([1יימת)
        phone_id = str(full_address_field).replace("WhatsApp:", "").replace("טלפון:", "").strip()
        if phone_id.startswith("0"): phone_id = "972" + phone, 1.5, 1])
    with cols[1]:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center;'>🔑 כני_id[1:]
        
        response = requests.post(
            f"{BOT_URL}/send_update", 
            json={"phone": phone_id, "message": message},
            headers={"Xסה למערכת</h1>", unsafe_allow_html=True)
        with st.container(border=True):
            pwd = st.text_input("סיסמת מנהל", type="password")
            remember = st.checkbox("זכור אותי במכשיר זה", value=True)
            if st.button("ה-Internal-Secret": INTERNAL_SECRET},
            timeout=10
        )
        return response.status_code == 200
    except:
        return False

# --- 4. מנגנון התחברותתחברות", use_container_width=True):
                if pwd == ADMIN_PASSWORD:
                     עמיד ---

if 'logged_in' not in st.session_state:
    st.session_state.logged_inst.session_state.logged_in = True
                    if remember:
                        st.query_params["auth"] = AUTH_TOKEN
                    st.rerun()
                else:
                    st.error("סי = False

# פונקציה פשוטה למנוע התנתקות מהירה (השארת הססמה שגויה")
    st.stop()

# --- 5. סרגל צד (שן חי)
if st.session_state.logged_in:
    if 'last_action' not in st.sessionSidebar) - נתונים מהירים ---
with st.sidebar:
    st.image("https://cdn_state:
        st.session_state.last_action = datetime.now()
    # אם עברו-icons-png.flaticon.com/512/3737/3737 יותר מ-12 שעות, תתנתק (למען אבטחה)
    if datetime.now() -372.png", width=80)
    st.title("ניהול המכולת")
    st st.session_state.last_action > timedelta(hours=12):
        st.session_state.markdown("---")
    
    # שליפת נתונים מהירה לסיכום
    conn =.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<br get_db_connection()
    pending_count = pd.read_sql("SELECT COUNT(*) FROM orders WHERE status = '><br>", unsafe_allow_html=True)
    cols = st.columns([1, 1.5, 1])
    with cols[1]:
        st.markdown("""
            <div style='background: rgba(2ממתין לאישור'", conn).iloc[0,0]
    comp_count = pd.read_sql("SELECT COUNT(*) FROM complaints WHERE status = 'פתוח'", conn).iloc[0,0]
    conn.close()
    
    st.metric("הזמנות ממתינות", pending_count)
    st55,255,255,0.05); padding: 40px; border-radius: 20px; border: 1px solid #38bdf8;'>
                <h2.metric("תלונות פתוחות", comp_count)
    
    st.markdown("---")
    if st.button("🚪 התנתק", use_container_width=True):
        st.session style='text-align: center;'>🔐 כניסת מנהל מכולת</h2>
            </div>
        """, unsafe_allow_state.logged_in = False
        st.query_params.clear()
        st.rerun()

# ---_html=True)
        pwd = st.text_input("סיסמה", type="password")
        if st.button("כניסה למערכת", use_container_width=True):
            if pwd == ADMIN 6. גוף המערכת ---
st.markdown(f"### שלום, בעל הבית 👋")

if pending_count > 0:
    st.markdown(f"<div class='new-order_PASSWORD:
                st.session_state.logged_in = True
                st.session_state.last_action = datetime.now()
                st.rerun()
            else:
                st.error-badge'>🔔 יש לך {pending_count} הזמנות שמחכות לאישור שלך!</div>", unsafe_allow_html=True)

tabs = st.tabs(["📦 הזמנות חדשות", "⚠️ תלונות("סיסמה לא נכונה")
    st.stop()

# --- 5. דשבורד ראשי ---", "📋 ניהול מלאי", "🕒 היסטוריה"])

# --- טאב 1: הזמנות ---
with tabs[0]:
    conn = get_db_connection()
    pending_df = pd.read_sql("SELECT * FROM orders WHERE status = 'ממתין לאישור' ORDER BY created_

# כותרת עליונה עם KPIs
today_count, open_complaints, low_stock = get_stats()

st.markdown(f"""
    <div style='display: flex; justify-content: space-betweenat DESC", conn)
    conn.close()

    if pending_df.empty:
        st.empty()
; align-items: center; margin-bottom: 30px;'>
        <h1>🛒 שלום, בע        st.info("אין הזמנות חדשות כרגע. אפשר לנוח!")
    else:
        for idx, row in pending_df.iterrows():
            with st.container():
                st.markdown(ל הבית 👋</h1>
        <p>{datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    </div>
""", unsafe_allow_html=True)

col1, col2, col3,f"""
                <div class='order-card'>
                    <div style='display: flex; justify-content: space-between;'>
                        <span style='color: #38bdf8; font-weight: bold;'> col4 = st.columns(4)
with col1:
    st.markdown(f"<div class='kpi-card'><h2>{today_count}</h2><p>הזמנות היום</p></div>", unsafe_allow_html=Trueהזמנה #{row['id']}</span>
                        <span style='font-size: 0.9em; opacity: 0.7;'>{row['created_at'].strftime('%H:%M:%S')}</span>
                    </div>)
with col2:
    st.markdown(f"<div class='kpi-card'><h2 style='color: #ef4444 !important;'>{open_complaints}</h2><p>תלונות פתוחות
                    <h4 style='margin: 10px 0;'>{row['customer_name']}</h4>
                    <p style='background: rgba(255,255,255,0.05); padding: 10px; border-radius: 10px;'>🛒 {row['items']}</p>
                    <p style='font-size: 0.9em;'>📍 {row['address']}</p>
                </div></p></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='kpi-card'><h2 style='color: #fbbf24 !important;'>{
                """, unsafe_allow_html=True)
                
                c1, c2, c3 = st.columns([2, 1, 1])
                with c1:
                    t_est = st.text_inputlow_stock}</h2><p>מוצרים במחסור</p></div>", unsafe_allow_html=True)
with col4:
    if st.button("🔄 רענון מהיר", use_container_("זמן מוכן/הגעה (לדוגמה: 30 דקות)", value="25width=True):
        st.rerun()
    if st.button("🚪 התנתק", use_container_width=True, type="secondary"):
        st.session_state.logged_in = False
         דקות", key=f"t_{row['id']}")
                with c2:
                    if st.button("✅ אשר", key=f"ok_{row['id']}", use_container_width=True):
                        conn =st.rerun()

# --- 6. טאבים לניהול ---

tab_orders, tab_inventory get_db_connection()
                        cur = conn.cursor()
                        cur.execute("UPDATE orders SET status='אושר', delivery_time=%s, approved_at=NOW() WHERE id=%s", (t_est, int, tab_complaints, tab_history = st.tabs([
    "📦 הזמנות לביצוע", "🍎 ניהול מלאי", "⚠️ שירות לקוחות", "📜 היסטוריה"
])

# --(row['id'])))
                        conn.commit()
                        conn.close()
                        msg = f"הזמנתך אושרה! ✅\nזמן משוער: {t_est}\nתודה ש טאב הזמנות --
with tab_orders:
    conn = get_db_connection()
    pending_df = pd.read_sql("SELECT * FROM orders WHERE status = 'ממתין לאיקנית ב'הזוג'!"
                        notify_customer(row['address'], msg)
                        st.success("הזמנה אושרה!")
                        time.sleep(1)
                        st.rerun()
                withשור' ORDER BY created_at DESC", conn)
    conn.close()

    if not pending_df c3:
                    if st.button("❌ בטל", key=f"no_{row['id']}", use_container_width=True):
                        conn = get_db_connection()
                        cur = conn.empty:
        for _, row in pending_df.iterrows():
            with st.expander(f"🔹 הזמנה #{row['id']} - {row['customer_name']}", expanded=True):
                c.cursor()
                        cur.execute("UPDATE orders SET status='בוטל' WHERE id=%s", (int(row['id']),))
                        conn.commit()
                        conn.close()
                        st.rerun()
                st.markdown("<1, c2 = st.columns([2, 1])
                with c1:
                    st.write(f"**סל מוצרים:** {row['items']}")
                    st.write(f"**כתובת/פרbr>", unsafe_allow_html=True)

# --- טאב 2: תלונות ---
with tabs[1]:
    conn = get_db_connection()
    comp_df = pd.read_sqlטים:** {row['address']}")
                with c2:
                    est_time = st.selectbox("זמן הכ("SELECT * FROM complaints WHERE status = 'פתוח' ORDER BY created_at DESC", conn)
    conn.close()
    
    if comp_df.empty:
        st.success("אין תלונות פתוחותנה/הגעה", ["15 דקות", "30 דקות", "45 דקות", "שעה", "איסוף מיידי"], key=f"time_{row['id']}")
                    col_b! השירות מעולה.")
    else:
        for i, row in comp_df.iterrows():
            st.warning(f"**{row['customer_name']}** ({row['phone']}): {row['description']}")
            if st.button("סמן כטופל", key=f"cp_{row['id']}"):
                conn = get_db_connection()1, col_b2 = st.columns(2)
                    if col_b1.button("✅ אשר
                cur = conn.cursor()
                cur.execute("UPDATE complaints SET status = 'טופל' WHERE id = %s", (row['id'],))
                conn.commit()
                conn.close()
                st.rer", key=f"app_{row['id']}", use_container_width=True):
                        # לוגיקת אישור (כמו בקוד שלך)
                        conn = get_db_connection()
                        cur = connun()

# --- טאב 3: מלאי (השדרוג המשמעותי) ---
with tabs[2]:
    st.subheader("ניהול מוצרים מהיר")
    st.write("נית.cursor()
                        cur.execute("UPDATE orders SET status='אושר', delivery_time=%s WHERE id=%s", (est_time, row['id']))
                        conn.commit()
                        conn.close()
                        notify_customer(row['address'], f"הזמנתך אושרה! תהיה מוכנה תון לערוך מחירים וכמויות ישירות בטבלה וללחוץ על 'שמור שינויים'")
    
    conn = get_db_connection()
    prod_df = pd.read_sql("SELECT id, name as 'שם המוצר', price as 'מחיר', stock as 'מלאיך {est_time}")
                        st.success("הודעה נשלחה ללקוח!")
                        time' FROM products ORDER BY name", conn)
    conn.close()
    
    # עריכה ב.sleep(1)
                        st.rerun()
                    if col_b2.button("❌ בטל", keyתוך טבלה (כמו אקסל)
    edited_df = st.data_editor(
        prod_df, 
        key="inventory_editor", 
        num_rows="dynamic", 
        use_container_width=True,
        hide_index=True,
        column_config={=f"rej_{row['id']}", use_container_width=True):
                        # ביטול...
                        st.rerun()
    else:
        st.info("אין הזמנות חדשות כ
            "id": None, # הסתרת עמודת ID
            "מחיר": st.column_config.NumberColumn(format="₪%.2f"),
            "מלאי": st.column_config.NumberColumnרגע. אפשר לנוח!")

# -- טאב מלאי (החלק המקצועי ביותר) --
(step=1)
        }
    )
    
    if st.button("💾 שמור שינויים במלאי"):
        conn = get_db_connection()
        cur = conn.cursor()with tab_inventory:
    st.subheader("עריכת מוצרים מהירה")
    st.write("ניתן לערוך ישירות בטבלה וללחוץ על 'שמור שינויים'")
    
    conn =
        # כאן בלוגיקה אמיתית נבדוק מה השתנה, לצורך הפשטות נעדכן הכל או רק מה ששונה
        for i, row in edited_df.iterrows():
            cur get_db_connection()
    products_df = pd.read_sql("SELECT id, name, price, stock FROM products ORDER BY name", conn)
    conn.close()
    
    # שימוש ב-Data Editor -.execute("UPDATE products SET name=%s, price=%s, stock=%s WHERE id=%s", 
                        (row['ש מאפשר עריכה כמו באקסל
    edited_df = st.data_editor(
        products_df,
        column_config={
            "id": None, # הסתרת ID
            "name": "ם המוצר'], row['מחיר'], row['מלאי'], int(prod_df.iloc[i]['id'])))
        conn.commit()
        conn.close()
        st.success("המלאי עודכן בהצלחה!")

# --- טאב 4: היסטוריה ---
with tabs[3]:
    connשם המוצר",
            "price": st.column_config.NumberColumn("מחיר (₪)", format="%.2f"),
            "stock": st.column_config.NumberColumn("כמות במלאי")
        }, = get_db_connection()
    hist_df = pd.read_sql("SELECT customer_name, items, approved_at, status FROM orders WHERE status != 'ממתין לאישור' ORDER BY approved_at DESC LIMIT 2
        num_rows="dynamic",
        use_container_width=True,
        key="inventory_editor"
    )
    
    if st.button("💾 שמור את כל השינויים במלאי", type="primary"):
        try0", conn)
    conn.close()
    st.table(hist_df)

# רענון אוטומטי כל 60 שניות כדי לא לפספס הזמנות
time.sleep(60)
st.rerun():
            conn = get_db_connection()
            cur = conn.cursor()
            # כאן היינו מוסיפים לוגיקה שמעדכנת רק מה שהשתנה (לצורך הפ
