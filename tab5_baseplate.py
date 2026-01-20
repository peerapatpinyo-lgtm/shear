import streamlit as st
import streamlit.components.v1 as components
import math

def render(res_ctx, v_design):
    # --- 1. ENGINEERING LOGIC ---
    h, b, tw, tf = res_ctx['h']/10, res_ctx['b']/10, res_ctx['tw']/10, res_ctx['tf']/10
    Fy, is_lrfd = res_ctx['Fy'], res_ctx['is_lrfd']

    # --- 2. INPUT INTERFACE ---
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        N = c1.number_input("N (Plate Length) cm", value=float(math.ceil(h + 15)))
        B = c2.number_input("B (Plate Width) cm", value=float(math.ceil(b + 15)))
        tp = c3.number_input("t (Thickness) mm", value=25.0)
        edge_d = c4.number_input("Edge Dist. (mm)", value=50.0)

    # Calculation AISC DG1
    m = (N - 0.95*h)/2
    n = (B - 0.80*b)/2
    l_crit = max(m, n, (math.sqrt(h*b)/4))
    t_req = l_crit * math.sqrt((2*v_design)/(0.9*Fy*B*N)) if is_lrfd else l_crit * math.sqrt((2*v_design*1.67)/(Fy*B*N))

    # --- 3. HIGH-DETAIL SVG BLUEPRINT ---
    sc = 220 / max(N, B)
    canvas_w, canvas_h = 800, 520
    px, py = 250, 260 # Plan Center
    
    # Bolt Offset
    eb = edge_d / 10
    bx, by = (B/2 - eb) * sc, (N/2 - eb) * sc

    svg_code = f"""
    <div style="display: flex; justify-content: center; background: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);">
    <svg width="{canvas_w}" height="{canvas_h}" viewBox="0 0 {canvas_w} {canvas_h}" xmlns="http://www.w3.org/2000/svg">
        <text x="20" y="30" font-family="monospace" font-size="18" font-weight="bold" fill="#1e3a8a">STRUCTURAL SHOP DRAWING: BASE PLATE</text>
        <line x1="20" y1="40" x2="520" y2="40" stroke="#1e3a8a" stroke-width="2"/>

        <g transform="translate(0, 20)">
            <text x="{px}" y="40" text-anchor="middle" font-weight="bold" font-family="monospace" font-size="14">TOP VIEW (PLAN)</text>
            
            <rect x="{px - B*sc/2}" y="{py - N*sc/2}" width="{B*sc}" height="{N*sc}" fill="#f8fafc" stroke="#1e293b" stroke-width="2.5"/>
            
            <g stroke="#94a3b8" stroke-width="0.8" stroke-dasharray="12,4,2,4">
                <line x1="{px - B*sc/2 - 30}" y1="{py}" x2="{px + B*sc/2 + 30}" y2="{py}"/>
                <line x1="{px}" y1="{py - N*sc/2 - 30}" x2="{px}" y2="{py + N*sc/2 + 30}"/>
            </g>

            <g transform="translate({px}, {py})" fill="#475569" stroke="#000" stroke-width="1">
                <rect x="{-b*sc/2}" y="{-h*sc/2}" width="{b*sc}" height="{tf*sc}"/> <rect x="{-b*sc/2}" y="{h*sc/2 - tf*sc}" width="{b*sc}" height="{tf*sc}"/> <rect x="{-tw*sc/2}" y="{-h*sc/2 + tf*sc}" width="{tw*sc}" height="{(h-2*tf)*sc}"/> </g>

            <g fill="none" stroke="#ef4444" stroke-width="1.5">
                <circle cx="{px-bx}" cy="{py-by}" r="8"/> <circle cx="{px-bx}" cy="{py-by}" r="2" fill="#ef4444"/>
                <circle cx="{px+bx}" cy="{py-by}" r="8"/> <circle cx="{px+bx}" cy="{py-by}" r="2" fill="#ef4444"/>
                <circle cx="{px-bx}" cy="{py+by}" r="8"/> <circle cx="{px-bx}" cy="{py+by}" r="2" fill="#ef4444"/>
                <circle cx="{px+bx}" cy="{py+by}" r="8"/> <circle cx="{px+bx}" cy="{py+by}" r="2" fill="#ef4444"/>
            </g>

            <g stroke="#64748b" stroke-width="1" font-family="monospace" font-size="11">
                <line x1="{px - B*sc/2}" y1="{py + N*sc/2 + 25}" x2="{px + B*sc/2}" y2="{py + N*sc/2 + 25}"/>
                <path d="M{px - B*sc/2} {py + N*sc/2 + 20} L{px - B*sc/2} {py + N*sc/2 + 30} M{px + B*sc/2} {py + N*sc/2 + 20} L{px + B*sc/2} {py + N*sc/2 + 30}"/>
                <text x="{px}" y="{py + N*sc/2 + 45}" text-anchor="middle">B = {B} cm</text>
                
                <line x1="{px + B*sc/2 + 25}" y1="{py - N*sc/2}" x2="{px + B*sc/2 + 25}" y2="{py + N*sc/2}"/>
                <text x="{px + B*sc/2 + 45}" y="{py}" transform="rotate(90 {px + B*sc/2 + 45} {py})" text-anchor="middle">N = {N} cm</text>
            </g>
        </g>

        <g transform="translate(560, 100)">
            <text x="80" y="0" text-anchor="middle" font-weight="bold" font-family="monospace" font-size="14">SECTION A-A</text>
            
            <rect x="55" y="30" width="50" height="150" fill="#cbd5e1" stroke="#334155"/>
            
            <rect x="0" y="180" width="160" height="18" fill="#1e293b"/>
            <text x="170" y="195" font-size="12" font-weight="bold" fill="#1e293b">PL {tp} mm</text>
            
            <rect x="0" y="198" width="160" height="10" fill="#94a3b8" opacity="0.4"/>
            <text x="170" y="208" font-size="10" fill="#64748b">30mm NON-SHRINK GROUT</text>
            
            <rect x="-20" y="208" width="200" height="80" fill="none" stroke="#94a3b8" stroke-dasharray="4,4"/>
            <text x="80" y="280" text-anchor="middle" font-size="10" fill="#94a3b8">CONCRETE FOUNDATION</text>

            <path d="M 105 180 L 130 150 H 155" fill="none" stroke="#ef4444" stroke-width="1.5"/>
            <path d="M 112 165 L 122 180 H 102 Z" fill="#ef4444"/> <text x="132" y="145" font-size="11" font-weight="bold" fill="#ef4444">FW E70XX</text>
        </g>
    </svg>
    </div>
    """
    components.html(svg_code, height=canvas_h + 20)
    
    

    # --- 4. CALCULATION LOGS ---
    st.divider()
    res1, res2, res3 = st.columns(3)
    res1.metric("Critical Arm (l)", f"{l_crit:.2f} cm")
    res2.metric("Min. Required t", f"{t_req*10:.2f} mm")
    
    status = "✅ PASS" if tp >= t_req*10 else "🚨 FAIL"
    res3.subheader(f"Status: {status}")
