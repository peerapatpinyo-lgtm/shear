import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & STYLE
# ==========================================
st.set_page_config(page_title="Structural Master Studio", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .math-card { background-color: #ffffff; border: 1px solid #e0e0e0; border-left: 5px solid #2e86c1; padding: 15px; margin-bottom: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .optimal-box { background-color: #e8f8f5; border-left: 5px solid #27ae60; padding: 15px; border-radius: 5px; margin-bottom: 15px; }
    .status-pass { background-color: #d4efdf; color: #145a32; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #27ae60; }
    .status-fail { background-color: #fadbd8; color: #7b241c; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #c0392b; }
    .section-header { font-size: 18px; font-weight: bold; color: #34495e; margin-top: 20px; margin-bottom: 10px; border-bottom: 2px solid #ecf0f1; padding-bottom: 5px; }
    .metric-val { font-size: 24px; font-weight: bold; color: #2e86c1; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE & INPUTS (SIDEBAR)
# ==========================================
steel_db = {
    "H 200x100x5.5x8": {"h": 200, "b": 100, "tw": 5.5, "tf": 8,   "Ix": 1840,   "Zx": 184,   "w": 21.3},
    "H 250x125x6x9":    {"h": 250, "b": 125, "tw": 6,   "tf": 9,   "Ix": 3690,   "Zx": 295,   "w": 29.6},
    "H 300x150x6.5x9": {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481,   "w": 36.7},
    "H 350x175x7x11":  {"h": 350, "b": 175, "tw": 7,   "tf": 11,  "Ix": 13600,  "Zx": 775,   "w": 49.6},
    "H 400x200x8x13":  {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190,  "w": 66.0},
    "H 450x200x9x14":  {"h": 450, "b": 200, "tw": 9,   "tf": 14,  "Ix": 33500,  "Zx": 1490,  "w": 76.0},
    "H 500x200x10x16": {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910,  "w": 89.6},
}

with st.sidebar:
    st.title("⚙️ Project Settings")
    st.subheader("1. Section & Material")
    sec_name = st.selectbox("Beam Section", list(steel_db.keys()), index=4)
    p = steel_db[sec_name]
    
    col_mat1, col_mat2 = st.columns(2)
    with col_mat1: fy = st.number_input("Fy (ksc)", value=2400)
    with col_mat2: fu = st.number_input("Fu (ksc)", value=4000)
    E_mod = 2.04e6

    st.info(f"""
    **Properties:**
    * Depth (h): {p['h']} mm
    * Web (tw): {p['tw']} mm
    * Ix: {p['Ix']:,} cm⁴ | Zx: {p['Zx']:,} cm³
    """)

# ==========================================
# 3. GLOBAL CALCULATION (BEAM LIMITS)
# ==========================================
h_cm = p['h']/10
tw_cm = p['tw']/10
Aw = h_cm * tw_cm
Ix, Zx = p['Ix'], p['Zx']

# Capacities
V_allow_web = 0.4 * fy * Aw  # kg
M_allow = 0.6 * fy * Zx      # kg.cm

# Optimal Span Logic (L/d = 15-20)
d_meter = p['h'] / 1000
opt_min = 15 * d_meter
opt_max = 20 * d_meter

# Curve Data
spans = np.linspace(2, 16, 100)
curve_shear, curve_moment, curve_defl, curve_safe = [], [], [], []

for L in spans:
    L_cm = L * 100
    ws = (2 * V_allow_web) / L_cm * 100 
    wm = (8 * M_allow) / (L_cm**2) * 100
    wd = ((L_cm / 360) * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100
    
    curve_shear.append(ws)
    curve_moment.append(wm)
    curve_defl.append(wd)
    curve_safe.append(min(ws, wm, wd))

# ==========================================
# 4. MAIN UI
# ==========================================
st.title("🏗️ Structural Studio: Beam & Connection Design")

tab1, tab2 = st.tabs(["📊 1. Beam Analysis (Span & Loads)", "🔩 2. Connection Detailing (Shear Tab)"])

# ==========================================
# TAB 1: BEAM ANALYSIS & OPTIMAL SPAN
# ==========================================
with tab1:
    col_main1, col_main2 = st.columns([1, 1.3])
    
    with col_main1:
        st.markdown('<div class="section-header">A. Span Selection</div>', unsafe_allow_html=True)
        
        # Optimal Span Logic
        st.markdown(f"""
        <div class="optimal-box">
            <b>🎯 Optimal Span Recommendation</b><br>
            Based on Rule of Thumb ($L/d \\approx 15-20$):
            <ul>
                <li>Section Depth: {d_meter:.2f} m</li>
                <li>Recommended Span: <b>{opt_min:.1f} - {opt_max:.1f} m</b></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        sel_span = st.slider("Select Span Length (m)", 2.0, 16.0, (opt_min+opt_max)/2, 0.5)
        
        # Determine Limit State for User Selection
        L_cm_user = sel_span * 100
        val_s = (2 * V_allow_web) / L_cm_user * 100
        val_m = (8 * M_allow) / (L_cm_user**2) * 100
        val_d = (L_cm_user / 360 * 384 * E_mod * Ix) / (5 * (L_cm_user**4)) * 100
        final_w = min(val_s, val_m, val_d)
        end_reaction = final_w * sel_span / 2
        
        limit_mode = "Shear" if final_w == val_s else ("Moment" if final_w == val_m else "Deflection")
        
        st.markdown(f"""
        <div style="padding:15px; background:#f4f6f7; border-radius:5px; margin-top:10px;">
            <div style="color:#7f8c8d; font-size:14px;">Safe Uniform Load</div>
            <div class="metric-val">{final_w:,.0f} kg/m</div>
            <div style="color:#c0392b; font-weight:bold;">Controlled by: {limit_mode}</div>
            <hr>
            <div style="color:#7f8c8d; font-size:14px;">End Reaction (for Connection)</div>
            <div class="metric-val" style="color:#d35400;">V = {end_reaction:,.0f} kg</div>
        </div>
        """, unsafe_allow_html=True)

    with col_main2:
        st.markdown('<div class="section-header">B. Capacity Curve & Derivations</div>', unsafe_allow_html=True)
        
        # PLOTLY CHART
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=spans, y=curve_shear, mode='lines', name='Shear Limit', line=dict(color='#e74c3c', dash='dash')))
        fig.add_trace(go.Scatter(x=spans, y=curve_moment, mode='lines', name='Moment Limit', line=dict(color='#f39c12', dash='dash')))
        fig.add_trace(go.Scatter(x=spans, y=curve_defl, mode='lines', name='Deflection Limit', line=dict(color='#27ae60', dash='dash')))
        fig.add_trace(go.Scatter(x=spans, y=curve_safe, mode='lines', name='Safe Zone', fill='tozeroy', line=dict(color='#2E86C1', width=3)))
        
        fig.add_vrect(x0=opt_min, x1=opt_max, fillcolor="green", opacity=0.1, annotation_text="Optimal", annotation_position="top left")
        fig.add_trace(go.Scatter(x=[sel_span], y=[final_w], mode='markers', marker=dict(size=12, color='red'), name='Selected Point'))

        fig.update_layout(xaxis_title="Span (m)", yaxis_title="Load (kg/m)", height=350, margin=dict(t=10,b=10,l=10,r=10), legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)
        
        # LATEX DERIVATIONS
        with st.expander("📝 Show Detailed Calculation Formula", expanded=True):
            st.markdown(f"**1. Shear Limit Derivation (Web Yield):**")
            st.latex(f"V_{{max}} = 0.4 \\cdot F_y \\cdot A_w = 0.4 \\cdot {fy} \\cdot ({h_cm} \\times {tw_cm}) = \\mathbf{{{V_allow_web:,.0f}}} \\; kg")
            st.latex(f"w_{{shear}} = \\frac{{2 V_{{max}}}}{{L}} = \\frac{{2 \\cdot {V_allow_web:,.0f}}}{{{sel_span}}} = \\mathbf{{{val_s:,.0f}}} \\; kg/m")
            
            st.markdown(f"**2. Moment Limit Derivation:**")
            st.latex(f"w_{{moment}} = \\frac{{8 M_{{allow}}}}{{L^2}} = \\frac{{8 \\cdot ({0.6*fy*Zx:,.0f})}}{{({sel_span}\\cdot 100)^2}} \\cdot 100 = \\mathbf{{{val_m:,.0f}}} \\; kg/m")

# ==========================================
# TAB 2: CONNECTION DETAIL
# ==========================================
with tab2:
    st.markdown('<div class="section-header">🛠️ Shear Connection Design (Single Plate)</div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns([1, 2])
    
    # --- INPUTS ---
    with c1:
        st.info("Load inputs linked from Tab 1")
        vu_input = st.number_input("Design Shear Force (Vu) [kg]", value=float(end_reaction), step=100.0)
        
        st.markdown("**Bolt Configuration**")
        bolt_gr = st.selectbox("Bolt Grade", ["A325 (N)", "A307", "A490"])
        d_mm = st.selectbox("Diameter (mm)", [16, 20, 22, 24], index=1)
        rows = st.number_input("Rows", 2, 8, 3)
        
        st.markdown("**Plate Configuration**")
        t_plate = st.selectbox("Plate Thickness (mm)", [6, 9, 12, 16, 20], index=1)
        
        # Auto Geometry
        pitch = 3 * d_mm
        lev = 1.5 * d_mm
        leh = 40
        st.caption(f"Geometry (Auto): Pitch={pitch}, Lev={lev}, Leh={leh} mm")

    # --- CALCULATIONS ---
    # Props
    db = d_mm/10; dh = db+0.2; tp = t_plate/10
    fv = 3720 if "A325" in bolt_gr else (1900 if "A307" in bolt_gr else 4760)
    
    # Checks
    rn_bolt = rows * (math.pi*(db/2)**2) * fv
    rn_bear_w = rows * (1.2 * fu * db * tw_cm)
    rn_bear_p = rows * (1.2 * fu * db * tp)
    
    # Block Shear Logic
    L_gv = (lev/10) + (rows-1)*(pitch/10)
    L_nv = L_gv - (rows-0.5)*dh
    L_nt = (leh/10) - 0.5*dh
    
    def block_shear(Fy, Fu, t, Agv, Anv, Ant):
        return min(0.6*Fu*Anv + 1.0*Fu*Ant, 0.6*Fy*Agv + 1.0*Fu*Ant)
        
    rn_bs_w = block_shear(fy, fu, tw_cm, L_gv*tw_cm, L_nv*tw_cm, L_nt*tw_cm)
    rn_bs_p = block_shear(2400, 4000, tp, L_gv*tp, L_nv*tp, L_nt*tp)
    
    rn_ply = 0.6*2400*(L_gv + lev/10)*tp
    rn_plr = 0.6*4000*((L_gv + lev/10) - rows*dh)*tp
    
    checks = {
        "Bolt Shear": rn_bolt,
        "Bearing (Web)": rn_bear_w,
        "Bearing (Plate)": rn_bear_p,
        "Block Shear (Web)": rn_bs_w,
        "Block Shear (Plate)": rn_bs_p,
        "Plate Yield": rn_ply,
        "Plate Rupture": rn_plr
    }
    
    min_cap = min(checks.values())
    gov_mode = min(checks, key=checks.get)
    status = "PASS" if min_cap >= vu_input else "FAIL"

    # --- OUTPUTS ---
    with c2:
        # Status Banner
        if status == "PASS":
            st.markdown(f"""
            <div class="status-pass">
                <h1>✅ PASS</h1>
                <h3>Capacity: {min_cap:,.0f} kg > Load: {vu_input:,.0f} kg</h3>
                <small>Governed by: {gov_mode}</small>
            </div>
            """, unsafe_allow_html=True)
            

[Image of steel connection detail drawing]

        else:
            st.markdown(f"""
            <div class="status-fail">
                <h1>❌ FAIL</h1>
                <h3>Capacity: {min_cap:,.0f} kg < Load: {vu_input:,.0f} kg</h3>
                <small>FAILURE MODE: <b>{gov_mode}</b></small>
            </div>
            """, unsafe_allow_html=True)
            if "Block Shear" in gov_mode:
                 

        
        # Detailed Check List (Bar Charts)
        st.markdown("### 📋 Detailed Check List")
        for mode, cap in checks.items():
            ratio = vu_input / cap
            bar_color = "#27ae60" if ratio <= 1.0 else "#c0392b"
            pct = min(ratio*100, 100)
            
            st.markdown(f"""
            <div style="margin-bottom:8px;">
                <div style="display:flex; justify-content:space-between; font-size:14px;">
                    <span><b>{mode}</b></span>
                    <span>{cap:,.0f} kg</span>
                </div>
                <div style="width:100%; background:#ecf0f1; height:8px; border-radius:4px;">
                    <div style="width:{pct}%; background:{bar_color}; height:100%; border-radius:4px;"></div>
                </div>
                <div style="text-align:right; font-size:12px; color:#7f8c8d;">Ratio: {ratio:.2f}</div>
            </div>
            """, unsafe_allow_html=True)

# ==========================================
# FOOTER: FUTURE IMPROVEMENTS
# ==========================================
st.markdown("---")
st.subheader("🚀 Future Improvements & Extensions")
c_f1, c_f2 = st.columns(2)
with c_f1:
    st.markdown("""
    **1. Advanced Calculation Modules**
    * **Weld Design:** Add Fillet weld sizing calculation based on electrode strength (E70XX).
    * **Moment Connection:** Add check for End-Plate Moment Connection (Flange bending, Bolt prying).
    * **LRFD Method:** Add toggle switch to change from ASD to LRFD ($1.2D+1.6L$).
    """)
with c_f2:
    st.markdown("""
    **2. Professional Reporting**
    * **PDF Export:** Generate a signed calculation sheet PDF.
    * **Cost Estimation:** Calculate total steel weight and bolt cost per joint.
    * **3D Visualization:** Render the connection geometry in 3D using PyDeck.
    """)
