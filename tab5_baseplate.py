import streamlit as st
import math
import pandas as pd

def render(res_ctx, v_design):
    st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>🏗️ Advanced Structural Base Plate Design</h2>", unsafe_allow_html=True)
    st.caption("AISC 360-22 & Design Guide 1: Base Plate and Anchor Rod Design")

    # --- 1. PRECISE DATA EXTRACTION ---
    try:
        h, b = res_ctx['h']/10, res_ctx['b']/10       # Depth and Width (cm)
        tw, tf = res_ctx['tw']/10, res_ctx['tf']/10   # Web and Flange (cm)
        Fy = res_ctx['Fy']                            # Steel Yield (kg/cm2)
        E = res_ctx['E']                              # Modulus (kg/cm2)
        is_lrfd = res_ctx['is_lrfd']
        fc = 240 # Default concrete f'c
    except KeyError:
        st.error("Please complete Section Selection in Tab 1 first.")
        return

    # --- 2. ENGINEERING INPUTS ---
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("##### 📏 Plate Dimensions")
            N = st.number_input("Length N (Parallel to Depth, cm)", value=float(math.ceil(h + 10)), step=1.0)
            B = st.number_input("Width B (Parallel to Flange, cm)", value=float(math.ceil(b + 10)), step=1.0)
        with col2:
            st.markdown("##### 🧱 Material & Grout")
            fc_input = st.number_input("Concrete f'c (ksc)", 150, 450, 240)
            grout_t = st.slider("Grout Thickness (mm)", 10, 50, 25)
        with col3:
            st.markdown("##### ⛓️ Anchor Rods")
            bolt_dia = st.selectbox("Rod Diameter (mm)", [16, 20, 24, 30, 36], index=1)
            edge_d = st.slider("Edge Distance (mm)", 35, 100, 50)

    # --- 3. THE "REAL" ENGINEERING CALCULATIONS ---
    A1 = N * B
    A2 = A1 * 4.0  # Conservative Pedestal Area assumption
    
    # 3.1 Bearing Strength (AISC J8)
    Pp = 0.85 * fc_input * A1 * min(math.sqrt(A2/A1), 2.0)
    phi_brg = 0.65 if is_lrfd else 1/2.31
    P_avail = phi_brg * Pp
    
    # 3.2 Required Thickness (Design Guide 1 - Plastic Stress Block)
    # Cantilever dimensions
    m = (N - 0.95 * h) / 2
    n = (B - 0.80 * b) / 2
    
    # Lambda optimization (AISC Eq. 3.1.1)
    X = ( (4 * h * b) / (h + b)**2 ) * (v_design / P_avail if P_avail > 0 else 1)
    lam = (2 * math.sqrt(X)) / (1 + math.sqrt(1 - X)) if X < 1 else 1.0
    n_prime = math.sqrt(h * b) / 4
    
    # Governing cantilever distance
    l_crit = max(m, n, lam * n_prime)
    
    # Thickness calculation
    phi_b = 0.90
    t_req = l_crit * math.sqrt((2 * v_design) / (phi_b * Fy * B * N)) if is_lrfd else \
            l_crit * math.sqrt((2 * v_design * 1.67) / (Fy * B * N))

    # --- 4. PROFESSIONAL ENGINEERING DRAWING (TOP VIEW) ---
    st.markdown("#### 📐 Engineering Detail Drawing")
    
    # SVG Constants
    view_box = 400
    scale = 300 / max(N, B)
    off = (view_box - max(N, B)*scale) / 2
    
    svg = f"""
    <svg width="100%" height="400" viewBox="0 0 {view_box} {view_box}" xmlns="http://www.w3.org/2000/svg">
        <line x1="{view_box/2}" y1="10" x2="{view_box/2}" y2="{view_box-10}" stroke="#94a3b8" stroke-dasharray="8,4" stroke-width="1"/>
        <line x1="10" y1="{view_box/2}" x2="{view_box-10}" y2="{view_box/2}" stroke="#94a3b8" stroke-dasharray="8,4" stroke-width="1"/>

        <rect x="{(view_box - B*scale)/2}" y="{(view_box - N*scale)/2}" width="{B*scale}" height="{N*scale}" 
              fill="#f8fafc" stroke="#1e293b" stroke-width="2"/>
        
        <g transform="translate({view_box/2}, {view_box/2})">
            <rect x="{-b*scale/2}" y="{-h*scale/2}" width="{b*scale}" height="{tf*scale}" fill="#334155"/>
            <rect x="{-b*scale/2}" y="{h*scale/2 - tf*scale}" width="{b*scale}" height="{tf*scale}" fill="#334155"/>
            <rect x="{-tw*scale/2}" y="{-h*scale/2 + tf*scale}" width="{tw*scale}" height="{(h-2*tf)*scale}" fill="#334155"/>
        </g>

        <line x1="{(view_box + B*scale)/2}" y1="{(view_box)/2}" x2="{(view_box + B*scale)/2 - n*scale}" y2="{(view_box)/2}" stroke="#ef4444" stroke-width="2"/>
        <text x="{(view_box + B*scale)/2 - 15}" y="{view_box/2 - 5}" fill="#ef4444" font-size="12" font-weight="bold">n</text>
        
        <line x1="{(view_box)/2}" y1="{(view_box + N*scale)/2}" x2="{(view_box)/2}" y2="{(view_box + N*scale)/2 - m*scale}" stroke="#ef4444" stroke-width="2"/>
        <text x="{view_box/2 + 5}" y="{(view_box + N*scale)/2 - 15}" fill="#ef4444" font-size="12" font-weight="bold">m</text>

        <circle cx="{(view_box - B*scale)/2 + edge_d/10*scale}" cy="{(view_box - N*scale)/2 + edge_d/10*scale}" r="{bolt_dia/20*scale}" fill="none" stroke="#dc2626" stroke-width="2"/>
        <circle cx="{(view_box + B*scale)/2 - edge_d/10*scale}" cy="{(view_box - N*scale)/2 + edge_d/10*scale}" r="{bolt_dia/20*scale}" fill="none" stroke="#dc2626" stroke-width="2"/>
        <circle cx="{(view_box - B*scale)/2 + edge_d/10*scale}" cy="{(view_box + N*scale)/2 - edge_d/10*scale}" r="{bolt_dia/20*scale}" fill="none" stroke="#dc2626" stroke-width="2"/>
        <circle cx="{(view_box + B*scale)/2 - edge_d/10*scale}" cy="{(view_box + N*scale)/2 - edge_d/10*scale}" r="{bolt_dia/20*scale}" fill="none" stroke="#dc2626" stroke-width="2"/>
    </svg>
    """
    
    col_v, col_s = st.columns([1.5, 1])
    with col_v:
        st.write(svg, unsafe_allow_html=True)
        
        
    with col_s:
        st.write("📊 **Technical Summary**")
        st.metric("Critical Distance ($l$)", f"{l_crit:.2f} cm")
        st.metric("Required Thickness", f"{t_req*10:.2f} mm")
        
        util = v_design / P_avail
        st.write(f"Bearing Utilization: **{util:.1%}**")
        st.progress(min(util, 1.0))
        
        if util > 1.0:
            st.error("❌ BEARING FAILURE: Increase Plate Area")
        else:
            st.success("✅ BEARING CAPACITY OK")

    # --- 5. DETAILED CALCULATION LOG ---
    with st.expander("📝 View Detailed Verification (AISC Methodology)"):
        st.write(f"- Applied Axial Load: {v_design:,.0f} kg")
        st.write(f"- Concrete Bearing Strength ($P_p$): {Pp:,.0f} kg")
        st.write(f"- Dimension m: {m:.2f} cm | n: {n:.2f} cm")
        st.write(f"- Optimization Parameter $\lambda$: {lam:.3f}")
        st.write(f"- Design Governing Length: {l_crit:.2f} cm")
