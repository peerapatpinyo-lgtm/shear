import streamlit as st
import streamlit.components.v1 as components

def get_connection_logic(res, p):
    # มาตรฐาน AISC 360-22 สำหรับงานระดับสากล
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
    
    # SVG Engine: จัดระเบียบพิกัดใหม่ทั้งหมดเพื่อเลี่ยงการทับซ้อน
    c_w, c_h = 850, 750
    p_x, p_y = 320, 180 # ย้ายชิ้นงานมาขวานิดหน่อยเพื่อให้พื้นที่ด้านซ้ายบอกระยะได้เต็มที่
    bolt_x = p_x + conn['edge_h']
    
    bolt_svg = ""
    pitch_svg = ""
    for i in range(conn['rows']):
        by = p_y + conn['edge_v'] + (i * conn['pitch'])
        bolt_svg += f'<g transform="translate({bolt_x}, {by})"><circle r="7" fill="white" stroke="#000" stroke-width="1.5"/><path d="M-5-5L5 5M5-5L-5 5" stroke="#000" stroke-width="1.2"/></g>'
        if i < conn['rows'] - 1:
            mid_y = by + (conn['pitch']/2)
            # ระยะ Pitch วางห่างจากขอบแผ่นเหล็ก 60px
            pitch_svg += f'<line x1="{bolt_x + 60}" y1="{by}" x2="{bolt_x + 60}" y2="{by+conn["pitch"]}" stroke="#475569" marker-start="url(#arr)" marker-end="url(#arr)"/><text x="{bolt_x + 70}" y="{mid_y + 5}" font-size="12" font-family="monospace" font-weight="bold">{conn["pitch"]}mm</text>'

    html_content = f"""
    <div style="background:#f8fafc; padding:40px; font-family:'Inter', sans-serif;">
        <div style="max-width:980px; margin:auto; background:white; padding:60px; border-radius:4px; box-shadow:0 40px 80px rgba(0,0,0,0.1); border-left:15px solid #0f172a;">
            
            <div style="display:flex; justify-content:space-between; border-bottom:3px solid #0f172a; padding-bottom:20px; margin-bottom:40px;">
                <div>
                    <h1 style="margin:0; font-size:26px; font-weight:900; color:#0f172a; text-transform:uppercase;">Construction Detail: Fin-Plate Connection</h1>
                    <p style="margin:5px 0; color:#64748b; font-weight:bold;">Project: Structural Analysis Report | Ref: AISC-360</p>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:32px; font-weight:900; color:{'#059669' if util <= 100 else '#dc2626'};">{util:.1f}%</div>
                    <div style="font-size:11px; font-weight:bold; color:#94a3b8; letter-spacing:1px;">UTILIZATION</div>
                </div>
            </div>

            <div style="background:white; border:1px solid #e2e8f0; padding:20px; border-radius:4px; margin-bottom:40px;">
                <svg width="100%" height="{c_h}" viewBox="0 0 {c_w} {c_h}">
                    <defs>
                        <marker id="arr" markerWidth="8" markerHeight="8" refX="8" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#1e293b" /></marker>
                    </defs>

                    <rect x="{p_x - 30}" y="60" width="30" height="{c_h-120}" fill="#f1f5f9" stroke="#cbd5e1"/>
                    <line x1="{p_x}" y1="100" x2="{c_w-50}" y2="100" stroke="#cbd5e1" stroke-dasharray="8,4"/>
                    <line x1="{p_x}" y1="{c_h-100}" x2="{c_w-50}" y2="{c_h-100}" stroke="#cbd5e1" stroke-dasharray="8,4"/>

                    <rect x="{p_x}" y="{p_y}" width="{conn['plate_w']}" height="{conn['plate_h']}" fill="#f0f7ff" stroke="#0f172a" stroke-width="2.5"/>

                    <line x1="{p_x - 120}" y1="{p_y}" x2="{p_x - 120}" y2="{p_y + conn['plate_h']}" stroke="#0f172a" stroke-width="1.2" marker-start="url(#arr)" marker-end="url(#arr)"/>
                    <text x="{p_x - 140}" y="{p_y + conn['plate_h']/2}" font-weight="900" font-size="14" transform="rotate(-90 {p_x - 140},{p_y + conn['plate_h']/2})" text-anchor="middle">PLATE HEIGHT: {conn['plate_h']} mm</text>

                    <line x1="{bolt_x + 60}" y1="{p_y}" x2="{bolt_x + 60}" y2="{p_y + conn['edge_v']}" stroke="#475569" marker-start="url(#arr)" marker-end="url(#arr)"/>
                    <text x="{bolt_x + 70}" y="{p_y + conn['edge_v']/2 + 5}" font-size="12" font-weight="bold">e_v = {conn['edge_v']}</text>

                    <line x1="{p_x}" y1="{p_y - 40}" x2="{bolt_x}" y2="{p_y - 40}" stroke="#475569" marker-start="url(#arr)" marker-end="url(#arr)"/>
                    <text x="{(p_x + bolt_x)/2}" y="{p_y - 50}" font-size="12" font-weight="bold" text-anchor="middle">e_h = {conn['edge_h']}</text>

                    <path d="M{bolt_x} {p_y + conn['edge_v']} L{bolt_x + 180} {p_y - 60} L{bolt_x + 250} {p_y - 60}" fill="none" stroke="#94a3b8" stroke-width="1"/>
                    <text x="{bolt_x + 185}" y="{p_y - 70}" font-size="13" font-weight="900" fill="#1e293b">{conn['rows']} x M{conn['bolt_dia']} (Gr {conn['bolt_grade']})</text>

                    <path d="M{p_x + conn['plate_w']} {p_y + conn['plate_h'] - 20} L{p_x + 220} {p_y + conn['plate_h'] + 40} L{p_x + 300} {p_y + conn['plate_h'] + 40}" fill="none" stroke="#94a3b8" stroke-width="1"/>
                    <text x="{p_x + 225}" y="{p_y + conn['plate_h'] + 55}" font-size="13" font-weight="900" fill="#1e293b">FIN PLATE: PL {conn['plate_t']} mm (SS400)</text>

                    <path d="M{p_x} {p_y + 40} L{p_x - 80} {p_y + 40}" fill="none" stroke="#ef4444" stroke-width="2"/>
                    <text x="{p_x - 140}" y="{p_y + 45}" font-size="14" font-weight="900" fill="#ef4444">△ {conn['weld_size']} (TYP)</text>

                    {bolt_svg} {pitch_svg}
                </svg>
            </div>

            <div style="display:grid; grid-template-columns: 1fr 1.5fr; gap:40px;">
                <div style="background:#f8fafc; padding:25px; border-radius:4px; border:1px solid #e2e8f0;">
                    <h4 style="margin:0 0 15px; color:#0f172a; border-left:4px solid #3b82f6; padding-left:10px;">DESIGN PARAMETERS</h4>
                    <ul style="list-style:none; padding:0; font-size:13px; line-height:2;">
                        <li>• Beam Profile: <b>{sec_name}</b></li>
                        <li>• Steel Grade: <b>{steel_grade}</b></li>
                        <li>• Bolt Type: <b>M20 Grade 8.8 HSFG</b></li>
                    </ul>
                </div>
                <div style="padding:10px;">
                    <h4 style="margin:0 0 15px; color:#0f172a;">LIMIT STATE VERIFICATION</h4>
                    <table style="width:100%; border-collapse:collapse; font-size:13px;">
                        <tr style="border-bottom:2px solid #0f172a; text-align:left;">
                            <th style="padding:8px;">Checklist</th>
                            <th style="padding:8px;">Capacity</th>
                            <th style="padding:8px;">Demand</th>
                            <th style="padding:8px;">Result</th>
                        </tr>
                        <tr>
                            <td style="padding:8px;">Shear Strength</td>
                            <td style="padding:8px;">{v_cap:,.0f} kg</td>
                            <td style="padding:8px;">{v_act:,.0f} kg</td>
                            <td style="padding:8px; font-weight:bold; color:{'green' if util <= 100 else 'red'}">{ "OK" if util <= 100 else "NG" }</td>
                        </tr>
                    </table>
                </div>
            </div>
        </div>
    </div>
    """
    components.html(html_content, height=1500, scrolling=True)
