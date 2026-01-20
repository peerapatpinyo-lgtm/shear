def get_svg_drawing(params):
    # --- ดึงข้อมูล ---
    B, N = params['B'], params['N']
    cb, ch = params['cb'], params['ch']
    ctw, ctf = params['ctw'], params['ctf']
    sx, sy = params['sx'], params['sy']
    tp, grout_h = params['tp'], params['grout_h']
    edge_x, edge_y = params['edge_x'], params['edge_y']
    clr_x, clr_y = params['clr_x'], params['clr_y']
    col_name, bolt_d = params['col_name'], params['bolt_d']
    
    cv_w, cv_h = 1350, 1500
    sc = 400 / max(N, B)  
    px, py = 450, 380  # Plan
    ax, ay = 450, 950  # Section A-A (Front)
    bx, by = 450, 1300 # Section B-B (Side) - ปรับตำแหน่งให้ชัด

    def tick(x, y): return f'<line x1="{x-6}" y1="{y+6}" x2="{x+6}" y2="{y-6}" stroke="black" stroke-width="1.2"/>'

    return f"""
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#ffffff"/>

        <g transform="translate({px}, {py})">
            <text x="0" y="{-N*sc/2 - 100}" text-anchor="middle" font-weight="bold" font-size="22">PLAN VIEW</text>
            <rect x="{-B*sc/2}" y="{-N*sc/2}" width="{B*sc}" height="{N*sc}" fill="none" stroke="black" stroke-width="2"/>
            </g>

        <g transform="translate({ax}, {ay})">
            <text x="0" y="-180" text-anchor="middle" font-weight="bold" font-size="20">SECTION A-A (FRONT VIEW)</text>
            <rect x="{-B*sc/2}" y="0" width="{B*sc}" height="{tp*sc}" fill="#f8fafc" stroke="black" stroke-width="2"/>
            <rect x="{-cb/2*sc}" y="-120" width="{cb*sc}" height="120" fill="#cbd5e1" stroke="black"/>
        </g>

        <g transform="translate({bx}, {by})">
            <text x="0" y="-220" text-anchor="middle" font-weight="bold" font-size="20">SECTION B-B (SIDE VIEW)</text>
            
            <rect x="{-N*sc/2}" y="0" width="{N*sc}" height="{tp*sc}" fill="#f8fafc" stroke="black" stroke-width="2"/>
            <rect x="{-N*sc/2}" y="{tp*sc}" width="{N*sc}" height="{grout_h*sc}" fill="#f1f5f9" stroke="black" stroke-dasharray="2,2"/>
            
            <rect x="{-ch/2*sc}" y="-150" width="{ch*sc}" height="150" fill="#cbd5e1" stroke="black"/>
            <line x1="{-ch/2*sc + ctf*sc}" y1="-150" x2="{-ch/2*sc + ctf*sc}" y2="0" stroke="black" stroke-width="1" stroke-dasharray="4,2"/>
            <line x1="{ch/2*sc - ctf*sc}" y1="-150" x2="{ch/2*sc - ctf*sc}" y2="0" stroke="black" stroke-width="1" stroke-dasharray="4,2"/>

            <g transform="translate(0, 160)" font-family="Arial" font-size="13" font-weight="bold">
                <line x1="{-N*sc/2}" y1="0" x2="{N*sc/2}" y2="0" stroke="black" stroke-width="1.2"/>
                {tick(-N*sc/2,0)} {tick(-sy/2*sc,0)} {tick(-ch/2*sc,0)} {tick(ch/2*sc,0)} {tick(sy/2*sc,0)} {tick(N*sc/2,0)}
                <text x="{-sy/2*sc - edge_y*sc/2}" y="20" text-anchor="middle" fill="green">{int(edge_y)}</text>
                <text x="{-ch/2*sc - clr_y*sc/2}" y="20" text-anchor="middle" fill="red">{int(clr_y)}</text>
                <text x="0" y="20" text-anchor="middle">DEPTH:{int(ch)}</text>
                <text x="{ch/2*sc + clr_y*sc/2}" y="20" text-anchor="middle" fill="red">{int(clr_y)}</text>
                <text x="{sy/2*sc + edge_y*sc/2}" y="20" text-anchor="middle" fill="green">{int(edge_y)}</text>
            </g>

            <g transform="translate({N*sc/2 + 60}, 0)" font-family="Arial" font-size="12" font-weight="bold">
                <line x1="0" y1="-150" x2="0" y2="{tp*sc + grout_h*sc}" stroke="black" stroke-width="1.2"/>
                {tick(0,-150)} {tick(0,0)} {tick(0,tp*sc)} {tick(0,tp*sc + grout_h*sc)}
                
                <text x="15" y="-75" text-anchor="start">COL HEIGHT</text>
                <text x="15" y="{tp*sc/2 + 5}" text-anchor="start" fill="#1e40af">PLATE: {int(tp)} mm</text>
                <text x="15" y="{tp*sc + grout_h*sc/2 + 5}" text-anchor="start" fill="#64748b">GROUT: {int(grout_h)} mm</text>
                
                <line x1="80" y1="0" x2="80" y2="{tp*sc + grout_h*sc}" stroke="black" stroke-width="1"/>
                {tick(80,0)} {tick(80, tp*sc+grout_h*sc)}
                <text x="90" y="{(tp*sc + grout_h*sc)/2 + 5}" text-anchor="start">SUM: {int(tp + grout_h)}</text>
            </g>
        </g>
        
        <g transform="translate(900, 1050)">
            <rect width="360" height="380" fill="none" stroke="black" stroke-width="2"/>
            <text x="15" y="40" font-family="sans-serif" font-weight="bold" font-size="22">BASE PLATE DRAWING</text>
            <line x1="0" y1="60" x2="360" y2="60" stroke="black"/>
            <text x="15" y="100" font-family="monospace" font-size="15">COLUMN: {col_name}</text>
            <text x="15" y="130" font-family="monospace" font-size="15">PLATE: {int(tp)}x{int(B)}x{int(N)}</text>
        </g>
    </svg>
    """
