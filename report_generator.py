import streamlit as st
import streamlit.components.v1 as components

def get_connection_logic(res, p):
    # Logic ตามมาตรฐาน AISC 360-22
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
    
    # SVG Layout Engine (ป้องกันการทับซ้อน)
    c_w, c_h = 850, 700
    p_x, p_y = 300, 150 # จุดอ้างอิงหลัก
    bolt_x = p_x + conn['edge_h']
    
    bolt_svg = ""
    pitch_svg = ""
    for i in range(conn['rows']):
        by = p_y + conn['edge_v'] + (i * conn['pitch'])
        bolt_svg += f'<g transform="translate({bolt_x}, {by})"><circle r="7" fill="white" stroke="#000" stroke-width="1.5"/><path d="M-5-5L5 5M5-5L-5 5" stroke="#000" stroke-width="1.2"/></g>'
        if i < conn['rows'] - 1:
            mid_y = by + (conn['pitch']/2)
            # เส้นมิติระยะห่างโบลต์ (ย้ายออกไปขวาเพื่อไม่ทับ)
            pitch_svg += f'<line x1="{bolt_x + 60}" y1="{by}" x2="{bolt_x + 60}" y2="{by+conn["pitch"]}" stroke="#475569" marker-start="url(#arr)" marker-end="url(#arr)"/><text x="{bolt_x + 70}" y="{mid_y + 5}" font-size="12" font-family="monospace">{conn["pitch"]}mm</text>'

    html_content = f"""
    <div style="background:#f4f7f6; padding:50px; font-family:'Inter', sans-serif;">
        <div style="max-width:950px; margin:auto; background:white; padding:50px; border-radius:4px; box-shadow:0 30px 60px rgba(0,0,0,0.1); border-top:10px solid #0f172a;">
            
            <div style="display:flex; justify-content:space-between; margin-bottom:40px; border-bottom:2px solid #eee; padding-bottom:20px;">
                <div>
                    <h1 style="margin:0; font-size:24px; font-weight:900; color:#0f172a;">FIN-PLATE CONNECTION DESIGN</h1>
                    <p style="margin:5px 0; color:#64748b;">Member: {sec_name} | Grade: {steel_grade}</p>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:30px; font-weight:900; color:{'#059669' if util <= 100 else '#dc2626'};">{util:.1f}%</div>
                    <div style="font-size:12px; font-weight:bold; color:#94a3b8;">UTILIZATION RATIO</div>
                </div>
            </div>

            <div style="background:white; border:1px solid #e2e8f0; padding:20px; border-radius:8px;">
                <svg width="100%" height="{c_h}" viewBox="0 0 {c_w} {c_h}">
                    <defs>
                        <marker id="arr" markerWidth="10" markerHeight="10" refX="10" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#1e293b" /></marker>
                    </defs>

                    <rect x="{p_x - 30}" y="50" width="30" height="{c_h-100}" fill="#f8fafc" stroke="#cbd5e1"/>
                    <line x1="{p_x}" y1="80" x2="{c_w-50}" y2="80" stroke="#cbd5e1" stroke-dasharray="5,5"/>
                    <line x1="{p_x}" y1="{c_h-80}" x2="{c_w-50}" y2="{c_h-80}" stroke="#cbd5e1" stroke-dasharray="5,5"/>

                    <rect x="{p_x}" y="{p_y}" width="{conn['plate_w']}" height="{conn['plate_h']}" fill="none" stroke="#000" stroke-width="2"/>

                    <line x1="{p_x - 100}" y1="{p_y}" x2="{p_x - 100}" y2="{p_y + conn['plate_h']}" stroke="#000" marker-start="url(#arr)" marker-end="url(#arr)"/>
                    <text x="{p_x - 120}" y="{p_y + conn['plate_h']/2}" font-weight="900" transform="rotate(-90 {p_x - 120},{p_y + conn['plate_h']/2})">PLATE HEIGHT {conn['plate_h']} mm</text>

                    <line x1="{bolt_x + 60}" y1="{p_y}" x2="{bolt_x + 60}" y2="{p_y + conn['edge_v']}" stroke="#475569" marker-start="url(#arr)" marker-end="url(#arr)"/>
                    <text x="{bolt_x + 70}" y="{p_y + conn['edge_v']/2 + 5}" font-size="11">e_v={conn['edge_v']}mm</text>

                    <line x1="{p_x}" y1="{p_y - 40}" x2="{bolt_x}" y2="{p_y - 40}" stroke="#475569" marker-start="url(#arr)" marker-end="url(#arr)"/>
                    <text x="{p_x + 5}" y="{p_y - 50}" font-size="11">e_h={conn['edge_h']}mm</text>

                    <path d="M{bolt_x} {p_y + conn['edge_v']} L{bolt_x + 180} {p_y - 20}" fill="none" stroke="#94a3b8" stroke-width="0.8"/>
                    <text x="{bolt_x + 190}" y="{p_y - 20}" font-size="13" font-weight="bold">{conn['rows']} x {bolt.get('size','M20')} (Gr 8.8)</text>

                    <path d="M{p_x + conn['plate_w']} {p_y + conn['plate_h'] - 20} L{p_x + 220} {p_y + conn['plate_h'] + 30}" fill="none" stroke="#94a3b8" stroke-width="0.8"/>
                    <text x="{p_x + 230}" y="{p_y + conn['plate_h'] + 35}" font-size="13" font-weight="bold">PLATE: PL {conn['plate_t']} mm (SS400)</text>

                    <path d="M{p_x} {p_y + 40} L{p_x - 70} {p_y + 40}" fill="none" stroke="#ef4444" stroke-width="1.5"/>
                    <text x="{p_x - 130}" y="{p_y + 45}" font-size="14" font-weight="bold" fill="#ef4444">△ {conn['weld_size']} (TYP)</text>

                    {bolt_svg} {pitch_svg}
                </svg>
            </div>

            <div style="margin-top:40px; display:grid; grid-template-columns: 1fr 1fr; gap:30px; font-size:13px;">
                <div style="border:1px solid #f1f5f9; padding:20px;">
                    <h4 style="margin:0 0 15px; color:#0f172a;">LIMIT STATE CHECK (LRFD)</h4>
                    <div style="display:flex; justify-content:space-between; margin-bottom:8px;"><span>Shear Capacity (φVn):</span><b>{v_cap:,.0f} kg</b></div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:8px;"><span>Applied Shear (Vu):</span><b>{v_act:,.0f} kg</b></div>
                    <div style="height:6px; background:#eee; border-radius:10px; margin-top:10px;"><div style="width:{util}%; height:100%; background:#0f172a; border-radius:10px;"></div></div>
                </div>
                <div style="border:1px solid #f1f5f9; padding:20px; background:#fafafa;">
                    <h4 style="margin:0 0 15px; color:#0f172a;">SPECIFICATION</h4>
                    <p style="margin:4px 0;">• Bolts: M20 Grade 8.8 High Strength</p>
                    <p style="margin:4px 0;">• Plate: ASTM A36 / SS400 (Fy 2450)</p>
                    <p style="margin:4px 0;">• Weld: E70XX Electrodes (min size {conn['weld_size']}mm)</p>
                </div>
            </div>
        </div>
    </div>
    """
    components.html(html_content, height=1400, scrolling=True)
