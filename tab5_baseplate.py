import streamlit as st
import streamlit.components.v1 as components
import steel_db

def render(res_ctx, v_design):
    # --- 1. SELECTION & INPUTS ---
    with st.container(border=True):
        st.markdown("##### 🛠️ Engineering Drawing Control")
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

    # --- 3. SVG ENGINE ---
    cv_w, cv_h = 1150, 1000
    sc = 400 / max(N, B) 
    
    px, py = 350, 320   # Plan
    ax, ay = 350, 820   # Front (X-X)
    bx, by = 900, 320   # Side (Y-Y)

    def tick(x, y): return f'<line x1="{x-4}" y1="{y+4}" x2="{x+4}" y2="{y-4}" stroke="black" stroke-width="1"/>'

    svg = f"""
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#ffffff" />
        
        <g transform="translate({px}, {py})">
            <text x="0" y="{-N*sc/2 - 60}" text-anchor="middle" font-weight="bold" font-size="16">PLAN VIEW</text>
            <rect x="{-B*sc/2}" y="{-N*sc/2}" width="{B*sc}" height="{N*sc}" fill="#f8fafc" stroke="black" stroke-width="2"/>
            <g fill="#cbd5e1" stroke="black" stroke-width="1.2">
                <rect x="{-cb/2*sc}" y="{-ch/2*sc}" width="{cb*sc}" height="{ctf*sc}"/>
                <rect x="{-cb/2*sc}" y="{(ch/2-ctf)*sc}" width="{cb*sc}" height="{ctf*sc}"/>
                <rect x="{-ctw/2*sc}" y="{-ch/2*sc+ctf*sc}" width="{ctw*sc}" height="{(ch-2*ctf)*sc}"/>
            </g>
            <g fill="white" stroke="#2563eb" stroke-width="1.5">
                <circle cx="{-sx/2*sc}" cy="{-sy/2*sc}" r="6"/><circle cx="{sx/2*sc}" cy="{-sy/2*sc}" r="6"/>
                <circle cx="{-sx/2*sc}" cy="{sy/2*sc}" r="6"/><circle cx="{sx/2*sc}" cy="{sy/2*sc}" r="6"/>
            </g>
            <text x="{B*sc/2 + 30}" y="0" fill="red" font-weight="bold">B-B →</text>
        </g>

        <g transform="translate({ax}, {ay})">
            <text x="0" y="-120" text-anchor="middle" font-weight="bold" font-size="14">SECTION A-A (FRONT)</text>
            <rect x="{-B*sc/2}" y="{tp*sc}" width="{B*sc}" height="{grout_h*sc}" fill="#f1f5f9" stroke="black" stroke-dasharray="2,1"/>
            <rect x="{-B*sc/2}" y="0" width="{B*sc}" height="{tp*sc}" fill="white" stroke="black" stroke-width="2"/>
            <rect x="{-cb/2*sc}" y="-120" width="{cb*sc}" height="120" fill="#cbd5e1" stroke="black"/>
            <line x1="{-sx/2*sc}" y1="-10" x2="{-sx/2*sc}" y2="120" stroke="#2563eb" stroke-width="2" stroke-dasharray="4,2"/>
            <line x1="{sx/2*sc}" y1="-10" x2="{sx/2*sc}" y2="120" stroke="#2563eb" stroke-width="2" stroke-dasharray="4,2"/>
        </g>

        <g transform="translate({bx}, {by})">
            <text x="0" y="{-N*sc/2 - 60}" text-anchor="middle" font-weight="bold" font-size="14">SECTION B-B (SIDE)</text>
            <rect x="{-N*sc/2}" y="{tp*sc}" width="{N*sc}" height="{grout_h*sc}" fill="#f1f5f9" stroke="black" stroke-dasharray="2,1"/>
            <rect x="{-N*sc/2}" y="0" width="{N*sc}" height="{tp*sc}" fill="white" stroke="black" stroke-width="2"/>
            
            <line x1="{-ch/2*sc}" y1="-120" x2="{-ch/2*sc}" y2="0" stroke="black" stroke-width="2.5"/>
            <line x1="{ch/2*sc}" y1="-120" x2="{ch/2*sc}" y2="0" stroke="black" stroke-width="2.5"/>
            <line x1="0" y1="-120" x2="0" y2="0" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="5,5"/>
            
            <line x1="{-sy/2*sc}" y1="-10" x2="{-sy/2*sc}" y2="120" stroke="#2563eb" stroke-width="2" stroke-dasharray="4,2"/>
            <line x1="{sy/2*sc}" y1="-10" x2="{sy/2*sc}" y2="120" stroke="#2563eb" stroke-width="2" stroke-dasharray="4,2"/>

            <g transform="translate({N*sc/2 + 40}, 0)" font-family="monospace" font-size="10">
                <line x1="0" y1="{-N*sc/2}" x2="0" y2="{N*sc/2}" stroke="black"/>
                {tick(0,-N*sc/2)} {tick(0,-sy*sc/2)} {tick(0,-ch/2*sc)} {tick(0,ch/2*sc)} {tick(0,sy*sc/2)} {tick(0,N*sc/2)}
                <text x="12" y="{-sy/2*sc - edge_y*sc/2}" transform="rotate(90, 12, {-sy/2*sc - edge_y*sc/2})" text-anchor="middle" fill="green">{int(edge_y)}</text>
                <text x="12" y="0" transform="rotate(90, 12, 0)" text-anchor="middle" font-weight="bold">Sy={int(sy)}</text>
                <text x="12" y="{sy/2*sc + edge_y*sc/2}" transform="rotate(90, 12, {sy/2*sc + edge_y*sc/2})" text-anchor="middle" fill="green">{int(edge_y)}</text>
                <text x="40" y="0" transform="rotate(90, 40, 0)" text-anchor="middle" font-size="13" font-weight="bold">N = {int(N)}</text>
            </g>
        </g>
    </svg>
    """
    components.html(svg, height=1050)
