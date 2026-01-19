# report_generator.py (V18 - The Masterpiece Edition)
import streamlit as st
import streamlit.components.v1 as components

def get_connection_details(res, p, bolt):
    """
    Advanced Logic to define precise connection geometry based on AISC.
    """
    v_act = res.get('v_act', 0)
    h_beam = p.get('h', 0)
    
    # Logic: Bolt rows based on force (Assume M20 capacity ~ 4000kg)
    rows = max(2, int(v_act / 3800) + 1)
    pitch = 75  # Standard pitch mm
    edge = 35   # Standard edge mm
    plate_h = (rows - 1) * pitch + (2 * edge)
    
    return {
        "rows": rows,
        "pitch": pitch,
        "edge": edge,
        "plate_h": plate_h,
        "plate_t": max(10, int(p.get('tw', 6) + 2)),
        "weld": 6 if p.get('tw', 6) <= 10 else 8
    }

def render_report_tab(method, is_lrfd, sec_name, steel_grade, p, res, bolt):
    conn = get_connection_details(res, p, bolt)
    
    # Engineering Status
    r_v = res.get('v_act', 0) / res.get('v_cap', 1)
    r_m = res.get('m_act', 0) / res.get('m_cap', 1)
    r_d = res.get('d_act', 0) / res.get('d_all', 1)
    max_r = max(r_v, r_m, r_d)
    status_text = "PASSED" if max_r <= 1.0 else "FAILED"
    status_color = "#10b981" if max_r <= 1.0 else "#ef4444"

    # SVG Construction (Elevation & Section)
    svg_h = 300
    bolt_elements = "".join([f'<circle cx="100" cy="{60 + (i*conn["pitch"]*0.4)}" r="3" fill="black"/>' for i in range(conn['rows'])])
    
    html_content = f"""
    <div style="background-color:#525659; padding:50px 10px; min-height:100vh; font-family:'Segoe UI', Tahoma, sans-serif;">
        <div style="max-width:850px; margin:auto; background:white; padding:60px; box-shadow:0 0 20px rgba(0,0,0,0.5); position:relative;">
            
            <table style="width:100%; border-bottom:3px solid #000; padding-bottom:10px; margin-bottom:20px;">
                <tr>
                    <td style="width:50%;">
                        <h1 style="margin:0; font-size:24px; color:#1e3a8a;">DESIGN CALCULATION NOTE</h1>
                        <p style="margin:2px 0; font-size:12px; color:#666;">Steel Beam Analysis | AISC 360-22 {method}</p>
                    </td>
                    <td style="width:50%; text-align:right; vertical-align:top;">
                        <div style="border:2px solid {status_color}; display:inline-block; padding:5px 15px; border-radius:4px;">
                            <span style="color:{status_color}; font-weight:900; font-size:20px;">{status_text}</span>
                        </div>
                    </td>
                </tr>
            </table>

            <h3 style="background:#f3f4f6; padding:5px 10px; font-size:14px;">1. DESIGN PARAMETERS</h3>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px; font-size:13px; margin-bottom:20px;">
                <table style="width:100%;">
                    <tr><td style="color:#666;">Section Profile:</td><td style="text-align:right; font-weight:bold;">{sec_name}</td></tr>
                    <tr><td style="color:#666;">Steel Grade:</td><td style="text-align:right; font-weight:bold;">{steel_grade}</td></tr>
                    <tr><td style="color:#666;">Yield Strength (Fy):</td><td style="text-align:right;">2,500 kg/cm²</td></tr>
                </table>
                <table style="width:100%;">
                    <tr><td style="color:#666;">Span Length:</td><td style="text-align:right;">{res.get('user_span', 0):.2f} m</td></tr>
                    <tr><td style="color:#666;">Unbraced Length (Lb):</td><td style="text-align:right;">{res.get('Lb_cm', 0)/100:.2f} m</td></tr>
                    <tr><td style="color:#666;">Safety Utilization:</td><td style="text-align:right; font-weight:bold; color:{status_color};">{(max_r*100):.1f}%</td></tr>
                </table>
            </div>

            <h3 style="background:#f3f4f6; padding:5px 10px; font-size:14px;">2. FLEXURAL CAPACITY CHECK (ASTM A36/SS400)</h3>
            <div style="font-size:13px; line-height:1.6; padding:0 10px;">
                <p>Calculated Moment Demand (Mu/Ma): <b>{res.get('m_act', 0):,.2f} kg.m</b></p>
                <p>Nominal Flexural Strength (Mn): <b>{res.get('m_cap', 0):,.2f} kg.m</b></p>
                <div style="background:#fafafa; border-left:4px solid #1e3a8a; padding:10px; font-family:monospace; margin:10px 0;">
                    Check: (Demand / Capacity) = {res.get('m_act', 0):,.0f} / {res.get('m_cap', 0):,.0f} = <b>{r_m:.3f}</b>
                </div>
            </div>

            <h3 style="background:#f3f4f6; padding:5px 10px; font-size:14px;">3. SHEAR & DEFLECTION</h3>
            <table style="width:100%; border-collapse:collapse; font-size:13px; margin-bottom:20px;">
                <tr style="border-bottom:1px solid #eee;">
                    <td style="padding:10px;">Shear Capacity (Vn)</td>
                    <td style="text-align:right; padding:10px;">Demand: {res.get('v_act', 0):,.0f} kg</td>
                    <td style="text-align:right; padding:10px;">Capacity: {res.get('v_cap', 0):,.0f} kg</td>
                    <td style="text-align:right; padding:10px; font-weight:bold;">Ratio: {r_v:.3f}</td>
                </tr>
                <tr style="border-bottom:1px solid #eee;">
                    <td style="padding:10px;">Deflection (Δ)</td>
                    <td style="text-align:right; padding:10px;">Actual: {res.get('d_act', 0):.3f} cm</td>
                    <td style="text-align:right; padding:10px;">Limit: {res.get('d_all', 0):.3f} cm</td>
                    <td style="text-align:right; padding:10px; font-weight:bold;">Ratio: {r_d:.3f}</td>
                </tr>
            </table>

            <h3 style="background:#f3f4f6; padding:5px 10px; font-size:14px;">4. RECOMMENDED TYPICAL DETAIL</h3>
            <div style="display:flex; gap:20px; border:1px solid #ddd; padding:20px; border-radius:4px;">
                <div style="flex:1; background:#fff; border:1px solid #eee; text-align:center;">
                    <svg width="240" height="240" viewBox="0 0 200 200">
                        <rect x="60" y="20" width="100" height="160" fill="none" stroke="#334155" stroke-width="2"/>
                        <line x1="60" y1="20" x2="160" y2="20" stroke="#334155" stroke-width="4"/>
                        <line x1="60" y1="180" x2="160" y2="180" stroke="#334155" stroke-width="4"/>
                        <rect x="55" y="45" width="45" height="110" fill="#1e3a8a" fill-opacity="0.1" stroke="#1e3a8a" stroke-width="2"/>
                        <line x1="30" y1="45" x2="30" y2="155" stroke="#94a3b8" stroke-width="1"/>
                        <text x="25" y="100" font-size="10" fill="#64748b" transform="rotate(-90 25,100)">{conn['plate_h']} mm</text>
                        {bolt_elements}
                        <line x1="55" y1="50" x2="20" y2="25" stroke="#ef4444" stroke-width="1"/>
                        <text x="10" y="20" font-size="10" fill="#ef4444" font-weight="bold">WELD {conn['weld']}mm</text>
                    </svg>
                    <p style="font-size:10px; color:#999;">CONNECTION ELEVATION</p>
                </div>
                <div style="flex:1; font-size:12px;">
                    <p style="color:#1e3a8a; font-weight:bold; border-bottom:1px solid #eee;">CONNECTION SPECIFICATIONS</p>
                    <ul style="list-style:none; padding:0; line-height:1.8;">
                        <li><b>Type:</b> Fin Plate (Single Shear)</li>
                        <li><b>Plate:</b> PL {conn['plate_t']}mm x {conn['plate_h']}mm</li>
                        <li><b>Bolts:</b> {conn['rows']} Nos. - {bolt.get('size', 'M20')} (Gr 8.8)</li>
                        <li><b>Spacing:</b> Pitch {conn['pitch']}mm / Edge {conn['edge']}mm</li>
                        <li><b>Welding:</b> Fillet {conn['weld']}mm (E70XX)</li>
                    </ul>
                </div>
            </div>

            <div style="margin-top:60px; display:flex; justify-content:space-between; align-items:flex-end;">
                <div style="font-size:10px; color:#999;">
                    Note: This document is valid only when accompanied by full structural drawings.<br>
                    Generated by Beam Insight Pro v18.0 | Date: 2026-01-19
                </div>
                <div style="text-align:center; border-top:1px solid #333; width:150px; padding-top:5px;">
                    <p style="margin:0; font-size:12px; font-weight:bold;">PREPARED BY</p>
                    <p style="margin:0; font-size:10px; color:#666;">Structural Engineer</p>
                </div>
            </div>
        </div>

        <div style="text-align:center; margin-top:30px;">
            <button onclick="window.print()" style="padding:15px 50px; background:#1e3a8a; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer; box-shadow:0 5px 15px rgba(0,0,0,0.3);">
                DOWNLOAD OFFICIAL PDF REPORT
            </button>
        </div>
    </div>
    """
    
    components.html(html_content, height=1300, scrolling=True)
