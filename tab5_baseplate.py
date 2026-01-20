import streamlit as st
import math

def render(res_ctx, v_design):
    st.subheader("🧱 Column & Base Plate Design (AISC 360-22)")
    
    # --- 1. DATA EXTRACTION ---
    h = res_ctx['h'] / 10      # cm
    b = res_ctx['b'] / 10      # cm
    tw = res_ctx['tw'] / 10    # cm
    tf = res_ctx['tf'] / 10    # cm
    Ag = 2*b*tf + (h-2*tf)*tw  # Cross section area
    ry = res_ctx['ry']         # Radius of gyration
    Fy = res_ctx['Fy']
    E = res_ctx['E']
    is_lrfd = res_ctx['is_lrfd']

    st.markdown("---")
    col_input, col_result = st.columns([1, 1.2])

    with col_input:
        st.markdown("#### 📏 Column & Material")
        col_h_m = st.number_input("Column Height (m)", 0.5, 20.0, 3.0, step=0.1)
        k_f = st.selectbox("Effective Length Factor (K)", [2.1, 1.2, 1.0, 0.8, 0.65], index=2)
        fc_prime = st.number_input("Concrete f'c (ksc)", 150, 450, 240)

        st.markdown("#### 🧱 Plate & Anchors")
        N = st.number_input("Plate Length N (cm)", value=float(math.ceil(h + 10)))
        B = st.number_input("Plate Width B (cm)", value=float(math.ceil(b + 10)))
        bolt_dist = st.slider("Bolt Edge Distance (mm)", 30, 100, 50) / 10 # cm

    # --- 2. COLUMN STABILITY CALCULATION ---
    L = col_h_m * 100
    slenderness = (k_f * L) / ry
    Fe = (math.pi**2 * E) / (slenderness**2) if slenderness > 0 else 1
    
    if slenderness <= 4.71 * math.sqrt(E/Fy):
        Fcr = (0.658**(Fy/Fe)) * Fy
    else:
        Fcr = 0.877 * Fe
    
    Pn = Fcr * Ag
    P_cap = (0.9 * Pn) if is_lrfd else (Pn / 1.67)

    # --- 3. BASE PLATE CALCULATION ---
    A1 = N * B
    Pp = (0.65 * 0.85 * fc_prime * A1) if is_lrfd else (0.85 * fc_prime * A1 / 2.31)
    
    # Thickness based on bending (m, n)
    m = (N - 0.95 * h) / 2
    n = (B - 0.80 * b) / 2
    l_max = max(m, n, 0)
    
    if is_lrfd:
        t_req = l_max * math.sqrt((2 * v_design) / (0.9 * Fy * B * N)) if A1 > 0 else 0
    else:
        t_req = l_max * math.sqrt((2 * v_design * 1.67) / (Fy * B * N)) if A1 > 0 else 0

    # --- 4. DISPLAY RESULTS ---
    with col_result:
        # Dashboard
        c1, c2 = st.columns(2)
        c1.metric("Column Ratio", f"{v_design/P_cap:.1%}", delta_color="inverse")
        c2.metric("Min Thickness", f"{t_req*10:.1f} mm")

        # Visual Drafting (SVG)
        st.markdown("#### 🎨 Drafting View (Top View)")
        
        # Scale factors for drawing
        scale = 200 / max(N, B)
        dw, dh = B * scale, N * scale
        sh, sw = h * scale, b * scale
        stw, stf = tw * scale, tf * scale
        ed = bolt_dist * scale

        svg = f"""
        <svg width="300" height="300" viewBox="-50 -50 300 300" xmlns="http://www.w3.org/2000/svg">
            <rect x="0" y="0" width="{dw}" height="{dh}" fill="#e5e7eb" stroke="#374151" stroke-width="2"/>
            <g transform="translate({(dw-sw)/2}, {(dh-sh)/2})">
                <rect x="0" y="0" width="{sw}" height="{stf}" fill="#1e40af" />
                <rect x="0" y="{sh-stf}" width="{sw}" height="{stf}" fill="#1e40af" />
                <rect x="{(sw-stw)/2}" y="{stf}" width="{stw}" height="{sh-2*stf}" fill="#1e40af" />
            </g>
            <circle cx="{ed}" cy="{ed}" r="5" fill="#ef4444" />
            <circle cx="{dw-ed}" cy="{ed}" r="5" fill="#ef4444" />
            <circle cx="{ed}" cy="{dh-ed}" r="5" fill="#ef4444" />
            <circle cx="{dw-ed}" cy="{dh-ed}" r="5" fill="#ef4444" />
            <text x="{dw/2}" y="-10" text-anchor="middle" font-size="12" fill="#374151">B = {B} cm</text>
            <text x="-10" y="{dh/2}" text-anchor="middle" font-size="12" fill="#374151" transform="rotate(-90, -10, {dh/2})">N = {N} cm</text>
        </svg>
        """
        st.write(svg, unsafe_allow_html=True)

    # Status Indicators
    if v_design > P_cap:
        st.error(f"❌ เสาโก่งเดาะ (Column Buckling)! แรงกด {v_design:,.0f} kg เกินความสามารถ {P_cap:,.0f} kg")
    elif slenderness > 200:
        st.warning(f"⚠️ เสาชะลูดเกินไป (KL/r = {slenderness:.1f} > 200)")
    else:
        st.success(f"✅ โครงสร้างเสาและแผ่นฐานมั่นคง (Safety Factor OK)")
