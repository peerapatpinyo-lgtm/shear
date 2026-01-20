import streamlit as st
import streamlit.components.v1 as components
import math

def render(res_ctx, v_design):
    # --- 1. CORE ENGINEERING DATA ---
    h_mm, b_mm = res_ctx['h'], res_ctx['b']
    tw_mm, tf_mm = res_ctx['tw'], res_ctx['tf']
    Fy = res_ctx['Fy']
    
    # --- 2. PROFESSIONAL DESIGN INPUTS ---
    with st.container(border=True):
        st.markdown("##### 🏛️ Master Blueprint Parameters")
        c1, c2, c3, c4 = st.columns(4)
        N_mm = c1.number_input("Plate Length N (mm)", value=float(math.ceil(h_mm + 150)))
        B_mm = c2.number_input("Plate Width B (mm)", value=float(math.ceil(b_mm + 150)))
        tp_mm = c3.number_input("Plate Thickness (mm)", value=25.0)
        fc_ksc = c4.number_input("Concrete f'c (ksc)", value=240.0)

    # --- 3. AISC DESIGN CALCULATIONS (DG1) ---
    m_mm = (N_mm - 0.95 * h_mm) / 2
    n_mm = (B_mm - 0.80 * b_mm) / 2
    l_crit_mm = max(m_mm, n_mm, (math.sqrt(h_mm * b_mm) / 4))
    
    # Required Thickness Calculation (LRFD)
    t_req_mm = l_crit_mm * math.sqrt((2 * v_design) / (0.9 * Fy * (B_mm/10) * (N_mm/10)))

    # --- 4. THE ULTIMATE BLUEPRINT (PRECISION SVG) ---
    # เราใช้ Scale ที่แม่นยำและเพิ่มเลเยอร์ของเส้นบอกระยะแบบ AutoCAD
    sc = 300 / max(N_mm, B_mm)
    cv_w, cv_h = 850, 600
    px, py = 280, 300 # Center ของรูป Plan
    
    svg = f"""
    <div style="display: flex; justify-content: center; background: #1a1a1a; padding: 20px; border-radius: 8px;">
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <rect x="5" y="5" width="{cv_w-10}" height="{cv_h-10}" fill="#0f172a" stroke="#334155" stroke-width="2"/>
        <defs>
            <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#1e293b" stroke-width="0.5"/>
            </pattern>
        </defs>
        <rect x="5" y="5" width="{cv_w-10}" height="{cv_h-10}" fill="url(#grid)" />

        <text x="{px}" y="40" text-anchor="middle" font-family="monospace" font-size="18" font-weight="bold" fill="#38bdf8">01 - BASE PLATE PLAN VIEW</text>
        
        <g stroke="#64748b" stroke-width="1" stroke-dasharray="15,5,2,5">
            <line x1="{px - (B_mm*sc/2 + 40)}" y1="{py}" x2="{px + (B_mm*sc/2 + 40)}" y2="{py}"/>
            <line x1="{px}" y1="{py - (N_mm*sc/2 + 40)}" x2="{px}" y2="{py + (N_mm*sc/2 + 40)}"/>
        </g>

        <rect x="{px - B_mm*sc/2}" y="{py - N_mm*sc/2}" width="{B_mm*sc}" height="{N_mm*sc}" fill="none" stroke="#fff" stroke-width="2"/>
        
        <g transform="translate({px}, {py})" fill="#475569" stroke="#fff" stroke-width="1">
            <rect x="{-b_mm*sc/2}" y="{-h_mm*sc/2}" width="{b_mm*sc}" height="{tf_mm*sc}"/>
            <rect x="{-b_mm*sc/2}" y="{h_mm*sc/2 - tf_mm*sc}" width="{b_mm*sc}" height="{tf_mm*sc}"/>
            <rect x="{-tw_mm*sc/2}" y="{-h_mm*sc/2 + tf_mm*sc}" width="{tw_mm*sc}" height="{(h_mm-2*tf_mm)*sc}"/>
        </g>

        <g stroke="#f43f5e" stroke-width="1.5">
            <line x1="{px + B_mm*sc/2}" y1="{py}" x2="{px + B_mm*sc/2 - n_mm*sc}" y2="{py}"/> <line x1="{px}" y1="{py + N_mm*sc/2}" x2="{px}" y2="{py + N_mm*sc/2 - m_mm*sc}" /> </g>
        <text x="{px + B_mm*sc/2 - n_mm*sc/2}" y="{py - 10}" fill="#f43f5e" font-size="12" text-anchor="middle" font-family="monospace">n={n_mm:.1f}</text>
        <text x="{px + 10}" y="{py + N_mm*sc/2 - m_mm*sc/2}" fill="#f43f5e" font-size="12" font-family="monospace" transform="rotate(90, {px+10}, {py + N_mm*sc/2 - m_mm*sc/2})">m={m_mm:.1f}</text>

        <g transform="translate(620, 150)">
            <text x="80" y="-30" text-anchor="middle" font-family="monospace" font-size="14" font-weight="bold" fill="#38bdf8">02 - SECTION A-A</text>
            <rect x="65" y="0" width="30" height="180" fill="#475569" stroke="#fff"/>
            <rect x="0" y="180" width="160" height="15" fill="#fff"/>
            <rect x="0" y="195" width="160" height="10" fill="#94a3b8" opacity="0.4"/>
            <text x="170" y="193" fill="#fff" font-size="12">PL {tp_mm}mm</text>
            
            <path d="M 95 180 L 130 140 H 160" fill="none" stroke="#fbbf24" stroke-width="1.5"/>
            <path d="M 105 165 L 115 180 H 95 Z" fill="#fbbf24"/>
            <text x="135" y="135" fill="#fbbf24" font-size="11" font-weight="bold">TYP. E70XX</text>
            
            <path d="M 0 205 L 0 320 M 160 205 L 160 320" stroke="#64748b" stroke-dasharray="5,5"/>
            <text x="80" y="340" text-anchor="middle" fill="#64748b" font-size="10">CONC. PEDESTAL</text>
        </g>

        <g transform="translate(580, 480)" fill="#94a3b8" font-family="monospace" font-size="11">
            <rect x="-10" y="-10" width="250" height="100" fill="none" stroke="#334155"/>
            <text x="0" y="15" fill="#38bdf8" font-weight="bold">DESIGN SUMMARY (LRFD)</text>
            <text x="0" y="35">Critical Arm (l): {l_crit_mm:.2f} mm</text>
            <text x="0" y="55">Req. Thickness: {t_req_mm:.2f} mm</text>
            <text x="0" y="75">Material: Fy {Fy} kg/cm²</text>
        </g>
    </svg>
    </div>
    """
    components.html(svg, height=620)

    # --- 5. PROFESSIONAL VERDICT ---
    st.divider()
    v1, v2, v3 = st.columns(3)
    v1.metric("Governing Arm", f"{l_crit_mm:.2f} mm")
    v2.metric("Min. Required t", f"{t_req_mm:.2f} mm")
    
    if tp_mm >= t_req_mm:
        v3.success("🛡️ DESIGN SAFE: PASS")
    else:
        v3.error("🚨 DESIGN UNSAFE: FAIL")
        st.warning(f"แนะนำให้เพิ่มความหนาเพลทเป็นอย่างน้อย {math.ceil(t_req_mm)} mm")
