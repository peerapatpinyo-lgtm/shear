import streamlit as st
import streamlit.components.v1 as components
import math
import steel_db  # ดึงฐานข้อมูลหน้าตัดเหล็กมาใช้

def render(res_ctx, v_design):
    st.markdown("### 🧱 Detailed Column Base Plate Design")
    
    # --- 1. SELECTION & INPUTS ---
    with st.container(border=True):
        col_main1, col_main2 = st.columns([1, 1.5])
        
        with col_main1:
            st.markdown("##### 📦 Column Section")
            sec_list = steel_db.get_section_list()
            # เลือกขนาดเสา (Default เป็นขนาดเดียวกับคานที่คำนวณมา)
            col_name = st.selectbox("Select Column Size", sec_list, index=sec_list.index(res_ctx['sec_name']) if res_ctx['sec_name'] in sec_list else 13)
            props = steel_db.get_properties(col_name)
            ch, cb, ctw, ctf = float(props['h']), float(props['b']), float(props['tw']), float(props['tf'])
            
            st.info(f"Column: {col_name} ({int(ch)}x{int(cb)} mm)")

        with col_main2:
            st.markdown("##### 📐 Plate & Bolt Geometry")
            c1, c2, c3 = st.columns(3)
            clr_x = c1.number_input("Clearance X (mm)", value=50.0, help="ระยะจากขอบปีกเสาถึงรูโบลต์")
            clr_y = c2.number_input("Clearance Y (mm)", value=60.0, help="ระยะจากเอวเสาถึงรูโบลต์")
            tp = c3.number_input("Plate Thickness (mm)", value=25.0)
            
            c4, c5, c6 = st.columns(3)
            edge_x = c4.number_input("Edge Dist X (mm)", value=50.0)
            edge_y = c5.number_input("Edge Dist Y (mm)", value=50.0)
            bolt_d = c6.selectbox("Bolt Size", [16, 20, 24, 30], index=1)

    # --- 2. CALCULATION LOGIC ---
    # Sx, Sy = Bolt Spacing (ระยะห่างระหว่างรูเจาะ)
    sx = cb + (2 * clr_x)
    sy = ch - (2 * ctf) + (2 * clr_y) # อ้างอิงจากระยะเอวเสา
    
    # B, N = Plate Dimensions (ขนาดแผ่นรวม)
    B = sx + (2 * edge_x)
    N = sy + (2 * edge_y)
    
    hole_d = bolt_d + 4  # มาตรฐานรูเจาะ Base Plate (Oversized)

    # --- 3. SVG DRAWING LOGIC ---
    cv_w, cv_h = 950, 900
    cx, cy = cv_w/2, cv_h/2 - 50
    sc = 550 / max(N, B) # Scaling Factor

    # SVG Components Construction
    svg = f"""
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#ffffff" />
        
        <text x="40" y="50" font-family="sans-serif" font-size="22" font-weight="bold" fill="#1e293b">BASE PLATE SHOP DRAWING (BP-01)</text>
        <line x1="40" y1="65" x2="500" y2="65" stroke="#1e293b" stroke-width="3"/>
        
        <g transform="translate({cx}, {cy})">
            <rect x="{-B*sc/2}" y="{-N*sc/2}" width="{B*sc}" height="{N*sc}" fill="#f8fafc" stroke="#000" stroke-width="3"/>
            
            <g fill="#cbd5e1" stroke="#000" stroke-width="1.5">
                <rect x="{-cb/2*sc}" y="{-ch/2*sc}" width="{cb*sc}" height="{ctf*sc}"/> <rect x="{-cb/2*sc}" y="{(ch/2-ctf)*sc}" width="{cb*sc}" height="{ctf*sc}"/> <rect x="{-ctw/2*sc}" y="{-ch/2*sc+ctf*sc}" width="{ctw*sc}" height="{(ch-2*ctf)*sc}"/> </g>

            <g fill="white" stroke="#2563eb" stroke-width="2">
                <circle cx="{-sx/2*sc}" cy="{-sy/2*sc}" r="{hole_d*sc/2}"/>
                <circle cx="{sx/2*sc}"  cy="{-sy/2*sc}" r="{hole_d*sc/2}"/>
                <circle cx="{-sx/2*sc}" cy="{sy/2*sc}"  r="{hole_d*sc/2}"/>
                <circle cx="{sx/2*sc}"  cy="{sy/2*sc}"  r="{hole_d*sc/2}"/>
            </g>

            <g font-family="monospace" font-size="14" font-weight="bold">
                <line x1="{-B*sc/2}" y1="{N*sc/2 + 60}" x2="{B*sc/2}" y2="{N*sc/2 + 60}" stroke="black" />
                <line x1="{-B*sc/2}" y1="{N*sc/2 + 50}" x2="{-B*sc/2}" y2="{N*sc/2 + 70}" stroke="black" />
                <line x1="{B*sc/2}" y1="{N*sc/2 + 50}" x2="{B*sc/2}" y2="{N*sc/2 + 70}" stroke="black" />
                <text x="0" y="{N*sc/2 + 85}" text-anchor="middle">WIDTH (B) = {int(B)} mm</text>

                <line x1="{-sx/2*sc}" y1="{N*sc/2 + 30}" x2="{sx/2*sc}" y2="{N*sc/2 + 30}" stroke="#2563eb" />
                <text x="0" y="{N*sc/2 + 25}" text-anchor="middle" fill="#2563eb" font-size="12">Sx = {int(sx)}</text>

                <line x1="{B*sc/2 + 60}" y1="{-N*sc/2}" x2="{B*sc/2 + 60}" y2="{N*sc/2}" stroke="black" />
                <text x="{B*sc/2 + 80}" y="0" transform="rotate(90, {B*sc/2 + 80}, 0)" text-anchor="middle">LENGTH (N) = {int(N)} mm</text>
                
                <line x1="{B*sc/2 + 30}" y1="{-sy/2*sc}" x2="{B*sc/2 + 30}" y2="{sy/2*sc}" stroke="#2563eb" />
                <text x="{B*sc/2 + 45}" y="0" transform="rotate(90, {B*sc/2 + 45}, 0)" text-anchor="middle" fill="#2563eb" font-size="12">Sy = {int(sy)}</text>
            </g>

            <g transform="translate({-cb/2*sc - 40}, {-ch/2*sc + 20})">
                <path d="M 0 0 L -40 -40 L -100 -40" fill="none" stroke="#dc2626" stroke-width="1.5"/>
                <text x="-100" y="-45" fill="#dc2626" font-size="14" font-weight="bold">△ 6 mm (Typical)</text>
            </g>
        </g>

        <g transform="translate(600, 680)">
            <rect width="320" height="180" fill="#f1f5f9" stroke="#1e293b" rx="10"/>
            <text x="20" y="35" font-family="sans-serif" font-weight="bold" font-size="16">MATERIAL SPECIFICATIONS</text>
            <line x1="20" y1="45" x2="300" y2="45" stroke="#1e293b"/>
            <text x="20" y="75" font-family="monospace" font-size="13">COLUMN   : {col_name}</text>
            <text x="20" y="100" font-family="monospace" font-size="13">PLATE    : PL {int(tp)}x{int(B)}x{int(N)} mm</text>
            <text x="20" y="125" font-family="monospace" font-size="13">ANCHOR   : 4-M{bolt_d} GR 8.8 (J-Bolt)</text>
            <text x="20" y="150" font-family="monospace" font-size="13" fill="#2563eb">HOLE DIA : Ø{int(hole_d)} mm (Oversized)</text>
        </g>
    </svg>
    """
    components.html(svg, height=920)

    # --- 4. STRUCTURAL CHECKS (Summary) ---
    st.divider()
    st.markdown("##### 🔍 Structural Check Summary")
    area = B * N / 100 # cm2
    bearing_stress = v_design / area if area > 0 else 0
    
    c_res1, c_res2, c_res3 = st.columns(3)
    c_res1.metric("Bearing Area", f"{area:,.1f} cm²")
    c_res2.metric("Bearing Stress", f"{bearing_stress:,.2f} kg/cm²")
    c_res3.info("Check against Concrete f'c in next update.")
