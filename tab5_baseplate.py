import streamlit as st
import streamlit.components.v1 as components
import steel_db

def render(res_ctx, v_design):
    # --- 1. INPUTS ---
    with st.container(border=True):
        st.markdown("##### 📐 High-Precision Dimension Control")
        c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])
        with c1:
            sec_list = steel_db.get_section_list()
            col_name = st.selectbox("Column Size", sec_list, index=sec_list.index(res_ctx['sec_name']) if res_ctx['sec_name'] in sec_list else 0)
            p = steel_db.get_properties(col_name)
            ch, cb, ctw, ctf = float(p['h']), float(p['b']), float(p['tw']), float(p['tf'])
        with c2:
            clr_x = st.number_input("Clearance X", value=50.0)
            edge_x = st.number_input("Edge X", value=50.0)
        with c3:
            clr_y = st.number_input("Clearance Y", value=60.0)
            edge_y = st.number_input("Edge Y", value=50.0)
        with c4:
            tp = st.number_input("Plate Thk.", value=25.0)
            bolt_d = st.selectbox("Bolt Size", [20, 24, 30])

    # --- 2. COORDINATE CALC ---
    sx, sy = cb + (2 * clr_x), ch - (2 * ctf) + (2 * clr_y)
    B, N = sx + (2 * edge_x), sy + (2 * edge_y)
    
    # --- 3. SVG DRAWING ---
    cv_w, cv_h = 1300, 1100
    sc = 380 / max(N, B) 
    px, py = 450, 320   # Plan
    bx, by = 1000, 320  # Section B-B

    def tick(x, y): return f'<line x1="{x-6}" y1="{y+6}" x2="{x+6}" y2="{y-6}" stroke="black" stroke-width="2"/>'

    svg = f"""
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#ffffff" />
        
        <g transform="translate({px}, {py})">
            <text x="0" y="{-N*sc/2 - 80}" text-anchor="middle" font-weight="bold" font-size="22">PLAN VIEW</text>
            <rect x="{-B*sc/2}" y="{-N*sc/2}" width="{B*sc}" height="{N*sc}" fill="none" stroke="black" stroke-width="3"/>
            
            <g fill="#e2e8f0" stroke="black" stroke-width="2">
                <rect x="{-cb/2*sc}" y="{-ch/2*sc}" width="{cb*sc}" height="{ctf*sc}"/>
                <rect x="{-cb/2*sc}" y="{(ch/2-ctf)*sc}" width="{cb*sc}" height="{ctf*sc}"/>
                <rect x="{-ctw/2*sc}" y="{-ch/2*sc+ctf*sc}" width="{ctw*sc}" height="{(ch-2*ctf)*sc}"/>
            </g>

            <g fill="white" stroke="#2563eb" stroke-width="2.5">
                <circle cx="{-sx/2*sc}" cy="{-sy/2*sc}" r="9"/><circle cx="{sx/2*sc}" cy="{-sy/2*sc}" r="9"/>
                <circle cx="{-sx/2*sc}" cy="{sy/2*sc}" r="9"/><circle cx="{sx/2*sc}" cy="{sy/2*sc}" r="9"/>
            </g>

            <g transform="translate(0, {N*sc/2 + 80})" font-family="Arial" font-size="16" font-weight="bold">
                <line x1="{-B*sc/2}" y1="0" x2="{B*sc/2}" y2="0" stroke="black" stroke-width="2"/>
                {tick(-B*sc/2,0)} {tick(-sx*sc/2,0)} {tick(-cb/2*sc,0)} {tick(-ctw/2*sc,0)} {tick(ctw/2*sc,0)} {tick(cb/2*sc,0)} {tick(sx*sc/2,0)} {tick(B*sc/2,0)}
                
                <text x="{-sx/2*sc - edge_x*sc/2}" y="25" text-anchor="middle" fill="green">{int(edge_x)}</text>
                <text x="{-cb/2*sc - clr_x*sc/2}" y="25" text-anchor="middle" fill="red">{int(clr_x)}</text>
                <text x="{-cb/4*sc}" y="25" text-anchor="middle" font-size="12">FLG</text>
                <text x="0" y="25" text-anchor="middle" font-size="13">WEB:{int(ctw)}</text>
                <text x="{cb/4*sc}" y="25" text-anchor="middle" font-size="12">FLG</text>
                <text x="{cb/2*sc + clr_x*sc/2}" y="25" text-anchor="middle" fill="red">{int(clr_x)}</text>
                <text x="{sx/2*sc + edge_x*sc/2}" y="25" text-anchor="middle" fill="green">{int(edge_x)}</text>
                
                <line x1="{-B*sc/2}" y1="60" x2="{B*sc/2}" y2="60" stroke="black" stroke-width="3"/>
                <text x="0" y="85" text-anchor="middle" font-size="22">B = {int(B)}</text>
            </g>
        </g>

        <g transform="translate({bx}, {by})">
            <text x="0" y="{-N*sc/2 - 80}" text-anchor="middle" font-weight="bold" font-size="22">SECTION B-B (SIDE)</text>
            <rect x="{-N*sc/2}" y="0" width="{N*sc}" height="{tp*sc}" fill="#cbd5e1" stroke="black" stroke-width="3"/>
            
            <rect x="{-ch/2*sc}" y="-150" width="{ctf*sc}" height="150" fill="#94a3b8" stroke="black" stroke-width="2"/> 
            <rect x="{(ch/2 - ctf)*sc}" y="-150" width="{ctf*sc}" height="150" fill="#94a3b8" stroke="black" stroke-width="2"/> 
            <rect x="{-ch/2*sc + ctf*sc}" y="-150" width="{(ch - 2*ctf)*sc}" height="150" fill="#f1f5f9" stroke="black" stroke-width="1"/>

            <g transform="translate({N*sc/2 + 100}, 0)" font-family="Arial" font-size="15" font-weight="bold">
                <line x1="0" y1="{-N*sc/2}" x2="0" y2="{N*sc/2}" stroke="black" stroke-width="2"/>
                {tick(0,-N*sc/2)} {tick(0,-sy*sc/2)} {tick(0,-ch/2*sc)} {tick(0,-(ch/2-ctf)*sc)} 
                {tick(0,(ch/2-ctf)*sc)} {tick(0,ch/2*sc)} {tick(0,sy*sc/2)} {tick(0,N*sc/2)}
                
                <text x="35" y="{-N*sc/2 + edge_y*sc/2}" transform="rotate(90, 35, {-N*sc/2 + edge_y*sc/2})" text-anchor="middle" fill="green">e:{int(edge_y)}</text>
                <text x="35" y="{-sy*sc/2 + clr_y*sc/2}" transform="rotate(90, 35, {-sy*sc/2 + clr_y*sc/2})" text-anchor="middle" fill="red">clr:{int(clr_y)}</text>
                <text x="35" y="{-ch/2*sc + ctf/2*sc}" transform="rotate(90, 35, {-ch/2*sc + ctf/2*sc})" text-anchor="middle" font-size="12">tf:{int(ctf)}</text>
                <text x="35" y="0" transform="rotate(90, 35, 0)" text-anchor="middle" fill="#2563eb">WEB:{int(ch-2*ctf)}</text>
                <text x="35" y="{ch/2*sc - ctf/2*sc}" transform="rotate(90, 35, {ch/2*sc - ctf/2*sc})" text-anchor="middle" font-size="12">tf:{int(ctf)}</text>
                <text x="35" y="{sy*sc/2 - clr_y*sc/2}" transform="rotate(90, 35, {sy*sc/2 - clr_y*sc/2})" text-anchor="middle" fill="red">clr:{int(clr_y)}</text>
                <text x="35" y="{N*sc/2 - edge_y*sc/2}" transform="rotate(90, 35, {N*sc/2 - edge_y*sc/2})" text-anchor="middle" fill="green">e:{int(edge_y)}</text>
                
                <line x1="90" y1="{-N*sc/2}" x2="90" y2="{N*sc/2}" stroke="black" stroke-width="4"/>
                <text x="125" y="0" transform="rotate(90, 125, 0)" text-anchor="middle" font-size="24">TOTAL N = {int(N)}</text>
            </g>
        </g>
    </svg>
    """
    components.html(svg, height=1150)
