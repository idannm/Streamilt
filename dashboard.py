import streamlit as st
import psycopg2
import pandas as pd
import os
import requests
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. הגדרות ---
st.set_page_config(page_title="ניהול מכולת - הזוג", page_icon="🛒", layout="wide", initial_sidebar_state="collapsed")

# משתני סביבה
DB_URL = os.environ.get("DB_URL")
BOT_URL = "https://minimarket-ocfq.onrender.com" 
INTERNAL_SECRET = os.environ.get("INTERNAL_SECRET", "123")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "12345")

# --- 2. עיצוב מודרני, נגיש וגדול יותר ---
st.markdown("""
    <style>
    /* רקע מודרני עם גרדיאנט עדין */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: #e0e0e0;
    }
    
    /* כותרות מעוצבות ובולטות */
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 700;
        text-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }
    h3 {
        font-size: 24px !important;
    }
    
    /* טבלאות מודרניות */
    div[data-testid="stDataFrame"] {
        background: linear-gradient(135deg, #252540 0%, #2d2d44 100%);
        border: 1px solid #404060;
        border-radius: 15px;
        padding: 15px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    
    /* כפתורים ראשיים קלים ללחיצה */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        transition: all 0.3s ease;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        font-size: 18px; /* הגדלנו פונט של הכפתורים */
        height: 60px; /* עשינו אותם גבוהים וידידותיים למגע/עכבר */
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    
    /* כפתור אישור - ירוק משמעותי */
    .approve-btn button {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%) !important;
        box-shadow: 0 4px 15px rgba(56, 239, 125, 0.4) !important;
    }
    .approve-btn button:hover {
        background: linear-gradient(135deg, #38ef7d 0%, #11998e 100%) !important;
    }
    
    /* כפתור ביטול - אדום */
    .cancel-btn button {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%) !important;
    }
    
    /* תיבת התחברות מעוצבת */
    .login-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 50px;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 20px 60px rgba(102, 126, 234, 0.4);
    }
    
    /* התראת הזמנה חדשה - אנימציה מרשימה */
    .new-order-alert {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 25px 40px;
        border-radius: 15px;
        text-align: center;
        font-size: 26px;
        font-weight: 700;
        margin: 25px 0;
        animation: pulse 1.5s ease-in-out infinite;
        box-shadow: 0 8px 30px rgba(245, 87, 108, 0.5);
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.03); }
    }
    
    /* כרטיס הזמנה מודרני מוגדל */
    .order-card {
        background: linear-gradient(135deg, #2d2d44 0%, #3a3a5a 100%);
        border: 2px solid #505070;
        border-radius: 15px;
        padding: 25px;
        margin: 20px 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        font-size: 18px; /* טקסט גדול וברור */
    }
    
    .complaint-card {
        background: linear-gradient(135deg, #3a2a2a 0%, #2d1f1f 100%);
        border: 2px solid #eb3349;
        border-radius: 15px;
        padding: 25px;
        margin: 20px 0;
        font-size: 18px;
    }
    
    /* Tabs מעוצבים בגדול */
    .stTabs [data-baseweb="tab"] {
        font-size: 20px;
        padding: 15px 30px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. פונקציות עזר (עם התראות קוליות!) ---
def get_db_connection():
    return psycopg2.connect(DB_URL)

def extract_phone_id(address_field):
    """חילוץ חכם של מזהה הוואטסאפ מהכתובת"""
    try:
        if "WA_ID:" in str(address_field):
            return str(address_field).split("WA_ID:")[-1].strip()
        
        clean = str(address_field).replace("WhatsApp:", "").replace("טלפון:", "").replace("-", "").strip()
        if ":" in clean: clean = clean.split(":")[-1].strip()
        if clean.startswith("0"): clean = "972" + clean[1:]
        return clean
    except:
        return None

def notify_customer(full_address_field, message):
    """שליחת הודעה ללקוח במערכת הוואטסאפ"""
    try:
        phone_id = extract_phone_id(full_address_field)
        
        if not phone_id:
            st.error("לא הצלחתי לחלץ מספר טלפון מההזמנה")
            return False
            
        response = requests.post(
            f"{BOT_URL}/send_update", 
            json={"phone": phone_id, "message": message},
            headers={"X-Internal-Secret": INTERNAL_SECRET},
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"שגיאת תקשורת: {e}")
        return False

def check_new_orders():
    """בדיקה אם יש הזמנות ממתינות חדשות"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM orders WHERE status = 'ממתין לאישור'")
        count = cur.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def check_new_complaints():
    """בדיקה קלה אם יש תלונות חדשות שממתינות לטיפול"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM complaints WHERE status = 'פתוח'")
        count = cur.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def delete_order(order_id):
    """מחיקת הזמנה לחלוטין"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM orders WHERE id = %s", (int(order_id),))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"שגיאה במחיקה: {e}")
        return False

def play_sound(sound_type):
    """פונקציה שבפועל מנגנת סאונדים לאירועים שונים"""
    # אנחנו משתמשים בצלילים אמינים, לא רועשים מידי ומארחים אותם מהרשת
    if sound_type == "order":
        # צליל עדין של פעמון - כנסיית הזמנה
        url = "https://actions.google.com/sounds/v1/alarms/dinner_bell_triangle_light.ogg"
    elif sound_type == "complaint":
        # צליל התראה/סירנה אלקטרונית - לתלונה
        url = "https://actions.google.com/sounds/v1/alarms/scifi_alarm.ogg"
    
    # מזריקים ל-HTML כרכיב שקוף שמנגן בטעינה האוטומטית
    html = f"""
    <audio autoplay style="display: none;">
        <source src="{url}" type="audio/ogg">
    </audio>
    """
    st.markdown(html, unsafe_allow_html=True)


# --- 4. מערכת התחברות ---
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<div class='login-box'><h2>🔐 כניסה למנהל המכולת</h2></div>", unsafe_allow_html=True)
        pwd = st.text_input("הזן סיסמה כאן:", type="password", key="login_pwd")
        if st.button("כניסـה", use_container_width=True):
            if pwd == ADMIN_PASSWORD: 
                st.session_state.logged_in = True
                st.rerun()
            else: 
                st.error("סיסמה שגויה! נסה שוב.")
    st.stop()


# --- 5. ממשק ראשי מחובר ---
# פונקציית הקסם - ירענן אוטומטית פעם ב-20 שניות לבד! (ערך של 20000 מילי-שניות)
st_autorefresh(interval=20000, limit=None, key="auto_refresh")

st.title("🛒 מערכת ניהול מכולת מתקדמת")

# כפתורי ניווט עליונים וידניים
col_header1, col_header2, col_header3 = st.columns([5, 2, 1])
with col_header2:
    st.markdown("<div class='refresh-btn'>", unsafe_allow_html=True)
    if st.button("🔄 רענן עכשיו", use_container_width=True, key="top_refresh"): 
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with col_header3:
    if st.button("🚪 התנתק", use_container_width=True): 
        st.session_state.logged_in = False
        st.rerun()

# --- בדיקת סטטוס להשמעת צלילים ---
if 'last_order_count' not in st.session_state:
    st.session_state.last_order_count = 0
if 'last_complaint_count' not in st.session_state:
    st.session_state.last_complaint_count = 0

current_order_count = check_new_orders()
current_complaint_count = check_new_complaints()

# אם נכנסה הזמנה חדשה - הפעלת צליל הפעמון והצגת התראה
if current_order_count > st.session_state.last_order_count and current_order_count > 0:
    play_sound("order")
    st.markdown(f"""
        <div class='new-order-alert'>
            🔔 נכנסה הזמנה חדשה! יש כרגע {current_order_count} הזמנות לטיפול
        </div>
    """, unsafe_allow_html=True)
    st.balloons()
st.session_state.last_order_count = current_order_count

# אם נוספה תלונה חדשה - הפעלת צליל תלונה/אזהרה עדין
if current_complaint_count > st.session_state.last_complaint_count and current_complaint_count > 0:
    play_sound("complaint")
    st.markdown(f"""
        <div class='new-order-alert' style='background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);'>
            ⚠️ לקוח השאיר פניה / תלונה חדשה!
        </div>
    """, unsafe_allow_html=True)
st.session_state.last_complaint_count = current_complaint_count

# ----------------- הטיה כרטיסיות (TABS) -----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📦 הזמנות לטיפול", "⚠️ תלונות", "✅ היסטוריית הזמנות", "❌ בוטלו", "🏪 ניהול מלאי"])

# --- טאב 1: הזמנות לטיפול ---
with tab1:
    st.markdown(f"### 📦 הזמנות חדשות - {current_order_count} פעילות ממתינות")
    
    conn = get_db_connection()
    pending_df = pd.read_sql(
        "SELECT id, customer_name, items, address, order_type, created_at FROM orders WHERE status = 'ממתין לאישור' ORDER BY created_at DESC", 
        conn
    )
    conn.close()
    
    if not pending_df.empty:
        for idx, row in pending_df.iterrows():
            oid = row['id']
            order_type = row.get('order_type', 'משלוח')
            type_icon = "🛒 הגעה למכולת לאיסוף ע\"י הלקוח" if order_type == 'איסוף עצמי' else "🛵 משלוח לבית הלקוח"
            
            st.markdown(f"""
                <div class='order-card'>
                    <h3>📋 הזמנה מס' {oid}</h3>
                    <p><strong>👤 שם הלקוח:</strong> {row['customer_name']}</p>
                    <p><strong>🛍️ מה להכין:</strong> {row['items']}</p>
                    <p><strong>🚚 סוג קבלה:</strong> <span style="color:#feca57; font-weight:bold;">{type_icon}</span></p>
                    <p><strong>📍 כתובת ופרטים:</strong> {row['address']}</p>
                    <p><strong>🕐 התקבלה ב-:</strong> {row['created_at'].strftime('%d/%m/%Y בשעה %H:%M')}</p>
                </div>
            """, unsafe_allow_html=True)
            
            col_time, col_approve, col_cancel, col_delete = st.columns([2.5, 2.5, 2, 1])
            
            with col_time:
                placeholder_text = "זמן מוכן לאיסוף (למשל: 10 דק')" if order_type == 'איסוף עצמי' else "זמן הגעת משלוח (למשל: 20 דק')"
                time_est = st.text_input(
                    f"⏱️ מתי יהיה מוכן?", 
                    value="20 דקות",
                    key=f"time_{oid}",
                    placeholder=placeholder_text
                )
            
            with col_approve:
                st.markdown("<br><div class='approve-btn'>", unsafe_allow_html=True)
                if st.button("✅ אישור והודעה ללקוח", use_container_width=True, key=f"approve_{oid}"):
                    if time_est:
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute(
                            "UPDATE orders SET status='אושר', delivery_time=%s, approved_at=NOW() WHERE id=%s", 
                            (time_est, int(oid))
                        )
                        conn.commit()
                        conn.close()
                        
                        if order_type == 'איסוף עצמי':
                            msg = f"היי {row['customer_name']}!\nההזמנה שלך במכולת אושרה ✅\n🛒 מוצרים: {row['items']}\n🛍️ ההזמנה תהיה מוכנה לאיסוף עצמי בעוד: {time_est}.\nנשמח לראותך!"
                        else:
                            msg = f"היי {row['customer_name']}!\nההזמנה אושרה והיא בדרך! ✅\n🛒 מהקנייה שלך: {row['items']}\n🛵 הזמן המשוער להגעה הוא: {time_est}.\nבתאבון!"
                        
                        if notify_customer(row['address'], msg):
                            st.success("✅ אושר בהצלחה – ההודעה נשלחה ללקוח בוואטסאפ!")
                        else:
                            st.warning("⚠️ ההזמנה אושרה, אבל הייתה בעיה לשלוח את ההודעה ללקוח.")
                        
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("חובה להכניס זמן הגעה/מוכנות!")
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col_cancel:
                st.markdown("<br><div class='cancel-btn'>", unsafe_allow_html=True)
                if st.button("❌ ביטול הזמנה", use_container_width=True, key=f"cancel_{oid}"):
                    st.session_state[f'show_cancel_{oid}'] = True
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col_delete:
                st.markdown("<br><div class='delete-btn'>", unsafe_allow_html=True)
                if st.button("🗑️ מחיקה", use_container_width=True, key=f"delete_{oid}", help="מוחק לגמרי מהמרכז"):
                    if delete_order(oid):
                        st.success(f"🗑️ הזמנה נמחקה")
                        time.sleep(1)
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            
            # --- אזור הביטול שמופיע רק אם לוחץ ביטול ---
            if st.session_state.get(f'show_cancel_{oid}', False):
                with st.container():
                    st.markdown("<div style='background-color:#4a2b2b; padding:15px; border-radius:10px;'>", unsafe_allow_html=True)
                    st.markdown("#### 🔴 למה מבטלים?")
                    col_reason, col_confirm = st.columns([3, 1])
                    with col_reason:
                        reason = st.selectbox(
                            "סיבה (לקוח יראה את זה):", 
                            ["חסר פריט במלאי", "כתובת שגויה או חסר פרטים", "אין אפשרות למשלוח כרגע", "אחר"],
                            key=f"reason_select_{oid}"
                        )
                        if reason == "אחר":
                            custom_reason = st.text_input("הסבר אחר במילים שלך:", key=f"custom_reason_{oid}")
                            final_reason = custom_reason if custom_reason else "לא צוינה סיבה מפורטת"
                        else:
                            final_reason = reason
                    
                    with col_confirm:
                        st.markdown("<br><div class='cancel-btn'>", unsafe_allow_html=True)
                        if st.button("אשר ביטול ושלח ❌", key=f"confirm_cancel_{oid}", use_container_width=True):
                            conn = get_db_connection()
                            cur = conn.cursor()
                            cur.execute("UPDATE orders SET status='בוטל', cancellation_reason=%s WHERE id=%s", (final_reason, int(oid)))
                            conn.commit()
                            conn.close()
                            
                            msg = f"שלום {row['customer_name']}, לצערנו ההזמנה שלך מהמכולת בוטלה ❌\nסיבת הביטול: {final_reason}.\nניתן ליצור איתנו קשר. עמך הסליחה!"
                            notify_customer(row['address'], msg)
                            
                            st.session_state[f'show_cancel_{oid}'] = False
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("---")
    else:
        st.markdown("""
            <div class='empty-state'>
                <h2 style="font-size:45px;">🎉 הזמן לנוח!</h2>
                <p style="font-size:22px;">כל ההזמנות טופלו! אין הזמנות חדשות כרגע בפתח.</p>
            </div>
        """, unsafe_allow_html=True)

# --- טאב 2: תלונות ופניות ---
with tab2:
    st.markdown("### ⚠️ לקוחות שצריך לחזור אליהם - תלונות/פניות")
    try:
        conn = get_db_connection()
        comp_df = pd.read_sql("SELECT * FROM complaints WHERE status = 'פתוח' ORDER BY created_at DESC", conn)
        conn.close()
        
        if not comp_df.empty:
            for i, row in comp_df.iterrows():
                st.markdown(f"""
                <div class='complaint-card'>
                    <h3>🗣️ פנייה חמה מהלקוח: {row['customer_name']}</h3>
                    <p><strong>📱 עשה טלפון אליו עכשיו:</strong> {row['phone']}</p>
                    <p><strong>📝 מה קרה:</strong> {row['description']}</p>
                    <p><strong>🕒 נתקבל בתאריך:</strong> {row['created_at'].strftime('%d/%m/%Y בשעה %H:%M')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col_mark, _ = st.columns([1.5, 4])
                with col_mark:
                    st.markdown("<div class='approve-btn'>", unsafe_allow_html=True)
                    if st.button("✅ דיברתי איתו - סיים טיפול", key=f"comp_{row['id']}", use_container_width=True):
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute("UPDATE complaints SET status = 'טופל' WHERE id = %s", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.success("נהדר! הפנייה ירדה מהרשימה.")
                        time.sleep(1.5)
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("---")
        else:
            st.markdown("""
                <div class='empty-state'>
                    <h2 style="font-size:45px;">🍯 הכל דבש!</h2>
                    <p style="font-size:22px;">אף לקוח לא התלונן ואין פניות חדשות.</p>
                </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error("הייתה בעיה בטעינה. שים לב שטבלת התלונות הוגדרה כראוי בבסיס הנתונים.")

# --- טאב 3: היסטוריית הזמנות שבוצעו ---
with tab3:
    st.markdown("### ✅ הזמנות שיצאו לדרך או נאספו (היסטוריה)")
    
    conn = get_db_connection()
    approved_df = pd.read_sql(
        "SELECT id, customer_name, items, delivery_time, approved_at FROM orders WHERE status='אושר' ORDER BY approved_at DESC LIMIT 50", 
        conn
    )
    conn.close()
    
    if not approved_df.empty:
        st.dataframe(
            approved_df, 
            use_container_width=True,
            column_config={
                "id": st.column_config.NumberColumn("מס' הזמנה", format="%d"),
                "customer_name": "שם הלקוח",
                "items": "מה הזמין",
                "delivery_time": "הבטחנו תוך",
                "approved_at": st.column_config.DatetimeColumn("אישרנו את זה ב-", format="DD/MM/YYYY | HH:mm")
            },
            hide_index=True
        )
    else:
        st.info("עדיין אין הזמנות שאושרו. מחכים לקופה הראשונה!")

# --- טאב 4: הזמנות שבוטלו ---
with tab4:
    st.markdown("### ❌ היסטוריית הזמנות שנאלצת לבטל")
    conn = get_db_connection()
    cancelled_df = pd.read_sql(
        "SELECT id, customer_name, items, cancellation_reason, created_at FROM orders WHERE status='בוטל' ORDER BY created_at DESC LIMIT 50", 
        conn
    )
    conn.close()
    
    if not cancelled_df.empty:
        st.dataframe(
            cancelled_df, 
            use_container_width=True,
            column_config={
                "id": st.column_config.NumberColumn("מס' הזמנה", format="%d"),
                "customer_name": "משם מי",
                "items": "מה רצה לקנות",
                "cancellation_reason": "סיבת הביטול",
                "created_at": st.column_config.DatetimeColumn("תאריך הביטול", format="DD/MM/YYYY | HH:mm")
            },
            hide_index=True
        )
    else:
        st.info("אין כאן הזמנות מבוטלות. יופי!")

# --- טאב 5: מלאי ---
with tab5:
    st.markdown("### 📦 ניהול מוצרים במכולת")
    subtab1, subtab2 = st.tabs(["📋 רשימת מוצרים ועריכה", "➕ הוספת מלאי ומוצרים חדשים"])
    
    with subtab1:
        search_products = st.text_input("🔍 חיפוש מוצר כדי למצוא מחיר/לשנות מלאי", placeholder="רשום שם של מוצר (למשל: תפוצ'יפס)...", key="search_products")
        conn = get_db_connection()
        df_p = pd.read_sql("SELECT id, name, price, stock FROM products ORDER BY name", conn)
        conn.close()
        
        if search_products:
            df_p = df_p[df_p['name'].str.contains(search_products, case=False, na=False)]
        
        if not df_p.empty:
            for idx, product in df_p.iterrows():
                pid = product['id']
                with st.container():
                    col_edit_name, col_edit_price, col_edit_stock, col_save, col_delete = st.columns([3, 1.5, 1.5, 1, 1])
                    with col_edit_name:
                        new_name = st.text_input("שם מוצר", value=product['name'], key=f"name_{pid}")
                    with col_edit_price:
                        new_price = st.number_input("מחיר מלא", value=float(product['price']), min_value=0.0, step=0.5, key=f"price_{pid}")
                    with col_edit_stock:
                        new_stock = st.number_input("נשאר לנו רק (יחידות):", value=int(product['stock']), min_value=0, step=1, key=f"stock_{pid}")
                    
                    with col_save:
                        st.markdown("<br><div class='approve-btn'>", unsafe_allow_html=True)
                        if st.button("💾 שמור", key=f"save_{pid}", use_container_width=True):
                            conn = get_db_connection()
                            cur = conn.cursor()
                            cur.execute("UPDATE products SET name=%s, price=%s, stock=%s WHERE id=%s", (new_name, new_price, new_stock, pid))
                            conn.commit()
                            conn.close()
                            st.success("נשמר!")
                            time.sleep(0.5)
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    with col_delete:
                        st.markdown("<br><div class='cancel-btn'>", unsafe_allow_html=True)
                        if st.button("🗑️ מחק", key=f"del_{pid}", use_container_width=True):
                            conn = get_db_connection()
                            cur = conn.cursor()
                            cur.execute("DELETE FROM products WHERE id=%s", (pid,))
                            conn.commit()
                            conn.close()
                            st.success("נמחק מהקופה.")
                            time.sleep(0.5)
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                    st.markdown("<hr style='border: 1px solid #404060;'>", unsafe_allow_html=True)

    with subtab2:
        with st.form("add_product_form", clear_on_submit=True):
            st.markdown("<div class='action-section'>", unsafe_allow_html=True)
            col_name, col_price, col_stock = st.columns([3, 2, 2])
            with col_name:
                product_name = st.text_input("🏷️ איזו סחורה הגיע?", placeholder="לדוגמה: לחמניות טריות")
            with col_price:
                product_price = st.number_input("💰 כמה עולה? (₪)", min_value=0.0, step=0.5, format="%.2f")
            with col_stock:
                product_stock = st.number_input("📦 כמה הבאת למכולת עכשיו (במקור)?", min_value=0, step=1, value=0)
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='approve-btn'>", unsafe_allow_html=True)
            submit = st.form_submit_button("➕ דחוף למדף (שמור לקופה)", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            if submit and product_name and product_price > 0:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("INSERT INTO products (name, price, stock) VALUES (%s, %s, %s)", (product_name, product_price, product_stock))
                conn.commit()
                conn.close()
                st.success(f"✅ המוצר '{product_name}' עלה למדף בהצלחה!")
                time.sleep(1.5)
                st.rerun()
