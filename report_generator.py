import streamlit as st
import streamlit.components.v1 as components

def get_connection_logic(res, p):
    # คำนวณตามมาตรฐาน AISC
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
    p_x, p_y = 350, 200 # จุดเริ่มวาด Plate
    bolt_x = p_x + conn['edge_h']
    
    # ส่วนประกอบของ Drawing
    bolt_svg = ""
    dim_svg = ""
    
    # วาด Bolts และระยะ Pitch (แนวตั้ง)
    for i in range(conn['rows']):
        by = p_y + conn['edge_v'] + (i * conn['pitch'])
        # ตัวโบลต์
        bolt_svg += f'<g transform="translate({bolt_x}, {by})"><circle r="7" fill="white" stroke="black" stroke-width="1.5"/><path d="M-5-5L5 5M5-5L-5 5" stroke="black" stroke-width="1"/></g>'
        
        # เส้นช่วยมิติ (Extension Lines) จากโบลต์
        dim_svg += f'<line x1="{bolt_x + 15}" y1="{by}" x2="{bolt_x + 75}" y2="{by}" stroke="#999" stroke-width="0.5"/>'
        
        if i < conn['rows'] - 1:
            mid_y = by + (conn['pitch'] / 2)
            # เส้นบอกระยะ Pitch
            dim_svg += f"""
                <line x1="{bolt_x + 70}" y1="{by}" x2="{bolt_x + 70}" y2="{by + conn['pitch']}" stroke="black" stroke-width="1"/>
                <line x1="{bolt_x + 65}" y1="{by + 5}" x2="{bolt_x + 75}" y2="{by - 5}" stroke="black" stroke-width="1.2"/>
                <line x1="{bolt_x + 65}" y1="{by + conn['pitch'] + 5}" x2="{bolt_x + 75}" y2="{by + conn['pitch'] - 5}" stroke="black" stroke-width="1.2"/>
                <text x="{bolt_x + 80}" y="{mid_y + 5}" font-size="12" font-weight="bold">{conn['pitch']}</text>
            """

    html_content = f"""
    <div style="background:#ffffff; padding:40px; font-family:'Helvetica', Arial, sans-serif;">
        <div style="max-width:900px; margin:auto; border:2px solid #000; padding:40px;">
            
            <div style="border-bottom:2px solid #000; padding-bottom:10px; margin-bottom:30px; display:flex; justify-content:space-between;">
                <div>
                    <h2 style="margin:0; text-transform:uppercase;">Connection Design Report</h2>
                    <span style="font-size:12px;">Standard: AISC 360-22 LRFD | Section: {sec_name}</span>
                </div>
                <div style="text-align:right;">
                    <span style="font-size:12px; font-weight:bold;">Status:</span>
                    <span style="color:{'green' if util <= 100 else 'red'}; font-weight:bold;">{'PASS' if util <= 100 else 'FAIL'} ({util:.1f}%)</span>
                </div>
            </div>

            <div style="text-align:center;">
                <svg width="{c_w}" height="{c_h}" viewBox="0 0 {c_w} {c_h}">
                    <rect x="{p_x}" y="{p_y}" width="{conn['plate_w']}" height="{conn['plate_h']}" fill="none" stroke="black" stroke-width="2"/>
                    
                    <line x1="{p_x}" y1="{p_y}" x2="{p_x - 80}" y2="{p_y}" stroke="#999" stroke-width="0.5"/>
                    <line x1="{p_x}" y1="{p_y + conn['plate_h']}" x2="{p_x - 80}" y2="{p_y + conn['plate_h']}" stroke="#999" stroke-width="0.5"/>
                    
                    <line x1="{p_x - 70}" y1="{p_y}" x2="{p_x - 70}" y2="{p_y + conn['plate_h']}" stroke="black" stroke-width="1"/>
                    <line x1="{p_x - 75}" y1="{p_y + 5}" x2="{p_x - 65}" y2="{p_y - 5}" stroke="black" stroke-width="1.2"/>
                    <line x1="{p_x - 75}" y1="{p_y + conn['plate_h'] + 5}" x2="{p_x - 65}" y2="{p_y + conn['plate_h'] - 5}" stroke="black" stroke-width="1.2"/>
                    <text x="{p_x - 90}" y="{p_y + conn['plate_h']/2}" transform="rotate(-90, {p_x - 90}, {p_y + conn['plate_h']/2})" text-anchor="middle" font-weight="bold">PL HT: {conn['plate_h']}</text>

                    <line x1="{p_x}" y1="{p_y - 80}" x2="{p_x + conn['plate_w']}" y2="{p_y - 80}" stroke="black" stroke-width="1"/>
                    <line x1="{p_x - 5}" y1="{p_y - 75}" x2="{p_x + 5}" y2="{p_y - 85}" stroke="black" stroke-width="1.2"/>
                    <line x1="{p_x + conn['plate_w'] - 5}" y1="{p_y - 75}" x2="{p_x + conn['plate_w'] + 5}" y2="{p_y - 85}" stroke="black" stroke-width="1.2"/>
                    <text x="{p_x + conn['plate_w']/2}" y="{p_y - 90}" text-anchor="middle" font-weight="bold">WIDTH: {conn['plate_w']}</text>

                    <line x1="{p_x}" y1="{p_y - 40}" x2="{bolt_x}" y2="{p_y - 40}" stroke="black" stroke-width="1"/>
                    <line x1="{p_x - 5}" y1="{p_y - 35}" x2="{p_x + 5}" y2="{p_y - 45}" stroke="black" stroke-width="1.2"/>
                    <line x1="{bolt_x - 5}" y1="{p_y - 35}" x2="{bolt_x + 5}" y2="{p_y - 45}" stroke="black" stroke-width="1.2"/>
                    <text x="{(p_x + bolt_x)/2}" y="{p_y - 50}" text-anchor="middle" font-size="11">e_h={conn['edge_h']}</text>

                    <line x1="{bolt_x + 70}" y1="{p_y}" x2="{bolt_x + 70}" y2="{p_y + conn['edge_v']}" stroke="black" stroke-width="1"/>
                    <line x1="{bolt_x + 65}" y1="{p_y + 5}" x2="{bolt_x + 75}" y2="{p_y - 5}" stroke="black" stroke-width="1.2"/>
                    <line x1="{bolt_x + 65}" y1="{p_y + conn['edge_v'] + 5}" x2="{bolt_x + 75}" y2="{p_y + conn['edge_v'] - 5}" stroke="black" stroke-width="1.2"/>
                    <text x="{bolt_x + 80}" y="{p_y + conn['edge_v']/2 + 5}" font-size="11">e_v={conn['edge_v']}</text>

                    <path d="M {p_x} {p_y+60} L {p_x-50} {p_y+100} L {p_x-120} {p_y+100}" fill="none" stroke="red" stroke-width="1.5"/>
                    <text x="-120" y="90" transform="translate({p_x}, {p_y})" fill="red" font-weight="bold" font-size="14">△ {conn['weld_size']}</text>

                    {dim_svg}
                    {bolt_svg}
                    
                    <text x="{p_x + conn['plate_w'] + 20}" y="{p_y + 120}" font-size="12">
                        <tspan x="{p_x + conn['plate_w'] + 20}" dy="1.2em">BOLTS: {conn['rows']} x M{conn['bolt_dia']} (8.8)</tspan>
                        <tspan x="{p_x + conn['plate_w'] + 20}" dy="1.2em">PLATE: PL {conn['plate_t']} mm (SS400)</tspan>
                    </text>
                </svg>
            </div>

            <div style="margin-top:20px;">
                <table style="width:100%; border-collapse: collapse; font-size:13px;">
                    <tr style="background:#eee;">
                        <th style="border:1px solid #000; padding:8px;">Component</th>
                        <th style="border:1px solid #000; padding:8px;">Description</th>
                        <th style="border:1px solid #000; padding:8px;">Material</th>
                    </tr>
                    <tr>
                        <td style="border:1px solid #000; padding:8px;">Fin Plate</td>
                        <td style="border:1px solid #000; padding:8px;">{conn['plate_h']} x {conn['plate_w']} x {conn['plate_t']} mm</td>
                        <td style="border:1px solid #000; padding:8px;">ASTM A36 / SS400</td>
                    </tr>
                </table>
            </div>
        </div>
    </div>
    """
    components.html(html_content, height=1400, scrolling=True)
