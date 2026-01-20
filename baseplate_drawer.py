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
    
    # --- Settings ---
    cv_w, cv_h = 1250, 1350
    sc = 420 / max(N, B)  
    px, py = 450, 400 
    ax, ay = 450, 1000 
    
    # Hole diameter typically bolt_d + 3mm for baseplates
    hole_d = bolt_d + 3

    def tick(x, y): return f'<line x1="{x-6}" y1="{y+6}" x2="{x+6}" y2="{y-6}" stroke="black" stroke-width="1.2"/>'

    return f"""
    <svg width="{cv_w}" height="{cv_h}" viewBox="0 0 {cv_w} {cv_h}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#ffffff" stroke="#1e293b" stroke-width="2"/>
        
        <g transform="translate(880, 880)">
            <rect width="340" height="420" fill="none" stroke="black" stroke-width="2"/>
            <text x="10" y="35" font-family="sans-serif" font-weight="bold" font-size="20">PROJECT: BASE PLATE DESIGN</text>
            <line x1="0" y1="50" x2="340" y2="50" stroke="black"/>
            <text x="10" y="75" font-family="sans-serif" font-weight="bold" font-size="14">FABRICATION NOTES:</text>
            <text x="10" y="100" font-family="sans-serif" font-size="12">- HOLE DIA: Ø{hole_d} mm (FOR M{bolt_d} BOLT)</text>
            <text x="10" y="120" font-family="sans-serif" font-size="12">- WELDING: FILLET WELD E70XX 8mm (ALL AROUND)</text>
            <text x="10" y="140" font-family="sans-serif" font-size="12">- PLATE GRADE: ASTM A36 / SS400</text>
            <text x="10" y="160" font-family="sans-serif" font-size="12">- TOLERANCE: +/- 2.0 mm</text>
            
            <line x1="0" y1="180" x2="340" y2="180" stroke="black"/>
            <text x="10" y="210" font-family="monospace" font-size="14" fill="#1e40af">● COL: {col_name}</text>
            <text x="10" y="235" font-family="monospace" font-size="14" fill="#1e40af">● PL: {int(tp)}x{int(B)}x{int(N)}</text>
            
            <rect x="0" y="340" width="340" height="80" fill="#1e293b"/>
            <text x="170" y="390" text-anchor="middle" fill="white" font-family="sans-serif" font-weight="bold" font-size="24">READY FOR FAB</text>
        </g>

        <g transform="translate({px}, {py})">
            <text x="0" y="{-N*sc/2 - 140}" text-anchor="middle" font-weight="bold" font-size="22">PLAN VIEW (TOP)</text>
            
            <line x1="{-B*sc/2 - 40}" y1="0" x2="{B*sc/2 + 40}" y2="0" stroke="#94a3b8" stroke-dasharray="10,5,2,5"/>
            <line x1="0" y1="{-N*sc/2 - 40}" x2="0" y2="{N*sc/2 + 40}" stroke="#94a3b8" stroke-dasharray="10,5,2,5"/>
            
            <rect x="{-B*sc/2}" y="{-N*sc/2}" width="{B*sc}" height="{N*sc}" fill="#f8fafc" stroke="black" stroke-width="3"/>
            
            <g fill="#cbd5e1" stroke="black" stroke-width="1.5">
                <rect x="{-cb/2*sc}" y="{-ch/2*sc}" width="{cb*sc}" height="{ctf*sc}"/> 
                <rect x="{-cb/2*sc}" y="{(ch/2-ctf)*sc}" width="{cb*sc}" height="{ctf*sc}"/>
                <rect x="{-ctw/2*sc}" y="{-ch/2*sc+ctf*sc}" width="{ctw*sc}" height="{(ch-2*ctf)*sc}"/>
            </g>

            <g fill="white" stroke="#2563eb" stroke-width="2.5">
                <circle cx="{-sx/2*sc}" cy="{-sy/2*sc}" r="{hole_d/2*sc}"/>
                <circle cx="{sx/2*sc}"  cy="{-sy/2*sc}" r="{hole_d/2*sc}"/>
                <circle cx="{-sx/2*sc}" cy="{sy/2*sc}"  r="{hole_d/2*sc}"/>
                <circle cx="{sx/2*sc}"  cy="{sy/2*sc}"  r="{hole_d/2*sc}"/>
            </g>
            <text x="{sx/2*sc + 15}" y="{-sy/2*sc - 15}" font-size="11" font-weight="bold" fill="#2563eb">4-Ø{hole_d} HOLES</text>

            <path d="M {cb/2*sc} {-ch/4*sc} L {cb/2*sc + 40} {-ch/4*sc - 30}" fill="none" stroke="black"/>
            <text x="{cb/2*sc + 45}" y="{-ch/4*sc - 35}" font-size="10">FW 8mm</text>

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
                <text x="-20" y="0" transform="rotate(-90, -20, 0)" text-anchor="middle">{int(ch)}</text>
            </g>
        </g>

        <g transform="translate({ax}, {ay})">
            <text x="0" y="-220" text-anchor="middle" font-weight="bold" font-size="20">SECTION A-A (FRONT VIEW)</text>
            
            <rect x="{-B*sc/2 - 40}" y="{tp*sc + grout_h*sc}" width="{B*sc + 80}" height="60" fill="#e2e8f0" stroke="#64748b" stroke-dasharray="4,2"/>
            <rect x="{-B*sc/2}" y="{tp*sc}" width="{B*sc}" height="{grout_h*sc}" fill="#f1f5f9" stroke="black"/>
            
            <rect x="{-B*sc/2}" y="0" width="{B*sc}" height="{tp*sc}" fill="white" stroke="black" stroke-width="2.5"/>
            
            <rect x="{-cb/2*sc}" y="-150" width="{cb*sc}" height="150" fill="#cbd5e1" stroke="black"/>
            
            <g stroke="#2563eb" stroke-width="3" fill="none">
                <line x1="{-sx/2*sc}" y1="-40" x2="{-sx/2*sc}" y2="200"/>
                <path d="M {-sx/2*sc} 200 L {-sx/2*sc - 30} 230"/> <line x1="{sx/2*sc}" y1="-40" x2="{sx/2*sc}" y2="200"/>
                <path d="M {sx/2*sc} 200 L {sx/2*sc + 30} 230"/> </g>

            <g transform="translate({B*sc/2 + 60}, 0)" font-family="Arial" font-size="12" font-weight="bold">
                <line x1="0" y1="-150" x2="0" y2="{tp*sc + grout_h*sc}" stroke="black"/>
                {tick(0,-150)} {tick(0,0)} {tick(0,tp*sc)} {tick(0,tp*sc + grout_h*sc)}
                <text x="15" y="{tp*sc/2}" transform="rotate(90, 15, {tp*sc/2})" text-anchor="middle" fill="#1e40af">PL THK:{int(tp)}</text>
                <text x="15" y="{tp*sc + grout_h*sc/2}" transform="rotate(90, 15, {tp*sc + grout_h*sc/2})" text-anchor="middle" fill="#64748b">GROUT:{int(grout_h)}</text>
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
