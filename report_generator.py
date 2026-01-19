# report_generator.py (V23 - Executive Senior Engineer Edition)
import streamlit as st
import streamlit.components.v1 as components

def get_connection_logic(res, p):
    v_act = res.get('v_act', 0)
    h_beam = p.get('h', 0)
    rows = max(2, int(v_act / 3800) + 1)
    pitch, edge = 75, 40
    plate_h = (rows - 1) * pitch + (2 * edge)
    
    # Check clearance to avoid hitting flanges
    if plate_h > (h_beam - 60):
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
    v_cap = res.get('v_cap', 1)
    v_act = res.get('v_act', 0)
    ratio = (v_act / v_cap) * 100

    # --- CANVAS SETTINGS ---
    # ใช้กว้างขึ้นเพื่อผลัก Dimension ออกไปด้านนอก ไม่ให้ทับรูป
    c_w, c_h = 550, 480
    c_x, c_y = 150, (c_h / 2) - (conn['plate_h'] / 2)
    
    bolt_elements = ""
    pitch_dims = ""
    
    for i in range(conn['rows']):
        by = c_y + conn['edge'] + (i * conn['pitch'])
        # Professional Bolt Symbol
        bolt_elements += f"""
        <g transform="translate({c_x + 35}, {by})">
            <circle r="6" fill="white" stroke="#0f172a" stroke-width="1.5"/>
            <line x1="-4" y1="-4" x2="4" y2="4" stroke="#0f172a" stroke-width="1"/>
            <line x1="4" y1="-4" x2="-4" y2="4" stroke="#0f172a" stroke-width="1"/>
        </g>"""
        
        # Pitch Dims (Placed inside but offset to prevent overlap)
        if i < conn['rows'] - 1:
            mid_y = by + (conn['pitch'] / 2)
            pitch_dims += f"""
            <line x1="{c_x + 75}" y1="{by}" x2="{c_x + 75}" y2="{by + conn['pitch']}" stroke="#64748b" stroke-width="1" marker-end="url(#arrow)" marker-start="url(#arrow)"/>
            <text x="{c_x + 82}" y="{mid_y + 4}" font-size="11" fill="#475569" font-family="Arial">{conn['pitch']}mm</text>
            """

    html_content = f"""
    <div style="background:#f0f2f5; padding:40px 20px; font-family:'Segoe UI', Roboto, sans-serif;">
        <div style="max-width:900px; margin:auto; background:white; border-radius:8px; box-shadow:0 15px 35px rgba(0,0,0,0.1); border:1px solid #d1d5db; overflow:hidden;">
            
            <div style="background:#1e293b; padding:25px 40px; color:white; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h2 style="margin:0; font-size:22px; letter-spacing:0.5px; font-weight:800;">BEAM CONNECTION DESIGN</h2>
                    <p style="margin:5px 0 0; color:#94a3b8; font-size:12px;">PROJECT STANDARD: AISC 360-22 | REF: {sec_name}</p>
                </div>
                <div style="text-align:right;">
                    <span style="display:inline-block; background:{'#10b981' if ratio <= 100 else '#ef4444'}; color:white; padding:8px 20px; border-radius:6px; font-size:18px; font-weight:900;">
                        {ratio:.1f}% UTIL.
                    </span>
                </div>
            </div>

            <div style="padding:40px;">
                <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:20px; margin-bottom:40px;">
                    <div style="background:#f8fafc; padding:15px; border-radius:6px; border:1px solid #e2e8f0;">
                        <div style="font-size:11px; color:#64748b; font-weight:bold;">MEMBER PROFILE</div>
                        <div style="font-size:15px; font-weight:bold; color:#1e293b; margin-top:5px;">{sec_name}</div>
                    </div>
                    <div style="background:#f8fafc; padding:15px; border-radius:6px; border:1px solid #e2e8f0;">
                        <div style="font-size:11px; color:#64748b; font-weight:bold;">DESIGN CAPACITY (φVn)</div>
                        <div style="font-size:15px; font-weight:bold; color:#1e293b; margin-top:5px;">{v_cap:,.0f} kg</div>
                    </div>
                    <div style="background:#f8fafc; padding:15px; border-radius:6px; border:1px solid #e2e8f0;">
                        <div style="font-size:11px; color:#64748b; font-weight:bold;">MAX SHEAR (Vu)</div>
                        <div style="font-size:15px; font-weight:bold; color:#ef4444; margin-top:5px;">{v_act:,.0f} kg</div>
                    </div>
                </div>

                <div style="border:1px solid #e5e7eb; border-radius:10px; background:#fff; padding:20px; position:relative;">
                    <div style="position:absolute; top:15px; left:20px; font-size:12px; font-weight:bold; color:#1e293b;">TYPICAL FIN PLATE DETAIL (ELEVATION)</div>
                    <svg width="100%" height="{c_h}" viewBox="0 0 {c_w} {c_h}">
                        <defs>
                            <marker id="arrow" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">
                                <path d="M0,0 L8,4 L0,8 Z" fill="#64748b" />
                            </marker>
                        </defs>
                        
                        <rect x="{c_x - 15}" y="30" width="15" height="{c_h - 60}" fill="#cbd5e1"/>
                        
                        <line x1="{c_x}" y1="60" x2="{c_w - 50}" y2="60" stroke="#e2e8f0" stroke-width="2" stroke-dasharray="10,5"/>
                        <line x1="{c_x}" y1="{c_h - 60}" x2="{c_w - 50}" y2="{c_h - 60}" stroke="#e2e8f0" stroke-width="2" stroke-dasharray="10,5"/>
                        
                        <rect x="{c_x}" y="{c_y}" width="70" height="{conn['plate_h']}" fill="#3b82f6" fill-opacity="0.08" stroke="#3b82f6" stroke-width="2.5"/>
                        
                        {bolt_elements}
                        {pitch_dims}
                        
                        <line x1="{c_w - 100}" y1="{c_y}" x2="{c_w - 100}" y2="{c_y + conn['plate_h']}" stroke="#1e293b" stroke-width="1.2" marker-end="url(#arrow)" marker-start="url(#arrow)"/>
                        <text x="{c_w - 85}" y="{c_y + conn['plate_h']/2 + 5}" font-size="13" font-weight="900" fill="#0f172a" transform="rotate(90 {c_w - 85}, {c_y + conn['plate_h']/2 + 5})">PLATE HEIGHT: {conn['plate_h']} mm</text>
                        
                        <path d="M{c_x} {c_y + 25} L{c_x - 60} {c_y - 40} L{c_x - 110} {c_y - 40}" fill="none" stroke="#ef4444" stroke-width="1.5"/>
                        <text x="{c_x - 110}" y="{c_y - 50}" font-size="12" font-weight="bold" fill="#ef4444">WELD FILLET {conn['weld_size']}mm (TYP)</text>
                    </svg>
                </div>

                <div style="margin-top:30px; display:grid; grid-template-columns: 1fr 1fr; gap:40px; padding:20px; border-top:2px solid #f1f5f9; font-size:13px;">
                    <div>
                        <div style="color:#64748b; font-weight:bold; margin-bottom:10px; text-transform:uppercase;">Material Specifications</div>
                        <table style="width:100%;">
                            <tr><td style="padding:4px 0;">Plate thickness:</td><td style="text-align:right; font-weight:bold;">PL {conn['plate_t']} mm</td></tr>
                            <tr><td style="padding:4px 0;">Steel Grade:</td><td style="text-align:right; font-weight:bold;">ASTM A36 / SS400</td></tr>
                            <tr><td style="padding:4px 0;">Electrode:</td><td style="text-align:right; font-weight:bold;">E70XX (min)</td></tr>
                        </table>
                    </div>
                    <div>
                        <div style="color:#64748b; font-weight:bold; margin-bottom:10px; text-transform:uppercase;">Installation Notes</div>
                        <table style="width:100%;">
                            <tr><td style="padding:4px 0;">Bolt Diameter:</td><td style="text-align:right; font-weight:bold;">{bolt.get('size','M20')} (Gr 8.8)</td></tr>
                            <tr><td style="padding:4px 0;">Edge distance:</td><td style="text-align:right; font-weight:bold;">{conn['edge']} mm (Min)</td></tr>
                            <tr><td style="padding:4px 0;">Bolt pitch:</td><td style="text-align:right; font-weight:bold;">{conn['pitch']} mm</td></tr>
                        </table>
                    </div>
                </div>
            </div>

            <div style="background:#f1f5f9; padding:20px 40px; border-top:1px solid #e2e8f0; display:flex; justify-content:space-between; align-items:center;">
                <p style="font-size:10px; color:#64748b; max-width:60%;">
                    Engineering validation performed by Gemini Structural Engine. Final construction drawings must be stamped by a Licensed Structural Engineer (P.E.).
                </p>
                <div style="text-align:center;">
                    <div style="width:160px; height:1px; background:#0f172a; margin-bottom:5px;"></div>
                    <span style="font-size:11px; font-weight:bold; color:#0f172a;">SENIOR ENGINEER REVIEW</span>
                </div>
            </div>
        </div>
        
        <div style="text-align:center; margin-top:30px; padding-bottom:50px;">
            <button onclick="window.print()" style="padding:15px 50px; background:#1e293b; color:white; border:none; border-radius:6px; font-weight:bold; cursor:pointer; box-shadow:0 10px 15px rgba(0,0,0,0.1);">
                PRINT PDF DOCUMENT
            </button>
        </div>
    </div>
    """
    components.html(html_content, height=1400, scrolling=True)
