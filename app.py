import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP
# ==========================================
st.set_page_config(page_title="Professional Shear Connection Design", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .header-box { background-color: #2c3e50; color: white; padding: 10px; border-radius: 5px; margin-bottom: 10px; }
    .pass-box { border-left: 5px solid #27ae60; background-color: #eafaf1; padding: 10px; margin: 5px 0; }
    .fail-box { border-left: 5px solid #c0392b; background-color: #fdedec; padding: 10px; margin: 5px 0; }
    .formula { font-family: 'Courier New'; font-size: 14px; color: #555; }
    .metric-value { font-size: 18px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE & INPUTS
# ==========================================
steel_sections = {
    "H 200x100x5.5x8": {"h": 200, "tw": 5.5, "tf": 8, "Zx": 184, "Fu": 4000, "Fy": 2400},
    "H 250x125x6x9":    {"h": 250, "tw": 6.0, "tf": 9, "Zx": 295, "Fu": 4000, "Fy": 2400},
    "H 300x150x6.5x9":  {"h": 300, "tw": 6.5, "tf": 9, "Zx": 481, "Fu": 4000, "Fy": 2400},
    "H 350x175x7x11":   {"h": 350, "tw": 7.0, "tf": 11, "Zx": 775, "Fu": 4000, "Fy": 2400},
    "H 400x200x8x13":   {"h": 400, "tw": 8.0, "tf": 13, "Zx": 1190, "Fu": 4000, "Fy": 2400},
    "H 500x200x10x16":  {"h": 500, "tw": 10.0, "tf": 16, "Zx": 1910, "Fu": 4000, "Fy": 2400},
}

with st.sidebar:
    st.header("1. Load & Section")
    sec_name = st.selectbox("Beam Section", list(steel_sections.keys()), index=4)
    beam = steel_sections[sec_name]
    
    vu_input = st.number_input("Required Shear Force (Vu) [tons]", value=15.0, step=1.0) * 1000 # Convert to kg
    
    st.header("2. Connection Config (Shear Tab)")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        bolt_grade = st.selectbox("Bolt Grade", ["A307", "A325 (N)", "A490 (N)"])
        bolt_dia_mm = st.selectbox("Bolt Dia (mm)", [16, 20, 22, 24], index=1)
    with col_s2:
        n_rows = st.number_input("Rows of Bolts", 2, 10, 3)
        plate_t = st.selectbox("Plate Thickness (mm)", [6, 9, 12, 16, 20], index=1)

    st.header("3. Geometry (mm)")
    pitch = st.number_input("Pitch (s)", value=3*bolt_dia_mm, min_value=3*bolt_dia_mm)
    lev = st.number_input("Vertical Edge (Lev)", value=1.5*bolt_dia_mm)
    leh = st.number_input("Horiz. Edge (Leh)", value=40)
    weld_s = st.number_input("Weld Size (mm)", value=6)

# ==========================================
# 3. ENGINEERING CALCULATION ENGINE
# ==========================================

# 3.1 Properties
db = bolt_dia_mm / 10 # cm
dh = db + 0.2 # Hole diameter cm
tp = plate_t / 10 # Plate thickness cm
tw = beam['tw'] / 10 # Web thickness cm
Fu_beam = beam['Fu']
Fy_plate = 2400 # Assume SS400
Fu_plate = 4000
Fy_weld = 0.6 * 4900 # E70xx electrode shear strength (approx)

# 3.2 Bolt Shear Capacity
# A325N Shear Strength ~ 3720 ksc (approx for Allowable), A307 ~ 1900
fv_bolt = 3720 if "A325" in bolt_grade else (4760 if "A490" in bolt_grade else 1900)
area_bolt = 3.1416 * (db/2)**2
rn_bolt_shear = n_rows * area_bolt * fv_bolt
# Note: For strict ASD/LRFD, need specific Fv. Using simplified Allowable stress here.

# 3.3 Bearing Capacity (R = 1.2 * Fu * d * t) (Simplified AISC J3.10)
rn_bear_web = n_rows * (1.2 * Fu_beam * db * tw)
rn_bear_plate = n_rows * (1.2 * Fu_plate * db * tp)

# 3.4 Block Shear (The Complex One)
# Variables
s = pitch / 10
lev_cm = lev / 10
leh_cm = leh / 10
L_gv = lev_cm + (n_rows - 1) * s # Gross vertical length
L_nv = L_gv - (n_rows - 0.5) * dh # Net vertical length
L_nt = leh_cm - 0.5 * dh # Net tension length (horizontal)

# Calc Function
def get_block_shear(Fy, Fu, t, Agv, Anv, Ant):
    # AISC Eq J4-5: min( 0.6Fu*Anv + Ubs*Fu*Ant , 0.6Fy*Agv + Ubs*Fu*Ant )
    term1 = 0.6 * Fu * Anv + 1.0 * Fu * Ant
    term2 = 0.6 * Fy * Agv + 1.0 * Fu * Ant
    return min(term1, term2)

rn_bs_web = get_block_shear(beam['Fy'], Fu_beam, tw, L_gv*tw, L_nv*tw, L_nt*tw)
rn_bs_plate = get_block_shear(Fy_plate, Fu_plate, tp, L_gv*tp, L_nv*tp, L_nt*tp)

# 3.5 Plate Yielding & Rupture (Shear Yield/Rupture)
plate_h = L_gv + lev_cm # Total plate height approx
rn_pl_yield = 0.6 * Fy_plate * (plate_h * tp)
rn_pl_rupture = 0.6 * Fu_plate * ((plate_h - n_rows*dh) * tp)

# 3.6 Weld Capacity (Double Fillet)
# Fw = 0.707 * s * 0.3 * Fu_weld (ASD) ... simplified logic
# Allowable weld stress ~ 0.3 * 4900 = 1470 ksc
rn_weld = 2 * (0.707 * (weld_s/10)) * plate_h * 0.3 * 4900

# 3.7 Governing Capacity
capacities = {
    "Bolt Shear": rn_bolt_shear,
    "Bearing (Web)": rn_bear_web,
    "Bearing (Plate)": rn_bear_plate,
    "Block Shear (Web)": rn_bs_web,
    "Block Shear (Plate)": rn_bs_plate,
    "Plate Shear Yield": rn_pl_yield,
    "Plate Shear Rupture": rn_pl_rupture,
    "Weld Strength": rn_weld
}
limit_state = min(capacities, key=capacities.get)
max_capacity = capacities[limit_state]

# ==========================================
# 4. REPORT UI
# ==========================================

st.title(f"🛠️ Detailed Connection Analysis: {sec_name}")

# --- Summary Banner ---
status = "PASS" if max_capacity >= vu_input else "FAIL"
color_banner = "#27ae60" if status == "PASS" else "#c0392b"

st.markdown(f"""
<div style="background-color:{color_banner}; padding:20px; border-radius:10px; color:white; text-align:center;">
    <h1 style="margin:0;">Status: {status}</h1>
    <h3 style="margin:0;">Load: {vu_input/1000:.2f} T  vs  Capacity: {max_capacity/1000:.2f} T</h3>
    <p>Governing Failure Mode: <strong>{limit_state}</strong></p>
</div>
""", unsafe_allow_html=True)

col_rep1, col_rep2 = st.columns([1.5, 1])

# --- LEFT: DETAILED CHECK LIST ---
with col_rep1:
    st.subheader("📝 Detailed Calculation Checks")
    
    def render_check(label, capacity, demand, unit="kg"):
        ratio = demand / capacity
        icon = "✅" if ratio <= 1.0 else "❌"
        bar_color = "green" if ratio <= 1.0 else "red"
        pct = min(ratio * 100, 100)
        
        st.markdown(f"""
        <div style="margin-bottom:15px; border-bottom:1px solid #eee; padding-bottom:5px;">
            <div style="display:flex; justify-content:space-between;">
                <strong>{icon} {label}</strong>
                <span>Cap: {capacity:,.0f} {unit}</span>
            </div>
            <div style="background-color:#eee; width:100%; height:8px; border-radius:4px; margin-top:5px;">
                <div style="background-color:{bar_color}; width:{pct}%; height:100%; border-radius:4px;"></div>
            </div>
            <div style="font-size:12px; color:#888; text-align:right;">Ratio: {ratio:.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    # 1. BOLTS & HOLES GROUP
    st.markdown("#### 1. Bolts & Holes Interaction")
    render_check(f"Bolt Shear ({n_rows}x{bolt_grade})", rn_bolt_shear, vu_input)
    render_check("Bearing on Beam Web", rn_bear_web, vu_input)
    render_check("Bearing on Plate", rn_bear_plate, vu_input)
    
    # 2. RUPTURE GROUP
    st.markdown("#### 2. Rupture & Tearing")
    
    # Expandable detail for Block Shear because it's complex
    with st.expander("🔍 See Block Shear Details"):
        st.markdown(f"""
        **Web Block Shear:**
        - Agv (Shear Gross): {L_gv*tw:.2f} cm²
        - Anv (Shear Net): {L_nv*tw:.2f} cm²
        - Ant (Tension Net): {L_nt*tw:.2f} cm²
        - **Capacity:** {rn_bs_web:,.0f} kg
        
        **Plate Block Shear:**
        - Agv: {L_gv*tp:.2f} cm² | Anv: {L_nv*tp:.2f} cm² | Ant: {L_nt*tp:.2f} cm²
        - **Capacity:** {rn_bs_plate:,.0f} kg
        """)
        

    render_check("Block Shear (Web)", rn_bs_web, vu_input)
    render_check("Block Shear (Plate)", rn_bs_plate, vu_input)
    
    # 3. PLATE & WELD GROUP
    st.markdown("#### 3. Plate & Weld")
    render_check("Plate Shear Yielding", rn_pl_yield, vu_input)
    render_check("Plate Shear Rupture", rn_pl_rupture, vu_input)
    render_check(f"Weld Strength (size {weld_s}mm)", rn_weld, vu_input)

# --- RIGHT: VISUALIZATION & GEOMETRY ---
with col_rep2:
    st.subheader("📊 Capacity Comparison")
    
    # Bar Chart
    df_cap = pd.DataFrame(list(capacities.items()), columns=['Mode', 'Capacity'])
    df_cap['Color'] = ['#95a5a6']*len(df_cap)
    
    # Highlight Min (Limit) and Demand
    min_idx = df_cap['Capacity'].idxmin()
    df_cap.at[min_idx, 'Color'] = '#c0392b' # Red for Limit
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_cap['Mode'], x=df_cap['Capacity']/1000,
        orientation='h', marker_color=df_cap['Color'],
        text=df_cap['Capacity']/1000, texttemplate='%{text:.1f}T'
    ))
    
    # Add Demand Line
    fig.add_vline(x=vu_input/1000, line_dash="dash", line_color="black", annotation_text="Load Vu")
    
    fig.update_layout(height=400, margin=dict(l=0,r=0,t=0,b=0), xaxis_title="Capacity (Tons)")
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("📏 Geometry Check (AISC)")
    # Geometric Rules
    min_pitch = 2.67 * bolt_dia_mm
    pref_pitch = 3.0 * bolt_dia_mm
    min_edge = bolt_dia_mm # Simplified, strictly depends on cut edge/rolled edge
    
    checks = {
        f"Pitch >= {min_pitch:.1f} mm": pitch >= min_pitch,
        f"Edge Dist >= {min_edge} mm": lev >= min_edge and leh >= min_edge,
        "Plate Thk vs Beam Web": plate_t >= beam['tw'] # Engineering Judgement
    }
    
    for rule, is_ok in checks.items():
        icon = "✅" if is_ok else "⚠️"
        st.write(f"{icon} {rule}")
