# report_generator.py (V16 - Engineering Advisor Version)
import streamlit as st
import streamlit.components.v1 as components

def get_connection_advisor(res, p, bolt):
    """
    Logic to recommend specific connection details based on calculated forces.
    """
    v_act = res.get('v_act', 0)
    h_beam = p.get('h', 0)
    tw = p.get('tw', 0)
    
    # 1. Bolt Rows Recommendation (Based on shear force)
    # Average capacity of one M20 Bolt in single shear is ~3,500 - 4,500 kg
    suggested_rows = max(2, int(v_act / 3500) + 1)
    
    # 2. Plate Dimensions (Standard practice: ~60-70% of beam depth)
    plate_h = int((h_beam * 0.6) / 10) * 10 
    plate_t = int(tw + 2) if tw > 0 else 10 # Plate thickness approx tw + 2mm
    
    # 3. Weld Size (Based on AISC min weld size for thickness)
    weld_size = 6 if tw <= 12 else 8 # mm
    
    return {
        "rows": suggested_rows,
        "plate_h": plate_h,
        "plate_t": plate_t,
        "weld": weld_size,
        "v_design": v_act
    }

def render_report_tab(method, is_lrfd, sec_name, steel_grade, p, res, bolt):
    # Prepare Data
    conn = get_connection_advisor(res, p, bolt)
    w_safe = res.get('w_safe', 0)
    cause = res.get('cause', 'N/A')
    
    # Ratios for color logic
    r_v = res.get('v_act', 0) / res.get('v_cap', 1)
    r_m = res.get('m_act', 0) / res.get('m_cap', 1)
    r_d = res.get('d_act', 0) / res.get('d_all', 1)
    max_r = max(r_v, r_m, r_d)
    
    status_text = "PASS" if max_r <= 1.0 else "FAIL"
    status_color = "#16a34a" if max_r <= 1.0 else "#dc2626"

    # SVG Construction for Typical Detail
    bolt_circles = "".join([f'<circle cx="35" cy="{35 + (i*25)}" r="4" fill="#334155"/>' for i in range(conn['rows'])])
    svg_h = 70 + (conn['rows'] - 1) * 25

    html_content = f"""
    <div style="background:#f8fafc; padding:20px; font-family:'Inter', sans-serif;">
        <div style="max-width:850px; margin:auto; background:white; padding:50px; border:1px solid #e2e8f0; border-radius:8px; box-shadow:0 10px 25px rgba(0,0,0,0.05);">
            
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:4px solid #1e40af; padding-bottom:20px;">
                <div>
                    <h1 style="margin:0; color:#1e40af; font-size:24px;">STRUCTURAL CALCULATION REPORT</h1>
                    <p style="margin:5px 0 0; color:#64748b; font-size:13px;">Standard: AISC 360-22 Specification | Unit: Metric (kg, cm, m)</p>
                </div>
                <div style="text-align:right;">
                    <div style="background:{status_color}; color:white; padding:8px 20px; border-radius:4px; font-weight:800; font-size:20px;">
                        {status_text}
                    </div>
                    <p style="margin:5px 0 0; font-size:12px; color:#64748b;">Utilization: {(max_r*100):.1f}%</p>
                </div>
            </div>

            <div style="margin-top:30px;">
                <h3 style="font-size:14px; text-transform:uppercase; color:#1e40af; border-bottom:1px solid #e2e8f0; padding-bottom:5px;">1. Design Parameters & Properties</h3>
                <div style="display:grid; grid-template-columns: 1fr 1.5fr; gap:40px; margin-top:10px;">
                    <table style="width:100%; font-size:13px; color:#334155;">
                        <tr><td style="padding:4px 0;"><b>Section:</b></td><td style="text-align:right;">{sec_name}</td></tr>
                        <tr><td style="padding:4px 0;"><b>Grade:</b></td><td style="text-align:right;">{steel_grade}</td></tr>
                        <tr><td style="padding:4px 0;"><b>Load Cap:</b></td><td style="text-align:right; color:#1e40af; font-weight:bold;">{w_safe:,.0f} kg/m</td></tr>
                    </table>
                    <table style="width:100%; font-size:12px; border-collapse:collapse; color:#334155;">
                        <tr style="border-bottom:1px solid #f1f5f9;"><td style="padding:4px;">h: {p['h']} mm</td><td>tw: {p['tw']} mm</td><td>Ix: {p['Ix']:,.0f} cm⁴</td></tr>
                        <tr style="border-bottom:1px solid #f1f5f9;"><td style="padding:4px;">b: {p['b']} mm</td><td>tf: {p['tf']} mm</td><td>Sx: {p['Sx']:,.0f} cm³</td></tr>
                    </table>
                </div>
            </div>

            <div style="margin-top:30px;">
                <h3 style="font-size:14px; text-transform:uppercase; color:#1e40af; border-bottom:1px solid #e2e8f0; padding-bottom:5px;">2. Performance Verification</h3>
                <table style="width:100%; margin-top:10px; border-collapse:collapse; font-size:13px;">
                    <thead style="background:#f8fafc; color:#1e40af; text-align:left;">
                        <tr>
                            <th style="padding:10px; border:1px solid #e2e8f0;">Constraint</th>
                            <th style="padding:10px; border:1px solid #e2e8f0;">Demand</th>
                            <th style="padding:10px; border:1px solid #e2e8f0;">Capacity</th>
                            <th style="padding:10px; border:1px solid #e2e8f0;">Ratio</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td style="padding:10px; border:1px solid #e2e8f0;">Flexure</td><td>{res.get('m_act', 0):,.0f} kg.m</td><td>{res.get('m_cap', 1):,.0f} kg.m</td><td style="font-weight:bold;">{r_m:.3f}</td></tr>
                        <tr><td style="padding:10px; border:1px solid #e2e8f0;">Shear</td><td>{res.get('v_act', 0):,.0f} kg</td><td>{res.get('v_cap', 1):,.0f} kg</td><td style="font-weight:bold;">{r_v:.3f}</td></tr>
                        <tr><td style="padding:10px; border:1px solid #e2e8f0;">Deflection</td><td>{res.get('d_act', 0):.3f} cm</td><td>{res.get('d_all', 1):.3f} cm</td><td style="font-weight:bold;">{r_d:.3f}</td></tr>
                    </tbody>
                </table>
            </div>

            <div style="margin-top:40px; border:2px solid #1e40af; border-radius:8px; overflow:hidden;">
                <div style="background:#1e40af; color:white; padding:10px 20px; font-weight:bold; font-size:14px;">
                    3. RECOMMENDED TYPICAL CONNECTION DETAIL (FIN PLATE)
                </div>
                <div style="display:flex; padding:25px; gap:40px; background:#f0f7ff; align-items:center;">
                    <div style="background:white; padding:15px; border-radius:4px; border:1px solid #cbd5e1; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
                        <svg width="160" height="{max(180, svg_h + 40)}" viewBox="0 0 120 {svg_h + 40}">
                            <rect x="5" y="5" width="20" height="{svg_h + 30}" fill="#cbd5e1" stroke="#94a3b8"/>
                            <line x1="25" y1="15" x2="110" y2="15" stroke="#1e40af" stroke-width="4"/>
                            <line x1="25" y1="{svg_h + 25}" x2="110" y2="{svg_h + 25}" stroke="#1e40af" stroke-width="4"/>
                            <rect x="25" y="15" width="85" height="{svg_h + 10}" fill="#f1f5f9" opacity="0.5"/>
                            <rect x="25" y="25" width="25" height="{svg_h - 10}" fill="#1e40af" fill-opacity="0.2" stroke="#1e40af" stroke-width="2"/>
                            {bolt_circles}
                        </svg>
                        <p style="font-size:10px; color:#64748b; text-align:center; margin-top:5px;">Dynamic Elevation</p>
                    </div>

                    <div style="flex-grow:1;">
                        <table style="width:100%; font-size:13px; color:#1e40af;">
                            <tr style="border-bottom:1px solid #dbeafe;"><td style="padding:8px 0;"><b>Plate Height:</b></td><td style="text-align:right;">{conn['plate_h']} mm</td></tr>
                            <tr style="border-bottom:1px solid #dbeafe;"><td style="padding:8px 0;"><b>Plate Thickness:</b></td><td style="text-align:right;">{conn['plate_t']} mm</td></tr>
                            <tr style="border-bottom:1px solid #dbeafe;"><td style="padding:8px 0;"><b>Bolt Quantity:</b></td><td style="text-align:right;">{conn['rows']} x {bolt.get('size', 'M20')}</td></tr>
                            <tr style="border-bottom:1px solid #dbeafe;"><td style="padding:8px 0;"><b>Weld (Both Sides):</b></td><td style="text-align:right;">Fillet {conn['weld']} mm</td></tr>
                        </table>
                        <div style="margin-top:15px; background:#dbeafe; padding:10px; border-radius:4px; font-size:11px; color:#1e40af;">
                            <b>Advisor Note:</b> Suggested layout is based on a shear force of {conn['v_design']:,.0f} kg. Maintain minimum bolt edge distance of 1.5d.
                        </div>
                    </div>
                </div>
            </div>

            <div style="margin-top:50px; border-top:1px solid #e2e8f0; padding-top:20px; text-align:center;">
                <p style="font-size:10px; color:#94a3b8;">
                    This computer-generated document is for preliminary design. Final engineering drawings must be verified by a licensed Structural Engineer.
                </p>
                <div style="font-size:12px; font-weight:bold; color:#1e40af; margin-top:10px;">
                    BEAM INSIGHT HYBRID ENGINE | 2026
                </div>
            </div>
        </div>

        <div style="text-align:center; margin-top:30px; padding-bottom:50px;">
            <button onclick="window.print()" style="padding:12px 30px; background:#1e40af; color:white; border:none; border-radius:6px; cursor:pointer; font-weight:700; box-shadow:0 4px 12px rgba(30,64,175,0.3);">
                🖨️ Export to PDF Report
            </button>
        </div>
    </div>
    """
    
    components.html(html_content, height=1200, scrolling=True)
