import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & STYLE
# ==========================================
st.set_page_config(page_title="Beam Insight Final Fix", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .highlight-card { background-color: #e8f6f3; padding: 20px; border-radius: 10px; border: 1px solid #1abc9c; }
    .conn-card { background-color: #fcf3cf; padding: 15px; border-radius: 8px; border: 1px solid #f1c40f; }
    .metric-box { text-align: center; padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-top: 3px solid #3498db; }
    .big-num { font-size: 24px; font-weight: bold; color: #17202a; }
    .sub-text { font-size: 14px; color: #7f8c8d; margin-top: 5px; }
    .report-line { font-family: 'Courier New', monospace; font-size: 16px; margin-bottom: 5px; }
    .report-header { font-weight: bold; font-size: 18px; margin-top: 20px; color: #2c3e50; }
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
    st.title("Beam Insight Final")
    st.caption("Clean Calculation Mode")
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

# Function to calculate capacity at any span
def get_capacity(L_m):
    L_cm = L_m * 100
    w_s = (2 * V_cap) / L_cm * 100
    w_m = (8 * M_cap) / (L_cm**2) * 100
    w_d = ((L_cm/defl_lim_val) * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100
    w_gov = min(w_s, w_m, w_d)
    cause = "Shear" if w_gov == w_s else ("Moment" if w_gov == w_m else "Deflection")
    return w_s, w_m, w_d, w_gov, cause

# 3.1 Calculate for Current User Span
_, _, _, user_safe_load, user_cause = get_capacity(user_span)
V_actual = user_safe_load * user_span / 2
M_actual = user_safe_load * user_span**2 / 8
delta_actual = (5 * (user_safe_load/100) * ((user_span*100)**4)) / (384 * E_mod * Ix)
delta_allow = (user_span*100) / defl_lim_val

# 3.2 Determine Connection Design Load
if design_mode == "Actual Load (from Span)":
    V_design = V_actual
    design_note = f"Actual Load @ Span {user_span}m"
else:
    V_design = V_cap * (target_pct / 100)
    design_note = f"Target {target_pct}% of Capacity"

req_bolt = math.ceil(V_design / v_bolt)
if req_bolt % 2 != 0: req_bolt += 1 
if req_bolt < 2: req_bolt = 2

# Layout Check
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

# --- TAB 1: BEAM ANALYSIS ---
with tab1:
    st.subheader(f"Capacity Analysis: {sec_name} @ {user_span} m.")
    cause_color = "#e74c3c" if user_cause == "Shear" else ("#f39c12" if user_cause == "Moment" else "#27ae60")
    st.markdown(f"""
    <div class="highlight-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span class="sub-text">Max Uniform Load</span><br>
                <span class="big-num" style="font-size: 36px;">{user_safe_load:,.0f}</span> <span style="font-size:20px; color:#555;">kg/m</span>
            </div>
            <div style="text-align: right;">
                <span class="sub-text">Controlled by</span><br>
                <span style="font-size: 18px; font-weight:bold; color:{cause_color};">{user_cause}</span>
            </div>
        </div>
    </div><br>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    shear_pct = (V_actual / V_cap) * 100
    moment_pct = ((M_actual*100) / M_cap) * 100 
    defl_pct = (delta_actual / delta_allow) * 100
    
    with c1: st.metric("Shear (V)", f"{V_actual:,.0f} kg", f"{shear_pct:.0f}% Used", delta_color="inverse")
    with c2: st.metric("Moment (M)", f"{M_actual:,.0f} kg.m", f"{moment_pct:.0f}% Used", delta_color="inverse")
    with c3: st.metric("Deflection", f"{delta_actual:.2f} cm", f"{defl_pct:.0f}% Used", delta_color="inverse")

    st.markdown("#### Capacity Curve")
    g_spans = np.linspace(2, 15, 100)
    g_data = [get_capacity(l) for l in g_spans]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=g_spans, y=[x[3] for x in g_data], mode='lines', name='Safe Load', fill='tozeroy'))
    fig.add_trace(go.Scatter(x=[user_span], y=[user_safe_load], mode='markers', marker=dict(color='red', size=10), name='Current'))
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: CONNECTION ---
with tab2:
    st.subheader(f"🔩 Connection: {req_bolt} x {bolt_size} Bolts")
    c_info, c_draw = st.columns([1, 1.5])
    with c_info:
        st.info(f"Design Load (Vu) = {V_design:,.0f} kg ({design_note})")
        st.write(f"Bolt Capacity = {v_bolt:,.0f} kg/bolt")
        if layout_ok:
            st.success(f"✅ Layout OK (Height: {req_height:.0f} mm)")
        else:
            st.error(f"❌ Layout Failed (Need {req_height:.0f} mm)")

# --- TAB 3: LOAD TABLE ---
with tab3:
    t_spans = np.arange(2, 12.5, 0.5)
    t_data = [get_capacity(l) for l in t_spans]
    df_res = pd.DataFrame({
        "Span (m)": t_spans, "Max Load (kg/m)": [x[3] for x in t_data], "Control": [x[4] for x in t_data]
    })
    st.dataframe(df_res, use_container_width=True)

# --- TAB 4: CALCULATION REPORT (FIXED) ---
with tab4:
    st.title("📝 Calculation Report")
    
    # 1. Section Properties
    st.markdown('<div class="report-header">1. Section Properties</div>', unsafe_allow_html=True)
    st.code(f"""
Section: {sec_name}
Aw = {h_cm} x {tw_cm} = {Aw:.2f} cm2
Zx = {Zx} cm3
Ix = {Ix} cm4
Fy = {fy} ksc
    """.strip())

    # 2. Capacity Calculations (Direct Math Format)
    st.markdown('<div class="report-header">2. Allowable Capacity</div>', unsafe_allow_html=True)
    
    st.write("**Shear Capacity (V_allow):**")
    st.code(f"= 0.4 x {fy} x {Aw:.2f} = {V_cap:,.0f} kg")
    
    st.write("**Moment Capacity (M_allow):**")
    st.code(f"= 0.6 x {fy} x {Zx} = {M_cap:,.0f} kg.cm")

    # 3. Connection Design
    st.markdown('<div class="report-header">3. Connection Design</div>', unsafe_allow_html=True)
    
    st.write(f"**Bolt Capacity ({bolt_size}):**")
    st.code(f"""
Shear   = 1000 x {b_area} = {v_bolt_shear:,.0f} kg
Bearing = 1.2 x 4000 x {dia_cm} x {tw_cm} = {v_bolt_bear:,.0f} kg
Use Min = {v_bolt:,.0f} kg/bolt
    """.strip())
    
    st.write("**Required Bolts:**")
    st.code(f"""
V_design = {V_design:,.0f} kg
Bolts    = {V_design:,.0f} / {v_bolt:,.0f} = {V_design/v_bolt:.2f}
Use      = {req_bolt} bolts
    """.strip())
