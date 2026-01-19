# report_generator.py (V15 - Ultra Professional)
import streamlit as st
import streamlit.components.v1 as components

def render_report_tab(method, is_lrfd, sec_name, steel_grade, p, res, bolt):
    # --- 1. Data Preparation ---
    w_safe = res.get('w_safe', 0)
    cause = res.get('cause', 'N/A')
    
    # Ratios for color logic
    r_v = res.get('v_act', 0) / res.get('v_cap', 1)
    r_m = res.get('m_act', 0) / res.get('m_cap', 1)
    r_d = res.get('d_act', 0) / res.get('d_all', 1)
    max_r = max(r_v, r_m, r_d)
    
    status_text = "PASS" if max_r <= 1.0 else "FAIL"
    status_color = "#16a34a" if max_r <= 1.0 else "#dc2626"

    # --- 2. HTML Template with CSS ---
    html_content = f"""
    <div id="report-page" style="background:#f8fafc; padding:20px; font-family:'Inter', sans-serif;">
        <div style="max-width:850px; margin:auto; background:white; padding:50px; border:1px solid #e2e8f0; box-shadow:0 10px 25px rgba(0,0,0,0.05); border-radius:8px;">
            
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:4px solid #1e40af; padding-bottom:20px;">
                <div>
                    <h1 style="margin:0; color:#1e40af; font-size:24px; letter-spacing:-0.5px;">STRUCTURAL CALCULATION SHEET</h1>
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
                <h3 style="font-size:14px; text-transform:uppercase; color:#1e40af; border-bottom:1px solid #e2e8f0; padding-bottom:5px;">1. Design Parameters</h3>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:40px; margin-top:10px;">
                    <table style="width:100%; font-size:13px; color:#334155;">
                        <tr><td style="padding:4px 0;"><b>Analysis Method:</b></td><td style="text-align:right;">{method}</td></tr>
                        <tr><td style="padding:4px 0;"><b>Steel Grade:</b></td><td style="text-align:right;">{steel_grade}</td></tr>
                        <tr><td style="padding:4px 0;"><b>Selected Section:</b></td><td style="text-align:right;"><b>{sec_name}</b></td></tr>
                    </table>
                    <table style="width:100%; font-size:13px; color:#334155;">
                        <tr><td style="padding:4px 0;"><b>Span Length:</b></td><td style="text-align:right;">{res.get('user_span', 0):.2f} m</td></tr>
                        <tr><td style="padding:4px 0;"><b>Unbraced Length (Lb):</b></td><td style="text-align:right;">{res.get('Lb_cm', 0)/100:.2f} m</td></tr>
                        <tr><td style="padding:4px 0;"><b>Deflection Limit:</b></td><td style="text-align:right;">L/{res.get('defl_denom', 360)}</td></tr>
                    </table>
                </div>
            </div>

            <div style="margin-top:30px;">
                <h3 style="font-size:14px; text-transform:uppercase; color:#1e40af; border-bottom:1px solid #e2e8f0; padding-bottom:5px;">2. Section Geometry & Properties</h3>
                <div style="display:flex; align-items:center; gap:30px; margin-top:10px;">
                    
                    <table style="flex-grow:1; font-size:12px; border-collapse:collapse; color:#334155;">
                        <tr style="border-bottom:1px solid #f1f5f9;"><td style="padding:6px;">Depth (h)</td><td>{p['h']} mm</td><td style="padding:6px;">Inertia (Ix)</td><td>{p['Ix']:,.0f} cm⁴</td></tr>
                        <tr style="border-bottom:1px solid #f1f5f9;"><td style="padding:6px;">Width (b)</td><td>{p['b']} mm</td><td style="padding:6px;">Section Modulus (Sx)</td><td>{p['Sx']:,.0f} cm³</td></tr>
                        <tr style="border-bottom:1px solid #f1f5f9;"><td style="padding:6px;">Web (tw)</td><td>{p['tw']} mm</td><td style="padding:6px;">Plastic Modulus (Zx)</td><td>{p['Zx']:,.0f} cm³</td></tr>
                        <tr style="border-bottom:1px solid #f1f5f9;"><td style="padding:6px;">Flange (tf)</td><td>{p['tf']} mm</td><td style="padding:6px;">Radius of Gyration (ry)</td><td>{res.get('ry',0):.2f} cm</td></tr>
                    </table>
                </div>
            </div>

            <div style="margin-top:30px;">
                <h3 style="font-size:14px; text-transform:uppercase; color:#1e40af; border-bottom:1px solid #e2e8f0; padding-bottom:5px;">3. Verification Results</h3>
                <table style="width:100%; margin-top:10px; border-collapse:collapse; font-size:13px; text-align:left;">
                    <thead>
                        <tr style="background:#f8fafc; color:#1e40af;">
                            <th style="padding:10px; border:1px solid #e2e8f0;">Constraint</th>
                            <th style="padding:10px; border:1px solid #e2e8f0;">Demand</th>
                            <th style="padding:10px; border:1px solid #e2e8f0;">Capacity</th>
                            <th style="padding:10px; border:1px solid #e2e8f0;">Ratio</th>
                            <th style="padding:10px; border:1px solid #e2e8f0;">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="padding:10px; border:1px solid #e2e8f0;">Flexural Capacity (Moment)</td>
                            <td style="padding:10px; border:1px solid #e2e8f0;">{res.get('m_act', 0):,.0f} kg.m</td>
                            <td style="padding:10px; border:1px solid #e2e8f0;">{res.get('m_cap', 1):,.0f} kg.m</td>
                            <td style="padding:10px; border:1px solid #e2e8f0;">{r_m:.3f}</td>
                            <td style="padding:10px; border:1px solid #e2e8f0; color:{r_m > 1 and '#dc2626' or '#16a34a'}; font-weight:bold;">{r_m > 1 and 'FAIL' or 'OK'}</td>
                        </tr>
                        <tr>
                            <td style="padding:10px; border:1px solid #e2e8f0;">Shear Capacity</td>
                            <td style="padding:10px; border:1px solid #e2e8f0;">{res.get('v_act', 0):,.0f} kg</td>
                            <td style="padding:10px; border:1px solid #e2e8f0;">{res.get('v_cap', 1):,.0f} kg</td>
                            <td style="padding:10px; border:1px solid #e2e8f0;">{r_v:.3f}</td>
                            <td style="padding:10px; border:1px solid #e2e8f0; color:{r_v > 1 and '#dc2626' or '#16a34a'}; font-weight:bold;">{r_v > 1 and 'FAIL' or 'OK'}</td>
                        </tr>
                        <tr>
                            <td style="padding:10px; border:1px solid #e2e8f0;">Deflection Control</td>
                            <td style="padding:10px; border:1px solid #e2e8f0;">{res.get('d_act', 0):.3f} cm</td>
                            <td style="padding:10px; border:1px solid #e2e8f0;">{res.get('d_all', 1):.3f} cm</td>
                            <td style="padding:10px; border:1px solid #e2e8f0;">{r_d:.3f}</td>
                            <td style="padding:10px; border:1px solid #e2e8f0; color:{r_d > 1 and '#dc2626' or '#16a34a'}; font-weight:bold;">{r_d > 1 and 'FAIL' or 'OK'}</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div style="margin-top:30px; background:#f1f5f9; padding:15px; border-radius:6px; border:1px solid #e2e8f0;">
                <h4 style="margin:0 0 10px; font-size:13px; color:#1e40af;">Stability Analysis: Lateral-Torsional Buckling</h4>
                <div style="display:flex; justify-content:space-between; font-size:12px; color:#475569;">
                    <span>Plastic Limit (Lp): <b>{res.get('Lp_cm', 0)/100:.2f} m</b></span>
                    <span>Elastic Limit (Lr): <b>{res.get('Lr_cm', 0)/100:.2f} m</b></span>
                    <span>Actual Unbraced (Lb): <b>{res.get('Lb_cm', 0)/100:.2f} m</b></span>
                </div>
                <div style="margin-top:10px; font-size:12px;">
                    Control Regime: <span style="color:#1e40af; font-weight:bold;">{res.get('ltb_zone', 'N/A')}</span>
                </div>
            </div>

            <div style="margin-top:30px;">
                <h3 style="font-size:14px; text-transform:uppercase; color:#1e40af; border-bottom:1px solid #e2e8f0; padding-bottom:5px;">4. Connection Detail</h3>
                <div style="display:flex; gap:20px; align-items:center; margin-top:10px;">
                    
                    <div style="font-size:13px; color:#334155;">
                        Connection Type: <b>{bolt.get('type', 'N/A')}</b><br>
                        Bolt Configuration: <b>{bolt.get('qty', 'N/A')} x {bolt.get('size', 'N/A')} ({bolt.get('grade', 'N/A')})</b><br>
                        Design Reaction Force (V_des): <b>{res.get('v_conn_design', 0):,.0f} kg</b>
                    </div>
                </div>
            </div>

            <div style="margin-top:50px; padding-top:20px; border-top:1px solid #e2e8f0; text-align:center;">
                <p style="font-size:10px; color:#94a3b8; line-height:1.5;">
                    <b>Disclaimer:</b> This calculation is performed based on the provided inputs and AISC 360 standards.<br>
                    The user is responsible for the accuracy of all input data. Final design approval must be made by a licensed structural engineer.
                </p>
                <div style="margin-top:10px; font-size:12px; font-weight:bold; color:#1e40af;">
                    GENERATED ON: 2026-01-19 | BEAM INSIGHT HYBRID ENGINE
                </div>
            </div>
        </div>
        
        <div style="text-align:center; margin-top:30px; padding-bottom:50px;">
            <button onclick="window.print()" style="padding:12px 30px; background:#1e40af; color:white; border:none; border-radius:6px; cursor:pointer; font-weight:700; box-shadow:0 4px 10px rgba(30,64,175,0.3);">
                📄 Download PDF Report
            </button>
        </div>
    </div>
    """
    
    components.html(html_content, height=1200, scrolling=True)
def get_connection_details(res, p, bolt):
    """
    ฟังก์ชันวิเคราะห์และแนะนำจุดต่อที่เหมาะสม (Advisor Logic)
    """
    v_act = res.get('v_act', 0)
    h_beam = p.get('h', 0)
    tw = p.get('tw', 0)
    
    # 1. แนะนำจำนวน Bolt (สมมติกำลัง Bolt 1 ตัวรับได้ประมาณ 3000-4000 kg สำหรับ M20)
    # ในหน้างานจริงควรคำนวณจาก bolt_capacity แต่ตรงนี้ใช้ Logic Advisor
    suggested_rows = max(2, int(v_act / 3500) + 1)
    
    # 2. ขนาดแผ่น Fin Plate (สูงประมาณ 60% ของความลึกคาน)
    plate_h = int((h_beam * 0.6) / 10) * 10 # ปัดเศษเป็นหลักสิบ mm
    plate_t = int(tw + 2) if tw > 0 else 10 # หนาฐานที่ tw+2 หรือขั้นต่ำ 10mm
    
    # 3. ขนาดรอยเชื่อม (Weld Size) ตามมาตรฐาน AISC (Min weld size)
    weld_size = 6 if tw <= 12 else 8 # mm
    
    return {
        "rows": suggested_rows,
        "plate_h": plate_h,
        "plate_t": plate_t,
        "weld": weld_size
    }

# ในฟังก์ชัน render_report_tab ให้เพิ่มส่วนนี้เข้าไปใน HTML:
def render_report_tab(method, is_lrfd, sec_name, steel_grade, p, res, bolt):
    conn = get_connection_details(res, p, bolt)
    
    # เพิ่ม HTML ต่อจากส่วนที่ 4 (Stability) ในเวอร์ชันก่อนหน้า
    connection_html = f"""
    <div style="margin-top:30px; border:2px dashed #1e40af; padding:20px; border-radius:8px; background:#f0f7ff;">
        <h3 style="margin-top:0; color:#1e40af; font-size:16px;">🛠️ RECOMMENDED TYPICAL DETAIL (FIN PLATE)</h3>
        <div style="display:flex; gap:30px; align-items:flex-start;">
            <div style="background:white; padding:10px; border:1px solid #cbd5e1;">
                <svg width="180" height="200" viewBox="0 0 100 120">
                    <rect x="0" y="0" width="20" height="120" fill="#e2e8f0" stroke="#94a3b8"/>
                    <rect x="25" y="20" width="75" height="80" fill="#f8fafc" stroke="#1e40af" stroke-width="2"/>
                    <rect x="20" y="30" width="15" height="60" fill="#1e40af" opacity="0.8"/>
                    {" ".join([f'<circle cx="27" cy="{40 + (i*20)}" r="3" fill="black"/>' for i in range(conn['rows'])])}
                </svg>
                <p style="font-size:10px; text-align:center; color:#64748b;">Schematic Diagram Only</p>
            </div>
            
            <div style="font-size:13px; color:#1e40af; flex-grow:1;">
                <table style="width:100%; border-collapse:collapse;">
                    <tr><td style="padding:5px;"><b>Fin Plate Size:</b></td><td>PL {conn['plate_t']} x {conn['plate_h']} mm</td></tr>
                    <tr><td style="padding:5px;"><b>Bolt Layout:</b></td><td>{conn['rows']} Rows x 1 Column</td></tr>
                    <tr><td style="padding:5px;"><b>Bolt Specs:</b></td><td>{bolt.get('size', 'M20')} (Grade {bolt.get('grade', '8.8')})</td></tr>
                    <tr><td style="padding:5px;"><b>Welding:</b></td><td>Fillet Weld {conn['weld']} mm (E70XX)</td></tr>
                    <tr><td style="padding:5px;"><b>Edge Distance:</b></td><td>Min 1.5d (~30-40 mm)</td></tr>
                </table>
                <p style="margin-top:10px; font-size:11px; color:#475569; font-style:italic;">
                    *คำแนะนำนี้อ้างอิงจากแรงเฉือน {res.get('v_act', 0):,.0f} kg และหน้าตัด {sec_name}
                </p>
            </div>
        </div>
    </div>
    """
    # รวม HTML ทั้งหมดแล้วแสดงผล...
