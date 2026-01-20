import streamlit as st
import streamlit.components.v1 as components
import math

def render(res_ctx, v_design):
    # --- 1. PHYSICAL DIMENSIONS (mm) ---
    h, b = res_ctx['h'], res_ctx['b']
    tw, tf = res_ctx['tw'], res_ctx['tf']
    
    # --- 2. INPUT INTERFACE ---
    with st.container(border=True):
        st.markdown("##### 📏 Dual-Axis Geometry & Bolt Grid")
        c1, c2, c3 = st.columns(3)
        N = c1.number_input("Plate Length N (mm)", value=float(math.ceil(h + 150)))
        B = c2.number_input("Plate Width B (mm)", value=float(math.ceil(b + 150)))
        tp = c3.number_input("Plate Thick (mm)", value=25.0)
        
        c4, c5, c6 = st.columns(3)
        sx = c4.number_input("Bolt Spacing X (mm)", value=b+100)
        sy = c5.number_input("Bolt Spacing Y (mm)", value=h+100)
        bolt_dia = c6.selectbox("Bolt Size (mm)", [16, 20, 24, 30], index=1)

    # --- 3. ANALYTICAL OFFSETS ---
    half_sx, half_sy = sx/2, sy/2
    half_b, half_h = b/2, h/2
    
    # Clearance Analysis
    clr_flange = half_sx - half_b # ระยะห่างจากปีกเสา (X)
    clr_web = half_sy - (tw/2)    # ระยะห่างจากเอวเสา (Y)
    
    # --- 4. PROFESSIONAL BLUEPRINT (SVG) ---
    sc = 340 / max(N, B)
    cv_w, cv_h = 850, 800
    cx, cy = 400, 400 # Drawing Center
    
    svg = f"""
    <div style="display:flex; justify-content:center; background:#ffffff; padding:20px; border:1px solid #1e293b;">
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <text x="20" y="35" font-family="sans-serif" font-size="18" font-weight="bold">SETTING OUT PLAN: DUAL-AXIS DIMENSIONING</text>
        <line x1="20" y1="45" x2="550" y2="45" stroke="#1e293b" stroke-width="2"/>

        <g stroke="#94a3b8" stroke-width="0.8" stroke-dasharray="20,5,2,5">
            <line x1="{cx - B*sc/2 - 80}" y1="{cy}" x2="{cx + B*sc/2 + 80}" y2="{cy}"/> 
            <line x1="{cx}" y1="{cy - N*sc/2 - 80}" x2="{cx}" y2="{cy + N*sc/2 + 80}"/>
        </g>

        <rect x="{cx - B*sc/2}" y="{cy - N*sc/2}" width="{B*sc}" height="{N*sc}" fill="none" stroke="#000" stroke-width="2.5"/>
        
        <g transform="translate({cx}, {cy})" fill="#cbd5e1" stroke="#000" stroke-width="1.5">
            <rect x="{-half_b*sc}" y="{-half_h*sc}" width="{b*sc}" height="{tf*sc}"/>
            <rect x="{-half_b*sc}" y="{(half_h-tf)*sc}" width="{b*sc}" height="{tf*sc}"/>
            <rect x="{-tw*sc/2}" y="{-half_h*sc + tf*sc}" width="{tw*sc}" height="{(h-2*tf)*sc}"/>
        </g>

        <g stroke="#3b82f6" stroke-width="2">
            <circle cx="{cx - half_sx*sc}" cy="{cy - half_sy*sc}" r="9" fill="none"/>
            <circle cx="{cx + half_sx*sc}" cy="{cy - half_sy*sc}" r="9" fill="none"/>
            <circle cx="{cx - half_sx*sc}" cy="{cy + half_sy*sc}" r="9" fill="none"/>
            <circle cx="{cx + half_sx*sc}" cy="{cy + half_sy*sc}" r="9" fill="none"/>
        </g>

        <g stroke="#000" stroke-width="1" font-family="monospace" font-size="12">
            <line x1="{cx - B*sc/2}" y1="{cy - N*sc/2 - 60}" x2="{cx + B*sc/2}" y2="{cy - N*sc/2 - 60}"/>
            <path d="M {cx - B*sc/2} {cy-N*sc/2-65} l 5 10 M {cx + B*sc/2} {cy-N*sc/2-65} l 5 10" />
            <text x="{cx}" y="{cy - N*sc/2 - 70}" text-anchor="middle" font-weight="bold">B = {B}</text>

            <line x1="{cx - half_sx*sc}" y1="{cy - N*sc/2 - 30}" x2="{cx + half_sx*sc}" y2="{cy - N*sc/2 - 30}"/>
            <path d="M {cx - half_sx*sc} {cy-N*sc/2-35} v 10 M {cx} {cy-N*sc/2-35} v 10 M {cx+half_sx*sc} {cy-N*sc/2-35} v 10" />
            <text x="{cx - half_sx*sc/2}" y="{cy - N*sc/2 - 40}" text-anchor="middle">{half_sx}</text>
            <text x="{cx + half_sx*sc/2}" y="{cy - N*sc/2 - 40}" text-anchor="middle">{half_sx}</text>
        </g>

        <g stroke="#000" stroke-width="1" font-family="monospace" font-size="12">
            <line x1="{cx - B*sc/2 - 60}" y1="{cy - N*sc/2}" x2="{cx - B*sc/2 - 60}" y2="{cy + N*sc/2}"/>
            <path d="M {cx-B*sc/2-65} {cy-N*sc/2} h 10 M {cx-B*sc/2-65} {cy+N*sc/2} h 10" />
            <text x="{cx - B*sc/2 - 70}" y="{cy}" transform="rotate(-90 {cx-B*sc/2-70} {cy})" text-anchor="middle" font-weight="bold">N = {N}</text>

            <line x1="{cx - B*sc/2 - 30}" y1="{cy - half_sy*sc}" x2="{cx - B*sc/2 - 30}" y2="{cy + half_sy*sc}"/>
            <path d="M {cx-B*sc/2-35} {cy-half_sy*sc} h 10 M {cx-B*sc/2-35} {cy} h 10 M {cx-B*sc/2-35} {cy+half_sy*sc} h 10" />
            <text x="{cx - B*sc/2 - 40}" y="{cy - half_sy*sc/2}" transform="rotate(-90 {cx-B*sc/2-40} {cy-half_sy*sc/2})" text-anchor="middle">{half_sy}</text>
            <text x="{cx - B*sc/2 - 40}" y="{cy + half_sy*sc/2}" transform="rotate(-90 {cx-B*sc/2-40} {cy+half_sy*sc/2})" text-anchor="middle">{half_sy}</text>
        </g>

        <g stroke="#ef4444" stroke-width="1.2" font-family="monospace" font-size="10">
            <line x1="{cx + half_b*sc}" y1="{cy + 25}" x2="{cx + half_sx*sc}" y2="{cy + 25}"/>
            <text x="{cx + (half_b + half_sx)/2*sc}" y="{cy + 20}" text-anchor="middle" fill="#ef4444">Clr_X: {clr_flange}mm</text>
            
            <line x1="{cx + 15}" y1="{cy - half_h*sc + tf*sc}" x2="{cx + 15}" y2="{cy - half_sy*sc}"/>
            <text x="{cx + 20}" y="{cy - (half_h + half_sy)/2*sc}" text-anchor="start" fill="#ef4444" transform="rotate(90 {cx+20} {cy - (half_h + half_sy)/2*sc})">Clr_Y: {clr_web}mm</text>
        </g>

        <g transform="translate(560, 600)" font-family="sans-serif">
            <rect x="0" y="0" width="260" height="150" fill="#f8fafc" stroke="#1e293b"/>
            <text x="15" y="25" font-weight="bold" font-size="13">FABRICATION SCHEDULE</text>
            <line x1="15" y1="35" x2="245" y2="35" stroke="#cbd5e1"/>
            <text x="15" y="60" font-size="11">● PLATE: {B}x{N}x{tp} mm</text>
            <text x="15" y="80" font-size="11">● HOLES: 4-Ø{bolt_dia+6} mm</text>
            <text x="15" y="100" font-size="11">● PITCH (Sy): {sy} mm</text>
            <text x="15" y="120" font-size="11">● GAUGE (Sx): {sx} mm</text>
            <text x="15" y="140" font-size="10" fill="#64748b">*Oversized holes for erection</text>
        </g>
    </svg>
    </div>
    """
    components.html(svg, height=820)
