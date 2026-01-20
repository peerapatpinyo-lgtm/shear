import streamlit as st
import streamlit.components.v1 as components
import steel_db

def render(res_ctx, v_design):
    # --- 1. CONFIGURATION & INPUTS ---
    with st.container(border=True):
        st.markdown("##### 📐 Design Control & Shop Drawing")
        c_m1, c_m2, c_m3 = st.columns([1, 1, 1])
        with c_m1:
            sec_list = steel_db.get_section_list()
            col_name = st.selectbox("Column Size", sec_list, index=sec_list.index(res_ctx['sec_name']) if res_ctx['sec_name'] in sec_list else 13)
            p = steel_db.get_properties(col_name)
            ch, cb, ctw, ctf = float(p['h']), float(p['b']), float(p['tw']), float(p['tf'])
        with c_m2:
            clr_x = st.number_input("Clearance X (mm)", value=50.0)
            clr_y = st.number_input("Clearance Y (mm)", value=60.0)
            tp = st.number_input("Plate Thk. (mm)", value=25.0)
        with c_m3:
            edge_x = st.number_input("Edge X (mm)", value=50.0)
            edge_y = st.number_input("Edge Y (mm)", value=50.0)
            bolt_d = st.selectbox("Bolt Dia.", [20, 24, 30], index=0)

    # --- 2. GEOMETRY CALC ---
    sx, sy = cb + (2 * clr_x), ch - (2 * ctf) + (2 * clr_y)
    B, N = sx + (2 * edge_x), sy + (2 * edge_y)
    grout_h = 50.0
    
    # --- 3. SVG DRAWING ---
    cv_w, cv_h = 1200, 1200
    sc = 450 / max(N, B)  
    px, py = 450, 350 # Plan
    ax, ay = 450, 900 # Section A-A

    def tick(x, y): return f'<line x1="{x-5}" y1="{y+5}" x2="{x+5}" y2="{y-5}" stroke="black" stroke-width="1.2"/>'

    svg = f"""
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#ffffff" stroke="#1e293b" stroke-width="2"/>
        
        <g transform="translate(850, 800)">
            <rect width="320" height="340" fill="none" stroke="black" stroke-width="2"/>
            <text x="10" y="30" font-family="sans-serif" font-weight="bold" font-size="18">PROJECT: BASE PLATE DESIGN</text>
            <line x1="0" y1="45" x2="320" y2="45" stroke="black"/>
            <text x="10" y="115" font-family="sans-serif" font-weight="bold" font-size="14">MATERIAL SPEC:</text>
            <text x="10" y="145" font-family="monospace" font-size="13">● COLUMN: {col_name}</text>
            <text x="10" y="170" font-family="monospace" font-size="13">● PLATE: PL{int(tp)}x{int(B)}x{int(N)}</text>
            <text x="10" y="195" font-family="monospace" font-size="13">● BOLT: 4-M{bolt_d} GR 8.8</text>
            <rect x="0" y="260" width="320" height="80" fill="#1e293b"/>
            <text x="160" y="310" text-anchor="middle" fill="white" font-family="sans-serif" font-weight="bold" font-size="22">CONSTRUCTION</text>
        </g>

        <g transform="translate({px}, {py})">
            <text x="0" y="{-N*sc/2 - 80}" text-anchor="middle" font-weight="bold" font-size="20">PLAN VIEW (TOP)</text>
            <rect x="{-B*sc/2}" y="{-N*sc/2}" width="{B*sc}" height="{N*sc}" fill="#f8fafc" stroke="black" stroke-width="2.5"/>
            <g fill="#cbd5e1" stroke="black" stroke-width="1.5">
                <rect x="{-cb/2*sc}" y="{-ch/2*sc}" width="{cb*sc}" height="{ctf*sc}"/> 
                <rect x="{-cb/2*sc}" y="{(ch/2-ctf)*sc}" width="{cb*sc}" height="{ctf*sc}"/>
                <rect x="{-ctw/2*sc}" y="{-ch/2*sc+ctf*sc}" width="{ctw*sc}" height="{(ch-2*ctf)*sc}"/>
            </g>
            <circle cx="{-sx/2*sc}" cy="{-sy/2*sc}" r="9" fill="white" stroke="#2563eb" stroke-width="2.5"/>
            <circle cx="{sx/2*sc}"  cy="{-sy/2*sc}" r="9" fill="white" stroke="#2563eb" stroke-width="2.5"/>
            <circle cx="{-sx/2*sc}" cy="{sy/2*sc}"  r="9" fill="white" stroke="#2563eb" stroke-width="2.5"/>
            <circle cx="{sx/2*sc}"  cy="{sy/2*sc}"  r="9" fill="white" stroke="#2563eb" stroke-width="2.5"/>
            
            <g transform="translate(0, {N*sc/2 + 50})" font-family="Arial" font-size="13" font-weight="bold">
                <line x1="{-B*sc/2}" y1="0" x2="{B*sc/2}" y2="0" stroke="black"/>
                {tick(-B*sc/2,0)} {tick(-sx/2*sc,0)} {tick(-cb/2*sc,0)} {tick(cb/2*sc,0)} {tick(sx/2*sc,0)} {tick(B*sc/2,0)}
                <text x="{-sx/2*sc - edge_x*sc/2}" y="18" text-anchor="middle" fill="green">{int(edge_x)}</text>
                <text x="{-cb/2*sc - clr_x*sc/2}" y="18" text-anchor="middle" fill="red">{int(clr_x)}</text>
                <text x="0" y="18" text-anchor="middle">{int(cb)}</text>
                <text x="{cb/2*sc + clr_x*sc/2}" y="18" text-anchor="middle" fill="red">{int(clr_x)}</text>
                <text x="{sx/2*sc + edge_x*sc/2}" y="18" text-anchor="middle" fill="green">{int(edge_x)}</text>
            </g>
        </g>

        <g transform="translate({ax}, {ay})">
            <text x="0" y="-180" text-anchor="middle" font-weight="bold" font-size="20">SECTION A-A (FRONT VIEW)</text>
            
            <rect x="{-B*sc/2}" y="{tp*sc}" width="{B*sc}" height="{grout_h*sc}" fill="#f1f5f9" stroke="black"/>
            <rect x="{-B*sc/2}" y="0" width="{B*sc}" height="{tp*sc}" fill="white" stroke="black" stroke-width="2.5"/>
            
            <rect x="{-cb/2*sc}" y="-150" width="{cb*sc}" height="150" fill="#cbd5e1" stroke="black"/>
            
            <line x1="{-sx/2*sc}" y1="-30" x2="{-sx/2*sc}" y2="180" stroke="#2563eb" stroke-width="3"/>
            <line x1="{sx/2*sc}" y1="-30" x2="{sx/2*sc}" y2="180" stroke="#2563eb" stroke-width="3"/>

            <g transform="translate(0, 130)" font-family="Arial" font-size="13" font-weight="bold">
                <line x1="{-B*sc/2}" y1="0" x2="{B*sc/2}" y2="0" stroke="black"/>
                {tick(-B*sc/2,0)} {tick(-sx/2*sc,0)} {tick(-cb/2*sc,0)} {tick(cb/2*sc,0)} {tick(sx/2*sc,0)} {tick(B*sc/2,0)}
                <text x="{-sx/2*sc - edge_x*sc/2}" y="18" text-anchor="middle" fill="green">e:{int(edge_x)}</text>
                <text x="{-cb/2*sc - clr_x*sc/2}" y="18" text-anchor="middle" fill="red">c:{int(clr_x)}</text>
                <text x="0" y="18" text-anchor="middle">COL:{int(cb)}</text>
                <text x="{cb/2*sc + clr_x*sc/2}" y="18" text-anchor="middle" fill="red">c:{int(clr_x)}</text>
                <text x="{sx/2*sc + edge_x*sc/2}" y="18" text-anchor="middle" fill="green">e:{int(edge_x)}</text>
                
                <line x1="{-B*sc/2}" y1="45" x2="{B*sc/2}" y2="45" stroke="black" stroke-width="2"/>
                <text x="0" y="65" text-anchor="middle" font-size="16">TOTAL B = {int(B)}</text>
            </g>

            <g transform="translate({-B*sc/2 - 40}, 0)" font-family="Arial" font-size="12" font-weight="bold">
                <line x1="0" y1="0" x2="0" y2="{tp*sc}" stroke="black"/>
                {tick(0,0)} {tick(0,tp*sc)}
                <text x="-15" y="{tp*sc/2}" text-anchor="middle" transform="rotate(-90, -15, {tp*sc/2})">tp:{int(tp)}</text>
            </g>

            <path d="M {-cb/4*sc} -100 L -250 -100" fill="none" stroke="red" marker-end="url(#arrow)"/>
            <text x="-255" y="-95" text-anchor="end" fill="red" font-size="14" font-weight="bold">COLUMN: {col_name}</text>
        </g>

        <defs>
            <marker id="arrow" markerWidth="10" markerHeight="10" refX="0" refY="3" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0 L0,6 L9,3 z" fill="red" />
            </marker>
        </defs>
    </svg>
    """
    components.html(svg, height=1200, scrolling=True)
