import streamlit as st
import streamlit.components.v1 as components

def get_connection_logic(res, p):
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
    c_w, c_h = 950, 850
    p_x, p_y = 380, 220 
    bolt_x = p_x + conn['edge_h']
    
    # ---------------------------------------------------------
    # SVG Components Engine
    # ---------------------------------------------------------
    
    # 1. Bolts and Extension Lines
    bolt_svg = ""
    v_dim_svg = ""
    for i in range(conn['rows']):
        by = p_y + conn['edge_v'] + (i * conn['pitch'])
        bolt_svg += f'<g transform="translate({bolt_x}, {by})"><circle r="7" fill="white" stroke="#000" stroke-width="1.5"/><path d="M-5-5L5 5M5-5L-5 5" stroke="#000" stroke-width="1.2"/></g>'
        
        # Extension lines from bolts to dimension line
        v_dim_svg += f'<line x1="{bolt_x + 15}" y1="{by}" x2="{bolt_x + 85}" y2="{by}" stroke="#94a3b8" stroke-width="0.5" stroke-dasharray="2,2"/>'
        
        if i < conn['rows'] - 1:
            mid_y = by + (conn['pitch']/2)
            v_dim_svg += f"""
                <line x1="{bolt_x + 80}" y1="{by}" x2="{bolt_x + 80}" y2="{by+conn['pitch']}" stroke="#000" stroke-width="1"/>
                <line x1="{bolt_x + 75}" y1="{by+5}" x2="{bolt_x + 85}" y2="{by-5}" stroke="#000" stroke-width="1.5"/>
                <line x1="{bolt_x + 75}" y1="{by+conn['pitch']+5}" x2="{bolt_x + 85}" y2="{by+conn['pitch']-5}" stroke="#000" stroke-width="1.5"/>
                <text x="{bolt_x + 95}" y="{mid_y + 5}" font-size="12" font-family="monospace" font-weight="bold">{conn['pitch']}</text>
            """

    # 2. Advanced Welding Symbol (AWS Standard)
    # เราจะใช้ Leader Line แบบซิกแซ็กและ Tail เพื่อความโปร่งใส
    weld_symbol = f"""
        <g transform="translate({p_x}, {p_y + 60})">
            <path d="M 0 0 L -80 -40 L -180 -40" fill="none" stroke="#ef4444" stroke-width="1.5"/>
            <path d="M 0 0 L -12 -8 L -10 0 L -12 8 Z" fill="#ef4444"/> <text x="-175" y="-50" font-size="14" font-weight="900" fill="#ef4444">△ {conn['weld_size']}</text>
            <path d="M -180 -40 L -195 -55 M -180 -40 L -195 -25" fill="none" stroke="#ef4444" stroke-width="1.5"/> <text x="-240" y="-35" font-size="11" font-weight="bold" fill="#ef4444">TYP. BOTH SIDES</text>
        </g>
    """

    html_content = f"""
    <div style="background:#f1f5f9; padding:50px; font-family:'Inter', sans-serif;">
        <div style="max-width:1000px; margin:auto; background:white; padding:60px; border:1px solid #000; box-shadow:0 10px 30px rgba(0,0,0,0.05);">
            
            <div style="border:2px solid #000; padding:20px; margin-bottom:40px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h1 style="margin:0; font-size:24px; font-weight:900; text-transform:uppercase;">Technical Shop Drawing: Steel Connection</h1>
                    <p style="margin:5px 0; font-size:12px; font-weight:bold; color:#475569;">AISC 360-22 | CALCULATION ID: GI-2026-B1</p>
                </div>
                <div style="background:#0f172a; color:white; padding:15px; text-align:center; min-width:120px;">
                    <div style="font-size:10px;">UTILIZATION</div>
                    <div style="font-size:24px; font-weight:900;">{util:.1f}%</div>
                </div>
            </div>

            <div style="border:1px solid #cbd5e1; padding:10px; background:#fff;">
                <svg width="100%" height="{c_h}" viewBox="0 0 {c_w} {c_h}">
                    <line x1="{p_x}" y1="{p_y}" x2="{p_x - 120}" y2="{p_y}" stroke="#94a3b8" stroke-width="0.5" stroke-dasharray="4,2"/>
                    <line x1="{p_x}" y1="{p_y + conn['plate_h']}" x2="{p_x - 120}" y2="{p_y + conn['plate_h']}" stroke="#94a3b8" stroke-width="0.5" stroke-dasharray="4,2"/>
                    
                    <rect x="{p_x}" y="{p_y}" width="{conn['plate_w']}" height="{conn['plate_h']}" fill="none" stroke="#000" stroke-width="2.5"/>

                    <line x1="{p_x - 110}" y1="{p_y}" x2="{p_x - 110}" y2="{p_y + conn['plate_h']}" stroke="#000" stroke-width="1.2"/>
                    <line x1="{p_x-115}" y1="{p_y+5}" x2="{p_x-105}" y2="{p_y-5}" stroke="#000" stroke-width="2"/>
                    <line x1="{p_x-115}" y1="{p_y+conn['plate_h']+5}" x2="{p_x-105}" y2="{p_y+conn['plate_h']-5}" stroke="#000" stroke-width="2"/>
                    <text x="{p_x - 125}" y="{p_y + conn['plate_h']/2}" font-weight="900" font-size="14" transform="rotate(-90 {p_x - 125},{p_y + conn['plate_h']/2})" text-anchor="middle">TOTAL PLATE HT: {conn['plate_h']} mm</text>

                    {v_dim_svg}
                    {bolt_svg}
                    
                    <line x1="{p_x}" y1="{p_y-20}" x2="{p_x}" y2="{p_y-80}" stroke="#94a3b8" stroke-width="0.5" stroke-dasharray="2,2"/>
                    <line x1="{bolt_x}" y1="{p_y+conn['edge_v']}" x2="{bolt_x}" y2="{p_y-80}" stroke="#94a3b8" stroke-width="0.5" stroke-dasharray="2,2"/>
                    
                    <line x1="{p_x}" y1="{p_y-75}" x2="{bolt_x}" y2="{p_y-75}" stroke="#000" stroke-width="1"/>
                    <line x1="{p_x-5}" y1="{p_y-70}" x2="{p_x+5}" y2="{p_y-80}" stroke="#000" stroke-width="1.5"/>
                    <line x1="{bolt_x-5}" y1="{p_y-70}" x2="{bolt_x+5}" y2="{p_y-80}" stroke="#000" stroke-width="1.5"/>
                    <text x="{(p_x+bolt_x)/2}" y="{p_y-85}" font-size="12" font-weight="bold" text-anchor="middle">e_h={conn['edge_h']}</text>

                    {weld_symbol}

                    <text x="{p_x + conn['plate_w'] + 20}" y="{p_y + 10}" font-size="12" font-weight="bold" fill="#64748b">MATERIAL SPECIFICATION:</text>
                    <text x="{p_x + conn['plate_w'] + 20}" y="{p_y + 35}" font-size="14" font-weight="900">- FIN PL: {conn['plate_t']}mm (SS400)</text>
                    <text x="{p_x + conn['plate_w'] + 20}" y="{p_y + 55}" font-size="14" font-weight="900">- {conn['rows']}xM{conn['bolt_dia']} (GRADE 8.8)</text>
                </svg>
            </div>
            
            <div style="margin-top:20px; font-size:11px; color:#94a3b8; display:flex; justify-content:space-between; border-top:1px solid #eee; padding-top:10px;">
                <span>* ALL DIMENSIONS ARE IN MILLIMETERS (MM)</span>
                <span>ENGINEERED BY GEMINI 3 FLASH (WEB MODE)</span>
            </div>
        </div>
    </div>
    """
    components.html(html_content, height=1400, scrolling=True)
