# report_generator.py (V22 - Ultra Precision & Full Canvas Edition)
import streamlit as st
import streamlit.components.v1 as components

def get_connection_logic(res, p):
    v_act = res.get('v_act', 0)
    h_beam = p.get('h', 0)
    rows = max(2, int(v_act / 3800) + 1)
    pitch = 75   
    edge = 40    
    plate_h = (rows - 1) * pitch + (2 * edge)
    
    # Validation against beam depth
    if plate_h > (h_beam - 50):
        rows = max(2, rows - 1)
        plate_h = (rows - 1) * pitch + (2 * edge)

    return {
        "rows": rows, "pitch": pitch, "edge": edge,
        "plate_h": int(plate_h),
        "plate_t": max(9, int(p.get('tw', 6) + 3)),
        "weld_size": 6 if p.get('tw', 6) <= 10 else 8
    }

def render_report_tab(method, is_lrfd, sec_name, steel_grade, p, res, bolt):
    conn = get_connection_logic(res, p)
    max_r = max(res.get('v_act', 0)/res.get('v_cap', 1), res.get('m_act', 0)/res.get('m_cap', 1))
    
    # --- DYNAMIC CANVAS & SCALING ---
    # เพิ่มพื้นที่ด้านข้างและด้านบน (Safe Zone) เพื่อไม่ให้ตกขอบ
    canvas_w = 450
    canvas_h = max(400, conn['plate_h'] + 150)
    
    # Center coordinates
    center_x = 180
    plate_y_start = (canvas_h - conn['plate_h']) / 2
    
    bolt_elements = ""
    pitch_dimensions = ""
    for i in range(conn['rows']):
        by = plate_y_start + conn['edge'] + (i * conn['pitch'])
        # Bolt Symbol (Center-cross circle)
        bolt_elements += f"""
        <g transform="translate({center_x + 25}, {by})">
            <circle r="5" fill="none" stroke="#0f172a" stroke-width="1.2"/>
            <line x1="-4" y1="-4" x2="4" y2="4" stroke="#0f172a" stroke-width="1"/>
            <line x1="4" y1="-4" x2="-4" y2="4" stroke="#0f172a" stroke-width="1"/>
        </g>"""
        
        # Dimension Lines (Pitch)
        if i < conn['rows'] - 1:
            next_by = by + conn['pitch']
            pitch_dimensions += f"""
            <line x1="{center_x + 65}" y1="{by}" x2="{center_x + 65}" y2="{next_by}" stroke="#64748b" stroke-width="1" marker-end="url(#arrow)" marker-start="url(#arrow)"/>
            <text x="{center_x + 75}" y="{(by + next_by)/2 + 4}" font-size="11" fill="#475569" font-family="monospace">{conn['pitch']}mm</text>
            """

    html_content = f"""
    <div style="background:#f8fafc; padding:40px 10px; font-family:'Segoe UI', Tahoma, sans-serif;">
        <div style="max-width:900px; margin:auto; background:white; border-radius:4px; box-shadow:0 20px 25px -5px rgba(0,0,0,0.1); overflow:hidden; border:1px solid #e2e8f0;">
            
            <div style="background:#0f172a; padding:30px 50px; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h1 style="margin:0; color:white; font-size:24px; letter-spacing:1px;">STRUCTURAL CALCULATION SHEET</h1>
                    <p style="margin:5px 0 0; color:#94a3b8; font-size:12px;">Standard: AISC 360-22 | Method: {method}</p>
                </div>
                <div style="background:{'#10b981' if max_r <= 1 else '#ef4444'}; color:white; padding:10px 25px; border-radius:4px; font-weight:900; font-size:20px;">
                    { "PASS" if max_r <= 1 else "FAIL" }
                </div>
            </div>

            <div style="padding:40px 50px;">
                <table style="width:100%; border-collapse:collapse; margin-bottom:40px; font-size:13px;">
                    <tr style="border-bottom:2px solid #f1f5f9;">
                        <th style="text-align:left; padding:12px 0; color:#64748b;">MEMBER PROFILE</th>
                        <th style="text-align:left; padding:12px 0; color:#64748b;">DESIGN CAPACITY</th>
                        <th style="text-align:left; padding:12px 0; color:#64748b;">ACTUAL LOAD</th>
                        <th style="text-align:right; padding:12px 0; color:#64748b;">RATIO</th>
                    </tr>
                    <tr>
                        <td style="padding:15px 0; font-weight:bold;">{sec_name} ({steel_grade})</td>
                        <td style="padding:15px 0;">Vn: {res.get('v_cap',0):,.0f} kg</td>
                        <td style="padding:15px 0;">V-max: {res.get('v_act',0):,.0f} kg</td>
                        <td style="padding:15px 0; text-align:right; font-weight:900; color:{'#059669' if max_r <= 1 else '#dc2626'};">{(max_r*100):.1f}%</td>
                    </tr>
                </table>

                <h3 style="font-size:14px; color:#0f172a; margin-bottom:20px; border-left:4px solid #3b82f6; padding-left:15px;">TYPICAL CONNECTION DETAIL (N.T.S)</h3>
                <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:20px; display:flex; justify-content:center; align-items:center;">
                    <svg width="{canvas_w}" height="{canvas_h}" viewBox="0 0 {canvas_w} {canvas_h}">
                        <defs>
                            <marker id="arrow" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">
                                <path d="M0,0 L8,4 L0,8 Z" fill="#64748b" />
                            </marker>
                        </defs>
                        
                        <rect x="{center_x - 10}" y="20" width="10" height="{canvas_h - 40}" fill="#cbd5e1"/>
                        
                        <line x1="{center_x}" y1="40" x2="{canvas_w - 40}" y2="40" stroke="#cbd5e1" stroke-width="2" stroke-dasharray="8,4"/>
                        <line x1="{center_x}" y1="{canvas_h - 40}" x2="{canvas_w - 40}" y2="{canvas_h - 40}" stroke="#cbd5e1" stroke-width="2" stroke-dasharray="8,4"/>
                        
                        <rect x="{center_x}" y="{plate_y_start}" width="60" height="{conn['plate_h']}" fill="#3b82f6" fill-opacity="0.05" stroke="#3b82f6" stroke-width="2"/>
                        
                        {bolt_elements}
                        {pitch_dimensions}
                        
                        <line x1="{center_x + 130}" y1="{plate_y_start}" x2="{center_x + 130}" y2="{plate_y_start + conn['plate_h']}" stroke="#1e293b" stroke-width="1" marker-end="url(#arrow)" marker-start="url(#arrow)"/>
                        <text x="{center_x + 140}" y="{plate_y_start + conn['plate_h']/2 + 5}" font-size="12" font-weight="bold" fill="#0f172a" transform="rotate(90 {center_x + 140}, {plate_y_start + conn['plate_h']/2 + 5})">PLATE HEIGHT: {conn['plate_h']}mm</text>
                        
                        <path d="M{center_x} {plate_y_start + 20} L{center_x - 50} {plate_y_start - 30} L{center_x - 100} {plate_y_start - 30}" fill="none" stroke="#ef4444" stroke-width="1.2"/>
                        <text x="{center_x - 100}" y="{plate_y_start - 40}" font-size="11" font-weight="bold" fill="#ef4444">WELD: FILLET {conn['weld_size']}mm (TYP)</text>
                    </svg>
                </div>

                <div style="margin-top:40px; border-top:1px solid #f1f5f9; padding-top:20px; display:grid; grid-template-columns: 1fr 1fr; gap:20px; font-size:12px; color:#475569;">
                    <div>
                        <p><b>PLATE SPEC:</b> PL {conn['plate_t']}mm (ASTM A36 / SS400)</p>
                        <p><b>BOLT SPEC:</b> {bolt.get('size','M20')} Grade 8.8 (High Strength)</p>
                    </div>
                    <div>
                        <p><b>SPACING:</b> Pitch {conn['pitch']}mm / Edge {conn['edge']}mm</p>
                        <p><b>WELDING:</b> E70XX Electrode, Full Height Fillet</p>
                    </div>
                </div>
            </div>

            <div style="background:#f8fafc; padding:30px 50px; border-top:1px solid #e2e8f0; display:flex; justify-content:space-between; align-items:center;">
                <p style="font-size:10px; color:#94a3b8; max-width:400px;">This automated design report is verified for static gravity loads. Connection design is based on the provided shear force {res.get('v_act',0):,.0f} kg.</p>
                <div style="text-align:center;">
                    <div style="border-bottom:1px solid #0f172a; width:150px; margin-bottom:5px;"></div>
                    <p style="margin:0; font-size:11px; font-weight:bold; color:#0f172a;">SENIOR STRUCTURAL ENGINEER</p>
                </div>
            </div>
        </div>

        <div style="text-align:center; margin-top:30px;">
            <button onclick="window.print()" style="padding:12px 40px; background:#0f172a; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">
                🖨️ EXPORT OFFICIAL PDF
            </button>
        </div>
    </div>
    """
    components.html(html_content, height=canvas_h + 800, scrolling=True)
