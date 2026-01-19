import streamlit as st
import streamlit.components.v1 as components

def get_connection_logic(res, p):
    v_act = res.get('v_act', 0)
    h_beam = p.get('h', 0)
    # Professional calculation logic
    rows = max(2, int(v_act / 4400) + 1)
    pitch, edge_v, edge_h = 75, 40, 50
    plate_h = (rows - 1) * pitch + (2 * edge_v)
    plate_w = 110 # Increased for clarity
    return {
        "rows": rows, "pitch": pitch, "edge_v": edge_v, "edge_h": edge_h,
        "plate_h": int(plate_h), "plate_w": plate_w,
        "plate_t": 12, "weld_size": 6, "bolt_dia": 20, "bolt_grade": "8.8"
    }

def render_report_tab(method, is_lrfd, sec_name, steel_grade, p, res, bolt):
    conn = get_connection_logic(res, p)
    v_act, v_cap = res.get('v_act', 0), res.get('v_cap', 1)
    
    # --- SVG CANVAS CONFIG ---
    c_w, c_h = 850, 650
    # Central Reference Points
    p_x, p_y = 280, (c_h - conn['plate_h']) / 2
    bolt_x = p_x + conn['edge_h']
    
    bolt_svg = ""
    pitch_svg = ""
    for i in range(conn['rows']):
        by = p_y + conn['edge_v'] + (i * conn['pitch'])
        # Bolt Symbol (Industrial Grade)
        bolt_svg += f"""
        <g transform="translate({bolt_x}, {by})">
            <circle r="7" fill="white" stroke="#000" stroke-width="1.5"/>
            <path d="M-5-5L5 5M5-5L-5 5" stroke="#000" stroke-width="1.2"/>
        </g>"""
        # Pitch Dimensions (Positioned far right to avoid overlap)
        if i < conn['rows'] - 1:
            mid_y = by + (conn['pitch']/2)
            pitch_svg += f"""
            <line x1="{bolt_x + 80}" y1="{by}" x2="{bolt_x + 80}" y2="{by+conn['pitch']}" stroke="#475569" stroke-width="1" marker-start="url(#arr)" marker-end="url(#arr)"/>
            <text x="{bolt_x + 90}" y="{mid_y + 5}" font-size="12" font-family="monospace" font-weight="bold">{conn['pitch']} mm</text>
            """

    html_content = f"""
    <div style="background:#f0f2f5; padding:40px; font-family:'Inter', system-ui, sans-serif;">
        <div style="max-width:1000px; margin:auto; background:white; padding:60px; border-radius:8px; box-shadow:0 30px 60px rgba(0,0,0,0.12); border-left:12px solid #0f172a;">
            
            <div style="display:flex; justify-content:space-between; border-bottom:3px solid #0f172a; padding-bottom:20px; margin-bottom:40px;">
                <div>
                    <h1 style="margin:0; font-size:30px; font-weight:900; letter-spacing:-1px; color:#0f172a;">TECHNICAL DESIGN RECORD</h1>
                    <p style="margin:5px 0; color:#64748b; font-weight:600;">Standard Compliance: AISC 360-22 LRFD Edition</p>
                </div>
                <div style="text-align:right;">
                    <div style="background:{'#059669' if v_act/v_cap < 1 else '#dc2626'}; color:white; padding:12px 30px; border-radius:4px; font-size:22px; font-weight:900;">
                        { "APPROVED" if v_act/v_cap < 1 else "REJECTED" }
                    </div>
                </div>
            </div>

            <div style="background:#fff; border:2px solid #e2e8f0; border-radius:8px; padding:30px; position:relative; margin-bottom:40px;">
                <h3 style="position:absolute; top:15px; left:20px; font-size:12px; color:#94a3b8; letter-spacing:1px;">SHOP DRAWING / ELEVATION VIEW (N.T.S)</h3>
                <svg width="100%" height="{c_h}" viewBox="0 0 {c_w} {c_h}">
                    <defs>
                        <marker id="arr" markerWidth="10" markerHeight="10" refX="10" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#000" /></marker>
                    </defs>
                    
                    <rect x="{p_x - 30}" y="40" width="30" height="{c_h-80}" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5"/>
                    <text x="{p_x - 20}" y="30" font-size="11" fill="#94a3b8" font-weight="bold">MAIN COLUMN FACE</text>

                    <rect x="{p_x}" y="{p_y}" width="{conn['plate_w']}" height="{conn['plate_h']}" fill="#3b82f6" fill-opacity="0.04" stroke="#000" stroke-width="2.5"/>
                    
                    <line x1="{p_x}" y1="80" x2="{c_w-100}" y2="80" stroke="#cbd5e1" stroke-width="2" stroke-dasharray="8,4"/>
                    <line x1="{p_x}" y1="{c_h-80}" x2="{c_w-100}" y2="{c_h-80}" stroke="#cbd5e1" stroke-width="2" stroke-dasharray="8,4"/>

                    <line x1="{p_x - 80}" y1="{p_y}" x2="{p_x - 80}" y2="{p_y + conn['plate_h']}" stroke="#000" stroke-width="1.5" marker-start="url(#arr)" marker-end="url(#arr)"/>
                    <text x="{p_x - 100}" y="{p_y + conn['plate_h']/2}" font-weight="900" font-size="14" transform="rotate(-90 {p_x - 100},{p_y + conn['plate_h']/2})">PLATE HEIGHT: {conn['plate_h']} mm</text>

                    <line x1="{p_x}" y1="{p_y - 40}" x2="{bolt_x}" y2="{p_y - 40}" stroke="#475569" marker-start="url(#arr)" marker-end="url(#arr)"/>
                    <text x="{p_x + 5}" y="{p_y - 50}" font-size="12" font-weight="bold">e_h={conn['edge_h']}</text>

                    <line x1="{bolt_x + 80}" y1="{p_y}" x2="{bolt_x + 80}" y2="{p_y + conn['edge_v']}" stroke="#475569" marker-start="url(#arr)" marker-end="url(#arr)"/>
                    <text x="{bolt_x + 90}" y="{p_y + conn['edge_v']/2 + 5}" font-size="12" font-weight="bold">e_v={conn['edge_v']}</text>

                    <path d="M{bolt_x} {p_y + conn['edge_v']} L{bolt_x + 150} {p_y - 80} L{bolt_x + 200} {p_y - 80}" fill="none" stroke="#64748b" stroke-width="1"/>
                    <text x="{bolt_x + 155}" y="{p_y - 90}" font-size="13" font-weight="bold" fill="#1e293b">{conn['rows']} x {bolt.get('size','M20')} (Grade {conn['bolt_grade']})</text>

                    <path d="M{p_x + conn['plate_w']} {p_y + conn['plate_h'] - 20} L{p_x + 200} {p_y + conn['plate_h'] + 40} L{p_x + 250} {p_y + conn['plate_h'] + 40}" fill="none" stroke="#64748b" stroke-width="1"/>
                    <text x="{p_x + 205}" y="{p_y + conn['plate_h'] + 55}" font-size="13" font-weight="bold" fill="#1e293b">FIN PLATE: PL {conn['plate_t']}mm (SS400)</text>

                    {bolt_svg} {pitch_svg}
                    
                    <path d="M{p_x} {p_y + 40} L{p_x - 100} {p_y + 40}" fill="none" stroke="#ef4444" stroke-width="1.5"/>
                    <text x="{p_x - 160}" y="{p_y + 45}" font-size="14" font-weight="bold" fill="#ef4444">△ {conn['weld_size']} (TYP)</text>
                </svg>
            </div>

            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:40px; font-size:14px; border-top:2px solid #f1f5f9; padding-top:30px;">
                <div>
                    <h4 style="margin:0 0 15px; text-transform:uppercase; color:#64748b;">Engineering Data</h4>
                    <table style="width:100%; line-height:2.2;">
                        <tr><td>Member Profile</td><td style="text-align:right; font-weight:bold;">{sec_name}</td></tr>
                        <tr><td>Steel Grade</td><td style="text-align:right; font-weight:bold;">{steel_grade}</td></tr>
                        <tr><td>Max Reaction (Vu)</td><td style="text-align:right; font-weight:bold; color:#ef4444;">{v_act:,.0f} kg</td></tr>
                    </table>
                </div>
                <div>
                    <h4 style="margin:0 0 15px; text-transform:uppercase; color:#64748b;">Verification Status</h4>
                    <div style="background:#f8fafc; padding:15px; border-radius:4px;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                            <span>Bolt Shear Capacity</span><span style="font-weight:bold;">{v_cap:,.0f} kg</span>
                        </div>
                        <div style="width:100%; height:8px; background:#e2e8f0; border-radius:10px; overflow:hidden;">
                            <div style="width:{(v_act/v_cap*100):.1f}%; height:100%; background:#0f172a;"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    components.html(html_content, height=1400, scrolling=True)
