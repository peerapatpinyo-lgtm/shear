import streamlit as st
import math

def render(res_ctx, v_design):
    # --- 1. SETUP & THEME ---
    st.markdown("""<h3 style='color: #1e3a8a;'>🧱 Advanced Base Plate & Column Stability</h3>""", unsafe_allow_html=True)
    
    # ดึงค่าพื้นฐาน
    h, b, tw, tf = res_ctx['h']/10, res_ctx['b']/10, res_ctx['tw']/10, res_ctx['tf']/10
    Fy, E, is_lrfd = res_ctx['Fy'], res_ctx['E'], res_ctx['is_lrfd']
    Ag, ry = 2*b*tf + (h-2*tf)*tw, res_ctx['ry']
    sec_name = res_ctx['sec_name']

    # --- 2. USER INPUTS (Interactive) ---
    with st.expander("🛠️ Design Parameters & Environment", expanded=True):
        col_in1, col_in2, col_in3 = st.columns(3)
        with col_in1:
            st.markdown("**Column Info**")
            L_m = st.number_input("Column Height (m)", 0.1, 25.0, 4.0)
            k_val = st.selectbox("K Factor", [2.1, 1.2, 1.0, 0.8, 0.65], index=2, help="K=1.0 for Pinned, K=2.1 for Cantilever")
        with col_in2:
            st.markdown("**Base Plate Geometry**")
            N = st.number_input("Plate Length N (cm)", value=float(math.ceil(h + 10)))
            B = st.number_input("Plate Width B (cm)", value=float(math.ceil(b + 10)))
        with col_in3:
            st.markdown("**Foundations**")
            fc = st.number_input("Concrete f'c (ksc)", 150, 450, 240)
            pedestal_area_ratio = st.slider("Area Ratio (A2/A1)", 1.0, 4.0, 1.0, help="1.0 means plate size = pedestal size")

    # --- 3. CORE CALCULATIONS ---
    # A. Column Buckling
    slenderness = (k_val * L_m * 100) / ry
    Fe = (math.pi**2 * E) / (slenderness**2) if slenderness > 0 else 0.1
    if slenderness <= 4.71 * math.sqrt(E/Fy):
        Fcr = (0.658**(Fy/Fe)) * Fy
    else:
        Fcr = 0.877 * Fe
    Pn = Fcr * Ag
    phi_c, omg_c = 0.90, 1.67
    P_cap = (phi_c * Pn) if is_lrfd else (Pn / omg_c)

    # B. Concrete Bearing (AISC J8)
    A1 = N * B
    # Pp = 0.85 * f'c * A1 * sqrt(A2/A1)
    Pp_nominal = 0.85 * fc * A1 * math.sqrt(pedestal_area_ratio)
    limit_Pp = 1.7 * fc * A1 # Limit Pp max
    Pp = min(Pp_nominal, limit_Pp)
    phi_b, omg_b = 0.65, 2.31
    P_bearing_cap = (phi_b * Pp) if is_lrfd else (Pp / omg_b)

    # C. Plate Thickness (AISC Design Guide 1)
    # Calculate m, n, and lambda*n'
    m_dist = (N - 0.95*h)/2
    n_dist = (B - 0.80*b)/2
    n_prime = math.sqrt(h * b) / 4
    l_crit = max(m_dist, n_dist, n_prime)
    
    # Required thickness formula
    if is_lrfd:
        t_req = l_crit * math.sqrt((2 * v_design) / (0.9 * Fy * B * N))
    else:
        t_req = l_crit * math.sqrt((2 * v_design * 1.67) / (Fy * B * N))

    # --- 4. VISUALIZATION ENGINE ---
    col_vis, col_stat = st.columns([1.5, 1])
    
    with col_vis:
        st.markdown(f"#### 📐 Drafting & Stress Points: {sec_name}")
        # SVG Logic
        canvas = 350
        pad = 40
        scale = (canvas - 2*pad) / max(N, B)
        # Coordinates
        dw, dh = B * scale, N * scale
        sw, sh = b * scale, h * scale
        off_x, off_y = (canvas-dw)/2, (canvas-dh)/2
        
        svg = f"""
        <svg width="100%" height="{canvas}" viewBox="0 0 {canvas} {canvas}" xmlns="http://www.w3.org/2000/svg">
            <rect x="{off_x}" y="{off_y}" width="{dw}" height="{dh}" fill="#f3f4f6" stroke="#1f2937" stroke-width="2"/>
            <text x="{off_x + dw/2}" y="{off_y - 10}" text-anchor="middle" font-size="12" fill="#4b5563">B = {B} cm</text>
            <text x="{off_x - 10}" y="{off_y + dh/2}" text-anchor="middle" font-size="12" fill="#4b5563" transform="rotate(-90 {off_x-10} {off_y+dh/2})">N = {N} cm</text>
            
            <g transform="translate({(canvas-sw)/2}, {(canvas-sh)/2})">
                <rect x="0" y="0" width="{sw}" height="{tf*scale}" fill="#3b82f6" fill-opacity="0.8"/>
                <rect x="0" y="{sh - tf*scale}" width="{sw}" height="{tf*scale}" fill="#3b82f6" fill-opacity="0.8"/>
                <rect x="{(sw - tw*scale)/2}" y="{tf*scale}" width="{tw*scale}" height="{sh - 2*tf*scale}" fill="#3b82f6" fill-opacity="0.8"/>
            </g>
            
            <line x1="{off_x + dw}" y1="{off_y + dh/2}" x2="{off_x + dw - n_dist*scale}" y2="{off_y + dh/2}" stroke="#ef4444" stroke-dasharray="4"/>
            <text x="{off_x + dw - 5}" y="{off_y + dh/2 - 5}" font-size="10" fill="#ef4444" text-anchor="end">n</text>
        </svg>
        """
        st.write(svg, unsafe_allow_html=True)
        

    with col_stat:
        st.markdown("#### 📊 Design Summary")
        
        # 1. Column Status
        c_ratio = v_design / P_cap
        st.write(f"**1. Column Stability ({'LRFD' if is_lrfd else 'ASD'})**")
        st.progress(min(c_ratio, 1.0))
        st.caption(f"Ratio: {c_ratio:.2%} (Limit: {P_cap:,.0f} kg)")
        
        # 2. Bearing Status
        b_ratio = v_design / P_bearing_cap
        st.write(f"**2. Concrete Bearing**")
        st.progress(min(b_ratio, 1.0))
        st.caption(f"Ratio: {b_ratio:.2%} (Limit: {P_bearing_cap:,.0f} kg)")

        # 3. Thickness Result
        st.markdown(f"""
        <div style="background:#eff6ff; padding:15px; border-radius:10px; border-left:5px solid #2563eb; margin-top:10px;">
            <span style="font-size:0.8em; color:#1e40af;">REQUIRED PLATE THICKNESS</span><br>
            <span style="font-size:1.8em; font-weight:bold; color:#1e3a8a;">{t_req*10:.2f} mm</span>
        </div>
        """, unsafe_allow_html=True)

    # --- 5. TECHNICAL FOOTNOTE ---
    if slenderness > 200:
        st.error(f"⚠️ Slenderness ratio (KL/r = {slenderness:.1f}) exceeds AISC limit of 200.")
    elif c_ratio > 1.0:
        st.error(f"❌ Column section is insufficient for axial load (Overstressed).")
    else:
        st.success("✅ Structural integrity of Column and Base Plate is within safe limits.")
