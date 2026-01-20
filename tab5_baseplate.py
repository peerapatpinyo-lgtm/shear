import streamlit as st
import streamlit.components.v1 as components
import math

def render(res_ctx, v_design):
    # --- 1. GEOMETRY DATA ---
    h, b = res_ctx['h'], res_ctx['b']
    tw, tf = res_ctx['tw'], res_ctx['tf']
    
    # --- 2. INPUT INTERFACE ---
    with st.container(border=True):
        st.markdown("##### 📐 Design Control & Manual Offsets")
        c1, c2, c3 = st.columns(3)
        clr_x = c1.number_input("Clearance X (จากขอบปีก) mm", value=50.0)
        clr_y = c2.number_input("Clearance Y (จากเอวเสา) mm", value=60.0)
        bolt_d = c3.selectbox("Bolt Size (mm)", [16, 20, 24, 30], index=1)
        
        c4, c5, c6 = st.columns(3)
        edge_x = c4.number_input("Edge Distance X (mm)", value=50.0)
        edge_y = c5.number_input("Edge Distance Y (mm)", value=50.0)
        tp = c6.number_input("Plate Thickness (mm)", value=25.0)

    # --- 3. COORDINATE CALCULATIONS ---
    sx = b + (2 * clr_x)
    sy = tw + (2 * clr_y)
    B = sx + (2 * edge_x)
    N = sy + (2 * edge_y)

    # Scaling
    sc = 420 / max(N, B)
    cv_w, cv_h = 950, 950
    cx, cy = 475, 475 # Center
    
    svg = f"""
    <div style="display:flex; justify-content:center; background:#ffffff; padding:20px; border:2px solid #1e293b; border-radius:10px;">
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <rect x="10" y="10" width="{cv_w-20}" height="{cv_h-20}" fill="none" stroke="#000" stroke-width="1"/>
        <text x="30" y="50" font-family="sans-serif" font-size="24" font-weight="bold">BASE PLATE SHOP DRAWING (BP-01)</text>
        <line x1="30" y1="65" x2="600" y2="65" stroke="#000" stroke-width="3"/>

        <g stroke="#94a3b8" stroke-width="1" stroke-dasharray="20,5,2,5">
            <line x1="{cx - B*sc/2 - 80}" y1="{cy}" x2="{cx + B*sc/2 + 80}" y2="{cy}"/> 
            <line x1="{cx}" y1="{cy - N*sc/2 - 80}" x2="{cx}" y2="{cy + N*sc/2 + 80}"/>
        </g>
        <text x="{cx + B*sc/2 + 90}" y="{cy+5}" font-style="italic" font-size="14">GRID CL</text>

        <rect x="{cx - B*sc/2}" y="{cy - N*sc/2}" width="{B*sc}" height="{N*sc}" fill="#f8fafc" stroke="#000" stroke-width="3"/>
        
        <g transform="translate({cx}, {cy})" fill="#cbd5e1" stroke="#000" stroke-width="2">
            <rect x="{-b/2*sc}" y="{-h/2*sc}" width="{b*sc}" height="{tf*sc}"/>
            <rect x="{-b/2*sc}" y="{(h/2-tf)*sc}" width="{b*sc}" height="{tf*sc}"/>
            <rect x="{-tw/2*sc}" y="{-h/2*sc + tf*sc}" width="{tw*sc}" height="{(h-2*tf)*sc}"/>
        </g>

        <g stroke="#3b82f6" stroke-width="2.5">
            <circle cx="{cx - sx/2*sc}" cy="{cy - sy/2*sc}" r="12" fill="white"/>
            <circle cx="{cx + sx/2*sc}" cy="{cy - sy/2*sc}" r="12" fill="white"/>
            <circle cx="{cx - sx/2*sc}" cy="{cy + sy/2*sc}" r="12" fill="white"/>
            <circle cx="{cx + sx/2*sc}" cy="{cy + sy/2*sc}" r="12" fill="white"/>
        </g>

        <g stroke="#000" stroke-width="1.2" font-family="monospace" font-size="14">
            <line x1="{cx - B*sc/2}" y1="{cy - N*sc/2 - 100}" x2="{cx + B*sc/2}" y2="{cy - N*sc/2 - 100}"/>
            <text x="{cx}" y="{cy - N*sc/2 - 110}" text-anchor="middle" font-weight="bold">B = {B} mm</text>
            
            <line x1="{cx - sx/2*sc}" y1="{cy - N*sc/2 - 60}" x2="{cx + sx/2*sc}" y2="{cy - N*sc/2 - 60}" stroke="#3b82f6"/>
            <text x="{cx}" y="{cy - N*sc/2 - 70}" text-anchor="middle" fill="#3b82f6">Sx = {sx} mm</text>

            <line x1="{cx + sx/2*sc}" y1="{cy - N*sc/2 - 30}" x2="{cx + B*sc/2}" y2="{cy - N*sc/2 - 30}" stroke="#16a34a"/>
            <text x="{cx + (sx/2 + B/2)/2*sc}" y="{cy - N*sc/2 - 35}" text-anchor="middle" fill="#16a34a" font-size="12">ex={edge_x}</text>
        </g>

        <g stroke="#000" stroke-width="1.2" font-family="monospace" font-size="14">
            <line x1="{cx - B*sc/2 - 100}" y1="{cy - N*sc/2}" x2="{cx - B*sc/2 - 100}" y2="{cy + N*sc/2}"/>
            <text x="{cx - B*sc/2 - 115}" y="{cy}" transform="rotate(-90 {cx-B*sc/2-115} {cy})" text-anchor="middle" font-weight="bold">N = {N} mm</text>

            <line x1="{cx - B*sc/2 - 60}" y1="{cy - sy/2*sc}" x2="{cx - B*sc/2 - 60}" y2="{cy + sy/2*sc}" stroke="#3b82f6"/>
            <text x="{cx - B*sc/2 - 75}" y="{cy}" transform="rotate(-90 {cx-B*sc/2-75} {cy})" text-anchor="middle" fill="#3b82f6">Sy = {sy} mm</text>
            
            <line x1="{cx - B*sc/2 - 30}" y1="{cy + sy/2*sc}" x2="{cx - B*sc/2 - 30}" y2="{cy + N*sc/2}" stroke="#16a34a"/>
            <text x="{cx - B*sc/2 - 35}" y="{cy + (sy/2 + N/2)/2*sc}" transform="rotate(-90 {cx-B*sc/2-35} {cy + (sy/2 + N/2)/2*sc})" text-anchor="middle" fill="#16a34a" font-size="12">ey={edge_y}</text>
        </g>

        <g stroke="#ef4444" stroke-width="1.5" font-family="monospace" font-size="13">
            <line x1="{cx + b/2*sc}" y1="{cy}" x2="{cx + sx/2*sc}" y2="{cy}"/>
            <text x="{cx + (b/2 + sx/2)/2*sc}" y="{cy - 8}" text-anchor="middle" fill="#ef4444" font-weight="bold">Clr_X={clr_x}</text>
            
            <line x1="{cx}" y1="{cy + tw/2*sc}" x2="{cx}" y2="{cy + sy/2*sc}"/>
            <text x="{cx + 8}" y="{cy + (tw/2 + sy/2)/2*sc}" text-anchor="start" fill="#ef4444" font-weight="bold">Clr_Y={clr_y}</text>
        </g>

        <g transform="translate(620, 750)">
            <rect x="0" y="0" width="280" height="150" fill="#f8fafc" stroke="#000" stroke-width="2"/>
            <text x="15" y="30" font-family="sans-serif" font-weight="bold" font-size="16">SPECIFICATIONS</text>
            <line x1="15" y1="40" x2="265" y2="40" stroke="#000"/>
            <text x="15" y="65" font-family="monospace" font-size="13">PLATE: {B}x{N}x{tp} mm</text>
            <text x="15" y="90" font-family="monospace" font-size="13">BOLTS: 4-M{bolt_d} GR 8.8</text>
            <text x="15" y="115" font-family="monospace" font-size="13">WELD : FILLET ALL AROUND</text>
            <text x="15" y="140" font-family="monospace" font-size="11" fill="#64748b">HOLE DIA: Ø{bolt_d+6} mm</text>
        </g>
    </svg>
    </div>
    """
    components.html(svg, height=980)

