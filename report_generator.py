import streamlit as st

def render_report_tab(method, is_lrfd, sec_name, fy, p, res, bolt):
    # ป้องกัน Error หากข้อมูลใน Dictionary มาไม่ครบ
    w_safe = res.get('w_safe', 0)
    cause = res.get('cause', 'N/A')
    v_act = res.get('v_act', 0)
    v_cap = res.get('v_cap', 1) # กันหารศูนย์
    m_act = res.get('m_act', 0)
    m_cap = res.get('m_cap', 1)

    # รวมทุกอย่างเข้าเป็น String เดียว
    # สำคัญ: ห้ามเคาะ Space หรือขึ้นบรรทัดใหม่มั่วซั่วในระหว่าง Tag HTML
    html_content = f"""
    <div style="background-color:#ffffff; padding:30px; border-radius:10px; border:1px solid #d1d5db; font-family:sans-serif; color:#111827;">
        <div style="border-bottom:2px solid #1e40af; margin-bottom:20px; padding-bottom:10px;">
            <h2 style="margin:0; color:#1e40af;">DESIGN CALCULATION REPORT</h2>
            <p style="margin:0; font-size:14px; color:#6b7280;">Steel Beam Verification | Method: {method}</p>
        </div>
        
        <div style="margin-bottom:20px;">
            <table style="width:100%; border-collapse:collapse;">
                <tr>
                    <td style="padding:10px; background:#f3f4f6; font-weight:bold; border:1px solid #e5e7eb;">Selected Section:</td>
                    <td style="padding:10px; border:1px solid #e5e7eb;">{sec_name}</td>
                </tr>
                <tr>
                    <td style="padding:10px; background:#f3f4f6; font-weight:bold; border:1px solid #e5e7eb;">Governing Safe Load:</td>
                    <td style="padding:10px; border:1px solid #e5e7eb; color:#dc2626; font-weight:bold; font-size:18px;">{w_safe:,.0f} kg/m</td>
                </tr>
                <tr>
                    <td style="padding:10px; background:#f3f4f6; font-weight:bold; border:1px solid #e5e7eb;">Failure Mode:</td>
                    <td style="padding:10px; border:1px solid #e5e7eb;">{cause}</td>
                </tr>
            </table>
        </div>

        <h4 style="color:#1e40af;">Capacity Check Details</h4>
        <table style="width:100%; border-collapse:collapse; text-align:center;">
            <thead>
                <tr style="background:#1e40af; color:white;">
                    <th style="padding:8px; border:1px solid #e5e7eb;">Check</th>
                    <th style="padding:8px; border:1px solid #e5e7eb;">Actual</th>
                    <th style="padding:8px; border:1px solid #e5e7eb;">Capacity</th>
                    <th style="padding:8px; border:1px solid #e5e7eb;">Ratio</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="padding:8px; border:1px solid #e5e7eb; text-align:left;">Shear Strength</td>
                    <td style="padding:8px; border:1px solid #e5e7eb;">{v_act:,.0f} kg</td>
                    <td style="padding:8px; border:1px solid #e5e7eb;">{v_cap:,.0f} kg</td>
                    <td style="padding:8px; border:1px solid #e5e7eb; font-weight:bold;">{(v_act/v_cap):.2f}</td>
                </tr>
                <tr>
                    <td style="padding:8px; border:1px solid #e5e7eb; text-align:left;">Moment Resistance</td>
                    <td style="padding:8px; border:1px solid #e5e7eb;">{m_act:,.0f} kg.m</td>
                    <td style="padding:8px; border:1px solid #e5e7eb;">{m_cap/100:,.0f} kg.m</td>
                    <td style="padding:8px; border:1px solid #e5e7eb; font-weight:bold;">{(m_act/(m_cap/100)):.2f}</td>
                </tr>
            </tbody>
        </table>
    </div>
    """
    
    # จุดตาย: ต้องใช้ st.markdown และต้องระบุ unsafe_allow_html=True
    # และ "ห้าม" มีการ return ใดๆ ท้ายฟังก์ชัน
    st.markdown(html_content, unsafe_allow_html=True)
