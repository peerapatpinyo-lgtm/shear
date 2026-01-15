import streamlit as st
import base64  # ✅ ต้อง Import ตรงนี้
import datetime

def render_report_tab(project_info, beam_res, conn_res):
    """
    Generate Professional Engineering Calculation Sheet
    """
    
    # 1. Prepare Data
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    logs = conn_res.get('report_data', {})
    
    # Check Status Colors
    status_beam = "✅ PASS" if beam_res['pass'] else "❌ FAIL"
    color_beam = "green" if beam_res['pass'] else "red"
    
    status_conn = "✅ PASS" if conn_res['pass'] else "❌ FAIL"
    color_conn = "green" if conn_res['pass'] else "red"

    # 2. HTML Template
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link href="https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600&display=swap" rel="stylesheet">
        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
        <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        <style>
            body {{ font-family: 'Sarabun', sans-serif; padding: 20px; color: #333; line-height: 1.4; }}
            .header {{ border-bottom: 2px solid #1e3a8a; padding-bottom: 10px; margin-bottom: 20px; }}
            .header h1 {{ color: #1e3a8a; margin: 0; font-size: 24px; }}
            .info-box {{ background: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 20px; }}
            h2 {{ color: #2563eb; font-size: 18px; margin-top: 25px; border-left: 5px solid #2563eb; padding-left: 10px; background: #eff6ff; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }}
            th, td {{ border: 1px solid #cbd5e1; padding: 8px 12px; text-align: left; }}
            th {{ background-color: #f1f5f9; font-weight: 600; color: #334155; }}
            .status-pass {{ color: #16a34a; font-weight: bold; }}
            .status-fail {{ color: #dc2626; font-weight: bold; }}
            .formula-box {{ padding: 10px; margin: 10px 0; background: #fff; border: 1px dashed #cbd5e1; }}
            .footer {{ margin-top: 40px; font-size: 12px; color: #94a3b8; text-align: right; border-top: 1px solid #e2e8f0; pt: 10px; }}
            
            @media print {{
                body {{ padding: 0; }}
                .no-print {{ display: none; }}
            }}
        </style>
    </head>
    <body>
    
    <div class="header">
        <div style="float:right; font-size:12px; text-align:right;">
            <b>Generated:</b> {now}<br>
            <b>Software:</b> Beam Insight V14
        </div>
        <h1>🏗️ STRUCTURAL CALCULATION SHEET</h1>
        <p style="margin:5px 0 0 0; color:#64748b;">Steel Beam & Connection Design according to AISC 360-16</p>
    </div>

    <div class="info-box">
        <table style="border:none;">
            <tr style="border:none;"><td style="border:none; width:50%;"><b>Project:</b> {project_info['name']}</td><td style="border:none;"><b>Engineer:</b> {project_info['eng']}</td></tr>
            <tr style="border:none;"><td style="border:none;"><b>Section:</b> {project_info['sec']}</td><td style="border:none;"><b>Design Method:</b> {project_info['method']}</td></tr>
        </table>
    </div>

    <h2>1. BEAM DESIGN ANALYSIS</h2>
    <table>
        <tr>
            <th>Parameter</th>
            <th>Value</th>
            <th>Limit / Capacity</th>
            <th>Check Result</th>
        </tr>
        <tr>
            <td>Actual Load (w)</td>
            <td><b>{beam_res['w_safe']:,.0f}</b> kg/m</td>
            <td>-</td>
            <td>-</td>
        </tr>
        <tr>
            <td>Shear Force (V)</td>
            <td>{beam_res['v_act']:,.0f} kg</td>
            <td>{beam_res['v_cap']:,.0f} kg</td>
            <td class="{color_beam}">Ratio: {beam_res['v_ratio']:.2f}</td>
        </tr>
        <tr>
            <td>Bending Moment (M)</td>
            <td>{beam_res['m_act']:,.0f} kg-m</td>
            <td>{beam_res['m_cap']:,.0f} kg-m</td>
            <td class="{color_beam}">Ratio: {beam_res['m_ratio']:.2f}</td>
        </tr>
        <tr>
            <td>Deflection (Δ)</td>
            <td>{beam_res['d_act']:.2f} cm</td>
            <td>{beam_res['d_all']:.2f} cm</td>
            <td class="{color_beam}">Ratio: {beam_res['d_ratio']:.2f}</td>
        </tr>
    </table>
    <div style="text-align:right; margin-top:5px; font-weight:bold; font-size:16px;">
        BEAM STATUS: <span class="status-{color_beam}">{status_beam}</span>
    </div>

    <h2>2. CONNECTION DESIGN ({conn_res['conn_type']})</h2>
    
    <p><b>Configuration:</b> {logs.get('bolt_info','-')} | <b>Plate:</b> {logs.get('plate_info','-')}</p>
    
    <table>
        <tr>
            <th>Failure Mode</th>
            <th>Demand ($V_u$)</th>
            <th>Capacity ($R_n$)</th>
            <th>Ratio</th>
            <th>Result</th>
        </tr>
        <tr>
            <td>Bolt Shear Strength</td>
            <td>{conn_res['demand']:,.0f} kg</td>
            <td>{logs.get('cap_shear',0):,.0f} kg</td>
            <td>{conn_res['demand']/logs.get('cap_shear',1):.2f}</td>
            <td class="{ 'status-pass' if conn_res['demand'] <= logs.get('cap_shear',0) else 'status-fail' }">
                { 'OK' if conn_res['demand'] <= logs.get('cap_shear',0) else 'NG' }
            </td>
        </tr>
        <tr>
            <td>Bolt Bearing Strength</td>
            <td>{conn_res['demand']:,.0f} kg</td>
            <td>{logs.get('cap_bear',0):,.0f} kg</td>
            <td>{conn_res['demand']/logs.get('cap_bear',1):.2f}</td>
            <td class="{ 'status-pass' if conn_res['demand'] <= logs.get('cap_bear',0) else 'status-fail' }">
                { 'OK' if conn_res['demand'] <= logs.get('cap_bear',0) else 'NG' }
            </td>
        </tr>
    </table>

    <div class="formula-box">
        <b>Reference Calculation ({logs.get('method','-')}):</b><br>
        1. Bolt Shear Strength ($R_n = F_{{nv}} A_b N_s$):<br>
        $$ {logs.get('Rn_shear',0):,.0f} \\text{{ kg/bolt}} \\times {logs.get('qty',0)} \\text{{ bolts}} = \\mathbf{{ {logs.get('cap_shear',0):,.0f} }} \\text{{ kg}} $$
        <br>
        2. Bearing Strength ($R_n = 1.2 L_c t F_u$):<br>
        $$ {logs.get('Rn_bear',0):,.0f} \\text{{ kg/bolt}} \\times {logs.get('qty',0)} \\text{{ bolts}} = \\mathbf{{ {logs.get('cap_bear',0):,.0f} }} \\text{{ kg}} $$
    </div>

    <div style="text-align:right; margin-top:5px; font-weight:bold; font-size:16px;">
        CONNECTION STATUS: <span class="status-{color_conn}">{status_conn}</span>
    </div>

    <div class="footer">
        End of Report | Verified by: __________________________
    </div>

    </body>
    </html>
    """
    
    # 3. Render in Streamlit
    st.markdown("### 📄 Calculation Report Preview")
    st.components.v1.html(html_content, height=600, scrolling=True)
    
    # ✅ FIX IS HERE: ใช้ base64.b64encode (ไม่ใช่ st.base64)
    b64 = base64.b64encode(html_content.encode()).decode()
    href = f'<a href="data:text/html;base64,{b64}" download="calculation_report.html" style="background:#2563eb; color:white; padding:10px 20px; text-decoration:none; border-radius:5px; font-weight:bold;">📥 Download HTML Report</a>'
    st.markdown(href, unsafe_allow_html=True)
