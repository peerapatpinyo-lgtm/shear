# report_generator.py (V20 - Global Senior Engineer Edition)
import streamlit as st
import streamlit.components.v1 as components

def get_connection_logic(res, p):
    """
    Advanced connection advisor based on AISC 360-22.
    Determines geometry, bolt spacing, and plate requirements.
    """
    v_act = res.get('v_act', 0)
    h_beam = p.get('h', 0)
    
    # Structural Logic: Capacity of one M20 Bolt (Gr 8.8) in single shear ~ 4,400 kg
    # Factor of safety or phi factor is already considered in res['v_cap']
    rows = max(2, int(v_act / 3800) + 1)
    
    # Engineering Standards (Metric)
    pitch = 75   # Standard pitch for M20
    edge = 35    # Minimum edge distance
    plate_h = (rows - 1) * pitch + (2 * edge)
    
    # Check for physical constraints
    if plate_h > (h_beam * 0.8):
        # If plate is too high, suggest double row or larger bolts (logic simplified for report)
        plate_h = h_beam * 0.75 

    return {
        "rows": rows,
        "pitch": pitch,
        "edge": edge,
        "plate_h": int(plate_h),
        "plate_t": max(9, int(p.get('tw', 6) + 3)),
        "weld_size": 6 if p.get('tw', 6) <= 10 else 8
    }

def render_report_tab(method, is_lrfd, sec_name, steel_grade, p, res, bolt):
    conn = get_connection_logic(res, p)
    
    # Performance Ratios
    r_v = res.get('v_act', 0) / res.get('v_cap', 1)
    r_m = res.get('m_act', 0) / res.get('m_cap', 1)
    r_d = res.get('d_act', 0) / res.get('d_all', 1)
    max_r = max(r_v, r_m, r_d)
    
    status_text = "CONFORMS" if max_r <= 1.0 else "NON-CONFORMING"
    status_color = "#065f46" if max_r <= 1.0 else "#991b1b"

    # SVG Drawing Elements
    bolt_elements = "".join([f'<circle cx="110" cy="{50 + (i*35)}" r="4" fill="#0f172a" />' for i in range(conn['rows'])])
    svg_height = 100 + (conn['rows'] * 35)

    html_content = f"""
    <div style="background:#e5e7eb; padding:50px 10px; font-family:'Helvetica Neue', Arial, sans-serif;">
        <div style="max-width:850px; margin:auto; background:white; padding:60px; box-shadow:0 25px 50px -12px rgba(0,0,0,0.25); position:relative; overflow:hidden;">
            
            <div style="display:flex; justify-content:space-between; align-items:flex-start; border-bottom:2px solid #0f172a; padding-bottom:20px; margin-bottom:30px;">
                <div>
                    <h1 style="margin:0; font-size:28px; font-weight:900; color:#0f172a; letter-spacing:-1px;">STRUCTURAL ANALYSIS REPORT</h1>
                    <p style="margin:5px 0; color:#4b5563; font-size:13px; font-weight:bold;">AISC 360-22 Specification for Structural Steel Buildings</p>
                </div>
                <div style="text-align:right;">
                    <div style="background:{status_color}; color:white; padding:8px 20px; font-weight:900; font-size:18px; border-radius:4px;">{status_text}</div>
                    <p style="margin:5px 0; font-size:12px; color:#6b7280;">REPORT NO: AS-{sec_name}-2026</p>
                </div>
            </div>

            <div style="margin-bottom:30px;">
                <h3 style="background:#0f172a; color:white; padding:8px 15px; font-size:14px; margin-bottom:15px; border-radius:2px;">1. DESIGN INPUTS & BASIS</h3>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:40px;">
                    <table style="width:100%; font-size:13px; border-collapse:collapse;">
                        <tr><td style="padding:6px 0; color:#6b7280;">Analytical Method</td><td style="text-align:right; font-weight:bold;">{method}</td></tr>
                        <tr><td style="padding:6px 0; color:#6b7280;">Steel Grade</td><td style="text-align:right; font-weight:bold;">{steel_grade}</td></tr>
                        <tr><td style="padding:6px 0; color:#6b7280;">Member Profile</td><td style="text-align:right; font-weight:bold;">{sec_name}</td></tr>
                    </table>
                    <table style="width:100%; font-size:13px; border-collapse:collapse;">
                        <tr><td style="padding:6px 0; color:#6b7280;">Design Span</td><td style="text-align:right; font-weight:bold;">{res.get('user_span', 0):.2f} m</td></tr>
                        <tr><td style="padding:6px 0; color:#6b7280;">Unbraced Length (Lb)</td><td style="text-align:right; font-weight:bold;">{res.get('Lb_cm', 0)/100:.2f} m</td></tr>
                        <tr><td style="padding:6px 0; color:#6b7280;">Max Load Capacity</td><td style="text-align:right; font-weight:bold; color:#1e40af;">{res.get('w_safe', 0):,.2f} kg/m</td></tr>
                    </table>
                </div>
            </div>

            <div style="margin-bottom:30px;">
                <h3 style="background:#0f172a; color:white; padding:8px 15px; font-size:14px; margin-bottom:15px; border-radius:2px;">2. PERFORMANCE VERIFICATION (STRENGTH & SERVICEABILITY)</h3>
                <table style="width:100%; border-collapse:collapse; font-size:12px;">
                    <thead>
                        <tr style="background:#f3f4f6; text-align:left; border-bottom:2px solid #0f172a;">
                            <th style="padding:12px; font-weight:900;">LIMIT STATE</th>
                            <th style="padding:12px; font-weight:900;">DEMAND (Ru)</th>
                            <th style="padding:12px; font-weight:900;">CAPACITY (φRn)</th>
                            <th style="padding:12px; font-weight:900;">RATIO</th>
                            <th style="padding:12px; font-weight:900; text-align:center;">STATUS</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr style="border-bottom:1px solid #e5e7eb;">
                            <td style="padding:12px;"><b>Flexure (Moment)</b><br><small>AISC 360-22 Chapter F</small></td>
                            <td style="padding:12px;">{res.get('m_act', 0):,.0f} kg·m</td>
                            <td style="padding:12px;">{res.get('m_cap', 0):,.0f} kg·m</td>
                            <td style="padding:12px;">{r_m:.3f}</td>
                            <td style="padding:12px; text-align:center; font-weight:bold; color:{'#10b981' if r_m <= 1 else '#ef4444'}">{"PASS" if r_m <= 1 else "FAIL"}</td>
                        </tr>
                        <tr style="border-bottom:1px solid #e5e7eb;">
                            <td style="padding:12px;"><b>Shear Strength</b><br><small>AISC 360-22 Chapter G</small></td>
                            <td style="padding:12px;">{res.get('v_act', 0):,.0f} kg</td>
                            <td style="padding:12px;">{res.get('v_cap', 0):,.0f} kg</td>
                            <td style="padding:12px;">{r_v:.3f}</td>
                            <td style="padding:12px; text-align:center; font-weight:bold; color:{'#10b981' if r_v <= 1 else '#ef4444'}">{"PASS" if r_v <= 1 else "FAIL"}</td>
                        </tr>
                        <tr style="border-bottom:1px solid #e5e7eb;">
                            <td style="padding:12px;"><b>Deflection Limit</b><br><small>L/{res.get('defl_denom', 360)} (Serviceability)</small></td>
                            <td style="padding:12px;">{res.get('d_act', 0):.3f} cm</td>
                            <td style="padding:12px;">{res.get('d_all', 0):.3f} cm</td>
                            <td style="padding:12px;">{r_d:.3f}</td>
                            <td style="padding:12px; text-align:center; font-weight:bold; color:{'#10b981' if r_d <= 1 else '#ef4444'}">{"PASS" if r_d <= 1 else "FAIL"}</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div style="margin-bottom:30px;">
                <h3 style="background:#0f172a; color:white; padding:8px 15px; font-size:14px; margin-bottom:15px; border-radius:2px;">3. CONNECTION RECOMMENDATION (TYPICAL)</h3>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:30px; border:1px solid #e5e7eb; padding:25px; border-radius:4px;">
                    
                    <div style="text-align:center;">
                        <svg width="240" height="{svg_height + 40}" viewBox="0 0 240 {svg_height + 40}">
                            <rect x="100" y="20" width="120" height="{svg_height}" fill="#f8fafc" stroke="#64748b" stroke-dasharray="4" />
                            <line x1="100" y1="20" x2="220" y2="20" stroke="#0f172a" stroke-width="4" />
                            <line x1="100" y1="{svg_height + 20}" x2="220" y2="{svg_height + 20}" stroke="#0f172a" stroke-width="4" />
                            <rect x="95" y="35" width="45" height="{conn['plate_h']}" fill="#3b82f6" fill-opacity="0.1" stroke="#3b82f6" stroke-width="2" />
                            <line x1="80" y1="35" x2="80" y2="{35 + conn['plate_h']}" stroke="#64748b" stroke-width="1" />
                            <text x="70" y="{35 + (conn['plate_h']/2)}" font-size="10" fill="#64748b" transform="rotate(-90 70,{35 + (conn['plate_h']/2)})">{conn['plate_h']} mm (PL HT)</text>
                            {bolt_elements}
                            <path d="M 95 40 L 60 10 L 40 10" fill="none" stroke="#ef4444" stroke-width="1" />
                            <text x="35" y="5" font-size="10" fill="#ef4444" font-weight="bold">WELD {conn['weld_size']}mm (TYP)</text>
                        </svg>
                    </div>

                    <div style="font-size:13px; line-height:1.6;">
                        <h4 style="margin:0 0 10px; color:#0f172a;">CONSTRUCTION SPECIFICATION:</h4>
                        <table style="width:100%;">
                            <tr><td style="color:#6b7280;">Plate Size:</td><td style="text-align:right;"><b>PL {conn['plate_t']} x {conn['plate_h']} mm</b></td></tr>
                            <tr><td style="color:#6b7280;">Bolt Specs:</td><td style="text-align:right;"><b>{conn['rows']} No. {bolt.get('size','M20')} (Gr 8.8)</b></td></tr>
                            <tr><td style="color:#6b7280;">Pitch / Edge:</td><td style="text-align:right;"><b>{conn['pitch']} / {conn['edge']} mm</b></td></tr>
                            <tr><td style="color:#6b7280;">Min. Welding:</td><td style="text-align:right;"><b>{conn['weld_size']} mm Fillet</b></td></tr>
                        </table>
                        <div style="margin-top:20px; font-size:11px; color:#4b5563; background:#fef3c7; padding:10px; border-radius:4px; border-left:4px solid #f59e0b;">
                            <b>ENGINEER'S NOTE:</b> Recommended connection based on shear demand. Welding to be performed by AWS-certified welders. Gap between beam end and support not to exceed 12mm.
                        </div>
                    </div>
                </div>
            </div>

            <div style="margin-top:60px; border-top:1px solid #0f172a; padding-top:20px; display:flex; justify-content:space-between; align-items:flex-end;">
                <div style="font-size:10px; color:#9ca3af; max-width:60%;">
                    DISCLAIMER: This automated report is generated for preliminary engineering design. All final structural documentation must be reviewed and stamped by a licensed Professional Engineer (P.E.) in the local jurisdiction.
                </div>
                <div style="text-align:center;">
                    <div style="width:180px; height:60px; border-bottom:1px solid #0f172a; margin-bottom:5px;"></div>
                    <p style="margin:0; font-size:12px; font-weight:900;">SENIOR STRUCTURAL ENGINEER</p>
                    <p style="margin:0; font-size:10px; color:#6b7280;">LICENSED MEMBER ID: GEM-2026-X</p>
                </div>
            </div>
        </div>

        <div style="text-align:center; margin-top:40px;">
            <button onclick="window.print()" style="padding:15px 40px; background:#0f172a; color:white; border:none; border-radius:4px; font-weight:900; cursor:pointer; box-shadow:0 10px 15px -3px rgba(0,0,0,0.1);">
                PRINT PDF REPORT
            </button>
        </div>
    </div>
    """
    
    components.html(html_content, height=1350, scrolling=True)
