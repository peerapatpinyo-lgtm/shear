import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & STYLE
# ==========================================
st.set_page_config(page_title="Structural Design Studio", layout="wide", page_icon="🏗️")

# Custom CSS for "Paper-like" feel
st.markdown("""
<style>
    .report-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .header-blue {
        color: #2e86c1;
        font-weight: bold;
        border-bottom: 2px solid #2e86c1;
        padding-bottom: 5px;
        margin-bottom: 15px;
        font-size: 18px;
    }
    .pass-badge {
        background-color: #d4efdf;
        color: #196f3d;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .fail-badge {
        background-color: #fadbd8;
        color: #943126;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .highlight-box {
        background-color: #eaf2f8;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #2980b9;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. INPUTS & DATABASE
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
    st.header("⚙️ Design Settings")
    
    st.subheader("1. Beam Section")
    sec_name = st.selectbox("Select Section", list(steel_db.keys()), index=4)
    p = steel_db[sec_name]
    
    st.subheader("2. Materials (kg/cm²)")
    fy = st.number_input("Yield Strength (Fy)", value=2400)
    fu = st.number_input("Ultimate Strength (Fu)", value=4000)
    E_mod = 2.04e6

    st.info(f"""
    **{sec_name} Props:**
    Depth (d) = {p['h']} mm
    Web (tw) = {p['tw']} mm
    Zx = {p['Zx']:,} cm³
    """)

# ==========================================
# 3. GLOBAL CALCULATION LOGIC
# ==========================================
# Beam Constants
h_cm = p['h']/10
tw_cm = p['tw']/10
Aw = h_cm * tw_cm
Ix, Zx = p['Ix'], p['Zx']

# Optimal Span Range Logic
d_meter = p['h'] / 1000
opt_min = 15 * d_meter
opt_max = 20 * d_meter

# Beam Capacities (ASD)
V_allow = 0.4 * fy * Aw
M_allow = 0.6 * fy * Zx

# Curve Data
spans = np.linspace(2, 16, 100)
curve_shear = (2 * V_allow) / (spans * 100) * 100
curve_moment = (8 * M_allow) / ((spans * 100)**2) * 100
curve_defl = ((spans * 100 / 360) * 384 * E_mod * Ix) / (5 * ((spans * 100)**4)) * 100
curve_safe = np.minimum(np.minimum(curve_shear, curve_moment), curve_defl)

# ==========================================
# 4. MAIN INTERFACE
# ==========================================
st.title("🏗️ Structural Studio Pro")

tab1, tab2 = st.tabs(["📊 Tab 1: Beam Span Optimization", "🔩 Tab 2: Connection Detailing"])

# ------------------------------------------
# TAB 1: BEAM OPTIMIZATION
# ------------------------------------------
with tab1:
    col_chart, col_info = st.columns([2, 1])
    
    with col_info:
        st.markdown("### 🎯 Span Selection Strategy")
        
        # Readable explanation using standard Streamlit markdown
        st.markdown("""
        To design an economical beam, we generally follow the **Span-to-Depth Ratio** rule of thumb.
        """)
        
        # Clear Equation Display
        st.latex(r"Efficiency \ Range: \frac{L}{d} \approx 15 - 20")
        
        st.markdown(f"""
        For section **{sec_name}** (Depth = {d_meter:.2f} m):
        - **Minimum Span ($15d$):** {opt_min:.1f} m
        - **Maximum Span ($20d$):** {opt_max:.1f} m
        """)
        
        st.info("💡 **Why?**\n\nIf L < 15d: Beam is too deep (Shear controlled).\n\nIf L > 20d: Beam is too slender (Deflection controlled).")

        # Interactive Slider
        st.markdown("---")
        sel_span = st.slider("Select Span Length (m)", 2.0, 16.0, (opt_min+opt_max)/2, 0.5)
        
        # Calculate Loads at selected span
        L_cm_sel = sel_span * 100
        w_s = (2 * V_allow) / L_cm_sel * 100
        w_m = (8 * M_allow) / (L_cm_sel**2) * 100
        w_d = ((L_cm_sel/360) * 384 * E_mod * Ix) / (5 * (L_cm_sel**4)) * 100
        
        final_w = min(w_s, w_m, w_d)
        end_reaction = final_w * sel_span / 2
        
        # Determine Governor
        gov = "Shear" if final_w == w_s else ("Moment" if final_w == w_m else "Deflection")
        
        st.success(f"**Safe Load:** {final_w:,.0f} kg/m")
        st.warning(f"**Reaction (V):** {end_reaction:,.0f} kg")

    with col_chart:
        st.markdown("### 📈 Capacity Curves")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=spans, y=curve_shear, name='Shear Limit', line=dict(dash='dash', color='#e74c3c')))
        fig.add_trace(go.Scatter(x=spans, y=curve_moment, name='Moment Limit', line=dict(dash='dash', color='#f39c12')))
        fig.add_trace(go.Scatter(x=spans, y=curve_defl, name='Deflection Limit', line=dict(dash='dash', color='#27ae60')))
        fig.add_trace(go.Scatter(x=spans, y=curve_safe, name='Safe Zone', fill='tozeroy', line=dict(color='#2E86C1', width=2)))
        
        # Visual Helper
        fig.add_vrect(x0=opt_min, x1=opt_max, fillcolor="green", opacity=0.1, annotation_text="Optimal Zone")
        fig.add_trace(go.Scatter(x=[sel_span], y=[final_w], mode='markers', marker=dict(size=15, color='red'), name='Your Design'))
        
        fig.update_layout(xaxis_title="Span (m)", yaxis_title="Uniform Load (kg/m)", height=450, legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------
# TAB 2: CONNECTION DETAIL
# ------------------------------------------
with tab2:
    st.markdown("### 🔩 Shear Connection Design (Single Plate)")
    
    # 2-Column Layout
    c_input, c_calc = st.columns([1, 1.5])
    
    with c_input:
        st.markdown('<div class="highlight-box"><b>INPUT PARAMETERS</b></div>', unsafe_allow_html=True)
        
        # Load linked from Tab 1
        vu_input = st.number_input("Design Shear Force (Vu) [kg]", value=float(end_reaction), step=100.0)
        st.caption("Linked from Tab 1 (Reaction Force)")
        
        st.markdown("**Bolt Settings**")
        d_mm = st.selectbox("Diameter (mm)", [16, 20, 22, 24], index=1)
        grade = st.selectbox("Bolt Grade", ["A325", "A307"])
        rows = st.number_input("Number of Rows", 2, 8, 3)
        
        st.markdown("**Plate Settings**")
        tp_mm = st.selectbox("Plate Thickness (mm)", [6, 9, 12, 16], index=1)
        
        # Automatic Geometry
        s = 3 * d_mm
        lev = 1.5 * d_mm
        leh = 40
        
        st.markdown("---")
        st.markdown("**Geometry (Auto-Calculated):**")
        st.text(f"Pitch (s)  : {s} mm")
        st.text(f"Edge V (Lev): {lev} mm")
        st.text(f"Edge H (Leh): {leh} mm")

    with c_calc:
        # --- CALCULATION ENGINE ---
        # 1. Props
        db = d_mm/10
        dh = db + 0.2
        tp = tp_mm/10
        fv = 3720 if "A325" in grade else 1900
        
        # 2. Areas for Block Shear (Detailed)
        # Gross Vertical, Net Vertical, Net Tension
        L_gv = (lev/10) + (rows-1)*(s/10)
        L_nv = L_gv - (rows-0.5)*dh
        L_nt = (leh/10) - 0.5*dh
        
        Agv = L_gv * tp
        Anv = L_nv * tp
        Ant = L_nt * tp
        
        # 3. Capacities
        # Bolt Shear
        Ab = math.pi * (db/2)**2
        Rn_bolt = rows * Ab * fv
        
        # Bearing
        Rn_bear_w = rows * (1.2 * fu * db * tw_cm)
        Rn_bear_p = rows * (1.2 * fu * db * tp)
        
        # Block Shear
        R_bs1 = 0.6 * fy * Agv + 1.0 * fu * Ant
        R_bs2 = 0.6 * fu * Anv + 1.0 * fu * Ant
        Rn_bs = min(R_bs1, R_bs2)
        
        # Plate Yield/Rupture
        Rn_yield = 0.6 * fy * (L_gv + lev/10) * tp
        Rn_rup = 0.6 * fu * ((L_gv + lev/10) - rows*dh) * tp
        
        # Find Minimum
        capabilities = {
            "Bolt Shear": Rn_bolt,
            "Bearing (Web)": Rn_bear_w,
            "Bearing (Plate)": Rn_bear_p,
            "Block Shear": Rn_bs,
            "Plate Yield": Rn_yield,
            "Plate Rupture": Rn_rup
        }
        min_cap = min(capabilities.values())
        gov_mode = min(capabilities, key=capabilities.get)
        passed = min_cap >= vu_input

        # --- RENDER REPORT CARD ---
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.markdown('<div class="header-blue">📝 Calculation Report</div>', unsafe_allow_html=True)
        
        # 1. Summary Header
        if passed:
            st.markdown(f'<span class="pass-badge">PASSED</span> Capacity: **{min_cap:,.0f}** kg > Load: **{vu_input:,.0f}** kg', unsafe_allow_html=True)
        else:
            st.markdown(f'<span class="fail-badge">FAILED</span> Capacity: **{min_cap:,.0f}** kg < Load: **{vu_input:,.0f}** kg', unsafe_allow_html=True)
            st.error(f"Failure Mode: {gov_mode}")

        st.markdown("---")
        
        # 2. Detailed Steps (Readable Text)
        st.markdown("**1. Bolt Shear Capacity:**")
        st.latex(fr"R_n = n \times A_b \times F_v = {rows} \times {Ab:.2f} \times {fv} = \mathbf{{{Rn_bolt:,.0f}}} \ kg")
        
        st.markdown("**2. Bearing Capacity (Min of Web/Plate):**")
        st.latex(fr"R_{{bear}} = 1.2 \times F_u \times d \times t \times n = \mathbf{{{min(Rn_bear_w, Rn_bear_p):,.0f}}} \ kg")
        
        st.markdown("**3. Block Shear (The Critical Check):**")
        st.write("Area Calculations:")
        c1, c2, c3 = st.columns(3)
        c1.metric("Agv (Gross Shear)", f"{Agv:.2f} cm²")
        c2.metric("Anv (Net Shear)", f"{Anv:.2f} cm²")
        c3.metric("Ant (Net Tension)", f"{Ant:.2f} cm²")
        
        st.write("Capacity:")
        st.latex(fr"R_{{bs}} = \min(0.6F_u A_{{nv}} + U_{{bs}}F_u A_{{nt}}, \ 0.6F_y A_{{gv}} + U_{{bs}}F_u A_{{nt}})")
        st.latex(fr"R_{{bs}} = \mathbf{{{Rn_bs:,.0f}}} \ kg")
        
        st.markdown('</div>', unsafe_allow_html=True) # End Report Card

# ------------------------------------------
# FOOTER: FUTURE EXTENSIONS
# ------------------------------------------
st.markdown("---")
with st.expander("🚀 What can be built next? (Extensions)"):
    st.markdown("""
    1.  **Cost Estimation:** Real-time pricing of steel and bolts.
    2.  **Report Generation:** Export this calculation card to PDF.
    3.  **Moment Connections:** Add End-plate design modules.
    4.  **Weld Design:** Add Fillet Weld sizing calculator.
    """)
