import streamlit as st
import math
import pandas as pd

def render(res_ctx, v_design):
    st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>🏛️ Structural Base Plate & Anchor Suite</h2>", unsafe_allow_html=True)
    
    # --- 1. ENGINEERING CONTEXT ---
    h, b, tw, tf = res_ctx['h']/10, res_ctx['b']/10, res_ctx['tw']/10, res_ctx['tf']/10
    Fy, E, is_lrfd = res_ctx['Fy'], res_ctx['E'], res_ctx['is_lrfd']
    Ag, ry = (2*b*tf + (h-2*tf)*tw), res_ctx['ry']
    k_dim = tf + 1.5 # k-distance for H-beam
    M_applied = res_ctx.get('M_max', 0) # ดึง Moment จาก Tab คำนวณคาน/เสา

    # --- 2. ADVANCED INPUTS ---
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("##### 📏 Geometry & Loads")
            col_h = st.number_input("Column Height (m)", value=4.0)
            k_val = st.selectbox("K-Factor", [2.1, 1.0, 0.85, 0.65], index=1)
            p_axial = v_design # Force from Tab 1
        with col2:
            st.markdown("##### 🧱 Plate Design")
            N = st.number_input("Length N (cm)", value=float(math.ceil(h + 15)))
            B = st.number_input("Width B (cm)", value=float(math.ceil(b + 15)))
            tp = st.number_input("Trial Thickness (mm)", value=25.0) / 10 # cm
        with col3:
            st.markdown("##### 🏗️ Foundation & Weld")
            fc = st.number_input("Concrete f'c (ksc)", value=240.0)
            w_size = st.slider("Weld Size (mm)", 3, 16, 6) / 10 # cm

    # --- 3. PROFESSIONAL ENGINE (AISC Design Guide 1) ---
    # A. Concrete Bearing Check
    A1 = N * B
    A2 = A1 * 2.0 # Assume pedestal area
    Pp_max = min(0.85 * fc * A1 * math.sqrt(A2/A1), 1.7 * fc * A1)
    phi_b = 0.65 if is_lrfd else 1.0
    P_avail_bearing = (phi_b * Pp_max) if is_lrfd else (Pp_max / 2.31)
    
    # B. Column Buckling (AISC 360 Chapter E)
    slenderness = (k_val * col_h * 100) / ry
    Fe = (math.pi**2 * E) / (slenderness**2) if slenderness > 0 else 0.1
    Fcr = (0.658**(Fy/Fe)) * Fy if slenderness <= 4.71*math.sqrt(E/Fy) else 0.877 * Fe
    P_column_cap = (0.9 * Fcr * Ag) if is_lrfd else (Fcr * Ag / 1.67)

    # C. Plate Thickness Optimization (Based on Plastic Moment)
    m = (N - 0.95*h)/2
    n = (B - 0.80*b)/2
    # Lambda optimization for large loads
    X = ((4*h*b)/((h+b)**2)) * (p_axial/P_avail_bearing if P_avail_bearing > 0 else 0)
    lambda_val = min(1.0, (2*math.sqrt(X))/(1+math.sqrt(1-X)) if X < 1 else 1.0)
    l_crit = max(m, n, lambda_val * (math.sqrt(h*b)/4))
    
    t_req = l_crit * math.sqrt((2*p_axial)/(0.9*Fy*B*N)) if is_lrfd else l_crit * math.sqrt((2*p_axial*1.67)/(Fy*B*N))

    # D. Weld Design (AISC Ch. J)
    # Strength of Fillet Weld
    Rn_weld = 0.6 * 4900 * (0.707 * w_size) * (2*h + 2*b) # Simple total length
    P_weld_cap = (0.75 * Rn_weld) if is_lrfd else (Rn_weld / 2.0)

    # --- 4. DATA VISUALIZATION (ENGINEERING VIEW) ---
    st.divider()
    v1, v2 = st.columns([1.2, 1])
    
    with v1:
        st.markdown("#### 📐 Engineering Drafting (Scale View)")
        sc = 250 / max(N, B)
        # SVG Draw
        dw, dh = B*sc, N*sc
        sw, sh = b*sc, h*sc
        
        svg = f"""
        <svg width="100%" height="350" viewBox="-40 -40 330 330">
            <rect x="-10" y="-10" width="{dw+20}" height="{dh+20}" fill="#f1f5f9" stroke="#cbd5e1" stroke-dasharray="4"/>
            <rect x="0" y="0" width="{dw}" height="{dh}" fill="#e2e8f0" stroke="#475569" stroke-width="2"/>
            <g transform="translate({(dw-sw)/2}, {(dh-sh)/2})">
                <rect x="0" y="0" width="{sw}" height="{tf*sc}" fill="#1e40af" />
                <rect x="0" y="{sh-tf*sc}" width="{sw}" height="{tf*sc}" fill="#1e40af" />
                <rect x="{(sw-tw*sc)/2}" y="{tf*sc}" width="{tw*sc}" height="{(sh-2*tf*sc)}" fill="#1e40af" />
                <rect x="0" y="{tf*sc}" width="{sw}" height="2" fill="#ef4444" opacity="0.6"/>
                <rect x="0" y="{sh-tf*sc-2}" width="{sw}" height="2" fill="#ef4444" opacity="0.6"/>
            </g>
            <text x="{dw/2}" y="-15" text-anchor="middle" font-size="12" fill="#1e3a8a">B = {B} cm</text>
            <text x="-25" y="{dh/2}" text-anchor="middle" font-size="12" fill="#1e3a8a" transform="rotate(-90 -25 {dh/2})">N = {N} cm</text>
        </svg>
        """
        st.write(svg, unsafe_allow_html=True)
        

    with v2:
        st.markdown("#### 📊 Stress States & Limit States")
        
        # Utilization Chart
        metrics = {
            "Bearing Pressure": p_axial / P_avail_bearing,
            "Column Buckling": p_axial / P_column_cap,
            "Weld Strength": p_axial / P_weld_cap,
            "Plate Bending": t_req / tp
        }
        
        for m_name, m_val in metrics.items():
            color = "red" if m_val > 1.0 else "#10b981"
            st.write(f"**{m_name}** ({m_val:.1%})")
            st.progress(min(m_val, 1.0))
            
        st.markdown(f"""
        <div style="background:#f8fafc; padding:15px; border-radius:10px; border-left:5px solid #1e40af;">
            <p style="margin:0; font-size:0.9em; color:#64748b;">RESULTANT MIN. THICKNESS</p>
            <h2 style="margin:0; color:#1e40af;">{t_req*10:.2f} mm</h2>
            <p style="margin:0; font-size:0.8em; color:{'#10b981' if tp >= t_req else '#ef4444'}">
                {'✅ Trial thickness is sufficient' if tp >= t_req else '❌ Increase trial thickness'}
            </p>
        </div>
        """, unsafe_allow_html=True)

    # --- 5. PROFESSIONAL FOOTER (Calculated Steps) ---
    with st.expander("📝 Detailed Engineering Verification (AISC Methodology)"):
        st.markdown(f"""
        - **Concrete Capacity ($P_p$):** {Pp_max/1000:.2f} Ton (AISC J8)
        - **Critical Cantilever ($l$):** max({m:.2f}, {n:.2f}, $\lambda n'$) = {l_crit:.2f} cm
        - **Required $t_p$:** $\sqrt{{(2 \cdot P) / (0.9 \cdot F_y \cdot B \cdot N)}} \cdot l$ = {t_req*10:.2f} mm
        - **Weld Capacity:** {P_weld_cap/1000:.2f} Ton (Based on E70XX)
        """)
        
        

    if slenderness > 200:
        st.warning("⚠️ **Warning:** Slenderness ratio $KL/r$ exceeds 200. Check AISC Section E2.")
    if p_axial > P_column_cap:
        st.error("🚨 **Failure:** Applied axial load exceeds Column Buckling capacity.")
