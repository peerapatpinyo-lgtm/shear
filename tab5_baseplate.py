import streamlit as st
import streamlit.components.v1 as components
import steel_db

def render(res_ctx, v_design):
    # --- 1. CONFIGURATION & INPUTS ---
    with st.container(border=True):
        st.markdown("##### 🛠️ Shop Drawing Control (Final Master)")
        c_m1, c_m2, c_m3 = st.columns([1, 1, 1])
        with c_m1:
            sec_list = steel_db.get_section_list()
            col_name = st.selectbox("Column Size", sec_list, index=sec_list.index(res_ctx['sec_name']) if res_ctx['sec_name'] in sec_list else 13)
            props = steel_db.get_properties(col_name)
            ch, cb, ctw, ctf = float(props['h']), float(props['b']), float(props['tw']), float(props['tf'])
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
    
    # --- 3. SVG DRAWING ENGINE ---
    cv_w, cv_h = 1200, 1150
    sc = 450 / max(N, B)  
    
    plan_x, plan_y = 380, 350
    front_x, front_y = 380, 880  
    side_x, side_y = 920, 350   

    def get_tick(x, y): return f'<line x1="{x-5}" y1="{y+5}" x2="{x+5}" y2="{y-5}" stroke="black" stroke-width="1.2"/>'

    svg = f"""
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#ffffff" stroke="#1e293b" stroke-width="2"/>
        
        <g transform="translate(850, 750)">
            <rect width="320" height="340" fill="none" stroke="black" stroke-width="2"/>
            <text x="10" y="30" font-family="sans-serif" font-weight="bold" font-size="18">PROJECT: BASE PLATE DESIGN</text>
            <line x1="0" y1="45" x2="320" y2="45" stroke="black"/>
            <text x="10" y="70" font-family="sans-serif" font-size="14">DRAWING: CONSTRUCTION DETAIL</text>
            <line x1="0" y1="85" x2="320" y2="85" stroke="black"/>
            <text x="10" y="115" font-family="sans-serif" font-weight="bold" font-size="14">MATERIAL SPECIFICATION:</text>
            <text x="10" y="145" font-family="monospace" font-size="13" fill="#1e40af">● COLUMN: {col_name}</text>
            <text x="10" y="170" font-family="monospace" font-size="13" fill="#1e40af">● PLATE: PL{int(tp)} x {int(B)} x {int(N)} mm</text>
            <text x="10" y="195" font-family="monospace" font-size="13" fill="#1e40af">● BOLT: 4-M{bolt_d} (Sx={int(sx)}, Sy={int(sy)})</text>
            <text x="10" y="220" font-family="monospace" font-size="13" fill="#1e40af">● GROUT: NON-SHRINK 50mm</text>
            <rect x="0" y="260" width="320" height="80" fill="#1e293b"/>
            <text x="160" y="310" text-anchor="middle" fill="white" font-family="sans-serif" font-weight="bold" font-size="22">APPROVED</text>
        </g>

        <g transform="translate({plan_x}, {plan_y})">
            <text x="0" y="{-N*sc/2 - 70}" text-anchor="middle" font-weight="bold" font-size="20">PLAN VIEW</text>
            <rect x="{-B*sc/2}" y="{-N*sc/2}" width="{B*sc}" height="{N*sc}" fill="#f8fafc" stroke="black" stroke-width="3"/>
            <g fill="#cbd5e1" stroke="black" stroke-width="1.5">
                <rect x="{-cb/2*sc}" y="{-ch/2*sc}" width="{cb*sc}" height="{ctf*sc}"/> 
                <rect x="{-cb/2*sc}" y="{(ch/2-ctf)*sc}" width="{cb*sc}" height="{ctf*sc}"/>
                <rect x="{-ctw/2*sc}" y="{-ch/2*sc+ctf*sc}" width="{ctw*sc}" height="{(ch-2*ctf)*sc}"/>
            </g>
            <circle cx="{-sx/2*sc}" cy="{-sy/2*sc}" r="9" fill="white" stroke="#2563eb" stroke-width="2.5"/>
            <circle cx="{sx/2*sc}"  cy="{-sy/2*sc}" r="9" fill="white" stroke="#2563eb" stroke-width="2.5"/>
            <circle cx="{-sx/2*sc}" cy="{sy/2*sc}"  r="9" fill="white" stroke="#2563eb" stroke-width="2.5"/>
            <circle cx="{sx/2*sc}"  cy="{sy/2*sc}"  r="9" fill="white" stroke="#2563eb" stroke-width="2.5"/>

            <g transform="translate(0, {N*sc/2 + 40})" font-family="monospace" font-size="12" font-weight="bold">
                <line x1="{-B*sc/2}" y1="0" x2="{B*sc/2}" y2="0" stroke="black"/>
                {get_tick(-B*sc/2,0)} {get_tick(-sx*sc/2,0)} {get_tick(-cb/2*sc,0)} {get_tick(cb/2*sc,0)} {get_tick(sx*sc/2,0)} {get_tick(B*sc/2,0)}
                <text x="{-sx/2*sc - edge_x*sc/2}" y="18" text-anchor="middle" fill="green">{int(edge_x)}</text>
                <text x="{-cb/2*sc - clr_x*sc/2}" y="18" text-anchor="middle" fill="red">{int(clr_x)}</text>
                <text x="0" y="18" text-anchor="middle">{int(cb)}</text>
                <text x="{cb/2*sc + clr_x*sc/2}" y="18" text-anchor="middle" fill="red">{int(clr_x)}</text>
                <text x="{sx/2*sc + edge_x*sc/2}" y="18" text-anchor="middle" fill="green">{int(edge_x)}</text>
                
                <line x1="{-B*sc/2}" y1="45" x2="{B*sc/2}" y2="45" stroke="black" stroke-width="2"/>
                <text x="0" y="65" text-anchor="middle" font-size="16">WIDTH B = {int(B)}</text>
            </g>
        </g>

        <g transform="translate({side_x}, {side_y})">
            <text x="0" y="{-N*sc/2 - 70}" text-anchor="middle" font-weight="bold" font-size="18">SECTION B-B (SIDE)</text>
            <rect x="{-N*sc/2}" y="0" width="{N*sc}" height="{tp*sc}" fill="white" stroke="black" stroke-width="2.5"/>
            <rect x="{-ch/2*sc}" y="-140" width="{ctf*sc}" height="140" fill="#94a3b8" stroke="black"/> 
            <rect x="{(ch/2 - ctf)*sc}" y="-140" width="{ctf*sc}" height="140" fill="#94a3b8" stroke="black"/> 
            <rect x="{-ch/2*sc + ctf*sc}" y="-140" width="{(ch - 2*ctf)*sc}" height="140" fill="#cbd5e1" stroke="black" opacity="0.5"/>

            <g transform="translate({N*sc/2 + 50}, 0)" font-family="monospace" font-size="11" font-weight="bold">
                <line x1="0" y1="{-N*sc/2}" x2="0" y2="{N*sc/2}" stroke="black"/>
                {get_tick(0, -N*sc/2)} {get_tick(0, -sy*sc/2)} {get_tick(0, -ch/2*sc)} {get_tick(0, ch/2*sc)} {get_tick(0, sy*sc/2)} {get_tick(0, N*sc/2)}
                <text x="20" y="{-N*sc/2 + edge_y*sc/2}" transform="rotate(90, 20, {-N*sc/2 + edge_y*sc/2})" text-anchor="middle" fill="green">e:{int(edge_y)}</text>
                <text x="20" y="{-sy*sc/2 + clr_y*sc/2}" transform="rotate(90, 20, {-sy*sc/2 + clr_y*sc/2})" text-anchor="middle" fill="red">c:{int(clr_y)}</text>
                <text x="20" y="0" transform="rotate(90, 20, 0)" text-anchor="middle">WEB:{int(ch-2*ctf)}</text>
                <text x="20" y="{sy*sc/2 - clr_y*sc/2}" transform="rotate(90, 20, {sy*sc/2 - clr_y*sc/2})" text-anchor="middle" fill="red">c:{int(clr_y)}</text>
                <text x="20" y="{N*sc/2 - edge_y*sc/2}" transform="rotate(90, 20, {N*sc/2 - edge_y*sc/2})" text-anchor="middle" fill="green">e:{int(edge_y)}</text>
                
                <line x1="55" y1="{-N*sc/2}" x2="55" y2="{N*sc/2}" stroke="black" stroke-width="2"/>
                <text x="75" y="0" transform="rotate(90, 75, 0)" text-anchor="middle" font-size="16">LENGTH N = {int(N)}</text>
            </g>
        </g>

        <g transform="translate({front_x}, {front_y})">
            <text x="0" y="-140" text-anchor="middle" font-weight="bold" font-size="18">SECTION A-A (FRONT)</text>
            <rect x="{-B*sc/2}" y="{tp*sc}" width="{B*sc}" height="{grout_h*sc}" fill="#f1f5f9" stroke="black"/>
            <rect x="{-B*sc/2}" y="0" width="{B*sc}" height="{tp*sc}" fill="white" stroke="black" stroke-width="2.5"/>
            <rect x="{-cb/2*sc}" y="-120" width="{cb*sc}" height="120" fill="#cbd5e1" stroke="black"/>
            <line x1="{-sx/2*sc}" y1="-20" x2="{-sx/2*sc}" y2="150" stroke="#2563eb" stroke-width="3"/>
            <line x1="{sx/2*sc}" y1="-20" x2="{sx/2*sc}" y2="150" stroke="#2563eb" stroke-width="3"/>
            
            <path d="M {-cb/2*sc} -60 L -280 -60" fill="none" stroke="red" marker-end="url(#arrow)"/>
            <text x="-285" y="-55" text-anchor="end" fill="red" font-size="14" font-weight="bold">COLUMN: {col_name}</text>
            <path d="M {B*sc/2} {tp*sc/2} L 300 {tp*sc/2}" fill="none" stroke="black" stroke-width="1"/>
            <text x="305" y="{tp*sc/2 + 5}" font-size="14" font-weight="bold">PLATE PL{int(tp)}</text>
        </g>

        <defs>
            <marker id="arrow" markerWidth="10" markerHeight="10" refX="0" refY="3" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0 L0,6 L9,3 z" fill="red" />
            </marker>
        </defs>
    </svg>
    """
    components.html(svg, height=1150, scrolling=True)
