import streamlit as st
import psycopg2
import pandas as pd
import os
import requests
import time
from datetime import datetime

# ══════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════
st.set_page_config(
    page_title="המכולת של הצדיק",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ══════════════════════════════════════════════
# ENV
# ══════════════════════════════════════════════
DB_URL          = os.environ.get("DB_URL")
BOT_URL         = os.environ.get("BOT_URL", "https://minimarket-ocfq.onrender.com")
INTERNAL_SECRET = os.environ.get("INTERNAL_SECRET", "123")
ADMIN_PASSWORD  = os.environ.get("ADMIN_PASSWORD", "12345")

# ══════════════════════════════════════════════
# GLOBAL STYLES
# ══════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rubik:wght@300;400;500;600;700;800;900&family=Rubik+Mono+One&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"] {
    font-family: 'Rubik', sans-serif !important;
    direction: rtl !important;
}

/* ── App background ── */
.stApp {
    background: #0b0e1a !important;
    color: #dde1f0 !important;
    min-height: 100vh;
}

/* ── Remove streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden !important; }
.block-container {
    padding: 1.5rem 1.5rem 4rem !important;
    max-width: 100% !important;
}
section[data-testid="stSidebar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
div[data-testid="stToolbar"] { display: none !important; }

/* ── Keep-alive (no session lock) ── */
.stApp iframe { display: none; }

/* ══ STAT CARDS ══ */
.stats-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 22px;
}
@media (max-width: 900px) { .stats-row { grid-template-columns: repeat(2,1fr); } }
@media (max-width: 500px) { .stats-row { grid-template-columns: 1fr 1fr; gap:10px; } }

.stat-card {
    border-radius: 18px;
    padding: 20px 18px 16px;
    position: relative;
    overflow: hidden;
    cursor: default;
    transition: transform .2s, box-shadow .2s;
    border: 1px solid rgba(255,255,255,.07);
}
.stat-card:hover { transform: translateY(-3px); box-shadow: 0 12px 40px rgba(0,0,0,.45); }
.stat-card::after {
    content: attr(data-icon);
    position: absolute;
    right: 14px; bottom: 8px;
    font-size: 52px;
    opacity: .12;
    line-height: 1;
    pointer-events: none;
}
.stat-card .num {
    font-size: clamp(32px, 5vw, 46px);
    font-weight: 900;
    line-height: 1;
    font-family: 'Rubik Mono One', monospace;
}
.stat-card .lbl {
    font-size: 12px;
    font-weight: 600;
    letter-spacing: .6px;
    text-transform: uppercase;
    margin-top: 6px;
    opacity: .7;
}
.sc-pending  { background: linear-gradient(135deg,#1c1730 0%,#231e42 100%); }
.sc-pending  .num { color: #a78bfa; }
.sc-delivery { background: linear-gradient(135deg,#0d1f34 0%,#112840 100%); }
.sc-delivery .num { color: #38bdf8; }
.sc-pickup   { background: linear-gradient(135deg,#0c2217 0%,#103020 100%); }
.sc-pickup   .num { color: #34d399; }
.sc-complaint{ background: linear-gradient(135deg,#270d0d 0%,#311010 100%); }
.sc-complaint .num { color: #f87171; }

/* ══ ALERT BANNER ══ */
.alert-banner {
    background: linear-gradient(90deg, #7c3aed 0%, #4f46e5 50%, #0ea5e9 100%);
    border-radius: 14px;
    padding: 14px 22px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: clamp(14px, 2.5vw, 17px);
    font-weight: 700;
    color: #fff;
    animation: breathe 2.5s ease-in-out infinite;
    box-shadow: 0 4px 30px rgba(124,58,237,.35);
}
@keyframes breathe {
    0%,100% { box-shadow: 0 4px 30px rgba(124,58,237,.35); }
    50%      { box-shadow: 0 4px 50px rgba(14,165,233,.55); }
}
.alert-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    background: #fff;
    animation: blink 1s step-start infinite;
    flex-shrink: 0;
}
@keyframes blink { 50% { opacity: 0; } }

/* ══ ORDER CARD ══ */
.order-card {
    background: #121520;
    border: 1px solid #1e2235;
    border-radius: 16px;
    padding: clamp(14px,2vw,22px) clamp(16px,2.5vw,26px);
    margin-bottom: 6px;
    position: relative;
    transition: border-color .2s, box-shadow .2s;
}
.order-card:hover { border-color: #2e3660; box-shadow: 0 6px 28px rgba(0,0,0,.4); }
.order-card .stripe {
    position: absolute;
    top: 0; right: 0;
    width: 5px; height: 100%;
    border-radius: 0 16px 16px 0;
}
.stripe-delivery { background: linear-gradient(180deg,#38bdf8,#0ea5e9); }
.stripe-pickup   { background: linear-gradient(180deg,#34d399,#10b981); }
.stripe-complaint{ background: linear-gradient(180deg,#f87171,#ef4444); }

.order-num   { font-size: 11px; font-weight: 600; color: #5a6180; letter-spacing: 1px; text-transform: uppercase; }
.order-name  { font-size: clamp(18px,3vw,24px); font-weight: 800; color: #f1f3ff; margin: 3px 0 10px; }
.order-items { background: #0d1018; border: 1px solid #1c2030; border-radius: 10px; padding: 10px 14px; font-size: clamp(13px,2vw,15px); color: #8892b0; margin-bottom: 12px; line-height: 1.5; }
.order-meta  { display: flex; gap: 18px; flex-wrap: wrap; }
.order-meta span { font-size: 13px; color: #515a75; display: flex; align-items: center; gap: 5px; }

.badge {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 3px 10px; border-radius: 20px;
    font-size: 11px; font-weight: 700; letter-spacing: .4px;
}
.b-delivery { background: #0c2236; color: #38bdf8; border: 1px solid #0e4a75; }
.b-pickup   { background: #0a2318; color: #34d399; border: 1px solid #0d5a38; }
.b-new      { background: #2d1f00; color: #fbbf24; border: 1px solid #6b4a00; animation: newpulse 2s ease-in-out infinite; }
@keyframes newpulse { 0%,100%{opacity:1}50%{opacity:.6} }

/* ══ COMPLAINT CARD ══ */
.complaint-card {
    background: #110a0a;
    border: 1px solid #3b1010;
    border-radius: 16px;
    padding: 20px 22px;
    margin-bottom: 6px;
    position: relative;
}
.complaint-card::before {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 5px; height: 100%;
    background: linear-gradient(180deg,#f87171,#dc2626);
    border-radius: 0 16px 16px 0;
}
.cname { font-size: 20px; font-weight: 800; color: #fca5a5; margin-bottom: 6px; }
.cdesc { font-size: 14px; color: #b0808080; color: #9ca3af; line-height: 1.6; }

/* ══ CANCEL PANEL ══ */
.cancel-panel {
    background: #0f0a0a;
    border: 1px dashed #7f1d1d;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 8px 0 4px;
}

/* ══ BUTTONS ══ */
.stButton > button {
    font-family: 'Rubik', sans-serif !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    border: none !important;
    padding: 10px 14px !important;
    font-size: clamp(12px, 1.8vw, 14px) !important;
    width: 100% !important;
    transition: transform .15s, box-shadow .15s, filter .15s !important;
    cursor: pointer !important;
    white-space: nowrap !important;
}
.stButton > button:hover  { transform: translateY(-1px) !important; filter: brightness(1.12) !important; }
.stButton > button:active { transform: translateY(0px)  !important; filter: brightness(.95) !important; }

div[data-btn="approve"] .stButton > button {
    background: linear-gradient(135deg,#059669,#10b981) !important;
    color: #fff !important;
    box-shadow: 0 3px 14px rgba(16,185,129,.3) !important;
}
div[data-btn="cancel"] .stButton > button {
    background: linear-gradient(135deg,#b91c1c,#ef4444) !important;
    color: #fff !important;
    box-shadow: 0 3px 14px rgba(239,68,68,.25) !important;
}
div[data-btn="confirm-cancel"] .stButton > button {
    background: linear-gradient(135deg,#7f1d1d,#dc2626) !important;
    color: #fff !important;
}
div[data-btn="delete"] .stButton > button {
    background: #151822 !important;
    color: #475069 !important;
    border: 1px solid #1e2235 !important;
    box-shadow: none !important;
}
div[data-btn="delete"] .stButton > button:hover {
    background: #1a0808 !important;
    color: #f87171 !important;
    border-color: #7f1d1d !important;
}
div[data-btn="refresh"] .stButton > button {
    background: linear-gradient(135deg,#1d4ed8,#3b82f6) !important;
    color: #fff !important;
    box-shadow: 0 3px 14px rgba(59,130,246,.3) !important;
}
div[data-btn="save"] .stButton > button {
    background: linear-gradient(135deg,#0369a1,#0ea5e9) !important;
    color: #fff !important;
}
div[data-btn="logout"] .stButton > button {
    background: #151822 !important;
    color: #5a6180 !important;
    border: 1px solid #1e2235 !important;
}

/* ══ INPUTS ══ */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div > div {
    background: #0d1018 !important;
    color: #dde1f0 !important;
    border: 1px solid #1e2235 !important;
    border-radius: 10px !important;
    font-family: 'Rubik', sans-serif !important;
    font-size: 14px !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,.15) !important;
    outline: none !important;
}
.stTextInput > label, .stNumberInput > label,
.stSelectbox > label { color: #5a6180 !important; font-size: 12px !important; font-weight: 600 !important; letter-spacing: .4px !important; }

/* ══ TABS ══ */
.stTabs [data-baseweb="tab-list"] {
    background: #0d1018 !important;
    border-radius: 12px !important;
    padding: 5px !important;
    gap: 3px !important;
    border: 1px solid #1e2235 !important;
    flex-wrap: wrap !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #5a6180 !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-size: clamp(11px, 1.8vw, 14px) !important;
    padding: 9px 16px !important;
    border: none !important;
    transition: all .2s !important;
    white-space: nowrap !important;
}
.stTabs [data-baseweb="tab"]:hover { background: #151822 !important; color: #a0aac0 !important; }
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg,#1d4ed8,#4f46e5) !important;
    color: #fff !important;
    box-shadow: 0 2px 12px rgba(79,70,229,.35) !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 18px !important; }

/* ══ DATAFRAME ══ */
.stDataFrame { background: #0d1018 !important; border-radius: 12px !important; overflow: hidden; border: 1px solid #1e2235 !important; }
.stDataFrame thead th { background: #0b0e1a !important; color: #5a6180 !important; font-size: 12px !important; font-weight: 700 !important; letter-spacing: .5px !important; }
.stDataFrame tbody tr:hover td { background: #151822 !important; }

/* ══ EMPTY STATE ══ */
.empty-state { text-align: center; padding: 60px 20px; color: #2e3450; }
.empty-state .icon { font-size: 56px; margin-bottom: 14px; }
.empty-state h3 { color: #3e4870 !important; font-size: 18px !important; font-weight: 700 !important; }

/* ══ SECTION HEADER ══ */
.section-hdr {
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 16px;
}
.section-hdr h3 {
    font-size: clamp(15px,2.5vw,19px) !important;
    font-weight: 800 !important;
    color: #c8cfe8 !important;
    margin: 0 !important;
}
.section-hdr .pill {
    background: #1e2235; color: #5a6180;
    border-radius: 20px; padding: 2px 10px;
    font-size: 12px; font-weight: 700;
}

/* ══ LOGIN ══ */
.login-wrap { min-height:80vh; display:flex; align-items:center; justify-content:center; }
.login-card {
    background: #121520;
    border: 1px solid #1e2235;
    border-radius: 24px;
    padding: clamp(32px,5vw,52px);
    width: min(380px, 90vw);
    text-align: center;
    box-shadow: 0 24px 80px rgba(0,0,0,.6);
}
.login-icon { font-size: 56px; margin-bottom: 12px; }
.login-card h2 { font-size: 26px !important; font-weight: 900 !important; color: #f1f3ff !important; margin-bottom: 6px; }
.login-card p  { color: #3e4870; font-size: 14px; margin-bottom: 28px; }

/* ══ DIVIDER ══ */
.div-line { height: 1px; background: #1e2235; margin: 10px 0 16px; }

/* ══ SUCCESS / ERROR TOAST ══ */
.stSuccess, .stError, .stWarning, .stInfo { border-radius: 10px !important; font-size: 14px !important; }

/* ══ SCROLLBAR ══ */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0b0e1a; }
::-webkit-scrollbar-thumb { background: #1e2235; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #2e3450; }

/* ══ RESPONSIVE HELPERS ══ */
@media (max-width: 768px) {
    .block-container { padding: 1rem 0.75rem 3rem !important; }
    .order-meta { gap: 10px; }
}
</style>

<!-- SOUNDS via Web Audio API -->
<script>
const _AC = window.AudioContext || window.webkitAudioContext;
let _ac = null;
function _ctx(){ if(!_ac || _ac.state==='closed') _ac = new _AC(); if(_ac.state==='suspended') _ac.resume(); return _ac; }

function playDelivery(){
    const c=_ctx(); const t=c.currentTime;
    [[0,440],[.13,560],[.26,680]].forEach(([d,f])=>{
        const o=c.createOscillator(), g=c.createGain();
        o.connect(g); g.connect(c.destination);
        o.frequency.value=f; o.type='sine';
        g.gain.setValueAtTime(0,t+d);
        g.gain.linearRampToValueAtTime(.38,t+d+.04);
        g.gain.exponentialRampToValueAtTime(.001,t+d+.22);
        o.start(t+d); o.stop(t+d+.25);
    });
}
function playPickup(){
    const c=_ctx(); const t=c.currentTime;
    [0,.22].forEach(d=>{
        const o=c.createOscillator(), g=c.createGain();
        o.connect(g); g.connect(c.destination);
        o.frequency.value=880; o.type='triangle';
        g.gain.setValueAtTime(0,t+d);
        g.gain.linearRampToValueAtTime(.3,t+d+.03);
        g.gain.exponentialRampToValueAtTime(.001,t+d+.18);
        o.start(t+d); o.stop(t+d+.2);
    });
}
function playComplaint(){
    const c=_ctx(); const t=c.currentTime;
    const o=c.createOscillator(), g=c.createGain();
    o.connect(g); g.connect(c.destination);
    o.frequency.setValueAtTime(260,t);
    o.frequency.linearRampToValueAtTime(180,t+.55);
    o.type='sawtooth';
    g.gain.setValueAtTime(.22,t);
    g.gain.linearRampToValueAtTime(0,t+.6);
    o.start(t); o.stop(t+.65);
}
function playNewOrder(){
    const c=_ctx(); const t=c.currentTime;
    [523,659,784,1047].forEach((f,i)=>{
        const o=c.createOscillator(), g=c.createGain();
        o.connect(g); g.connect(c.destination);
        o.frequency.value=f; o.type='sine';
        const d=t+i*.11;
        g.gain.setValueAtTime(0,d);
        g.gain.linearRampToValueAtTime(.32,d+.03);
        g.gain.exponentialRampToValueAtTime(.001,d+.22);
        o.start(d); o.stop(d+.25);
    });
}

// Watch hidden data attrs for changes
let _prev={orders:-1,complaints:-1,sound:''};
function _watch(){
    const oel=document.getElementById('_oc'); const cel=document.getElementById('_cc'); const sel=document.getElementById('_st');
    if(!oel||!cel||!sel) return;
    const o=parseInt(oel.dataset.v||-1); const cmp=parseInt(cel.dataset.v||-1); const snd=sel.dataset.v||'';
    if(snd && snd!==_prev.sound){ _prev.sound=snd;
        if(snd==='delivery')   playDelivery();
        else if(snd==='pickup')   playPickup();
        else if(snd==='complaint') playComplaint();
        else if(snd==='new_order') playNewOrder();
    }
    if(_prev.orders>=0 && o>_prev.orders) playNewOrder();
    if(_prev.complaints>=0 && cmp>_prev.complaints) playComplaint();
    _prev.orders=o; _prev.complaints=cmp;
}
setInterval(_watch,900);

// Anti-session-lock keepalive
setInterval(()=>{ try{fetch(window.location.href,{method:'HEAD'})}catch(e){} },150000);
</script>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# DB HELPERS
# ══════════════════════════════════════════════
def db():
    return psycopg2.connect(DB_URL)

def q(sql, params=(), fetch=True):
    conn = db()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        if fetch:
            return cur.fetchall()
        conn.commit()
        return True
    except Exception as e:
        if not fetch:
            conn.rollback()
        st.error(f"DB שגיאה: {e}")
        return [] if fetch else False
    finally:
        conn.close()

def read_df(sql):
    conn = db()
    try:
        return pd.read_sql(sql, conn)
    except:
        return pd.DataFrame()
    finally:
        conn.close()

def extract_phone(addr):
    try:
        if "WA_ID:" in str(addr):
            return str(addr).split("WA_ID:")[-1].strip()
        c = str(addr).replace("-","").strip()
        return ("972" + c[1:]) if c.startswith("0") else c
    except:
        return None

def notify(addr, msg):
    phone = extract_phone(addr)
    if not phone:
        return False
    try:
        r = requests.post(
            f"{BOT_URL}/send_update",
            json={"phone": phone, "message": msg},
            headers={"X-Internal-Secret": INTERNAL_SECRET},
            timeout=10
        )
        return r.status_code == 200
    except:
        return False

def get_counts():
    rows = q("SELECT status, order_type FROM orders WHERE status IN ('ממתין לאישור')")
    pending   = len(rows)
    deliveries = sum(1 for r in rows if 'איסוף' not in str(r[1]).lower())
    pickups    = pending - deliveries
    comp = q("SELECT COUNT(*) FROM complaints WHERE status='פתוח'")
    complaints = comp[0][0] if comp else 0
    return pending, deliveries, pickups, complaints

# ══════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════
for k, v in {
    'logged_in': False,
    'prev_pending': -1,
    'prev_complaints': -1,
    'sound': '',
    'cancel_open': {},
    'cancel_reason': {},
    'cancel_custom': {},
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════
# LOGIN
# ══════════════════════════════════════════════
if not st.session_state.logged_in:
    st.markdown("<div class='login-wrap'>", unsafe_allow_html=True)
    _, col, _ = st.columns([1,1.4,1])
    with col:
        st.markdown("""
            <div class='login-card'>
                <div class='login-icon'>🛒</div>
                <h2>המכולת של הצדיק</h2>
                <p>ממשק ניהול · כניסת מנהל</p>
            </div>
        """, unsafe_allow_html=True)
        pwd = st.text_input("סיסמה", type="password", placeholder="הכנס סיסמה...", label_visibility="collapsed")
        st.markdown('<div data-btn="refresh">', unsafe_allow_html=True)
        if st.button("כניסה →", use_container_width=True):
            if pwd == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("❌ סיסמה שגויה")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════
# MAIN — COUNTS + SOUNDS
# ══════════════════════════════════════════════
pending, deliveries, pickups, complaints = get_counts()

sound = ''
if st.session_state.prev_pending >= 0 and pending > st.session_state.prev_pending:
    sound = 'new_order'
if st.session_state.prev_complaints >= 0 and complaints > st.session_state.prev_complaints:
    sound = 'complaint'
if st.session_state.sound:
    sound = st.session_state.sound
    st.session_state.sound = ''

st.session_state.prev_pending    = pending
st.session_state.prev_complaints = complaints

# Hidden data for JS
st.markdown(f"""
<div id='_oc' data-v='{pending}'    style='display:none'></div>
<div id='_cc' data-v='{complaints}' style='display:none'></div>
<div id='_st' data-v='{sound}'      style='display:none'></div>
""", unsafe_allow_html=True)

# ══ HEADER ══
h_left, h_right = st.columns([5, 1])
with h_left:
    now = datetime.now().strftime("%A %d/%m/%Y · %H:%M")
    st.markdown(f"""
        <div style='margin-bottom:18px'>
            <div style='font-size:clamp(20px,4vw,28px); font-weight:900; color:#f1f3ff; letter-spacing:-.5px'>
                🛒 המכולת של הצדיק
            </div>
            <div style='font-size:13px; color:#3e4870; margin-top:3px'>{now}</div>
        </div>
    """, unsafe_allow_html=True)
with h_right:
    r1, r2 = st.columns(2)
    with r1:
        st.markdown('<div data-btn="refresh">', unsafe_allow_html=True)
        if st.button("🔄", help="רענן", key="hrefresh"):
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with r2:
        st.markdown('<div data-btn="logout">', unsafe_allow_html=True)
        if st.button("🚪", help="התנתק", key="hlogout"):
            st.session_state.logged_in = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ══ STAT CARDS ══
st.markdown(f"""
<div class='stats-row'>
  <div class='stat-card sc-pending'  data-icon='📦'>
    <div class='num'>{pending}</div><div class='lbl'>ממתינות לטיפול</div>
  </div>
  <div class='stat-card sc-delivery' data-icon='🛵'>
    <div class='num'>{deliveries}</div><div class='lbl'>משלוחים</div>
  </div>
  <div class='stat-card sc-pickup'   data-icon='🛒'>
    <div class='num'>{pickups}</div><div class='lbl'>איסופים</div>
  </div>
  <div class='stat-card sc-complaint' data-icon='⚠️'>
    <div class='num'>{complaints}</div><div class='lbl'>תלונות פתוחות</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ══ ALERT ══
if pending > 0:
    st.markdown(f"""
        <div class='alert-banner'>
            <div class='alert-dot'></div>
            יש {pending} הזמנה{'ות' if pending>1 else ''} שמחכ{'ות' if pending>1 else 'ה'} לאישור שלך!
        </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════
t1, t2, t3, t4, t5 = st.tabs([
    f"📦 לטיפול ({pending})",
    f"⚠️ תלונות ({complaints})",
    "✅ אושרו",
    "❌ בוטלו",
    "🏪 מלאי",
])

# ══════════════════════════════════════════════
# TAB 1 — ORDERS TO HANDLE
# ══════════════════════════════════════════════
with t1:
    srch = st.text_input("🔍 חיפוש לפי שם / מוצר / מספר", placeholder="הקלד...", key="s1", label_visibility="collapsed")

    conn = db()
    df = pd.read_sql(
        "SELECT id, customer_name, items, address, order_type, created_at FROM orders WHERE status='ממתין לאישור' ORDER BY created_at DESC",
        conn
    )
    conn.close()

    if srch:
        m = (
            df['customer_name'].str.contains(srch, case=False, na=False) |
            df['items'].str.contains(srch, case=False, na=False) |
            df['id'].astype(str).str.contains(srch)
        )
        df = df[m]

    if df.empty:
        st.markdown("""
            <div class='empty-state'>
                <div class='icon'>🎉</div>
                <h3>כל ההזמנות טופלו — עבודה מצוינת!</h3>
            </div>
        """, unsafe_allow_html=True)
    else:
        for _, row in df.iterrows():
            oid       = int(row['id'])
            otype     = str(row.get('order_type', 'משלוח'))
            is_pickup = 'איסוף' in otype
            stripe    = 'stripe-pickup' if is_pickup else 'stripe-delivery'
            badge     = f"<span class='badge b-pickup'>🛒 איסוף</span>" if is_pickup else f"<span class='badge b-delivery'>🛵 משלוח</span>"
            addr_clean = str(row['address']).split('|')[0].strip()
            created    = row['created_at'].strftime('%H:%M  %d/%m/%Y')

            st.markdown(f"""
                <div class='order-card'>
                    <div class='stripe {stripe}'></div>
                    <div style='display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:6px'>
                        <div>
                            <div class='order-num'>הזמנה #{oid} &nbsp;·&nbsp; {badge} &nbsp;<span class='badge b-new'>חדש</span></div>
                            <div class='order-name'>{row['customer_name']}</div>
                        </div>
                        <div style='color:#3e4870; font-size:12px; padding-top:4px'>{created}</div>
                    </div>
                    <div class='order-items'>🛍️ {row['items']}</div>
                    <div class='order-meta'>
                        <span>📍 {addr_clean}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # ── Action row ──
            c_time, c_app, c_can, c_del = st.columns([2.4, 2.2, 2.2, 0.7])

            with c_time:
                placeholder = "מוכן לאיסוף בעוד..." if is_pickup else "זמן הגעה משוער..."
                time_val = st.text_input("⏱", value="20 דקות", key=f"tv_{oid}",
                                         label_visibility="collapsed", placeholder=placeholder)

            with c_app:
                st.markdown('<div data-btn="approve">', unsafe_allow_html=True)
                if st.button("✅ אשר ושלח ללקוח", key=f"ap_{oid}", use_container_width=True):
                    q(
                        "UPDATE orders SET status='אושר', delivery_time=%s, approved_at=NOW() WHERE id=%s",
                        (time_val, oid), fetch=False
                    )
                    msg = (
                        f"היי {row['customer_name']}! ✅ ההזמנה אושרה.\n"
                        f"{'🛒 מוכן לאיסוף בעוד: ' if is_pickup else '🛵 זמן הגעה: '}{time_val}\n"
                        f"🛍️ {row['items']}\nתודה! 🙏"
                    )
                    ok = notify(row['address'], msg)
                    snd = 'pickup' if is_pickup else 'delivery'
                    st.session_state.sound = snd
                    if ok:
                        st.success("✅ אושר ונשלחה הודעה")
                    else:
                        st.warning("⚠️ אושר, אבל ההודעה לא נשלחה")
                    time.sleep(1)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            with c_can:
                st.markdown('<div data-btn="cancel">', unsafe_allow_html=True)
                if st.button("❌ בטל הזמנה", key=f"cbt_{oid}", use_container_width=True):
                    cur_state = st.session_state.cancel_open.get(oid, False)
                    st.session_state.cancel_open[oid] = not cur_state
                st.markdown('</div>', unsafe_allow_html=True)

            with c_del:
                st.markdown('<div data-btn="delete">', unsafe_allow_html=True)
                if st.button("🗑️", key=f"dl_{oid}", use_container_width=True, help="מחק"):
                    q("DELETE FROM orders WHERE id=%s", (oid,), fetch=False)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            # ── CANCEL PANEL ─────────────────────────────────────────────
            # הבאג היה כאן: st.rerun() נקרא לפני notify(), ו-final_reason
            # לא נשמר נכון. הפתרון: שומרים הכל ב-session_state ורק אז מבצעים.
            # ─────────────────────────────────────────────────────────────
            if st.session_state.cancel_open.get(oid, False):
                st.markdown("<div class='cancel-panel'>", unsafe_allow_html=True)
                st.markdown("<div style='font-size:14px; font-weight:700; color:#f87171; margin-bottom:10px'>🔴 ביטול הזמנה</div>", unsafe_allow_html=True)

                reason_options = ["חוסר במלאי", "כתובת שגויה", "לקוח לא זמין", "מחוץ לאזור משלוח", "אחר"]
                cp1, cp2 = st.columns([3, 1])

                with cp1:
                    chosen = st.selectbox(
                        "סיבת ביטול",
                        reason_options,
                        key=f"rs_{oid}",
                        label_visibility="collapsed"
                    )
                    # שמירה בsession_state מיד
                    st.session_state.cancel_reason[oid] = chosen

                    if chosen == "אחר":
                        custom = st.text_input(
                            "פרט סיבה",
                            key=f"rc_{oid}",
                            placeholder="כתוב סיבה קצרה...",
                            label_visibility="collapsed"
                        )
                        st.session_state.cancel_custom[oid] = custom

                with cp2:
                    st.markdown('<div data-btn="confirm-cancel">', unsafe_allow_html=True)
                    if st.button("אשר ביטול", key=f"ccf_{oid}", use_container_width=True):
                        # קריאת הסיבה מה-session_state — לא מהwidget ישירות
                        final_reason = st.session_state.cancel_reason.get(oid, "לא צוינה סיבה")
                        if final_reason == "אחר":
                            final_reason = st.session_state.cancel_custom.get(oid, "") or "לא צוינה סיבה"

                        # 1. עדכון DB
                        q(
                            "UPDATE orders SET status='בוטל', cancellation_reason=%s WHERE id=%s",
                            (final_reason, oid), fetch=False
                        )

                        # 2. שליחת הודעה ללקוח — חייב לפני rerun!
                        msg = (
                            f"היי {row['customer_name']}, ההזמנה שלך בוטלה ❌\n"
                            f"סיבה: {final_reason}\n"
                            f"מצטערים מאוד על אי הנוחות 🙏"
                        )
                        ok = notify(row['address'], msg)

                        # 3. ניקוי state
                        st.session_state.cancel_open.pop(oid, None)
                        st.session_state.cancel_reason.pop(oid, None)
                        st.session_state.cancel_custom.pop(oid, None)

                        if ok:
                            st.error(f"❌ הזמנה #{oid} בוטלה ונשלחה הודעה ללקוח")
                        else:
                            st.error(f"❌ הזמנה #{oid} בוטלה (ההודעה לא נשלחה)")

                        time.sleep(1.2)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='div-line'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# TAB 2 — COMPLAINTS
# ══════════════════════════════════════════════
with t2:
    try:
        conn = db()
        cdf = pd.read_sql("SELECT * FROM complaints WHERE status='פתוח' ORDER BY created_at DESC", conn)
        conn.close()

        if cdf.empty:
            st.markdown("""
                <div class='empty-state'>
                    <div class='icon'>😊</div>
                    <h3>אין תלונות פתוחות — הכל טוב!</h3>
                </div>
            """, unsafe_allow_html=True)
        else:
            for _, row in cdf.iterrows():
                t_str = row['created_at'].strftime('%H:%M  %d/%m/%Y')
                st.markdown(f"""
                    <div class='complaint-card'>
                        <div class='stripe stripe-complaint'></div>
                        <div style='display:flex; justify-content:space-between; flex-wrap:wrap; gap:6px; margin-bottom:8px'>
                            <div class='cname'>⚠️ {row['customer_name']}</div>
                            <div style='font-size:12px; color:#3e4870'>{t_str}</div>
                        </div>
                        <div style='font-size:13px; color:#4a3030; margin-bottom:8px'>📱 {row['phone']}</div>
                        <div class='cdesc'>{row['description']}</div>
                    </div>
                """, unsafe_allow_html=True)
                ca, _ = st.columns([1, 4])
                with ca:
                    st.markdown('<div data-btn="approve">', unsafe_allow_html=True)
                    if st.button("✅ סמן כטופל", key=f"cp_{row['id']}", use_container_width=True):
                        q("UPDATE complaints SET status='טופל' WHERE id=%s", (row['id'],), fetch=False)
                        st.success("✔ נסגר")
                        time.sleep(.7)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("<div class='div-line'></div>", unsafe_allow_html=True)
    except:
        st.error("שגיאה בטעינת תלונות — ודא שהטבלה קיימת ב-DB")

# ══════════════════════════════════════════════
# TAB 3 — APPROVED
# ══════════════════════════════════════════════
with t3:
    adf = read_df(
        "SELECT id, customer_name, items, order_type, delivery_time, approved_at FROM orders WHERE status='אושר' ORDER BY approved_at DESC LIMIT 60"
    )
    if not adf.empty:
        st.dataframe(adf, use_container_width=True, hide_index=True, column_config={
            "id":            st.column_config.NumberColumn("מס'", format="%d"),
            "customer_name": "לקוח",
            "items":         "מוצרים",
            "order_type":    "סוג",
            "delivery_time": "זמן",
            "approved_at":   st.column_config.DatetimeColumn("אושר", format="DD/MM HH:mm"),
        })
    else:
        st.info("אין עדיין היסטוריה")

# ══════════════════════════════════════════════
# TAB 4 — CANCELLED
# ══════════════════════════════════════════════
with t4:
    candf = read_df(
        "SELECT id, customer_name, items, cancellation_reason, created_at FROM orders WHERE status='בוטל' ORDER BY created_at DESC LIMIT 60"
    )
    if not candf.empty:
        st.dataframe(candf, use_container_width=True, hide_index=True, column_config={
            "id":                  st.column_config.NumberColumn("מס'", format="%d"),
            "customer_name":       "לקוח",
            "items":               "מוצרים",
            "cancellation_reason": "סיבה",
            "created_at":          st.column_config.DatetimeColumn("תאריך", format="DD/MM HH:mm"),
        })
    else:
        st.info("אין הזמנות מבוטלות")

# ══════════════════════════════════════════════
# TAB 5 — INVENTORY
# ══════════════════════════════════════════════
with t5:
    sub1, sub2 = st.tabs(["📋 מוצרים קיימים", "➕ הוסף מוצר"])

    with sub1:
        ps = st.text_input("🔍 חפש מוצר", placeholder="שם מוצר...", key="ps", label_visibility="collapsed")
        conn = db()
        pf = pd.read_sql("SELECT id, name, price, stock FROM products ORDER BY name", conn)
        conn.close()
        if ps:
            pf = pf[pf['name'].str.contains(ps, case=False, na=False)]

        if pf.empty:
            st.info("לא נמצאו מוצרים")
        else:
            for _, p in pf.iterrows():
                pid = int(p['id'])
                c1, c2, c3, c4, c5 = st.columns([3, 1.5, 1.5, .8, .8])
                with c1:
                    nn = st.text_input("שם", value=p['name'], key=f"pn_{pid}", label_visibility="collapsed")
                with c2:
                    np_ = st.number_input("מחיר", value=float(p['price']), min_value=0.0, step=0.5, key=f"pp_{pid}", label_visibility="collapsed", format="%.2f")
                with c3:
                    ns = st.number_input("מלאי", value=int(p['stock']), min_value=0, step=1, key=f"ps2_{pid}", label_visibility="collapsed")
                with c4:
                    st.markdown('<div data-btn="save">', unsafe_allow_html=True)
                    if st.button("💾", key=f"sv_{pid}", use_container_width=True):
                        q("UPDATE products SET name=%s, price=%s, stock=%s WHERE id=%s",
                          (nn, np_, ns, pid), fetch=False)
                        st.success("✅")
                        time.sleep(.4)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                with c5:
                    st.markdown('<div data-btn="delete">', unsafe_allow_html=True)
                    if st.button("🗑️", key=f"dp_{pid}", use_container_width=True):
                        q("DELETE FROM products WHERE id=%s", (pid,), fetch=False)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    with sub2:
        with st.form("add_prod", clear_on_submit=True):
            a1, a2, a3 = st.columns([3, 2, 2])
            with a1: pname  = st.text_input("🏷️ שם המוצר", placeholder="לחם אחיד, חלב 3%...")
            with a2: pprice = st.number_input("💰 מחיר (₪)", min_value=0.0, step=0.5, format="%.2f")
            with a3: pstock = st.number_input("📦 כמות", min_value=0, step=1, value=10)
            st.markdown('<div data-btn="approve">', unsafe_allow_html=True)
            if st.form_submit_button("➕ הוסף מוצר", use_container_width=True):
                if pname and pprice > 0:
                    q("INSERT INTO products (name, price, stock) VALUES (%s,%s,%s)",
                      (pname, pprice, pstock), fetch=False)
                    st.success(f"✅ '{pname}' נוסף!")
                    time.sleep(.7)
                    st.rerun()
                else:
                    st.error("חסר שם או מחיר")
            st.markdown('</div>', unsafe_allow_html=True)

# ── Footer ──
st.markdown("""
    <div style='text-align:center; padding:28px 0 4px; font-size:12px; color:#1e2235; letter-spacing:.5px'>
        המכולת של הצדיק · ממשק ניהול v4.1
    </div>
""", unsafe_allow_html=True)
