import streamlit as st
import streamlit.components.v1 as components

def render_enhanced(res_ctx, v_design):
    # --- 1. PREPARE DATA ---
    # ดึงค่าจาก Context (สมมติว่าเป็น H-Beam)
    h, b = res_ctx.get('h', 300), res_ctx.get('b', 150)
    tw, tf = res_ctx.get('tw', 6), res_ctx.get('tf', 9)

    # --- 2. INPUT INTERFACE (SIDEBAR / EXPANDER) ---
    with st.container():
        st.markdown("### 🛠️ Base Plate Configurator")
        
        # ใช้ Tabs เพื่อแยกหมวดหมู่การตั้งค่า
        tab1, tab2 = st.tabs(["📐 Geometry & Layout", "🔩 Spec & Export"])
        
        with tab1:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Offsets (ระยะห่างจากเสา)**")
                clr_x = st.number_input("Clearance X (จากขอบปีก) mm", value=50.0, step=5.0, key="clr_x")
                clr_y = st.number_input("Clearance Y (จากเอวเสา) mm", value=60.0, step=5.0, key="clr_y")
            with c2:
                st.markdown("**Plate Margins (ระยะขอบ)**")
                edge_x = st.number_input("Edge Distance X (mm)", value=40.0, step=5.0, key="edge_x")
                edge_y = st.number_input("Edge Distance Y (mm)", value=40.0, step=5.0, key="edge_y")

        with tab2:
            c3, c4 = st.columns(2)
            bolt_d = c3.selectbox("Bolt Size", [16, 20, 24, 30, 36], index=2, format_func=lambda x: f"M{x}", key="bolt_d")
            tp = c4.number_input("Plate Thickness (mm)", value=20.0, step=1.0, key="tp")
            
            st.info(f"Hole Diameter: Ø{bolt_d + 3} mm (Standard +3mm)")

    # --- 3. CALCULATIONS ---
    # ระยะห่างระหว่าง Bolt (Gauge)
    sx = b + (2 * clr_x)
    sy = tw + (2 * clr_y)  # กรณี Bolt วางข้าง Web
    
    # ขนาด Plate จริง
    B_plate = sx + (2 * edge_x)
    N_plate = sy + (2 * edge_y)
    
    # คำนวณน้ำหนักเหล็ก (Density 7850 kg/m3)
    weight = (B_plate/1000) * (N_plate/1000) * (tp/1000) * 7850

    # --- 4. SVG GENERATION LOGIC ---
    # Canvas Settings
    cv_w, cv_h = 1000, 800
    cx, cy = cv_w / 2, cv_h / 2
    
    # Auto Scaling: หา Scale ที่เหมาะสมที่สุดให้รูปเต็มจอแต่ไม่ล้น
    padding = 150 # พื้นที่เผื่อเส้น dimension
    max_dim_mm = max(B_plate, N_plate)
    avail_size_px = min(cv_w, cv_h) - (padding * 2)
    sc = avail_size_px / max_dim_mm

    # Helper function สำหรับวาดเส้น Dimension แบบมีลูกศร
    def draw_dim(x1, y1, x2, y2, text, offset=0, color="#000", is_vert=False):
        # คำนวณตำแหน่งเส้น
        if is_vert:
            lx1, ly1 = x1 + offset, y1
            lx2, ly2 = x2 + offset, y2
            tx, ty = lx1 - 10, (ly1 + ly2) / 2
            rotate = f"rotate(-90 {tx} {ty})"
        else:
            lx1, ly1 = x1, y1 + offset
            lx2, ly2 = x2, y2 + offset
            tx, ty = (lx1 + lx2) / 2, ly1 - 8
            rotate = ""

        return f"""
        <g stroke="{color}" fill="{color}" stroke-width="1.5">
            <line x1="{x1}" y1="{y1}" x2="{lx1}" y2="{ly1}" stroke-width="1" stroke-dasharray="2,2" opacity="0.5"/>
            <line x1="{x2}" y1="{y2}" x2="{lx2}" y2="{ly2}" stroke-width="1" stroke-dasharray="2,2" opacity="0.5"/>
            <line x1="{lx1}" y1="{ly1}" x2="{lx2}" y2="{ly2}" marker-start="url(#arrow)" marker-end="url(#arrow)"/>
            <text x="{tx}" y="{ty}" text-anchor="middle" font-family="monospace" font-size="14" stroke="none" transform="{rotate}">{text}</text>
        </g>
        """

    svg_content = f"""
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0 L0,6 L9,3 z" fill="#000" />
            </marker>
            <pattern id="hatch" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
                <line x1="0" y1="0" x2="0" y2="10" stroke="#94a3b8" stroke-width="1"/>
            </pattern>
        </defs>

        <rect x="0" y="0" width="{cv_w}" height="{cv_h}" fill="#ffffff"/>
        <text x="30" y="40" font-family="sans-serif" font-size="20" font-weight="bold" fill="#334155">BASE PLATE DETAIL</text>
        <line x1="30" y1="50" x2="300" y2="50" stroke="#334155" stroke-width="2"/>
        
        <g transform="translate({cv_w - 260}, 30)">
            <rect width="230" height="100" fill="#f1f5f9" rx="8" stroke="#cbd5e1"/>
            <text x="15" y="25" font-family="sans-serif" font-size="12" font-weight="bold">SUMMARY</text>
            <text x="15" y="45" font-family="monospace" font-size="12">Size: {B_plate:.0f} x {N_plate:.0f} x {int(tp)} mm</text>
            <text x="15" y="65" font-family="monospace" font-size="12">Bolts: 4-M{bolt_d}</text>
            <text x="15" y="85" font-family="monospace" font-size="12" fill="#ef4444">Weight: {weight:.2f} kg</text>
        </g>

        <g transform="translate({cx}, {cy})">
            
            <line x1="-{cv_w/2}" y1="0" x2="{cv_w/2}" y2="0" stroke="#94a3b8" stroke-dasharray="15,5,2,5" stroke-width="1"/>
            <line x1="0" y1="-{cv_h/2}" x2="0" y2="{cv_h/2}" stroke="#94a3b8" stroke-dasharray="15,5,2,5" stroke-width="1"/>

            <rect x="{-B_plate/2*sc}" y="{-N_plate/2*sc}" width="{B_plate*sc}" height="{N_plate*sc}" 
                  fill="#f8fafc" stroke="#1e293b" stroke-width="3"/>

            <g fill="url(#hatch)" stroke="#334155" stroke-width="2">
                <rect x="{-b/2*sc}" y="{-h/2*sc}" width="{b*sc}" height="{tf*sc}"/>
                <rect x="{-b/2*sc}" y="{(h/2-tf)*sc}" width="{b*sc}" height="{tf*sc}"/>
                <rect x="{-tw/2*sc}" y="{-h/2*sc + tf*sc}" width="{tw*sc}" height="{(h-2*tf)*sc}"/>
            </g>

            <g fill="#ffffff" stroke="#ef4444" stroke-width="2">
                <circle cx="{-sx/2*sc}" cy="{-sy/2*sc}" r="{bolt_d/2*sc}"/>
                <circle cx="{sx/2*sc}" cy="{-sy/2*sc}" r="{bolt_d/2*sc}"/>
                <circle cx="{-sx/2*sc}" cy="{sy/2*sc}" r="{bolt_d/2*sc}"/>
                <circle cx="{sx/2*sc}" cy="{sy/2*sc}" r="{bolt_d/2*sc}"/>
                
                <path d="M{-sx/2*sc - 5},{-sy/2*sc} h10 M{-sx/2*sc},{-sy/2*sc - 5} v10" stroke="#ef4444" stroke-width="1"/>
                <path d="M{sx/2*sc - 5},{-sy/2*sc} h10 M{sx/2*sc},{-sy/2*sc - 5} v10" stroke="#ef4444" stroke-width="1"/>
                <path d="M{-sx/2*sc - 5},{sy/2*sc} h10 M{-sx/2*sc},{sy/2*sc - 5} v10" stroke="#ef4444" stroke-width="1"/>
                <path d="M{sx/2*sc - 5},{sy/2*sc} h10 M{sx/2*sc},{sy/2*sc - 5} v10" stroke="#ef4444" stroke-width="1"/>
            </g>

            {draw_dim(-B_plate/2*sc, N_plate/2*sc, B_plate/2*sc, N_plate/2*sc, f"B = {B_plate} mm", offset=40)}
            {draw_dim(-sx/2*sc, N_plate/2*sc, sx/2*sc, N_plate/2*sc, f"Gauge = {sx}", offset=80, color="#2563eb")}
            
            {draw_dim(-B_plate/2*sc, -N_plate/2*sc, -B_plate/2*sc, N_plate/2*sc, f"N = {N_plate} mm", offset=-40, is_vert=True)}
            {draw_dim(-B_plate/2*sc, -sy/2*sc, -B_plate/2*sc, sy/2*sc, f"Gauge = {sy}", offset=-80, color="#2563eb", is_vert=True)}

            <g font-family="monospace" font-size="12" fill="#16a34a">
                 <text x="{sx/2*sc + (B_plate-sx)/4*sc}" y="{N_plate/2*sc + 25}" text-anchor="middle">edge={edge_x}</text>
                 <text x="{-B_plate/2*sc - 25}" y="{sy/2*sc + (N_plate-sy)/4*sc}" text-anchor="middle" transform="rotate(-90 {-B_plate/2*sc - 25} {sy/2*sc + (N_plate-sy)/4*sc})">edge={edge_y}</text>
            </g>

        </g>
    </svg>
    """

    # --- 5. RENDER & EXPORT ---
    # Container for the drawing with border
    st.markdown(
        f"""
        <div style="border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
            {svg_content}
        </div>
        """,
        unsafe_allow_html=True
    )

    # ปุ่ม Download (ใช้เทคนิค data URI)
    import base64
    b64 = base64.b64encode(svg_content.encode('utf-8')).decode("utf-8")
    href = f'<a href="data:image/svg+xml;base64,{b64}" download="baseplate_{int(B_plate)}x{int(N_plate)}.svg" style="text-decoration:none; color:white; background-color:#ef4444; padding:8px 16px; border-radius:4px; font-weight:bold;">📥 Download SVG Drawing</a>'
    st.markdown(f"<div style='text-align:right; margin-top:10px;'>{href}</div>", unsafe_allow_html=True)

# --- DEMO USAGE ---
# จำลองข้อมูล H-Beam (เช่น H300x150x6.5x9)
mock_ctx = {'h': 300, 'b': 150, 'tw': 6.5, 'tf': 9}
render_enhanced(mock_ctx, None)
