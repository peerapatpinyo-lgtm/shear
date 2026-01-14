import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & STYLE (PREMIUM UI V12 - The Best One)
# ==========================================
st.set_page_config(page_title="Beam Insight V12 (ASD/LRFD)", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }

    /* Highlight Card (Gradient & Shadow) */
    .highlight-card { 
        background: linear-gradient(135deg, #ebf5fb 0%, #ffffff 100%);
        padding: 25px; 
        border-radius: 12px; 
        border-left: 6px solid #2e86c1; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 25px; 
    }

    /* Metric Box (Interactive Hover) */
    .metric-box { 
        text-align: center; 
        padding: 20px; 
        background: white; 
        border-radius: 12px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
        border-top: 5px solid #ccc; 
        height: 100%;
        transition: all 0.3s ease;
    }
    .metric-box:hover { transform: translateY(-5px); box-shadow: 0 12px 20px rgba(0,0,0,0.1); }
    
    .big-num { font-size: 28px; font-weight: 800; color: #17202a; margin-bottom: 5px; }
    .sub-text { font-size: 16px; font-weight: 600; color: #566573; text-transform: uppercase; }
    
    /* Notebook Style Mini Calc */
    .mini-calc {
        background-color: #f8f9fa;
        border: 1px dashed #bdc3c7;
        border-radius: 6px;
        padding: 10px;
        margin-top: 12px;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        color: #444;
        text-align: left;
        line-height: 1.6;
    }
    
    /* Paper Report Style */
    .report-paper {
        background-color: #ffffff;
        padding: 40px;
        border: 1px solid #e5e7e9;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        border-radius: 2px;
        max-width: 900px;
        margin: auto;
    }
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
    st.caption("Premium UI + ASD/LRFD")
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
# 3. CORE CALCULATION
# ==========================================
p = steel_db[sec_name]
h_cm, tw_cm = p['h']/10, p['tw']/10
Aw = h_cm * tw_cm
Ix, Zx = p['Ix'], p['Zx']

# --- SWITCH FORMULAS ---
if is_lrfd:
    phi_b = 0.90
    phi_v = 1.00
    M_cap = phi_b * fy * Zx
    V_cap = phi_v * 0.6 * fy * Aw
    label_load = "Factored Load (Wu)"
    label_cap_m = "Phi Mn"
    label_cap_v = "Phi Vn"
    bolt_factor = 1.5 
else:
    M_cap = 0.6 * fy * Zx
    V_cap = 0.4 * fy * Aw
    label_load = "Safe Load (w)"
    label_cap_m = "M allow"
    label_cap_v = "V allow"
    bolt_factor = 1.0

# Bolt Properties
dia_mm = int(bolt_size[1:])
dia_cm = dia_mm/10
b_area = 3.14 if bolt_size=="M20" else (2.01 if bolt_size=="M16" else 3.8)
v_bolt_shear_base = 1000 * b_area 
v_bolt_bear_base = 1.2 * 4000 * dia_cm * tw_cm
v_bolt = min(v_bolt_shear_base, v_bolt_bear_base) * bolt_factor

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
L_cm = user_span * 100

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
    
    # 2. Logic Source (Dynamic Text)
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
    st.markdown("#### 📊 ผลลัพธ์แรงจริง & Usage")
    cm1, cm2, cm3 = st.columns(3)
    
    shear_pct = (V_actual / V_cap) * 100
    moment_pct = ((M_actual*100) / M_cap) * 100 
    defl_pct = (delta_actual / delta_allow) * 100
    
    with cm1: 
        st.markdown(f"""
        <div class="metric-box" style="border-top-color: #e74c3c;">
            <div class="sub-text">Shear (V) Actual</div>
            <div class="big-num">{V_actual:,.0f} kg</div>
            <div class="mini-calc">
                <b>Usage ({'Vu/PhiVn' if is_lrfd else 'V/Vall'}):</b><br>
                {V_actual:,.0f} / {V_cap:,.0f}<br>
                = <b>{shear_pct:.0f}%</b>
            </div>
        </div>""", unsafe_allow_html=True)
    with cm2: 
        st.markdown(f"""
        <div class="metric-box" style="border-top-color: #f39c12;">
            <div class="sub-text">Moment (M) Actual</div>
            <div class="big-num">{M_actual:,.0f} kg.m</div>
            <div class="mini-calc">
                <b>Usage ({'Mu/PhiMn' if is_lrfd else 'M/Mall'}):</b><br>
                {M_actual:,.0f} / {M_cap:,.0f}<br>
                = <b>{moment_pct:.0f}%</b>
            </div>
        </div>""", unsafe_allow_html=True)
    with cm3: 
        st.markdown(f"""
        <div class="metric-box" style="border-top-color: #27ae60;">
            <div class="sub-text">Deflection Actual</div>
            <div class="big-num">{delta_actual:.2f} cm</div>
            <div class="mini-calc">
                <b>Usage (Act/Allow):</b><br>
                {delta_actual:.2f} / {delta_allow:.2f}<br>
                = <b>{defl_pct:.0f}%</b>
            </div>
        </div>""", unsafe_allow_html=True)

    # 4. Graph
    st.markdown("<br>", unsafe_allow_html=True)
    g_spans = np.linspace(2, 15, 100)
    g_data = [get_capacity(l) for l in g_spans]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=g_spans, y=[x[1] for x in g_data], mode='lines', name=f'{label_cap_m} Limit', line=dict(color='#f39c12', dash='dot')))
    fig.add_trace(go.Scatter(x=g_spans, y=[x[0] for x in g_data], mode='lines', name=f'{label_cap_v} Limit', line=dict(color='#e74c3c', dash='dot')))
    fig.add_trace(go.Scatter(x=g_spans, y=[x[2] for x in g_data], mode='lines', name='Defl. Limit', line=dict(color='#27ae60', dash='dot')))
    fig.add_trace(go.Scatter(x=g_spans, y=[x[3] for x in g_data], mode='lines', name=f'Max {label_load}', line=dict(color='#2E86C1', width=3), fill='tozeroy', fillcolor='rgba(46, 134, 193, 0.1)'))
    fig.add_trace(go.Scatter(x=[user_span], y=[user_safe_load], mode='markers', marker=dict(color='#17202a', size=14, symbol='star', line=dict(width=2, color='white')), name='Current Design'))
    
    fig.update_layout(
        xaxis_title="Span Length (m)", 
        yaxis_title=f"{label_load} (kg/m)", 
        height=450, 
        margin=dict(t=30, b=30, l=40, r=40),
        plot_bgcolor='white',
        xaxis=dict(showgrid=True, gridcolor='#eee'),
        yaxis=dict(showgrid=True, gridcolor='#eee'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader(f"🔩 Connection Design ({'LRFD' if is_lrfd else 'ASD'})")
    c_info, c_draw = st.columns([1, 1.5])
    with c_info:
        st.markdown(f"""<div class="conn-card"><h4 style="margin:0; color:#b7950b;">📋 Design Criteria</h4><div style="margin-top:10px;"><b>Method:</b> {method}</div><div style="margin-top:5px;"><b>Load (Vu):</b> <span style="font-size:22px; font-weight:bold; color:#d35400;">{V_design:,.0f} kg</span></div><hr><div><b>Bolt Cap ({bolt_size}):</b> {v_bolt:,.0f} kg/bolt</div><div><b>Required:</b> {V_design/v_bolt:.2f} → <b style="color:#2980b9; font-size:18px;">{req_bolt} pcs</b></div></div>""", unsafe_allow_html=True)
        status_color = "#27ae60" if layout_ok else "#c0392b"
        status_text = "PASSED" if layout_ok else "FAILED"
        st.markdown(f"""<div style="margin-top:20px; padding:15px; border-left:6px solid {status_color}; background:#f9f9f9;"><b>Layout Check:</b> <span style="color:{status_color}; font-weight:bold;">{status_text}</span></div>""", unsafe_allow_html=True)
    with c_draw:
        fig_c = go.Figure()
        fig_c.add_shape(type="rect", x0=-p['b']/2, y0=0, x1=p['b']/2, y1=p['h'], line=dict(color="RoyalBlue", width=1), fillcolor="rgba(65, 105, 225, 0.1)")
        fig_c.add_shape(type="rect", x0=-p['b']/2, y0=0, x1=p['b']/2, y1=p['tf'], fillcolor="#1f618d", line_width=0)
        fig_c.add_shape(type="rect", x0=-p['b']/2, y0=p['h']-p['tf'], x1=p['b']/2, y1=p['h'], fillcolor="#1f618d", line_width=0)
        cy = p['h'] / 2
        start_y = cy - ((n_rows-1)*pitch)/2
        gage = 60 if p['h'] < 200 else (100 if p['h'] > 400 else 80)
        bx, by = [], []
        for r in range(n_rows):
            y_pos = start_y + r*pitch
            bx.extend([-gage/2, gage/2])
            by.extend([y_pos, y_pos])
        fig_c.add_trace(go.Scatter(x=bx, y=by, mode='markers', marker=dict(size=14, color='#c0392b', line=dict(width=2, color='white')), name='Bolts'))
        fig_c.update_layout(xaxis=dict(visible=False, range=[-p['b'], p['b']]), yaxis=dict(visible=False, scaleanchor="x"), width=400, height=500, margin=dict(l=20, r=20, t=20, b=20), plot_bgcolor='white')
        st.plotly_chart(fig_c)

with tab3:
    st.subheader("Reference Load Table")
    t_spans = np.arange(2, 15.5, 0.5)
    t_data = [get_capacity(l) for l in t_spans]
    df_res = pd.DataFrame({"Span (m)": t_spans, f"Max {label_load}": [x[3] for x in t_data], "Control": [x[4] for x in t_data]})
    st.dataframe(df_res.style.format("{:,.0f}", subset=[f"Max {label_load}"]), use_container_width=True)

with tab4:
    st.markdown('<div class="report-paper">', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:right; color:#999;">METHOD: {method}</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="report-header">1. Section & Properties</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="report-line">Section: {sec_name} (Fy={fy} ksc)</div>
    <div class="report-line">Aw = {Aw:.2f} cm2, Zx = {Zx} cm3, Ix = {Ix} cm4</div>
    """, unsafe_allow_html=True)
    
    st.markdown(f'<div class="report-header">2. Capacity Calculation ({method})</div>', unsafe_allow_html=True)
    if is_lrfd:
        st.markdown(f"""
        <div class="report-line"><b>Moment (Phi Mn):</b></div>
        <div class="report-line">Phi = 0.90 (Flexure)</div>
        <div class="report-line">Phi Mn = 0.90 * Fy * Zx = 0.9 * {fy} * {Zx} = <b>{M_cap:,.0f} kg.cm</b></div>
        <br>
        <div class="report-line"><b>Shear (Phi Vn):</b></div>
        <div class="report-line">Phi = 1.00 (Shear), Vn = 0.6 Fy Aw</div>
        <div class="report-line">Phi Vn = 1.0 * 0.6 * {fy} * {Aw:.2f} = <b>{V_cap:,.0f} kg</b></div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="report-line"><b>Moment (Allowable):</b></div>
        <div class="report-line">M_all = 0.60 * Fy * Zx = 0.6 * {fy} * {Zx} = <b>{M_cap:,.0f} kg.cm</b></div>
        <br>
        <div class="report-line"><b>Shear (Allowable):</b></div>
        <div class="report-line">V_all = 0.40 * Fy * Aw = 0.4 * {fy} * {Aw:.2f} = <b>{V_cap:,.0f} kg</b></div>
        """, unsafe_allow_html=True)
        
    st.markdown('<div class="report-header">3. Bolt Capacity</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="report-line">Bolt: {bolt_size} (A325/Gr.8.8 approx)</div>
    <div class="report-line">Capacity per bolt = <b>{v_bolt:,.0f} kg</b> ({'Phi Rn' if is_lrfd else 'Rn/Omega'})</div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
