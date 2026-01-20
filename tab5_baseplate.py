import streamlit as st
import streamlit.components.v1 as components
import steel_db

def render(res_ctx, v_design):
    # --- 1. INPUTS ---
    with st.container(border=True):
        st.markdown("##### 📐 Base Plate Final Layout")
        c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
        with c1:
            sec_list = steel_db.get_section_list()
            col_name = st.selectbox("Column Size", sec_list, index=sec_list.index(res_ctx['sec_name']) if res_ctx['sec_name'] in sec_list else 0)
            p = steel_db.get_properties(col_name)
            ch, cb, ctw, ctf = float(p['h']), float(p['b']), float(p['tw']), float(p['tf'])
        with c2:
            clr_x = st.number_input("Clearance X (clr x)", value=50.0)
            edge_x = st.number_input("Edge Distance X", value=50.0)
        with c3:
            clr_y = st.number_input("Clearance Y (clr y)", value=60.0)
            edge_y = st.number_input("Edge Distance Y", value=50.0)
        with c4:
            tp = st.number_input("Plate Thk. (tp)", value=25.0)
            bolt_d = st.selectbox("Anchor Bolt", [20, 24, 30])

    # --- 2. CALCULATION ---
    sx = cb + (2 * clr_x)
    sy = ch - (2 * ctf) + (2 * clr_y)
    B, N = sx + (2 * edge_x), sy + (2 * edge_y)
    grout_h = 50.0

    # --- 3. SVG ENGINE ---
    cv_w, cv_h = 1200, 1100
    sc = 400 / max(N, B) 
    px, py = 400, 320   # Plan
    ax, ay = 400, 850   # Section A-A
    bx, by = 950, 320   # Section B-B

    def tick(x, y): return f'<line x1="{x-4}" y1="{y+4}" x2="{x+4}" y2="{y-4}" stroke="black" stroke-width="1.2"/>'

    svg = f"""
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#ffffff" />
        
        <g transform="translate({px}, {py})">
            <text x="0" y="{-N*sc/2 - 80}" text-anchor="middle" font-weight="bold" font-size="18">PLAN VIEW (TOP)</text>
            <rect x="{-B*sc/2}" y="{-N*sc/2}" width="{B*sc}" height="{N*sc}" fill="#fcfcfc" stroke="black" stroke-width="2.5"/>
            <g fill="#e2e8f0" stroke="black" stroke-width="1.5">
                <rect x="{-cb/2*sc}" y="{-ch/2*sc}" width="{cb*sc}" height="{ctf*sc}"/>
                <rect x="{-cb/2*sc}" y="{(ch/2-ctf)*sc}" width="{cb*sc}" height="{ctf*sc}"/>
                <rect x="{-ctw/2*sc}" y="{-ch/2*sc+ctf*sc}" width="{ctw*sc}" height="{(ch-2*ctf)*sc}"/>
            </g>
            <g fill="white" stroke="#2563eb" stroke-width="2">
                <circle cx="{-sx/2*sc}" cy="{-sy/2*sc}" r="8"/><circle cx="{sx/2*sc}" cy="{-sy/2*sc}" r="8"/>
                <circle cx="{-sx/2*sc}" cy="{sy/2*sc}" r="8"/><circle cx="{sx/2*sc}" cy="{sy/2*sc}" r="8"/>
            </g>

            <g transform="translate(0, {N*sc/2 + 50})" font-family="monospace" font-size="11">
                <line x1="{-B*sc/2}" y1="0" x2="{B*sc/2}" y2="0" stroke="black"/>
                {tick(-B*sc/2,0)} {tick(-sx*sc/2,0)} {tick(-cb*sc/2,0)} {tick(cb*sc/2,0)} {tick(sx*sc/2,0)} {tick(B*sc/2,0)}
                <text x="{-sx/2*sc - edge_x*sc/2}" y="15" text-anchor="middle" fill="green">{int(edge_x)}</text>
                <text x="{-cb/2*sc - clr_x*sc/2}" y="15" text-anchor="middle" fill="red">{int(clr_x)}</text>
                <text x="0" y="15" text-anchor="middle" font-weight="bold">{int(cb)}</text>
                <text x="{cb/2*sc + clr_x*sc/2}" y="15" text-anchor="middle" fill="red">{int(clr_x)}</text>
                <text x="{sx/2*sc + edge_x*sc/2}" y="15" text-anchor="middle" fill="green">{int(edge_x)}</text>
                <text x="0" y="45" text-anchor="middle" font-size="14" font-weight="bold">B = {int(B)}</text>
            </g>
        </g>

        <g transform="translate({ax}, {ay})">
            <text x="0" y="-140" text-anchor="middle" font-weight="bold" font-size="16">SECTION A-A (FRONT)</text>
            <rect x="{-B*sc/2}" y="{tp*sc}" width="{B*sc}" height="{grout_h*sc}" fill="#f1f5f9" stroke="black" stroke-dasharray="2,2"/>
            <rect x="{-B*sc/2}" y="0" width="{B*sc}" height="{tp*sc}" fill="#cbd5e1" stroke="black" stroke-width="2"/>
            <rect x="{-cb/2*sc}" y="-120" width="{cb*sc}" height="120" fill="#e2e8f0" stroke="black"/>
            <line x1="{-sx/2*sc}" y1="-15" x2="{-sx/2*sc}" y2="150" stroke="#2563eb" stroke-width="2" stroke-dasharray="8,4"/>
            <line x1="{sx/2*sc}" y1="-15" x2="{sx/2*sc}" y2="150" stroke="#2563eb" stroke-width="2" stroke-dasharray="8,4"/>
        </g>

        <g transform="translate({bx}, {by})">
            <text x="0" y="{-N*sc/2 - 80}" text-anchor="middle" font-weight="bold" font-size="16">SECTION B-B (SIDE)</text>
            <rect x="{-N*sc/2}" y="{tp*sc}" width="{N*sc}" height="{grout_h*sc}" fill="#f1f5f9" stroke="black" stroke-dasharray="2,2"/>
            <rect x="{-N*sc/2}" y="0" width="{N*sc}" height="{tp*sc}" fill="#cbd5e1" stroke="black" stroke-width="2"/>
            
            <rect x="{-ch/2*sc}" y="-120" width="{ctf*sc}" height="120" fill="#94a3b8" stroke="black"/> 
            <rect x="{(ch/2 - ctf)*sc}" y="-120" width="{ctf*sc}" height="120" fill="#94a3b8" stroke="black"/> 
            <rect x="{-ch/2*sc + ctf*sc}" y="-120" width="{(ch - 2*ctf)*sc}" height="120" fill="#cbd5e1" stroke="black" fill-opacity="0.4"/>

            <g transform="translate({N*sc/2 + 50}, 0)" font-family="monospace" font-size="11">
                <line x1="0" y1="{-N*sc/2}" x2="0" y2="{N*sc/2}" stroke="black"/>
                {tick(0,-N*sc/2)} {tick(0,-sy*sc/2)} {tick(0,-(ch/2-ctf)*sc)} {tick(0,-ch/2*sc+ctf*sc)} {tick(0,(ch/2-ctf)*sc)} {tick(0,sy*sc/2)} {tick(0,N*sc/2)}
                
                <text x="15" y="{-N*sc/2 + edge_y*sc/2}" transform="rotate(90, 15, {-N*sc/2 + edge_y*sc/2})" text-anchor="middle" fill="green">{int(edge_y)}</text>
                <text x="15" y="{-sy*sc/2 + clr_y*sc/2}" transform="rotate(90, 15, {-sy*sc/2 + clr_y*sc/2})" text-anchor="middle" fill="red">{int(clr_y)}</text>
                <text x="15" y="{-ch/2*sc + ctf*sc/2}" transform="rotate(90, 15, {-ch/2*sc + ctf*sc/2})" text-anchor="middle" font-size="9">FLG {int(ctf)}</text>
                <text x="15" y="0" transform="rotate(90, 15, 0)" text-anchor="middle" font-weight="bold">WEB {int(ch-2*ctf)}</text>
                <text x="15" y="{ch/2*sc - ctf*sc/2}" transform="rotate(90, 15, {ch/2*sc - ctf*sc/2})" text-anchor="middle" font-size="9">FLG {int(ctf)}</text>
                <text x="15" y="{sy*sc/2 - clr_y*sc/2}" transform="rotate(90, 15, {sy*sc/2 - clr_y*sc/2})" text-anchor="middle" fill="red">{int(clr_y)}</text>
                <text x="15" y="{N*sc/2 - edge_y*sc/2}" transform="rotate(90, 15, {N*sc/2 - edge_y*sc/2})" text-anchor="middle" fill="green">{int(edge_y)}</text>
                
                <line x1="55" y1="{-N*sc/2}" x2="55" y2="{N*sc/2}" stroke="black" stroke-width="2"/>
                <text x="70" y="0" transform="rotate(90, 70, 0)" text-anchor="middle" font-size="14" font-weight="bold">LENGTH N = {int(N)}</text>
            </g>
        </g>
    </svg>
    """
    components.html(svg, height=1050)
