import streamlit as st
import streamlit.components.v1 as components
import math

def render(res_ctx, v_design):
    st.markdown("### 🏛️ Advanced Base Plate & Bolt Placement Analysis")
    
    # --- 1. DATA EXTRACTION ---
    h, b, tw, tf = res_ctx['h']/10, res_ctx['b']/10, res_ctx['tw']/10, res_ctx['tf']/10
    Fy, is_lrfd = res_ctx['Fy'], res_ctx['is_lrfd']
    
    # --- 2. COMPREHENSIVE INPUTS ---
    with st.container(border=True):
        st.markdown("##### 🛠️ Design Specification")
        c1, c2, c3, c4 = st.columns(4)
        N = c1.number_input("Plate Length N (cm)", value=float(math.ceil(h + 15)))
        B = c2.number_input("Plate Width B (cm)", value=float(math.ceil(b + 15)))
        tp = c3.number_input("Thickness (mm)", value=25.0)
        fc = c4.number_input("Concrete f'c (ksc)", value=240.0)
        
        st.markdown("##### ⛓️ Bolt Placement (Constructability)")
        c5, c6, c7, c8 = st.columns(4)
        bolt_d = c5.selectbox("Bolt Size (mm)", [16, 20, 24, 30], index=1)
        edge_d = c6.number_input("Edge Distance (mm)", value=50.0)
        # Bolt offset from center calculation
        dist_x = c7.number_input("Bolt Spacing X (cm)", value=B-10.0)
        dist_y = c8.number_input("Bolt Spacing Y (cm)", value=N-10.0)

    # --- 3. ENGINEERING CALCULATIONS ---
    # AISC DG1: Cantilever distances
    m = (N - 0.95*h)/2
    n = (B - 0.80*b)/2
    l_crit = max(m, n, (math.sqrt(h*b)/4))
    t_req = l_crit * math.sqrt((2*v_design)/(0.9*Fy*B*N)) if is_lrfd else l_crit * math.sqrt((2*v_design*1.67)/(Fy*B*N))
    
    # Bolt Clearance Checks
    bolt_c_x = (B - dist_x) / 2 # Edge distance actual (cm)
    bolt_to_flange = (dist_x - b) / 2 # Clearance from flange to bolt center
    
    # --- 4. PRECISION BLUEPRINT (SVG) ---
    sc = 250 / max(N, B)
    canvas_w, canvas_h = 800, 500
    px, py = 250, 250 # Plan Center
    
    # Dynamic Colors based on checks
    edge_color = "#ef4444" if (bolt_c_x * 10) < (1.5 * bolt_d) else "#22c55e"
    wrench_color = "#ef4444" if (bolt_to_flange * 10) < 40 else "#3b82f6"

    svg_code = f"""
    <div style="display: flex; justify-content: center; background: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0;">
    <svg width="{canvas_w}" height="{canvas_h}" viewBox="0 0 {canvas_w} {canvas_h}" xmlns="http://www.w3.org/2000/svg">
        <text x="{px}" y="40" text-anchor="middle" font-weight="bold" font-family="monospace" font-size="14">ENGINEERING PLAN: BOLT & CLEARANCE</text>
        
        <rect x="{px - B*sc/2}" y="{py - N*sc/2}" width="{B*sc}" height="{N*sc}" fill="#f8fafc" stroke="#1e293b" stroke-width="2"/>
        
        <g transform="translate({px}, {py})" fill="#cbd5e1" stroke="#000" stroke-width="1.2">
            <rect x="{-b*sc/2}" y="{-h*sc/2}" width="{b*sc}" height="{tf*sc}"/>
            <rect x="{-b*sc/2}" y="{h*sc/2 - tf*sc}" width="{b*sc}" height="{tf*sc}"/>
            <rect x="{-tw*sc/2}" y="{-h*sc/2 + tf*sc}" width="{tw*sc}" height="{(h-2*tf)*sc}"/>
        </g>

        <g stroke-width="2">
            <circle cx="{px - dist_x/2*sc}" cy="{py - dist_y/2*sc}" r="8" fill="none" stroke="{wrench_color}"/>
            <circle cx="{px + dist_x/2*sc}" cy="{py - dist_y/2*sc}" r="8" fill="none" stroke="{wrench_color}"/>
            <circle cx="{px - dist_x/2*sc}" cy="{py + dist_y/2*sc}" r="8" fill="none" stroke="{wrench_color}"/>
            <circle cx="{px + dist_x/2*sc}" cy="{py + dist_y/2*sc}" r="8" fill="none" stroke="{wrench_color}"/>
        </g>

        <line x1="{px + b/2*sc}" y1="{py}" x2="{px + dist_x/2*sc}" y2="{py}" stroke="{wrench_color}" stroke-dasharray="4"/>
        <text x="{px + (b/2 + dist_x/4)*sc}" y="{py - 10}" fill="{wrench_color}" font-size="10" text-anchor="middle">Wrench: {bolt_to_flange*10:.0f}mm</text>

        <line x1="{px + B/2*sc}" y1="{py + dist_y/2*sc}" x2="{px + dist_x/2*sc}" y2="{py + dist_y/2*sc}" stroke="{edge_color}" />
        <text x="{px + B/2*sc + 10}" y="{py + dist_y/2*sc + 5}" fill="{edge_color}" font-size="10">Edge: {bolt_c_x*10:.0f}mm</text>

        <g transform="translate(550, 120)">
            <text x="80" y="-30" text-anchor="middle" font-weight="bold" font-family="monospace">SECTION A-A</text>
            <rect x="65" y="0" width="30" height="150" fill="#f1f5f9" stroke="#334155"/>
            <rect x="0" y="150" width="160" height="12" fill="#334155"/>
            <text x="170" y="160" font-size="11" font-weight="bold">t={tp}mm</text>
            <path d="M 95 150 L 115 130 h 20" fill="none" stroke="#ef4444" stroke-width="1"/>
            <path d="M 100 142 L 108 150 L 92 150 Z" fill="#ef4444"/>
        </g>
    </svg>
    </div>
    """
    components.html(svg_code, height=520)

    # --- 5. TECHNICAL VERDICT ---
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🛡️ Structural Strength**")
        st.write(f"Req. Thickness: `{t_req*10:.2f} mm`")
        if tp >= t_req*10: st.success("Plate Thickness OK")
        else: st.error("Plate too thin")

    with col2:
        st.markdown("**🔧 Constructability**")
        st.write(f"Wrench Clearance: `{bolt_to_flange*10:.1f} mm`")
        if (bolt_to_flange*10) >= 40: st.success("Clearance OK")
        else: st.warning("Space tight for Wrench")

    with col3:
        st.markdown("**📐 Concrete Edge**")
        st.write(f"Min. Edge (1.5d): `{1.5*bolt_d:.1f} mm`")
        if (bolt_c_x*10) >= (1.5*bolt_d): st.success("Edge Distance OK")
        else: st.error("Edge Distance FAIL")
