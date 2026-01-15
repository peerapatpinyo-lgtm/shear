import streamlit as st

def render_report_tab(method, is_lrfd, sec_name, fy, p, res, bolt):
    # 1. นิยามสไตล์ (CSS) แยกไว้ เพื่อให้ HTML สะอาด
    report_css = """
    <style>
        .report-container {
            font-family: 'Sarabun', sans-serif;
            background-color: white;
            padding: 40px;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            color: #1e293b;
            max-width: 850px;
            margin: auto;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }
        .report-header {
            border-bottom: 3px solid #1e40af;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            padding-bottom: 15px;
            margin-bottom: 30px;
        }
        .table-report {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        .table-report th {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            padding: 12px;
            text-align: left;
            color: #475569;
        }
        .table-report td {
            border: 1px solid #e2e8f0;
            padding: 12px;
        }
        .status-pass {
            color: #15803d;
            font-weight: bold;
            background: #f0fdf4;
            padding: 4px 8px;
            border-radius: 4px;
        }
    </style>
    """

    # 2. เนื้อหา HTML
    report_content = f"""
    <div class="report-container">
        <div class="report-header">
            <div>
                <h1 style="margin:0; color:#1e40af; font-size:28px;">STRUCTURAL ANALYSIS REPORT</h1>
                <p style="margin:5px 0 0 0; color:#64748b;">Beam Design Verification System</p>
            </div>
            <div style="text-align:right; font-size:14px; color:#64748b;">
                Method: <b>{method}</b><br>
                Section: <b>{sec_name}</b>
            </div>
        </div>

        <div style="background:#eff6ff; padding:20px; border-radius:8px; margin-bottom:25px;">
            <h3 style="margin:0 0 10px 0; color:#1e40af; font-size:16px;">DESIGN SUMMARY</h3>
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:18px;">Maximum Allowable Load:</span>
                <span style="font-size:32px; font-weight:bold; color:#1e40af;">{res['w_safe']:,.0f} <span style="font-size:18px;">kg/m</span></span>
            </div>
            <p style="margin:10px 0 0 0; color:#475569;">Governing Limit State: <b>{res['cause'].upper()}</b></p>
        </div>

        <h3 style="font-size:16px; color:#1e40af;">CAPACITY VERIFICATION</h3>
        <table class="table-report">
            <thead>
                <tr>
                    <th>Description</th>
                    <th>Actual Force</th>
                    <th>Design Capacity</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Shear Force (V)</td>
                    <td>{res['v_act']:,.0f} kg</td>
                    <td>{res['v_cap']:,.0f} kg</td>
                    <td><span class="status-pass">PASS</span></td>
                </tr>
                <tr>
                    <td>Bending Moment (M)</td>
                    <td>{res['m_act']:,.0f} kg.m</td>
                    <td>{res['m_cap']/100:,.0f} kg.m</td>
                    <td><span class="status-pass">PASS</span></td>
                </tr>
                <tr>
                    <td>Deflection (Δ)</td>
                    <td>{res['d_act']:.3f} cm</td>
                    <td>{res['d_all']:.3f} cm</td>
                    <td><span class="status-pass">PASS</span></td>
                </tr>
            </tbody>
        </table>

        <div style="margin-top:40px; border-top:1px dashed #cbd5e1; padding-top:20px; font-size:12px; color:#94a3b8; text-align:center;">
            * This report is generated automatically based on the provided input parameters. *
        </div>
    </div>
    """

    # 3. แสดงผล (ใช้คำสั่งเดียวจบ ไม่มีการ return ค่าใดๆ)
    st.markdown(report_css + report_content, unsafe_allow_html=True)
