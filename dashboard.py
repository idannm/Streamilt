import streamlit as st
import psycopg2
import pandas as pd
import os
import requests
import time
from datetime import datetime

# ─────────────────────────────────────
# הגדרות
# ─────────────────────────────────────
st.set_page_config(
    page_title="המכולת של הצדיק",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DB_URL          = os.environ.get("DB_URL")
BOT_URL         = os.environ.get("BOT_URL", "https://minimarket-ocfq.onrender.com")
INTERNAL_SECRET = os.environ.get("INTERNAL_SECRET", "123")
ADMIN_PASSWORD  = os.environ.get("ADMIN_PASSWORD", "12345")

# ─────────────────────────────────────
# CSS + סאונד
# ─────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;700;800;900&display=swap');

* { font-family: 'Heebo', sans-serif !important; }

/* רקע */
.stApp {
    background: #0f1117;
    color: #e8eaf0;
    direction: rtl;
}

/* הסרת padding מיותר */
.block-container { padding: 1.5rem 2rem 3rem !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { display: none; }

/* כותרת ראשית */
.main-header {
    background: linear-gradient(135deg, #1a1d2e 0%, #252840 100%);
    border: 1px solid #2e3250;
    border-radius: 20px;
    padding: 24px 32px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4);
}
.main-header h1 {
    font-size: 28px !important;
    font-weight: 900 !important;
    color: #fff !important;
    margin: 0 !important;
    letter-spacing: -0.5px;
}
.main-header .subtitle {
    color: #7c85b3;
    font-size: 14px;
    margin-top: 4px;
}

/* כרטיסי סטטיסטיקה */
.stat-card {
    background: linear-gradient(135deg, #1a1d2e 0%, #1e2135 100%);
    border: 1px solid #2e3250;
    border-radius: 16px;
    padding: 20px 24px;
    text-align: center;
    box-shadow: 0 2px 12px rgba(0,0,0,0.3);
    transition: all 0.2s ease;
}
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.4); }
.stat-number {
    font-size: 40px;
    font-weight: 900;
    line-height: 1;
    margin-bottom: 4px;
}
.stat-label { font-size: 13px; color: #7c85b3; font-weight: 500; }
.stat-pending .stat-number { color: #f59e0b; }
.stat-delivery .stat-number { color: #3b82f6; }
.stat-pickup .stat-number { color: #10b981; }
.stat-complaints .stat-number { color: #ef4444; }

/* התראת הזמנה */
@keyframes slideIn {
    from { transform: translateY(-20px); opacity: 0; }
    to   { transform: translateY(0);     opacity: 1; }
}
@keyframes glow {
    0%, 100% { box-shadow: 0 0 20px rgba(245,158,11,0.4); }
    50%       { box-shadow: 0 0 40px rgba(245,158,11,0.8); }
}
.alert-banner {
    background: linear-gradient(135deg, #92400e 0%, #78350f 100%);
    border: 2px solid #f59e0b;
    border-radius: 16px;
    padding: 20px 28px;
    margin: 16px 0;
    text-align: center;
    font-size: 20px;
    font-weight: 700;
    color: #fef3c7;
    animation: slideIn 0.4s ease, glow 2s ease-in-out infinite;
}

/* כרטיסי הזמנה */
.order-card {
    background: #1a1d2e;
    border: 1px solid #2e3250;
    border-radius: 16px;
    padding: 20px 24px;
    margin: 12px 0;
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
}
.order-card::before {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 4px;
    height: 100%;
    background: #3b82f6;
    border-radius: 4px 0 0 4px;
}
.order-card.pickup::before { background: #10b981; }
.order-card:hover { border-color: #3e4470; transform: translateX(-2px); }
.order-card .order-id {
    font-size: 13px;
    color: #7c85b3;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.order-card .order-name {
    font-size: 22px;
    font-weight: 800;
    color: #fff;
    margin: 4px 0 12px;
}
.order-card .order-items {
    background: #12141f;
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 15px;
    color: #a0a8cc;
    margin-bottom: 12px;
    border: 1px solid #1e2135;
}
.order-meta {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
}
.order-meta span {
    font-size: 13px;
    color: #6b7280;
    display: flex;
    align-items: center;
    gap: 4px;
}
.badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.5px;
}
.badge-delivery { background: #1e3a5f; color: #60a5fa; border: 1px solid #2563eb; }
.badge-pickup   { background: #064e3b; color: #34d399; border: 1px solid #059669; }
.badge-new      { background: #78350f; color: #fbbf24; border: 1px solid #d97706; }

/* כרטיסי תלונה */
.complaint-card {
    background: #1f1215;
    border: 1px solid #7f1d1d;
    border-radius: 16px;
    padding: 20px 24px;
    margin: 12px 0;
}
.complaint-card .complaint-name { font-size: 20px; font-weight: 800; color: #fca5a5; }
.complaint-card .complaint-desc { color: #d1d5db; font-size: 15px; line-height: 1.6; }

/* כפתורים */
.stButton > button {
    border-radius: 10px !important;
    font-family: 'Heebo', sans-serif !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    padding: 10px 16px !important;
    border: none !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
}

/* כפתור ראשי (אישור) */
div[data-btn="approve"] .stButton > button {
    background: linear-gradient(135deg, #059669, #10b981) !important;
    color: #fff !important;
    box-shadow: 0 4px 12px rgba(16,185,129,0.3) !important;
}
div[data-btn="approve"] .stButton > button:hover {
    background: linear-gradient(135deg, #10b981, #34d399) !important;
    box-shadow: 0 6px 16px rgba(16,185,129,0.5) !important;
    transform: translateY(-1px) !important;
}

/* ביטול */
div[data-btn="cancel"] .stButton > button {
    background: linear-gradient(135deg, #dc2626, #ef4444) !important;
    color: #fff !important;
    box-shadow: 0 4px 12px rgba(239,68,68,0.3) !important;
}
div[data-btn="cancel"] .stButton > button:hover {
    background: linear-gradient(135deg, #ef4444, #f87171) !important;
    transform: translateY(-1px) !important;
}

/* מחיקה */
div[data-btn="delete"] .stButton > button {
    background: #1e2135 !important;
    color: #9ca3af !important;
    border: 1px solid #2e3250 !important;
}
div[data-btn="delete"] .stButton > button:hover {
    background: #7f1d1d !important;
    color: #fca5a5 !important;
    border-color: #991b1b !important;
}

/* רענון */
div[data-btn="refresh"] .stButton > button {
    background: linear-gradient(135deg, #1d4ed8, #3b82f6) !important;
    color: #fff !important;
    box-shadow: 0 4px 12px rgba(59,130,246,0.3) !important;
}

/* שדות קלט */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div > select {
    background: #1a1d2e !important;
    color: #e8eaf0 !important;
    border: 1px solid #2e3250 !important;
    border-radius: 10px !important;
    font-family: 'Heebo', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.15) !important;
}
label { color: #9ca3af !important; font-weight: 600 !important; font-size: 13px !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #1a1d2e !important;
    border-radius: 12px !important;
    padding: 6px !important;
    gap: 4px !important;
    border: 1px solid #2e3250 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #7c85b3 !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    padding: 10px 18px !important;
    border: none !important;
    transition: all 0.2s !important;
}
.stTabs [data-baseweb="tab"]:hover { background: #252840 !important; color: #c4cbe8 !important; }
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #1d4ed8, #3b82f6) !important;
    color: #fff !important;
    box-shadow: 0 2px 8px rgba(59,130,246,0.4) !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 20px !important; }

/* Empty state */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #4b5563;
}
.empty-state .icon { font-size: 64px; margin-bottom: 16px; }
.empty-state h3 { color: #6b7280 !important; font-size: 20px !important; margin-bottom: 8px; }
.empty-state p { font-size: 15px; }

/* Divider */
.divider { height: 1px; background: #1e2135; margin: 8px 0 16px; border: none; }

/* Success/error */
.stSuccess, .stError, .stWarning, .stInfo { border-radius: 10px !important; }

/* טופס login */
.login-wrap {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
}
.login-card {
    background: #1a1d2e;
    border: 1px solid #2e3250;
    border-radius: 24px;
    padding: 48px 40px;
    width: 380px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    text-align: center;
}
.login-card h2 { font-size: 28px !important; font-weight: 900 !important; color: #fff !important; margin-bottom: 8px; }
.login-card p { color: #7c85b3; font-size: 14px; margin-bottom: 32px; }

/* No session timeout — keep alive indicator */
.keepalive { display: none; }

/* RTL fix for dataframe */
.stDataFrame { direction: ltr; }

/* הסרת border מיותר מ-Streamlit */
hr { border-color: #1e2135 !important; }
</style>

<!-- סאונדים בווב אודיו -->
<script>
const AudioContext = window.AudioContext || window.webkitAudioContext;

function playSound(type) {
    try {
        const ctx = new AudioContext();
        
        if (type === 'delivery') {
            // 🛵 משלוח — 3 פעימות עולות
            [0, 0.15, 0.30].forEach((delay, i) => {
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain); gain.connect(ctx.destination);
                osc.frequency.value = 440 + i * 120;
                osc.type = 'sine';
                gain.gain.setValueAtTime(0, ctx.currentTime + delay);
                gain.gain.linearRampToValueAtTime(0.4, ctx.currentTime + delay + 0.05);
                gain.gain.linearRampToValueAtTime(0, ctx.currentTime + delay + 0.18);
                osc.start(ctx.currentTime + delay);
                osc.stop(ctx.currentTime + delay + 0.2);
            });
            
        } else if (type === 'pickup') {
            // 🛒 איסוף — צלצול כפול פשוט
            [0, 0.25].forEach(delay => {
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain); gain.connect(ctx.destination);
                osc.frequency.value = 880;
                osc.type = 'triangle';
                gain.gain.setValueAtTime(0, ctx.currentTime + delay);
                gain.gain.linearRampToValueAtTime(0.3, ctx.currentTime + delay + 0.04);
                gain.gain.linearRampToValueAtTime(0, ctx.currentTime + delay + 0.2);
                osc.start(ctx.currentTime + delay);
                osc.stop(ctx.currentTime + delay + 0.25);
            });
            
        } else if (type === 'complaint') {
            // ⚠️ תלונה — צליל נמוך מטריד
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain); gain.connect(ctx.destination);
            osc.frequency.setValueAtTime(220, ctx.currentTime);
            osc.frequency.linearRampToValueAtTime(180, ctx.currentTime + 0.5);
            osc.type = 'sawtooth';
            gain.gain.setValueAtTime(0.25, ctx.currentTime);
            gain.gain.linearRampToValueAtTime(0, ctx.currentTime + 0.5);
            osc.start(ctx.currentTime);
            osc.stop(ctx.currentTime + 0.55);
            
        } else if (type === 'new_order') {
            // 🔔 הזמנה חדשה — צלצול קופה
            const freqs = [523, 659, 784, 1047];
            freqs.forEach((f, i) => {
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain); gain.connect(ctx.destination);
                osc.frequency.value = f;
                osc.type = 'sine';
                const t = ctx.currentTime + i * 0.12;
                gain.gain.setValueAtTime(0, t);
                gain.gain.linearRampToValueAtTime(0.35, t + 0.03);
                gain.gain.linearRampToValueAtTime(0, t + 0.25);
                osc.start(t);
                osc.stop(t + 0.3);
            });
        }
    } catch(e) { console.log('Audio error:', e); }
}

// שמירת מצב קודם לזיהוי שינויים
let prevState = { orders: -1, complaints: -1 };

function checkForChanges() {
    const curr = {
        orders:     parseInt(document.getElementById('order-count-data')?.dataset?.count  ?? -1),
        complaints: parseInt(document.getElementById('complaint-count-data')?.dataset?.count ?? -1),
        sound:      document.getElementById('sound-trigger')?.dataset?.sound ?? ''
    };
    
    if (curr.sound && curr.sound !== window._lastSound) {
        window._lastSound = curr.sound;
        playSound(curr.sound);
    }
    
    if (prevState.orders >= 0 && curr.orders > prevState.orders)     playSound('new_order');
    if (prevState.complaints >= 0 && curr.complaints > prevState.complaints) playSound('complaint');
    
    prevState = curr;
}

// בדיקה כל שנייה
setInterval(checkForChanges, 1000);

// מניעת נעילה — ping כל 3 דקות
setInterval(() => {
    fetch(window.location.href, {method:'HEAD'}).catch(()=>{});
}, 180000);
</script>
""", unsafe_allow_html=True)

# ─────────────────────────────────────
# DB helpers
# ─────────────────────────────────────
def get_db():
    return psycopg2.connect(DB_URL)

def run_query(sql, params=(), fetch=True):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        if fetch:
            result = cur.fetchall()
        else:
            conn.commit()
            result = True
        return result
    except Exception as e:
        st.error(f"שגיאת DB: {e}")
        return [] if fetch else False
    finally:
        conn.close()

def read_df(sql, conn=None):
    c = conn or get_db()
    try:
        df = pd.read_sql(sql, c)
        if not conn:
            c.close()
        return df
    except:
        return pd.DataFrame()

def extract_phone(address):
    try:
        if "WA_ID:" in str(address):
            return str(address).split("WA_ID:")[-1].strip()
        clean = str(address).replace("-","").strip()
        if clean.startswith("0"):
            return "972" + clean[1:]
        return clean
    except:
        return None

def notify(address, message):
    phone = extract_phone(address)
    if not phone:
        return False
    try:
        r = requests.post(
            f"{BOT_URL}/send_update",
            json={"phone": phone, "message": message},
            headers={"X-Internal-Secret": INTERNAL_SECRET},
            timeout=10
        )
        return r.status_code == 200
    except:
        return False

def get_counts():
    rows = run_query("SELECT status FROM orders WHERE status IN ('ממתין לאישור','אושר')")
    pending   = sum(1 for r in rows if r[0] == 'ממתין לאישור')
    approved  = sum(1 for r in rows if r[0] == 'אושר')

    delivery_rows = run_query("SELECT order_type FROM orders WHERE status = 'ממתין לאישור'")
    deliveries = sum(1 for r in delivery_rows if 'משלוח' in str(r[0]).lower() or 'delivery' in str(r[0]).lower())
    pickups    = pending - deliveries

    comp = run_query("SELECT COUNT(*) FROM complaints WHERE status='פתוח'")
    complaints = comp[0][0] if comp else 0
    return pending, approved, deliveries, pickups, complaints

# ─────────────────────────────────────
# Session state init
# ─────────────────────────────────────
for k, v in {
    'logged_in': False,
    'prev_pending': -1,
    'prev_complaints': -1,
    'sound_trigger': '',
    'cancel_open': {}
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────
# LOGIN
# ─────────────────────────────────────
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
            <div class='login-card'>
                <div style='font-size:52px;margin-bottom:16px'>🛒</div>
                <h2>המכולת של הצדיק</h2>
                <p>כניסה לממשק ניהול</p>
            </div>
        """, unsafe_allow_html=True)
        pwd = st.text_input("סיסמה", type="password", placeholder="הקלד סיסמה...", key="pwd")
        if st.button("כניסה →", use_container_width=True):
            if pwd == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("❌ סיסמה שגויה")
    st.stop()

# ─────────────────────────────────────
# MAIN UI
# ─────────────────────────────────────
pending, approved, deliveries, pickups, complaints = get_counts()

# זיהוי שינויים לסאונד
sound_to_play = ''
if st.session_state.prev_pending >= 0 and pending > st.session_state.prev_pending:
    sound_to_play = 'new_order'
if st.session_state.prev_complaints >= 0 and complaints > st.session_state.prev_complaints:
    sound_to_play = 'complaint'
st.session_state.prev_pending    = pending
st.session_state.prev_complaints = complaints

# data elements לJS
st.markdown(f"""
<div id='order-count-data'     data-count='{pending}'    style='display:none'></div>
<div id='complaint-count-data' data-count='{complaints}' style='display:none'></div>
<div id='sound-trigger'        data-sound='{sound_to_play}' style='display:none'></div>
""", unsafe_allow_html=True)

# ─── Header ───
header_col, btn_col = st.columns([5, 1])
with header_col:
    now = datetime.now().strftime("%A, %d/%m/%Y | %H:%M")
    st.markdown(f"""
        <div class='main-header'>
            <div>
                <h1>🛒 המכולת של הצדיק</h1>
                <div class='subtitle'>{now}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
with btn_col:
    st.markdown("<br>", unsafe_allow_html=True)
    col_r, col_l = st.columns(2)
    with col_r:
        st.markdown('<div data-btn="refresh">', unsafe_allow_html=True)
        if st.button("🔄", help="רענן", key="refresh_top"):
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with col_l:
        if st.button("🚪", help="התנתק", key="logout"):
            st.session_state.logged_in = False
            st.rerun()

# ─── Stats ───
s1, s2, s3, s4 = st.columns(4)
for col, cls, num, label in [
    (s1, "stat-pending",    pending,    "ממתינות לטיפול"),
    (s2, "stat-delivery",   deliveries, "משלוחים"),
    (s3, "stat-pickup",     pickups,    "איסופים"),
    (s4, "stat-complaints", complaints, "תלונות פתוחות"),
]:
    with col:
        st.markdown(f"""
            <div class='stat-card {cls}'>
                <div class='stat-number'>{num}</div>
                <div class='stat-label'>{label}</div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ─── Alert banner ───
if pending > 0:
    icons = "🔔" * min(pending, 5)
    st.markdown(f"""
        <div class='alert-banner'>
            {icons} יש {pending} הזמנות שמחכות לאישור שלך!
        </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────
# TABS
# ─────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    f"📦 לטיפול ({pending})",
    f"⚠️ תלונות ({complaints})",
    "✅ אושרו",
    "❌ בוטלו",
    "🏪 מלאי"
])

# ══════════════════════════════════════
# TAB 1 — הזמנות לטיפול
# ══════════════════════════════════════
with tab1:
    search = st.text_input("🔍 חפש לפי שם, מוצר או מספר הזמנה", placeholder="הקלד...", key="s1")

    conn = get_db()
    df = pd.read_sql(
        "SELECT id, customer_name, items, address, order_type, created_at FROM orders WHERE status='ממתין לאישור' ORDER BY created_at DESC",
        conn
    )
    conn.close()

    if search:
        mask = (
            df['customer_name'].str.contains(search, case=False, na=False) |
            df['items'].str.contains(search, case=False, na=False) |
            df['id'].astype(str).str.contains(search)
        )
        df = df[mask]

    if df.empty:
        st.markdown("""
            <div class='empty-state'>
                <div class='icon'>🎉</div>
                <h3>כל ההזמנות טופלו!</h3>
                <p>אין הזמנות חדשות כרגע. תמשיך כך 💪</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        for _, row in df.iterrows():
            oid        = row['id']
            otype      = str(row.get('order_type', 'משלוח'))
            is_pickup  = 'איסוף' in otype
            card_class = 'order-card pickup' if is_pickup else 'order-card'
            badge_html = "<span class='badge badge-pickup'>🛒 איסוף עצמי</span>" if is_pickup else "<span class='badge badge-delivery'>🛵 משלוח</span>"
            created    = row['created_at'].strftime('%H:%M — %d/%m/%Y')

            # חילוץ כתובת נקייה (בלי WA_ID)
            address_clean = str(row['address']).split('|')[0].strip() if '|' in str(row['address']) else str(row['address'])

            st.markdown(f"""
                <div class='{card_class}'>
                    <div style='display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:8px'>
                        <div>
                            <div class='order-id'>הזמנה #{oid} &nbsp;•&nbsp; {badge_html} &nbsp;<span class='badge badge-new'>חדש</span></div>
                            <div class='order-name'>{row['customer_name']}</div>
                        </div>
                        <div style='color:#6b7280; font-size:13px'>{created}</div>
                    </div>
                    <div class='order-items'>🛍️ {row['items']}</div>
                    <div class='order-meta'>
                        <span>📍 {address_clean}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            c_time, c_approve, c_cancel, c_del = st.columns([2.5, 2, 2, 0.7])

            with c_time:
                placeholder = "כמה דקות עד מוכן לאיסוף?" if is_pickup else "זמן הגעה משוער"
                time_val = st.text_input("⏱️", value="20 דקות", key=f"t_{oid}",
                                          label_visibility="collapsed", placeholder=placeholder)

            with c_approve:
                st.markdown('<div data-btn="approve">', unsafe_allow_html=True)
                if st.button("✅ אשר ושלח ללקוח", key=f"app_{oid}", use_container_width=True):
                    run_query(
                        "UPDATE orders SET status='אושר', delivery_time=%s, approved_at=NOW() WHERE id=%s",
                        (time_val, int(oid)), fetch=False
                    )
                    if is_pickup:
                        msg = f"היי {row['customer_name']}! ✅ ההזמנה שלך מאושרת.\n🛒 מוצרים: {row['items']}\n⏱️ מוכן לאיסוף בעוד: {time_val}\nתודה שקנית אצלנו! 🙏"
                        # נגן צליל איסוף
                        st.markdown('<div id="sound-trigger" data-sound="pickup" style="display:none"></div>', unsafe_allow_html=True)
                    else:
                        msg = f"היי {row['customer_name']}! ✅ ההזמנה שלך אושרה.\n🛵 זמן הגעה משוער: {time_val}\n🛍️ מוצרים: {row['items']}\nתודה! 🙏"
                        st.markdown('<div id="sound-trigger" data-sound="delivery" style="display:none"></div>', unsafe_allow_html=True)

                    ok = notify(row['address'], msg)
                    if ok:
                        st.success("✅ אושר ונשלחה הודעה ללקוח")
                    else:
                        st.warning("⚠️ אושר, אבל שליחת ההודעה נכשלה")
                    time.sleep(1)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            with c_cancel:
                st.markdown('<div data-btn="cancel">', unsafe_allow_html=True)
                if st.button("❌ בטל הזמנה", key=f"can_{oid}", use_container_width=True):
                    st.session_state.cancel_open[oid] = not st.session_state.cancel_open.get(oid, False)
                st.markdown('</div>', unsafe_allow_html=True)

            with c_del:
                st.markdown('<div data-btn="delete">', unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_{oid}", use_container_width=True, help="מחק"):
                    run_query("DELETE FROM orders WHERE id=%s", (int(oid),), fetch=False)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            # ביטול מורחב
            if st.session_state.cancel_open.get(oid, False):
                with st.container():
                    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
                    cr1, cr2 = st.columns([3, 1])
                    with cr1:
                        reason = st.selectbox("סיבת ביטול", ["חוסר במלאי","כתובת שגויה","לקוח לא זמין","אחר"], key=f"rs_{oid}")
                        if reason == "אחר":
                            reason = st.text_input("פרט:", key=f"rc_{oid}", placeholder="כתוב סיבה...") or "לא צוינה סיבה"
                    with cr2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown('<div data-btn="cancel">', unsafe_allow_html=True)
                        if st.button("אשר ביטול", key=f"cb_{oid}", use_container_width=True):
                            run_query("UPDATE orders SET status='בוטל', cancellation_reason=%s WHERE id=%s",
                                      (reason, int(oid)), fetch=False)
                            notify(row['address'], f"היי {row['customer_name']}, ההזמנה בוטלה ❌\nסיבה: {reason}\nמצטערים מאוד!")
                            st.session_state.cancel_open[oid] = False
                            time.sleep(1)
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# ══════════════════════════════════════
# TAB 2 — תלונות
# ══════════════════════════════════════
with tab2:
    try:
        conn = get_db()
        comp_df = pd.read_sql("SELECT * FROM complaints WHERE status='פתוח' ORDER BY created_at DESC", conn)
        conn.close()

        if comp_df.empty:
            st.markdown("""
                <div class='empty-state'>
                    <div class='icon'>😊</div>
                    <h3>אין תלונות פתוחות!</h3>
                    <p>כולם מרוצים — כך ממשיכים 💪</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            for _, row in comp_df.iterrows():
                t = row['created_at'].strftime('%H:%M — %d/%m/%Y')
                st.markdown(f"""
                    <div class='complaint-card'>
                        <div style='display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px; margin-bottom:12px'>
                            <div class='complaint-name'>⚠️ {row['customer_name']}</div>
                            <div style='color:#6b7280; font-size:13px'>{t}</div>
                        </div>
                        <div style='color:#9ca3af; font-size:13px; margin-bottom:8px'>📱 {row['phone']}</div>
                        <div class='complaint-desc'>{row['description']}</div>
                    </div>
                """, unsafe_allow_html=True)

                c_mark, _ = st.columns([1, 4])
                with c_mark:
                    st.markdown('<div data-btn="approve">', unsafe_allow_html=True)
                    if st.button("✅ סמן כטופל", key=f"cp_{row['id']}", use_container_width=True):
                        run_query("UPDATE complaints SET status='טופל' WHERE id=%s", (row['id'],), fetch=False)
                        st.success("✔ נסגר")
                        time.sleep(0.8)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    except:
        st.error("שגיאה בטעינת תלונות — ודא שהטבלה קיימת ב-DB")

# ══════════════════════════════════════
# TAB 3 — אושרו
# ══════════════════════════════════════
with tab3:
    conn = get_db()
    adf = pd.read_sql(
        "SELECT id, customer_name, items, order_type, delivery_time, approved_at FROM orders WHERE status='אושר' ORDER BY approved_at DESC LIMIT 60",
        conn
    )
    conn.close()
    if not adf.empty:
        st.dataframe(adf, use_container_width=True, hide_index=True,
            column_config={
                "id":            st.column_config.NumberColumn("מס'", format="%d"),
                "customer_name": "לקוח",
                "items":         "מוצרים",
                "order_type":    "סוג",
                "delivery_time": "זמן",
                "approved_at":   st.column_config.DatetimeColumn("אישור", format="DD/MM HH:mm"),
            })
    else:
        st.info("אין עדיין הזמנות שאושרו")

# ══════════════════════════════════════
# TAB 4 — בוטלו
# ══════════════════════════════════════
with tab4:
    conn = get_db()
    cdf = pd.read_sql(
        "SELECT id, customer_name, items, cancellation_reason, created_at FROM orders WHERE status='בוטל' ORDER BY created_at DESC LIMIT 60",
        conn
    )
    conn.close()
    if not cdf.empty:
        st.dataframe(cdf, use_container_width=True, hide_index=True,
            column_config={
                "id":                  st.column_config.NumberColumn("מס'", format="%d"),
                "customer_name":       "לקוח",
                "items":               "מוצרים",
                "cancellation_reason": "סיבה",
                "created_at":          st.column_config.DatetimeColumn("תאריך", format="DD/MM HH:mm"),
            })
    else:
        st.info("אין הזמנות מבוטלות")

# ══════════════════════════════════════
# TAB 5 — מלאי
# ══════════════════════════════════════
with tab5:
    sub1, sub2 = st.tabs(["📋 מוצרים קיימים", "➕ הוסף מוצר"])

    with sub1:
        ps = st.text_input("🔍 חפש מוצר", placeholder="שם מוצר...", key="ps")
        conn = get_db()
        pf = pd.read_sql("SELECT id, name, price, stock FROM products ORDER BY name", conn)
        conn.close()
        if ps:
            pf = pf[pf['name'].str.contains(ps, case=False, na=False)]

        if pf.empty:
            st.info("לא נמצאו מוצרים")
        else:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            for _, p in pf.iterrows():
                pid = p['id']
                c1, c2, c3, c4, c5 = st.columns([3, 1.5, 1.5, 0.8, 0.8])
                with c1:
                    new_name = st.text_input("שם", value=p['name'], key=f"pn_{pid}", label_visibility="collapsed")
                with c2:
                    new_price = st.number_input("מחיר", value=float(p['price']), min_value=0.0, step=0.5, key=f"pp_{pid}", label_visibility="collapsed", format="%.2f")
                with c3:
                    new_stock = st.number_input("מלאי", value=int(p['stock']), min_value=0, step=1, key=f"ps2_{pid}", label_visibility="collapsed")
                with c4:
                    st.markdown('<div data-btn="approve">', unsafe_allow_html=True)
                    if st.button("💾", key=f"sv_{pid}", use_container_width=True):
                        run_query("UPDATE products SET name=%s, price=%s, stock=%s WHERE id=%s",
                                  (new_name, new_price, new_stock, pid), fetch=False)
                        st.success("✅")
                        time.sleep(0.4)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                with c5:
                    st.markdown('<div data-btn="delete">', unsafe_allow_html=True)
                    if st.button("🗑️", key=f"dp_{pid}", use_container_width=True):
                        run_query("DELETE FROM products WHERE id=%s", (pid,), fetch=False)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    with sub2:
        with st.form("add_prod", clear_on_submit=True):
            a1, a2, a3 = st.columns([3, 2, 2])
            with a1:
                pname  = st.text_input("🏷️ שם המוצר", placeholder="לדוגמה: לחם אחיד")
            with a2:
                pprice = st.number_input("💰 מחיר (₪)", min_value=0.0, step=0.5, format="%.2f")
            with a3:
                pstock = st.number_input("📦 כמות", min_value=0, step=1, value=10)

            st.markdown('<div data-btn="approve">', unsafe_allow_html=True)
            if st.form_submit_button("➕ הוסף מוצר", use_container_width=True):
                if pname and pprice > 0:
                    run_query("INSERT INTO products (name, price, stock) VALUES (%s,%s,%s)",
                              (pname, pprice, pstock), fetch=False)
                    st.success(f"✅ '{pname}' נוסף!")
                    time.sleep(0.8)
                    st.rerun()
                else:
                    st.error("מלא שם ומחיר")
            st.markdown('</div>', unsafe_allow_html=True)

# ─── Footer ───
st.markdown("""
    <div style='text-align:center; padding:32px 0 8px; color:#374151; font-size:13px'>
        המכולת של הצדיק · ממשק ניהול v4.0
    </div>
""", unsafe_allow_html=True)
