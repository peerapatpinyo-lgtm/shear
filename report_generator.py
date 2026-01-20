# report_generator.py
import streamlit as st
from datetime import datetime
import base64

def render(res_ctx, v_res):
    """
    Render Professional Engineering Report
    """
    st.subheader("📑 Engineering Calculation Report")

    # --- 1. REPORT CONTROL PANEL ---
    with st.expander("⚙️ Report Settings", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            proj_name = st.text_input("Project Name", value="Warehouse A - Mezzanine")
            client_name = st.text_input("Client/Owner", value="Siam Construction Co.,Ltd.")
        with c2:
            eng_name = st.text_input("Designed By", value="Eng. Somchai")
            job_no = st.text_input("Job Number", value="S-2024-001")
        with c3:
            rev_no = st.text_input("Revision", value="0")
            report_date = datetime.now().strftime("%d-%b-%Y")
            st.text_input("Date", value=report_date, disabled=True)

    # --- 2. PREPARE DATA ---
    # ถ้ายังไม่ได้คำนวณ ให้ใส่ค่า Default กัน Error
    if not res_ctx:
        st.error("⚠️ Please run calculation in Tab 1 first!")
        return

    # Data Extraction
    sec_name = res_ctx.get('sec_name', '-')
    span = res_ctx.get('user_span', 0)
    
    # Analysis Ratios
    ratio_m = res_ctx.get('ratio_m', 0)
    ratio_v = res_ctx.get('ratio_v', 0)
    ratio_d = res_ctx.get('ratio_d', 0)
    max_ratio = max(ratio_m, ratio_v, ratio_d)
    
    # Status Logic
    is_pass = max_ratio <= 1.0
    status_text = "PASSED" if is_pass else "FAILED"
    status_color = "#16a34a" if is_pass else "#dc2626" # Green / Red
    status_bg = "#dcfce7" if is_pass else "#fee2e2"

    # Connection Data
    if v_res:
        conn_type = v_res.get('type', '-')
        conn_summ = v_res.get('summary', '-')
        conn_pass = v_res.get('pass', False)
        conn_status_txt = "OK" if conn_pass else "NG"
        conn_color = "green" if conn_pass else "red"
    else:
        conn_type, conn_summ, conn_status_txt, conn_color = "-", "Not Designed", "-", "black"

    # --- 3. HTML TEMPLATE (CSS + CONTENT) ---
    html_content = f"""
    <html>
    <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&display=swap');
            body {{ font-family: 'Sarabun', sans-serif; color: #333; }}
            .paper {{
                background-color: white;
                width: 210mm;
                min-height: 297mm;
                padding: 15mm;
                margin: auto;
                border: 1px solid #ddd;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
                position: relative;
            }}
            .header {{ border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; display: flex; justify-content: space-between; }}
            .title-box {{ text-align: left; }}
            .meta-box {{ text-align: right; font-size: 14px; }}
            h1 {{ margin: 0; font-size: 24px; color: #1e293b; }}
            h2 {{ font-size: 18px; margin-top: 20px; border-bottom: 1px solid #ccc; padding-bottom: 5px; color: #2563eb; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
            .item {{ margin-bottom: 8px; font-size: 14px; }}
            .label {{ font-weight: bold; color: #555; width: 120px; display: inline-block; }}
            .val {{ font-weight: bold; color: #000; }}
            .status-stamp {{
                position: absolute;
                top: 20px;
                right: 20px;
                border: 3px solid {status_color};
                color: {status_color};
                font-size: 32px;
                font-weight: bold;
                padding: 10px 20px;
                transform: rotate(-15deg);
                opacity: 0.8;
                border-radius: 8px;
            }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
            th {{ background-color: #f8fafc; }}
            .footer {{ margin-top: 50px; font-size: 12px; color: #888; text-align: center; border-top: 1px solid #eee; padding-top: 10px; }}
            .signature {{ margin-top: 40px; display: flex; justify-content: space-between; }}
            .sig-box {{ border-top: 1px solid #333; width: 40%; text-align: center; padding-top: 5px; }}
        </style>
    </head>
    <body>
        <div class="paper">
            <div class="status-stamp">{status_text}</div>

            <div class="header">
                <div class="title-box">
                    <h1>STRUCTURAL CALCULATION</h1>
                    <div style="font-size:14px; color:#666;">Standard: AISC 360-16 ({'LRFD' if res_ctx.get('is_lrfd') else 'ASD'})</div>
                </div>
                <div class="meta-box">
                    <div><strong>Project:</strong> {proj_name}</div>
                    <div><strong>Job No:</strong> {job_no} | <strong>Rev:</strong> {rev_no}</div>
                    <div><strong>Date:</strong> {report_date}</div>
                </div>
            </div>

            <h2>1. Design Parameters</h2>
            <div class="grid">
                <div>
                    <div class="item"><span class="label">Section:</span> <span class="val" style="font-size:16px;">{sec_name}</span></div>
                    <div class="item"><span class="label">Steel Grade:</span> <span class="val">{res_ctx.get('Fy',0)} ksc</span></div>
                    <div class="item"><span class="label">Span (L):</span> <span class="val">{span} m</span></div>
                    <div class="item"><span class="label">Unbraced (Lb):</span> <span class="val">{res_ctx.get('Lb',0)} m</span></div>
                </div>
                <div>
                    <div class="item"><span class="label">Uniform Load:</span> <span class="val">{res_ctx.get('w_load',0):,.0f} kg/m</span></div>
                    <div class="item"><span class="label">Point Load:</span> <span class="val">{res_ctx.get('p_load',0):,.0f} kg</span></div>
                    <div class="item"><span class="label">Max Moment (Mu):</span> <span class="val">{res_ctx.get('m_act',0):,.0f} kg-m</span></div>
                    <div class="item"><span class="label">Max Shear (Vu):</span> <span class="val">{res_ctx.get('v_act',0):,.0f} kg</span></div>
                </div>
            </div>

            <h2>2. Member Capacity Check</h2>
            <table>
                <tr>
                    <th>Check Type</th>
                    <th>Demand</th>
                    <th>Capacity</th>
                    <th>Ratio</th>
                    <th>Result</th>
                </tr>
                <tr>
                    <td style="text-align:left;">Bending Moment</td>
                    <td>{res_ctx.get('m_act',0):,.0f} kg-m</td>
                    <td>{res_ctx.get('mn',0):,.0f} kg-m</td>
                    <td style="font-weight:bold; color:{'red' if ratio_m>1 else 'black'}">{ratio_m:.2f}</td>
                    <td>{'❌ Fail' if ratio_m>1 else '✅ Pass'}</td>
                </tr>
                <tr>
                    <td style="text-align:left;">Shear Force</td>
                    <td>{res_ctx.get('v_act',0):,.0f} kg</td>
                    <td>{res_ctx.get('vn',0):,.0f} kg</td>
                    <td style="font-weight:bold; color:{'red' if ratio_v>1 else 'black'}">{ratio_v:.2f}</td>
                    <td>{'❌ Fail' if ratio_v>1 else '✅ Pass'}</td>
                </tr>
                <tr>
                    <td style="text-align:left;">Deflection</td>
                    <td>{res_ctx.get('defl_act',0):.2f} cm</td>
                    <td>{res_ctx.get('defl_all',0):.2f} cm</td>
                    <td style="font-weight:bold; color:{'red' if ratio_d>1 else 'black'}">{ratio_d:.2f}</td>
                    <td>{'❌ Fail' if ratio_d>1 else '✅ Pass'}</td>
                </tr>
            </table>

            <h2>3. Connection Design Summary</h2>
            <div style="padding: 10px; background-color: #f8fafc; border: 1px dashed #ccc;">
                <div class="item"><span class="label">Type:</span> <span class="val">{conn_type}</span></div>
                <div class="item"><span class="label">Detail:</span> <span class="val">{conn_summ}</span></div>
                <div class="item"><span class="label">Status:</span> <span class="val" style="color:{conn_color}">{conn_status_txt}</span></div>
            </div>

            <div class="signature">
                <div class="sig-box">
                    <br><br>
                    ({eng_name})<br>
                    <strong>Design Engineer</strong>
                </div>
                <div class="sig-box">
                    <br><br>
                    (..........................................)<br>
                    <strong>Approver / Client</strong>
                </div>
            </div>

            <div class="footer">
                Generated by Python Steel Design App | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            </div>
        </div>
    </body>
    </html>
    """

    # --- 4. DISPLAY & DOWNLOAD ---
    
    # Preview
    st.markdown(html_content, unsafe_allow_html=True)
    st.markdown("---")
    
    # Download Button logic
    b64 = base64.b64encode(html_content.encode()).decode()
    href = f'<a href="data:text/html;base64,{b64}" download="Design_Report_{job_no}.html" style="text-decoration:none;">'
    href += f'<button style="background-color:#2563eb; color:white; padding:10px 20px; border:none; border-radius:5px; cursor:pointer; font-weight:bold;">📥 Download HTML Report</button></a>'
    
    c_btn1, c_btn2 = st.columns([1,4])
    with c_btn1:
        st.markdown(href, unsafe_allow_html=True)
    with c_btn2:
        st.caption("👈 Click to download report. You can open it in any browser and Print to PDF.")
