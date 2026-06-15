import streamlit as st
import psycopg2
import psycopg2.pool
import pandas as pd
import os
import requests
import time
import io
from datetime import datetime, date

# ══════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════
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

# ══════════════════════════════════════════════
# CONNECTION POOL
# ══════════════════════════════════════════════
@st.cache_resource
def get_pool():
    return psycopg2.pool.ThreadedConnectionPool(minconn=1, maxconn=5, dsn=DB_URL)

def db_execute(sql: str, params=(), fetch: bool = True):
    pool = get_pool()
    conn = pool.getconn()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        if fetch:
            result = cur.fetchall()
        else:
            conn.commit()
            result = cur.rowcount
        cur.close()
        return result
    except Exception as e:
        conn.rollback()
        st.error(f"DB שגיאה: {e}")
        return [] if fetch else 0
    finally:
        pool.putconn(conn)

def db_df(sql: str, params=None):
    pool = get_pool()
    conn = pool.getconn()
    try:
        df = pd.read_sql(sql, conn, params=params)
        return df
    except Exception as e:
        st.error(f"DB שגיאה: {e}")
        return pd.DataFrame()
    finally:
        pool.putconn(conn)

# ══════════════════════════════════════════════
# ENSURE TABLES
# ══════════════════════════════════════════════
def ensure_promotions_table():
    db_execute("""
        CREATE TABLE IF NOT EXISTS promotions (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """, fetch=False)
    for col_sql in [
        "ALTER TABLE promotions ADD COLUMN IF NOT EXISTS description TEXT",
        "ALTER TABLE promotions ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT TRUE",
        "ALTER TABLE promotions ADD COLUMN IF NOT EXISTS never_ends BOOLEAN DEFAULT FALSE",
        "ALTER TABLE promotions ADD COLUMN IF NOT EXISTS start_date DATE",
        "ALTER TABLE promotions ADD COLUMN IF NOT EXISTS end_date DATE",
    ]:
        db_execute(col_sql, fetch=False)

# ══════════════════════════════════════════════
# CACHED QUERIES
# ══════════════════════════════════════════════
@st.cache_data(ttl=6)
def fetch_pending_orders():
    return db_df(
        "SELECT id, customer_name, items, address, order_type, created_at FROM orders WHERE status='ממתין לאישור' ORDER BY created_at DESC"
    )

@st.cache_data(ttl=6)
def fetch_counts():
    rows = db_execute("SELECT status, order_type FROM orders WHERE status='ממתין לאישור'")
    pending    = len(rows)
    deliveries = sum(1 for r in rows if 'איסוף' not in str(r[1]).lower())
    pickups    = pending - deliveries
    comp       = db_execute("SELECT COUNT(*) FROM complaints WHERE status='פתוח'")
    complaints = comp[0][0] if comp else 0
    return pending, deliveries, pickups, complaints

@st.cache_data(ttl=20)
def fetch_complaints():
    return db_df("SELECT * FROM complaints WHERE status='פתוח' ORDER BY created_at DESC")

@st.cache_data(ttl=30)
def fetch_approved():
    return db_df(
        "SELECT id, customer_name, items, order_type, address, delivery_time, approved_at FROM orders WHERE status='אושר' ORDER BY approved_at DESC LIMIT 60"
    )

@st.cache_data(ttl=30)
def fetch_cancelled():
    return db_df(
        "SELECT id, customer_name, items, cancellation_reason, created_at FROM orders WHERE status='בוטל' ORDER BY created_at DESC LIMIT 60"
    )

@st.cache_data(ttl=15)
def fetch_products(search=""):
    df = db_df("SELECT id, name, price, stock FROM products ORDER BY name")
    if search and not df.empty:
        df = df[df['name'].str.contains(search, case=False, na=False)]
    return df

@st.cache_data(ttl=10)
def fetch_promotions():
    try:
        return db_df("SELECT * FROM promotions ORDER BY created_at DESC")
    except:
        return pd.DataFrame()

@st.cache_data(ttl=10)
def fetch_active_promotions():
    try:
        today = date.today().isoformat()
        return db_df(f"""
            SELECT title, description FROM promotions
            WHERE active=TRUE
              AND (never_ends=TRUE OR (start_date <= '{today}' AND end_date >= '{today}'))
            ORDER BY created_at DESC
        """)
    except:
        return pd.DataFrame()

@st.cache_data(ttl=0)
def fetch_day_stats():
    today = datetime.now().strftime('%Y-%m-%d')
    rows  = db_execute(f"SELECT status FROM orders WHERE DATE(created_at)='{today}'")
    comp  = db_execute(f"SELECT COUNT(*) FROM complaints WHERE DATE(created_at)='{today}'")
    return {
        "total":      len(rows),
        "approved":   sum(1 for r in rows if r[0]=='אושר'),
        "cancelled":  sum(1 for r in rows if r[0]=='בוטל'),
        "pending":    sum(1 for r in rows if r[0]=='ממתין לאישור'),
        "complaints": comp[0][0] if comp else 0,
    }

def invalidate_orders():
    fetch_pending_orders.clear()
    fetch_counts.clear()
    fetch_approved.clear()
    fetch_cancelled.clear()

def invalidate_complaints():
    fetch_complaints.clear()

def invalidate_products():
    fetch_products.clear()

def invalidate_promotions():
    fetch_promotions.clear()
    fetch_active_promotions.clear()

# ══════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════
def extract_phone(addr):
    try:
        if "WA_ID:" in str(addr):
            return str(addr).split("WA_ID:")[-1].strip()
        c = str(addr).replace("-","").strip()
        return ("972" + c[1:]) if c.startswith("0") else c
    except:
        return None

def fmt_phone(addr):
    raw = extract_phone(addr)
    if not raw:
        return "—"
    if raw.startswith("972") and len(raw) == 12:
        local = "0" + raw[3:]
        return f"{local[:3]}-{local[3:6]}-{local[6:]}"
    return raw

def clean_address(addr_raw):
    """מחזיר כתובת נקיה בלי חלק הטלפון"""
    addr_raw = str(addr_raw)
    if "WA_ID:" in addr_raw:
        addr_raw = addr_raw.split("WA_ID:")[0]
    if "|" in addr_raw:
        addr_raw = addr_raw.split("|")[0]
    return addr_raw.strip()

def notify(addr, msg):
    phone = extract_phone(addr)
    if not phone:
        return False
    try:
        r = requests.post(
            f"{BOT_URL}/send_update",
            json={"phone": phone, "message": msg},
            headers={"X-Internal-Secret": INTERNAL_SECRET},
            timeout=8
        )
        return r.status_code == 200
    except:
        return False

def _read_csv_hebrew(uploaded_file):
    """קריאת CSV עם טיפול אוטומטי בקידוד עברי."""
    encodings = ['utf-8-sig', 'utf-8', 'cp1255', 'windows-1255', 'iso-8859-8', 'latin-1']
    last_err = None
    for enc in encodings:
            try:
                if file_ext == "csv":
                    # התיקון כאן: הוספנו זיהוי מפריד אוטומטי והתעלמות משורות בעייתיות
                    df_raw = pd.read_csv(
                        io.BytesIO(bytes_data), 
                        encoding=enc, 
                        sep=None, 
                        engine='python',
                        on_bad_lines='skip'
                    )
                else:
                    df_raw = pd.read_excel(io.BytesIO(bytes_data))
                parsed = True
                break
            except Exception as e:
                last_err = str(e)

def _map_columns(cols):
    """מיפוי גמיש של שמות עמודות לפי רשימה מורחבת, תוך ניקוי רווחים וקטנות."""
    NAME_KEYS  = {'שם','שם המוצר','שם מוצר','name','product_name','product','מוצר','item','פריט','תיאור'}
    PRICE_KEYS = {'מחיר','מחיר ליחידה','מחיר יחידה','מחיר ₪','מחיר (₪)','price','cost','עלות'}
    STOCK_KEYS = {'מלאי','כמות','stock','quantity','qty','כמות במלאי'}
    col_map = {}
    for c in cols:
        cn = c.strip().lower()
        if cn in NAME_KEYS  and 'name'  not in col_map: col_map['name']  = c
        if cn in PRICE_KEYS and 'price' not in col_map: col_map['price'] = c
        if cn in STOCK_KEYS and 'stock' not in col_map: col_map['stock'] = c
    return col_map

def import_products_from_df(df_import):
    """
    Upsert מוצרים מ-DataFrame.
    חובה: name/שם + price/מחיר.  אופציונלי: stock/מלאי.
    לא מוחק שום מוצר קיים ב-DB.
    מחזיר (inserted, updated, errors).
    """
    inserted, updated, errors = 0, 0, []

    # נרמול שמות עמודות
    df_import.columns = [str(c).strip() for c in df_import.columns]
    col_map = _map_columns(df_import.columns)

    if 'name' not in col_map or 'price' not in col_map:
        found = ", ".join(df_import.columns.tolist())
        return 0, 0, [f"לא זוהו עמודות חובה. עמודות שנמצאו: {found}. נדרש: שם/name ומחיר/price"]

    for i, row in df_import.iterrows():
        try:
            name_raw = str(row[col_map['name']]).strip()
            if not name_raw or name_raw.lower() in ('nan','none',''):
                continue
            price_raw = str(row[col_map['price']]).replace('₪','').replace(',','').strip()
            price = float(price_raw)
            if 'stock' in col_map:
                stock_raw = str(row[col_map['stock']]).replace(',','').strip()
                stock = int(float(stock_raw)) if stock_raw not in ('','nan','none') else 0
            else:
                stock = 0

            existing = db_execute("SELECT id FROM products WHERE name=%s", (name_raw,))
            if existing:
                db_execute("UPDATE products SET price=%s, stock=%s WHERE name=%s",
                           (price, stock, name_raw), fetch=False)
                updated += 1
            else:
                db_execute("INSERT INTO products (name, price, stock) VALUES (%s,%s,%s)",
                           (name_raw, price, stock), fetch=False)
                inserted += 1
        except Exception as e:
            errors.append(f"שורה {i+2}: {e}")

    return inserted, updated, errors

# ══════════════════════════════════════════════
# STYLES — צבע אחיד, כהה לאורך כל הממשק
# ══════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rubik:wght@300;400;500;600;700;800;900&family=Rubik+Mono+One&display=swap');

/* ── RESET & BASE ── */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body,[class*="css"]{font-family:'Rubik',sans-serif!important;direction:rtl!important;font-size:15px!important}
.stApp{background:#0a0d16!important;color:#c8cfe0!important}
#MainMenu,footer,header,[data-testid="stDecoration"],[data-testid="stToolbar"]{display:none!important}
.block-container{padding:1.2rem 1.6rem 3rem!important;max-width:100%!important}
section[data-testid="stSidebar"]{display:none!important}

/* ── STATS ── */
.stats-row{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px}
@media(max-width:860px){.stats-row{grid-template-columns:repeat(2,1fr)}}
.sc{border-radius:16px;padding:20px 22px;border:1px solid rgba(255,255,255,.06);transition:transform .18s,box-shadow .18s;position:relative;overflow:hidden}
.sc:hover{transform:translateY(-2px);box-shadow:0 14px 40px rgba(0,0,0,.5)}
.sc::after{content:attr(data-icon);position:absolute;right:10px;bottom:4px;font-size:56px;opacity:.09;pointer-events:none;line-height:1}
.sc .num{font-size:44px;font-weight:900;line-height:1;font-family:'Rubik Mono One',monospace}
.sc .lbl{font-size:11px;font-weight:600;letter-spacing:.7px;text-transform:uppercase;margin-top:6px;color:#5a6280}
.sc-pending {background:linear-gradient(135deg,#13102b,#1a1840)} .sc-pending  .num{color:#a78bfa}
.sc-delivery{background:linear-gradient(135deg,#09172a,#0e1e36)} .sc-delivery .num{color:#38bdf8}
.sc-pickup  {background:linear-gradient(135deg,#091a12,#0d2018)} .sc-pickup   .num{color:#34d399}
.sc-comp    {background:linear-gradient(135deg,#1e0808,#280d0d)} .sc-comp     .num{color:#f87171}

/* ── BANNERS ── */
.alert-banner{background:linear-gradient(90deg,#5b21b6,#4338ca 50%,#0284c7);border-radius:12px;padding:13px 22px;margin-bottom:16px;display:flex;align-items:center;gap:10px;font-size:16px;font-weight:700;color:#fff;animation:breathe 2.5s ease-in-out infinite;box-shadow:0 4px 28px rgba(91,33,182,.3)}
.promo-banner{background:linear-gradient(90deg,#92400e,#b45309 50%,#d97706);border-radius:12px;padding:11px 18px;margin-bottom:10px;display:flex;align-items:center;gap:10px;font-size:14px;font-weight:700;color:#fff;box-shadow:0 4px 20px rgba(146,64,14,.3)}
@keyframes breathe{0%,100%{box-shadow:0 4px 28px rgba(91,33,182,.3)}50%{box-shadow:0 4px 45px rgba(2,132,199,.45)}}
.adot{width:9px;height:9px;border-radius:50%;background:#fff;animation:blink 1s step-start infinite;flex-shrink:0}
.pdot{width:9px;height:9px;border-radius:50%;background:#fffbeb;flex-shrink:0}
@keyframes blink{50%{opacity:0}}

/* ── ORDER CARDS ── */
.oc{background:#0d1020;border:1px solid #16192e;border-radius:16px;padding:18px 22px;margin-bottom:6px;position:relative;transition:border-color .18s}
.oc:hover{border-color:#252a50}
.oc .stripe{position:absolute;top:0;right:0;width:5px;height:100%;border-radius:0 16px 16px 0}
.s-del  {background:linear-gradient(180deg,#38bdf8,#0ea5e9)}
.s-pick {background:linear-gradient(180deg,#34d399,#10b981)}
.s-comp {background:linear-gradient(180deg,#f87171,#ef4444)}
.s-promo{background:linear-gradient(180deg,#f59e0b,#d97706)}
.onum{font-size:11px;font-weight:700;color:#2a3058;letter-spacing:1px;text-transform:uppercase}
.oname{font-size:22px;font-weight:800;color:#e8ecff;margin:3px 0 10px}
.oitems{background:#080b18;border:1px solid #141830;border-radius:10px;padding:10px 14px;font-size:14px;color:#7a84a0;margin-bottom:10px;line-height:1.6}
.oaddr{background:#080e1a;border:1px solid #10192a;border-radius:8px;padding:7px 12px;font-size:13px;color:#4a7090;margin-bottom:8px;display:flex;align-items:center;gap:6px}
.ometa{display:flex;gap:16px;flex-wrap:wrap;margin-top:2px}
.ometa span{font-size:12px;color:#4a5a80}
.phone-pill{background:#080f1e;border:1px solid #112540;border-radius:20px;padding:3px 12px;font-size:12px;color:#38bdf8;font-weight:600}
.badge{display:inline-flex;align-items:center;gap:3px;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700}
.b-del{background:#071a2c;color:#38bdf8;border:1px solid #0a3558}
.b-pick{background:#061a0f;color:#34d399;border:1px solid #0a4025}
.b-new{background:#221700;color:#fbbf24;border:1px solid #5a3c00;animation:npulse 2s ease-in-out infinite}
.b-promo{background:#1e1200;color:#f59e0b;border:1px solid #6a3e00}
@keyframes npulse{0%,100%{opacity:1}50%{opacity:.45}}

/* ── COMPLAINT CARDS ── */
.cc{background:#0d0606;border:1px solid #2e0c0c;border-radius:16px;padding:18px 22px;margin-bottom:6px;position:relative}
.cname{font-size:19px;font-weight:800;color:#fca5a5;margin-bottom:6px}
.cdesc{font-size:14px;color:#7a7e8a;line-height:1.6}
.reply-box{background:#070c18;border:1px solid #141e40;border-radius:9px;padding:10px 14px;font-size:13px;color:#4a6090;line-height:1.5;margin-top:8px}

/* ── PROMO CARDS ── */
.pc{background:#0c0a04;border:1px solid #2e2600;border-radius:16px;padding:18px 22px;margin-bottom:6px;position:relative}
.pname{font-size:19px;font-weight:800;color:#fcd34d;margin-bottom:6px}
.pdesc{font-size:14px;color:#7a7e8a;line-height:1.6;margin-bottom:8px}
.p-active{border-color:#4a3a00}
.p-inactive{opacity:.45;filter:saturate(.3)}

/* ── APPROVED ROW CARD ── */
.appr-card{background:#0d1020;border:1px solid #16192e;border-radius:14px;padding:14px 18px;margin-bottom:6px;display:grid;grid-template-columns:auto 1fr auto;gap:10px;align-items:start}
.appr-num{font-size:10px;font-weight:700;color:#2a3058;letter-spacing:1px}
.appr-name{font-size:17px;font-weight:800;color:#e8ecff}
.appr-items{font-size:13px;color:#4a5278;margin-top:3px;line-height:1.5}
.appr-addr{font-size:12px;color:#2a5070;margin-top:4px;display:flex;align-items:center;gap:5px}
.appr-time{font-size:11px;color:#1e2840;text-align:left}

/* ── APPROVED LIGHT CARDS ── */
.oc-light{background:#f0f7f1;border:1px solid #c8e0cc;border-radius:16px;padding:18px 22px;margin-bottom:6px;position:relative;transition:border-color .18s}
.oc-light:hover{border-color:#8ab89a}
.oc-light .stripe{position:absolute;top:0;right:0;width:5px;height:100%;border-radius:0 16px 16px 0}
.onum-light{font-size:11px;font-weight:700;color:#5a8060;letter-spacing:1px;text-transform:uppercase}
.oname-light{font-size:22px;font-weight:800;color:#1a3020;margin:3px 0 10px}
.oitems-light{background:#e0f0e4;border:1px solid #b8d8be;border-radius:10px;padding:10px 14px;font-size:14px;color:#3a6040;margin-bottom:10px;line-height:1.6}
.oaddr-light{background:#d8eedd;border:1px solid #a8d0b0;border-radius:8px;padding:7px 12px;font-size:13px;color:#2a5035;margin-bottom:8px;display:flex;align-items:center;gap:6px;font-weight:600}

/* ── CANCEL PANEL ── */
.cancel-panel{background:#070404;border:1px dashed #6b1010;border-radius:12px;padding:14px 18px;margin:6px 0}

/* ── BUTTONS ── */
.stButton>button{
  font-family:'Rubik',sans-serif!important;font-weight:700!important;
  border-radius:10px!important;border:none!important;
  padding:11px 14px!important;font-size:14px!important;
  width:100%!important;transition:transform .12s,filter .12s!important;
  white-space:nowrap!important;cursor:pointer!important
}
.stButton>button:hover{transform:translateY(-1px)!important;filter:brightness(1.12)!important}
div[data-btn="approve"]    .stButton>button{background:linear-gradient(135deg,#047857,#059669)!important;color:#fff!important;box-shadow:0 3px 12px rgba(5,150,105,.25)!important}
div[data-btn="cancel"]     .stButton>button{background:linear-gradient(135deg,#991b1b,#dc2626)!important;color:#fff!important}
div[data-btn="cc"]         .stButton>button{background:linear-gradient(135deg,#7f1d1d,#b91c1c)!important;color:#fff!important}
div[data-btn="delete"]     .stButton>button{background:#0d1020!important;color:#3a4268!important;border:1px solid #16192e!important}
div[data-btn="delete"]     .stButton>button:hover{background:#130708!important;color:#f87171!important;border-color:#6b1010!important}
div[data-btn="refresh"]    .stButton>button{background:linear-gradient(135deg,#1e40af,#2563eb)!important;color:#fff!important}
div[data-btn="save"]       .stButton>button{background:linear-gradient(135deg,#0369a1,#0284c7)!important;color:#fff!important}
div[data-btn="reply"]      .stButton>button{background:linear-gradient(135deg,#3730a3,#4f46e5)!important;color:#fff!important}
div[data-btn="logout"]     .stButton>button{background:#0d1020!important;color:#3a4268!important;border:1px solid #16192e!important}
div[data-btn="break"]      .stButton>button{background:linear-gradient(135deg,#1f2937,#374151)!important;color:#9ca3af!important}
div[data-btn="endday"]     .stButton>button{background:linear-gradient(135deg,#78350f,#92400e)!important;color:#fef3c7!important}
div[data-btn="login"]      .stButton>button{background:linear-gradient(135deg,#3730a3,#4f46e5)!important;color:#fff!important;font-size:16px!important;padding:14px!important;box-shadow:0 4px 22px rgba(79,70,229,.35)!important}
div[data-btn="promo-add"]  .stButton>button{background:linear-gradient(135deg,#78350f,#b45309)!important;color:#fff!important}
div[data-btn="promo-toggle"].stButton>button{background:linear-gradient(135deg,#064e3b,#065f46)!important;color:#6ee7b7!important;border:1px solid #047857!important}
div[data-btn="promo-del"]  .stButton>button{background:#0c0a04!important;color:#3a2a00!important;border:1px solid #2e2600!important}
div[data-btn="promo-del"]  .stButton>button:hover{color:#f59e0b!important;border-color:#78350f!important}
div[data-btn="import"]     .stButton>button{background:linear-gradient(135deg,#1e3a5f,#1d4ed8)!important;color:#fff!important}

/* ── INPUTS — כולם כהים ואחידים ── */
.stTextInput>div>div>input,
.stNumberInput>div>div>input,
.stSelectbox>div>div>div{
  background:#080b18!important;color:#c8cfe0!important;
  border:1px solid #1a1e30!important;border-radius:10px!important;
  font-family:'Rubik',sans-serif!important;font-size:14px!important
}
.stTextInput>div>div>input::placeholder{color:#2a3058!important}
.stTextArea>div>div>textarea{
  background:#080b18!important;color:#c8cfe0!important;
  border:1px solid #1a1e30!important;border-radius:10px!important;
  font-family:'Rubik',sans-serif!important;font-size:14px!important
}
.stDateInput>div>div>input{
  background:#080b18!important;color:#c8cfe0!important;
  border:1px solid #1a1e30!important;border-radius:10px!important;
  font-family:'Rubik',sans-serif!important;font-size:14px!important
}
/* date picker */
[data-baseweb="calendar"]{background:#0d1020!important;border:1px solid #1a1e30!important}
[data-baseweb="calendar"] *{color:#c8cfe0!important}
[data-baseweb="calendar"] [aria-selected="true"]{background:#4338ca!important}
/* labels */
label{color:#3a4268!important;font-size:12px!important;font-weight:600!important;letter-spacing:.4px!important}
.stCheckbox>label{color:#7a84a0!important;font-size:14px!important;font-weight:500!important}
/* selectbox dropdown */
[data-baseweb="popover"],[data-baseweb="menu"]{background:#0d1020!important;border:1px solid #1a1e30!important}
[data-baseweb="option"]{background:#0d1020!important;color:#c8cfe0!important}
[data-baseweb="option"]:hover,[data-baseweb="option"]:focus{background:#141830!important}
/* number input arrows */
.stNumberInput button{background:#141830!important;color:#c8cfe0!important;border:none!important}
/* file uploader */
[data-testid="stFileUploader"]{background:#080b18!important;border:2px dashed #1a1e30!important;border-radius:12px!important}
[data-testid="stFileUploader"] *{color:#4a5278!important}
[data-testid="stFileUploaderDropzone"]{background:#080b18!important}
/* expander */
[data-testid="stExpander"]{background:#0d1020!important;border:1px solid #16192e!important;border-radius:12px!important}
[data-testid="stExpander"] summary{color:#7a84a0!important;font-weight:600!important}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"]{
  background:#080b18!important;border-radius:12px!important;
  padding:5px!important;gap:3px!important;
  border:1px solid #16192e!important;flex-wrap:wrap!important
}
.stTabs [data-baseweb="tab"]{
  background:transparent!important;color:#3a4268!important;
  border-radius:8px!important;font-weight:700!important;
  font-size:13px!important;padding:9px 16px!important;
  border:none!important;transition:all .18s!important;white-space:nowrap!important
}
.stTabs [data-baseweb="tab"]:hover{background:#0d1020!important;color:#6a78a0!important}
.stTabs [aria-selected="true"]{
  background:linear-gradient(135deg,#1e3a8a,#3730a3)!important;
  color:#fff!important;box-shadow:0 2px 10px rgba(55,48,163,.3)!important
}
.stTabs [data-baseweb="tab-panel"]{padding-top:16px!important}

/* ── MISC ── */
.empty-state{text-align:center;padding:60px 20px;color:#141830}
.empty-state .icon{font-size:52px;margin-bottom:12px}
.empty-state h3{color:#3a4a70!important;font-size:17px!important;font-weight:700!important}
.div-line{height:1px;background:#0e1224;margin:8px 0 14px}
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:#080b18}
::-webkit-scrollbar-thumb{background:#16192e;border-radius:3px}
.stDataFrame{background:#080b18!important;border-radius:12px!important;border:1px solid #16192e!important;overflow:hidden}
.stDataFrame *{color:#c8cfe0!important;background:transparent!important}
.stDataFrame thead th{background:#0d1020!important;color:#4a5278!important;font-size:11px!important;font-weight:700!important;letter-spacing:.5px!important}
.stDataFrame tbody tr:hover td{background:#0d1020!important}

/* ── END-OF-DAY STATS ── */
.stats-modal{background:#0d1020;border:1px solid #16192e;border-radius:18px;padding:28px 32px;margin:16px 0}
.sg{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-top:14px}
@media(min-width:560px){.sg{grid-template-columns:repeat(4,1fr)}}
.sb{background:#080b18;border:1px solid #16192e;border-radius:12px;padding:16px;text-align:center}
.sb .big{font-size:36px;font-weight:900;font-family:'Rubik Mono One',monospace}
.sb .sm{font-size:11px;font-weight:600;letter-spacing:.5px;text-transform:uppercase;color:#2a3058;margin-top:4px}
.sp .big{color:#34d399}.so .big{color:#a78bfa}.sca .big{color:#f87171}.scm .big{color:#fbbf24}

/* ── LOGIN ── */
.lc{
  background:#0d1020;border:1px solid #16192e;border-radius:22px;
  padding:44px 48px;text-align:center;
  box-shadow:0 24px 80px rgba(0,0,0,.7);margin-top:60px
}
.li{font-size:62px;margin-bottom:10px;line-height:1}
.lc h1{font-size:24px!important;font-weight:900!important;color:#e8ecff!important;margin-bottom:6px}
.lc p{color:#6a78a0;font-size:13px;margin-bottom:20px}
</style>

<script>
const _AC=window.AudioContext||window.webkitAudioContext;
let _ac=null;
function _ctx(){if(!_ac||_ac.state==='closed')_ac=new _AC();if(_ac.state==='suspended')_ac.resume();return _ac}
function playD(){const c=_ctx(),t=c.currentTime;[[0,440],[.13,560],[.26,680]].forEach(([d,f])=>{const o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);o.frequency.value=f;o.type='sine';g.gain.setValueAtTime(0,t+d);g.gain.linearRampToValueAtTime(.36,t+d+.04);g.gain.exponentialRampToValueAtTime(.001,t+d+.2);o.start(t+d);o.stop(t+d+.22)})}
function playP(){const c=_ctx(),t=c.currentTime;[0,.2].forEach(d=>{const o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);o.frequency.value=880;o.type='triangle';g.gain.setValueAtTime(0,t+d);g.gain.linearRampToValueAtTime(.28,t+d+.03);g.gain.exponentialRampToValueAtTime(.001,t+d+.16);o.start(t+d);o.stop(t+d+.18)})}
function playC(){const c=_ctx(),t=c.currentTime;const o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);o.frequency.setValueAtTime(260,t);o.frequency.linearRampToValueAtTime(180,t+.5);o.type='sawtooth';g.gain.setValueAtTime(.2,t);g.gain.linearRampToValueAtTime(0,t+.55);o.start(t);o.stop(t+.6)}
function playN(){const c=_ctx(),t=c.currentTime;[523,659,784,1047].forEach((f,i)=>{const o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);o.frequency.value=f;o.type='sine';const d=t+i*.1;g.gain.setValueAtTime(0,d);g.gain.linearRampToValueAtTime(.3,d+.03);g.gain.exponentialRampToValueAtTime(.001,d+.2);o.start(d);o.stop(d+.22)})}
let _pv={o:-1,c:-1,s:''};
function _w(){
  const oe=document.getElementById('_oc'),ce=document.getElementById('_cc'),se=document.getElementById('_st');
  if(!oe||!ce||!se)return;
  const o=parseInt(oe.dataset.v||-1),cmp=parseInt(ce.dataset.v||-1),snd=se.dataset.v||'';
  if(snd&&snd!==_pv.s){_pv.s=snd;if(snd==='d')playD();else if(snd==='p')playP();else if(snd==='c')playC();else if(snd==='n')playN();}
  if(_pv.o>=0&&o>_pv.o)playN();
  if(_pv.c>=0&&cmp>_pv.c)playC();
  _pv.o=o;_pv.c=cmp;
}
setInterval(_w,900);
let _li=Date.now();
document.addEventListener('click',()=>_li=Date.now());
document.addEventListener('keydown',()=>_li=Date.now());
document.addEventListener('touchstart',()=>_li=Date.now());
setInterval(()=>{if(Date.now()-_li>5000){const b=Array.from(document.querySelectorAll('button')).find(x=>x.textContent.trim()==='🔄');if(b)b.click();}},12000);
setInterval(()=>{try{fetch(window.location.href,{method:'HEAD'})}catch(e){}},100000);
</script>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════
for k, v in {
    'logged_in': False, 'prev_p': -1, 'prev_c': -1,
    'sound': '', 'cancel_open': {}, 'cancel_reason': {},
    'cancel_custom': {}, 'reply_open': {}, 'show_end': False,
    'show_exit': False, 'active_filter': 'all',
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════
# LOGIN — מוצג במרכז המסך, בלי גלילה
# ══════════════════════════════════════════════
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("""
            <div class='lc'>
                <div class='li'>🛒</div>
                <h1>המכולת של הצדיק</h1>
                <p>ממשק ניהול מתקדם · כניסת מנהל</p>
            </div>
        """, unsafe_allow_html=True)
        pwd = st.text_input(" ", type="password", placeholder="🔑  סיסמה...", label_visibility="collapsed", key="login_pwd")
        st.markdown('<div data-btn="login">', unsafe_allow_html=True)
        if st.button("כניסה לניהול  →", use_container_width=True, key="login_btn"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                ensure_promotions_table()
                st.rerun()
            else:
                st.error("❌ סיסמה שגויה")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

ensure_promotions_table()

# ══════════════════════════════════════════════
# END-OF-DAY
# ══════════════════════════════════════════════
if st.session_state.show_end:
    fetch_day_stats.clear()
    s = fetch_day_stats()
    st.markdown(f"""
        <div class='stats-modal'>
            <div style='font-size:22px;font-weight:900;color:#e8ecff;margin-bottom:3px'>
                📊 סיכום היום · {datetime.now().strftime('%d/%m/%Y')}
            </div>
        </div>
        <div class='sg'>
          <div class='sb so'><div class='big'>{s['total']}</div><div class='sm'>סה"כ הזמנות</div></div>
          <div class='sb sp'><div class='big'>{s['approved']}</div><div class='sm'>אושרו</div></div>
          <div class='sb sca'><div class='big'>{s['cancelled']}</div><div class='sm'>בוטלו</div></div>
          <div class='sb scm'><div class='big'>{s['complaints']}</div><div class='sm'>תלונות</div></div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    ca, cb = st.columns(2)
    with ca:
        if st.button("← חזור לניהול", use_container_width=True):
            st.session_state.show_end = False
            st.rerun()
    with cb:
        st.markdown('<div data-btn="logout">', unsafe_allow_html=True)
        if st.button("🚪 סגור וצא", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.show_end  = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════
pending, deliveries, pickups, complaints = fetch_counts()

sound = st.session_state.sound
if st.session_state.prev_p >= 0 and pending > st.session_state.prev_p and not sound:
    sound = 'n'
if st.session_state.prev_c >= 0 and complaints > st.session_state.prev_c and not sound:
    sound = 'c'
st.session_state.prev_p = pending
st.session_state.prev_c = complaints
st.session_state.sound  = ''

st.markdown(f"""
<div id='_oc' data-v='{pending}'    style='display:none'></div>
<div id='_cc' data-v='{complaints}' style='display:none'></div>
<div id='_st' data-v='{sound}'      style='display:none'></div>
""", unsafe_allow_html=True)

# ── HEADER ──
h1, h2 = st.columns([5, 1])
with h1:
    st.markdown(f"""
        <div style='margin-bottom:16px'>
            <div style='font-size:26px;font-weight:900;color:#e8ecff;letter-spacing:-.5px'>
                🛒 המכולת של הצדיק
            </div>
            <div style='font-size:13px;color:#1e2440;margin-top:3px'>
                {datetime.now().strftime('%A %d/%m/%Y · %H:%M')}
            </div>
        </div>
    """, unsafe_allow_html=True)
with h2:
    r1, r2 = st.columns(2)
    with r1:
        st.markdown('<div data-btn="refresh">', unsafe_allow_html=True)
        if st.button("🔄", help="רענן", key="hr"):
            invalidate_orders(); invalidate_complaints(); invalidate_promotions()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with r2:
        st.markdown('<div data-btn="logout">', unsafe_allow_html=True)
        if st.button("🚪", help="יציאה", key="hx"):
            st.session_state.show_exit = not st.session_state.show_exit
        st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.show_exit:
    ex1, ex2, ex3 = st.columns([2, 2.5, 3])
    with ex1:
        st.markdown('<div data-btn="break">', unsafe_allow_html=True)
        if st.button("☕ הפסקה", use_container_width=True):
            st.session_state.logged_in = False; st.session_state.show_exit = False; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with ex2:
        st.markdown('<div data-btn="endday">', unsafe_allow_html=True)
        if st.button("📊 סיום יום", use_container_width=True):
            st.session_state.show_exit = False; st.session_state.show_end = True; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with ex3:
        st.markdown("<div style='font-size:12px;color:#1e2440;padding:8px 0;line-height:1.6'>☕ סגור, הזמנות ממשיכות<br>📊 ראה סטטיסטיקה ואז צא</div>", unsafe_allow_html=True)

# ── PROMO BANNERS ──
active_promos = fetch_active_promotions()
if not active_promos.empty:
    for _, promo in active_promos.iterrows():
        desc_part = f" · {promo['description']}" if promo.get('description') else ""
        st.markdown(f"""
            <div class='promo-banner'>
                <div class='pdot'></div>
                🏷️ מבצע פעיל: <strong>{promo['title']}</strong>{desc_part}
            </div>
        """, unsafe_allow_html=True)

# ── STATS ──
st.markdown(f"""
<div class='stats-row'>
  <div class='sc sc-pending'  data-icon='📦'><div class='num'>{pending}</div><div class='lbl'>ממתינות לטיפול</div></div>
  <div class='sc sc-delivery' data-icon='🛵'><div class='num'>{deliveries}</div><div class='lbl'>משלוחים</div></div>
  <div class='sc sc-pickup'   data-icon='🛒'><div class='num'>{pickups}</div><div class='lbl'>איסופים</div></div>
  <div class='sc sc-comp'     data-icon='⚠️'><div class='num'>{complaints}</div><div class='lbl'>תלונות פתוחות</div></div>
</div>
""", unsafe_allow_html=True)

# ── FILTER BUTTONS ──
fc1, fc2, fc3 = st.columns(3)
for col, lbl, key, fval in [
    (fc1,"📦 הכל","fa","all"),
    (fc2,"🛵 משלוחים","fd","delivery"),
    (fc3,"🛒 איסופים","fp","pickup"),
]:
    with col:
        active = st.session_state.active_filter == fval
        st.markdown(f'<div data-btn="{"approve" if active else "delete"}">', unsafe_allow_html=True)
        if st.button(lbl, key=key, use_container_width=True):
            st.session_state.active_filter = fval; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

if pending > 0:
    st.markdown(f"""
        <div class='alert-banner'>
            <div class='adot'></div>
            {pending} הזמנה{'ות' if pending>1 else ''} מחכ{'ות' if pending>1 else 'ה'} לאישורך!
        </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════
t1, t2, t3, t4, t5, t6 = st.tabs([
    f"📦 לטיפול ({pending})",
    f"⚠️ תלונות ({complaints})",
    "✅ אושרו", "❌ בוטלו", "🏷️ מבצעים", "🏪 מלאי",
])

# ──────────────────────────────────────────────
# TAB 1 — PENDING
# ──────────────────────────────────────────────
with t1:
    srch = st.text_input("🔍", placeholder="שם / מוצר / מספר הזמנה...", key="s1", label_visibility="collapsed")
    df   = fetch_pending_orders()
    filt = st.session_state.active_filter
    if filt == 'delivery': df = df[~df['order_type'].str.contains('איסוף', na=False)]
    elif filt == 'pickup': df = df[df['order_type'].str.contains('איסוף', na=False)]
    if srch:
        m = (df['customer_name'].str.contains(srch,case=False,na=False) |
             df['items'].str.contains(srch,case=False,na=False) |
             df['id'].astype(str).str.contains(srch))
        df = df[m]

    if df.empty:
        st.markdown('<div class="empty-state"><div class="icon">🎉</div><h3>כל ההזמנות טופלו!</h3></div>', unsafe_allow_html=True)
    else:
        for _, row in df.iterrows():
            oid        = int(row['id'])
            otype      = str(row.get('order_type','משלוח'))
            is_pick    = 'איסוף' in otype
            stripe     = 's-pick' if is_pick else 's-del'
            badge      = "<span class='badge b-pick'>🛒 איסוף</span>" if is_pick else "<span class='badge b-del'>🛵 משלוח</span>"
            addr_raw   = str(row['address'])
            addr_disp  = clean_address(addr_raw)
            phone_disp = fmt_phone(addr_raw)
            created    = row['created_at'].strftime('%H:%M  %d/%m')

            st.markdown(f"""
                <div class='oc'>
                    <div class='stripe {stripe}'></div>
                    <div style='display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:6px'>
                        <div>
                            <div class='onum'>#{oid} · {badge} <span class='badge b-new'>חדש</span></div>
                            <div class='oname'>{row['customer_name']}</div>
                        </div>
                        <div style='display:flex;flex-direction:column;align-items:flex-end;gap:6px'>
                            <div style='color:#1e2440;font-size:12px'>{created}</div>
                            <span class='phone-pill'>📱 {phone_disp}</span>
                        </div>
                    </div>
                    <div class='oitems'>🛍️ {row['items']}</div>
                    <div class='ometa'><span>📍 {addr_disp}</span></div>
                </div>
            """, unsafe_allow_html=True)

            c1, c2, c3, c4 = st.columns([2.4, 2.2, 2.2, 0.65])
            with c1:
                tv = st.text_input("⏱", value="20 דקות", key=f"tv_{oid}", label_visibility="collapsed",
                                   placeholder="מוכן בעוד..." if is_pick else "זמן הגעה...")
            with c2:
                st.markdown('<div data-btn="approve">', unsafe_allow_html=True)
                if st.button("✅ אשר ושלח ללקוח", key=f"ap_{oid}", use_container_width=True):
                    db_execute("UPDATE orders SET status='אושר', delivery_time=%s, approved_at=NOW() WHERE id=%s", (tv, oid), fetch=False)
                    msg = (f"היי {row['customer_name']}! ✅ ההזמנה אושרה.\n"
                           f"{'🛒 מוכן לאיסוף בעוד: ' if is_pick else '🛵 זמן הגעה: '}{tv}\n"
                           f"🛍️ {row['items']}\nתודה! 🙏")
                    ok = notify(row['address'], msg)
                    st.session_state.sound = 'p' if is_pick else 'd'
                    invalidate_orders()
                    st.success("✅ אושר!" + (" הודעה נשלחה" if ok else " (הודעה נכשלה)"))
                    time.sleep(.9); st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with c3:
                st.markdown('<div data-btn="cancel">', unsafe_allow_html=True)
                if st.button("❌ בטל", key=f"cbt_{oid}", use_container_width=True):
                    st.session_state.cancel_open[oid] = not st.session_state.cancel_open.get(oid, False)
                st.markdown('</div>', unsafe_allow_html=True)
            with c4:
                st.markdown('<div data-btn="delete">', unsafe_allow_html=True)
                if st.button("🗑️", key=f"dl_{oid}", use_container_width=True, help="מחק"):
                    db_execute("DELETE FROM orders WHERE id=%s", (oid,), fetch=False)
                    invalidate_orders(); st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            if st.session_state.cancel_open.get(oid, False):
                st.markdown("<div class='cancel-panel'>", unsafe_allow_html=True)
                st.markdown("<div style='font-size:13px;font-weight:700;color:#f87171;margin-bottom:10px'>🔴 סיבת ביטול (אופציונלי)</div>", unsafe_allow_html=True)
                cp1, cp2, cp3 = st.columns([3, 1.5, 1])
                with cp1:
                    chosen = st.selectbox("סיבה", ["— ללא סיבה —","חוסר במלאי","כתובת שגויה","לקוח לא זמין","מחוץ לאזור","אחר"],
                                          key=f"rs_{oid}", label_visibility="collapsed")
                    st.session_state.cancel_reason[oid] = chosen
                    if chosen == "אחר":
                        custom = st.text_input("פרט", key=f"rc_{oid}", placeholder="סיבה מפורטת...", label_visibility="collapsed")
                        st.session_state.cancel_custom[oid] = custom
                with cp2:
                    st.markdown('<div data-btn="cc">', unsafe_allow_html=True)
                    if st.button("✔ אשר ביטול", key=f"ccf_{oid}", use_container_width=True):
                        raw = st.session_state.cancel_reason.get(oid, "— ללא סיבה —")
                        if raw == "— ללא סיבה —":   reason = None
                        elif raw == "אחר":           reason = st.session_state.cancel_custom.get(oid,"") or None
                        else:                        reason = raw
                        db_execute("UPDATE orders SET status='בוטל', cancellation_reason=%s WHERE id=%s", (reason, oid), fetch=False)
                        msg = (f"היי {row['customer_name']}, ההזמנה בוטלה ❌\n"
                               + (f"סיבה: {reason}\n" if reason else "")
                               + "מצטערים! 🙏")
                        ok = notify(row['address'], msg)
                        st.session_state.cancel_open.pop(oid,None)
                        st.session_state.cancel_reason.pop(oid,None)
                        st.session_state.cancel_custom.pop(oid,None)
                        invalidate_orders()
                        st.error("❌ בוטל" + (" · הודעה נשלחה" if ok else " · הודעה נכשלה"))
                        time.sleep(1); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                with cp3:
                    st.markdown('<div data-btn="delete">', unsafe_allow_html=True)
                    if st.button("סגור", key=f"ccc_{oid}", use_container_width=True):
                        st.session_state.cancel_open.pop(oid,None); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<div class='div-line'></div>", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# TAB 2 — COMPLAINTS
# ──────────────────────────────────────────────
with t2:
    try:
        cdf = fetch_complaints()
        if cdf.empty:
            st.markdown('<div class="empty-state"><div class="icon">😊</div><h3>אין תלונות פתוחות!</h3></div>', unsafe_allow_html=True)
        else:
            for _, row in cdf.iterrows():
                cid = int(row['id'])
                t_str = row['created_at'].strftime('%H:%M  %d/%m/%Y')
                has_reply = bool(row.get('owner_reply',''))
                reply_html = f"<div class='reply-box'>💬 תשובתך: {row['owner_reply']}</div>" if has_reply else ""
                st.markdown(f"""
                    <div class='cc'>
                        <div class='stripe s-comp'></div>
                        <div style='display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px;margin-bottom:8px'>
                            <div class='cname'>⚠️ {row['customer_name']}</div>
                            <div style='font-size:12px;color:#5a2a2a'>{t_str}</div>
                        </div>
                        <div style='margin-bottom:8px'><span class='phone-pill'>📱 {row['phone']}</span></div>
                        <div class='cdesc'>{row['description']}</div>
                        {reply_html}
                    </div>
                """, unsafe_allow_html=True)
                ca1, ca2 = st.columns(2)
                with ca1:
                    st.markdown('<div data-btn="approve">', unsafe_allow_html=True)
                    if st.button("✅ סמן כטופל", key=f"cp_{cid}", use_container_width=True):
                        db_execute("UPDATE complaints SET status='טופל' WHERE id=%s", (cid,), fetch=False)
                        invalidate_complaints(); st.success("✔ נסגר"); time.sleep(.6); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                with ca2:
                    st.markdown('<div data-btn="reply">', unsafe_allow_html=True)
                    if st.button("💬 השב ללקוח", key=f"ro_{cid}", use_container_width=True):
                        st.session_state.reply_open[cid] = not st.session_state.reply_open.get(cid,False)
                    st.markdown('</div>', unsafe_allow_html=True)
                if st.session_state.reply_open.get(cid, False):
                    rt = st.text_area("תשובה", key=f"rt_{cid}", placeholder="כתוב תשובה שתישלח בוואטסאפ...", height=90, label_visibility="collapsed")
                    rs1, _ = st.columns([1, 3])
                    with rs1:
                        st.markdown('<div data-btn="reply">', unsafe_allow_html=True)
                        if st.button("📤 שלח", key=f"rs_{cid}", use_container_width=True):
                            if rt and rt.strip():
                                full = (f"שלום {row['customer_name']},\nבנוגע לפנייתך: \"{row['description']}\"\n\n{rt.strip()}\n\nבברכה, המכולת של הצדיק 🛒")
                                ok = notify(f"WA_ID:{row['phone']}", full)
                                if ok:
                                    db_execute("UPDATE complaints SET owner_reply=%s, replied_at=NOW() WHERE id=%s", (rt.strip(), cid), fetch=False)
                                    invalidate_complaints(); st.success("✅ נשלח!")
                                    st.session_state.reply_open[cid] = False; time.sleep(.6); st.rerun()
                                else: st.error("❌ שליחה נכשלה")
                            else: st.warning("כתוב תשובה")
                        st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("<div class='div-line'></div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"שגיאה: {e}")
        st.info("הרץ ב-DB: ALTER TABLE complaints ADD COLUMN IF NOT EXISTS owner_reply TEXT; ALTER TABLE complaints ADD COLUMN IF NOT EXISTS replied_at TIMESTAMP;")

# ──────────────────────────────────────────────
# TAB 3 — APPROVED (עם כתובת יעד + מחיקה עם אישור)
# ──────────────────────────────────────────────
with t3:
    adf = fetch_approved()
    if adf.empty:
        st.markdown('<div class="empty-state"><div class="icon">📋</div><h3>אין עדיין היסטוריה</h3></div>', unsafe_allow_html=True)
    else:
        srch3 = st.text_input("🔍", placeholder="חפש לקוח / מוצרים...", key="s3", label_visibility="collapsed")
        if srch3:
            adf = adf[adf['customer_name'].str.contains(srch3,case=False,na=False) |
                      adf['items'].str.contains(srch3,case=False,na=False)]

        for _, row in adf.iterrows():
            oid      = int(row['id'])
            otype    = str(row.get('order_type',''))
            is_pick  = 'איסוף' in otype
            stripe   = 's-pick' if is_pick else 's-del'
            badge    = "<span class='badge b-pick'>🛒 איסוף</span>" if is_pick else "<span class='badge b-del'>🛵 משלוח</span>"
            addr_raw = str(row.get('address',''))
            addr_d   = clean_address(addr_raw)
            appr_t   = row['approved_at'].strftime('%H:%M %d/%m') if pd.notna(row['approved_at']) else '—'
            del_key  = f"del_appr_{oid}"

            st.markdown(f"""
                <div class='oc-light'>
                    <div class='stripe {stripe}'></div>
                    <div style='display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:6px'>
                        <div>
                            <div class='onum-light'>#{oid} · {badge}</div>
                            <div class='oname-light'>{row['customer_name']}</div>
                        </div>
                        <div style='text-align:left'>
                            <div style='color:#6a8a70;font-size:11px;font-weight:600'>✅ אושר: {appr_t}</div>
                            <div style='color:#5a7a60;font-size:12px;margin-top:3px'>⏱ {row.get('delivery_time','—')}</div>
                        </div>
                    </div>
                    <div class='oitems-light'>🛍️ {row['items']}</div>
                    {'<div class="oaddr-light">📍 ' + addr_d + '</div>' if addr_d and addr_d not in ('nan','None','') else ''}
                </div>
            """, unsafe_allow_html=True)

            # כפתור מחיקה עם אישור
            confirming = st.session_state.get(del_key, False)
            if not confirming:
                dc1, dc2 = st.columns([6, 1])
                with dc2:
                    st.markdown('<div data-btn="delete">', unsafe_allow_html=True)
                    if st.button("🗑️", key=f"da_{oid}", use_container_width=True, help="מחק מהזיכרון"):
                        st.session_state[del_key] = True
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown(
                    "<div style='background:#1a0a0a;border:1px solid #6b1010;border-radius:10px;"
                    "padding:10px 16px;margin:4px 0;display:flex;align-items:center;gap:10px;flex-wrap:wrap'>"
                    "<span style='color:#f87171;font-size:13px;font-weight:700'>⚠️ למחוק הזמנה זו לצמיתות?</span>",
                    unsafe_allow_html=True
                )
                bc1, bc2, bc3 = st.columns([3, 2, 2])
                with bc1:
                    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                with bc2:
                    st.markdown('<div data-btn="cc">', unsafe_allow_html=True)
                    if st.button("✔ כן, מחק", key=f"dac_{oid}", use_container_width=True):
                        db_execute("DELETE FROM orders WHERE id=%s", (oid,), fetch=False)
                        st.session_state.pop(del_key, None)
                        invalidate_orders()
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                with bc3:
                    st.markdown('<div data-btn="delete">', unsafe_allow_html=True)
                    if st.button("✕ ביטול", key=f"dax_{oid}", use_container_width=True):
                        st.session_state.pop(del_key, None)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='div-line'></div>", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# TAB 4 — CANCELLED
# ──────────────────────────────────────────────
with t4:
    cdf2 = fetch_cancelled()
    if cdf2.empty:
        st.markdown('<div class="empty-state"><div class="icon">✨</div><h3>אין הזמנות מבוטלות</h3></div>', unsafe_allow_html=True)
    else:
        if 'cancellation_reason' in cdf2.columns:
            cdf2['cancellation_reason'] = cdf2['cancellation_reason'].fillna('לא צוינה סיבה').replace('','לא צוינה סיבה')
        st.dataframe(cdf2, use_container_width=True, hide_index=True, column_config={
            "id": st.column_config.NumberColumn("מס'",format="%d"),
            "customer_name":"לקוח","items":"מוצרים","cancellation_reason":"סיבת ביטול",
            "created_at": st.column_config.DatetimeColumn("תאריך",format="DD/MM HH:mm"),
        })

# ──────────────────────────────────────────────
# TAB 5 — PROMOTIONS
# ──────────────────────────────────────────────
with t5:
    st.markdown("<div style='font-size:15px;font-weight:700;color:#fcd34d;margin-bottom:14px'>🏷️ ניהול מבצעים</div>", unsafe_allow_html=True)
    with st.expander("➕ הוסף מבצע חדש", expanded=False):
        pa1, pa2 = st.columns([3, 2])
        with pa1: p_title = st.text_input("🏷️ שם המבצע", placeholder="10% הנחה על כל הירקות...", key="pt")
        with pa2: p_desc  = st.text_input("📝 תיאור (אופציונלי)", placeholder="פרטים נוספים...", key="pd")
        p_never = st.checkbox("♾️ ללא הגבלת זמן (NEVER ENDS)", key="pne", value=False)
        if not p_never:
            pb1, pb2 = st.columns(2)
            with pb1: p_start = st.date_input("📅 תאריך התחלה", value=date.today(), key="psd")
            with pb2: p_end   = st.date_input("📅 תאריך סיום",   value=date.today(), key="ped")
        else:
            p_start = p_end = None
        st.markdown('<div data-btn="promo-add">', unsafe_allow_html=True)
        if st.button("➕ פרסם מבצע", use_container_width=True, key="padd"):
            if p_title:
                if p_never:
                    db_execute("INSERT INTO promotions (title,description,active,never_ends,start_date,end_date) VALUES (%s,%s,TRUE,TRUE,NULL,NULL)",
                               (p_title, p_desc or None), fetch=False)
                else:
                    if p_end < p_start:
                        st.error("❌ תאריך סיום לא יכול להיות לפני תאריך ההתחלה")
                    else:
                        db_execute("INSERT INTO promotions (title,description,active,never_ends,start_date,end_date) VALUES (%s,%s,TRUE,FALSE,%s,%s)",
                                   (p_title, p_desc or None, p_start.isoformat(), p_end.isoformat()), fetch=False)
                invalidate_promotions()
                st.success(f"✅ המבצע '{p_title}' נוסף!")
                time.sleep(.6); st.rerun()
            else:
                st.error("חסר שם מבצע")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    promos = fetch_promotions()
    today_str = date.today().isoformat()
    if promos.empty:
        st.markdown('<div class="empty-state"><div class="icon">🏷️</div><h3>אין מבצעים. צור מבצע חדש!</h3></div>', unsafe_allow_html=True)
    else:
        for _, p in promos.iterrows():
            pid = int(p['id'])
            is_active  = bool(p['active'])
            never_ends = bool(p.get('never_ends', False))
            if never_ends:
                date_str   = "<span style='color:#b45309;font-size:12px'>♾️ ללא הגבלת זמן</span>"
                currently_on = is_active
            else:
                sd = str(p.get('start_date',''))[:10] if p.get('start_date') else '?'
                ed = str(p.get('end_date',''))[:10]   if p.get('end_date')   else '?'
                date_str   = f"<span style='color:#4a3a00;font-size:12px'>📅 {sd} → {ed}</span>"
                currently_on = is_active and sd <= today_str <= ed
            status_badge = (
                "<span class='badge b-promo'>🟢 פעיל</span>" if currently_on
                else "<span class='badge' style='background:#111;color:#3a4268;border:1px solid #1a1a1a'>⏸ לא פעיל</span>"
            )
            desc_html = f"<div class='pdesc'>{p['description']}</div>" if p.get('description') else ''
            st.markdown(f"""
                <div class='pc {"p-active" if currently_on else "p-inactive"}'>
                    <div class='stripe s-promo'></div>
                    <div style='display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px'>
                        <div class='pname'>🏷️ {p['title']} &nbsp; {status_badge}</div>
                        <div>{date_str}</div>
                    </div>
                    {desc_html}
                </div>
            """, unsafe_allow_html=True)
            pm1, pm2, pm3 = st.columns([2, 2, 1])
            with pm1:
                st.markdown('<div data-btn="promo-toggle">', unsafe_allow_html=True)
                if st.button("⏸ השבת" if is_active else "▶️ הפעל", key=f"ptog_{pid}", use_container_width=True):
                    db_execute("UPDATE promotions SET active=%s WHERE id=%s", (not is_active, pid), fetch=False)
                    invalidate_promotions(); st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            with pm2:
                if not never_ends:
                    new_end = st.date_input("📅 שנה תאריך סיום", key=f"pext_{pid}", label_visibility="collapsed")
                    st.markdown('<div data-btn="save">', unsafe_allow_html=True)
                    if st.button("💾 עדכן תאריך", key=f"pupd_{pid}", use_container_width=True):
                        db_execute("UPDATE promotions SET end_date=%s WHERE id=%s", (new_end.isoformat(), pid), fetch=False)
                        invalidate_promotions(); st.success("✅ עודכן!"); time.sleep(.4); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
            with pm3:
                st.markdown('<div data-btn="promo-del">', unsafe_allow_html=True)
                if st.button("🗑️", key=f"pdel_{pid}", use_container_width=True, help="מחק מבצע"):
                    db_execute("DELETE FROM promotions WHERE id=%s", (pid,), fetch=False)
                    invalidate_promotions(); st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("<div class='div-line'></div>", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# TAB 6 — INVENTORY + IMPORT
# ──────────────────────────────────────────────
with t6:
    sb1, sb2, sb3 = st.tabs(["📋 מוצרים", "➕ הוסף", "📂 יבא קובץ"])

    with sb1:
        ps = st.text_input("🔍", placeholder="חפש מוצר...", key="ps", label_visibility="collapsed")
        pf = fetch_products(ps)
        if pf.empty:
            st.markdown('<div class="empty-state"><div class="icon">📦</div><h3>לא נמצאו מוצרים</h3></div>', unsafe_allow_html=True)
        else:
            # כותרת
            hc1,hc2,hc3,hc4,hc5 = st.columns([3,1.5,1.5,.8,.8])
            with hc1: st.markdown("<div style='font-size:11px;font-weight:700;color:#2a3058;padding:4px 2px'>שם המוצר</div>", unsafe_allow_html=True)
            with hc2: st.markdown("<div style='font-size:11px;font-weight:700;color:#2a3058;padding:4px 2px'>מחיר ₪</div>", unsafe_allow_html=True)
            with hc3: st.markdown("<div style='font-size:11px;font-weight:700;color:#2a3058;padding:4px 2px'>מלאי</div>", unsafe_allow_html=True)
            for _, p in pf.iterrows():
                pid = int(p['id'])
                c1,c2,c3,c4,c5 = st.columns([3,1.5,1.5,.8,.8])
                with c1: nn  = st.text_input("שם",  value=p['name'],        key=f"pn_{pid}", label_visibility="collapsed")
                with c2: np_ = st.number_input("₪",  value=float(p['price']),min_value=0.0,step=0.5,key=f"pp_{pid}",label_visibility="collapsed",format="%.2f")
                with c3: ns  = st.number_input("📦", value=int(p['stock']),  min_value=0,  step=1,  key=f"ps_{pid}", label_visibility="collapsed")
                with c4:
                    st.markdown('<div data-btn="save">', unsafe_allow_html=True)
                    if st.button("💾", key=f"sv_{pid}", use_container_width=True):
                        db_execute("UPDATE products SET name=%s,price=%s,stock=%s WHERE id=%s", (nn,np_,ns,pid), fetch=False)
                        invalidate_products(); st.success("✅"); time.sleep(.3); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                with c5:
                    st.markdown('<div data-btn="delete">', unsafe_allow_html=True)
                    if st.button("🗑️", key=f"dp_{pid}", use_container_width=True):
                        db_execute("DELETE FROM products WHERE id=%s", (pid,), fetch=False)
                        invalidate_products(); st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    with sb2:
        with st.form("add_p", clear_on_submit=True):
            a1,a2,a3 = st.columns([3,2,2])
            with a1: pname  = st.text_input("🏷️ שם", placeholder="לחם אחיד...")
            with a2: pprice = st.number_input("💰 מחיר (₪)", min_value=0.0, step=0.5, format="%.2f")
            with a3: pstock = st.number_input("📦 כמות", min_value=0, step=1, value=10)
            st.markdown('<div data-btn="approve">', unsafe_allow_html=True)
            if st.form_submit_button("➕ הוסף", use_container_width=True):
                if pname and pprice > 0:
                    db_execute("INSERT INTO products (name,price,stock) VALUES (%s,%s,%s)", (pname,pprice,pstock), fetch=False)
                    invalidate_products(); st.success(f"✅ '{pname}' נוסף!"); time.sleep(.6); st.rerun()
                else:
                    st.error("חסר שם/מחיר")
            st.markdown('</div>', unsafe_allow_html=True)

    with sb3:
        st.markdown("""
            <div style='background:#080b18;border:1px solid #1a1e30;border-radius:12px;padding:16px 20px;margin-bottom:16px'>
                <div style='font-size:15px;font-weight:700;color:#c8cfe0;margin-bottom:8px'>📂 יבא מוצרים מקובץ</div>
                <div style='font-size:13px;color:#3a4268;line-height:1.7'>
                    • תומך בקבצי <strong style='color:#7a84a0'>Excel (.xlsx/.xls)</strong> ו-<strong style='color:#7a84a0'>CSV (.csv)</strong><br>
                    • הקובץ חייב לכלול עמודה <strong style='color:#38bdf8'>name / שם</strong> ועמודה <strong style='color:#38bdf8'>price / מחיר</strong><br>
                    • עמודת <strong style='color:#34d399'>stock / מלאי / כמות</strong> — אופציונלית (ברירת מחדל: 0)<br>
                    • מוצר קיים (לפי שם) → מחיר ומלאי יתעדכנו. מוצר חדש → ייווסף.<br>
                    • <strong style='color:#f87171'>לא נמחק</strong> אף מוצר קיים ב-DB
                </div>
            </div>
        """, unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "בחר קובץ Excel או CSV",
            type=["xlsx","xls","csv"],
            key="prod_import",
            label_visibility="collapsed"
        )

        if uploaded:
            try:
                fname = uploaded.name.lower()
                if fname.endswith('.csv'):
                    df_raw = _read_csv_hebrew(uploaded)
                elif fname.endswith('.xls'):
                    uploaded.seek(0)
                    df_raw = pd.read_excel(uploaded, engine='xlrd')
                else:  # .xlsx
                    uploaded.seek(0)
                    df_raw = pd.read_excel(uploaded, engine='openpyxl')

                # הצג תצוגה מקדימה
                col_map_preview = _map_columns(df_raw.columns.tolist())
                cols_found = []
                if 'name'  in col_map_preview: cols_found.append(f"✅ שם: <b>{col_map_preview['name']}</b>")
                if 'price' in col_map_preview: cols_found.append(f"✅ מחיר: <b>{col_map_preview['price']}</b>")
                if 'stock' in col_map_preview: cols_found.append(f"✅ מלאי: <b>{col_map_preview['stock']}</b>")
                missing = []
                if 'name'  not in col_map_preview: missing.append("שם/name")
                if 'price' not in col_map_preview: missing.append("מחיר/price")

                st.markdown(
                    f"<div style='background:#080b18;border:1px solid #1a1e30;border-radius:10px;padding:12px 16px;margin-bottom:12px;font-size:13px;line-height:1.8'>"
                    f"<b style='color:#c8cfe0'>נמצאו {len(df_raw)} שורות</b> &nbsp;·&nbsp; "
                    + " &nbsp;·&nbsp; ".join(f"<span style='color:#7a84a0'>{c}</span>" for c in cols_found)
                    + ("" if not missing else f"<br><span style='color:#f87171'>⚠️ חסרות: {', '.join(missing)}</span>")
                    + "</div>",
                    unsafe_allow_html=True
                )
                st.dataframe(df_raw.head(8), use_container_width=True, hide_index=True)

                if missing:
                    st.error(f"❌ לא ניתן לייבא — חסרות עמודות: {', '.join(missing)}")
                else:
                    st.markdown('<div data-btn="import">', unsafe_allow_html=True)
                    if st.button(f"📥 יבא {len(df_raw)} מוצרים לDB", use_container_width=True, key="do_import"):
                        with st.spinner("מייבא מוצרים..."):
                            ins, upd, errs = import_products_from_df(df_raw.copy())
                        invalidate_products()
                        if ins or upd:
                            st.success(f"✅ הושלם! נוספו: {ins} מוצרים חדשים · עודכנו: {upd} מוצרים קיימים")
                        elif not errs:
                            st.info("ℹ️ לא בוצעו שינויים — כל המוצרים כבר עדכניים")
                        if errs:
                            st.warning(f"⚠️ {len(errs)} שגיאות בשורות:")
                            for e in errs[:15]:
                                st.caption(f"  {e}")
                    st.markdown('</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"❌ לא ניתן לקרוא את הקובץ: {e}")
                st.caption("💡 טיפ: שמור את הקובץ כ-Excel (.xlsx) — זה הפורמט הכי אמין לעברית")

st.markdown("<div style='text-align:center;padding:22px 0 4px;font-size:11px;color:#0e1224'>המכולת של הצדיק · v7.0</div>", unsafe_allow_html=True)
