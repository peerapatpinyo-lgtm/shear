import streamlit as st
import streamlit.components.v1 as components
import math
import steel_db 

def render(res_ctx, v_design):
    # --- 1. SELECTION & INPUTS ---
    with st.container(border=True):
        col_main1, col_main2 = st.columns([1, 1.5])
        with col_main1:
            st.markdown("##### 📦 Column Section")
            sec_list = steel_db.get_section_list()
            col_name = st.selectbox("Select Column Size", sec_list, index=sec_list.index(res_ctx['sec_name']) if res_ctx['sec_name'] in sec_list else 13)
            props = steel_db.get_properties(col_name)
            ch, cb, ctw, ctf = float(props['h']), float(props['b']), float(props['tw']), float(props['tf'])
            
        with col_main2:
            st.markdown("##### 📐 Detailed Offsets")
            c1, c2, c3 = st.columns(3)
            clr_x = c1.number_input("Clearance X (mm)", value=50.0, help="ระยะจากขอบปีกเสาถึงรูโบลต์")
            clr_y = c2.number_input("Clearance Y (mm)", value=60.0, help="ระยะจากด้านในปีกเสาถึงรูโบลต์")
            tp = c3.number_input("Plate Thickness (mm)", value=25.0)
            
            c4, c5, c6 = st.columns(3)
            edge_x = c4.number_input("Edge Dist X (mm)", value=50.0)
            edge_y = c5.number_input("Edge Dist Y (mm)", value=50.0)
            bolt_d = c6.selectbox("Bolt Size", [16, 20, 24, 30], index=1)

    # --- 2. CALCULATE ALL COORDINATES (mm) ---
    sx = cb + (2 * clr_x)
    sy = ch - (2 * ctf) + (2 * clr_y)
    B = sx + (2 * edge_x)
    N = sy + (2 * edge_y)
    hole_d = bolt_d + 4

    # --- 3. SVG DRAWING CONFIG ---
    cv_w, cv_h = 1000, 950
    cx, cy = cv_w/2, cv_h/2 - 20
    sc = 520 / max(N, B) # Scaling Factor

    # Helper function for CAD Ticks
    def draw_tick(x, y, vertical=False):
        if vertical: return f'<line x1="{x-5}" y1="{y+5}" x2="{x+5}" y2="{y-5}" stroke="black" stroke-width="1.5"/>'
        return f'<line x1="{x-5}" y1="{y+5}" x2="{x+5}" y2="{y-5}" stroke="black" stroke-width="1.5"/>'

    svg = f"""
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#ffffff" />
        <text x="40" y="45" font-family="sans-serif" font-size="20" font-weight="bold">DETAILED BASE PLATE LAYOUT (BP-01)</text>
        
        <g transform="translate({cx}, {cy})">
            <rect x="{-B*sc/2}" y="{-N*sc/2}" width="{B*sc}" height="{N*sc}" fill="#fcfcfc" stroke="#000" stroke-width="2.5"/>
            
            <g fill="#e2e8f0" stroke="#1e293b" stroke-width="1.5">
                <rect x="{-cb/2*sc}" y="{-ch/2*sc}" width="{cb*sc}" height="{ctf*sc}"/> 
                <rect x="{-cb/2*sc}" y="{(ch/2-ctf)*sc}" width="{cb*sc}" height="{ctf*sc}"/>
                <rect x="{-ctw/2*sc}" y="{-ch/2*sc+ctf*sc}" width="{ctw*sc}" height="{(ch-2*ctf)*sc}"/>
            </g>

            <g fill="#ffffff" stroke="#2563eb" stroke-width="2">
                <circle cx="{-sx/2*sc}" cy="{-sy/2*sc}" r="{hole_d*sc/2}"/>
                <circle cx="{sx/2*sc}"  cy="{-sy/2*sc}" r="{hole_d*sc/2}"/>
                <circle cx="{-sx/2*sc}" cy="{sy/2*sc}"  r="{hole_d*sc/2}"/>
                <circle cx="{sx/2*sc}"  cy="{sy/2*sc}"  r="{hole_d*sc/2}"/>
            </g>

            <g transform="translate(0, {N*sc/2 + 60})" font-family="monospace" font-size="12">
                <line x1="{-B*sc/2}" y1="0" x2="{B*sc/2}" y2="0" stroke="black" stroke-width="1"/>
                
                {draw_tick(-B*sc/2, 0)} {draw_tick(-sx*sc/2, 0)} {draw_tick(-cb*sc/2, 0)}
                {draw_tick(cb*sc/2, 0)} {draw_tick(sx*sc/2, 0)} {draw_tick(B*sc/2, 0)}
                
                <text x="{-B*sc/2 + (edge_x*sc/2)}" y="15" text-anchor="middle" fill="green">{int(edge_x)}</text>
                <text x="{-sx*sc/2 + (clr_x*sc/2)}" y="15" text-anchor="middle" fill="red">{int(clr_x)}</text>
                <text x="0" y="15" text-anchor="middle" font-weight="bold">COL WIDTH: {int(cb)}</text>
                <text x="{sx*sc/2 - (clr_x*sc/2)}" y="15" text-anchor="middle" fill="red">{int(clr_x)}</text>
                <text x="{B*sc/2 - (edge_x*sc/2)}" y="15" text-anchor="middle" fill="green">{int(edge_x)}</text>
                
                <line x1="{-sx*sc/2}" y1="35" x2="{sx*sc/2}" y2="35" stroke="#2563eb" stroke-width="1" stroke-dasharray="4"/>
                <text x="0" y="50" text-anchor="middle" fill="#2563eb" font-weight="bold">Sx = {int(sx)}</text>
                
                <line x1="{-B*sc/2}" y1="70" x2="{B*sc/2}" y2="70" stroke="black" stroke-width="2"/>
                <text x="0" y="85" text-anchor="middle" font-size="14" font-weight="bold">B = {int(B)} mm</text>
            </g>

            <g transform="translate({B*sc/2 + 60}, 0)" font-family="monospace" font-size="12">
                <line x1="0" y1="{-N*sc/2}" x2="0" y2="{N*sc/2}" stroke="black" stroke-width="1"/>
                {draw_tick(0, -N*sc/2)} {draw_tick(0, -sy*sc/2)} {draw_tick(0, -(ch/2-ctf)*sc)}
                {draw_tick(0, (ch/2-ctf)*sc)} {draw_tick(0, sy*sc/2)} {draw_tick(0, N*sc/2)}
                
                <text x="15" y="{-N*sc/2 + (edge_y*sc/2)}" text-anchor="middle" transform="rotate(90, 15, {-N*sc/2 + (edge_y*sc/2)})" fill="green">{int(edge_y)}</text>
                <text x="15" y="{-sy*sc/2 + (clr_y*sc/2)}" text-anchor="middle" transform="rotate(90, 15, {-sy*sc/2 + (clr_y*sc/2)})" fill="red">{int(clr_y)}</text>
                <text x="15" y="0" text-anchor="middle" transform="rotate(90, 15, 0)" font-weight="bold">WEB HT: {int(ch-2*ctf)}</text>
                <text x="15" y="{sy*sc/2 - (clr_y*sc/2)}" text-anchor="middle" transform="rotate(90, 15, {sy*sc/2 - (clr_y*sc/2)})" fill="red">{int(clr_y)}</text>
                <text x="15" y="{N*sc/2 - (edge_y*sc/2)}" text-anchor="middle" transform="rotate(90, 15, {N*sc/2 - (edge_y*sc/2)})" fill="green">{int(edge_y)}</text>

                <line x1="35" y1="{-sy*sc/2}" x2="35" y2="{sy*sc/2}" stroke="#2563eb" stroke-width="1" stroke-dasharray="4"/>
                <text x="50" y="0" text-anchor="middle" transform="rotate(90, 50, 0)" fill="#2563eb" font-weight="bold">Sy = {int(sy)}</text>

                <line x1="75" y1="{-N*sc/2}" x2="75" y2="{N*sc/2}" stroke="black" stroke-width="2"/>
                <text x="90" y="0" text-anchor="middle" transform="rotate(90, 90, 0)" font-size="14" font-weight="bold">N = {int(N)} mm</text>
            </g>

            <g stroke="#94a3b8" stroke-width="0.8" stroke-dasharray="10,5">
                <line x1="{-B*sc/2 - 20}" y1="0" x2="{B*sc/2 + 20}" y2="0"/>
                <line x1="0" y1="{-N*sc/2 - 20}" x2="0" y2="{N*sc/2 + 20}"/>
            </g>
        </g>

        <g transform="translate(40, {cv_h - 180})">
            <rect width="250" height="140" fill="#f8fafc" stroke="#1e293b" rx="5"/>
            <text x="15" y="25" font-family="sans-serif" font-weight="bold" font-size="14" fill="#1e293b">DIMENSION KEY</text>
            <circle cx="20" cy="45" r="5" fill="green"/><text x="35" y="50" font-family="monospace" font-size="12">Edge Distance (e)</text>
            <circle cx="20" cy="70" r="5" fill="red"/><text x="35" y="75" font-family="monospace" font-size="12">Clearance Offset</text>
            <circle cx="20" cy="95" r="5" fill="#2563eb"/><text x="35" y="100" font-family="monospace" font-size="12">Bolt Spacing (S)</text>
            <text x="15" y="125" font-family="monospace" font-size="12" font-weight="bold">ALL DIMENSIONS IN MM</text>
        </g>
    </svg>
    """
    components.html(svg, height=950)
