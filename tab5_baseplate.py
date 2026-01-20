import streamlit as st
import math

def render(res_ctx, v_design):
    # --- 1. DATA & AISC DG1 LOGIC ---
    h, b, tw, tf = res_ctx['h']/10, res_ctx['b']/10, res_ctx['tw']/10, res_ctx['tf']/10
    Fy, is_lrfd = res_ctx['Fy'], res_ctx['is_lrfd']

    # --- 2. INPUT INTERFACE ---
    with st.container(border=True):
        st.markdown("##### 📐 Engineering Specification")
        c1, c2, c3, c4 = st.columns(4)
        N = c1.number_input("Plate Length N (cm)", value=float(math.ceil(h + 15)))
        B = c2.number_input("Plate Width B (cm)", value=float(math.ceil(b + 15)))
        tp_mm = c3.number_input("Plate Thickness (mm)", value=25.0)
        bolt_d = c4.selectbox("Bolt Size (mm)", [16, 20, 24, 30])

    # AISC Calculation
    m = (N - 0.95*h)/2
    n = (B - 0.80*b)/2
    n_prime = math.sqrt(h * b) / 4
    l_crit = max(m, n, n_prime)
    t_req = l_crit * math.sqrt((2*v_design)/(0.9*Fy*B*N)) if is_lrfd else l_crit * math.sqrt((2*v_design*1.67)/(Fy*B*N))

    # --- 3. THE MASTER BLUEPRINT (SVG PRECISION) ---
    sc = 220 / max(N, B)
    canvas_w, canvas_h = 800, 500
    px, py = 250, 250 # Plan Center
    
    svg = f"""
    <svg width="100%" height="{canvas_h}" viewBox="0 0 {canvas_w} {canvas_h}" style="background:#fdfdfd; border:2px solid #334155;">
        <rect x="10" y="10" width="780" height="480" fill="none" stroke="#334155" stroke-width="1"/>
        <line x1="550" y1="10" x2="550" y2="490" stroke="#334155" stroke-width="1"/>
        
        <text x="{px}" y="40" text-anchor="middle" font-weight="bold" font-family="monospace" font-size="16">BASE PLATE PLAN</text>
        
        <g stroke="#94a3b8" stroke-width="1" stroke-dasharray="10,5,2,5">
            <line x1="{px - B*sc/2 - 30}" y1="{py}" x2="{px + B*sc/2 + 30}" y2="{py}"/>
            <line x1="{px}" y1="{py - N*sc/2 - 30}" x2="{px}" y2="{py + N*sc/2 + 30}"/>
        </g>

        <rect x="{px - B*sc/2}" y="{py - N*sc/2}" width="{B*sc}" height="{N*sc}" fill="none" stroke="#000" stroke-width="2"/>
        
        <g transform="translate({px}, {py})" fill="#cbd5e1" stroke="#000" stroke-width="1">
            <rect x="{-b*sc/2}" y="{-h*sc/2}" width="{b*sc}" height="{tf*sc}"/>
            <rect x="{-b*sc/2}" y="{h*sc/2 - tf*sc}" width="{b*sc}" height="{tf*sc}"/>
            <rect x="{-tw*sc/2}" y="{-h*sc/2 + tf*sc}" width="{tw*sc}" height="{(h-2*tf)*sc}"/>
        </g>

        <g stroke="#dc2626" stroke-width="1.5">
            <line x1="{px + B*sc/2}" y1="{py}" x2="{px + B*sc/2 - n*sc}" y2="{py}"/>
            <line x1="{px}" y1="{py + N*sc/2}" x2="{px}" y2="{py + N*sc/2 - m*sc}"/>
        </g>
        <text x="{px + B*sc/2 - n*sc/2}" y="{py - 10}" fill="#dc2626" font-size="12" text-anchor="middle">n = {n:.2f}</text>
        <text x="{px + 10}" y="{py + N*sc/2 - m*sc/2}" fill="#dc2626" font-size="12" transform="rotate(90 {px+10} {py + N*sc/2 - m*sc/2})">m = {m:.2f}</text>

        <g transform="translate(580, 80)">
            <text x="80" y="0" text-anchor="middle" font-weight="bold" font-family="monospace">SECTION A-A</text>
            <rect x="60" y="30" width="40" height="120" fill="#94a3b8" stroke="#000"/>
            <rect x="0" y="150" width="160" height="12" fill="#334155"/>
            <text x="170" y="160" font-size="11">PL {tp_mm}mm</text>
            <rect x="0" y="162" width="160" height="8" fill="#e2e8f0" stroke="#94a3b8" stroke-dasharray="2"/>
            <text x="170" y="170" font-size="10" fill="#64748b">Grout</text>
            <path d="M 0 170 L 0 250 L 160 250 L 160 170" fill="none" stroke="#334155" stroke-dasharray="5,3"/>
            
            <path d="M 100 150 L 130 120 h 20" fill="none" stroke="#dc2626" stroke-width="1"/>
            <path d="M 110 140 L 120 150 L 100 150 Z" fill="#dc2626"/> </g>

        <g transform="translate(560, 350)" font-family="monospace" font-size="12">
            <text x="0" y="0" font-weight="bold">DESIGN SUMMARY:</text>
            <text x="0" y="25">PL: {B}x{N}x{tp_mm} mm</text>
            <text x="0" y="45">Fy: {Fy} kg/cm2</text>
            <text x="0" y="65">L_crit: {l_crit:.2f} cm</text>
            <text x="0" y="85">t_req: {t_req*10:.2f} mm</text>
        </g>
    </svg>
    """
    st.write(svg, unsafe_allow_html=True)

    # --- 4. VERIFICATION VERDICT ---
    st.divider()
    v1, v2, v3 = st.columns(3)
    v1.metric("Required Thickness", f"{t_req*10:.2f} mm")
    v2.metric("Provided Thickness", f"{tp_mm} mm")
    
    if tp_mm >= t_req*10:
        v3.success("🛡️ DESIGN SAFE")
    else:
        v3.error("🚨 THICKNESS INSUFFICIENT")
