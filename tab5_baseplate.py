import streamlit as st
import streamlit.components.v1 as components
import steel_db

def render(res_ctx, v_design):
    # --- 1. CONFIGURATION & INPUTS ---
    with st.container(border=True):
        st.markdown("##### 🛠️ Design & Shop Drawing Control")
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
    cv_w, cv_h = 1100, 1100
    sc = 480 / max(N, B)  # Scaling to fit layout
    
    # Define View Centers
    plan_x, plan_y = 350, 350
    front_x, front_y = 350, 850  # Below Plan
    side_x, side_y = 850, 350   # Right of Plan

    def get_tick(x, y): return f'<line x1="{x-4}" y1="{y+4}" x2="{x+4}" y2="{y-4}" stroke="black" stroke-width="1"/>'

    svg = f"""
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#ffffff" stroke="#1e293b" stroke-width="4"/>
        
        <g transform="translate(800, 750)">
            <rect width="260" height="310" fill="none" stroke="black" stroke-width="2"/>
            <text x="10" y="30" font-family="sans-serif" font-weight="bold" font-size="16">PROJECT: STEEL DESIGN</text>
            <line x1="0" y1="45" x2="260" y2="45" stroke="black"/>
            <text x="10" y="70" font-family="sans-serif" font-size="12">DRAWING: BASE PLATE DETAIL</text>
            <text x="10" y="90" font-family="sans-serif" font-size="12">MARK: BP-01</text>
            <line x1="0" y1="105" x2="260" y2="105" stroke="black"/>
            <text x="10" y="130" font-family="sans-serif" font-weight="bold" font-size="12">MATERIAL SPEC:</text>
            <text x="10" y="150" font-family="monospace" font-size="11">- COLUMN: {col_name}</text>
            <text x="10" y="170" font-family="monospace" font-size="11">- PLATE: PL{int(tp)}x{int(B)}x{int(N)}</text>
            <text x="10" y="190" font-family="monospace" font-size="11">- BOLT: 4-M{bolt_d} GR 8.8</text>
            <text x="10" y="210" font-family="monospace" font-size="11">- GROUT: NON-SHRINK (50mm)</text>
            <rect x="0" y="240" width="260" height="70" fill="#f1f5f9"/>
            <text x="130" y="280" text-anchor="middle" font-family="sans-serif" font-weight="bold" font-size="20">CONSTRUCTION</text>
        </g>

        <g transform="translate({plan_x}, {plan_y})">
            <text x="0" y="{-N*sc/2 - 60}" text-anchor="middle" font-weight="bold" font-size="18">PLAN VIEW (TOP)</text>
            <rect x="{-B*sc/2}" y="{-N*sc/2}" width="{B*sc}" height="{N*sc}" fill="#f8fafc" stroke="black" stroke-width="2.5"/>
            <g fill="#cbd5e1" stroke="black" stroke-width="1.5">
                <rect x="{-cb/2*sc}" y="{-ch/2*sc}" width="{cb*sc}" height="{ctf*sc}"/> 
                <rect x="{-cb/2*sc}" y="{(ch/2-ctf)*sc}" width="{cb*sc}" height="{ctf*sc}"/>
                <rect x="{-ctw/2*sc}" y="{-ch/2*sc+ctf*sc}" width="{ctw*sc}" height="{(ch-2*ctf)*sc}"/>
            </g>
            <circle cx="{-sx/2*sc}" cy="{-sy/2*sc}" r="8" fill="white" stroke="#2563eb" stroke-width="2"/>
            <circle cx="{sx/2*sc}"  cy="{-sy/2*sc}" r="8" fill="white" stroke="#2563eb" stroke-width="2"/>
            <circle cx="{-sx/2*sc}" cy="{sy/2*sc}"  r="8" fill="white" stroke="#2563eb" stroke-width="2"/>
            <circle cx="{sx/2*sc}"  cy="{sy/2*sc}"  r="8" fill="white" stroke="#2563eb" stroke-width="2"/>

            <g transform="translate(0, {N*sc/2 + 40})">
                <line x1="{-B*sc/2}" y1="0" x2="{B*sc/2}" y2="0" stroke="black"/>
                {get_tick(-B*sc/2,0)} {get_tick(-sx*sc/2,0)} {get_tick(sx*sc/2,0)} {get_tick(B*sc/2,0)}
                <text x="{-sx/2*sc - edge_x*sc/2}" y="15" text-anchor="middle" font-size="11">{int(edge_x)}</text>
                <text x="0" y="15" text-anchor="middle" font-size="12" font-weight="bold">Sx = {int(sx)}</text>
                <text x="{sx/2*sc + edge_x*sc/2}" y="15" text-anchor="middle" font-size="11">{int(edge_x)}</text>
                <line x1="{-B*sc/2}" y1="35" x2="{B*sc/2}" y2="35" stroke="black" stroke-width="2"/>
                <text x="0" y="55" text-anchor="middle" font-size="14" font-weight="bold">B = {int(B)}</text>
            </g>
        </g>

        <g transform="translate({front_x}, {front_y})">
            <text x="0" y="-120" text-anchor="middle" font-weight="bold" font-size="16">SECTION A-A (FRONT)</text>
            <rect x="{-B*sc/2 - 50}" y="{tp*sc + grout_h*sc}" width="{B*sc + 100}" height="80" fill="#e2e8f0" stroke="black" stroke-dasharray="2,2"/>
            <rect x="{-B*sc/2}" y="{tp*sc}" width="{B*sc}" height="{grout_h*sc}" fill="#f1f5f9" stroke="black"/>
            <rect x="{-B*sc/2}" y="0" width="{B*sc}" height="{tp*sc}" fill="white" stroke="black" stroke-width="2"/>
            <rect x="{-cb/2*sc}" y="-100" width="{cb*sc}" height="100" fill="#cbd5e1" stroke="black"/>
            <line x1="{-sx/2*sc}" y1="-20" x2="{-sx/2*sc}" y2="150" stroke="#2563eb" stroke-width="3"/>
            <line x1="{sx/2*sc}" y1="-20" x2="{sx/2*sc}" y2="150" stroke="#2563eb" stroke-width="3"/>
            
            <path d="M {-cb/2*sc} -50 L -250 -50" fill="none" stroke="red" marker-end="url(#arrow)"/>
            <text x="-255" y="-45" text-anchor="end" fill="red" font-size="12">COLUMN: {col_name}</text>
            <path d="M {B*sc/2} {tp*sc/2} L 220 {tp*sc/2}" fill="none" stroke="black"/>
            <text x="225" y="{tp*sc/2 + 5}" font-size="12">BASE PLATE PL{int(tp)}</text>
        </g>

        <g transform="translate({side_x}, {side_y})">
            <text x="0" y="{-N*sc/2 - 60}" text-anchor="middle" font-weight="bold" font-size="16">SECTION B-B (SIDE)</text>
            <rect x="{-N*sc/2 - 30}" y="{tp*sc + grout_h*sc}" width="{N*sc + 60}" height="80" fill="#e2e8f0" stroke="black" stroke-dasharray="2,2"/>
            <rect x="{-N*sc/2}" y="0" width="{N*sc}" height="{tp*sc}" fill="white" stroke="black" stroke-width="2"/>
            <line x1="{-ch/2*sc}" y1="-100" x2="{-ch/2*sc}" y2="0" stroke="black" stroke-width="3"/>
            <line x1="{ch/2*sc}" y1="-100" x2="{ch/2*sc}" y2="0" stroke="black" stroke-width="3"/>
            <rect x="{-ctw/2*sc}" y="-100" width="{ctw*sc}" height="100" fill="#cbd5e1" stroke="black"/>

            <g transform="translate({N*sc/2 + 40}, 0)">
                <line x1="0" y1="{-N*sc/2}" x2="0" y2="{N*sc/2}" stroke="black"/>
                {get_tick(0, -N*sc/2)} {get_tick(0, -sy*sc/2)} {get_tick(0, sy*sc/2)} {get_tick(0, N*sc/2)}
                <text x="15" y="0" transform="rotate(90, 15, 0)" text-anchor="middle" font-size="12" font-weight="bold">Sy = {int(sy)}</text>
                <line x1="45" y1="{-N*sc/2}" x2="45" y2="{N*sc/2}" stroke="black" stroke-width="2"/>
                <text x="65" y="0" transform="rotate(90, 65, 0)" text-anchor="middle" font-size="14" font-weight="bold">N = {int(N)}</text>
            </g>
        </g>

        <defs>
            <marker id="arrow" markerWidth="10" markerHeight="10" refX="0" refY="3" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0 L0,6 L9,3 z" fill="red" />
            </marker>
        </defs>
    </svg>
    """
    components.html(svg, height=1150, scrolling=True)
