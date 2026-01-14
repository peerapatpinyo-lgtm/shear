import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & STYLE
# ==========================================
st.set_page_config(page_title="Structural Studio Pro", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .math-card { background-color: #f8f9fa; border-left: 5px solid #2e86c1; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    .limit-label { font-weight: bold; font-size: 14px; }
    .shear-highlight { background-color: #fadbd8; border-left: 5px solid #c0392b; padding: 15px; border-radius: 5px; }
    .pass-box { color: #27ae60; font-weight: bold; }
    .fail-box { color: #c0392b; font-weight: bold; }
    .metric-val { font-size: 20px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE (H-BEAM JIS/TIS)
# ==========================================
steel_db = {
    "H 150x75x5x7":     {"h": 150, "b": 75,  "tw": 5,   "tf": 7,   "Ix": 666,    "Zx": 88.8,  "w": 14.0},
    "H 200x100x5.5x8": {"h": 200, "b": 100, "tw": 5.5, "tf": 8,   "Ix": 1840,   "Zx": 184,   "w": 21.3},
    "H 250x125x6x9":    {"h": 250, "b": 125, "tw": 6,   "tf": 9,   "Ix": 3690,   "Zx": 295,   "w": 29.6},
    "H 300x150x6.5x9": {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481,   "w": 36.7},
    "H 350x175x7x11":  {"h": 350, "b": 175, "tw": 7,   "tf": 11,  "Ix": 13600,  "Zx": 775,   "w": 49.6},
    "H 400x200x8x13":  {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190,  "w": 66.0},
    "H 450x200x9x14":  {"h": 450, "b": 200, "tw": 9,   "tf": 14,  "Ix": 33500,  "Zx": 1490,  "w": 76.0},
    "H 500x200x10x16": {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910,  "w": 89.6},
}

# ==========================================
# 3. SIDEBAR INPUTS
# ==========================================
with st.sidebar:
    st.header("⚙️ Project Settings")
    
    st.subheader("1. Beam Section")
    sec_name = st.selectbox("Select Section", list(steel_db.keys()), index=4)
    p = steel_db[sec_name]
    
    # Display Properties
    st.info(f"""
    **{sec_name} Properties:**
    * Depth (h): {p['h']} mm
    * Web Thk (tw): {p['tw']} mm
    * Flange Thk (tf): {p['tf']} mm
    * Modulus (Zx): {p['Zx']} cm³
    """)
    
    st.subheader("2. Material Properties")
    fy = st.number_input("Yield Strength (Fy)", value=2400)
    fu = st.number_input("Ultimate Strength (Fu)", value=4000)
    E_mod = 2.04e6 # ksc

# ==========================================
# 4. CALCULATION CORE (BEAM)
# ==========================================
# Constants
h_cm = p['h']/10
tw_cm = p['tw']/10
Aw = h_cm * tw_cm
Ix, Zx = p['Ix'], p['Zx']

# Limits (Allowable Stress Design - ASD)
V_allow_web = 0.4 * fy * Aw  # Shear Capacity (kg)
M_allow = 0.6 * fy * Zx      # Moment Capacity (kg.cm)

# Curve Generation
spans = np.linspace(2, 16, 100)
curve_shear, curve_moment, curve_defl, curve_safe = [], [], [], []

for L in spans:
    L_cm = L * 100
    # 1. Shear Limit (V = wL/2 -> w = 2V/L)
    ws = (2 * V_allow_web) / L_cm * 100 
    # 2. Moment Limit (M = wL^2/8 -> w = 8M/L^2)
    wm = (8 * M_allow) / (L_cm**2) * 100
    # 3. Deflection Limit (L/360)
    wd = ((L_cm / 360) * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100
    
    curve_shear.append(ws)
    curve_moment.append(wm)
    curve_defl.append(wd)
    curve_safe.append(min(ws, wm, wd))

# ==========================================
# 5. UI TABS
# ==========================================
st.title("🏗️ Structural Studio: Beam & Connection Analysis")

tab1, tab2 = st.tabs(["📊 Tab 1: Beam Capacity & Span", "🔩 Tab 2: Connection Detailing"])

# ==========================================
# TAB 1: BEAM ANALYSIS
# ==========================================
with tab1:
    col_chart, col_calc = st.columns([2, 1])
    
    with col_chart:
        st.subheader("📉 Capacity Curves (Shear vs Moment vs Deflection)")
        
        fig = go.Figure()
        
        # Plot Lines
        fig.add_trace(go.Scatter(x=spans, y=curve_shear, mode='lines', name='Shear Limit (Web)', line=dict(color='#e74c3c', dash='dash')))
        fig.add_trace(go.Scatter(x=spans, y=curve_moment, mode='lines', name='Moment Limit', line=dict(color='#f39c12', dash='dash')))
        fig.add_trace(go.Scatter(x=spans, y=curve_defl, mode='lines', name='Deflection Limit (L/360)', line=dict(color='#27ae60', dash='dash')))
        fig.add_trace(go.Scatter(x=spans, y=curve_safe, mode='lines', name='Safe Design Zone', fill='tozeroy', line=dict(color='#2E86C1', width=3)))

        fig.update_layout(xaxis_title="Span Length (m)", yaxis_title="Safe Uniform Load (kg/m)", hovermode="x unified", height=500, legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)
        
        # Interaction
        sel_span = st.slider("Select Span Length (m)", 2.0, 15.0, 6.0, 0.5)

    with col_calc:
        idx = (np.abs(spans - sel_span)).argmin()
        val_s, val_m, val_d = curve_shear[idx], curve_moment[idx], curve_defl[idx]
        final_val = min(val_s, val_m, val_d)
        end_reaction = final_val * sel_span / 2
        
        st.subheader(f"🧮 Calculation at L = {sel_span} m")
        
        # 1. SHEAR DERIVATION
        st.markdown('<div class="limit-label" style="color:#c0392b;">1. Shear Limit Derivation</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="shear-highlight">
            <b>Concept:</b> Web yielding limit.<br>
            $V_{{max}} = 0.4 F_y A_w = 0.4 \\times {fy} \\times {Aw:.2f}$<br>
            $= \\mathbf{{{V_allow_web:,.0f}}}$ <b>kg</b> (Constant Capacity)<br>
            <hr>
            <b>Convert to Load ($w$):</b><br>
            $w = 2 V_{{max}} / L = (2 \\times {V_allow_web:,.0f}) / {sel_span}$<br>
            $= \\mathbf{{{val_s:,.0f}}}$ <b>kg/m</b>
        </div>
        """, unsafe_allow_html=True)

        # 2. MOMENT & DEFLECTION
        st.markdown(f"""
        <div class="math-card">
            <span style="color:#d35400"><b>2. Moment Limit:</b></span> {val_m:,.0f} kg/m<br>
            <span style="color:#27ae60"><b>3. Deflection Limit:</b></span> {val_d:,.0f} kg/m
        </div>
        """, unsafe_allow_html=True)
        
        st.success(f"**Governing Load:** {final_val:,.0f} kg/m")
        st.info(f"👉 **Design Reaction (V): {end_reaction:,.0f} kg** (Go to Tab 2)")

# ==========================================
# TAB 2: CONNECTION DETAIL (RESTORED)
# ==========================================
with tab2:
    st.subheader("🔩 Shear Connection Design (Single Plate / Shear Tab)")
    
    col_input, col_result = st.columns([1, 2])
    
    # --- A. INPUT SECTION ---
    with col_input:
        st.markdown("#### A. Design Loads & Bolts")
        # Link load from Tab 1
        vu_input = st.number_input("Required Shear (Vu) [kg]", value=float(end_reaction), step=100.0)
        
        bolt_grade = st.selectbox("Bolt Grade", ["A325 (N)", "A307", "A490 (N)"])
        bolt_dia_mm = st.selectbox("Bolt Diameter (mm)", [16, 20, 22, 24], index=1)
        
        st.markdown("#### B. Plate Geometry")
        n_rows = st.number_input("Number of Bolts (Rows)", 2, 8, 3)
        plate_t = st.selectbox("Plate Thickness (mm)", [6, 9, 12, 16, 20], index=1)
        
        # Auto-Geometry
        st.caption("Geometry (Auto-calculated)")
        pitch = st.number_input("Pitch (s) mm", value=3*bolt_dia_mm)
        edge_v = st.number_input("Vert. Edge (Lev) mm", value=1.5*bolt_dia_mm)
        edge_h = st.number_input("Horiz. Edge (Leh) mm", value=40)

    # --- B. CALCULATION ENGINE ---
    # Props
    db = bolt_dia_mm / 10
    dh = db + 0.2
    tp = plate_t / 10
    
    # 1. Bolt Shear
    # Allowable Shear Stress (approximate ASD)
    Fv_bolt = 3720 if "A325" in bolt_grade else (1900 if "A307" in bolt_grade else 4760)
    rn_bolt = n_rows * (math.pi * (db/2)**2) * Fv_bolt
    
    # 2. Bearing (Web & Plate)
    rn_bear_web = n_rows * (1.2 * fu * db * tw_cm)
    rn_bear_pl = n_rows * (1.2 * fu * db * tp)
    
    # 3. Block Shear (The critical check)
    # Dimensions
    L_gv = (edge_v/10) + (n_rows-1)*(pitch/10)
    L_nv = L_gv - (n_rows-0.5)*dh
    L_nt = (edge_h/10) - 0.5*dh
    
    def calc_bs(Fy_mat, Fu_mat, t_mat, Agv, Anv, Ant):
        term1 = 0.6 * Fu_mat * Anv + 1.0 * Fu_mat * Ant
        term2 = 0.6 * Fy_mat * Agv + 1.0 * Fu_mat * Ant
        return min(term1, term2)
        
    rn_bs_web = calc_bs(fy, fu, tw_cm, L_gv*tw_cm, L_nv*tw_cm, L_nt*tw_cm)
    rn_bs_pl = calc_bs(2400, 4000, tp, L_gv*tp, L_nv*tp, L_nt*tp) # Plate is SS400
    
    # 4. Plate Shear Yield & Rupture
    H_pl = L_gv + (edge_v/10)
    rn_pl_yield = 0.6 * 2400 * H_pl * tp
    rn_pl_rup = 0.6 * 4000 * (H_pl - n_rows*dh) * tp

    # Consolidate
    checks = {
        "Bolt Shear": rn_bolt,
        "Bearing (Web)": rn_bear_web,
        "Bearing (Plate)": rn_bear_pl,
        "Block Shear (Web)": rn_bs_web,
        "Block Shear (Plate)": rn_bs_pl,
        "Plate Yield": rn_pl_yield,
        "Plate Rupture": rn_pl_rup
    }
    
    min_cap = min(checks.values())
    limit_state = min(checks, key=checks.get)
    status = "PASS" if min_cap >= vu_input else "FAIL"
    
    # --- C. RESULT DISPLAY ---
    with col_result:
        # Status Banner
        color = "#27ae60" if status == "PASS" else "#c0392b"
        st.markdown(f"""
        <div style="background-color:{color}; color:white; padding:15px; border-radius:8px; text-align:center; margin-bottom:20px;">
            <h2 style="margin:0">{status}</h2>
            <p style="margin:0">Load: {vu_input:,.0f} kg  vs  Capacity: {min_cap:,.0f} kg</p>
            <p style="margin:0; font-size:14px;">Governed by: <strong>{limit_state}</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        

        # Bar Chart Comparison
        df_res = pd.DataFrame(list(checks.items()), columns=["Check", "Capacity"])
        df_res['Color'] = np.where(df_res['Capacity'] < vu_input, '#c0392b', '#95a5a6')
        df_res.loc[df_res['Check'] == limit_state, 'Color'] = '#f39c12' # Highlight Governor
        
        fig2 = go.Figure(go.Bar(
            x=df_res['Capacity'], y=df_res['Check'], orientation='h',
            marker_color=df_res['Color'], text=df_res['Capacity'], texttemplate='%{text:,.0f}', textposition='auto'
        ))
        fig2.add_vline(x=vu_input, line_dash="dash", line_color="black", annotation_text="Load Vu")
        fig2.update_layout(height=400, margin=dict(t=0, b=0), xaxis_title="Capacity (kg)")
        st.plotly_chart(fig2, use_container_width=True)
        
        # Detailed Expandable
        with st.expander("🔍 View Detailed Calculations"):
            st.write("### Geometric Check")
            st.write(f"- Gross Shear Area (Agv): {L_gv*tp:.2f} cm²")
            st.write(f"- Net Shear Area (Anv): {L_nv*tp:.2f} cm²")
            st.write(f"- Net Tension Area (Ant): {L_nt*tp:.2f} cm²")
