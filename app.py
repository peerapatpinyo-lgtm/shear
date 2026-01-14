import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & STYLE
# ==========================================
st.set_page_config(page_title="Structural Engineer's Companion", layout="wide", page_icon="👷‍♂️")

st.markdown("""
<style>
    .report-box { border: 1px solid #ddd; padding: 25px; background-color: #f9f9f9; font-family: 'Courier New', monospace; white-space: pre-wrap; }
    .status-pass { color: green; font-weight: bold; }
    .status-fail { color: red; font-weight: bold; }
    .warning-box { background-color: #fff3cd; color: #856404; padding: 10px; border-radius: 5px; border-left: 5px solid #ffeeba; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE & ENGINEERING PROPS
# ==========================================
# Properties needed: h, b, tw, tf, Ix, Zx, ry (radius of gyration y - important for LTB)
steel_db = {
    # Name: {dims..., props..., ry (cm)}
    "H 150x75x5x7":     {"h": 150, "b": 75,  "tw": 5,   "tf": 7,   "Ix": 666,    "Zx": 88.8,  "ry": 1.66, "w": 14.0},
    "H 200x100x5.5x8": {"h": 200, "b": 100, "tw": 5.5, "tf": 8,   "Ix": 1840,   "Zx": 184,   "ry": 2.22, "w": 21.3},
    "H 250x125x6x9":    {"h": 250, "b": 125, "tw": 6,   "tf": 9,   "Ix": 3690,   "Zx": 295,   "ry": 2.79, "w": 29.6},
    "H 300x150x6.5x9": {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481,   "ry": 3.29, "w": 36.7},
    "H 350x175x7x11":  {"h": 350, "b": 175, "tw": 7,   "tf": 11,  "Ix": 13600,  "Zx": 775,   "ry": 3.86, "w": 49.6},
    "H 400x200x8x13":  {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190,  "ry": 4.54, "w": 66.0},
    "H 450x200x9x14":  {"h": 450, "b": 200, "tw": 9,   "tf": 14,  "Ix": 33500,  "Zx": 1490,  "ry": 4.43, "w": 76.0},
    "H 500x200x10x16": {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910,  "ry": 4.33, "w": 89.6},
}

# ==========================================
# 3. SIDEBAR CONTROLS
# ==========================================
with st.sidebar:
    st.header("⚙️ Design Parameters")
    
    # Section
    sec_name = st.selectbox("Section", list(steel_db.keys()), index=3)
    p = steel_db[sec_name]
    
    st.divider()
    
    # Loads & Span
    span_L = st.number_input("Beam Span (m)", value=6.0, step=0.5)
    
    # 🌟 NEW: Unbraced Length Input (Real Engineering)
    st.markdown("**🛡️ Stability (Bracing)**")
    bracing_cond = st.radio("Lateral Bracing:", ["Fully Braced (L_b = 0)", "Ends Only (L_b = L)", "Mid-Point (L_b = L/2)"])
    
    if bracing_cond == "Fully Braced (L_b = 0)": Lb = 0
    elif bracing_cond == "Ends Only (L_b = L)": Lb = span_L
    else: Lb = span_L / 2
    
    st.divider()
    bolt_size = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)
    
    fy = 2400 # ksc
    E = 2.04e6 # ksc

# ==========================================
# 4. ENGINEERING CALCULATIONS (THE ENGINE)
# ==========================================

# 4.1 Section Classification (Compact Check)
# Limit for Flange (SS400): b/2tf <= 15.8 (Example check)
b_2tf = (p['b']/10) / (2 * p['tf']/10)
compact_status = "Compact" if b_2tf < 15.8 else "Non-Compact"

# 4.2 Allowable Bending Stress (Fb) Calculation with LTB
# Basic ASD Method (Simulated logic for demo)
# Lc (Critical Length) ~ 200 * b / sqrt(Fy) approx for logic visualization
Lc_val = (200 * (p['b']/10)) / math.sqrt(fy) # cm (Simplified rule)
Lb_cm = Lb * 100

if Lb_cm <= Lc_val:
    Fb = 0.6 * fy # Full capacity
    ltb_note = "Compact & Braced (Full Fb)"
else:
    # Reduction for LTB (Simplified Linear Reduction for Demo)
    # Real formula involves Cb and rT, here we use a simplified reduction factor
    reduction_factor = max(0.6, 1.0 - (0.002 * (Lb_cm/p['ry']))) 
    Fb = 0.6 * fy * reduction_factor
    ltb_note = f"⚠️ Reduced Capacity (LTB governs, factor={reduction_factor:.2f})"

# 4.3 Capacities
M_cap = Fb * p['Zx'] # kg.cm
V_cap = 0.4 * fy * (p['h']/10 * p['tw']/10) # kg

# 4.4 Allowable Load (w_allow)
# From Moment
w_moment = (8 * M_cap) / ((span_L*100)**2) * 100 # kg/m
# From Shear
w_shear = (2 * V_cap) / (span_L*100) * 100 # kg/m
# From Deflection (L/360)
delta_limit = (span_L*100) / 360
w_defl = (delta_limit * 384 * E * p['Ix']) / (5 * (span_L*100)**4) * 100 # kg/m

# Governing Load
w_safe = min(w_moment, w_shear, w_defl)
gov_case = "Moment" if w_safe == w_moment else ("Shear" if w_safe == w_shear else "Deflection")

# 4.5 Bolt Calculation
reaction = w_safe * span_L / 2
d_bolt = int(bolt_size[1:])/10
area_bolt = 3.14 * (d_bolt/2)**2
v_bolt = min(1000*area_bolt, 1.2*4000*d_bolt*(p['tw']/10))
n_bolts = math.ceil(reaction / v_bolt)

# ==========================================
# 5. UI: DESIGN STUDIO
# ==========================================
st.title("🏗️ Structural Beam Analysis (ASD)")

tab_main, tab_calc, tab_detail = st.tabs(["📊 Analysis Dashboard", "📝 Calculation Sheet", "📐 Connection Detail"])

with tab_main:
    # Summary Cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Section", sec_name, f"{p['w']} kg/m")
    c2.metric("Safe Load (w)", f"{w_safe:,.0f} kg/m", f"Gov: {gov_case}")
    c3.metric("Reaction (R)", f"{reaction:,.0f} kg", f"{n_bolts} x {bolt_size}")
    
    if Lb_cm > Lc_val:
        c4.markdown(f"**⚠️ Stability Issue**")
        c4.caption(f"Unbraced Lb = {Lb:.2f} m")
        c4.markdown(f"<span style='color:red'>Capacity Reduced</span>", unsafe_allow_html=True)
    else:
        c4.metric("Stability", "OK", "Fully Braced")

    st.divider()
    
    # Comparison Chart (Span vs Load)
    col_chart, col_info = st.columns([2, 1])
    
    with col_chart:
        st.subheader("Performance Curve")
        spans_plot = np.linspace(2, 15, 50)
        loads_plot = []
        for l in spans_plot:
            # Simple M limit logic for plot
            wm = (8 * M_cap) / ((l*100)**2) * 100
            ws = (2 * V_cap) / (l*100) * 100
            wd = (((l*100)/360) * 384 * E * p['Ix']) / (5 * (l*100)**4) * 100
            loads_plot.append(min(wm, ws, wd))
            
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=spans_plot, y=loads_plot, fill='tozeroy', name='Safe Load', line=dict(color='#2980b9')))
        fig.add_trace(go.Scatter(x=[span_L], y=[w_safe], mode='markers', marker=dict(size=12, color='red'), name='Current Design'))
        
        fig.update_layout(xaxis_title="Span (m)", yaxis_title="Safe Load (kg/m)", height=400, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True)
        
    with col_info:
        st.subheader("💡 Engineer's Note")
        st.info(f"""
        **1. Compactness Check:**
        * Flange: {b_2tf:.1f} < 15.8 ({compact_status})
        
        **2. Stability Check (LTB):**
        * Unbraced Length ($L_b$): {Lb:.2f} m
        * Status: {ltb_note}
        
        **3. Deflection Check:**
        * Allowable: {delta_limit:.2f} cm (L/360)
        """)

# ==========================================
# 6. UI: CALCULATION SHEET (The Real Deal)
# ==========================================
with tab_calc:
    st.subheader("📄 Design Calculation Report")
    st.caption("Copy ข้อความนี้ไปแปะในรายงานได้เลย")
    
    report_text = f"""
PROJECT: STRUCTURAL DESIGN REPORT
SUBJECT: BEAM DESIGN & CONNECTION CHECK ({sec_name})
CODE: ASD (EIT Standard / AISC)
------------------------------------------------------------
1. DESIGN PARAMETERS
   Section      : {sec_name}
   Span Length  : {span_L:.2f} m
   Steel Grade  : SS400 (Fy = {fy} ksc, Fu = 4000 ksc)
   Bolt Grade   : A325 / F10T (Assuming Shear = 1.0 t/cm2)
   Bolt Size    : {bolt_size} (Dia = {d_bolt} cm)

2. SECTION PROPERTIES
   Depth (h)    : {p['h']} mm
   Web (tw)     : {p['tw']} mm
   Zx           : {p['Zx']} cm3
   Ix           : {p['Ix']} cm4
   Compact Check: {compact_status}

3. ALLOWABLE STRESS CALCULATION
   Unbraced Length (Lb) : {Lb:.2f} m
   Allowable Bending (Fb) : {Fb:,.0f} ksc  [{ltb_note}]
   Allowable Shear (Fv)   : {0.4*fy:,.0f} ksc

4. LOAD CAPACITY ANALYSIS
   Moment Capacity (M_all) : {M_cap/100:,.2f} kg.m
   Shear Capacity (V_all)  : {V_cap:,.0f} kg
   
   SAFE UNIFORM LOAD (w):
   a) Based on Moment     : {w_moment:,.0f} kg/m
   b) Based on Shear      : {w_shear:,.0f} kg/m
   c) Based on Deflection : {w_defl:,.0f} kg/m (Limit L/360)
   
   >>> GOVERNING LOAD     : {w_safe:,.0f} kg/m (Controlled by {gov_case})

5. CONNECTION DESIGN (SHEAR)
   End Reaction (R)       : {reaction:,.0f} kg
   Bolt Shear Capacity    : {v_bolt:,.0f} kg/bolt
   Bolts Required         : {reaction} / {v_bolt} = {reaction/v_bolt:.2f}
   
   >>> USE                : {n_bolts} x {bolt_size}
   
   *Check Detailing:
   - Pitch (3d)           : {3*d_bolt*10:.0f} mm
   - Edge Dist (1.5d)     : {1.5*d_bolt*10:.0f} mm
------------------------------------------------------------
ENGINEER'S SIGNATURE: __________________________
    """
    st.text_area("Calculation Output", report_text, height=600)

# ==========================================
# 7. UI: DETAIL CHECK
# ==========================================
with tab_detail:
    st.subheader("📐 Standard Detailing Requirements")
    col_d1, col_d2 = st.columns(2)
    
    dia_mm = int(bolt_size[1:])
    min_pitch = 3 * dia_mm
    min_edge = 1.5 * dia_mm
    plate_t = max(9, math.ceil(p['tw']))
    
    with col_d1:
        st.markdown(f"""
        **สำหรับ {bolt_size}:**
        - **Min. Pitch (ระยะห่างน็อต):** {min_pitch} mm
        - **Min. Edge (ระยะขอบ):** {min_edge} mm
        - **Min. Plate Thickness:** {plate_t} mm
        """)
        
    
    with col_d2:
        # Visualize Plate
        h_plate = (n_bolts * min_pitch) + (2 * min_edge) if n_bolts > 1 else 100
        w_plate = 100
        st.info(f"แนะนำขนาดแผ่นเหล็ก (Plate Estimation):\nกว้าง {w_plate} mm x สูง {h_plate} mm x หนา {plate_t} mm")
