def get_svg_drawing(params):
    # ดึงค่าจาก Dictionary params
    B, N = params['B'], params['N']
    cb, ch = params['cb'], params['ch']
    ctw, ctf = params['ctw'], params['ctf']
    sx, sy = params['sx'], params['sy']
    tp, grout_h = params['tp'], params['grout_h']
    edge_x, edge_y = params['edge_x'], params['edge_y']
    clr_x, clr_y = params['clr_x'], params['clr_y']
    col_name, bolt_d = params['col_name'], params['bolt_d']
    
    cv_w, cv_h = 1250, 1300
    sc = 420 / max(N, B)  
    px, py = 450, 400 
    ax, ay = 450, 950 

    def tick(x, y): return f'<line x1="{x-6}" y1="{y+6}" x2="{x+6}" y2="{y-6}" stroke="black" stroke-width="1.2"/>'

    return f"""
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#ffffff" stroke="#1e293b" stroke-width="2"/>
        
        <g transform="translate(880, 850)">
            <rect width="340" height="380" fill="none" stroke="black" stroke-width="2"/>
            <text x="10" y="35" font-family="sans-serif" font-weight="bold" font-size="20">PROJECT: BASE PLATE DESIGN</text>
            <line x1="0" y1="50" x2="340" y2="50" stroke="black"/>
            <text x="10" y="80" font-family="sans-serif" font-size="14">DRAWING: CONSTRUCTION DETAIL</text>
            <text x="10" y="110" font-family="monospace" font-size="14" fill="#1e40af">● COL: {col_name}</text>
            <text x="10" y="135" font-family="monospace" font-size="14" fill="#1e40af">● PL: {int(tp)}x{int(B)}x{int(N)}</text>
            <text x="10" y="160" font-family="monospace" font-size="14" fill="#1e40af">● BOLT: 4-M{bolt_d}</text>
            <rect x="0" y="300" width="340" height="80" fill="#1e293b"/>
            <text x="170" y="350" text-anchor="middle" fill="white" font-family="sans-serif" font-weight="bold" font-size="24">APPROVED</text>
        </g>

        <g transform="translate({px}, {py})">
            <text x="0" y="{-N*sc/2 - 120}" text-anchor="middle" font-weight="bold" font-size="22">PLAN VIEW</text>
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

            <g transform="translate(0, {N*sc/2 + 60})" font-family="Arial" font-size="13" font-weight="bold">
                <line x1="{-B*sc/2}" y1="0" x2="{B*sc/2}" y2="0" stroke="black"/>
                {tick(-B*sc/2,0)} {tick(-sx/2*sc,0)} {tick(-cb/2*sc,0)} {tick(cb/2*sc,0)} {tick(sx/2*sc,0)} {tick(B*sc/2,0)}
                <text x="{-sx/2*sc - edge_x*sc/2}" y="20" text-anchor="middle" fill="green">{int(edge_x)}</text>
                <text x="{-cb/2*sc - clr_x*sc/2}" y="20" text-anchor="middle" fill="red">{int(clr_x)}</text>
                <text x="0" y="20" text-anchor="middle">{int(cb)}</text>
                <text x="{cb/2*sc + clr_x*sc/2}" y="20" text-anchor="middle" fill="red">{int(clr_x)}</text>
                <text x="{sx/2*sc + edge_x*sc/2}" y="20" text-anchor="middle" fill="green">{int(edge_x)}</text>
            </g>

            <g transform="translate({-B*sc/2 - 60}, 0)" font-family="Arial" font-size="13" font-weight="bold">
                <line x1="0" y1="{-N*sc/2}" x2="0" y2="{N*sc/2}" stroke="black"/>
                {tick(0, -N*sc/2)} {tick(0, -sy/2*sc)} {tick(0, -ch/2*sc)} {tick(0, ch/2*sc)} {tick(0, sy/2*sc)} {tick(0, N*sc/2)}
                <text x="-20" y="{-sy/2*sc - edge_y*sc/2}" transform="rotate(-90, -20, {-sy/2*sc - edge_y*sc/2})" text-anchor="middle" fill="green">{int(edge_y)}</text>
                <text x="-20" y="{-ch/2*sc - clr_y*sc/2 + ctf*sc/2}" transform="rotate(-90, -20, {-ch/2*sc - clr_y*sc/2 + ctf*sc/2})" text-anchor="middle" fill="red">{int(clr_y)}</text>
                <text x="-20" y="0" transform="rotate(-90, -20, 0)" text-anchor="middle">{int(ch)}</text>
                <text x="-20" y="{ch/2*sc + clr_y*sc/2 - ctf*sc/2}" transform="rotate(-90, -20, {ch/2*sc + clr_y*sc/2 - ctf*sc/2})" text-anchor="middle" fill="red">{int(clr_y)}</text>
                <text x="-20" y="{sy/2*sc + edge_y*sc/2}" transform="rotate(-90, -20, {sy/2*sc + edge_y*sc/2})" text-anchor="middle" fill="green">{int(edge_y)}</text>
            </g>
        </g>

        <g transform="translate({ax}, {ay})">
            <text x="0" y="-200" text-anchor="middle" font-weight="bold" font-size="20">SECTION A-A</text>
            <rect x="{-B*sc/2}" y="{tp*sc}" width="{B*sc}" height="{grout_h*sc}" fill="#f1f5f9" stroke="black"/>
            <rect x="{-B*sc/2}" y="0" width="{B*sc}" height="{tp*sc}" fill="white" stroke="black" stroke-width="2.5"/>
            <rect x="{-cb/2*sc}" y="-150" width="{cb*sc}" height="150" fill="#cbd5e1" stroke="black"/>
            <line x1="{-sx/2*sc}" y1="-30" x2="{-sx/2*sc}" y2="180" stroke="#2563eb" stroke-width="3"/>
            <line x1="{sx/2*sc}" y1="-30" x2="{sx/2*sc}" y2="180" stroke="#2563eb" stroke-width="3"/>

            <g transform="translate(0, 150)" font-family="Arial" font-size="13" font-weight="bold">
                <line x1="{-B*sc/2}" y1="0" x2="{B*sc/2}" y2="0" stroke="black"/>
                {tick(-B*sc/2,0)} {tick(-sx/2*sc,0)} {tick(-cb/2*sc,0)} {tick(cb/2*sc,0)} {tick(sx/2*sc,0)} {tick(B*sc/2,0)}
                <text x="{-sx/2*sc - edge_x*sc/2}" y="20" text-anchor="middle" fill="green">e:{int(edge_x)}</text>
                <text x="{-cb/2*sc - clr_x*sc/2}" y="20" text-anchor="middle" fill="red">c:{int(clr_x)}</text>
                <text x="0" y="20" text-anchor="middle">COL:{int(cb)}</text>
                <text x="{cb/2*sc + clr_x*sc/2}" y="20" text-anchor="middle" fill="red">c:{int(clr_x)}</text>
                <text x="{sx/2*sc + edge_x*sc/2}" y="20" text-anchor="middle" fill="green">e:{int(edge_x)}</text>
            </g>

            <g transform="translate({B*sc/2 + 50}, 0)" font-family="Arial" font-size="12" font-weight="bold">
                <line x1="0" y1="-150" x2="0" y2="{tp*sc + grout_h*sc}" stroke="black"/>
                {tick(0,-150)} {tick(0,0)} {tick(0,tp*sc)} {tick(0,tp*sc + grout_h*sc)}
                <text x="15" y="-75" transform="rotate(90, 15, -75)" text-anchor="middle">COL</text>
                <text x="15" y="{tp*sc/2}" transform="rotate(90, 15, {tp*sc/2})" text-anchor="middle" fill="#1e40af">tp:{int(tp)}</text>
                <text x="15" y="{tp*sc + grout_h*sc/2}" transform="rotate(90, 15, {tp*sc + grout_h*sc/2})" text-anchor="middle" fill="#64748b">GRT:{int(grout_h)}</text>
            </g>

            <path d="M {-cb/4*sc} -80 L -250 -80" fill="none" stroke="red" marker-end="url(#arrow)"/>
            <text x="-255" y="-75" text-anchor="end" fill="red" font-size="14" font-weight="bold">{col_name}</text>
        </g>

        <defs>
            <marker id="arrow" markerWidth="10" markerHeight="10" refX="0" refY="3" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0 L0,6 L9,3 z" fill="red" />
            </marker>
        </defs>
    </svg>
    """
