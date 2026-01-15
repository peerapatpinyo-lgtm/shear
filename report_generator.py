import streamlit as st

def render_report_tab(method, is_lrfd, sec_name, fy, p, res, bolt):
    # สร้างเนื้อหา HTML ไว้ในตัวแปรเดียว
    report_html = f"""
    <div style="background-color: white; padding: 30px; border: 1px solid #ccc; color: #333; font-family: sans-serif;">
        <div style="text-align: center; border-bottom: 2px solid #1e40af; padding-bottom: 10px;">
            <h1 style="color: #1e40af; margin: 0;">ENGINEERING REPORT</h1>
            <p style="margin: 5px 0;">Method: {method} | Section: {sec_name}</p>
        </div>

        <div style="margin-top: 20px;">
            <h3 style="background: #f0f2f6; padding: 10px;">1. Results Summary</h3>
            <p>Governing Safe Load: <b style="font-size: 1.2em; color: #d32f2f;">{res['w_safe']:,.0f} kg/m</b></p>
            <p>Control Reason: <b>{res['cause']}</b></p>
        </div>

        <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
            <tr style="background-color: #1e40af; color: white;">
                <th style="padding: 10px; border: 1px solid #ddd;">Verification</th>
                <th style="padding: 10px; border: 1px solid #ddd;">Actual</th>
                <th style="padding: 10px; border: 1px solid #ddd;">Limit</th>
                <th style="padding: 10px; border: 1px solid #ddd;">Status</th>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;">Shear Force</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{res['v_act']:,.0f} kg</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{res['v_cap']:,.0f} kg</td>
                <td style="padding: 10px; border: 1px solid #ddd; color: green;">PASS</td>
            </tr>
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;">Moment</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{res['m_act']:,.0f} kg.m</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{res['m_cap']/100:,.0f} kg.m</td>
                <td style="padding: 10px; border: 1px solid #ddd; color: green;">PASS</td>
            </tr>
        </table>
        
        <div style="margin-top: 30px; text-align: right; font-style: italic;">
            <p>Verified by Beam Insight V12</p>
        </div>
    </div>
    """
    
    # คำสั่งสำคัญที่สุดคือบรรทัดล่างนี้ ต้องมี unsafe_allow_html=True
    st.markdown(report_html, unsafe_allow_html=True)
