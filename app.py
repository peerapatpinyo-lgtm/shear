import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & CUSTOM CSS
# ==========================================
st.set_page_config(page_title="Structural Master Studio", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .report-box { border: 1px solid #dcdcdc; padding: 20px; border-radius: 5px; background-color: #f9f9f9; font-family: 'Courier New', monospace; font-size: 14px; }
    .optimal-box { background-color: #e8f8f5; border-left: 5px solid #27ae60; padding: 15px; border-radius: 5px; margin-bottom: 15px; }
    .theory-box { background-color: #fdfefe; border: 1px solid #d6dbdf; padding: 15px; border-radius: 5px; margin-top: 10px; }
    .pass-tag { background-color: #27ae60; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    .fail-tag { background-color: #c0392b; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    h3 { color: #2e86c1; border-bottom: 2px solid #eaecee; padding-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. INPUT DATA
# ==========================================
steel_db = {
    "H 200x100x5.5x8": {"h": 200, "b": 100, "tw": 5.5, "tf": 8,   "Ix": 1840,   "Zx": 184},
    "H 250x125x6x9":    {"h": 250, "b": 125, "tw": 6,   "tf": 9,   "Ix": 3690,   "Zx": 295},
    "H 300x150x6.5x9": {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481},
    "H 350x175x7x11":  {"h": 350, "b": 175, "tw": 7,   "tf": 11,  "Ix": 13600,  "Zx": 775},
    "H 400x200x8x13":  {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190},
    "H 450x200x9x14":  {"h": 450, "b": 200, "tw": 9,   "tf": 14,  "Ix": 33500,  "Zx": 1490},
    "H 500x200x10x16": {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910},
}

with st.sidebar:
    st.title("⚙️ Design Parameters")
    sec_name = st.selectbox("Select Section", list(steel_db.keys()), index=4)
    p = steel_db[sec_name]
    fy = st.number_input("Yield Strength (Fy) ksc", value=2400)
    fu = st.number_input("Ultimate Strength (Fu) ksc", value=4000)
    E_mod = 2.04e6
    
    st.info(f"**Props:** A_w={p['h']*p['tw']/100:.1f} cm² | Zx={p['Zx']} cm³")

# ==========================================
# 3. GLOBAL CALCULATION (BEAM)
# ==========================================
h_cm, tw_cm = p['h']/10, p['tw']/10
Aw = h_cm * tw_cm
Ix, Zx = p['Ix'], p['Zx']

# Constants
V_allow_web = 0.4 * fy * Aw
M_allow = 0.6 * fy * Zx

# Optimal Span Logic
d_meter = p['h'] / 1000
opt_min, opt_max = 15 * d_meter, 20 * d_meter

# Curve Generation
spans = np.linspace(2, 16, 100)
curve_shear = (2 * V_allow_web) / (spans * 100) * 100
curve_moment = (8 * M_allow) / ((spans * 100)**2) * 100
curve_defl = ((spans * 100 / 360) * 384 * E_mod * Ix) / (5 * ((spans * 100)**4)) * 100
curve_safe = np.minimum(np.minimum(curve_shear, curve_moment), curve_defl)

# ==========================================
# 4. UI STRUCTURE
# ==========================================
st.title("🏗️ Structural Studio: Detailed Analysis Report")
tab1, tab2 = st.tabs(["📊 1. Beam Optimization", "🔩 2. Connection Design (Detailed)"])

# ==========================================
# TAB 1: BEAM ANALYSIS
# ==========================================
with tab1:
    c1, c2 = st.columns([1, 1.5])
    with c1:
        st.markdown("### A. Span Selection Strategy")
        
        # --- THEORY: WHY THIS SPAN? ---
        st.markdown(f"""
        <div class="optimal-box">
            <b>🎯 Optimal Span: {opt_min:.1f} - {opt_max:.1f} m</b><br>
            <small>Based on Efficiency Rule: $L/d \\approx 15 - 20$</small>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("💡 Why this specific range? (Click to learn)", expanded=False):
            st.markdown("""
            **The Engineering Logic:**
            1.  **Short Span ($L < 15d$):** * Governed by **Shear**. 
                * *Result:* Using a deep beam here is wasteful; the flanges are barely stressed.
            2.  **Long Span ($L > 20d$):** * Governed by **Deflection**.
                * *Result:* You need a huge beam just to stop it from sagging, not because it will break.
            3.  **Optimal Zone ($15d < L < 20d$):**
                * Governed by **Moment (Bending)**.
                * *Result:* This is where H-Beams are most efficient. You use the full strength of the steel (Yielding).
            """)

        sel_span = st.slider("Select Design Span (m)", 2.0, 16.0, (opt_min+opt_max)/2, 0.5)

    with c2:
        # Chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=spans, y=curve_shear, name='Shear Limit', line=dict(dash='dash', color='#e74c3c')))
        fig.add_trace(go.Scatter(x=spans, y=curve_moment, name='Moment Limit', line=dict(dash='dash', color='#f39c12')))
        fig.add_trace(go.Scatter(x=spans, y=curve_defl, name='Deflection Limit', line=dict(dash='dash', color='#27ae60')))
        fig.add_trace(go.Scatter(x=spans, y=curve_safe, name='Safe Capacity', fill='tozeroy', line=dict(color='#2E86C1', width=3)))
        
        # Highlight Optimal Zone
        fig.add_vrect(x0=opt_min, x1=opt_max, fillcolor="green", opacity=0.1, annotation_text="Efficiency Zone", annotation_position="top right")
        fig.add_vline(x=sel_span, line_dash="dot", line_color="black")
        
        fig.update_layout(height=350, margin=dict(t=0, b=0), xaxis_title="Span (m)", yaxis_title="Load (kg/m)")
        st.plotly_chart(fig, use_container_width=True)

    # Calc Values
    L_cm = sel_span * 100
    w_shear = (2 * V_allow_web) / L_cm * 100
    w_moment = (8 * M_allow) / (L_cm**2) * 100
    w_defl = ((L_cm/360) * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100
    final_w = min(w_shear, w_moment, w_defl)
    end_reaction = final_w * sel_span / 2

    st.success(f"**Design Result:** At {sel_span}m, Safe Load = **{final_w:,.0f} kg/m** (Reaction V = **{end_reaction:,.0f} kg**)")

# ==========================================
# TAB 2: CONNECTION DETAIL (FULL CALC)
# ==========================================
with tab2:
    st.markdown("### B. Shear Connection Design (Plate)")
    
    col_in, col_out = st.columns([1, 2])
    
    with col_in:
        st.info(f"Target Load $V_u$ from Tab 1: **{end_reaction:,.0f} kg**")
        vu = st.number_input("Design Shear (kg)", value=float(end_reaction), step=100.0)
        
        st.markdown("**Parameters**")
        d_mm = st.selectbox("Bolt Dia (mm)", [16, 20, 22, 24], index=1)
        grade = st.selectbox("Grade", ["A325", "A307"])
        rows = st.number_input("Rows", 2, 8, 3)
        tp_mm = st.selectbox("Plate Thick (mm)", [6, 9, 12, 16], index=1)
        
        # Geometry
        s = 3 * d_mm
        lev = 1.5 * d_mm
        leh = 40
        st.caption(f"Pitch(s)={s}, Lev={lev}, Leh={leh} mm")

    # --- CALCULATION ENGINE ---
    # 1. Properties
    db = d_mm/10
    dh = db + 0.2
    tp = tp_mm/10
    fv = 3720 if "A325" in grade else 1900
    
    # 2. Geometry Areas (Crucial for Block Shear)
    # L_gv: Gross Vertical Length, L_nv: Net Vertical, L_nt: Net Tension
    L_gv = (lev/10) + (rows-1)*(s/10)
    L_nv = L_gv - (rows-0.5)*dh
    L_nt = (leh/10) - 0.5*dh
    
    Agv = L_gv * tp
    Anv = L_nv * tp
    Ant = L_nt * tp
    
    # 3. Capacities
    # A. Bolt Shear
    Ab = math.pi * (db/2)**2
    Rn_bolt = rows * Ab * fv
    
    # B. Bearing
    Rn_bear_w = rows * (1.2 * fu * db * tw_cm)
    Rn_bear_p = rows * (1.2 * fu * db * tp)
    
    # C. Block Shear (Plate)
    # Ubs = 1.0 for flat plate
    R_bs1 = 0.6 * 2400 * Agv + 1.0 * 4000 * Ant
    R_bs2 = 0.6 * 4000 * Anv + 1.0 * 4000 * Ant
    Rn_bs = min(R_bs1, R_bs2)
    
    # D. Yield/Rupture
    Rn_yield = 0.6 * 2400 * (L_gv + lev/10) * tp
    Rn_rup = 0.6 * 4000 * ((L_gv + lev/10) - rows*dh) * tp
    
    capacities = {
        "Bolt Shear": Rn_bolt,
        "Bearing (Web)": Rn_bear_w,
        "Bearing (Plate)": Rn_bear_p,
        "Block Shear": Rn_bs,
        "Plate Yield": Rn_yield,
        "Plate Rupture": Rn_rup
    }
    min_cap = min(capacities.values())
    status = "PASS" if min_cap >= vu else "FAIL"

    with col_out:
        # Result Banner
        color = "#27ae60" if status == "PASS" else "#c0392b"
        st.markdown(f"""
        <div style="background-color:{color}; color:white; padding:15px; border-radius:8px; text-align:center;">
            <h2>{status}</h2>
            Capacity: <b>{min_cap:,.0f} kg</b> vs Load: {vu:,.0f} kg
        </div>
        """, unsafe_allow_html=True)
        
        

        # --- FULL CALCULATION REPORT ---
        st.markdown("### 📜 Detailed Calculation Report")
        with st.container():
            st.markdown(f"""
            <div class="report-box">
            <b>1. GEOMETRY CHECK</b><br>
            Bolt: M{d_mm} | Hole ($d_h$): {dh:.2f} cm | Plate: {tp_mm} mm (SS400)<br>
            Vertical Edge ($L_{{ev}}$): {lev} mm | Pitch ($s$): {s} mm<br>
            <br>
            <b>2. BOLT SHEAR ($R_n$)</b><br>
            $A_b = \pi \cdot ({db}/2)^2 = {Ab:.2f} \ cm^2$<br>
            $R_n = n \cdot A_b \cdot F_v = {rows} \cdot {Ab:.2f} \cdot {fv}$<br>
            $R_n = $ <b>{Rn_bolt:,.0f} kg</b> {'<span class="pass-tag">PASS</span>' if Rn_bolt >= vu else '<span class="fail-tag">FAIL</span>'}<br>
            <br>
            <b>3. BEARING CHECK ($R_n$)</b><br>
            Web: $1.2 \cdot F_u \cdot d \cdot t_w = 1.2 \cdot {fu} \cdot {db} \cdot {tw_cm} \cdot {rows} = $ <b>{Rn_bear_w:,.0f} kg</b><br>
            Plate: $1.2 \cdot F_u \cdot d \cdot t_p = 1.2 \cdot {fu} \cdot {db} \cdot {tp} \cdot {rows} = $ <b>{Rn_bear_p:,.0f} kg</b><br>
            <br>
            <b>4. BLOCK SHEAR BREAKDOWN</b> (The Tricky Part)<br>
            <i>Shear Areas:</i><br>
            $A_{{gv}} = (L_{{ev}} + (n-1)s) \cdot t = ({lev/10} + {(rows-1)*s/10}) \cdot {tp} = {Agv:.2f} \ cm^2$<br>
            $A_{{nv}} = A_{{gv}} - (n-0.5)d_h \cdot t = {Agv:.2f} - ({rows-0.5}) \cdot {dh:.2f} \cdot {tp} = {Anv:.2f} \ cm^2$<br>
            <i>Tension Area:</i><br>
            $A_{{nt}} = (L_{{eh}} - 0.5d_h) \cdot t = ({leh/10} - 0.5 \cdot {dh:.2f}) \cdot {tp} = {Ant:.2f} \ cm^2$<br>
            <i>Calculation:</i><br>
            (1) $0.6F_u A_{{nv}} + U_{{bs}}F_u A_{{nt}} = 0.6({4000})({Anv:.2f}) + (1)({4000})({Ant:.2f}) = {R_bs2:,.0f}$<br>
            (2) $0.6F_y A_{{gv}} + U_{{bs}}F_u A_{{nt}} = 0.6({2400})({Agv:.2f}) + (1)({4000})({Ant:.2f}) = {R_bs1:,.0f}$<br>
            $R_{{bs}} = \min(1, 2) = $ <b>{Rn_bs:,.0f} kg</b> {'<span class="pass-tag">PASS</span>' if Rn_bs >= vu else '<span class="fail-tag">FAIL</span>'}<br>
            </div>
            """, unsafe_allow_html=True)
