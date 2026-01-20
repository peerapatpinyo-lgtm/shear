def get_svg_drawing(params):
    # --- Data Extraction ---
    B, N = params['B'], params['N']
    cb, ch = params['cb'], params['ch']
    ctw, ctf = params['ctw'], params['ctf']
    sx, sy = params['sx'], params['sy']
    tp, grout_h = params['tp'], params['grout_h']
    edge_x, edge_y = params['edge_x'], params['edge_y']
    clr_x, clr_y = params['clr_x'], params['clr_y']
    col_name, bolt_d = params['col_name'], params['bolt_d']
    
    cv_w, cv_h = 1350, 1850 # เพิ่มความสูงเผื่อ 3 วิว
    sc = 400 / max(N, B)  
    px, py = 500, 400   # Plan
    ax, ay = 500, 1000  # Section A-A (Front)
    bx, by = 500, 1500  # Section B-B (Side)

    def tick(x, y): return f'<line x1="{x-6}" y1="{y+6}" x2="{x+6}" y2="{y-6}" stroke="black" stroke-width="1.2"/>'

    return f"""
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#ffffff"/>

        <g transform="translate({px}, {py})">
            <text x="0" y="{-N*sc/2 - 120}" text-anchor="middle" font-weight="bold" font-size="24">PLAN VIEW</text>
            <rect x="{-B*sc/2}" y="{-N*sc/2}" width="{B*sc}" height="{N*sc}" fill="none" stroke="black" stroke-width="3"/>
            
            <g fill="#cbd5e1" stroke="black" stroke-width="1.5">
                <rect x="{-cb/2*sc}" y="{-ch/2*sc}" width="{cb*sc}" height="{ctf*sc}"/> 
                <rect x="{-cb/2*sc}" y="{(ch/2-ctf)*sc}" width="{cb*sc}" height="{ctf*sc}"/>
                <rect x="{-ctw/2*sc}" y="{-ch/2*sc+ctf*sc}" width="{ctw*sc}" height="{(ch-2*ctf)*sc}"/>
            </g>

            <g transform="translate(0, {N*sc/2 + 70})" font-family="Arial" font-size="14" font-weight="bold">
                <line x1="{-B*sc/2}" y1="0" x2="{B*sc/2}" y2="0" stroke="black" stroke-width="1.5"/>
                {tick(-B*sc/2,0)} {tick(-sx/2*sc,0)} {tick(-cb/2*sc,0)} {tick(cb/2*sc,0)} {tick(sx/2*sc,0)} {tick(B*sc/2,0)}
                <text x="{-sx/2*sc - edge_x*sc/2}" y="25" text-anchor="middle" fill="green">{int(edge_x)}</text>
                <text x="{-cb/2*sc - clr_x*sc/2}" y="25" text-anchor="middle" fill="red">{int(clr_x)}</text>
                <text x="0" y="25" text-anchor="middle">{int(cb)}</text>
                <text x="{cb/2*sc + clr_x*sc/2}" y="25" text-anchor="middle" fill="red">{int(clr_x)}</text>
                <text x="{sx/2*sc + edge_x*sc/2}" y="25" text-anchor="middle" fill="green">{int(edge_x)}</text>
            </g>

            <g transform="translate({-B*sc/2 - 70}, 0)" font-family="Arial" font-size="14" font-weight="bold">
                <line x1="0" y1="{-N*sc/2}" x2="0" y2="{N*sc/2}" stroke="black" stroke-width="1.5"/>
                {tick(0, -N*sc/2)} {tick(0, -sy/2*sc)} {tick(0, -ch/2*sc)} {tick(0, ch/2*sc)} {tick(0, sy/2*sc)} {tick(0, N*sc/2)}
                <text x="-15" y="{-sy/2*sc - edge_y*sc/2}" text-anchor="end" fill="green">{int(edge_y)}</text>
                <text x="-15" y="{-ch/2*sc - clr_y*sc/2 + ctf*sc/2}" text-anchor="end" fill="red">{int(clr_y)}</text>
                <text x="-15" y="0" text-anchor="end">{int(ch)}</text>
                <text x="-15" y="{ch/2*sc + clr_y*sc/2 - ctf*sc/2}" text-anchor="end" fill="red">{int(clr_y)}</text>
                <text x="-15" y="{sy/2*sc + edge_y*sc/2}" text-anchor="end" fill="green">{int(edge_y)}</text>
            </g>
        </g>

        <g transform="translate({ax}, {ay})">
            <text x="0" y="-200" text-anchor="middle" font-weight="bold" font-size="22">SECTION A-A (FRONT VIEW)</text>
            <rect x="{-B*sc/2}" y="0" width="{B*sc}" height="{tp*sc}" fill="#f8fafc" stroke="black" stroke-width="2.5"/>
            <rect x="{-B*sc/2}" y="{tp*sc}" width="{B*sc}" height="{grout_h*sc}" fill="#f1f5f9" stroke="black" stroke-dasharray="2,2"/>
            <rect x="{-cb/2*sc}" y="-150" width="{cb*sc}" height="150" fill="#cbd5e1" stroke="black"/>
            
            <g transform="translate(0, 150)" font-family="Arial" font-size="14" font-weight="bold">
                <line x1="{-B*sc/2}" y1="0" x2="{B*sc/2}" y2="0" stroke="black" stroke-width="1.5"/>
                {tick(-B*sc/2,0)} {tick(-sx/2*sc,0)} {tick(-cb/2*sc,0)} {tick(cb/2*sc,0)} {tick(sx/2*sc,0)} {tick(B*sc/2,0)}
                <text x="0" y="25" text-anchor="middle">WIDTH: {int(B)}</text>
            </g>

            <g transform="translate({B*sc/2 + 60}, 0)" font-family="Arial" font-size="13" font-weight="bold">
                <line x1="0" y1="-150" x2="0" y2="{tp*sc + grout_h*sc}" stroke="black" stroke-width="1.2"/>
                {tick(0,-150)} {tick(0,0)} {tick(0,tp*sc)} {tick(0,tp*sc + grout_h*sc)}
                <text x="15" y="-75" text-anchor="start">COLUMN</text>
                <text x="15" y="{tp*sc/2 + 5}" text-anchor="start" fill="#1e40af">tp: {int(tp)}</text>
                <text x="15" y="{tp*sc + grout_h*sc/2 + 5}" text-anchor="start" fill="#64748b">GRT: {int(grout_h)}</text>
            </g>
        </g>

        <g transform="translate({bx}, {by})">
            <text x="0" y="-220" text-anchor="middle" font-weight="bold" font-size="22">SECTION B-B (SIDE VIEW)</text>
            <rect x="{-N*sc/2}" y="0" width="{N*sc}" height="{tp*sc}" fill="#f8fafc" stroke="black" stroke-width="2.5"/>
            <rect x="{-N*sc/2}" y="{tp*sc}" width="{N*sc}" height="{grout_h*sc}" fill="#f1f5f9" stroke="black" stroke-dasharray="2,2"/>
            <rect x="{-ch/2*sc}" y="-150" width="{ch*sc}" height="150" fill="#cbd5e1" stroke="black"/>
            
            <g transform="translate(0, 160)" font-family="Arial" font-size="14" font-weight="bold">
                <line x1="{-N*sc/2}" y1="0" x2="{N*sc/2}" y2="0" stroke="black" stroke-width="1.5"/>
                {tick(-N*sc/2,0)} {tick(-ch/2*sc,0)} {tick(ch/2*sc,0)} {tick(N*sc/2,0)}
                <text x="0" y="25" text-anchor="middle">DEPTH: {int(N)}</text>
            </g>

            <g transform="translate({N*sc/2 + 60}, 0)" font-family="Arial" font-size="13" font-weight="bold">
                <line x1="0" y1="-150" x2="0" y2="{tp*sc + grout_h*sc}" stroke="black" stroke-width="1.2"/>
                {tick(0,-150)} {tick(0,0)} {tick(0,tp*sc)} {tick(0,tp*sc + grout_h*sc)}
                <text x="15" y="{tp*sc/2 + 5}" text-anchor="start" fill="#1e40af">PLATE: {int(tp)}</text>
                <text x="15" y="{tp*sc + grout_h*sc/2 + 5}" text-anchor="start" fill="#64748b">GROUT: {int(grout_h)}</text>
            </g>
        </g>
        
        <g transform="translate(900, 1400)">
            <rect width="360" height="400" fill="none" stroke="black" stroke-width="2"/>
            <text x="15" y="40" font-family="sans-serif" font-weight="bold" font-size="22">BASE PLATE DESIGN</text>
            <line x1="0" y1="60" x2="360" y2="60" stroke="black" stroke-width="2"/>
            <text x="15" y="130" font-family="monospace" font-size="16">● COL: {col_name}</text>
            <text x="15" y="160" font-family="monospace" font-size="16">● PL: {int(tp)}x{int(B)}x{int(N)}</text>
            <rect x="0" y="320" width="360" height="80" fill="#1e293b"/>
            <text x="180" y="370" text-anchor="middle" fill="white" font-family="sans-serif" font-weight="bold" font-size="26">FINAL SHOP DRAWING</text>
        </g>

        <defs>
            <marker id="arrow" markerWidth="10" markerHeight="10" refX="0" refY="3" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0 L0,6 L9,3 z" fill="red" />
            </marker>
        </defs>
    </svg>
    """
