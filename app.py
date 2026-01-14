import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- IMPORT MODULES ที่เราแยกไว้ ---
import connection_design as conn
import report_generator as rep

# ==========================================
# 1. SETUP & STYLE (PREMIUM UI V12)
# ==========================================
st.set_page_config(page_title="Beam Insight V12 (Modular)", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }

    /* Highlight Card */
    .highlight-card { 
        background: linear-gradient(135deg, #ebf5fb 0%, #ffffff 100%);
        padding: 25px; border-radius: 12px; border-left: 6px solid #2e86c1; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 25px; 
    }

    /* Metric Box */
    .metric-box { 
        text-align: center; padding: 20px; background: white; 
        border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
        border-top: 5px solid #ccc; height: 100%; transition: all 0.3s ease;
    }
    .metric-box:hover { transform: translateY(-5px); box-shadow: 0 12px 20px rgba(0,0,0,0.1); }
    
    .big-num { font-size: 28px; font-weight: 800; color: #17202a; margin-bottom: 5px; }
    .sub-text { font-size: 16px; font-weight: 600; color: #566573; text-transform: uppercase; }
    
    .mini-calc {
        background-color: #f8f9fa; border: 1px dashed #bdc3c7; border-radius: 6px; 
        padding: 10px; margin-top: 12px; font-family: 'Courier New', monospace; 
        font-size: 13px; color: #444; text-align: left; line-height: 1.6;
    }
    
    /* Styles for Report & Connection (Global) */
    .report-paper { background-color: #ffffff; padding: 40px; border: 1px solid #e5e7e9; box-shadow: 0 10px 30px rgba(0,0,0,0.08); border-radius: 2px; max-width: 900px; margin: auto; }
    .report-header { font-size: 20px; font-weight: 800; color: #1a5276; margin-top: 25px; border-bottom: 2px solid #a9cce3; padding-bottom: 8px; }
    .report-line { font-family: 'Courier New', monospace; font-size: 16px; margin-bottom: 8px; color: #2c3e50; border-bottom: 1px dotted #eee; }
    .calc-box { background-color: #f4f6f7; padding: 12px; border-radius: 6px; border-left: 4px solid #85c1e9; margin-bottom: 10px; font-family: 'Courier New', monospace; font-size: 14px; }
    .conn-card { background-color: #fffbf0; padding: 20px; border-radius: 10px; border-left: 6px solid #f1c40f; box-shadow: 0 2px 5px rgba(0,0,0,0.02); }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE & INPUTS
# ==========================================
steel_db = {
    "H 150x75x5x7":     {"h": 150, "b": 75,  "tw": 5,   "tf": 7,   "Ix": 666,    "Zx": 88.8,  "w": 14.0},
    "H 200x100x5.5x8":  {"h": 200, "b": 100, "tw": 5.5, "tf": 8,   "Ix": 1840,   "Zx": 184,   "w": 21.3},
    "H 250x125x6x9":    {"h": 250, "b": 125, "tw": 6,   "tf": 9,   "Ix": 3690,   "Zx": 295,   "w": 29.6},
    "H 300x150x6.5x9":  {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481,   "w": 36.7},
    "H 350x175x7x11":   {"h": 350, "b": 175, "tw": 7,   "tf": 11,  "Ix": 13600,  "Zx": 775,   "w": 49.6},
    "H 400x200x8x13":   {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190,  "w": 66.0},
    "H 450x200x9x14":   {"h": 450, "b": 200, "tw": 9,   "tf": 14,  "Ix": 33500,  "Zx": 1490,  "w": 76.0},
    "H 500x200x10x16":  {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910,  "w": 89.6},
    "H 600x200x11x17":  {"h": 600, "b": 200, "tw": 11,  "tf": 17,  "Ix": 77600,  "Zx": 2590,  "w": 106},
}

with st.sidebar:
    st.title("Beam Insight V12")
    st.caption("Modular Edition")
    st.divider()
    
    st.header("1. Design Method")
    method = st.radio("Standard", ["ASD (Allowable Stress)", "LRFD (Limit State)"])
    is_lrfd = "LRFD" in method
    
    st.divider()
    st.header("2. Beam Settings")
    sec_name = st.selectbox("Select Section", list(steel_db.keys()), index=5)
    user_span = st.number_input("Span Length (m)", min_value=1.0, value=6.0, step=0.5)
    fy = st.number_input("Fy (ksc)", 2400)
    defl_ratio = st.selectbox("Defl. Limit", ["L/300", "L/360", "L/400"], index=1)
    
    st.divider()
    st.header("3. Connection Settings")
    bolt_size = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)
    design_mode = st.radio("Connection Design:", 
                           ["Actual Load (from Span)", "Fixed % Capacity"])
    
    if design_mode == "Fixed % Capacity":
        target_pct = st.slider("Target % Usage", 50, 100, 75, 5)
    else:
        target_pct = None

    E_mod = 2.04e6 
    defl_lim_val = int(defl_ratio.split("/")[1])

# ==========================================
# 3. CORE BEAM CALCULATION
# ==========================================
p = steel_db[sec_name]
h_cm, tw_cm = p['h']/10, p['tw']/10
Aw = h_cm * tw_cm
Ix, Zx = p['Ix'], p['Zx']

# --- ASD vs LRFD Logic for Beam ---
if is_lrfd:
    phi_b, phi_v = 0.90, 1.00
    M_cap = phi_b * fy * Zx
    V_cap = phi_v * 0.6 * fy * Aw
    label_load = "Factored Load (Wu)"
    label_cap_m = "Phi Mn"
    label_cap_v = "Phi Vn"
else:
    M_cap = 0.6 * fy * Zx
    V_cap = 0.4 * fy * Aw
    label_load = "Safe Load (w)"
    label_cap_m = "M allow"
    label_cap_v = "V allow"

def get_capacity(L_m):
    L_cm = L_m * 100
    w_s = (2 * V_cap) / L_cm * 100
    w_m = (8 * M_cap) / (L_cm**2) * 100
    w_d = ((L_cm/defl_lim_val) * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100
    w_gov = min(w_s, w_m, w_d)
    cause = "Shear" if w_gov == w_s else ("Moment" if w_gov == w_m else "Deflection")
    return w_s, w_m, w_d, w_gov, cause

w_shear, w_moment, w_defl, user_safe_load, user_cause = get_capacity(user_span)
V_actual = user_safe_load * user_span / 2
M_actual = user_safe_load * user_span**2 / 8
delta_actual = (5 * (user_safe_load/100) * ((user_span*100)**4)) / (384 * E_mod * Ix)
delta_allow = (user_span*100) / defl_lim_val

# Determine V_design for Connection
if design_mode == "Actual Load (from Span)":
    V_design = V_actual
else:
    V_design = V_cap * (target_pct / 100)

# ==========================================
# 4. UI DISPLAY (Main & Modules)
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Beam Analysis", "🔩 Connection Detail", "💾 Load Table", "📝 Calculation Report"])

with tab1:
    st.subheader(f"Capacity Analysis: {sec_name} ({'LRFD' if is_lrfd else 'ASD'})")
    cause_color = "#e74c3c" if user_cause == "Shear" else ("#f39c12" if user_cause == "Moment" else "#27ae60")
    
    # 1. Main Load Card
    st.markdown(f"""
    <div class="highlight-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span class="sub-text" style="color:#2874a6;">Max {label_load}</span><br>
                <span class="big-num" style="color:#2874a6; font-size:38px;">{user_safe_load:,.0f}</span> <span style="font-size:20px; color:#555;">kg/m</span>
            </div>
            <div style="text-align: right;">
                <span class="sub-text">Control Factor</span><br>
                <span style="font-size: 22px; font-weight:bold; color:{cause_color}; background-color:rgba(0,0,0,0.05); padding: 5px 15px; border-radius:20px;">{user_cause}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ====================================================
    # ✅ ส่วนที่กู้คืนกลับมา: Logic Source (Detail Expander)
    # ====================================================
    with st.expander(f"🕵️‍♂️ ดูที่มาการคำนวณ (Method: {method})", expanded=False):
        c_cal1, c_cal2, c_cal3 = st.columns(3)
        with c_cal1:
            formula_v = "Phi Vn = 1.0*0.6*Fy*Aw" if is_lrfd else "V_all = 0.4*Fy*Aw"
            st.markdown(f"""<div class="calc-box"><b>1. Shear ({'LRFD' if is_lrfd else 'ASD'}):</b><br>Cap = {formula_v}<br>= {V_cap:,.0f} kg<br>w = 2*Cap/L = <b>{w_shear:,.0f}</b></div>""", unsafe_allow_html=True)
        with c_cal2:
            formula_m = "Phi Mn = 0.9*Fy*Zx" if is_lrfd else "M_all = 0.6*Fy*Zx"
            st.markdown(f"""<div class="calc-box"><b>2. Moment ({'LRFD' if is_lrfd else 'ASD'}):</b><br>Cap = {formula_m}<br>= {M_cap:,.0f} kg.cm<br>w = 8*Cap/L^2 = <b>{w_moment:,.0f}</b></div>""", unsafe_allow_html=True)
        with c_cal3:
            st.markdown(f"""<div class="calc-box"><b>3. Deflection:</b><br>Limit = L/{defl_lim_val}<br>w = (d*384EI)/(5L^4)<br>= <b>{w_defl:,.0f}</b></div>""", unsafe_allow_html=True)
    
    st.markdown("---")

    # 3. Metrics
    cm1, cm2, cm3 = st.columns(3)
    with cm1: 
        st.markdown(f"""<div class="metric-box" style="border-top-color: #e74c3c;"><div class="sub-text">Shear (V) Actual</div><div class="big-num">{V_actual:,.0f} kg</div><div class="mini-calc">Usage: {V_actual/V_cap*100:.0f}%</div></div>""", unsafe_allow_html=True)
    with cm2: 
        st.markdown(f"""<div class="metric-box" style="border-top-color: #f39c12;"><div class="sub-text">Moment (M) Actual</div><div class="big-num">{M_actual:,.0f} kg.m</div><div class="mini-calc">Usage: {M_actual*100/M_cap*100:.0f}%</div></div>""", unsafe_allow_html=True)
    with cm3: 
        st.markdown(f"""<div class="metric-box" style="border-top-color: #27ae60;"><div class="sub-text">Deflection Actual</div><div class="big-num">{delta_actual:.2f} cm</div><div class="mini-calc">Usage: {delta_actual/delta_allow*100:.0f}%</div></div>""", unsafe_allow_html=True)

    # 4. Graph
    st.markdown("<br>", unsafe_allow_html=True)
    g_spans = np.linspace(2, 15, 100)
    g_data = [get_capacity(l) for l in g_spans]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=g_spans, y=[x[1] for x in g_data], mode='lines', name=f'{label_cap_m} Limit', line=dict(color='#f39c12', dash='dot')))
    fig.add_trace(go.Scatter(x=g_spans, y=[x[0] for x in g_data], mode='lines', name=f'{label_cap_v} Limit', line=dict(color='#e74c3c', dash='dot')))
    fig.add_trace(go.Scatter(x=g_spans, y=[x[3] for x in g_data], mode='lines', name=f'Max {label_load}', line=dict(color='#2E86C1', width=3), fill='tozeroy', fillcolor='rgba(46, 134, 193, 0.1)'))
    fig.add_trace(go.Scatter(x=[user_span], y=[user_safe_load], mode='markers', marker=dict(color='#17202a', size=14, symbol='star'), name='Design'))
    fig.update_layout(height=400, margin=dict(t=20, b=20, l=40, r=40))
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    # เรียกใช้ Module ภายนอก (Connection)
    req_bolt_result, v_bolt_result = conn.render_connection_tab(
        V_design=V_design, 
        bolt_size=bolt_size, 
        method=method, 
        is_lrfd=is_lrfd, 
        section_data=p
    )

with tab3:
    st.subheader("Reference Load Table")
    t_spans = np.arange(2, 15.5, 0.5)
    t_data = [get_capacity(l) for l in t_spans]
    df_res = pd.DataFrame({"Span (m)": t_spans, f"Max {label_load}": [x[3] for x in t_data], "Control": [x[4] for x in t_data]})
    st.dataframe(df_res.style.format("{:,.0f}", subset=[f"Max {label_load}"]), use_container_width=True)

with tab4:
    # เรียกใช้ Module ภายนอก (Report)
    # เราส่งค่าที่คำนวณจาก Main ไปให้ Report Render
    caps = {'M_cap': M_cap, 'V_cap': V_cap}
    bolt_info = {'size': bolt_size, 'capacity': v_bolt_result}
    
    rep.render_report_tab(
        method=method, 
        is_lrfd=is_lrfd, 
        sec_name=sec_name, 
        fy=fy, 
        section_data=p,
        caps=caps,
        bolt_info=bolt_info
    )
