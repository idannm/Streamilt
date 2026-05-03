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

DB_URL          = os.environ.get("DB_URL")
BOT_URL         = os.environ.get("BOT_URL", "https://minimarket-ocfq.onrender.com")
INTERNAL_SECRET = os.environ.get("INTERNAL_SECRET", "123")
ADMIN_PASSWORD  = os.environ.get("ADMIN_PASSWORD", "12345")

# ══════════════════════════════════════════════
# STYLES
# ══════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rubik:wght@300;400;500;600;700;800;900&family=Rubik+Mono+One&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body,[class*="css"]{font-family:'Rubik',sans-serif!important;direction:rtl!important}
.stApp{background:#080b14!important;color:#dde1f0!important;min-height:100vh}
#MainMenu,footer,header{visibility:hidden!important}
.block-container{padding:clamp(.75rem,2vw,1.5rem) clamp(.75rem,2vw,1.5rem) 4rem!important;max-width:100%!important}
section[data-testid="stSidebar"]{display:none!important}
[data-testid="stDecoration"],[data-testid="stToolbar"]{display:none!important}

/* ── STATS ── */
.stats-row{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px}
@media(max-width:900px){.stats-row{grid-template-columns:repeat(2,1fr)}}
@media(max-width:480px){.stats-row{grid-template-columns:repeat(2,1fr);gap:8px}}
.sc{border-radius:16px;padding:clamp(14px,2vw,20px) clamp(14px,2vw,20px) clamp(12px,1.5vw,16px);border:1px solid rgba(255,255,255,.07);cursor:pointer;transition:transform .2s,box-shadow .2s,border-color .2s;position:relative;overflow:hidden;user-select:none}
.sc:hover{transform:translateY(-3px);box-shadow:0 14px 40px rgba(0,0,0,.5)}
.sc.active-filter{border-color:#4f46e5!important;box-shadow:0 0 0 2px rgba(79,70,229,.4)!important}
.sc::after{content:attr(data-icon);position:absolute;right:10px;bottom:4px;font-size:clamp(40px,6vw,56px);opacity:.1;pointer-events:none;line-height:1}
.sc .num{font-size:clamp(28px,5vw,44px);font-weight:900;line-height:1;font-family:'Rubik Mono One',monospace}
.sc .lbl{font-size:clamp(10px,1.5vw,12px);font-weight:600;letter-spacing:.6px;text-transform:uppercase;margin-top:5px;opacity:.65}
.sc-all     {background:linear-gradient(135deg,#111520 0%,#161b2e 100%)} .sc-all .num{color:#94a3b8}
.sc-pending {background:linear-gradient(135deg,#1c1730 0%,#221e40 100%)} .sc-pending .num{color:#a78bfa}
.sc-delivery{background:linear-gradient(135deg,#0d1f34 0%,#112840 100%)} .sc-delivery .num{color:#38bdf8}
.sc-pickup  {background:linear-gradient(135deg,#0c2217 0%,#103020 100%)} .sc-pickup .num{color:#34d399}
.sc-complaint{background:linear-gradient(135deg,#270d0d 0%,#311010 100%)} .sc-complaint .num{color:#f87171}

/* ── ALERT ── */
.alert-banner{background:linear-gradient(90deg,#7c3aed 0%,#4f46e5 50%,#0ea5e9 100%);border-radius:14px;padding:clamp(10px,2vw,14px) clamp(14px,3vw,22px);margin-bottom:18px;display:flex;align-items:center;gap:12px;font-size:clamp(13px,2.5vw,17px);font-weight:700;color:#fff;animation:breathe 2.5s ease-in-out infinite;box-shadow:0 4px 30px rgba(124,58,237,.35)}
@keyframes breathe{0%,100%{box-shadow:0 4px 30px rgba(124,58,237,.35)}50%{box-shadow:0 4px 50px rgba(14,165,233,.55)}}
.alert-dot{width:9px;height:9px;border-radius:50%;background:#fff;animation:blink 1s step-start infinite;flex-shrink:0}
@keyframes blink{50%{opacity:0}}

/* ── ORDER CARD ── */
.order-card{background:#0f1320;border:1px solid #1a1f35;border-radius:16px;padding:clamp(12px,2vw,20px) clamp(14px,2.5vw,24px);margin-bottom:6px;position:relative;transition:border-color .2s,box-shadow .2s}
.order-card:hover{border-color:#2a3060;box-shadow:0 6px 28px rgba(0,0,0,.4)}
.order-card .stripe{position:absolute;top:0;right:0;width:5px;height:100%;border-radius:0 16px 16px 0}
.stripe-delivery{background:linear-gradient(180deg,#38bdf8,#0ea5e9)}
.stripe-pickup  {background:linear-gradient(180deg,#34d399,#10b981)}
.stripe-complaint{background:linear-gradient(180deg,#f87171,#ef4444)}
.order-num {font-size:11px;font-weight:600;color:#4a5280;letter-spacing:1px;text-transform:uppercase;margin-bottom:2px}
.order-name{font-size:clamp(17px,3vw,23px);font-weight:800;color:#f1f3ff;margin:2px 0 10px}
.order-items{background:#090d18;border:1px solid #181e30;border-radius:10px;padding:9px 13px;font-size:clamp(12px,2vw,14px);color:#7a84a0;margin-bottom:10px;line-height:1.5}
.order-meta{display:flex;gap:clamp(10px,2vw,18px);flex-wrap:wrap}
.order-meta span{font-size:clamp(11px,1.8vw,13px);color:#4a5280;display:flex;align-items:center;gap:4px}
.phone-pill{background:#111828;border:1px solid #1e3050;border-radius:20px;padding:3px 10px;font-size:12px;color:#38bdf8;font-weight:600;letter-spacing:.3px;cursor:pointer;transition:background .2s}
.phone-pill:hover{background:#1a2840}
.badge{display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;letter-spacing:.3px}
.b-delivery{background:#0c2236;color:#38bdf8;border:1px solid #0e4a75}
.b-pickup  {background:#0a2318;color:#34d399;border:1px solid #0d5a38}
.b-new{background:#2d1f00;color:#fbbf24;border:1px solid #6b4a00;animation:npulse 2s ease-in-out infinite}
@keyframes npulse{0%,100%{opacity:1}50%{opacity:.55}}

/* ── COMPLAINT CARD ── */
.complaint-card{background:#100808;border:1px solid #3b1010;border-radius:16px;padding:clamp(14px,2vw,20px) clamp(16px,2.5vw,22px);margin-bottom:6px;position:relative}
.cname{font-size:clamp(16px,2.5vw,20px);font-weight:800;color:#fca5a5;margin-bottom:6px}
.cdesc{font-size:clamp(12px,2vw,14px);color:#9ca3af;line-height:1.6}
.reply-box{background:#0a1020;border:1px solid #1e3060;border-radius:10px;padding:10px 14px;font-size:13px;color:#7aa0d0;line-height:1.5;margin-top:8px}

/* ── CANCEL PANEL ── */
.cancel-panel{background:#0a0606;border:1px dashed #7f1d1d;border-radius:12px;padding:clamp(12px,2vw,16px) clamp(14px,2.5vw,20px);margin:6px 0}

/* ── BUTTONS ── */
.stButton>button{font-family:'Rubik',sans-serif!important;font-weight:700!important;border-radius:10px!important;border:none!important;padding:clamp(8px,1.5vw,11px) clamp(10px,2vw,14px)!important;font-size:clamp(11px,1.8vw,14px)!important;width:100%!important;transition:transform .15s,filter .15s!important;cursor:pointer!important;white-space:nowrap!important}
.stButton>button:hover{transform:translateY(-1px)!important;filter:brightness(1.12)!important}
.stButton>button:active{transform:translateY(0)!important;filter:brightness(.94)!important}
div[data-btn="approve"] .stButton>button{background:linear-gradient(135deg,#059669,#10b981)!important;color:#fff!important;box-shadow:0 3px 14px rgba(16,185,129,.3)!important}
div[data-btn="cancel"] .stButton>button{background:linear-gradient(135deg,#b91c1c,#ef4444)!important;color:#fff!important;box-shadow:0 3px 14px rgba(239,68,68,.25)!important}
div[data-btn="confirm-cancel"] .stButton>button{background:linear-gradient(135deg,#7f1d1d,#dc2626)!important;color:#fff!important}
div[data-btn="delete"] .stButton>button{background:#0f1320!important;color:#3a4060!important;border:1px solid #1a1f35!important;box-shadow:none!important}
div[data-btn="delete"] .stButton>button:hover{background:#180808!important;color:#f87171!important;border-color:#7f1d1d!important}
div[data-btn="refresh"] .stButton>button{background:linear-gradient(135deg,#1d4ed8,#3b82f6)!important;color:#fff!important;box-shadow:0 3px 14px rgba(59,130,246,.3)!important}
div[data-btn="save"] .stButton>button{background:linear-gradient(135deg,#0369a1,#0ea5e9)!important;color:#fff!important}
div[data-btn="reply"] .stButton>button{background:linear-gradient(135deg,#4f46e5,#7c3aed)!important;color:#fff!important}
div[data-btn="logout"] .stButton>button{background:#0f1320!important;color:#3a4060!important;border:1px solid #1a1f35!important}
div[data-btn="break"] .stButton>button{background:linear-gradient(135deg,#374151,#4b5563)!important;color:#d1d5db!important}
div[data-btn="endday"] .stButton>button{background:linear-gradient(135deg,#92400e,#d97706)!important;color:#fff!important;box-shadow:0 3px 14px rgba(217,119,6,.3)!important}

/* ── INPUTS ── */
.stTextInput>div>div>input,.stNumberInput>div>div>input,.stSelectbox>div>div>div{background:#090d18!important;color:#dde1f0!important;border:1px solid #1a1f35!important;border-radius:10px!important;font-family:'Rubik',sans-serif!important;font-size:clamp(12px,2vw,14px)!important}
.stTextInput>div>div>input:focus,.stNumberInput>div>div>input:focus{border-color:#3b82f6!important;box-shadow:0 0 0 3px rgba(59,130,246,.15)!important;outline:none!important}
.stTextArea>div>div>textarea{background:#090d18!important;color:#dde1f0!important;border:1px solid #1a1f35!important;border-radius:10px!important;font-family:'Rubik',sans-serif!important;font-size:13px!important}
.stTextArea>div>div>textarea:focus{border-color:#7c3aed!important;box-shadow:0 0 0 3px rgba(124,58,237,.15)!important}
label{color:#4a5280!important;font-size:clamp(10px,1.5vw,12px)!important;font-weight:600!important;letter-spacing:.4px!important}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"]{background:#090d18!important;border-radius:12px!important;padding:5px!important;gap:3px!important;border:1px solid #1a1f35!important;flex-wrap:wrap!important}
.stTabs [data-baseweb="tab"]{background:transparent!important;color:#4a5280!important;border-radius:8px!important;font-weight:700!important;font-size:clamp(10px,1.8vw,13px)!important;padding:clamp(7px,1.5vw,10px) clamp(10px,2vw,16px)!important;border:none!important;transition:all .2s!important;white-space:nowrap!important}
.stTabs [data-baseweb="tab"]:hover{background:#111828!important;color:#8892b0!important}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,#1d4ed8,#4f46e5)!important;color:#fff!important;box-shadow:0 2px 12px rgba(79,70,229,.35)!important}
.stTabs [data-baseweb="tab-panel"]{padding-top:16px!important}

/* ── DATAFRAME ── */
.stDataFrame{background:#090d18!important;border-radius:12px!important;border:1px solid #1a1f35!important;overflow:hidden}

/* ── EMPTY STATE ── */
.empty-state{text-align:center;padding:clamp(40px,8vw,70px) 20px;color:#1e2438}
.empty-state .icon{font-size:clamp(40px,8vw,60px);margin-bottom:12px}
.empty-state h3{color:#2e3660!important;font-size:clamp(14px,2.5vw,18px)!important;font-weight:700!important}

/* ── STATS MODAL ── */
.stats-modal{background:#0f1320;border:1px solid #1a1f35;border-radius:20px;padding:clamp(20px,4vw,36px);margin:20px 0}
.stat-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-top:16px}
@media(min-width:600px){.stat-grid{grid-template-columns:repeat(4,1fr)}}
.stat-box{background:#090d18;border:1px solid #1a1f35;border-radius:14px;padding:16px;text-align:center}
.stat-box .big{font-size:clamp(24px,5vw,36px);font-weight:900;font-family:'Rubik Mono One',monospace}
.stat-box .sm{font-size:11px;font-weight:600;letter-spacing:.5px;text-transform:uppercase;opacity:.6;margin-top:4px}
.stat-profit .big{color:#34d399}
.stat-orders .big{color:#a78bfa}
.stat-cancel .big{color:#f87171}
.stat-comp   .big{color:#fbbf24}

/* ── LOGIN ── */
.login-wrap{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.login-card{background:#0f1320;border:1px solid #1a1f35;border-radius:24px;padding:clamp(28px,6vw,52px);width:min(420px,100%);text-align:center;box-shadow:0 24px 80px rgba(0,0,0,.6)}
.login-logo{font-size:clamp(48px,10vw,68px);margin-bottom:10px}
.login-card h1{font-size:clamp(20px,4vw,28px)!important;font-weight:900!important;color:#f1f3ff!important;margin-bottom:6px}
.login-card p{color:#2e3660;font-size:clamp(12px,2vw,14px);margin-bottom:clamp(20px,4vw,32px)}
div[data-btn="login"] .stButton>button{background:linear-gradient(135deg,#4f46e5,#7c3aed)!important;color:#fff!important;font-size:clamp(14px,2.5vw,16px)!important;padding:clamp(12px,2.5vw,16px)!important;box-shadow:0 4px 24px rgba(124,58,237,.4)!important}
div[data-btn="login"] .stButton>button:hover{box-shadow:0 6px 32px rgba(124,58,237,.6)!important}

/* ── DIVIDER ── */
.div-line{height:1px;background:#131825;margin:8px 0 14px}

/* ── SCROLLBAR ── */
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:#080b14}
::-webkit-scrollbar-thumb{background:#1a1f35;border-radius:3px}

/* ── FILTER LABEL ── */
.filter-label{font-size:11px;font-weight:700;color:#3a4270;letter-spacing:.8px;text-transform:uppercase;margin-bottom:8px}
</style>

<script>
// ── WEB AUDIO SOUNDS ──
const _AC=window.AudioContext||window.webkitAudioContext;
let _ac=null;
function _ctx(){if(!_ac||_ac.state==='closed')_ac=new _AC();if(_ac.state==='suspended')_ac.resume();return _ac}
function playDelivery(){const c=_ctx(),t=c.currentTime;[[0,440],[.13,560],[.26,680]].forEach(([d,f])=>{const o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);o.frequency.value=f;o.type='sine';g.gain.setValueAtTime(0,t+d);g.gain.linearRampToValueAtTime(.38,t+d+.04);g.gain.exponentialRampToValueAtTime(.001,t+d+.22);o.start(t+d);o.stop(t+d+.25)})}
function playPickup(){const c=_ctx(),t=c.currentTime;[0,.22].forEach(d=>{const o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);o.frequency.value=880;o.type='triangle';g.gain.setValueAtTime(0,t+d);g.gain.linearRampToValueAtTime(.3,t+d+.03);g.gain.exponentialRampToValueAtTime(.001,t+d+.18);o.start(t+d);o.stop(t+d+.2)})}
function playComplaint(){const c=_ctx(),t=c.currentTime;const o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);o.frequency.setValueAtTime(260,t);o.frequency.linearRampToValueAtTime(180,t+.55);o.type='sawtooth';g.gain.setValueAtTime(.22,t);g.gain.linearRampToValueAtTime(0,t+.6);o.start(t);o.stop(t+.65)}
function playNewOrder(){const c=_ctx(),t=c.currentTime;[523,659,784,1047].forEach((f,i)=>{const o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);o.frequency.value=f;o.type='sine';const d=t+i*.11;g.gain.setValueAtTime(0,d);g.gain.linearRampToValueAtTime(.32,d+.03);g.gain.exponentialRampToValueAtTime(.001,d+.22);o.start(d);o.stop(d+.25)})}

let _prev={o:-1,c:-1,s:''};
function _watch(){
  const oe=document.getElementById('_oc'),ce=document.getElementById('_cc'),se=document.getElementById('_st');
  if(!oe||!ce||!se)return;
  const o=parseInt(oe.dataset.v||-1),cmp=parseInt(ce.dataset.v||-1),snd=se.dataset.v||'';
  if(snd&&snd!==_prev.s){_prev.s=snd;
    if(snd==='delivery')playDelivery();
    else if(snd==='pickup')playPickup();
    else if(snd==='complaint')playComplaint();
    else if(snd==='new_order')playNewOrder();
  }
  if(_prev.o>=0&&o>_prev.o)playNewOrder();
  if(_prev.c>=0&&cmp>_prev.c)playComplaint();
  _prev.o=o;_prev.c=cmp;
}
setInterval(_watch,900);

// ── AUTO-REFRESH every 30s (receives new orders without manual refresh) ──
let _lastInteract=Date.now();
document.addEventListener('click',()=>_lastInteract=Date.now());
document.addEventListener('keydown',()=>_lastInteract=Date.now());
setInterval(()=>{
  // Only auto-refresh if user hasn't interacted in last 5s (avoid interrupting actions)
  if(Date.now()-_lastInteract>5000){
    const btn=Array.from(document.querySelectorAll('button')).find(b=>b.textContent.includes('🔄'));
    if(btn)btn.click();
  }
},30000);

// ── KEEPALIVE (no session timeout) ──
setInterval(()=>{try{fetch(window.location.href,{method:'HEAD'})}catch(e){}},120000);
</script>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# DB
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

def read_df(sql, params=None):
    conn = db()
    try:
        return pd.read_sql(sql, conn, params=params)
    except:
        return pd.DataFrame()
    finally:
        conn.close()

def extract_phone(addr):
    try:
        if "WA_ID:" in str(addr):
            raw = str(addr).split("WA_ID:")[-1].strip()
            # Format nicely: 972501234567 → 050-123-4567
            return raw
        c = str(addr).replace("-","").strip()
        return ("972" + c[1:]) if c.startswith("0") else c
    except:
        return None

def format_phone_display(addr):
    """Extract phone and format for display"""
    raw = extract_phone(addr)
    if not raw:
        return "—"
    # 972XXXXXXXXX → 05X-XXX-XXXX
    if raw.startswith("972") and len(raw) == 12:
        local = "0" + raw[3:]
        return f"{local[:3]}-{local[3:6]}-{local[6:]}"
    return raw

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
    rows = q("SELECT status, order_type FROM orders WHERE status='ממתין לאישור'")
    pending    = len(rows)
    deliveries = sum(1 for r in rows if 'איסוף' not in str(r[1]).lower())
    pickups    = pending - deliveries
    comp = q("SELECT COUNT(*) FROM complaints WHERE status='פתוח'")
    complaints = comp[0][0] if comp else 0
    return pending, deliveries, pickups, complaints

def get_day_stats():
    """Stats for end-of-day summary"""
    today = datetime.now().strftime('%Y-%m-%d')
    orders = q(f"""
        SELECT status, order_type, total_price FROM orders
        WHERE DATE(created_at) = '{today}'
    """)
    comp = q(f"SELECT COUNT(*) FROM complaints WHERE DATE(created_at)='{today}'")
    total    = len(orders)
    approved = sum(1 for r in orders if r[0]=='אושר')
    cancelled= sum(1 for r in orders if r[0]=='בוטל')
    pending  = sum(1 for r in orders if r[0]=='ממתין לאישור')
    # Rough profit estimate (total_price stored as 0 currently, so show order count)
    complaints_today = comp[0][0] if comp else 0
    return {
        "total": total, "approved": approved,
        "cancelled": cancelled, "pending": pending,
        "complaints": complaints_today
    }

# ══════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════
defaults = {
    'logged_in': False,
    'prev_pending': -1,
    'prev_complaints': -1,
    'sound': '',
    'cancel_open': {},
    'cancel_reason': {},
    'cancel_custom': {},
    'active_filter': 'all',   # all | delivery | pickup
    'reply_open': {},
    'show_end_day': False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════
# LOGIN PAGE
# ══════════════════════════════════════════════
if not st.session_state.logged_in:
    st.markdown("<div class='login-wrap'>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("""
            <div class='login-card'>
                <div class='login-logo'>🛒</div>
                <h1>המכולת של הצדיק</h1>
                <p>ממשק ניהול מתקדם · כניסת מנהל</p>
            </div>
        """, unsafe_allow_html=True)
        pwd = st.text_input(" ", type="password", placeholder="🔑  הכנס סיסמה...",
                            label_visibility="collapsed")
        st.markdown('<div data-btn="login">', unsafe_allow_html=True)
        if st.button("כניסה לניהול  →", use_container_width=True):
            if pwd == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("❌ סיסמה שגויה — נסה שוב")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════
# END-OF-DAY MODAL
# ══════════════════════════════════════════════
if st.session_state.show_end_day:
    stats = get_day_stats()
    st.markdown(f"""
        <div class='stats-modal'>
            <div style='font-size:clamp(18px,3vw,24px);font-weight:900;color:#f1f3ff;margin-bottom:4px'>
                📊 סיכום היום · {datetime.now().strftime('%d/%m/%Y')}
            </div>
            <div style='font-size:13px;color:#3a4270;margin-bottom:4px'>
                כל הנתונים הם של היום בלבד
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
        <div class='stat-grid'>
            <div class='stat-box stat-orders'>
                <div class='big'>{stats['total']}</div>
                <div class='sm'>הזמנות סה"כ</div>
            </div>
            <div class='stat-box stat-profit'>
                <div class='big'>{stats['approved']}</div>
                <div class='sm'>הזמנות שאושרו</div>
            </div>
            <div class='stat-box stat-cancel'>
                <div class='big'>{stats['cancelled']}</div>
                <div class='sm'>ביטולים</div>
            </div>
            <div class='stat-box stat-comp'>
                <div class='big'>{stats['complaints']}</div>
                <div class='sm'>תלונות היום</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    ca, cb = st.columns(2)
    with ca:
        if st.button("← חזור לניהול", use_container_width=True):
            st.session_state.show_end_day = False
            st.rerun()
    with cb:
        st.markdown('<div data-btn="logout">', unsafe_allow_html=True)
        if st.button("🚪 סגור וצא מהמערכת", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.show_end_day = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════
# MAIN — COUNTS + SOUND DATA
# ══════════════════════════════════════════════
pending, deliveries, pickups, complaints = get_counts()

sound = st.session_state.sound
if st.session_state.prev_pending >= 0 and pending > st.session_state.prev_pending and not sound:
    sound = 'new_order'
if st.session_state.prev_complaints >= 0 and complaints > st.session_state.prev_complaints and not sound:
    sound = 'complaint'
st.session_state.prev_pending    = pending
st.session_state.prev_complaints = complaints
st.session_state.sound = ''

st.markdown(f"""
<div id='_oc' data-v='{pending}'    style='display:none'></div>
<div id='_cc' data-v='{complaints}' style='display:none'></div>
<div id='_st' data-v='{sound}'      style='display:none'></div>
""", unsafe_allow_html=True)

# ══ HEADER ══
h1, h2 = st.columns([5, 1])
with h1:
    now_str = datetime.now().strftime("%A %d/%m/%Y · %H:%M")
    st.markdown(f"""
        <div style='margin-bottom:16px'>
            <div style='font-size:clamp(18px,4vw,26px);font-weight:900;color:#f1f3ff;letter-spacing:-.5px'>
                🛒 המכולת של הצדיק
            </div>
            <div style='font-size:clamp(11px,2vw,13px);color:#2e3660;margin-top:2px'>{now_str}</div>
        </div>
    """, unsafe_allow_html=True)
with h2:
    r1, r2 = st.columns(2)
    with r1:
        st.markdown('<div data-btn="refresh">', unsafe_allow_html=True)
        if st.button("🔄", help="רענן", key="hrefresh"):
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with r2:
        st.markdown('<div data-btn="logout">', unsafe_allow_html=True)
        if st.button("🚪", help="יציאה", key="hlogout_menu"):
            # Show exit options below
            st.session_state['show_exit_menu'] = not st.session_state.get('show_exit_menu', False)
        st.markdown('</div>', unsafe_allow_html=True)

# ── EXIT MENU ──
if st.session_state.get('show_exit_menu', False):
    ex1, ex2, ex3 = st.columns([2, 2, 3])
    with ex1:
        st.markdown('<div data-btn="break">', unsafe_allow_html=True)
        if st.button("☕ הפסקה (סגור)", use_container_width=True, key="break_btn"):
            st.session_state.logged_in = False
            st.session_state.show_exit_menu = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with ex2:
        st.markdown('<div data-btn="endday">', unsafe_allow_html=True)
        if st.button("📊 סיום יום + סטטיסטיקה", use_container_width=True, key="endday_btn"):
            st.session_state.show_exit_menu = False
            st.session_state.show_end_day = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with ex3:
        st.markdown("""
            <div style='padding:8px 0; font-size:12px; color:#3a4270'>
                ☕ הפסקה — ייסגר, הזמנות ממשיכות להתקבל<br>
                📊 סיום יום — סטטיסטיקה ואז יציאה
            </div>
        """, unsafe_allow_html=True)

# ══ STAT CARDS (clickable filters) ══
af = st.session_state.active_filter
all_cls      = 'sc sc-all'      + (' active-filter' if af=='all'      else '')
pending_cls  = 'sc sc-pending'  + (' active-filter' if af=='pending'  else '')
delivery_cls = 'sc sc-delivery' + (' active-filter' if af=='delivery' else '')
pickup_cls   = 'sc sc-pickup'   + (' active-filter' if af=='pickup'   else '')
complaint_cls= 'sc sc-complaint'+ (' active-filter' if af=='complaint'else '')

st.markdown(f"""
<div class='stats-row'>
  <div class='{pending_cls}'  data-icon='📦' onclick="window.parent.document.querySelector('[data-testid=stApp]').dispatchEvent(new CustomEvent('filter',{{detail:'pending'}}))">
    <div class='num'>{pending}</div><div class='lbl'>ממתינות לטיפול</div>
  </div>
  <div class='{delivery_cls}' data-icon='🛵'>
    <div class='num'>{deliveries}</div><div class='lbl'>משלוחים</div>
  </div>
  <div class='{pickup_cls}'   data-icon='🛒'>
    <div class='num'>{pickups}</div><div class='lbl'>איסופים</div>
  </div>
  <div class='{complaint_cls}' data-icon='⚠️'>
    <div class='num'>{complaints}</div><div class='lbl'>תלונות פתוחות</div>
  </div>
</div>
""", unsafe_allow_html=True)

# Clickable filter buttons under stats
fc1, fc2, fc3, fc4 = st.columns(4)
for col, label, key, fval in [
    (fc1, "📦 כל הממתינות", "f_all", "all"),
    (fc2, "🛵 משלוחים בלבד", "f_del", "delivery"),
    (fc3, "🛒 איסופים בלבד", "f_pick", "pickup"),
    (fc4, "", "f_none", None),
]:
    if fval:
        with col:
            is_active = st.session_state.active_filter == fval
            btn_style = "refresh" if is_active else "delete"
            st.markdown(f'<div data-btn="{btn_style}">', unsafe_allow_html=True)
            if st.button(label, key=key, use_container_width=True):
                st.session_state.active_filter = fval
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

if pending > 0:
    st.markdown(f"""
        <div class='alert-banner'>
            <div class='alert-dot'></div>
            {pending} הזמנה{'ות' if pending>1 else ''} מחכ{'ות' if pending>1 else 'ה'} לאישורך!
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
# TAB 1 — PENDING ORDERS
# ══════════════════════════════════════════════
with t1:
    srch = st.text_input("🔍", placeholder="חיפוש לפי שם / מוצר / מספר הזמנה...",
                         key="s1", label_visibility="collapsed")

    conn = db()
    df = pd.read_sql(
        "SELECT id, customer_name, items, address, order_type, created_at FROM orders WHERE status='ממתין לאישור' ORDER BY created_at DESC",
        conn
    )
    conn.close()

    # Apply filter
    filt = st.session_state.active_filter
    if filt == 'delivery':
        df = df[~df['order_type'].str.contains('איסוף', na=False)]
    elif filt == 'pickup':
        df = df[df['order_type'].str.contains('איסוף', na=False)]

    if srch:
        m = (
            df['customer_name'].str.contains(srch, case=False, na=False) |
            df['items'].str.contains(srch, case=False, na=False) |
            df['id'].astype(str).str.contains(srch)
        )
        df = df[m]

    if filt != 'all':
        label = "איסופים" if filt == 'pickup' else "משלוחים"
        st.markdown(f"<div class='filter-label'>מסנן: {label} בלבד</div>", unsafe_allow_html=True)

    if df.empty:
        st.markdown("""
            <div class='empty-state'>
                <div class='icon'>🎉</div>
                <h3>כל ההזמנות טופלו — כל הכבוד!</h3>
            </div>
        """, unsafe_allow_html=True)
    else:
        for _, row in df.iterrows():
            oid       = int(row['id'])
            otype     = str(row.get('order_type','משלוח'))
            is_pickup = 'איסוף' in otype
            stripe    = 'stripe-pickup' if is_pickup else 'stripe-delivery'
            badge     = "<span class='badge b-pickup'>🛒 איסוף</span>" if is_pickup else "<span class='badge b-delivery'>🛵 משלוח</span>"
            addr_raw  = str(row['address'])
            addr_display = addr_raw.split('|')[0].strip()
            phone_display = format_phone_display(addr_raw)
            created   = row['created_at'].strftime('%H:%M  %d/%m')

            st.markdown(f"""
                <div class='order-card'>
                    <div class='stripe {stripe}'></div>
                    <div style='display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:6px'>
                        <div>
                            <div class='order-num'>הזמנה #{oid} &nbsp;·&nbsp; {badge} &nbsp;<span class='badge b-new'>חדש</span></div>
                            <div class='order-name'>{row['customer_name']}</div>
                        </div>
                        <div style='text-align:left;display:flex;flex-direction:column;align-items:flex-end;gap:6px'>
                            <div style='color:#2e3660;font-size:12px'>{created}</div>
                            <span class='phone-pill'>📱 {phone_display}</span>
                        </div>
                    </div>
                    <div class='order-items'>🛍️ {row['items']}</div>
                    <div class='order-meta'>
                        <span>📍 {addr_display}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            c_time, c_app, c_can, c_del = st.columns([2.4, 2.2, 2.2, 0.65])

            with c_time:
                placeholder = "מוכן לאיסוף בעוד..." if is_pickup else "זמן הגעה משוער..."
                time_val = st.text_input("⏱", value="20 דקות", key=f"tv_{oid}",
                                         label_visibility="collapsed", placeholder=placeholder)
            with c_app:
                st.markdown('<div data-btn="approve">', unsafe_allow_html=True)
                if st.button("✅ אשר ושלח ללקוח", key=f"ap_{oid}", use_container_width=True):
                    q("UPDATE orders SET status='אושר', delivery_time=%s, approved_at=NOW() WHERE id=%s",
                      (time_val, oid), fetch=False)
                    msg = (
                        f"היי {row['customer_name']}! ✅ ההזמנה שלך אושרה.\n"
                        f"{'🛒 מוכן לאיסוף בעוד: ' if is_pickup else '🛵 זמן הגעה: '}{time_val}\n"
                        f"🛍️ {row['items']}\nתודה שקנית אצלנו! 🙏"
                    )
                    ok = notify(row['address'], msg)
                    st.session_state.sound = 'pickup' if is_pickup else 'delivery'
                    if ok:
                        st.success(f"✅ הזמנה #{oid} אושרה ונשלחה הודעה")
                    else:
                        st.warning(f"⚠️ אושר, אבל ההודעה לא נשלחה")
                    time.sleep(1)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            with c_can:
                st.markdown('<div data-btn="cancel">', unsafe_allow_html=True)
                if st.button("❌ בטל הזמנה", key=f"cbt_{oid}", use_container_width=True):
                    st.session_state.cancel_open[oid] = not st.session_state.cancel_open.get(oid, False)
                st.markdown('</div>', unsafe_allow_html=True)

            with c_del:
                st.markdown('<div data-btn="delete">', unsafe_allow_html=True)
                if st.button("🗑️", key=f"dl_{oid}", use_container_width=True, help="מחק"):
                    q("DELETE FROM orders WHERE id=%s", (oid,), fetch=False)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            # ── CANCEL PANEL ──
            if st.session_state.cancel_open.get(oid, False):
                st.markdown("<div class='cancel-panel'>", unsafe_allow_html=True)
                st.markdown("<div style='font-size:13px;font-weight:700;color:#f87171;margin-bottom:10px'>🔴 ביטול הזמנה — בחר סיבה</div>", unsafe_allow_html=True)
                cp1, cp2 = st.columns([3, 1])
                with cp1:
                    chosen = st.selectbox(
                        "סיבה",
                        ["חוסר במלאי", "כתובת שגויה", "לקוח לא זמין", "מחוץ לאזור משלוח", "אחר"],
                        key=f"rs_{oid}", label_visibility="collapsed"
                    )
                    st.session_state.cancel_reason[oid] = chosen
                    if chosen == "אחר":
                        custom = st.text_input("פרט:", key=f"rc_{oid}",
                                               placeholder="כתוב סיבה...", label_visibility="collapsed")
                        st.session_state.cancel_custom[oid] = custom
                with cp2:
                    st.markdown('<div data-btn="confirm-cancel">', unsafe_allow_html=True)
                    if st.button("אשר ביטול", key=f"ccf_{oid}", use_container_width=True):
                        final_reason = st.session_state.cancel_reason.get(oid, "לא צוינה סיבה")
                        if final_reason == "אחר":
                            final_reason = st.session_state.cancel_custom.get(oid, "") or "לא צוינה סיבה"
                        # 1. DB update
                        q("UPDATE orders SET status='בוטל', cancellation_reason=%s WHERE id=%s",
                          (final_reason, oid), fetch=False)
                        # 2. Notify customer BEFORE rerun
                        msg = (
                            f"היי {row['customer_name']}, ההזמנה שלך בוטלה ❌\n"
                            f"סיבה: {final_reason}\n"
                            f"מצטערים מאוד! אם יש שאלות — דבר איתנו 🙏"
                        )
                        ok = notify(row['address'], msg)
                        # 3. Clean state
                        st.session_state.cancel_open.pop(oid, None)
                        st.session_state.cancel_reason.pop(oid, None)
                        st.session_state.cancel_custom.pop(oid, None)
                        if ok:
                            st.error(f"❌ הזמנה #{oid} בוטלה ונשלחה הודעה ללקוח")
                        else:
                            st.error(f"❌ הזמנה #{oid} בוטלה (שליחת הודעה נכשלה)")
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
                    <h3>אין תלונות פתוחות — הכל מצוין!</h3>
                </div>
            """, unsafe_allow_html=True)
        else:
            for _, row in cdf.iterrows():
                cid   = int(row['id'])
                t_str = row['created_at'].strftime('%H:%M  %d/%m/%Y')
                phone_disp = row['phone'] if row['phone'] else "—"

                # Check if already replied
                has_reply = bool(row.get('owner_reply',''))
                reply_html = f"<div class='reply-box'>💬 תשובתך: {row['owner_reply']}</div>" if has_reply else ""

                st.markdown(f"""
                    <div class='complaint-card'>
                        <div class='stripe stripe-complaint'></div>
                        <div style='display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px;margin-bottom:8px'>
                            <div class='cname'>⚠️ {row['customer_name']}</div>
                            <div style='font-size:12px;color:#2e2020'>{t_str}</div>
                        </div>
                        <div style='margin-bottom:6px'>
                            <span class='phone-pill'>📱 {phone_disp}</span>
                        </div>
                        <div class='cdesc'>{row['description']}</div>
                        {reply_html}
                    </div>
                """, unsafe_allow_html=True)

                # Action row
                ca1, ca2, ca3 = st.columns([2, 2, 2])

                with ca1:
                    st.markdown('<div data-btn="approve">', unsafe_allow_html=True)
                    if st.button("✅ סמן כטופל", key=f"cp_{cid}", use_container_width=True):
                        q("UPDATE complaints SET status='טופל' WHERE id=%s", (cid,), fetch=False)
                        st.success("✔ התלונה נסגרה")
                        time.sleep(.7)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

                with ca2:
                    st.markdown('<div data-btn="reply">', unsafe_allow_html=True)
                    if st.button("💬 השב ללקוח", key=f"replyopen_{cid}", use_container_width=True):
                        st.session_state.reply_open[cid] = not st.session_state.reply_open.get(cid, False)
                    st.markdown('</div>', unsafe_allow_html=True)

                with ca3:
                    st.markdown("""
                        <div style='font-size:11px;color:#2e2030;padding:6px 0;line-height:1.5'>
                            💡 השב ישירות בוואטסאפ<br>או סמן כטופל אחרי שפתרת
                        </div>
                    """, unsafe_allow_html=True)

                # Reply box
                if st.session_state.reply_open.get(cid, False):
                    reply_text = st.text_area(
                        "תשובה ללקוח",
                        key=f"rt_{cid}",
                        placeholder="כתוב תשובה שתישלח ישירות ללקוח בוואטסאפ...",
                        height=90,
                        label_visibility="collapsed"
                    )
                    rs1, rs2 = st.columns([1,3])
                    with rs1:
                        st.markdown('<div data-btn="reply">', unsafe_allow_html=True)
                        if st.button("📤 שלח", key=f"rsend_{cid}", use_container_width=True):
                            if reply_text and reply_text.strip():
                                full_msg = f"שלום {row['customer_name']},\n\nבנוגע לפנייתך: \"{row['description']}\"\n\n{reply_text.strip()}\n\nבברכה, המכולת של הצדיק 🛒"
                                ok = notify(f"WA_ID:{row['phone']}", full_msg)
                                if ok:
                                    # Save reply to DB
                                    q("UPDATE complaints SET owner_reply=%s, replied_at=NOW() WHERE id=%s",
                                      (reply_text.strip(), cid), fetch=False)
                                    st.success("✅ התשובה נשלחה ללקוח!")
                                    st.session_state.reply_open[cid] = False
                                    time.sleep(.8)
                                    st.rerun()
                                else:
                                    st.error("❌ שליחה נכשלה — בדוק את חיבור הבוט")
                            else:
                                st.warning("כתוב תשובה לפני השליחה")
                        st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("<div class='div-line'></div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"שגיאה בטעינת תלונות: {e}")
        st.info("ודא שהרצת: ALTER TABLE complaints ADD COLUMN IF NOT EXISTS owner_reply TEXT; ALTER TABLE complaints ADD COLUMN IF NOT EXISTS replied_at TIMESTAMP;")

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
        ps = st.text_input("🔍", placeholder="חפש מוצר...", key="ps", label_visibility="collapsed")
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
    <div style='text-align:center;padding:24px 0 4px;font-size:11px;color:#1a1f35;letter-spacing:.5px'>
        המכולת של הצדיק · v5.0
    </div>
""", unsafe_allow_html=True)
