import streamlit as st
import streamlit.components.v1 as components
import math

def render(res_ctx, v_design):
    st.markdown("### 🏛️ Master Structural Detail: Base Plate Section")

    # --- 1. ดึงข้อมูลจาก Context ---
    h, b, tw, tf = res_ctx['h']/10, res_ctx['b']/10, res_ctx['tw']/10, res_ctx['tf']/10
    Fy, is_lrfd = res_ctx['Fy'], res_ctx['is_lrfd']

    # --- 2. ส่วนควบคุม (Sidebar หรือ Column) ---
    c1, c2, c3 = st.columns(3)
    with c1:
        N = st.number_input("Plate Length N (cm)", value=float(math.ceil(h + 15)))
    with c2:
        B = st.number_input("Plate Width B (cm)", value=float(math.ceil(b + 15)))
    with c3:
        tp_mm = st.number_input("Plate Thickness (mm)", value=25.0)

    # --- 3. การคำนวณตามมาตรฐาน AISC DG1 ---
    m = (N - 0.95*h)/2
    n = (B - 0.80*b)/2
    l_crit = max(m, n, (math.sqrt(h*b)/4))
    t_req = l_crit * math.sqrt((2*v_design)/(0.9*Fy*B*N)) if is_lrfd else l_crit * math.sqrt((2*v_design*1.67)/(Fy*B*N))

    # --- 4. การวาดรูปด้วย HTML/SVG (แก้ไขให้แสดงผลแน่นอน) ---
    sc = 220 / max(N, B)
    canvas_w, canvas_h = 750, 450
    cx, cy = 200, 220 # Plan Center
    
    # สร้าง String ของ SVG
    svg_code = f"""
    <div style="display: flex; justify-content: center; background: #f8fafc; padding: 20px; border-radius: 10px; border: 1px solid #e2e8f0;">
    <svg width="{canvas_w}" height="{canvas_h}" viewBox="0 0 {canvas_w} {canvas_h}" xmlns="http://www.w3.org/2000/svg">
        <rect x="0" y="0" width="{canvas_w}" height="{canvas_h}" fill="#ffffff" stroke="#334155" stroke-width="1"/>
        
        <text x="{cx}" y="40" text-anchor="middle" font-weight="bold" font-family="sans-serif" font-size="16" fill="#1e3a8a">TOP VIEW (PLAN)</text>
        <rect x="{cx - B*sc/2}" y="{cy - N*sc/2}" width="{B*sc}" height="{N*sc}" fill="none" stroke="#000" stroke-width="2"/>
        
        <g transform="translate({cx}, {cy})" fill="#94a3b8" stroke="#000">
            <rect x="{-b*sc/2}" y="{-h*sc/2}" width="{b*sc}" height="{tf*sc}"/>
            <rect x="{-b*sc/2}" y="{h*sc/2 - tf*sc}" width="{b*sc}" height="{tf*sc}"/>
            <rect x="{-tw*sc/2}" y="{-h*sc/2 + tf*sc}" width="{tw*sc}" height="{(h-2*tf)*sc}"/>
        </g>

        <g stroke="#dc2626" stroke-width="2">
            <line x1="{cx + B*sc/2}" y1="{cy}" x2="{cx + B*sc/2 - n*sc}" y2="{cy}"/>
            <line x1="{cx}" y1="{cy + N*sc/2}" x2="{cx}" y2="{cy + N*sc/2 - m*sc}"/>
        </g>
        <text x="{cx + B*sc/2 - n*sc/2}" y="{cy - 10}" fill="#dc2626" font-weight="bold" font-size="12" text-anchor="middle">n = {n:.2f}</text>
        <text x="{cx + 10}" y="{cy + N*sc/2 - m*sc/2}" fill="#dc2626" font-weight="bold" font-size="12">m = {m:.2f}</text>

        <g transform="translate(480, 80)">
            <text x="80" y="0" text-anchor="middle" font-weight="bold" font-size="14" fill="#1e3a8a">SECTION A-A</text>
            <rect x="65" y="30" width="30" height="120" fill="#cbd5e1" stroke="#000"/>
            <rect x="0" y="150" width="160" height="15" fill="#334155"/>
            <text x="170" y="162" font-size="12" font-weight="bold">PL {tp_mm} mm</text>
            <rect x="0" y="165" width="160" height="8" fill="#e2e8f0" stroke="#94a3b8" stroke-dasharray="3,2"/>
            <text x="170" y="175" font-size="10" fill="#64748b">NON-SHRINK GROUT</text>
            <rect x="-10" y="173" width="180" height="80" fill="none" stroke="#94a3b8" stroke-dasharray="5,5"/>
            <text x="80" y="240" text-anchor="middle" font-size="10" fill="#94a3b8">CONCRETE PEDESTAL</text>
        </g>
    </svg>
    </div>
    """
    
    # ใช้ components.html เพื่อให้ Browser เรนเดอร์ SVG ออกมาเป็นรูป
    components.html(svg_code, height=canvas_h + 50)

    # --- 5. สรุปผลการตรวจสอบ ---
    st.divider()
    res1, res2, res3 = st.columns(3)
    res1.metric("Min. Required t", f"{t_req*10:.2f} mm")
    res2.metric("Actual Provided t", f"{tp_mm} mm")
    if tp_mm >= t_req*10:
        res3.success("🛡️ SAFE")
    else:
        res3.error("🚨 FAIL: INCREASE t")
