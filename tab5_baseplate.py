import streamlit as st
import streamlit.components.v1 as components
import math

def render(res_ctx, v_design):
    # --- 1. PHYSICAL GEOMETRY ---
    h, b, tw, tf = res_ctx['h'], res_ctx['b'], res_ctx['tw'], res_ctx['tf']
    Fy = res_ctx['Fy']
    
    # --- 2. ADVANCED CONTROL PANEL ---
    with st.container(border=True):
        st.markdown("##### 📐 Design Optimization & Tolerance")
        c1, c2, c3, c4 = st.columns(4)
        N = c1.number_input("N (Plate Length) mm", value=float(math.ceil(h + 150)))
        B = c2.number_input("B (Plate Width) mm", value=float(math.ceil(b + 150)))
        tp = c3.number_input("Plate Thickness (mm)", value=25.0)
        hole_d = c4.number_input("Bolt Hole Dia (mm)", value=32.0) # Oversized hole for tolerance

    # --- 3. SENIOR LEVEL CALCULATIONS ---
    # AISC Design Guide 1 (Yiel Line Patterns)
    m = (N - 0.95 * h) / 2
    n = (B - 0.80 * b) / 2
    l_crit = max(m, n, (math.sqrt(h * b) / 4))
    t_req = l_crit * math.sqrt((2 * v_design) / (0.9 * Fy * (B/10) * (N/10)))

    # Stiffness Check: Plate thickness should be > Bolt Diameter / 2 (Rule of thumb for rigidity)
    is_rigid = tp >= (hole_d * 0.8)

    # --- 4. HIGH-PRECISION ENGINEERING BLUEPRINT ---
    sc = 350 / max(N, B)
    cv_w, cv_h = 850, 700
    px, py = 280, 350 # Master Center
    
    svg = f"""
    <div style="display:flex; justify-content:center; background:#f1f5f9; padding:25px; border-radius:12px;">
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <rect x="0" y="0" width="{cv_w}" height="{cv_h}" fill="#ffffff" stroke="#1e293b" stroke-width="2"/>
        
        <text x="20" y="40" font-family="monospace" font-size="22" font-weight="bold" fill="#0f172a">STRUCTURAL DETAIL: BP-01</text>
        <text x="20" y="65" font-family="monospace" font-size="12" fill="#64748b">PROJECT: INDUSTRIAL STEEL STRUCTURE | DATE: 2026</text>
        <line x1="20" y1="80" x2="830" y2="80" stroke="#e2e8f0" stroke-width="2"/>

        <g transform="translate(0, 50)">
            <text x="{px}" y="20" text-anchor="middle" font-weight="bold" font-size="14" fill="#334155">TOP VIEW (Scale 1:10)</text>
            <rect x="{px-B*sc/2}" y="{py-N*sc/2}" width="{B*sc}" height="{N*sc}" fill="#f8fafc" stroke="#000" stroke-width="2.5"/>
            
            <g transform="translate({px}, {py})" fill="#cbd5e1" stroke="#000" stroke-width="1.5">
                <rect x="{-b*sc/2}" y="{-h*sc/2}" width="{b*sc}" height="{tf*sc}"/>
                <rect x="{-b*sc/2}" y="{h*sc/2-tf*sc}" width="{b*sc}" height="{tf*sc}"/>
                <rect x="{-tw*sc/2}" y="{-h*sc/2+tf*sc}" width="{tw*sc}" height="{(h-2*tf)*sc}"/>
                <rect x="{-b*sc/2 - 2}" y="{-h*sc/2 - 2}" width="{b*sc + 4}" height="{h*sc + 4}" fill="none" stroke="#ef4444" stroke-dasharray="3,3" stroke-width="1"/>
            </g>

            <g fill="none" stroke="#3b82f6" stroke-width="1.5">
                <circle cx="{px-(B/2-60)*sc}" cy="{py-(N/2-60)*sc}" r="{hole_d/2*sc}"/>
                <circle cx="{px+(B/2-60)*sc}" cy="{py-(N/2-60)*sc}" r="{hole_d/2*sc}"/>
                <circle cx="{px-(B/2-60)*sc}" cy="{py+(N/2-60)*sc}" r="{hole_d/2*sc}"/>
                <circle cx="{px+(B/2-60)*sc}" cy="{py+(N/2-60)*sc}" r="{hole_d/2*sc}"/>
            </g>

            <g stroke="#94a3b8" stroke-width="1" font-size="11" font-family="monospace">
                <path d="M{px-B*sc/2} {py+N*sc/2+30} h{B*sc}" fill="none" stroke="#000"/>
                <text x="{px}" y="{py+N*sc/2+50}" text-anchor="middle" fill="#000">B = {B} mm</text>
                <path d="M{px+B*sc/2+30} {py-N*sc/2} v{N*sc}" fill="none" stroke="#000"/>
                <text x="{px+B*sc/2+60}" y="{py}" transform="rotate(90 {px+B*sc/2+60} {py})" text-anchor="middle" fill="#000">N = {N} mm</text>
            </g>
        </g>

        <g transform="translate(620, 180)">
            <text x="80" y="-30" text-anchor="middle" font-weight="bold" font-size="14">SECTION A-A</text>
            <rect x="65" y="0" width="30" height="200" fill="#cbd5e1" stroke="#000"/>
            <path d="M 95 200 L 130 160 H 170" fill="none" stroke="#ef4444" stroke-width="2"/>
            <path d="M 105 185 L 115 200 H 95 Z" fill="#ef4444"/>
            <text x="135" y="155" fill="#ef4444" font-weight="bold" font-size="12">FW TYP.</text>
            
            <rect x="0" y="200" width="160" height="15" fill="#1e293b"/>
            <rect x="0" y="215" width="160" height="10" fill="#94a3b8" opacity="0.4"/>
            <path d="M 0 215 l 160 10 M 20 215 l 140 10 M 0 215 l 160 10" stroke="#64748b" stroke-width="0.5" opacity="0.3"/>
            
            <rect x="-20" y="225" width="200" height="100" fill="none" stroke="#cbd5e1" stroke-dasharray="5,5"/>
            <text x="80" y="340" text-anchor="middle" fill="#94a3b8" font-size="10">REINFORCED CONCRETE PEDESTAL</text>
        </g>

        <g transform="translate(20, 580)">
            <rect x="0" y="0" width="810" height="100" fill="#f8fafc" stroke="#e2e8f0"/>
            <text x="15" y="25" font-weight="bold" font-size="12">STRUCTURAL SUMMARY:</text>
            <text x="15" y="50" font-size="11">● Max Cantilever (l): {l_crit:.2f} mm</text>
            <text x="15" y="75" font-size="11">● Min Thickness (tp_req): {t_req:.2f} mm</text>
            <text x="300" y="50" font-size="11">● Weld Strength: E70XX Fillet</text>
            <text x="300" y="75" font-size="11">● Grout Type: Non-Shrink (Min 60MPa)</text>
            <text x="600" y="60" font-size="14" font-weight="bold" fill="{"#15803d" if tp >= t_req else "#b91c1c"}">
                VERDICT: {"PASS" if tp >= t_req else "FAIL (INCREASE THICKNESS)"}
            </text>
        </g>
    </svg>
    </div>
    """
    components.html(svg, height=720)

    # --- 5. FIELD GUIDANCE (THE SENIOR'S ADVICE) ---
    st.divider()
    
    st.info("💡 **Senior Engineer's Note:** สำหรับหน้างานจริง อย่าลืมใช้ **Washers** ขนาดใหญ่พิเศษครอบรู Oversized และตรวจสอบให้แน่ใจว่า **Non-shrink Grout** ถูกเทจนล้นออกมาเล็กน้อยเพื่อให้แน่ใจว่าไม่มีโพรงอากาศ (Air Voids) ใต้แผ่นเพลท")
