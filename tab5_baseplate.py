import streamlit as st
import streamlit.components.v1 as components
import steel_db

def render(res_ctx, v_design):
    # --- 1. INPUTS ---
    with st.container(border=True):
        st.markdown("##### 📐 Base Plate Master Configuration")
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
            bolt_d = st.selectbox("Bolt Size", [20, 24, 30], index=0)

    # --- 2. CALCULATE DIMENSIONS ---
    sx = cb + (2 * clr_x)
    sy = ch - (2 * ctf) + (2 * clr_y)
    B = sx + (2 * edge_x)
    N = sy + (2 * edge_y)
    grout_h = 50.0

    # --- 3. SVG ENGINE ---
    cv_w, cv_h = 1150, 1100
    sc = 450 / max(N, B) # Scaling
    
    # Centers
    plan_x, plan_y = 380, 350
    front_x, front_y = 380, 850
    side_x, side_y = 900, 350

    def draw_tick(x, y):
        return f'<line x1="{x-4}" y1="{y+4}" x2="{x+4}" y2="{y-4}" stroke="black" stroke-width="1.2"/>'

    svg = f"""
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#ffffff" stroke="#cbd5e1" stroke-width="2"/>
        
        <g transform="translate({plan_x}, {plan_y})">
            <text x="0" y="{-N*sc/2 - 70}" text-anchor="middle" font-weight="bold" font-size="18">PLAN VIEW (SCALE 1:AUTO)</text>
            
            <rect x="{-B*sc/2}" y="{-N*sc/2}" width="{B*sc}" height="{N*sc}" fill="#fcfcfc" stroke="black" stroke-width="2.5"/>
            
            <g fill="#e2e8f0" stroke="black" stroke-width="1.5">
                <rect x="{-cb/2*sc}" y="{-ch/2*sc}" width="{cb*sc}" height="{ctf*sc}"/> 
                <rect x="{-cb/2*sc}" y="{(ch/2-ctf)*sc}" width="{cb*sc}" height="{ctf*sc}"/>
                <rect x="{-ctw/2*sc}" y="{-ch/2*sc+ctf*sc}" width="{ctw*sc}" height="{(ch-2*ctf)*sc}"/>
            </g>
            
            <g fill="white" stroke="#2563eb" stroke-width="2">
                <circle cx="{-sx/2*sc}" cy="{-sy/2*sc}" r="8"/><circle cx="{sx/2*sc}"  cy="{-sy/2*sc}" r="8"/>
                <circle cx="{-sx/2*sc}" cy="{sy/2*sc}"  r="8"/><circle cx="{sx/2*sc}"  cy="{sy/2*sc}"  r="8"/>
            </g>

            <g transform="translate(0, {N*sc/2 + 50})" font-family="monospace" font-size="11">
                <line x1="{-B*sc/2}" y1="0" x2="{B*sc/2}" y2="0" stroke="black"/>
                {draw_tick(-B*sc/2,0)} {draw_tick(-sx*sc/2,0)} {draw_tick(-cb*sc/2,0)} 
                {draw_tick(cb*sc/2,0)} {draw_tick(sx*sc/2,0)} {draw_tick(B*sc/2,0)}
                
                <text x="{-B*sc/2 + (edge_x*sc/2)}" y="15" text-anchor="middle" fill="green">{int(edge_x)}</text>
                <text x="{-sx*sc/2 + (clr_x*sc/2)}" y="15" text-anchor="middle" fill="red">{int(clr_x)}</text>
                <text x="0" y="15" text-anchor="middle" font-weight="bold">{int(cb)}</text>
                <text x="{sx*sc/2 - (clr_x*sc/2)}" y="15" text-anchor="middle" fill="red">{int(clr_x)}</text>
                <text x="{B*sc/2 - (edge_x*sc/2)}" y="15" text-anchor="middle" fill="green">{int(edge_x)}</text>
                
                <line x1="{-B*sc/2}" y1="35" x2="{B*sc/2}" y2="35" stroke="black" stroke-width="2"/>
                <text x="0" y="50" text-anchor="middle" font-size="14" font-weight="bold">B = {int(B)}</text>
            </g>
            
            <g transform="translate({-B*sc/2 - 50}, 0)" font-family="monospace" font-size="11">
                <line x1="0" y1="{-N*sc/2}" x2="0" y2="{N*sc/2}" stroke="black"/>
                {draw_tick(0, -N*sc/2)} {draw_tick(0, -sy*sc/2)} {draw_tick(0, -(ch/2-ctf)*sc)} 
                {draw_tick(0, (ch/2-ctf)*sc)} {draw_tick(0, sy*sc/2)} {draw_tick(0, N*sc/2)}
                
                <text x="-15" y="{-N*sc/2 + edge_y*sc/2}" transform="rotate(-90, -15, {-N*sc/2 + edge_y*sc/2})" text-anchor="middle" fill="green">{int(edge_y)}</text>
                <text x="-15" y="{-sy*sc/2 + clr_y*sc/2}" transform="rotate(-90, -15, {-sy*sc/2 + clr_y*sc/2})" text-anchor="middle" fill="red">{int(clr_y)}</text>
                <text x="-15" y="0" transform="rotate(-90, -15, 0)" text-anchor="middle" font-weight="bold">{int(ch-2*ctf)}</text>
                <text x="-15" y="{sy*sc/2 - clr_y*sc/2}" transform="rotate(-90, -15, {sy*sc/2 - clr_y*sc/2})" text-anchor="middle" fill="red">{int(clr_y)}</text>
                <text x="-15" y="{N*sc/2 - edge_y*sc/2}" transform="rotate(-90, -15, {N*sc/2 - edge_y*sc/2})" text-anchor="middle" fill="green">{int(edge_y)}</text>
            </g>
        </g>

        <g transform="translate({front_x}, {front_y})">
            <text x="0" y="-120" text-anchor="middle" font-weight="bold" font-size="16">SECTION A-A (FRONT)</text>
            <rect x="{-B*sc/2 - 30}" y="{tp*sc + grout_h*sc}" width="{B*sc + 60}" height="70" fill="#f1f5f9" stroke="#94a3b8" stroke-dasharray="4,2"/>
            <rect x="{-B*sc/2}" y="{tp*sc}" width="{B*sc}" height="{grout_h*sc}" fill="#e2e8f0" stroke="black"/>
            <rect x="{-B*sc/2}" y="0" width="{B*sc}" height="{tp*sc}" fill="white" stroke="black" stroke-width="2"/>
            <rect x="{-cb/2*sc}" y="-100" width="{cb*sc}" height="100" fill="#cbd5e1" stroke="black"/>
            <line x1="{-sx*sc/2}" y1="-10" x2="{-sx*sc/2}" y2="130" stroke="#2563eb" stroke-width="2" stroke-dasharray="5,2"/>
            <line x1="{sx*sc/2}" y1="-10" x2="{sx*sc/2}" y2="130" stroke="#2563eb" stroke-width="2" stroke-dasharray="5,2"/>

            <g transform="translate({B*sc/2 + 30}, 0)" font-family="monospace" font-size="11">
                <line x1="0" y1="0" x2="0" y2="{tp*sc + grout_h*sc}" stroke="black"/>
                {draw_tick(0, 0)} {draw_tick(0, tp*sc)} {draw_tick(0, tp*sc + grout_h*sc)}
                <text x="15" y="{tp*sc/2}" alignment-baseline="middle">PL={int(tp)}</text>
                <text x="15" y="{tp*sc + grout_h*sc/2}" alignment-baseline="middle">GRT={int(grout_h)}</text>
            </g>
        </g>

        <g transform="translate({side_x}, {side_y})">
            <text x="0" y="{-N*sc/2 - 70}" text-anchor="middle" font-weight="bold" font-size="16">SECTION B-B (SIDE)</text>
            <rect x="{-N*sc/2}" y="0" width="{N*sc}" height="{tp*sc}" fill="white" stroke="black" stroke-width="2"/>
            <line x1="{-ch/2*sc}" y1="-100" x2="{-ch/2*sc}" y2="0" stroke="black" stroke-width="2"/>
            <line x1="{ch/2*sc}" y1="-100" x2="{ch/2*sc}" y2="0" stroke="black" stroke-width="2"/>
            <rect x="{-ctw/2*sc}" y="-100" width="{ctw*sc}" height="100" fill="#cbd5e1" stroke="black"/>
            
            <text x="0" y="50" text-anchor="middle" font-family="monospace" font-size="14" font-weight="bold">N = {int(N)}</text>
        </g>

        <g transform="translate(800, 750)">
            <rect width="320" height="320" fill="none" stroke="black" stroke-width="2"/>
            <text x="10" y="30" font-family="sans-serif" font-weight="bold" font-size="18">SHOP DRAWING: BP-01</text>
            <line x1="0" y1="45" x2="320" y2="45" stroke="black"/>
            <text x="10" y="75" font-size="13">COL SECTION: {col_name}</text>
            <text x="10" y="100" font-size="13">PLATE SIZE: {int(B)}x{int(N)}x{int(tp)} mm</text>
            <text x="10" y="125" font-size="13">ANCHOR BOLT: 4-M{bolt_d} (GR 8.8)</text>
            <text x="10" y="150" font-size="13">HOLE DIA: Ø{int(bolt_d+6)} mm</text>
            <line x1="0" y1="170" x2="320" y2="170" stroke="black" stroke-dasharray="2,2"/>
            <text x="10" y="200" font-weight="bold" fill="green">GREEN: Edge Dist (e)</text>
            <text x="10" y="225" font-weight="bold" fill="red">RED: Clearance (clr)</text>
            <text x="10" y="250" font-weight="bold" fill="black">BLACK: Section/Overall</text>
        </g>
    </svg>
    """
    components.html(svg, height=1150, scrolling=True)
