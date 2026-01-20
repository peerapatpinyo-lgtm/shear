import streamlit as st
import streamlit.components.v1 as components
import math

def render(res_ctx, v_design):
    # --- 1. ENGINEERING GEOMETRY (mm) ---
    h, b, tw, tf = res_ctx['h'], res_ctx['b'], res_ctx['tw'], res_ctx['tf']
    Fy = res_ctx['Fy']
    
    # --- 2. CONSTRUCTION INPUTS ---
    with st.container(border=True):
        st.markdown("##### 📐 Structural Detailing Parameters")
        c1, c2, c3, c4 = st.columns(4)
        N = c1.number_input("N (Plate Length) mm", value=float(math.ceil(h + 150)))
        B = c2.number_input("B (Plate Width) mm", value=float(math.ceil(b + 150)))
        tp = c3.number_input("Plate Thick (mm)", value=25.0)
        bolt_d = c4.selectbox("Anchor Rod (mm)", [16, 20, 24, 30], index=1)
        
        c5, c6, c7, c8 = st.columns(4)
        edge_x = c5.number_input("Edge Dist. X (mm)", value=50.0)
        edge_y = c6.number_input("Edge Dist. Y (mm)", value=50.0)
        grout_t = c7.number_input("Grout Space (mm)", value=50.0)
        embed_l = c8.number_input("Embedment (mm)", value=400.0)

    # --- 3. THE "ALL-IN-ONE" BLUEPRINT (SVG) ---
    # คำนวณความแม่นยำเพื่อเช็ค Clearance หน้างาน
    sp_x = B - (2 * edge_x)
    sp_y = N - (2 * edge_y)
    wrench_clearance = (sp_x - b) / 2
    
    sc = 300 / max(N, B)
    cv_w, cv_h = 850, 600
    px, py = 250, 320 # Plan Center

    svg = f"""
    <div style="display: flex; justify-content: center; background: #ffffff; padding: 20px; border: 2px solid #1e293b; border-radius: 8px;">
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <rect x="10" y="10" width="830" height="50" fill="#f1f5f9" stroke="#1e293b"/>
        <text x="25" y="42" font-family="sans-serif" font-size="18" font-weight="bold" fill="#1e293b">CONSTRUCTION DRAWING: BASE PLATE & ANCHORAGE</text>

        <g transform="translate(0, 50)">
            <text x="{px}" y="30" text-anchor="middle" font-weight="bold" font-size="14" fill="#334155">TOP VIEW: BOLT SETTING</text>
            <rect x="{px-B*sc/2}" y="{py-N*sc/2}" width="{B*sc}" height="{N*sc}" fill="none" stroke="#000" stroke-width="2"/>
            
            <g transform="translate({px}, {py})" fill="#cbd5e1" stroke="#000">
                <rect x="{-b*sc/2}" y="{-h*sc/2}" width="{b*sc}" height="{tf*sc}"/>
                <rect x="{-b*sc/2}" y="{h*sc/2-tf*sc}" width="{b*sc}" height="{tf*sc}"/>
                <rect x="{-tw*sc/2}" y="{-h*sc/2+tf*sc}" width="{tw*sc}" height="{(h-2*tf)*sc}"/>
            </g>

            <g stroke="#3b82f6" stroke-width="1.5">
                <circle cx="{px-sp_x/2*sc}" cy="{py-sp_y/2*sc}" r="10" fill="none"/>
                <circle cx="{px+sp_x/2*sc}" cy="{py-sp_y/2*sc}" r="10" fill="none"/>
                <circle cx="{px-sp_x/2*sc}" cy="{py+sp_y/2*sc}" r="10" fill="none"/>
                <circle cx="{px+sp_x/2*sc}" cy="{py+sp_y/2*sc}" r="10" fill="none"/>
            </g>

            <g stroke="#64748b" stroke-width="1" font-size="11">
                <line x1="{px-sp_x/2*sc}" y1="{py-N*sc/2-20}" x2="{px+sp_x/2*sc}" y2="{py-N*sc/2-20}"/>
                <text x="{px}" y="{py-N*sc/2-30}" text-anchor="middle" fill="#000">Sp_x = {sp_x} mm</text>
                
                <line x1="{px+b/2*sc}" y1="{py}" x2="{px+sp_x/2*sc}" y2="{py}" stroke="#ef4444" stroke-dasharray="4"/>
                <text x="{px+b/2*sc+10}" y="{py-5}" fill="#ef4444" font-size="10">Gap: {wrench_clearance:.1f} mm</text>
            </g>
        </g>

        <g transform="translate(560, 150)">
            <text x="80" y="-30" text-anchor="middle" font-weight="bold" font-size="14" fill="#334155">SECTION A-A: EMBEDMENT</text>
            <rect x="65" y="0" width="30" height="150" fill="#f1f5f9" stroke="#1e293b"/>
            <rect x="0" y="150" width="160" height="15" fill="#1e293b"/>
            <rect x="0" y="165" width="160" height="10" fill="#94a3b8" opacity="0.4"/> <path d="M 30 140 L 30 350 L 60 350" fill="none" stroke="#3b82f6" stroke-width="3"/>
            <text x="40" y="300" transform="rotate(90 40 300)" font-size="10" fill="#3b82f6">Embedment = {embed_l} mm</text>
            
            <text x="170" y="162" font-weight="bold" font-size="12">PL {tp}mm</text>
            <text x="170" y="180" font-size="10" fill="#64748b">Non-Shrink Grout</text>
        </g>
    </svg>
    </div>
    """
    components.html(svg, height=650)

    # --- 4. THE PROFESSIONAL CHECKLIST ---
    st.divider()
    v1, v2, v3, v4 = st.columns(4)
    v1.metric("Wrench Gap", f"{wrench_clearance:.1f} mm", delta="OK" if wrench_clearance > 40 else "Tight")
    v2.metric("Bolt Spacing X", f"{sp_x} mm")
    v3.metric("Bolt Spacing Y", f"{sp_y} mm")
    v4.metric("Plate Status", "PASS" if tp >= 20 else "Check Load") # Simple threshold for example

    st.warning("💡 **Field Alert:** ระยะ Gap สำหรับขันประแจควรมีอย่างน้อย 40-50 mm เพื่อให้ Impact Wrench เข้าถึงได้")
