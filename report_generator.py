# report_generator.py (V17 - The "Ultimate Engineering" Edition)
import streamlit as st
import streamlit.components.v1 as components

def get_connection_advisor(res, p, bolt):
    v_act = res.get('v_act', 0)
    h_beam = p.get('h', 0)
    tw = p.get('tw', 0)
    
    # Advisor Logic
    suggested_rows = max(2, int(v_act / 3500) + 1)
    plate_h = int((h_beam * 0.6) / 10) * 10 
    plate_t = int(tw + 2) if tw > 0 else 10 
    weld_size = 6 if tw <= 12 else 8
    
    return {
        "rows": suggested_rows,
        "plate_h": plate_h,
        "plate_t": plate_t,
        "weld": weld_size,
        "v_design": v_act,
        "spacing": 75, # mm standard pitch
        "edge": 35    # mm standard edge
    }

def render_report_tab(method, is_lrfd, sec_name, steel_grade, p, res, bolt):
    conn = get_connection_advisor(res, p, bolt)
    
    # Ratios & Status
    r_v = res.get('v_act', 0) / res.get('v_cap', 1)
    r_m = res.get('m_act', 0) / res.get('m_cap', 1)
    r_d = res.get('d_act', 0) / res.get('d_all', 1)
    max_r = max(r_v, r_m, r_d)
    status_text = "PASSED" if max_r <= 1.0 else "FAILED"
    status_color = "#059669" if max_r <= 1.0 else "#dc2626"

    # SVG Dimensioning Logic
    svg_w = 250
    plate_draw_h = 40 + (conn['rows'] * 30)
    svg_h = plate_draw_h + 60
    
    bolt_elements = ""
    for i in range(conn['rows']):
        y_pos = 50 + (i * 30)
        bolt_elements += f'<circle cx="100" cy="{y_pos}" r="4" fill="#1e293b"/>'

    html_content = f"""
    <div style="background:#f1f5f9; padding:40px 10px; font-family:'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
        <div style="max-width:900px; margin:auto; background:white; box-shadow:0 20px 25px -5px rgb(0 0 0 / 0.1); border-radius:4px; overflow:hidden;">
            
            <div style="background:{status_color}; height:8px;"></div>
            
            <div style="padding:40px;">
                <div style="display:flex; justify-content:space-between; border-bottom:2px solid #e2e8f0; padding-bottom:20px;">
                    <div style="flex:1;">
                        <h1 style="margin:0; color:#0f172a; font-size:26px; font-weight:800; letter-spacing:-0.025em;">STRUCTURAL CALCULATION SHEET</h1>
                        <p style="margin:4px 0; color:#64748b; font-size:12px; font-weight:500;">
                            PROJECT: BEAM DESIGN VERIFICATION | AISC 360-22 {method}
                        </p>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:32px; font-weight:900; color:{status_color}; line-height:1;">{status_text}</div>
                        <div style="font-size:12px; color:#64748b; margin-top:4px;">UTILIZATION: {(max_r*100):.1f}%</div>
                    </div>
                </div>

                <div style="margin-top:30px; display:grid; grid-template-columns: 1fr 1fr; gap:40px;">
                    <div>
                        <h3 style="font-size:13px; color:#1e40af; text-transform:uppercase; margin-bottom:12px; border-left:3px solid #1e40af; padding-left:8px;">1. Section Information</h3>
                        <table style="width:100%; font-size:13px; border-collapse:collapse;">
                            <tr style="border-bottom:1px solid #f1f5f9;"><td style="padding:8px 0; color:#64748b;">Section Profile</td><td style="text-align:right; font-weight:600;">{sec_name}</td></tr>
                            <tr style="border-bottom:1px solid #f1f5f9;"><td style="padding:8px 0; color:#64748b;">Material Grade</td><td style="text-align:right; font-weight:600;">{steel_grade}</td></tr>
                            <tr style="border-bottom:1px solid #f1f5f9;"><td style="padding:8px 0; color:#64748b;">Span Length</td><td style="text-align:right; font-weight:600;">{res.get('user_span',0):.2f} m</td></tr>
                        </table>
                    </div>
                    <div>
                        <h3 style="font-size:13px; color:#1e40af; text-transform:uppercase; margin-bottom:12px; border-left:3px solid #1e40af; padding-left:8px;">2. Governing Load</h3>
                        <div style="background:#f8fafc; padding:15px; border-radius:4px; border:1px solid #e2e8f0;">
                            <div style="font-size:24px; font-weight:700; color:#1e293b;">{w_safe:,.0f} <span style="font-size:14px; color:#64748b;">kg/m</span></div>
                            <div style="font-size:11px; color:#ef4444; font-weight:600; margin-top:4px;">LIMIT STATE: {cause.upper()}</div>
                        </div>
                    </div>
                </div>

                <div style="margin-top:40px;">
                    <h3 style="font-size:13px; color:#1e40af; text-transform:uppercase; margin-bottom:12px; border-left:3px solid #1e40af; padding-left:8px;">3. Detailed Strength Analysis</h3>
                    <table style="width:100%; border-collapse:collapse; font-size:13px;">
                        <tr style="background:#f8fafc; font-weight:600; color:#475569;">
                            <td style="padding:12px; border:1px solid #e2e8f0;">Constraint</td>
                            <td style="padding:12px; border:1px solid #e2e8f0;">Equation Reference</td>
                            <td style="padding:12px; border:1px solid #e2e8f0; text-align:center;">Demand/Capacity</td>
                            <td style="padding:12px; border:1px solid #e2e8f0; text-align:right;">Ratio</td>
                        </tr>
                        <tr>
                            <td style="padding:12px; border:1px solid #e2e8f0;"><b>Flexural</b></td>
                            <td style="padding:12px; border:1px solid #e2e8f0; color:#64748b; font-family:monospace;">Mn = Cb[Mp-(Mp-0.7FySx)...]</td>
                            <td style="padding:12px; border:1px solid #e2e8f0; text-align:center;">{res.get('m_act',0):,.0f} / {res.get('m_cap',0):,.0f}</td>
                            <td style="padding:12px; border:1px solid #e2e8f0; text-align:right; font-weight:700; color:{r_m > 1 and '#dc2626' or '#0f172a'};">{(r_m):.3f}</td>
                        </tr>
                        <tr>
                            <td style="padding:12px; border:1px solid #e2e8f0;"><b>Shear</b></td>
                            <td style="padding:12px; border:1px solid #e2e8f0; color:#64748b; font-family:monospace;">Vn = 0.6 * Fy * Aw</td>
                            <td style="padding:12px; border:1px solid #e2e8f0; text-align:center;">{res.get('v_act',0):,.0f} / {res.get('v_cap',0):,.0f}</td>
                            <td style="padding:12px; border:1px solid #e2e8f0; text-align:right; font-weight:700; color:{r_v > 1 and '#dc2626' or '#0f172a'};">{(r_v):.3f}</td>
                        </tr>
                    </table>
                </div>

                <div style="margin-top:40px;">
                    <h3 style="font-size:13px; color:#1e40af; text-transform:uppercase; margin-bottom:12px; border-left:3px solid #1e40af; padding-left:8px;">4. Recommended Connection Drawing</h3>
                    <div style="display:flex; gap:30px; border:1px solid #e2e8f0; border-radius:4px; padding:30px; background:#fcfcfc;">
                        <div style="background:white; border:1px solid #cbd5e1; padding:10px;">
                            <svg width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}">
                                <rect x="80" y="20" width="120" height="{svg_h-40}" fill="#f8fafc" stroke="#1e40af" stroke-width="2"/>
                                <line x1="80" y1="20" x2="200" y2="20" stroke="#1e40af" stroke-width="4"/>
                                <line x1="80" y1="{svg_h-20}" x2="200" y2="{svg_h-20}" stroke="#1e40af" stroke-width="4"/>
                                
                                <rect x="75" y="40" width="40" height="{plate_draw_h}" fill="#1e40af" fill-opacity="0.1" stroke="#1e40af" stroke-width="2"/>
                                
                                <line x1="60" y1="40" x2="60" y2="{40+plate_draw_h}" stroke="#64748b" stroke-width="1"/>
                                <text x="45" y="{45+plate_draw_h/2}" font-size="10" fill="#64748b" transform="rotate(-90 45,{45+plate_draw_h/2})">{conn['plate_h']}mm</text>
                                
                                {bolt_elements}
                                
                                <line x1="75" y1="50" x2="60" y2="35" stroke="#ef4444" stroke-width="1"/>
                                <text x="35" y="30" font-size="9" fill="#ef4444" font-weight="bold">WELD {conn['weld']}mm</text>
                            </svg>
                        </div>

                        <div style="flex:1;">
                            <h4 style="margin:0 0 15px; font-size:14px; color:#334155;">Connection Specification</h4>
                            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; font-size:12px;">
                                <div style="color:#64748b;">Plate Size:</div><div style="font-weight:600; text-align:right;">PL {conn['plate_t']} x {conn['plate_h']} mm</div>
                                <div style="color:#64748b;">Bolt Type:</div><div style="font-weight:600; text-align:right;">{bolt.get('size','M20')} (Gr 8.8)</div>
                                <div style="color:#64748b;">Bolt Layout:</div><div style="font-weight:600; text-align:right;">{conn['rows']} No. (1 Column)</div>
                                <div style="color:#64748b;">Hole Diameter:</div><div style="font-weight:600; text-align:right;">{int(bolt.get('size','M20')[1:])+2} mm</div>
                            </div>
                            <div style="margin-top:20px; padding:12px; background:#fff7ed; border-radius:4px; border:1px solid #ffedd5; font-size:11px; color:#9a3412;">
                                ⚠️ <b>ERECTION NOTE:</b> Ensure beam-to-support gap does not exceed 10mm. Use washers for all high-strength bolts.
                            </div>
                        </div>
                    </div>
                </div>

                <div style="margin-top:60px; padding-top:20px; border-top:1px solid #e2e8f0; display:flex; justify-content:space-between; align-items:center;">
                    <div style="font-size:10px; color:#94a3b8; max-width:60%;">
                        AISC 360-22 Structural Steel Compliance Report. Calculated by Gemini Hybrid Engine. Verified for static loading conditions only.
                    </div>
                    <div style="text-align:right;">
                        <span style="font-size:12px; font-weight:700; color:#1e40af;">BEAM INSIGHT PRO v2.0</span>
                    </div>
                </div>
            </div>
        </div>

        <div style="text-align:center; margin-top:40px; margin-bottom:60px;">
            <button onclick="window.print()" style="padding:14px 40px; background:#0f172a; color:white; border:none; border-radius:6px; cursor:pointer; font-weight:700; font-size:14px; transition:all 0.2s;">
                PRINT CALCULATION SHEET (PDF)
            </button>
        </div>
    </div>
    """
    
    components.html(html_content, height=1300, scrolling=True)
