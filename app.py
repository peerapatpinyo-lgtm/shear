import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & STYLE
# ==========================================
st.set_page_config(page_title="Beam Insight V6.1 (Transparent)", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .highlight-card { background-color: #e8f6f3; padding: 20px; border-radius: 10px; border: 1px solid #1abc9c; }
    .conn-card { background-color: #fcf3cf; padding: 15px; border-radius: 8px; border: 1px solid #f1c40f; }
    .metric-box { text-align: center; padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-top: 3px solid #3498db; }
    .big-num { font-size: 24px; font-weight: bold; color: #17202a; }
    .sub-text { font-size: 14px; color: #7f8c8d; margin-top: 5px; }
    .calc-step { font-family: 'Courier New', monospace; font-size: 14px; background: #f4f6f6; padding: 10px; border-radius: 5px; margin-bottom: 5px; border-left: 4px solid #85929e;}
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
    st.title("Beam Insight V6.1")
    st.caption("Transparent Calculation Edition")
    st.divider()
    
    st.header("1. Beam Settings")
    sec_name = st.selectbox("Select Section", list(steel_db.keys()), index=5)
    user_span = st.number_input("Span Length (m)", min_value=1.0, value=6.0, step=0.5)
    fy = st.number_input("Fy (ksc)", 2400)
    defl_ratio = st.selectbox("Defl. Limit", ["L/300", "L/360", "L/400"], index=1)
    
    st.divider()
    st.header("2. Connection Settings")
    bolt_size = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)
    design_mode = st.radio("Design Basis:", ["Actual Load (from Span)", "Fixed % Capacity"])
    
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
Aw = h_cm * tw_cm # Standard assumption: d * tw
Ix, Zx = p['Ix'], p['Zx']

# Capacities
M_cap = 0.6 * fy * Zx
V_cap = 0.4 * fy * Aw 

# Bolt Properties
dia_mm = int(bolt_size[1:])
dia_cm = dia_mm/10
b_area = 3.14 if bolt_size=="M20" else (2.01 if bolt_size=="M16" else 3.8)
v_bolt_shear = 1000 * b_area 
v_bolt_bear = 1.2 * 4000 * dia_cm * tw_cm # Bearing on Web
v_bolt = min(v_bolt_shear, v_bolt_bear)

# Function
def get_capacity(L_m):
    L_cm = L_m * 100
    # Formula explanation:
    # w (kg/cm) = Load / Length
    # w (kg/m) = w(kg/cm) * 100
    
    # 1. Shear Control: w = 2V/L
    w_s_kgcm = (2 * V_cap) / L_cm
    w_s = w_s_kgcm * 100
    
    # 2. Moment Control: w = 8M/L^2
    w_m_kgcm = (8 * M_cap) / (L_cm**2)
    w_m = w_m_kgcm * 100
    
    # 3. Deflection Control: w = (Delta * 384EI) / (5L^4)
    delta_target = L_cm / defl_lim_val
    w_d_kgcm = (delta_target * 384 * E_mod * Ix) / (5 * (L_cm**4))
    w_d = w_d_kgcm * 100
    
    w_gov = min(w_s, w_m, w_d)
    cause = "Shear" if w_gov == w_s else ("Moment" if w_gov == w_m else "Deflection")
    return w_s, w_m, w_d, w_gov, cause

# Current State Calc
w_shear_limit, w_moment_limit, w_defl_limit, user_safe_load, user_cause = get_capacity(user_span)
V_actual = user_safe_load * user_span / 2
M_actual = user_safe_load * user_span**2 / 8
# Recalculate Delta Actual for display
# Delta = 5wL^4 / 384EI. Note: w must be kg/cm here. So user_safe_load/100
delta_actual = (5 * (user_safe_load/100) * ((user_span*100)**4)) / (384 * E_mod * Ix)
delta_allow = (user_span*100) / defl_lim_val

# Connection Calc
if design_mode == "Actual Load (from Span)":
    V_design = V_actual
    design_usage = (V_actual / V_cap) * 100
    design_basis_txt = f"Actual Shear @ L={user_span}m"
else:
    V_design = V_cap * (target_pct / 100)
    design_usage = target_pct
    design_basis_txt = f"Fixed Target ({target_pct}% of Capacity)"

req_bolt = math.ceil(V_design / v_bolt)
if req_bolt % 2 != 0: req_bolt += 1 
if req_bolt < 2: req_bolt = 2

# Layout Check
n_cols = 2
n_rows = int(req_bolt / 2)
pitch = 3 * dia_mm
edge_dist = 1.5 * dia_mm
req_height = (n_rows - 1) * pitch + 2 * edge_dist
avail_height = p['h'] - 2*p['tf'] - 20 # approx fillet
layout_ok = req_height <= avail_height

# ==========================================
# 4. UI DISPLAY
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 Beam Analysis", "🔩 Connection Detail", "💾 Load Table"])

# --- TAB 1: BEAM ANALYSIS ---
with tab1:
    st.subheader(f"Capacity Analysis: {sec_name} @ {user_span} m.")
    
    # [Top Section: Same as before]
    cause_color = "#e74c3c" if user_cause == "Shear" else ("#f39c12" if user_cause == "Moment" else "#27ae60")
    st.markdown(f"""
    <div class="highlight-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span class="sub-text">Max Safe Uniform Load (Total)</span><br>
                <span class="big-num" style="font-size: 36px;">{user_safe_load:,.0f}</span> <span style="font-size:20px; color:#555;">kg/m</span>
            </div>
            <div style="text-align: right;">
                <span class="sub-text">Controlled by</span><br>
                <span style="font-size: 18px; font-weight:bold; color:{cause_color};">{user_cause}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    shear_pct = (V_actual / V_cap) * 100
    moment_pct = ((M_actual*100) / M_cap) * 100
    defl_pct = (delta_actual / delta_allow) * 100
    
    with c1: st.markdown(f"""<div class="metric-box" style="border-top-color: #e74c3c;"><div class="sub-text">Shear (V)</div><div class="big-num">{V_actual:,.0f} kg</div><div class="sub-text">Usage: <b>{shear_pct:.0f}%</b></div><div style="background:#eee; height:6px; width:100%; margin-top:5px;"><div style="background:#e74c3c; width:{shear_pct}%; height:100%;"></div></div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="metric-box" style="border-top-color: #f39c12;"><div class="sub-text">Moment (M)</div><div class="big-num">{M_actual:,.0f} kg.m</div><div class="sub-text">Usage: <b>{moment_pct:.0f}%</b></div><div style="background:#eee; height:6px; width:100%; margin-top:5px;"><div style="background:#f39c12; width:{moment_pct}%; height:100%;"></div></div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="metric-box" style="border-top-color: #27ae60;"><div class="sub-text">Deflection</div><div class="big-num">{delta_actual:.2f} cm</div><div class="sub-text">Usage: <b>{defl_pct:.0f}%</b></div><div style="background:#eee; height:6px; width:100%; margin-top:5px;"><div style="background:#27ae60; width:{min(defl_pct,100)}%; height:100%;"></div></div></div>""", unsafe_allow_html=True)

    # Graph (Compact)
    st.markdown("#### 📈 Capacity Curve")
    g_spans = np.linspace(2, 15, 100)
    g_data = [get_capacity(l) for l in g_spans]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=g_spans, y=[x[3] for x in g_data], mode='lines', name='Safe Load', line=dict(color='#2E86C1', width=3), fill='tozeroy'))
    fig.add_trace(go.Scatter(x=[user_span], y=[user_safe_load], mode='markers', marker=dict(color='red', size=10)))
    fig.update_layout(xaxis_title="Span (m)", yaxis_title="Load (kg/m)", height=300, margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig, use_container_width=True)

    # ================= DETAIL CALCULATION (STEP-BY-STEP) =================
    st.markdown("---")
    with st.expander("📝 Show Calculation Steps (Why do I get these numbers?)", expanded=True):
        st.markdown(f"""
        **1. Beam Parameters ({sec_name})**
        * $F_y = {fy}$ ksc, $E = {E_mod:,.0f}$ ksc
        * $A_w = h \\times t_w = {h_cm} \\times {tw_cm} = {Aw:.2f}$ cm² (Using total depth)
        * $Z_x = {Zx}$ cm³, $I_x = {Ix}$ cm⁴
        * Allowable Shear ($V_a$) = $0.4 F_y A_w = 0.4 \\times {fy} \\times {Aw:.2f} = \\mathbf{{{V_cap:,.0f}}}$ kg
        * Allowable Moment ($M_a$) = $0.6 F_y Z_x = 0.6 \\times {fy} \\times {Zx} = \\mathbf{{{M_cap:,.0f}}}$ kg.cm
        
        **2. Safe Load Calculation (at L = {user_span} m)**
        Convert L to cm: $L = {user_span} \\times 100 = {user_span*100}$ cm
        
        **Case A: Shear Limit** ($w = 2V/L$)
        > $w = \\frac{{2 \\times {V_cap:,.0f}}}{{{user_span*100}}} = {2*V_cap/(user_span*100):.2f}$ kg/cm
        > Convert to kg/m: ${2*V_cap/(user_span*100):.2f} \\times 100 = \\mathbf{{{w_shear_limit:,.0f}}}$ kg/m
        
        **Case B: Moment Limit** ($w = 8M/L^2$)
        > $w = \\frac{{8 \\times {M_cap:,.0f}}}{{{(user_span*100)}^2}} = {8*M_cap/((user_span*100)**2):.2f}$ kg/cm
        > Convert to kg/m: ${8*M_cap/((user_span*100)**2):.2f} \\times 100 = \\mathbf{{{w_moment_limit:,.0f}}}$ kg/m
        
        **Case C: Deflection Limit** (Limit = L/{defl_lim_val} = {delta_allow:.2f} cm)
        > $w = \\frac{{\\Delta \\cdot 384EI}}{{5L^4}} = \\frac{{{delta_allow:.2f} \\cdot 384 \\cdot {E_mod:,.0f} \\cdot {Ix}}}{{5 \\cdot {user_span*100}^4}} = {w_defl_limit/100:.2f}$ kg/cm
        > Convert to kg/m: ${w_defl_limit/100:.2f} \\times 100 = \\mathbf{{{w_defl_limit:,.0f}}}$ kg/m
        
        **Conclusion:**
        The lowest value controls: **{min(w_shear_limit, w_moment_limit, w_defl_limit):,.0f} kg/m**
        """)

# --- TAB 2: CONNECTION ---
with tab2:
    st.subheader(f"🔩 Connection Design ({bolt_size})")
    
    # [Main Section: Same as before]
    c_info, c_draw = st.columns([1, 1.5])
    with c_info:
        st.markdown(f"""
        <div class="conn-card">
            <h4 style="margin:0; color:#b7950b;">📋 Design Criteria</h4>
            <div style="margin-top:10px;"><b>Basis:</b> {design_basis_txt}</div>
            <div style="margin-top:5px;"><b>Design Shear (Vu):</b> <span style="font-size:20px; font-weight:bold; color:#d35400;">{V_design:,.0f} kg</span></div>
            <hr>
            <div><b>Single Bolt Cap:</b> {v_bolt:,.0f} kg</div>
            <div><b>Required:</b> <b style="color:blue;">{req_bolt} pcs</b></div>
        </div>
        """, unsafe_allow_html=True)
        status_color = "green" if layout_ok else "red"
        st.markdown(f"<div style='margin-top:10px; color:{status_color}; font-weight:bold;'>Layout Check: {'OK' if layout_ok else 'FAILED'}</div>", unsafe_allow_html=True)

    with c_draw:
        fig_c = go.Figure()
        # Shapes
        fig_c.add_shape(type="rect", x0=-p['b']/2, y0=0, x1=p['b']/2, y1=p['h'], line=dict(color="RoyalBlue"), fillcolor="rgba(173, 216, 230, 0.2)")
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
        fig_c.update_layout(title="Front View Layout", xaxis=dict(visible=False, range=[-p['b'], p['b']]), yaxis=dict(visible=False, scaleanchor="x"), width=350, height=450, margin=dict(l=20, r=20, t=30, b=20), plot_bgcolor='white')
        st.plotly_chart(fig_c)

    # ================= DETAIL CALCULATION (TAB 2) =================
    st.markdown("---")
    with st.expander("📝 Bolt Capacity Check", expanded=True):
        st.markdown(f"""
        **1. Bolt Area ($A_b$)**
        Using {bolt_size} (Diameter {dia_mm} mm):
        $A_b = \\frac{{\\pi \\cdot {dia_cm}^2}}{{4}} \\approx {b_area}$ cm²
        
        **2. Shear Capacity ($R_v$)**
        Using $F_v \\approx 1000$ ksc (Grade 8.8):
        $R_v = 1000 \\times {b_area} = \\mathbf{{{v_bolt_shear:,.0f}}}$ kg
        
        **3. Bearing Capacity ($R_b$)**
        Using $F_b \\approx 4800$ ksc on Web $t_w = {tw_cm}$ cm:
        $R_b = 4800 \\times {dia_cm} \\times {tw_cm} = \\mathbf{{{v_bolt_bear:,.0f}}}$ kg
        
        **4. Conclusion**
        Use min value: **{v_bolt:,.0f} kg/bolt**
        """)

# --- TAB 3: LOAD TABLE ---
with tab3:
    st.subheader("Reference Load Table")
    t_spans = np.arange(2, 15.5, 0.5)
    t_data = [get_capacity(l) for l in t_spans]
    df_res = pd.DataFrame({
        "Span (m)": t_spans,
        "Max Load (kg/m)": [x[3] for x in t_data],
        "Limited By": [x[4] for x in t_data],
        "V_actual (kg)": [x[3]*l/2 for l, x in zip(t_spans, t_data)],
        "Shear Usage (%)": [(x[3]*l/2 / V_cap)*100 for l, x in zip(t_spans, t_data)]
    })
    st.dataframe(df_res.style.format("{:.1f}", subset=["Span (m)", "Shear Usage (%)"]).format("{:,.0f}", subset=["Max Load (kg/m)", "V_actual (kg)"]), use_container_width=True, height=500)
