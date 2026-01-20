import streamlit as st
import streamlit.components.v1 as components
import math

def render(res_ctx, v_design):
    h, b = res_ctx['h'], res_ctx['b']
    
    # --- 1. INPUT INTERFACE ---
    with st.container(border=True):
        st.markdown("##### 📏 Plate Edge & Bolt Placement Control")
        c1, c2, c3 = st.columns(3)
        N = c1.number_input("Plate Height N (mm)", value=float(math.ceil(h + 200)))
        B = c2.number_input("Plate Width B (mm)", value=float(math.ceil(b + 200)))
        bolt_dia = c3.selectbox("Bolt Size (mm)", [16, 20, 24, 30], index=1)
        
        c4, c5 = st.columns(2)
        sx = c4.number_input("Bolt Spacing X (mm)", value=b+100)
        sy = c5.number_input("Bolt Spacing Y (mm)", value=h+100)

    # --- 2. CALCULATION OF EDGE DISTANCES ---
    # ระยะขอบ (Edge Distance)
    e_x = (B - sx) / 2
    e_y = (N - sy) / 2
    
    # เช็คระยะขอบขั้นต่ำ (AISC J3.4: ~1.25d - 1.5d)
    min_e_req = bolt_dia * 1.5
    is_e_safe = e_x >= min_e_req and e_y >= min_e_req

    # --- 3. PROFESSIONAL BLUEPRINT (SVG) ---
    sc = 360 / max(N, B)
    cv_w, cv_h = 850, 850
    cx, cy = 425, 425 # Center
    
    svg = f"""
    <div style="display:flex; justify-content:center; background:#ffffff; padding:20px; border:1px solid #1e293b; border-radius:8px;">
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <text x="25" y="40" font-family="sans-serif" font-size="20" font-weight="bold" fill="#0f172a">BASE PLATE DETAIL: EDGE DISTANCE ANALYSIS</text>
        <line x1="25" y1="55" x2="600" y2="55" stroke="#1e293b" stroke-width="3"/>

        <rect x="{cx - B*sc/2}" y="{cy - N*sc/2}" width="{B*sc}" height="{N*sc}" fill="#f8fafc" stroke="#000" stroke-width="2.5"/>
        
        <g transform="translate({cx}, {cy})" fill="#cbd5e1" stroke="#000" stroke-width="1.5">
            <rect x="{-b/2*sc}" y="{-h/2*sc}" width="{b*sc}" height="{res_ctx['tf']*sc}"/>
            <rect x="{-b/2*sc}" y="{(h/2-res_ctx['tf'])*sc}" width="{b*sc}" height="{res_ctx['tf']*sc}"/>
            <rect x="{-res_ctx['tw']/2*sc}" y="{-h/2*sc + res_ctx['tf']*sc}" width="{res_ctx['tw']*sc}" height="{(h-2*res_ctx['tf'])*sc}"/>
        </g>

        <g stroke="#3b82f6" stroke-width="2">
            <circle cx="{cx - sx/2*sc}" cy="{cy - sy/2*sc}" r="10" fill="none"/>
            <circle cx="{cx + sx/2*sc}" cy="{cy - sy/2*sc}" r="10" fill="none"/>
            <circle cx="{cx - sx/2*sc}" cy="{cy + sy/2*sc}" r="10" fill="none"/>
            <circle cx="{cx + sx/2*sc}" cy="{cy + sy/2*sc}" r="10" fill="none"/>
        </g>

        <g stroke="#16a34a" stroke-width="1.5" font-family="monospace" font-size="13" font-weight="bold">
            <line x1="{cx + sx/2*sc}" y1="{cy}" x2="{cx + B*sc/2}" y2="{cy}"/>
            <text x="{cx + (sx/2 + B/4)*sc}" y="{cy - 10}" text-anchor="middle" fill="#16a34a">e_x = {e_x}mm</text>
            
            <line x1="{cx}" y1="{cy + sy/2*sc}" x2="{cx}" y2="{cy + N*sc/2}"/>
            <text x="{cx + 10}" y="{cy + (sy/2 + N/4)*sc}" text-anchor="start" fill="#16a34a">e_y = {e_y}mm</text>
        </g>

        <g stroke="#3b82f6" stroke-width="1" font-family="monospace" font-size="12">
            <line x1="{cx - sx/2*sc}" y1="{cy + N*sc/2 + 30}" x2="{cx + sx/2*sc}" y2="{cy + N*sc/2 + 30}"/>
            <text x="{cx}" y="{cy + N*sc/2 + 50}" text-anchor="middle" fill="#3b82f6">Sx = {sx}mm</text>
            
            <line x1="{cx + B*sc/2 + 30}" y1="{cy - sy/2*sc}" x2="{cx + B*sc/2 + 30}" y2="{cy + sy/2*sc}"/>
            <text x="{cx + B*sc/2 + 50}" y="{cy}" transform="rotate(90 {cx+B*sc/2+50} {cy})" text-anchor="middle" fill="#3b82f6">Sy = {sy}mm</text>
        </g>

        <g transform="translate(50, 700)">
            <rect x="0" y="0" width="300" height="80" fill="{"#f0fdf4" if is_e_safe else "#fef2f2"}" stroke="{"#16a34a" if is_e_safe else "#dc2626"}"/>
            <text x="15" y="30" font-family="sans-serif" font-weight="bold" fill="{"#16a34a" if is_e_safe else "#dc2626"}">EDGE DISTANCE VERDICT:</text>
            <text x="15" y="55" font-family="sans-serif" font-size="14">{"✅ SAFE (PASS MIN REQ)" if is_e_safe else "❌ TOO SHORT (MIN "+str(min_e_req)+"mm)"}</text>
        </g>
    </svg>
    </div>
    """
    components.html(svg, height=860)
