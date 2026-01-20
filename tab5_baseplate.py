import streamlit as st
import streamlit.components.v1 as components
import math
import steel_db

def render(res_ctx, v_design):
    # --- 1. INPUTS ---
    with st.container(border=True):
        c_main1, c_main2 = st.columns([1, 1.5])
        with c_main1:
            st.markdown("##### 📦 Column Section")
            sec_list = steel_db.get_section_list()
            col_name = st.selectbox("Select Column Size", sec_list, index=sec_list.index(res_ctx['sec_name']) if res_ctx['sec_name'] in sec_list else 13)
            props = steel_db.get_properties(col_name)
            ch, cb, ctw, ctf = float(props['h']), float(props['b']), float(props['tw']), float(props['tf'])
        with c_main2:
            st.markdown("##### 📐 Geometry & Offsets")
            c1, c2, c3 = st.columns(3)
            clr_x = c1.number_input("Clearance X (mm)", value=50.0)
            clr_y = c2.number_input("Clearance Y (mm)", value=60.0)
            tp = c3.number_input("Plate Thickness (mm)", value=25.0)
            c4, c5, c6 = st.columns(3)
            edge_x = c4.number_input("Edge Dist X (mm)", value=50.0)
            edge_y = c5.number_input("Edge Dist Y (mm)", value=50.0)
            bolt_d = c6.selectbox("Bolt Size", [20, 24, 30, 36], index=0)

    # --- 2. CALCULATIONS ---
    sx = cb + (2 * clr_x)
    sy = ch - (2 * ctf) + (2 * clr_y)
    B = sx + (2 * edge_x)
    N = sy + (2 * edge_y)
    hole_d = bolt_d + 6 # Oversized hole standard
    grout_thk = 50.0 # Standard Grout
    anchor_len = 400.0 # Visual representation length

    # --- 3. SVG CONFIG ---
    cv_w, cv_h = 1000, 1600 # Increased height for 3 views
    cx = cv_w / 2
    cy_plan = 450
    cy_front = 1000
    cy_side = 1350
    
    sc = 520 / max(N, B) # Main Scale Factor

    def draw_tick(x, y, vertical=False):
        if vertical: return f'<line x1="{x-5}" y1="{y+5}" x2="{x+5}" y2="{y-5}" stroke="black" stroke-width="1.5"/>'
        return f'<line x1="{x-5}" y1="{y+5}" x2="{x+5}" y2="{y-5}" stroke="black" stroke-width="1.5"/>'

    # Hatching Patterns
    patterns = """
    <defs>
        <pattern id="concrete" patternUnits="userSpaceOnUse" width="20" height="20">
            <image href="https://www.transparenttextures.com/patterns/concrete-wall.png" x="0" y="0" width="20" height="20" opacity="0.3"/>
        </pattern>
         <pattern id="grout" patternUnits="userSpaceOnUse" width="5" height="5" patternTransform="rotate(45)">
            <line x1="0" y1="0" x2="0" y2="5" stroke="#a0aec0" stroke-width="1"/>
        </pattern>
    </defs>
    """

    svg = f"""
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#ffffff" />
        {patterns}
        <text x="40" y="45" font-family="sans-serif" font-size="24" font-weight="bold">COMPLETE BASE PLATE DETAILS (BP-01)</text>
        <line x1="40" y1="55" x2="600" y2="55" stroke="black" stroke-width="3"/>

        <g transform="translate({cx}, {cy_plan})">
            <text x="{-B*sc/2}" y="{-N*sc/2 - 40}" font-weight="bold" font-size="16">PLAN VIEW</text>
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
                <text x="0" y="15" text-anchor="middle" font-weight="bold">{int(cb)}</text>
                <text x="{sx*sc/2 - (clr_x*sc/2)}" y="15" text-anchor="middle" fill="red">{int(clr_x)}</text>
                <text x="{B*sc/2 - (edge_x*sc/2)}" y="15" text-anchor="middle" fill="green">{int(edge_x)}</text>
                <line x1="{-B*sc/2}" y1="45" x2="{B*sc/2}" y2="45" stroke="black" stroke-width="2"/>
                <text x="0" y="60" text-anchor="middle" font-size="14" font-weight="bold">B = {int(B)}</text>
            </g>
            <g transform="translate({B*sc/2 + 40}, 0)" font-family="monospace" font-size="12">
                <line x1="0" y1="{-N*sc/2}" x2="0" y2="{N*sc/2}" stroke="black" stroke-width="2"/>
                <text x="15" y="0" transform="rotate(90, 15, 0)" text-anchor="middle" font-size="14" font-weight="bold">N = {int(N)}</text>
                <line x1="-20" y1="{-sy*sc/2}" x2="-20" y2="{sy*sc/2}" stroke="#2563eb"/>
                <text x="-30" y="0" transform="rotate(90, -30, 0)" text-anchor="middle" fill="#2563eb">Sy={int(sy)}</text>
            </g>
            <g stroke="red" stroke-width="2" stroke-dasharray="10,5">
                <line x1="{-B*sc/2-50}" y1="0" x2="{B*sc/2+50}" y2="0"/><text x="{B*sc/2+60}" y="5" fill="red">X</text>
                <line x1="0" y1="{-N*sc/2-50}" x2="0" y2="{N*sc/2+50}"/><text x="0" y="{N*sc/2+70}" fill="red">Y</text>
            </g>
        </g>

        <g transform="translate({cx}, {cy_front})">
             <text x="{-B*sc/2}" y="-100" font-weight="bold" font-size="16">ELEVATION X-X</text>
             <rect x="{-B*sc/2 - 100}" y="{tp*sc + grout_thk*sc}" width="{B*sc + 200}" height="100" fill="url(#concrete)"/>
             <rect x="{-B*sc/2}" y="{tp*sc}" width="{B*sc}" height="{grout_thk*sc}" fill="url(#grout)" stroke="black"/>
             <rect x="{-B*sc/2}" y="0" width="{B*sc}" height="{tp*sc}" fill="#fcfcfc" stroke="black" stroke-width="2"/>
             <rect x="{-cb*sc/2}" y="{-200}" width="{cb*sc}" height="200" fill="#e2e8f0" stroke="#1e293b" stroke-width="1.5"/>
             <line x1="{-ctw*sc/2}" y1="{-200}" x2="{-ctw*sc/2}" y2="0" stroke="#1e293b" stroke-dasharray="5,5"/>
             <line x1="{ctw*sc/2}" y1="{-200}" x2="{ctw*sc/2}" y2="0" stroke="#1e293b" stroke-dasharray="5,5"/>
             <g stroke="#2563eb" stroke-width="3">
                 <line x1="{-sx*sc/2}" y1="-30" x2="{-sx*sc/2}" y2="{tp*sc + anchor_len*sc}"/>
                 <line x1="{sx*sc/2}" y1="-30" x2="{sx*sc/2}" y2="{tp*sc + anchor_len*sc}"/>
             </g>
             <g transform="translate({B*sc/2 + 40}, 0)" font-family="monospace" font-size="12">
                <line x1="0" y1="0" x2="0" y2="{tp*sc + grout_thk*sc}" stroke="black" stroke-width="1"/>
                {draw_tick(0, 0, True)} {draw_tick(0, tp*sc, True)} {draw_tick(0, tp*sc + grout_thk*sc, True)}
                <text x="20" y="{tp*sc/2}" text-anchor="middle" alignment-baseline="middle">tp={int(tp)}</text>
                <text x="20" y="{tp*sc + grout_thk*sc/2}" text-anchor="middle" alignment-baseline="middle">Grout={int(grout_thk)}</text>
             </g>
        </g>

        <g transform="translate({cx}, {cy_side})">
             <text x="{-B*sc/2}" y="-100" font-weight="bold" font-size="16">ELEVATION Y-Y</text>
             <rect x="{-N*sc/2 - 50}" y="{tp*sc + grout_thk*sc}" width="{N*sc + 100}" height="100" fill="url(#concrete)"/>
             <rect x="{-N*sc/2}" y="{tp*sc}" width="{N*sc}" height="{grout_thk*sc}" fill="url(#grout)" stroke="black"/>
             <rect x="{-N*sc/2}" y="0" width="{N*sc}" height="{tp*sc}" fill="#fcfcfc" stroke="black" stroke-width="2"/>
             <rect x="{-ctw*sc/2}" y="{-200}" width="{ctw*sc}" height="200" fill="#e2e8f0" stroke="#1e293b"/>
             <line x1="{-ch*sc/2}" y1="{-200}" x2="{-ch*sc/2}" y2="0" stroke="#1e293b" stroke-width="2"/>
             <line x1="{ch*sc/2}" y1="{-200}" x2="{ch*sc/2}" y2="0" stroke="#1e293b" stroke-width="2"/>
             <g stroke="#2563eb" stroke-width="3">
                 <line x1="{-sy*sc/2}" y1="-30" x2="{-sy*sc/2}" y2="{tp*sc + anchor_len*sc}"/>
                 <line x1="{sy*sc/2}" y1="-30" x2="{sy*sc/2}" y2="{tp*sc + anchor_len*sc}"/>
             </g>
             <g transform="translate(0, {tp*sc + grout_thk*sc + 30})" font-family="monospace" font-size="12">
                <line x1="{-N*sc/2}" y1="0" x2="{N*sc/2}" y2="0" stroke="black" stroke-width="2"/>
                <text x="0" y="15" text-anchor="middle" font-weight="bold">N = {int(N)}</text>
                <line x1="{-sy*sc/2}" y1="-20" x2="{sy*sc/2}" y2="-20" stroke="#2563eb"/>
                <text x="0" y="-25" text-anchor="middle" fill="#2563eb">Sy = {int(sy)}</text>
             </g>
        </g>

        <g transform="translate(40, {cv_h - 150})">
            <rect width="200" height="120" fill="white" stroke="black"/>
            <text x="10" y="20" font-weight="bold">LEGEND</text>
            <rect x="10" y="35" width="20" height="20" fill="url(#concrete)" stroke="black"/><text x="40" y="50">Concrete</text>
            <rect x="10" y="65" width="20" height="20" fill="url(#grout)" stroke="black"/><text x="40" y="80">Non-shrink Grout</text>
            <line x1="10" y1="100" x2="30" y2="100" stroke="#2563eb" stroke-width="3"/><text x="40" y="105">Anchor Bolt (J-Type)</text>
        </g>
    </svg>
    """
    components.html(svg, height=cv_h + 50, scrolling=True)
