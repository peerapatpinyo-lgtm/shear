import streamlit as st
import streamlit.components.v1 as components

def get_connection_logic(res, p):
    # มาตรฐานวิศวกรรมสากล
    v_act = res.get('v_act', 0)
    rows = max(2, int(v_act / 4400) + 1)
    pitch, edge_v, edge_h = 75, 40, 50
    plate_h = (rows - 1) * pitch + (2 * edge_v)
    plate_w = 110 
    return {
        "rows": rows, "pitch": pitch, "edge_v": edge_v, "edge_h": edge_h,
        "plate_h": int(plate_h), "plate_w": plate_w,
        "plate_t": 12, "weld_size": 6, "bolt_dia": 20, "bolt_grade": "8.8"
    }

def render_report_tab(method, is_lrfd, sec_name, steel_grade, p, res, bolt):
    conn = get_connection_logic(res, p)
    v_act, v_cap = res.get('v_act', 0), res.get('v_cap', 1)
    util = (v_act / v_cap) * 100
    
    # SVG Configuration
    c_w, c_h = 900, 800
    p_x, p_y = 350, 200 # Main Plate Start
    bolt_x = p_x + conn['edge_h']
    
    # ---------------------------------------------------------
    # Building SVG Components
    # ---------------------------------------------------------
    
    # 1. Bolts and Vertical Pitch Dimensions (Architecture Ticks)
    bolt_svg = ""
    v_dim_svg = ""
    for i in range(conn['rows']):
        by = p_y + conn['edge_v'] + (i * conn['pitch'])
        # Bolt Symbol
        bolt_svg += f'<g transform="translate({bolt_x}, {by})"><circle r="7" fill="white" stroke="#000" stroke-width="1.5"/><path d="M-5-5L5 5M5-5L-5 5" stroke="#000" stroke-width="1.2"/></g>'
        
        # Vertical Pitch Lines (Far Right)
        if i < conn['rows'] - 1:
            mid_y = by + (conn['pitch']/2)
            v_dim_svg += f"""
                <line x1="{bolt_x + 80}" y1="{by}" x2="{bolt_x + 80}" y2="{by+conn['pitch']}" stroke="#000" stroke-width="1"/>
                <line x1="{bolt_x + 75}" y1="{by+5}" x2="{bolt_x + 85}" y2="{by-5}" stroke="#000" stroke-width="1.5"/> <line x1="{bolt_x + 75}" y1="{by+conn['pitch']+5}" x2="{bolt_x + 85}" y2="{by+conn['pitch']-5}" stroke="#000" stroke-width="1.5"/> <text x="{bolt_x + 90}" y="{mid_y + 5}" font-size="12" font-family="monospace" font-weight="bold">{conn['pitch']}</text>
            """

    # 2. Complete Plate Dimensions (All Edges)
    plate_dims = f"""
        <line x1="{p_x}" y1="{p_y - 60}" x2="{bolt_x}" y2="{p_y - 60}" stroke="#000" stroke-width="1"/>
        <line x1="{p_x-5}" y1="{p_y-55}" x2="{p_x+5}" y2="{p_y-65}" stroke="#000" stroke-width="1.5"/> <line x1="{bolt_x-5}" y1="{p_y-55}" x2="{bolt_x+5}" y2="{p_y-65}" stroke="#000" stroke-width="1.5"/> <text x="{(p_x+bolt_x)/2}" y="{p_y-70}" font-size="12" font-weight="bold" text-anchor="middle">e_h={conn['edge_h']}</text>

        <line x1="{p_x}" y1="{p_y - 100}" x2="{p_x + conn['plate_w']}" y2="{p_y - 100}" stroke="#000" stroke-width="1"/>
        <line x1="{p_x-5}" y1="{p_y-95}" x2="{p_x+5}" y2="{p_y-105}" stroke="#000" stroke-width="1.5"/>
        <line x1="{p_x+conn['plate_w']-5}" y1="{p_y-95}" x2="{p_x+conn['plate_w']+5}" y2="{p_y-105}" stroke="#000" stroke-width="1.5"/>
        <text x="{p_x + conn['plate_w']/2}" y="{p_y-110}" font-size="12" font-weight="900" text-anchor="middle">PLATE WIDTH: {conn['plate_w']}</text>

        <line x1="{bolt_x + 80}" y1="{p_y}" x2="{bolt_x + 80}" y2="{p_y + conn['edge_v']}" stroke="#000" stroke-width="1"/>
        <line x1="{bolt_x+75}" y1="{p_y+5}" x2="{bolt_x+85}" y2="{p_y-5}" stroke="#000" stroke-width="1.5"/>
        <line x1="{bolt_x+75}" y1="{p_y+conn['edge_v']+5}" x2="{bolt_x+85}" y2="{p_y+conn['edge_v']-5}" stroke="#000" stroke-width="1.5"/>
        <text x="{bolt_x + 90}" y="{p_y + conn['edge_v']/2 + 5}" font-size="11">e_v={conn['edge_v']}</text>
    """

    html_content = f"""
    <div style="background:#f1f5f9; padding:50px; font-family:'Inter', sans-serif;">
        <div style="max-width:1000px; margin:auto; background:white; padding:60px; border-radius:2px; box-shadow:0 50px 100px rgba(0,0,0,0.1); border:1px solid #e2e8f0;">
            
            <div style="border-bottom:4px solid #0f172a; padding-bottom:20px; margin-bottom:40px; display:flex; justify-content:space-between; align-items:flex-end;">
                <div>
                    <h1 style="margin:0; font-size:28px; font-weight:900; color:#0f172a; letter-spacing:-1px;">SHOP DRAWING: FIN-PLATE DETAIL</h1>
                    <p style="margin:5px 0; color:#64748b; font-weight:bold;">AISC 360-22 LRFD METHOD | FOR CONSTRUCTION</p>
                </div>
                <div style="text-align:right; font-family:monospace;">
                    <div style="font-size:14px; color:#94a3b8;">UTILIZATION RATIO</div>
                    <div style="font-size:35px; font-weight:900; color:{'#059669' if util <= 100 else '#dc2626'};">{util:.1f}%</div>
                </div>
            </div>

            <div style="position:relative; background:#fff; padding:20px; border:1px solid #f1f5f9;">
                <svg width="100%" height="{c_h}" viewBox="0 0 {c_w} {c_h}">
                    <rect x="{p_x - 20}" y="50" width="20" height="{c_h-100}" fill="#f8fafc" stroke="#cbd5e1"/>
                    
                    <rect x="{p_x}" y="{p_y}" width="{conn['plate_w']}" height="{conn['plate_h']}" fill="none" stroke="#000" stroke-width="2.5"/>

                    <line x1="{p_x - 100}" y1="{p_y}" x2="{p_x - 100}" y2="{p_y + conn['plate_h']}" stroke="#000" stroke-width="1.2"/>
                    <line x1="{p_x-105}" y1="{p_y+5}" x2="{p_x-95}" y2="{p_y-5}" stroke="#000" stroke-width="2"/> <line x1="{p_x-105}" y1="{p_y+conn['plate_h']+5}" x2="{p_x-95}" y2="{p_y+conn['plate_h']-5}" stroke="#000" stroke-width="2"/> <text x="{p_x - 115}" y="{p_y + conn['plate_h']/2}" font-weight="900" font-size="15" transform="rotate(-90 {p_x - 115},{p_y + conn['plate_h']/2})" text-anchor="middle">PL HEIGHT: {conn['plate_h']} mm</text>

                    {plate_dims}
                    {bolt_svg}
                    {v_dim_svg}

                    <path d="M{bolt_x} {p_y + conn['edge_v']} L{bolt_x + 220} {p_y - 20} L{bolt_x + 300} {p_y - 20}" fill="none" stroke="#64748b" stroke-width="1"/>
                    <text x="{bolt_x + 220}" y="{p_y - 30}" font-size="13" font-weight="900">{conn['rows']} x M{conn['bolt_dia']} BOLTS (GRADE {conn['bolt_grade']})</text>

                    <path d="M{p_x + conn['plate_w']} {p_y + conn['plate_h'] - 20} L{p_x + 250} {p_y + conn['plate_h'] + 40} L{p_x + 350} {p_y + conn['plate_h'] + 40}" fill="none" stroke="#64748b" stroke-width="1"/>
                    <text x="{p_x + 255}" y="{p_y + conn['plate_h'] + 55}" font-size="13" font-weight="900">PLATE: PL {conn['plate_t']}mm (SS400 / A36)</text>

                    <path d="M{p_x} {p_y + 40} L{p_x - 120} {p_y + 40}" fill="none" stroke="#ef4444" stroke-width="2"/>
                    <text x="{p_x - 120}" y="{p_y + 30}" font-size="14" font-weight="900" fill="#ef4444">△ {conn['weld_size']} (TYP)</text>
                    
                    <text x="20" y="{c_h-20}" font-size="12" font-weight="bold" fill="#94a3b8">SCALE: N.T.S | DIMENSIONS IN MM</text>
                </svg>
            </div>

            <div style="margin-top:40px; display:grid; grid-size: 1fr 1fr; grid-template-columns: 1fr 1fr; gap:30px;">
                <div style="border:1.5px solid #0f172a; padding:25px;">
                    <h4 style="margin:0 0 15px; background:#0f172a; color:white; padding:5px 10px; display:inline-block;">BILL OF MATERIALS</h4>
                    <table style="width:100%; font-size:13px; line-height:1.8;">
                        <tr><td>Plate Thickness:</td><td style="text-align:right;"><b>{conn['plate_t']} mm</b></td></tr>
                        <tr><td>Bolt Size/Grade:</td><td style="text-align:right;"><b>M{conn['bolt_dia']} / 8.8</b></td></tr>
                        <tr><td>Weld Size:</td><td style="text-align:right; color:#ef4444;"><b>{conn['weld_size']} mm Fillet</b></td></tr>
                    </table>
                </div>
                <div style="background:#f8fafc; padding:25px; border:1px solid #e2e8f0;">
                    <h4 style="margin:0 0 15px; color:#64748b; font-size:12px; letter-spacing:1px; text-transform:uppercase;">Engineering Note</h4>
                    <p style="font-size:12px; color:#475569; margin:0;">1. All holes shall be standard size (Dia + 2mm) unless noted.<br>2. Welders must be certified for 2G position.<br>3. Verify all dimensions at shop before cutting.</p>
                </div>
            </div>
        </div>
    </div>
    """
    components.html(html_content, height=1500, scrolling=True)
