import streamlit as st
import streamlit.components.v1 as components
import math

def render(res_ctx, v_design):
    # --- 1. COLUMN DATA (mm) ---
    h, b = res_ctx['h'], res_ctx['b']
    tw, tf = res_ctx['tw'], res_ctx['tf']
    
    # --- 2. INPUT INTERFACE (Manual Control) ---
    with st.container(border=True):
        st.markdown("##### 🛠️ Precision Clearance & Plate Control")
        c1, c2, c3 = st.columns(3)
        # ให้วิศวกรเลือกระยะเว้นจากเสาเอง
        clr_x_req = c1.number_input("Clearance X (จากขอบปีก) mm", value=50.0)
        clr_y_req = c2.number_input("Clearance Y (จากเอวเสา) mm", value=60.0)
        bolt_dia = c3.selectbox("Anchor Bolt Size (mm)", [16, 20, 24, 30], index=1)
        
        c4, c5, c6 = st.columns(3)
        # ระยะขอบ Plate ที่ต้องการเผื่อ
        edge_x_req = c4.number_input("Edge Distance X (mm)", value=50.0)
        edge_y_req = c5.number_input("Edge Distance Y (mm)", value=50.0)
        tp = c6.number_input("Plate Thickness (mm)", value=25.0)

    # --- 3. AUTO-CALCULATE SPACING & TOTAL SIZE ---
    # คำนวณระยะ Spacing จาก Clearance ที่เลือก
    sx = b + (2 * clr_x_req)
    sy = tw + (2 * clr_y_req) # วัดจาก Web (เอวเสา)
    
    # คำนวณขนาด Plate รวม
    B_total = sx + (2 * edge_x_req)
    N_total = sy + (2 * edge_y_req)

    # --- 4. MASTER BLUEPRINT (SVG) ---
    sc = 350 / max(N_total, B_total)
    cv_w, cv_h = 900, 850
    cx, cy = 450, 400
    
    svg = f"""
    <div style="display:flex; justify-content:center; background:#ffffff; padding:20px; border:2px solid #0f172a;">
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <g stroke="#94a3b8" stroke-width="0.8" stroke-dasharray="10,5">
            <line x1="{cx - B_total*sc/2 - 50}" y1="{cy}" x2="{cx + B_total*sc/2 + 50}" y2="{cy}"/> 
            <line x1="{cx}" y1="{cy - N_total*sc/2 - 50}" x2="{cx}" y2="{cy + N_total*sc/2 + 50}"/>
        </g>

        <rect x="{cx - B_total*sc/2}" y="{cy - N_total*sc/2}" width="{B_total*sc}" height="{N_total*sc}" fill="#fcfcfc" stroke="#000" stroke-width="3"/>
        
        <g transform="translate({cx}, {cy})" fill="#cbd5e1" stroke="#000" stroke-width="2">
            <rect x="{-b/2*sc}" y="{-h/2*sc}" width="{b*sc}" height="{tf*sc}"/>
            <rect x="{-b/2*sc}" y="{(h/2-tf)*sc}" width="{b*sc}" height="{tf*sc}"/>
            <rect x="{-tw/2*sc}" y="{-h/2*sc + tf*sc}" width="{tw*sc}" height="{(h-2*tf)*sc}"/>
        </g>

        <g stroke="#3b82f6" stroke-width="2">
            <circle cx="{cx - sx/2*sc}" cy="{cy - sy/2*sc}" r="10" fill="white"/>
            <circle cx="{cx + sx/2*sc}" cy="{cy - sy/2*sc}" r="10" fill="white"/>
            <circle cx="{cx - sx/2*sc}" cy="{cy + sy/2*sc}" r="10" fill="white"/>
            <circle cx="{cx + sx/2*sc}" cy="{cy + sy/2*sc}" r="10" fill="white"/>
        </g>

        <g stroke="#ef4444" stroke-width="1.5" font-family="monospace" font-size="12" font-weight="bold">
            <line x1="{cx + b/2*sc}" y1="{cy - sy/2*sc}" x2="{cx + sx/2*sc}" y2="{cy - sy/2*sc}"/>
            <text x="{cx + (b/2 + sx/2)/2*sc}" y="{cy - sy/2*sc - 10}" text-anchor="middle" fill="#ef4444">Clr_X: {clr_x_req}</text>
            
            <line x1="{cx}" y1="{cy - tw/2*sc}" x2="{cx}" y2="{cy - sy/2*sc}"/>
            <text x="{cx + 10}" y="{cy - (tw/2 + sy/2)/2*sc}" text-anchor="start" fill="#ef4444">Clr_Y: {clr_y_req}</text>
        </g>

        <g stroke="#16a34a" stroke-width="1.5" font-family="monospace" font-size="12">
            <line x1="{cx + sx/2*sc}" y1="{cy + sy/2*sc}" x2="{cx + B_total*sc/2}" y2="{cy + sy/2*sc}"/>
            <text x="{cx + (sx/2 + B_total/2)/2*sc}" y="{cy + sy/2*sc - 10}" text-anchor="middle" fill="#16a34a">e_x: {edge_x_req}</text>
            
            <line x1="{cx - sx/2*sc}" y1="{cy + sy/2*sc}" x2="{cx - sx/2*sc}" y2="{cy + N_total*sc/2}"/>
            <text x="{cx - sx/2*sc - 10}" y="{cy + (sy/2 + N_total/2)/2*sc}" text-anchor="end" fill="#16a34a">e_y: {edge_y_req}</text>
        </g>

        <g transform="translate(30, 680)">
            <rect x="0" y="0" width="350" height="130" fill="#f8fafc" stroke="#0f172a" stroke-width="1"/>
            <text x="15" y="25" font-weight="bold" font-size="14">FINAL DIMENSIONS (mm)</text>
            <text x="15" y="55" font-size="13">PLATE SIZE: {B_total} x {N_total} x {tp}</text>
            <text x="15" y="80" font-size="13">BOLT SPACING (Sx, Sy): {sx}, {sy}</text>
            <text x="15" y="105" font-size="13">BOLT HOLE: Ø{bolt_dia + 6} (M{bolt_dia} Bolt)</text>
        </g>
    </svg>
    </div>
    """
    components.html(svg, height=870)
