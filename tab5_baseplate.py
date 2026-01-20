import streamlit as st
import streamlit.components.v1 as components
import math

def render(res_ctx, v_design):
    # --- 1. CORE DATA & WELD LOGIC ---
    h, b, tw, tf = res_ctx['h'], res_ctx['b'], res_ctx['tw'], res_ctx['tf']
    Fy = res_ctx['Fy']
    
    # AISC Minimum Weld Size Logic (based on thicker part)
    min_weld = 3 if tf <= 6 else 5 if tf <= 13 else 6 if tf <= 19 else 8

    # --- 2. CONSTRUCTION INPUTS ---
    with st.container(border=True):
        st.markdown("##### 🛠️ Field Installation Parameters")
        c1, c2, c3, c4 = st.columns(4)
        N = c1.number_input("N (Plate Length) mm", value=float(math.ceil(h + 150)))
        B = c2.number_input("B (Plate Width) mm", value=float(math.ceil(b + 150)))
        tp = c3.number_input("Plate Thick (mm)", value=25.0)
        bolt_d = c4.selectbox("Anchor Bolt (mm)", [16, 20, 24, 30], index=1)
        
        c5, c6, c7, c8 = st.columns(4)
        edge_x = c5.number_input("Edge Dist. X (mm)", value=50.0)
        edge_y = c6.number_input("Edge Dist. Y (mm)", value=50.0)
        grout_thk = c7.number_input("Grout Space (mm)", value=50.0)
        weld_size = c8.number_input("Fillet Weld (mm)", value=float(min_weld))

    # --- 3. ANALYSIS ---
    m = (N - 0.95*h)/2
    n = (B - 0.80*b)/2
    l_crit = max(m, n, (math.sqrt(h*b)/4))
    t_req = l_crit * math.sqrt((2*v_design)/(0.9*Fy*(B/10)*(N/10)))

    # Bolt Spacing (The "Template" Dimension)
    s_x = B - (2 * edge_x)
    s_y = N - (2 * edge_y)

    # --- 4. THE ULTIMATE CONSTRUCTION BLUEPRINT (SVG) ---
    sc = 320 / max(N, B)
    cv_w, cv_h = 850, 650
    px, py = 280, 320 # Plan Center
    
    svg = f"""
    <div style="display: flex; justify-content: center; background: #ffffff; padding: 20px; border: 3px solid #334155;">
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <text x="20" y="30" font-family="sans-serif" font-size="20" font-weight="bold" fill="#1e293b">FOR CONSTRUCTION: BASE PLATE DETAIL</text>
        <line x1="20" y1="45" x2="550" y2="45" stroke="#1e293b" stroke-width="3"/>

        <g transform="translate(0, 40)">
            <text x="{px}" y="30" text-anchor="middle" font-weight="bold" font-size="14">TOP VIEW: ANCHOR BOLT TEMPLATE</text>
            <rect x="{px-B*sc/2}" y="{py-N*sc/2}" width="{B*sc}" height="{N*sc}" fill="#f8fafc" stroke="#000" stroke-width="2.5"/>
            <g transform="translate({px}, {py})" fill="#94a3b8" stroke="#000" stroke-width="1">
                <rect x="{-b*sc/2}" y="{-h*sc/2}" width="{b*sc}" height="{tf*sc}"/>
                <rect x="{-b*sc/2}" y="{h*sc/2-tf*sc}" width="{b*sc}" height="{tf*sc}"/>
                <rect x="{-tw*sc/2}" y="{-h*sc/2+tf*sc}" width="{tw*sc}" height="{(h-2*tf)*sc}"/>
            </g>
            <circle cx="{px-s_x/2*sc}" cy="{py-s_y/2*sc}" r="10" fill="none" stroke="#3b82f6" stroke-width="2"/>
            <circle cx="{px+s_x/2*sc}" cy="{py-s_y/2*sc}" r="10" fill="none" stroke="#3b82f6" stroke-width="2"/>
            <circle cx="{px-s_x/2*sc}" cy="{py+s_y/2*sc}" r="10" fill="none" stroke="#3b82f6" stroke-width="2"/>
            <circle cx="{px+s_x/2*sc}" cy="{py+s_y/2*sc}" r="10" fill="none" stroke="#3b82f6" stroke-width="2"/>
            
            <g stroke="#475569" stroke-width="1" font-size="12">
                <line x1="{px-s_x/2*sc}" y1="{py-N*sc/2-20}" x2="{px+s_x/2*sc}" y2="{py-N*sc/2-20}"/>
                <text x="{px}" y="{py-N*sc/2-30}" text-anchor="middle">S_x = {s_x} mm</text>
                <line x1="{px-B*sc/2-20}" y1="{py-s_y/2*sc}" x2="{px-B*sc/2-20}" y2="{py+s_y/2*sc}"/>
                <text x="{px-B*sc/2-35}" y="{py}" transform="rotate(-90 {px-B*sc/2-35} {py})" text-anchor="middle">S_y = {s_y} mm</text>
            </g>
        </g>

        <g transform="translate(600, 150)">
            <text x="80" y="-30" text-anchor="middle" font-weight="bold" font-size="14">SECTION A-A: INSTALLATION</text>
            <rect x="65" y="0" width="30" height="150" fill="#cbd5e1" stroke="#000"/>
            <path d="M 95 150 L 130 110 H 160" fill="none" stroke="#ef4444" stroke-width="1.5"/>
            <path d="M 105 135 L 115 150 H 95 Z" fill="#ef4444"/>
            <text x="132" y="105" fill="#ef4444" font-size="12" font-weight="bold">{weld_size}mm / ALL AROUND</text>
            
            <rect x="0" y="150" width="160" height="15" fill="#1e293b"/>
            <rect x="0" y="165" width="160" height="15" fill="#94a3b8" opacity="0.3"/>
            <text x="170" y="162" font-size="12" font-weight="bold">PL {tp}mm</text>
            <text x="170" y="180" font-size="11" fill="#64748b">NON-SHRINK GROUT {grout_thk}mm</text>
            
            <line x1="20" y1="120" x2="20" y2="300" stroke="#3b82f6" stroke-width="3"/>
            <rect x="10" y="165" width="20" height="8" fill="#3b82f6"/> <text x="25" y="320" font-size="10" fill="#3b82f6">ANCHOR M{bolt_d} (MIN 400mm EMBED.)</text>
        </g>
    </svg>
    </div>
    """
    components.html(svg, height=650)

    # --- 5. FIELD CHECKLIST & VERDICT ---
    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Required Plate t", f"{t_req:.2f} mm")
    c2.metric("Min. Weld Size", f"{min_weld} mm")
    c3.metric("Bolt X-Spacing", f"{s_x} mm")

    with st.expander("📝 Engineer's Notes for Construction"):
        st.write(f"""
        1. **Template:** ให้ใช้แผ่นไม้อัดหรือเพลทบางเจาะรูตามระยะ S_x={s_x} และ S_y={s_y} เพื่อประคองโบลท์ตอนเทคอนกรีต
        2. **Leveling:** ต้องมี Leveling Nut ใต้เพลทเพื่อปรับระดับก่อนเท Grout
        3. **Grouting:** ใช้ Non-shrink Grout รับแรงอัดสูง (Min 600 ksc) เทให้เต็มหน้าสัมผัส 100%
        4. **Welding:** เชื่อมแบบ Fillet Weld รอบหน้าตัดเสา (All-Around) ขนาด {weld_size} mm
        """)
