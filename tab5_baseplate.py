import streamlit as st
import streamlit.components.v1 as components
import steel_db

def render(res_ctx, v_design):
    # --- 1. CONFIGURATION & INPUTS ---
    with st.container(border=True):
        st.markdown("##### 🛠️ Shop Drawing Control (Full-Chain Version)")
        c_m1, c_m2, c_m3 = st.columns([1, 1, 1])
        with c_m1:
            sec_list = steel_db.get_section_list()
            col_name = st.selectbox("Column Size", sec_list, index=sec_list.index(res_ctx['sec_name']) if res_ctx['sec_name'] in sec_list else 13)
            p = steel_db.get_properties(col_name)
            ch, cb, ctw, ctf = float(p['h']), float(p['b']), float(p['tw']), float(p['tf'])
        with c_m2:
            clr_x = st.number_input("Clearance X (clr x)", value=50.0)
            clr_y = st.number_input("Clearance Y (clr y)", value=60.0)
            tp = st.number_input("Plate Thk. (tp)", value=25.0)
        with c_m3:
            edge_x = st.number_input("Edge X (mm)", value=50.0)
            edge_y = st.number_input("Edge Y (mm)", value=50.0)
            bolt_d = st.selectbox("Bolt Dia.", [20, 24, 30], index=0)

    # --- 2. GEOMETRY CALC ---
    sx, sy = cb + (2 * clr_x), ch - (2 * ctf) + (2 * clr_y)
    B, N = sx + (2 * edge_x), sy + (2 * edge_y)
    
    # --- 3. SVG DRAWING ---
    cv_w, cv_h = 1200, 1150
    sc = 450 / max(N, B)  
    px, py = 450, 400 # Center the Plan

    def tick(x, y, is_v=False):
        if is_v: return f'<line x1="{x-6}" y1="{y+6}" x2="{x+6}" y2="{y-6}" stroke="black" stroke-width="1.5"/>'
        return f'<line x1="{x-6}" y1="{y+6}" x2="{x+6}" y2="{y-6}" stroke="black" stroke-width="1.5"/>'

    svg = f"""
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#ffffff" stroke="#1e293b" stroke-width="2"/>
        
        <g transform="translate(850, 780)">
            <rect width="320" height="340" fill="none" stroke="black" stroke-width="2"/>
            <text x="10" y="30" font-family="sans-serif" font-weight="bold" font-size="18">PROJECT: BASE PLATE DESIGN</text>
            <line x1="0" y1="45" x2="320" y2="45" stroke="black"/>
            <text x="10" y="120" font-family="sans-serif" font-weight="bold" font-size="14">SPECIFICATION:</text>
            <text x="10" y="150" font-family="monospace" font-size="13">● COLUMN: {col_name}</text>
            <text x="10" y="175" font-family="monospace" font-size="13">● PLATE: PL{int(tp)} x {int(B)} x {int(N)}</text>
            <text x="10" y="200" font-family="monospace" font-size="13">● BOLT: 4-M{bolt_d} (Sx={int(sx)}, Sy={int(sy)})</text>
            <rect x="0" y="260" width="320" height="80" fill="#1e293b"/>
            <text x="160" y="310" text-anchor="middle" fill="white" font-family="sans-serif" font-weight="bold" font-size="22">MASTER PLAN</text>
        </g>

        <g transform="translate({px}, {py})">
            <text x="0" y="{-N*sc/2 - 120}" text-anchor="middle" font-weight="bold" font-size="22">PLAN VIEW (SCALE 1:XX)</text>
            
            <rect x="{-B*sc/2}" y="{-N*sc/2}" width="{B*sc}" height="{N*sc}" fill="#f8fafc" stroke="black" stroke-width="3"/>
            
            <g fill="#cbd5e1" stroke="black" stroke-width="1.5">
                <rect x="{-cb/2*sc}" y="{-ch/2*sc}" width="{cb*sc}" height="{ctf*sc}"/> 
                <rect x="{-cb/2*sc}" y="{(ch/2-ctf)*sc}" width="{cb*sc}" height="{ctf*sc}"/>
                <rect x="{-ctw/2*sc}" y="{-ch/2*sc+ctf*sc}" width="{ctw*sc}" height="{(ch-2*ctf)*sc}"/>
            </g>

            <g fill="white" stroke="#2563eb" stroke-width="2.5">
                <circle cx="{-sx/2*sc}" cy="{-sy/2*sc}" r="10"/><circle cx="{sx/2*sc}" cy="{-sy/2*sc}" r="10"/>
                <circle cx="{-sx/2*sc}" cy="{sy/2*sc}" r="10"/><circle cx="{sx/2*sc}" cy="{sy/2*sc}" r="10"/>
            </g>

            <g transform="translate(0, {N*sc/2 + 60})" font-family="Arial" font-size="14" font-weight="bold">
                <line x1="{-B*sc/2}" y1="0" x2="{B*sc/2}" y2="0" stroke="black" stroke-width="1.5"/>
                {tick(-B*sc/2,0)} {tick(-sx/2*sc,0)} {tick(-cb/2*sc,0)} {tick(cb/2*sc,0)} {tick(sx/2*sc,0)} {tick(B*sc/2,0)}
                <text x="{-sx/2*sc - edge_x*sc/2}" y="22" text-anchor="middle" fill="green">{int(edge_x)}</text>
                <text x="{-cb/2*sc - clr_x*sc/2}" y="22" text-anchor="middle" fill="red">{int(clr_x)}</text>
                <text x="0" y="22" text-anchor="middle">{int(cb)}</text>
                <text x="{cb/2*sc + clr_x*sc/2}" y="22" text-anchor="middle" fill="red">{int(clr_x)}</text>
                <text x="{sx/2*sc + edge_x*sc/2}" y="22" text-anchor="middle" fill="green">{int(edge_x)}</text>
                
                <line x1="{-B*sc/2}" y1="50" x2="{B*sc/2}" y2="50" stroke="black" stroke-width="2.5"/>
                <text x="0" y="75" text-anchor="middle" font-size="18">B = {int(B)}</text>
            </g>

            <g transform="translate({-B*sc/2 - 60}, 0)" font-family="Arial" font-size="14" font-weight="bold">
                <line x1="0" y1="{-N*sc/2}" x2="0" y2="{N*sc/2}" stroke="black" stroke-width="1.5"/>
                {tick(0,-N*sc/2)} {tick(0,-sy/2*sc)} {tick(0,-ch/2*sc)} {tick(0,ch/2*sc)} {tick(0,sy/2*sc)} {tick(0,N*sc/2)}
                
                <text x="-25" y="{-sy*sc/2 - edge_y*sc/2}" text-anchor="middle" transform="rotate(-90, -25, {-sy*sc/2 - edge_y*sc/2})" fill="green">{int(edge_y)}</text>
                <text x="-25" y="{-ch*sc/2 - clr_y*sc/2 + ctf*sc/2}" text-anchor="middle" transform="rotate(-90, -25, {-ch*sc/2 - clr_y*sc/2 + ctf*sc/2})" fill="red">{int(clr_y)}</text>
                <text x="-25" y="0" text-anchor="middle" transform="rotate(-90, -25, 0)">{int(ch)}</text>
                <text x="-25" y="{ch*sc/2 + clr_y*sc/2 - ctf*sc/2}" text-anchor="middle" transform="rotate(-90, -25, {ch*sc/2 + clr_y*sc/2 - ctf*sc/2})" fill="red">{int(clr_y)}</text>
                <text x="-25" y="{sy*sc/2 + edge_y*sc/2}" text-anchor="middle" transform="rotate(-90, -25, {sy*sc/2 + edge_y*sc/2})" fill="green">{int(edge_y)}</text>

                <line x1="-50" y1="{-N*sc/2}" x2="-50" y2="{N*sc/2}" stroke="black" stroke-width="2.5"/>
                <text x="-75" y="0" text-anchor="middle" transform="rotate(-90, -75, 0)" font-size="18">N = {int(N)}</text>
            </g>
        </g>
        
        <g transform="translate(350, 950)">
            <text x="0" y="-140" text-anchor="middle" font-weight="bold" font-size="18">SECTION A-A (FRONT VIEW)</text>
            <rect x="{-B*sc/2}" y="0" width="{B*sc}" height="{tp*sc}" fill="white" stroke="black" stroke-width="2"/>
            <rect x="{-cb/2*sc}" y="-120" width="{cb*sc}" height="120" fill="#cbd5e1" stroke="black"/>
            <line x1="{-sx/2*sc}" y1="-20" x2="{-sx/2*sc}" y2="120" stroke="#2563eb" stroke-width="3" stroke-dasharray="4,2"/>
            <line x1="{sx/2*sc}" y1="-20" x2="{sx/2*sc}" y2="120" stroke="#2563eb" stroke-width="3" stroke-dasharray="4,2"/>
        </g>

    </svg>
    """
    components.html(svg, height=1150, scrolling=True)
