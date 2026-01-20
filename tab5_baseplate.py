import streamlit as st
import streamlit.components.v1 as components
import steel_db

def render(res_ctx, v_design):
    # --- 1. INPUTS ---
    with st.container(border=True):
        st.markdown("##### 📏 Drawing Control Center")
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

    # --- 2. CALCULATION ---
    sx, sy = cb + (2 * clr_x), ch - (2 * ctf) + (2 * clr_y)
    B, N = sx + (2 * edge_x), sy + (2 * edge_y)
    grout_h = 50.0

    # --- 3. SVG ENGINE (High Visibility) ---
    cv_w, cv_h = 1250, 1150
    sc = 400 / max(N, B) 
    px, py = 420, 350   # Plan
    ax, ay = 420, 900   # Section A-A
    bx, by = 950, 350   # Section B-B

    def tick(x, y, v=False): 
        if v: return f'<line x1="{x-6}" y1="{y+6}" x2="{x+6}" y2="{y-6}" stroke="black" stroke-width="2"/>'
        return f'<line x1="{x-6}" y1="{y+6}" x2="{x+6}" y2="{y-6}" stroke="black" stroke-width="2"/>'

    svg = f"""
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#ffffff" />
        
        <g transform="translate({px}, {py})">
            <text x="0" y="{-N*sc/2 - 100}" text-anchor="middle" font-weight="bold" font-size="22" text-decoration="underline">PLAN VIEW</text>
            <rect x="{-B*sc/2}" y="{-N*sc/2}" width="{B*sc}" height="{N*sc}" fill="none" stroke="black" stroke-width="3"/>
            <g fill="#e2e8f0" stroke="black" stroke-width="2">
                <rect x="{-cb/2*sc}" y="{-ch/2*sc}" width="{cb*sc}" height="{ctf*sc}"/>
                <rect x="{-cb/2*sc}" y="{(ch/2-ctf)*sc}" width="{cb*sc}" height="{ctf*sc}"/>
                <rect x="{-ctw/2*sc}" y="{-ch/2*sc+ctf*sc}" width="{ctw*sc}" height="{(ch-2*ctf)*sc}"/>
            </g>
            <g fill="white" stroke="#2563eb" stroke-width="2.5">
                <circle cx="{-sx/2*sc}" cy="{-sy/2*sc}" r="10"/><circle cx="{sx/2*sc}" cy="{-sy/2*sc}" r="10"/>
                <circle cx="{-sx/2*sc}" cy="{sy/2*sc}" r="10"/><circle cx="{sx/2*sc}" cy="{sy/2*sc}" r="10"/>
            </g>
            <g transform="translate(0, {N*sc/2 + 80})" font-family="Arial" font-size="15" font-weight="bold">
                <line x1="{-B*sc/2}" y1="0" x2="{B*sc/2}" y2="0" stroke="black" stroke-width="1.5"/>
                {tick(-B*sc/2,0)} {tick(-sx*sc/2,0)} {tick(-cb*sc/2,0)} {tick(cb*sc/2,0)} {tick(sx*sc/2,0)} {tick(B*sc/2,0)}
                <text x="{-sx/2*sc - edge_x*sc/2}" y="25" text-anchor="middle" fill="#059669">{int(edge_x)}</text>
                <text x="{-cb/2*sc - clr_x*sc/2}" y="25" text-anchor="middle" fill="#dc2626">{int(clr_x)}</text>
                <text x="0" y="25" text-anchor="middle" fill="black">{int(cb)}</text>
                <text x="{cb/2*sc + clr_x*sc/2}" y="25" text-anchor="middle" fill="#dc2626">{int(clr_x)}</text>
                <text x="{sx/2*sc + edge_x*sc/2}" y="25" text-anchor="middle" fill="#059669">{int(edge_x)}</text>
                <text x="0" y="60" text-anchor="middle" font-size="20">B = {int(B)}</text>
            </g>
        </g>

        <g transform="translate({bx}, {by})">
            <text x="0" y="{-N*sc/2 - 100}" text-anchor="middle" font-weight="bold" font-size="22" text-decoration="underline">SECTION B-B</text>
            <rect x="{-N*sc/2}" y="0" width="{N*sc}" height="{tp*sc}" fill="#f8fafc" stroke="black" stroke-width="3"/>
            
            <rect x="{-ch/2*sc}" y="-150" width="{ctf*sc}" height="150" fill="#94a3b8" stroke="black" stroke-width="2"/> 
            <rect x="{(ch/2 - ctf)*sc}" y="-150" width="{ctf*sc}" height="150" fill="#94a3b8" stroke="black" stroke-width="2"/> 
            <rect x="{-ch/2*sc + ctf*sc}" y="-150" width="{(ch - 2*ctf)*sc}" height="150" fill="#e2e8f0" stroke="black" stroke-width="1" fill-opacity="0.5"/>

            <g transform="translate({N*sc/2 + 100}, 0)" font-family="Arial" font-size="15" font-weight="bold">
                <line x1="0" y1="{-N*sc/2}" x2="0" y2="{N*sc/2}" stroke="black" stroke-width="1.5"/>
                {tick(0,-N*sc/2)} {tick(0,-sy*sc/2)} {tick(0,-(ch/2-ctf)*sc)} {tick(0,-ch/2*sc+ctf*sc)} {tick(0,(ch/2-ctf)*sc)} {tick(0,sy*sc/2)} {tick(0,N*sc/2)}
                
                <text x="30" y="{-N*sc/2 + edge_y*sc/2}" transform="rotate(90, 30, {-N*sc/2 + edge_y*sc/2})" text-anchor="middle" fill="#059669">e:{int(edge_y)}</text>
                <text x="30" y="{-sy*sc/2 + clr_y*sc/2}" transform="rotate(90, 30, {-sy*sc/2 + clr_y*sc/2})" text-anchor="middle" fill="#dc2626">clr:{int(clr_y)}</text>
                <text x="30" y="{-ch/2*sc + ctf*sc/2}" transform="rotate(90, 30, {-ch/2*sc + ctf*sc/2})" text-anchor="middle" font-size="12">tf:{int(ctf)}</text>
                <text x="30" y="0" transform="rotate(90, 30, 0)" text-anchor="middle">WEB:{int(ch-2*ctf)}</text>
                <text x="30" y="{ch/2*sc - ctf*sc/2}" transform="rotate(90, 30, {ch/2*sc - ctf*sc/2})" text-anchor="middle" font-size="12">tf:{int(ctf)}</text>
                <text x="30" y="{sy*sc/2 - clr_y*sc/2}" transform="rotate(90, 30, {sy*sc/2 - clr_y*sc/2})" text-anchor="middle" fill="#dc2626">clr:{int(clr_y)}</text>
                <text x="30" y="{N*sc/2 - edge_y*sc/2}" transform="rotate(90, 30, {N*sc/2 - edge_y*sc/2})" text-anchor="middle" fill="#059669">e:{int(edge_y)}</text>
                
                <line x1="80" y1="{-N*sc/2}" x2="80" y2="{N*sc/2}" stroke="black" stroke-width="3"/>
                <text x="110" y="0" transform="rotate(90, 110, 0)" text-anchor="middle" font-size="20">TOTAL N = {int(N)}</text>
            </g>
        </g>
    </svg>
    """
    components.html(svg, height=1150)
