import streamlit as st
import math

def render(res_ctx, v_design):
    st.markdown("### 🏛️ Master Structural Detail: Base Plate Section")

    # --- 1. ENGINEERING DATA ---
    h, b, tw, tf = res_ctx['h']/10, res_ctx['b']/10, res_ctx['tw']/10, res_ctx['tf']/10
    Fy, is_lrfd = res_ctx['Fy'], res_ctx['is_lrfd']

    # --- 2. INPUTS ---
    with st.sidebar:
        st.markdown("### 🛠️ Detail Setting")
        N = st.number_input("Plate Length N (cm)", value=float(math.ceil(h + 15)))
        B = st.number_input("Plate Width B (cm)", value=float(math.ceil(b + 15)))
        tp = st.number_input("Plate Thickness (mm)", value=25.0)
        g_t = st.number_input("Grout Thickness (mm)", value=30.0)
        e_d = st.number_input("Bolt Edge Distance (mm)", value=50.0)

    # --- 3. AISC CALCULATIONS (STRICT DG1) ---
    m = (N - 0.95*h)/2
    n = (B - 0.80*b)/2
    l_crit = max(m, n, (math.sqrt(h*b)/4))
    t_req = l_crit * math.sqrt((2*v_design)/(0.9*Fy*B*N)) if is_lrfd else l_crit * math.sqrt((2*v_design*1.67)/(Fy*B*N))

    # --- 4. PRECISION SHOP DRAWING (SVG) ---
    # เราจะวาดแบบ Detail ที่มีเส้นบอกระยะ (Dimension Lines) และสัญลักษณ์ครบถ้วน
    st.markdown("#### 📐 Engineering Drawing & Dimensioning")
    
    sc = 250 / max(N, B + 15)
    canvas_w, canvas_h = 600, 450
    cx, cy = 180, 200 # Top View Center
    
    svg = f"""
    <svg width="100%" height="{canvas_h}" viewBox="0 0 {canvas_w} {canvas_h}" xmlns="http://www.w3.org/2000/svg">
        <rect x="{cx - B*sc/2}" y="{cy - N*sc/2}" width="{B*sc}" height="{N*sc}" fill="none" stroke="#1e293b" stroke-width="2"/>
        
        <g transform="translate({cx}, {cy})">
            <rect x="{-b*sc/2}" y="{-h*sc/2}" width="{b*sc}" height="{tf*sc}" fill="#475569"/>
            <rect x="{-b*sc/2}" y="{h*sc/2 - tf*sc}" width="{b*sc}" height="{tf*sc}" fill="#475569"/>
            <rect x="{-tw*sc/2}" y="{-h*sc/2 + tf*sc}" width="{tw*sc}" height="{(h-2*tf)*sc}" fill="#475569"/>
        </g>

        <line x1="{cx + B*sc/2}" y1="{cy}" x2="{cx + B*sc/2 - n*sc}" y2="{cy}" stroke="#ef4444" stroke-width="2"/>
        <text x="{cx + B*sc/2 - 20}" y="{cy - 5}" fill="#ef4444" font-size="12" font-weight="bold">n</text>
        
        <line x1="{cx}" y1="{cy + N*sc/2}" x2="{cx}" y2="{cy + N*sc/2 - m*sc}" stroke="#ef4444" stroke-width="2"/>
        <text x="{cx + 5}" y="{cy + N*sc/2 - 15}" fill="#ef4444" font-size="12" font-weight="bold">m</text>

        <g stroke="#64748b" stroke-width="1">
            <line x1="{cx - B*sc/2}" y1="{cy + N*sc/2 + 20}" x2="{cx + B*sc/2}" y2="{cy + N*sc/2 + 20}"/>
            <line x1="{cx - B*sc/2}" y1="{cy + N*sc/2 + 15}" x2="{cx - B*sc/2}" y2="{cy + N*sc/2 + 25}"/>
            <line x1="{cx + B*sc/2}" y1="{cy + N*sc/2 + 15}" x2="{cx + B*sc/2}" y2="{cy + N*sc/2 + 25}"/>
        </g>
        <text x="{cx}" y="{cy + N*sc/2 + 40}" text-anchor="middle" font-size="12">B = {B} cm</text>

        <g transform="translate(380, 50)">
            <text x="50" y="20" text-anchor="middle" font-weight="bold">SECTION A-A</text>
            <rect x="35" y="40" width="30" height="150" fill="#475569"/>
            <path d="M 65 190 L 85 170 h 20" fill="none" stroke="#ef4444" stroke-width="1"/>
            <text x="90" y="165" font-size="10" fill="#ef4444">Fillet Weld</text>
            <rect x="0" y="190" width="100" height="15" fill="#1e293b"/>
            <rect x="0" y="205" width="100" height="10" fill="#94a3b8" opacity="0.4"/>
            <rect x="-20" y="215" width="140" height="60" fill="none" stroke="#94a3b8" stroke-dasharray="2"/>
            
            <text x="110" y="202" font-size="10">Plate {tp}mm</text>
            <text x="110" y="215" font-size="10">Grout {g_t}mm</text>
        </g>
    </svg>
    """
    st.write(svg, unsafe_allow_html=True)
    
    # --- 5. RESULT TABLE ---
    st.divider()
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.markdown("#### 📝 Design Summary")
        st.write(f"Governing Cantilever ($l$): **{l_crit:.2f} cm**")
        st.write(f"Bending Strength Stress: **{v_design/(B*N):.2f} kg/cm²**")
        
    with res_col2:
        st.markdown("#### ✅ Verification")
        if tp/10 >= t_req:
            st.success(f"Thickness OK (Min: {t_req*10:.2f} mm)")
        else:
            st.error(f"Increase Thickness (Min: {t_req*10:.2f} mm)")
