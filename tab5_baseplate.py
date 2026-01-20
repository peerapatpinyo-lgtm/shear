import streamlit as st
import streamlit.components.v1 as components
import math

def render(res_ctx, v_design):
    # --- 1. ENGINEERING LOGIC ---
    h, b, tw, tf = res_ctx['h']/10, res_ctx['b']/10, res_ctx['tw']/10, res_ctx['tf']/10
    Fy, is_lrfd = res_ctx['Fy'], res_ctx['is_lrfd']

    # --- 2. PROFESSIONAL INTERFACE ---
    with st.container(border=True):
        st.markdown("##### 🏛️ Structural Component Definition")
        c1, c2, c3, c4 = st.columns(4)
        N = c1.number_input("Plate Length N (cm)", value=float(math.ceil(h + 15)))
        B = c2.number_input("Plate Width B (cm)", value=float(math.ceil(b + 15)))
        tp = c3.number_input("Thickness (mm)", value=25.0)
        edge_d = c4.number_input("Edge Dist. (mm)", value=50.0)

    # Calculation AISC Design Guide 1
    m = (N - 0.95*h)/2
    n = (B - 0.80*b)/2
    l_crit = max(m, n, (math.sqrt(h*b)/4))
    t_req = l_crit * math.sqrt((2*v_design)/(0.9*Fy*B*N)) if is_lrfd else l_crit * math.sqrt((2*v_design*1.67)/(Fy*B*N))

    # --- 3. THE ENGINEERING DETAIL (SVG PRECISION) ---
    sc = 200 / max(N, B)
    canvas_w, canvas_h = 800, 500
    px, py = 250, 250  # Center for Plan View
    
    # Coordinates for Anchor Bolts
    eb = edge_d / 10
    bx = (B/2 - eb) * sc
    by = (N/2 - eb) * sc

    svg_code = f"""
    <div style="display: flex; justify-content: center; background: #ffffff; padding: 20px;">
    <svg width="{canvas_w}" height="{canvas_h}" viewBox="0 0 {canvas_w} {canvas_h}" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <pattern id="smallGrid" width="10" height="10" patternUnits="userSpaceOnUse">
                <path d="M 10 0 L 0 0 0 10" fill="none" stroke="#f1f5f9" stroke-width="0.5"/>
            </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#smallGrid)" />

        <text x="{px}" y="40" text-anchor="middle" font-weight="bold" font-family="monospace" font-size="14">BASE PLATE PLAN VIEW</text>
        
        <rect x="{px - B*sc/2}" y="{py - N*sc/2}" width="{B*sc}" height="{N*sc}" fill="none" stroke="#334155" stroke-width="2"/>
        <line x1="{px - B*sc/2 - 20}" y1="{py}" x2="{px + B*sc/2 + 20}" y2="{py}" stroke="#94a3b8" stroke-dasharray="10,5"/>
        <line x1="{px}" y1="{py - N*sc/2 - 20}" x2="{px}" y2="{py + N*sc/2 + 20}" stroke="#94a3b8" stroke-dasharray="10,5"/>

        <g transform="translate({px}, {py})" fill="#cbd5e1" stroke="#1e293b" stroke-width="1.2">
            <rect x="{-b*sc/2}" y="{-h*sc/2}" width="{b*sc}" height="{tf*sc}"/>
            <rect x="{-b*sc/2}" y="{h*sc/2 - tf*sc}" width="{b*sc}" height="{tf*sc}"/>
            <rect x="{-tw*sc/2}" y="{-h*sc/2 + tf*sc}" width="{tw*sc}" height="{(h-2*tf)*sc}"/>
        </g>

        <circle cx="{px-bx}" cy="{py-by}" r="6" fill="none" stroke="#ef4444" stroke-width="2"/>
        <circle cx="{px+bx}" cy="{py-by}" r="6" fill="none" stroke="#ef4444" stroke-width="2"/>
        <circle cx="{px-bx}" cy="{py+by}" r="6" fill="none" stroke="#ef4444" stroke-width="2"/>
        <circle cx="{px+bx}" cy="{py+by}" r="6" fill="none" stroke="#ef4444" stroke-width="2"/>

        <g fill="#475569" font-size="11" font-family="monospace">
            <text x="{px}" y="{py + N*sc/2 + 25}" text-anchor="middle">B = {B} cm</text>
            <text x="{px - B*sc/2 - 40}" y="{py}" text-anchor="middle" transform="rotate(-90 {px-B*sc/2-40} {py})">N = {N} cm</text>
        </g>

        <g transform="translate(550, 100)">
            <text x="75" y="-30" text-anchor="middle" font-weight="bold" font-family="monospace">SECTION A-A</text>
            <rect x="55" y="0" width="40" height="150" fill="#f1f5f9" stroke="#334155"/>
            <rect x="0" y="150" width="150" height="15" fill="#334155" stroke="#000"/>
            <text x="160" y="162" font-size="11" font-weight="bold">PL {tp} mm</text>
            
            <rect x="0" y="165" width="150" height="10" fill="#94a3b8" opacity="0.3"/>
            <line x1="25" y1="130" x2="25" y2="250" stroke="#ef4444" stroke-width="2" stroke-dasharray="4,2"/>
            <line x1="125" y1="130" x2="125" y2="250" stroke="#ef4444" stroke-width="2" stroke-dasharray="4,2"/>
            
            <path d="M 95 150 L 115 130 h 20" fill="none" stroke="#ef4444" stroke-width="1"/>
            <path d="M 100 142 L 110 150 L 90 150 Z" fill="#ef4444"/> <text x="120" y="125" font-size="10" fill="#ef4444">FW E70XX</text>
        </g>
    </svg>
    </div>
    """
    components.html(svg_code, height=canvas_h + 50)

    # --- 4. ENGINEERING VERDICT ---
    st.divider()
    v1, v2, v3 = st.columns(3)
    with v1:
        st.metric("Critical Arm (l)", f"{l_crit:.2f} cm")
    with v2:
        st.metric("Required t", f"{t_req*10:.2f} mm")
    with v3:
        status = "✅ PASS" if tp >= t_req*10 else "🚨 FAIL"
        st.subheader(f"Status: {status}")

    if tp < t_req*10:
        st.error(f"Design is unsafe. Increase Plate Thickness by at least {t_req*10 - tp:.2f} mm")
