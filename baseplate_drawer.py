def get_svg_drawing(params):
    # --- ดึงข้อมูลกลับมาให้ครบ ---
    B, N = params['B'], params['N']
    cb, ch = params['cb'], params['ch']
    ctw, ctf = params['ctw'], params['ctf']
    sx, sy = params['sx'], params['sy']
    tp, grout_h = params['tp'], params['grout_h']
    edge_x, edge_y = params['edge_x'], params['edge_y']
    clr_x, clr_y = params['clr_x'], params['clr_y']
    col_name, bolt_d = params['col_name'], params['bolt_d']
    hole_d = bolt_d + 3

    cv_w, cv_h = 1300, 1400
    sc = 420 / max(N, B)  
    px, py = 500, 400 
    ax, ay = 500, 1050 

    def tick(x, y, is_v=False):
        if is_v: return f'<line x1="{x-6}" y1="{y+6}" x2="{x+6}" y2="{y-6}" stroke="black" stroke-width="1.5"/>'
        return f'<line x1="{x-6}" y1="{y+6}" x2="{x+6}" y2="{y-6}" stroke="black" stroke-width="1.5"/>'

    return f"""
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#ffffff" stroke="#1e293b" stroke-width="2"/>
        
        <g transform="translate(900, 950)">
            <rect width="360" height="400" fill="none" stroke="black" stroke-width="2"/>
            <text x="15" y="40" font-family="sans-serif" font-weight="bold" font-size="22">PROJECT: BASE PLATE DESIGN</text>
            <line x1="0" y1="60" x2="360" y2="60" stroke="black" stroke-width="2"/>
            <text x="15" y="100" font-family="sans-serif" font-size="14" font-weight="bold">SPECIFICATIONS:</text>
            <text x="15" y="130" font-family="monospace" font-size="15" fill="#1e40af">● COLUMN: {col_name}</text>
            <text x="15" y="160" font-family="monospace" font-size="15" fill="#1e40af">● PLATE: PL{int(tp)}x{int(B)}x{int(N)}</text>
            <text x="15" y="190" font-family="monospace" font-size="15" fill="#1e40af">● BOLT: 4-M{bolt_d} (Hole Ø{hole_d})</text>
            <text x="15" y="220" font-family="monospace" font-size="15" fill="#1e40af">● WELD: Fillet All Around 8mm</text>
            <rect x="0" y="320" width="360" height="80" fill="#1e293b"/>
            <text x="180" y="370" text-anchor="middle" fill="white" font-family="sans-serif" font-weight="bold" font-size="26">APPROVED</text>
        </g>

        <g transform="translate({px}, {py})">
            <text x="0" y="{-N*sc/2 - 140}" text-anchor="middle" font-weight="bold" font-size="24">PLAN VIEW</text>
            
            <line x1="{-B*sc/2 - 50}" y1="0" x2="{B*sc/2 + 50}" y2="0" stroke="#94a3b8" stroke-dasharray="8,4,2,4" stroke-width="1"/>
            <line x1="0" y1="{-N*sc/2 - 50}" x2="0" y2="{N*sc/2 + 50}" stroke="#94a3b8" stroke-dasharray="8,4,2,4" stroke-width="1"/>
            
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

            <g transform="translate(0, {N*sc/2 + 70})" font-family="Arial" font-size="14" font-weight="bold">
                <line x1="{-B*sc/2}" y1="0" x2="{B*sc/2}" y2="0" stroke="black" stroke-width="1.5"/>
                {tick(-B*sc/2,0)} {tick(-sx/2*sc,0)} {tick(-cb/2*sc,0)} {tick(cb/2*sc,0)} {tick(sx/2*sc,0)} {tick(B*sc/2,0)}
                <text x="{-sx/2*sc - edge_x*sc/2}" y="25" text-anchor="middle" fill="green">{int(edge_x)}</text>
                <text x="{-cb/2*sc - clr_x*sc/2}" y="25" text-anchor="middle" fill="red">{int(clr_x)}</text>
                <text x="0" y="25" text-anchor="middle">{int(cb)}</text>
                <text x="{cb/2*sc + clr_x*sc/2}" y="25" text-anchor="middle" fill="red">{int(clr_x)}</text>
                <text x="{sx/2*sc + edge_x*sc/2}" y="25" text-anchor="middle" fill="green">{int(edge_x)}</text>
                <line x1="{-B*sc/2}" y1="55" x2="{B*sc/2}" y2="55" stroke="black" stroke-width="2"/>
                <text x="0" y="75" text-anchor="middle">TOTAL B = {int(B)}</text>
            </g>

            <g transform="translate({-B*sc/2 - 70}, 0)" font-family="Arial" font-size="14" font-weight="bold">
                <line x1="0" y1="{-N*sc/2}" x2="0" y2="{N*sc/2}" stroke="black" stroke-width="1.5"/>
                {tick(0, -N*sc/2)} {tick(0, -sy/2*sc)} {tick(0, -ch/2*sc)} {tick(0, ch/2*sc)} {tick(0, sy/2*sc)} {tick(0, N*sc/2)}
                <text x="-25" y="{-sy/2*sc - edge_y*sc/2}" transform="rotate(-90, -25, {-sy/2*sc - edge_y*sc/2})" text-anchor="middle" fill="green">{int(edge_y)}</text>
                <text x="-25" y="{-ch/2*sc - clr_y*sc/2 + ctf*sc/2}" transform="rotate(-90, -25, {-ch/2*sc - clr_y*sc/2 + ctf*sc/2})" text-anchor="middle" fill="red">{int(clr_y)}</text>
                <text x="-25" y="0" transform="rotate(-90, -25, 0)" text-anchor="middle">{int(ch)}</text>
                <text x="-25" y="{ch/2*sc + clr_y*sc/2 - ctf*sc/2}" transform="rotate(-90, -25, {ch/2*sc + clr_y*sc/2 - ctf*sc/2})" text-anchor="middle" fill="red">{int(clr_y)}</text>
                <text x="-25" y="{sy/2*sc + edge_y*sc/2}" transform="rotate(-90, -25, {sy/2*sc + edge_y*sc/2})" text-anchor="middle" fill="green">{int(edge_y)}</text>
                <line x1="-55" y1="{-N*sc/2}" x2="-55" y2="{N*sc/2}" stroke="black" stroke-width="2"/>
                <text x="-75" y="0" transform="rotate(-90, -75, 0)" text-anchor="middle">TOTAL N = {int(N)}</text>
            </g>
        </g>

        <g transform="translate({ax}, {ay})">
            <text x="0" y="-220" text-anchor="middle" font-weight="bold" font-size="22">SECTION A-A</text>
            
            <rect x="{-B*sc/2}" y="{tp*sc}" width="{B*sc}" height="{grout_h*sc}" fill="#f1f5f9" stroke="black"/>
            <rect x="{-B*sc/2}" y="0" width="{B*sc}" height="{tp*sc}" fill="white" stroke="black" stroke-width="2.5"/>
            <rect x="{-cb/2*sc}" y="-150" width="{cb*sc}" height="150" fill="#cbd5e1" stroke="black"/>
            
            <line x1="{-sx/2*sc}" y1="-40" x2="{-sx/2*sc}" y2="200" stroke="#2563eb" stroke-width="3"/>
            <line x1="{sx/2*sc}" y1="-40" x2="{sx/2*sc}" y2="200" stroke="#2563eb" stroke-width="3"/>

            <g transform="translate(0, 160)" font-family="Arial" font-size="14" font-weight="bold">
                <line x1="{-B*sc/2}" y1="0" x2="{B*sc/2}" y2="0" stroke="black" stroke-width="1.5"/>
                {tick(-B*sc/2,0)} {tick(-sx/2*sc,0)} {tick(-cb/2*sc,0)} {tick(cb/2*sc,0)} {tick(sx/2*sc,0)} {tick(B*sc/2,0)}
                <text x="{-sx/2*sc - edge_x*sc/2}" y="25" text-anchor="middle" fill="green">e:{int(edge_x)}</text>
                <text x="{-cb/2*sc - clr_x*sc/2}" y="25" text-anchor="middle" fill="red">c:{int(clr_x)}</text>
                <text x="0" y="25" text-anchor="middle">COL:{int(cb)}</text>
                <text x="{cb/2*sc + clr_x*sc/2}" y="25" text-anchor="middle" fill="red">c:{int(clr_x)}</text>
                <text x="{sx/2*sc + edge_x*sc/2}" y="25" text-anchor="middle" fill="green">e:{int(edge_x)}</text>
            </g>

            <g transform="translate({B*sc/2 + 70}, 0)" font-family="Arial" font-size="13" font-weight="bold">
                <line x1="0" y1="-150" x2="0" y2="{tp*sc + grout_h*sc}" stroke="black" stroke-width="1.5"/>
                {tick(0,-150)} {tick(0,0)} {tick(0,tp*sc)} {tick(0,tp*sc + grout_h*sc)}
                <text x="20" y="-75" transform="rotate(90, 20, -75)" text-anchor="middle">COL</text>
                <text x="20" y="{tp*sc/2}" transform="rotate(90, 20, {tp*sc/2})" text-anchor="middle" fill="#1e40af">tp:{int(tp)}</text>
                <text x="20" y="{tp*sc + grout_h*sc/2}" transform="rotate(90, 20, {tp*sc + grout_h*sc/2})" text-anchor="middle" fill="#64748b">GRT:{int(grout_h)}</text>
            </g>

            <path d="M {-cb/4*sc} -80 L -250 -80" fill="none" stroke="red" marker-end="url(#arrow)" stroke-width="1.5"/>
            <text x="-255" y="-75" text-anchor="end" fill="red" font-size="16" font-weight="bold">{col_name}</text>
        </g>

        <defs>
            <marker id="arrow" markerWidth="10" markerHeight="10" refX="0" refY="3" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0 L0,6 L9,3 z" fill="red" />
            </marker>
        </defs>
    </svg>
    """
