import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & STYLE
# ==========================================
st.set_page_config(page_title="Beam Insight V8", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .highlight-card { background-color: #e8f6f3; padding: 20px; border-radius: 10px; border: 1px solid #1abc9c; margin-bottom: 20px; }
    .conn-card { background-color: #fcf3cf; padding: 15px; border-radius: 8px; border: 1px solid #f1c40f; }
    .metric-box { text-align: center; padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-top: 3px solid #3498db; }
    .big-num { font-size: 36px; font-weight: bold; color: #17202a; }
    .sub-text { font-size: 14px; color: #7f8c8d; margin-top: 5px; }
    .calc-box { font-family: 'Sarabun', sans-serif; font-size: 16px; background-color: #ffffff; padding: 10px; border-radius: 5px; border-left: 4px solid #3498db; margin-top: 10px; }
    .report-header { font-size: 18px; font-weight: bold; color: #2c3e50; margin-top: 20px; border-bottom: 2px solid #ddd; padding-bottom: 5px; }
    .report-line { font-family: 'Courier New', monospace; font-size: 16px; margin-bottom: 5px; color: #333; }
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
    st.title("Beam Insight V8")
    st.caption("Final Polish")
    st.divider()
    
    st.header("1. Beam Settings")
    sec_name = st.selectbox("Select Section", list(steel_db.keys()), index=5)
    user_span = st.number_input("Span Length (m)", min_value=1.0, value=6.0, step=0.5)
    fy = st.number_input("Fy (ksc)", 2400)
    defl_ratio = st.selectbox("Defl. Limit", ["L/300", "L/360", "L/400"], index=1)
    
    st.divider()
    st.header("2. Connection Settings")
    bolt_size = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)
    design_mode = st.radio("Design Connection Based on:", 
                           ["Actual Load (from Span)", "Fixed % Capacity (Standard)"])
    
    if design_mode == "Fixed % Capacity (Standard)":
        target_pct = st.slider("Target % Usage", 50, 100, 75, 5)
    else:
        target_pct = None

    E_mod = 2.04e6 
    defl_lim_val = int(defl_ratio.split("/")[1])

# ==========================================
# 3. CORE CALCULATION
# ==========================================
p = steel_db[sec_name]
h_cm, tw_cm = p['h']/10, p['tw']/10
Aw = h_cm * tw_cm
Ix, Zx = p['Ix'], p['Zx']

# Capacities
M_cap = 0.6 * fy * Zx
V_cap = 0.4 * fy * Aw 

# Bolt Properties
dia_mm = int(bolt_size[1:])
dia_cm = dia_mm/10
b_area = 3.14 if bolt_size=="M20" else (2.01 if bolt_size=="M16" else 3.8)
v_bolt_shear = 1000 * b_area 
v_bolt_bear = 1.2 * 4000 * dia_cm * tw_cm
v_bolt = min(v_bolt_shear, v_bolt_bear)

def get_capacity(L_m):
    L_cm = L_m * 100
    w_s = (2 * V_cap) / L_cm * 100
    w_m = (8 * M_cap) / (L_cm**2) * 100
    w_d = ((L_cm/defl_lim_val) * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100
    w_gov = min(w_s, w_m, w_d)
    cause = "Shear" if w_gov == w_s else ("Moment" if w_gov == w_m else "Deflection")
    return w_s, w_m, w_d, w_gov, cause

# Analysis Current Span
w_shear, w_moment, w_defl, user_safe_load, user_cause = get_capacity(user_span)
V_actual = user_safe_load * user_span / 2
M_actual = user_safe_load * user_span**2 / 8
delta_actual = (5 * (user_safe_load/100) * ((user_span*100)**4)) / (384 * E_mod * Ix)
delta_allow = (user_span*100) / defl_lim_val

# Connection Design
if design_mode == "Actual Load (from Span)":
    V_design = V_actual
    design_note = f"Actual Load @ {user_span}m"
    design_usage = (V_actual / V_cap) * 100
else:
    V_design = V_cap * (target_pct / 100)
    design_note = f"Target {target_pct}% Capacity"
    design_usage = target_pct

req_bolt = math.ceil(V_design / v_bolt)
if req_bolt % 2 != 0: req_bolt += 1 
if req_bolt < 2: req_bolt = 2

# Layout
n_cols = 2
n_rows = int(req_bolt / 2)
pitch = 3 * dia_mm
edge_dist = 1.5 * dia_mm
req_height = (n_rows - 1) * pitch + 2 * edge_dist
avail_height = p['h'] - 2*p['tf'] - 20
layout_ok = req_height <= avail_height

# ==========================================
# 4. UI DISPLAY
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Beam Analysis", "🔩 Connection Detail", "💾 Load Table", "📝 Calculation Report"])

# --- TAB 1: BEAM ANALYSIS (เพิ่มที่มาของค่า) ---
with tab1:
    st.subheader(f"Capacity Analysis: {sec_name} @ {user_span} m.")
    
    cause_color = "#e74c3c" if user_cause == "Shear" else ("#f39c12" if user_cause == "Moment" else "#27ae60")
    
    # 1. Main Card with Calculation Source
    st.markdown(f"""
    <div class="highlight-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span class="sub-text">Max Uniform Load (w)</span><br>
                <span class="big-num">{user_safe_load:,.0f}</span> <span style="font-size:24px; color:#555;">kg/m</span>
            </div>
            <div style="text-align: right;">
                <span class="sub-text">Limited by</span><br>
                <span style="font-size: 20px; font-weight:bold; color:{cause_color};">{user_cause}</span>
            </div>
        </div>
        <hr style="margin:10px 0; border-top: 1px dashed #bbb;">
        <div style="font-size:14px; color:#333;">
            <b>🕵️‍♂️ ที่มาของค่า (Calculation Source):</b><br>
            <i>คิดจากเงื่อนไขที่รับน้ำหนักได้น้อยที่สุด (Governing Case):</i><br>
    """, unsafe_allow_html=True)
    
    # แสดงการคำนวณของ Case ที่ควบคุม (Governing Case)
    L_cm = user_span * 100
    if user_cause == "Shear":
        # w = 2V/L
        st.code(f"w = 2 * V_cap / L\n  = 2 * {V_cap:,.0f} / {L_cm}\n  = {w_shear:,.0f} kg/m")
    elif user_cause == "Moment":
        # w = 8M/L^2
        st.code(f"w = 8 * M_cap / L^2\n  = 8 * {M_cap:,.0f} / {L_cm}^2\n  = {w_moment:,.0f} kg/m")
    else:
        # w = Delta * ...
        st.code(f"w = (Delta * 384 * E * I) / (5 * L^4)\n  = ({L_cm/defl_lim_val:.2f} * 384 * {E_mod:.0e} * {Ix}) / (5 * {L_cm}^4)\n  = {w_defl:,.0f} kg/m")
        
    st.markdown("</div></div>", unsafe_allow_html=True)

    # 2. Metrics
    c1, c2, c3 = st.columns(3)
    shear_pct = (V_actual / V_cap) * 100
    moment_pct = ((M_actual*100) / M_cap) * 100 
    defl_pct = (delta_actual / delta_allow) * 100
    
    with c1: st.markdown(f"""<div class="metric-box" style="border-top-color: #e74c3c;"><div class="sub-text">Shear (V)</div><div class="big-num" style="font-size:24px;">{V_actual:,.0f} kg</div><div class="sub-text">Usage: <b>{shear_pct:.0f}%</b></div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="metric-box" style="border-top-color: #f39c12;"><div class="sub-text">Moment (M)</div><div class="big-num" style="font-size:24px;">{M_actual:,.0f} kg.m</div><div class="sub-text">Usage: <b>{moment_pct:.0f}%</b></div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="metric-box" style="border-top-color: #27ae60;"><div class="sub-text">Deflection</div><div class="big-num" style="font-size:24px;">{delta_actual:.2f} cm</div><div class="sub-text">Usage: <b>{defl_pct:.0f}%</b></div></div>""", unsafe_allow_html=True)

    # 3. Graph
    st.markdown("#### 📈 Capacity Curve")
    g_spans = np.linspace(2, 15, 100)
    g_data = [get_capacity(l) for l in g_spans]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=g_spans, y=[x[1] for x in g_data], mode='lines', name='Moment Limit', line=dict(color='orange', dash='dot')))
    fig.add_trace(go.Scatter(x=g_spans, y=[x[0] for x in g_data], mode='lines', name='Shear Limit', line=dict(color='red', dash='dot')))
    fig.add_trace(go.Scatter(x=g_spans, y=[x[2] for x in g_data], mode='lines', name='Defl. Limit', line=dict(color='green', dash='dot')))
    fig.add_trace(go.Scatter(x=g_spans, y=[x[3] for x in g_data], mode='lines', name='Safe Load', line=dict(color='#2E86C1', width=3), fill='tozeroy', fillcolor='rgba(46, 134, 193, 0.1)'))
    fig.add_trace(go.Scatter(x=[user_span], y=[user_safe_load], mode='markers', marker=dict(color='black', size=12, symbol='star'), name='Selected'))
    fig.update_layout(xaxis_title="Span (m)", yaxis_title="Load (kg/m)", height=400, margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: CONNECTION (กู้คืนกราฟิก) ---
with tab2:
    st.subheader(f"🔩 Connection Design ({bolt_size})")
    c_info, c_draw = st.columns([1, 1.5])
    with c_info:
        st.markdown(f"""<div class="conn-card"><h4 style="margin:0; color:#b7950b;">📋 Design Criteria</h4><div style="margin-top:10px;"><b>Mode:</b> {design_mode}</div><div style="margin-top:5px;"><b>Design Shear (Vu):</b> <span style="font-size:20px; font-weight:bold; color:#d35400;">{V_design:,.0f} kg</span></div><div style="font-size:14px; color:#555;">(Equivalent to {design_usage:.1f}% of Section Capacity)</div><hr><div><b>Single Bolt Cap ({bolt_size}):</b> {v_bolt:,.0f} kg</div><div><b>Required Bolts:</b> {V_design/v_bolt:.2f} → <b style="color:blue;">{req_bolt} pcs</b></div></div>""", unsafe_allow_html=True)
        status_color = "green" if layout_ok else "red"
        status_text = "PASSED" if layout_ok else "FAILED"
        st.markdown(f"""<div style="margin-top:20px; padding:10px; border-left:5px solid {status_color}; background:#eee;"><b>Layout Check:</b> <span style="color:{status_color}; font-weight:bold;">{status_text}</span><br><small>Requires {req_height:.0f} mm space (Available {avail_height:.0f} mm)</small></div>""", unsafe_allow_html=True)

    with c_draw:
        # กู้คืนส่วนวาดรูป (Drawing Logic)
        fig_c = go.Figure()
        # Web
        fig_c.add_shape(type="rect", x0=-p['b']/2, y0=0, x1=p['b']/2, y1=p['h'], line=dict(color="RoyalBlue"), fillcolor="rgba(173, 216, 230, 0.2)")
        # Flanges
        fig_c.add_shape(type="rect", x0=-p['b']/2, y0=0, x1=p['b']/2, y1=p['tf'], fillcolor="RoyalBlue", line_width=0)
        fig_c.add_shape(type="rect", x0=-p['b']/2, y0=p['h']-p['tf'], x1=p['b']/2, y1=p['h'], fillcolor="RoyalBlue", line_width=0)
        
        # Bolts
        cy = p['h'] / 2
        start_y = cy - ((n_rows-1)*pitch)/2
        gage = 60 if p['h'] < 200 else (100 if p['h'] > 400 else 80)
        
        bx, by = [], []
        for r in range(n_rows):
            y_pos = start_y + r*pitch
            bx.extend([-gage/2, gage/2])
            by.extend([y_pos, y_pos])
            
        fig_c.add_trace(go.Scatter(x=bx, y=by, mode='markers', marker=dict(size=14, color='#e74c3c', line=dict(width=2, color='black')), name='Bolts'))
        fig_c.update_layout(title="Front View Layout", xaxis=dict(visible=False, range=[-p['b'], p['b']]), yaxis=dict(visible=False, scaleanchor="x"), width=400, height=500, margin=dict(l=20, r=20, t=30, b=20), plot_bgcolor='white')
        st.plotly_chart(fig_c)

# --- TAB 3: LOAD TABLE ---
with tab3:
    st.subheader("Reference Load Table")
    t_spans = np.arange(2, 15.5, 0.5)
    t_data = [get_capacity(l) for l in t_spans]
    df_res = pd.DataFrame({"Span (m)": t_spans, "Max Load (kg/m)": [x[3] for x in t_data], "Limited By": [x[4] for x in t_data]})
    st.dataframe(df_res.style.format("{:,.0f}", subset=["Max Load (kg/m)"]), use_container_width=True)

# --- TAB 4: CALCULATION REPORT (Plain Text Mode) ---
with tab4:
    st.markdown('<div class="report-header">1. Section Properties</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="report-line">Section: {sec_name}</div>
    <div class="report-line">Aw = {h_cm:.1f} x {tw_cm:.1f} = {Aw:.2f} cm2</div>
    <div class="report-line">Zx = {Zx} cm3, Ix = {Ix} cm4</div>
    <div class="report-line">Fy = {fy} ksc, Fu = 4000 ksc</div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="report-header">2. Allowable Capacity</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="report-line"><b>Shear Capacity (V_allow):</b></div>
    <div class="report-line">= 0.4 x {fy} x {Aw:.2f} = {V_cap:,.0f} kg</div>
    <br>
    <div class="report-line"><b>Moment Capacity (M_allow):</b></div>
    <div class="report-line">= 0.6 x {fy} x {Zx} = {M_cap:,.0f} kg.cm</div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="report-header">3. Connection Design</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="report-line"><b>Bolt Capacity ({bolt_size}):</b></div>
    <div class="report-line">- Shear = 1000 x {b_area} = {v_bolt_shear:,.0f} kg</div>
    <div class="report-line">- Bearing = 1.2 x 4000 x {dia_cm} x {tw_cm} = {v_bolt_bear:,.0f} kg</div>
    <div class="report-line"><b>=> Use Min = {v_bolt:,.0f} kg/bolt</b></div>
    <hr>
    <div class="report-line"><b>Required Bolts:</b></div>
    <div class="report-line">V_design = {V_design:,.0f} kg</div>
    <div class="report-line">Bolts = {V_design:,.0f} / {v_bolt:,.0f} = {V_design/v_bolt:.2f}</div>
    <div class="report-line"><b>=> Use {req_bolt} bolts</b></div>
    """, unsafe_allow_html=True)
