import streamlit as st
import streamlit.components.v1 as components
import math

def render(res_ctx, v_design):
    # --- 1. GEOMETRY DATA (mm) ---
    h, b = res_ctx['h'], res_ctx['b']
    tw, tf = res_ctx['tw'], res_ctx['tf']
    
    # --- 2. INPUT INTERFACE ---
    with st.container(border=True):
        st.markdown("##### 📐 Base Plate Configuration")
        c1, c2, c3 = st.columns(3)
        clr_x = c1.number_input("Clearance X (Side) mm", value=50.0)
        clr_y = c2.number_input("Clearance Y (Top/Bot) mm", value=60.0)
        bolt_d = c3.selectbox("Bolt Size (mm)", [16, 20, 24, 30], index=1)
        
        c4, c5, c6 = st.columns(3)
        edge_x = c4.number_input("Edge Distance X (mm)", value=50.0)
        edge_y = c5.number_input("Edge Distance Y (mm)", value=50.0)
        tp = c6.number_input("Plate Thickness (mm)", value=25.0)

    # --- 3. CALCULATE PLATE DIMENSIONS ---
    # B = Width (ตามแนวปีก b), N = Height (ตามแนวความลึก h)
    B = b + (2 * clr_x) + (2 * edge_x)
    N = h + (2 * clr_y) + (2 * edge_y)
    
    # ระยะห่างระหว่างโบลต์ (Bolt Spacing)
    sx = b + (2 * clr_x)
    sy = h + (2 * clr_y)

    # --- 4. SVG SETTINGS ---
    cv_w, cv_h = 800, 800
    cx, cy = cv_w/2, cv_h/2
    
    # Dynamic Scaling: ให้รูปพอดีกับ Canvas เสมอ (เผื่อที่ว่างสำหรับ Dimension 150px)
    draw_area = 500 
    sc = draw_area / max(N, B)

    # สไตล์เส้น
    dim_style = 'stroke="#64748b" stroke-width="1"'
    tick_style = 'stroke="#000" stroke-width="1.5"'
    beam_style = 'fill="#cbd5e1" stroke="#1e293b" stroke-width="1.5"'
    bolt_style = 'fill="white" stroke="#2563eb" stroke-width="2"'

    # --- 5. GENERATE SVG ---
    svg_content = f"""
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#ffffff" />
        <text x="20" y="40" font-family="sans-serif" font-size="18" font-weight="bold" fill="#1e293b">BASE PLATE DRAWING: {int(B)}x{int(N)} mm</text>
        
        <g transform="translate({cx}, {cy})">
            
            <rect x="{-B*sc/2}" y="{-N*sc/2}" width="{B*sc}" height="{N*sc}" fill="#f1f5f9" stroke="#000" stroke-width="2.5"/>

            <g>
                <rect x="{-b/2*sc}" y="{-h/2*sc}" width="{b*sc}" height="{tf*sc}" {beam_style}/>
                <rect x="{-b/2*sc}" y="{(h/2-tf)*sc}" width="{b*sc}" height="{tf*sc}" {beam_style}/>
                <rect x="{-tw/2*sc}" y="{-h/2*sc + tf*sc}" width="{tw*sc}" height="{(h-2*tf)*sc}" {beam_style}/>
            </g>

            <g>
                <circle cx="{-sx/2*sc}" cy="{-sy/2*sc}" r="{bolt_d*sc*0.8}" {bolt_style}/>
                <circle cx="{sx/2*sc}"  cy="{-sy/2*sc}" r="{bolt_d*sc*0.8}" {bolt_style}/>
                <circle cx="{-sx/2*sc}" cy="{sy/2*sc}"  r="{bolt_d*sc*0.8}" {bolt_style}/>
                <circle cx="{sx/2*sc}"  cy="{sy/2*sc}"  r="{bolt_d*sc*0.8}" {bolt_style}/>
                <g stroke="#2563eb" stroke-width="1">
                    <line x1="{-sx/2*sc-5}" y1="{-sy/2*sc}" x2="{-sx/2*sc+5}" y2="{-sy/2*sc}" />
                    <line x1="{-sx/2*sc}" y1="{-sy/2*sc-5}" x2="{-sx/2*sc}" y2="{-sy/2*sc+5}" />
                    </g>
            </g>

            <g transform="translate(0, {-N*sc/2 - 40})">
                <line x1="{-B*sc/2}" y1="0" x2="{B*sc/2}" y2="0" {dim_style}/>
                <line x1="{-B*sc/2-5}" y1="5" x2="{-B*sc/2+5}" y2="-5" {tick_style}/>
                <line x1="{B*sc/2-5}" y1="5" x2="{B*sc/2+5}" y2="-5" {tick_style}/>
                <text x="0" y="-10" text-anchor="middle" font-family="monospace" font-size="14" font-weight="bold">B = {int(B)}</text>
            </g>
            
            <g transform="translate(0, {-N*sc/2 - 15})">
                <line x1="{-sx/2*sc}" y1="0" x2="{sx/2*sc}" y2="0" stroke="#2563eb" stroke-width="1"/>
                <text x="0" y="-5" text-anchor="middle" font-family="monospace" font-size="12" fill="#2563eb">Sx = {int(sx)}</text>
            </g>

            <g transform="translate({-B*sc/2 - 60}, 0)">
                <line x1="0" y1="{-N*sc/2}" x2="0" y2="{N*sc/2}" {dim_style}/>
                <line x1="-5" y1="{-N*sc/2+5}" x2="5" y2="{-N*sc/2-5}" {tick_style}/>
                <line x1="-5" y1="{N*sc/2+5}" x2="5" y2="{N*sc/2-5}" {tick_style}/>
                <text x="-15" y="0" transform="rotate(-90, -15, 0)" text-anchor="middle" font-family="monospace" font-size="14" font-weight="bold">N = {int(N)}</text>
            </g>

            <g stroke="#94a3b8" stroke-width="1" stroke-dasharray="10,5">
                <line x1="{-B*sc/2 - 20}" y1="0" x2="{B*sc/2 + 20}" y2="0" />
                <line x1="0" y1="{-N*sc/2 - 20}" x2="0" y2="{N*sc/2 + 20}" />
            </g>
        </g>

        <g transform="translate({cv_w-220}, {cv_h-130})">
            <rect width="200" height="110" fill="#f8fafc" stroke="#334155" rx="5"/>
            <text x="10" y="25" font-family="sans-serif" font-weight="bold" font-size="14">DATA SHEET</text>
            <line x1="10" y1="35" x2="190" y2="35" stroke="#334155" />
            <text x="10" y="55" font-family="monospace" font-size="12">Plate: t={int(tp)} mm</text>
            <text x="10" y="75" font-family="monospace" font-size="12">Bolt: 4-M{bolt_d} (8.8)</text>
            <text x="10" y="95" font-family="monospace" font-size="12">Hole: Ø{bolt_d+4} mm</text>
        </g>
    </svg>
    """
    components.html(svg_content, height=800)
