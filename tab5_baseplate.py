import streamlit as st
import streamlit.components.v1 as components
import math

def render(res_ctx, v_design):
    st.markdown("## 🏛️ Ultimate Base Plate Engineering Suite")
    st.caption("AISC 360-22 & ACI 318-19 Professional Analysis")

    # --- 1. PHYSICAL & LOAD DATA ---
    h, b, tw, tf = res_ctx['h']/10, res_ctx['b']/10, res_ctx['tw']/10, res_ctx['tf']/10
    Fy = res_ctx['Fy']
    # รับแรงเฉือนและโมเมนต์เพิ่ม (สมมติค่าเพื่อการคำนวณขั้นสูง)
    V_shear = st.sidebar.number_input("Design Shear (kg)", value=2000.0)
    M_moment = st.sidebar.number_input("Design Moment (kg-cm)", value=50000.0)

    # --- 2. ADVANCED INPUTS ---
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        N = c1.number_input("N (Length) cm", value=float(math.ceil(h + 20)))
        B = c2.number_input("B (Width) cm", value=float(math.ceil(b + 20)))
        tp = c3.number_input("Thickness (mm)", value=25.0)
        fc = c4.number_input("Concrete f'c (ksc)", value=240.0)

        c5, c6, c7, c8 = st.columns(4)
        bolt_d = c5.selectbox("Bolt Dia (mm)", [16, 20, 24, 30, 36], index=1)
        bolt_n = c6.selectbox("No. of Bolts", [4, 6, 8], index=0)
        edge_d = c7.number_input("Edge Distance (mm)", value=50.0)
        mu = c8.slider("Friction Coeff (μ)", 0.2, 0.7, 0.4)

    # --- 3. MULTI-LIMIT STATE ANALYSIS ---
    # A. Plate Bending (AISC DG1)
    m = (N - 0.95*h)/2
    n = (B - 0.80*b)/2
    l_crit = max(m, n, (math.sqrt(h*b)/4))
    t_req = l_crit * math.sqrt((2*v_design)/(0.9*Fy*B*N))

    # B. Shear Transfer Check
    phi_v = 0.75
    friction_cap = phi_v * mu * v_design
    need_lug = V_shear > friction_cap

    # C. Bolt Tension (Simplified for Moment)
    dist_bolt = N - (2 * edge_d / 10) # ระยะระหว่างโบลท์
    tension_per_bolt = (M_moment / dist_bolt) / (bolt_n / 2) if M_moment > 0 else 0

    # --- 4. PRECISION ENGINEERING DRAWING (SVG) ---
    sc = 220 / max(N, B)
    cv_w, cv_h = 850, 550
    px, py = 250, 280
    ed = edge_d / 10
    bx, by = (B/2 - ed) * sc, (N/2 - ed) * sc

    svg = f"""
    <div style="display: flex; justify-content: center; background: #ffffff; padding: 15px; border-radius: 8px; border: 2px solid #1e293b;">
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <defs><pattern id="g" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M 20 0 L 0 0 0 20" fill="none" stroke="#f1f5f9" stroke-width="0.5"/></pattern></defs>
        <rect width="100%" height="100%" fill="url(#g)" />

        <text x="{px}" y="40" text-anchor="middle" font-weight="bold" font-family="monospace" font-size="16">TOP VIEW: BOLT LAYOUT & YIELD LINES</text>
        <rect x="{px-B*sc/2}" y="{py-N*sc/2}" width="{B*sc}" height="{N*sc}" fill="none" stroke="#1e293b" stroke-width="2.5"/>
        
        <g transform="translate({px}, {py})" fill="#cbd5e1" stroke="#000">
            <rect x="{-b*sc/2}" y="{-h*sc/2}" width="{b*sc}" height="{tf*sc}"/>
            <rect x="{-b*sc/2}" y="{h*sc/2-tf*sc}" width="{b*sc}" height="{tf*sc}"/>
            <rect x="{-tw*sc/2}" y="{-h*sc/2+tf*sc}" width="{tw*sc}" height="{(h-2*tf)*sc}"/>
        </g>

        <line x1="{px-B*sc/2}" y1="{py-h*sc/2*0.95}" x2="{px+B*sc/2}" y2="{py-h*sc/2*0.95}" stroke="#ef4444" stroke-dasharray="5,5"/>
        <line x1="{px-B*sc/2}" y1="{py+h*sc/2*0.95}" x2="{px+B*sc/2}" y2="{py+h*sc/2*0.95}" stroke="#ef4444" stroke-dasharray="5,5"/>

        <g fill="none" stroke="#3b82f6" stroke-width="2">
            <circle cx="{px-bx}" cy="{py-by}" r="8"/> <circle cx="{px+bx}" cy="{py-by}" r="8"/>
            <circle cx="{px-bx}" cy="{py+by}" r="8"/> <circle cx="{px+bx}" cy="{py+by}" r="8"/>
        </g>

        <g transform="translate(560, 120)">
            <text x="80" y="-30" text-anchor="middle" font-weight="bold" font-family="monospace">SECTION A-A</text>
            <rect x="65" y="0" width="30" height="150" fill="#f1f5f9" stroke="#1e293b"/>
            <rect x="0" y="150" width="160" height="15" fill="#1e293b"/>
            {"<rect x='70' y='165' width='20' height='40' fill='#1e293b'/>" if need_lug else ""}
            <rect x="0" y="165" width="160" height="8" fill="#94a3b8" opacity="0.4"/>
            <path d="M -10 173 L -10 300 L 170 300 L 170 173" fill="none" stroke="#94a3b8" stroke-dasharray="4,2"/>
            
            <path d="M 95 150 L 120 125 h 30" fill="none" stroke="#ef4444" stroke-width="1.5"/>
            <path d="M 100 142 L 110 150 H 90 Z" fill="#ef4444"/>
            <text x="125" y="120" font-size="10" fill="#ef4444" font-weight="bold">FW E70XX</text>
        </g>
    </svg>
    </div>
    """
    components.html(svg, height=580)

    # --- 5. SENIOR ANALYSIS DASHBOARD ---
    st.divider()
    v1, v2, v3, v4 = st.columns(4)
    v1.metric("Plate Bending", f"{(t_req*10/tp):.1%}", delta="SAFE" if tp >= t_req*10 else "FAIL")
    v2.metric("Shear Status", "LUG REQ." if need_lug else "FRICTION OK")
    v3.metric("Bolt Tension", f"{tension_per_bolt:.0f} kg/bolt")
    v4.metric("Wrench Space", f"{( ( (B-b)/2*10 ) - edge_d ):.0f} mm")

    if need_lug:
        st.warning("⚠️ **High Shear Detected:** แรงเฉือนเกินกำลังแรงเสียดทาน แนะนำให้ติด Shear Lug ขนาด 50x50mm ใต้เพลท")
