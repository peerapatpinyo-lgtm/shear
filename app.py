import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- IMPORT MODULES ---
try:
    import connection_design as conn
    import report_generator as rep
except ImportError:
    st.error("Missing Files: Please ensure connection_design.py and report_generator.py exist in the same folder.")

# ==========================================
# 1. SETUP & STYLE
# ==========================================
st.set_page_config(page_title="Beam Insight V13", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
    .detail-card {
        background: white; border-radius: 12px; padding: 20px;
        border: 1px solid #e5e7eb; border-top: 6px solid #2563eb;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 20px;
    }
    .highlight-card { 
        background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%);
        padding: 25px; border-radius: 20px; border-left: 8px solid #2563eb; 
        box-shadow: 0 10px 30px rgba(37, 99, 235, 0.08); margin-bottom: 25px; border: 1px solid #e5e7eb;
    }
    .big-num { color: #1e40af; font-size: 42px; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA & SIDEBAR
# ==========================================
steel_db = {
    "H 400x200x8x13": {"h": 400, "b": 200, "tw": 8, "tf": 13, "Ix": 23700, "Zx": 1190, "w": 66.0},
    "H 500x200x10x16": {"h": 500, "b": 200, "tw": 10, "tf": 16, "Ix": 47800, "Zx": 1910, "w": 89.6}
}

with st.sidebar:
    st.title("🏗️ Beam Insight")
    method = st.radio("Design Method", ["ASD", "LRFD"])
    is_lrfd = (method == "LRFD")
    sec_name = st.selectbox("Section", list(steel_db.keys()))
    user_span = st.number_input("Span (m)", value=6.0)
    fy = st.number_input("Fy (kg/cm2)", value=2450)
    
    st.subheader("Connection")
    bolt_size = st.selectbox("Bolt Size", ["M16", "M20", "M24"], index=1)
    bolt_grade = st.selectbox("Bolt Grade", ["A325 (High Strength)", "Grade 8.8"])
    conn_type = "Fin Plate (Single Shear)"

# ==========================================
# 3. CALCULATIONS
# ==========================================
p = steel_db[sec_name]
Aw = (p['h']/10) * (p['tw']/10)
E_mod = 2.04e6

if is_lrfd:
    M_cap, V_cap = 0.90 * fy * p['Zx'], 1.00 * 0.6 * fy * Aw
else:
    M_cap, V_cap = 0.60 * fy * p['Zx'], 0.40 * fy * Aw

def get_capacity(L_m):
    L_cm = L_m * 100
    w_v = (2 * V_cap / L_cm) * 100
    w_m = (8 * M_cap / (L_cm**2)) * 100
    w_d = ((L_cm/360) * 384 * E_mod * p['Ix']) / (5 * (L_cm**4)) * 100
    w_gov = min(w_v, w_m, w_d)
    cause = "Shear" if w_gov == w_v else ("Moment" if w_gov == w_m else "Deflection")
    return w_v, w_m, w_d, w_gov, cause

w_shear, w_moment, w_defl, user_safe_load, user_cause = get_capacity(user_span)
V_design = user_safe_load * user_span / 2

# ==========================================
# 4. TABS
# ==========================================
t1, t2, t3 = st.tabs(["📊 Analysis", "🔩 Connection", "📝 Report"])

with t1:
    st.markdown(f"""<div class="highlight-card"><span class="big-num">{user_safe_load:,.0f}</span> kg/m<br>Control: {user_cause}</div>""", unsafe_allow_html=True)

with t2:
    try:
        req_bolt, v_bolt = conn.render_connection_tab(V_design, bolt_size, method, is_lrfd, p, conn_type, bolt_grade)
    except NameError:
        st.warning("Connection module failed to load.")

with t3:
    try:
        res = {'w_safe': user_safe_load, 'cause': user_cause, 'v_act': V_design, 'v_cap': V_cap, 'm_act': (user_safe_load*user_span**2/8), 'm_cap': M_cap, 'd_all': (user_span*100/360), 'd_act': 0.1}
        bolt_data = {'size': bolt_size, 'qty': 4, 'type': conn_type, 'grade': bolt_grade}
        rep.render_report_tab(method, is_lrfd, sec_name, "SS400", p, res, bolt_data)
    except:
        st.warning("Report module failed to load.")
