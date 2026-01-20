import streamlit as st
import streamlit.components.v1 as components
import math

def render(res_ctx, v_design):
    # --- 1. PHYSICAL DIMENSIONS (mm) ---
    h, b = res_ctx['h'], res_ctx['b']
    
    # --- 2. INPUT INTERFACE ---
    with st.container(border=True):
        st.markdown("##### 📏 Drawing Geometry Control")
        c1, c2, c3 = st.columns(3)
        N = c1.number_input("Plate Height N (mm)", value=float(math.ceil(h + 150)))
        B = c2.number_input("Plate Width B (mm)", value=float(math.ceil(b + 150)))
        
        c4, c5, c6 = st.columns(3)
        sx = c4.number_input("Bolt Spacing X (mm)", value=b+100)
        sy = c5.number_input("Bolt Spacing Y (mm)", value=h+100)
        bolt_dia = c6.selectbox("Bolt Size (mm)", [16, 20, 24, 30], index=1)

    # --- 3. CALCULATE OFFSETS FOR DRAWING ---
    # ระยะห่างจาก Centerline
    half_sx, half_sy = sx/2, sy/2
    half_b, half_h = b/2, h/2
    # ระยะ Clearance (วิกฤตหน้างาน)
    clr_x = half_sx - half_b
    edge_x = (B/2) - half_sx

    # --- 4. HIGH-DETAIL BLUEPRINT (SVG) ---
    sc = 380 / max(N, B) # Scaling factor
    cv_w, cv_h = 850, 750
    cx, cy = 350, 380 # Plan Center
    
    svg = f"""
    <div style="display:flex; justify-content:center; background:#ffffff; padding:30px; border-radius:4px; border:1px solid #1e293b;">
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <rect x="5" y="5" width="{cv_w-10}" height="{cv_h-10}" fill="none" stroke="#1e293b" stroke-width="1"/>
        <text x="25" y="40" font-family="sans-serif" font-size="18" font-weight="bold">01 - BASE PLATE PLAN VIEW (UNIT: MM)</text>
        
        <g stroke="#94a3b8" stroke-width="0.8" stroke-dasharray="20,5,2,5">
            <line x1="{cx - B*sc/2 - 60}" y1="{cy}" x2="{cx + B*sc/2 + 60}" y2="{cy}"/> 
            <line x1="{cx}" y1="{cy - N*sc/2 - 60}" x2="{cx}" y2="{cy + N*sc/2 + 60}"/>
        </g>
        <text x="{cx + B*sc/2 + 70}" y="{cy+5}" font-size="12" font-style="italic">CL</text>
        <text x="{cx}" y="{cy - N*sc/2 - 70}" text-anchor="middle" font-size="12" font-style="italic">CL</text>

        <rect x="{cx - B*sc/2}" y="{cy - N*sc/2}" width="{B*sc}" height="{N*sc}" fill="#fcfcfc" stroke="#000" stroke-width="2"/>
        <g transform="translate({cx}, {cy})" fill="#cbd5e1" stroke="#000" stroke-width="1.5">
            <rect x="{-half_b*sc}" y="{-half_h*sc}" width="{b*sc}" height="{res_ctx['tf']*sc}"/> <rect x="{-half_b*sc}" y="{(half_h-res_ctx['tf'])*sc}" width="{b*sc}" height="{res_ctx['tf']*sc}"/> <rect x="{-res_ctx['tw']*sc/2}" y="{-half_h*sc + res_ctx['tf']*sc}" width="{res_ctx['tw']*sc}" height="{(h-2*res_ctx['tf'])*sc}"/> </g>

        <g stroke="#3b82f6" stroke-width="2">
            <circle cx="{cx - half_sx*sc}" cy="{cy - half_sy*sc}" r="8" fill="none"/>
            <circle cx="{cx + half_sx*sc}" cy="{cy - half_sy*sc}" r="8" fill="none"/>
            <circle cx="{cx - half_sx*sc}" cy="{cy + half_sy*sc}" r="8" fill="none"/>
            <circle cx="{cx + half_sx*sc}" cy="{cy + half_sy*sc}" r="8" fill="none"/>
        </g>

        <g stroke="#000" stroke-width="1" font-family="monospace" font-size="12">
            <line x1="{cx - B*sc/2}" y1="{cy - N*sc/2 - 50}" x2="{cx + B*sc/2}" y2="{cy - N*sc/2 - 50}"/>
            <path d="M {cx - B*sc/2} {cy-N*sc/2-55} l 5 10 M {cx + B*sc/2} {cy-N*sc/2-55} l 5 10" fill="none" stroke="#000"/>
            <text x="{cx}" y="{cy - N*sc/2 - 60}" text-anchor="middle" font-weight="bold">{B} (Overall)</text>

            <line x1="{cx - half_sx*sc}" y1="{cy - N*sc/2 - 25}" x2="{cx + half_sx*sc}" y2="{cy - N*sc/2 - 25}"/>
            <path d="M {cx - half_sx*sc} {cy-N*sc/2-30} l 5 10 M {cx} {cy-N*sc/2-30} l 5 10 M {cx+half_sx*sc} {cy-N*sc/2-30} l 5 10" />
            <text x="{cx - half_sx*sc/2}" y="{cy - N*sc/2 - 35}" text-anchor="middle">{half_sx}</text>
            <text x="{cx + half_sx*sc/2}" y="{cy - N*sc/2 - 35}" text-anchor="middle">{half_sx}</text>
        </g>

        <g stroke="#ef4444" stroke-width="1.2">
            <line x1="{cx + half_b*sc}" y1="{cy + 25}" x2="{cx + half_sx*sc}" y2="{cy + 25}"/>
            <path d="M {cx+half_b*sc} {cy+20} v 10 M {cx+half_sx*sc} {cy+20} v 10" fill="none"/>
            <text x="{cx + (half_b + half_sx)/2*sc}" y="{cy + 18}" fill="#ef4444" text-anchor="middle" font-family="monospace" font-size="11">Clearance: {clr_x} mm</text>
        </g>

        <g stroke="#16a34a" stroke-width="1.2">
            <line x1="{cx + half_sx*sc}" y1="{cy + half_sy*sc}" x2="{cx + B*sc/2}" y2="{cy + half_sy*sc}"/>
            <path d="M {cx+half_sx*sc} {cy+half_sy*sc-5} v 10 M {cx+B*sc/2} {cy+half_sy*sc-5} v 10" fill="none"/>
            <text x="{cx + (half_sx + B/2)/2*sc}" y="{cy + half_sy*sc - 8}" fill="#16a34a" text-anchor="middle" font-family="monospace" font-size="11">e: {edge_x} mm</text>
        </g>

        <g transform="translate(580, 580)" font-family="sans-serif" font-size="11">
            <rect x="0" y="0" width="240" height="130" fill="#f8fafc" stroke="#cbd5e1"/>
            <text x="10" y="20" font-weight="bold" font-size="12">ENGINEERING NOTES:</text>
            <text x="10" y="45">● DIMENSIONS IN MILLIMETERS</text>
            <text x="10" y="65">● BOLT: 4-M{bolt_dia} GR 8.8</text>
            <text x="10" y="85">● MIN CLEARANCE REQ: 40 mm</text>
            <text x="10" y="105" fill="{"#15803d" if clr_x >= 40 else "#b91c1c"}">● STATUS: {"CLEARANCE OK" if clr_x >= 40 else "TIGHT! ADJUST SpX"}</text>
        </g>
    </svg>
    </div>
    """
    components.html(svg, height=760)
