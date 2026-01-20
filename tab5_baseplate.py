import streamlit as st
import math

def render(res_ctx, v_design):
    st.markdown("<h2 style='text-align: center; color: #1e3a8a;'>🏗️ Construction Detail & Analysis</h2>", unsafe_allow_html=True)

    # --- 1. SETUP DATA ---
    h, b, tw, tf = res_ctx['h']/10, res_ctx['b']/10, res_ctx['tw']/10, res_ctx['tf']/10
    Fy, E, is_lrfd = res_ctx['Fy'], res_ctx['E'], res_ctx['is_lrfd']
    
    # --- 2. ADVANCED INPUTS ---
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("##### 📏 Dimensions")
            N = st.number_input("Plate Length N (cm)", value=float(math.ceil(h + 15)))
            B = st.number_input("Plate Width B (cm)", value=float(math.ceil(b + 15)))
            tp = st.number_input("Thickness (mm)", 10, 100, 25) / 10
        with c2:
            st.markdown("##### ⛓️ Anchors")
            bolt_d = st.selectbox("Bolt Size (mm)", [16, 20, 24, 30, 36], index=1)
            edge_dist = st.slider("Edge Dist (mm)", 30, 100, 50) / 10
        with c3:
            st.markdown("##### 🏗️ Field Detail")
            grout_t = st.slider("Grout Thick (mm)", 10, 60, 30) / 10
            fc = st.number_input("Concrete f'c (ksc)", 150, 450, 240)

    # --- 3. ENGINEERING CALCULATIONS (AISC Design Guide 1) ---
    A1 = N * B
    Pp = 0.85 * fc * A1 * 2.0 # Assume A2/A1 = 4.0 -> sqrt = 2
    phi_b = 0.65 if is_lrfd else 1/2.31
    P_cap = phi_b * Pp
    
    # Thickness check (Plastic Moment)
    m = (N - 0.95*h)/2
    n = (B - 0.80*b)/2
    l_crit = max(m, n, (math.sqrt(h*b)/4))
    t_req = l_crit * math.sqrt((2*v_design)/(0.9*Fy*B*N)) if is_lrfd else l_crit * math.sqrt((2*v_design*1.67)/(Fy*B*N))

    # --- 4. THE "MASTER DETAIL" DRAWING (SVG) ---
    st.markdown("#### 📐 Construction Section Detail")
    
    # SVG Configuration
    cv_w, cv_h = 600, 350
    # Scale calculation
    scale = 200 / max(N, (h + 15)) # Scale based on total height of drawing
    
    # Coordinates
    base_y = 250
    plate_h = tp * scale
    grout_h = grout_t * scale
    col_w = h * scale
    plate_w = N * scale
    
    svg = f"""
    <svg width="100%" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <rect x="50" y="{base_y}" width="500" height="100" fill="#f3f4f6" stroke="#9ca3af" stroke-width="1"/>
        <text x="540" y="{base_y + 30}" font-size="12" fill="#9ca3af" text-anchor="end">CONCRETE PEDESTAL</text>
        
        <rect x="80" y="{base_y - grout_h}" width="440" height="{grout_h}" fill="#94a3b8" opacity="0.6"/>
        <text x="525" y="{base_y - grout_h/2}" font-size="10" fill="#475569" dy="3">NON-SHRINK GROUT ({grout_t*10}mm)</text>
        
        <rect x="{(cv_w - plate_w)/2}" y="{base_y - grout_h - plate_h}" width="{plate_w}" height="{plate_h}" fill="#334155" stroke="#000" stroke-width="1"/>
        <text x="{(cv_w + plate_w)/2 + 10}" y="{base_y - grout_h - plate_h/2}" font-size="12" fill="#1e293b" dy="4">PLATE t={tp*10}mm</text>
        
        <rect x="{(cv_w - col_w)/2}" y="50" width="{col_w}" height="{base_y - grout_h - plate_h - 50}" fill="#1e40af" fill-opacity="0.9"/>
        <line x1="{(cv_w - col_w)/2 + tf*scale}" y1="50" x2="{(cv_w - col_w)/2 + tf*scale}" y2="{base_y - grout_h - plate_h}" stroke="#1e3a8a" stroke-width="1" stroke-dasharray="4"/>
        <line x1="{(cv_w + col_w)/2 - tf*scale}" y1="50" x2="{(cv_w + col_w)/2 - tf*scale}" y2="{base_y - grout_h - plate_h}" stroke="#1e3a8a" stroke-width="1" stroke-dasharray="4"/>
        
        <g stroke="#ef4444" stroke-width="3">
            <line x1="{(cv_w - plate_w)/2 + edge_dist*scale}" y1="{base_y - grout_h - plate_h - 20}" x2="{(cv_w - plate_w)/2 + edge_dist*scale}" y2="{base_y + 80}"/>
            <line x1="{(cv_w + plate_w)/2 - edge_dist*scale}" y1="{base_y - grout_h - plate_h - 20}" x2="{(cv_w + plate_w)/2 - edge_dist*scale}" y2="{base_y + 80}"/>
            <rect x="{(cv_w - plate_w)/2 + edge_dist*scale - 8}" y="{base_y - grout_h - plate_h - 25}" width="16" height="8" fill="#ef4444"/>
            <rect x="{(cv_w + plate_w)/2 - edge_dist*scale - 8}" y="{base_y - grout_h - plate_h - 25}" width="16" height="8" fill="#ef4444"/>
        </g>
        
        <path d="M {(cv_w + col_w)/2} {base_y - grout_h - plate_h} L {(cv_w + col_w)/2 + 20} {base_y - grout_h - plate_h - 20} h 30" fill="none" stroke="#dc2626" stroke-width="1"/>
        <text x="{(cv_w + col_w)/2 + 25}" y="{base_y - grout_h - plate_h - 25}" font-size="10" fill="#dc2626">FILLET E70XX</text>

        <line x1="{(cv_w - plate_w)/2}" y1="{base_y + 20}" x2="{(cv_w + plate_w)/2}" y2="{base_y + 20}" stroke="#475569" stroke-width="1"/>
        <text x="{cv_w/2}" y="{base_y + 35}" text-anchor="middle" font-size="12" fill="#475569">N = {N} cm</text>
    </svg>
    """
    st.write(svg, unsafe_allow_html=True)

    # --- 5. DETAILED ANALYSIS SUMMARY ---
    st.divider()
    col_res1, col_res2 = st.columns(2)
    
    with col_res1:
        st.write("📊 **Limit State Verification**")
        bearing_ratio = v_design / P_cap
        st.write(f"Concrete Bearing: `{bearing_ratio:.2%}`")
        st.progress(min(bearing_ratio, 1.0))
        
        thick_ratio = t_req / tp
        st.write(f"Plate Bending: `{thick_ratio:.2%}`")
        st.progress(min(thick_ratio, 1.0))

    with col_res2:
        st.write("📝 **Engineering Remarks**")
        if tp < t_req:
            st.error(f"❌ Plate thickness ({tp*10}mm) is insufficient. Min: {t_req*10:.1f}mm")
        else:
            st.success(f"✅ Design is adequate for axial load {v_design:,.0f} kg")
        st.caption(f"Min. Bolt Embedment: {bolt_d * 12 / 10:.1f} cm (AISC Recommendation)")
