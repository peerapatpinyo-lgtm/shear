# report_generator.py
import streamlit as st
from datetime import datetime
import base64

# 👇 แก้ชื่อฟังก์ชันตรงนี้ให้ตรงกับที่ app.py เรียกใช้
def render_report_tab(res_ctx, v_res):
    """
    Render Professional Engineering Report (Version 2.0)
    """
    # --- 1. HEADER & SETTINGS ---
    st.subheader("📑 Professional Report (v2.0)") 
    st.markdown("---")

    with st.expander("🛠️ Report Configuration (ตั้งค่าหัวกระดาษ)", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            proj_name = st.text_input("Project Name", value="Proposed Mezzanine Floor")
            client_name = st.text_input("Owner / Client", value="Siam Industry Co., Ltd.")
        with c2:
            eng_name = st.text_input("Engineer Name", value="Mr. Somchai Jai-dee (PE)")
            rev_no = st.text_input("Revision No.", value="Rev.0A")
            
    # --- 2. DATA PREPARATION ---
    if not res_ctx:
        st.warning("⚠️ Waiting for Calculation Data from Tab 1...")
        return

    # Extract Data
    sec_name = res_ctx.get('sec_name', '-')
    span = res_ctx.get('user_span', 0)
    fy = res_ctx.get('Fy', 0)
    
    # Ratios
    r_m = res_ctx.get('ratio_m', 0)
    r_v = res_ctx.get('ratio_v', 0)
    r_d = res_ctx.get('ratio_d', 0)
    max_r = max(r_m, r_v, r_d)
    
    # Status Logic
    is_pass = max_r <= 1.0
    status_text = "APPROVED" if is_pass else "REJECTED"
    status_color = "#22c55e" if is_pass else "#ef4444" # Green / Red
    stamp_border = "double" if is_pass else "solid"

    # Connection Data
    conn_txt = v_res.get('summary', 'N/A') if v_res else "Not Designed"

    # Report Date
    now_str = datetime.now().strftime("%d %B %Y")

    # --- 3. HTML REPORT TEMPLATE ---
    html_code = f"""
    <div style="
        font-family: 'Sarabun', sans-serif;
        background-color: white;
        padding: 40px;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        color: #1f2937;
        position: relative;
    ">
        <div style="
            position: absolute;
            top: 20px;
            right: 20px;
            color: {status_color};
            border: 4px {stamp_border} {status_color};
            padding: 10px 20px;
            font-size: 24px;
            font-weight: 900;
            transform: rotate(-10deg);
            opacity: 0.8;
            letter-spacing: 2px;
        ">{status_text}</div>

        <div style="border-bottom: 3px solid #1e3a8a; padding-bottom: 15px; margin-bottom: 25px;">
            <h2 style="margin:0; color:#1e3a8a; font-size:24px;">STRUCTURAL CALCULATION SHEET</h2>
            <div style="color:#6b7280; font-size:14px; margin-top:5px;">Reference Code: AISC 360-16 (LRFD/ASD)</div>
        </div>

        <table style="width:100%; border-collapse: collapse; margin-bottom: 25px;">
            <tr style="background-color: #f3f4f6;">
                <td style="padding:8px; border:1px solid #d1d5db; font-weight:bold; width:150px;">Project:</td>
                <td style="padding:8px; border:1px solid #d1d5db;">{proj_name}</td>
                <td style="padding:8px; border:1px solid #d1d5db; font-weight:bold; width:100px;">Job No:</td>
                <td style="padding:8px; border:1px solid #d1d5db;">2024-STD-01</td>
            </tr>
            <tr>
                <td style="padding:8px; border:1px solid #d1d5db; font-weight:bold;">Client:</td>
                <td style="padding:8px; border:1px solid #d1d5db;">{client_name}</td>
                <td style="padding:8px; border:1px solid #d1d5db; font-weight:bold;">Date:</td>
                <td style="padding:8px; border:1px solid #d1d5db;">{now_str}</td>
            </tr>
        </table>

        <h3 style="background-color:#1e3a8a; color:white; padding:8px; font-size:16px; margin-bottom:10px;">1. BEAM DESIGN PARAMETERS</h3>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px; margin-bottom:20px;">
            <div>
                <strong>Section Size:</strong> <span style="font-size:1.1em; color:#1d4ed8;">{sec_name}</span><br>
                <strong>Steel Grade (Fy):</strong> {fy} ksc<br>
                <strong>Span Length:</strong> {span} m<br>
            </div>
            <div>
                <strong>Factored Moment (Mu):</strong> {res_ctx.get('m_act',0):,.0f} kg-m<br>
                <strong>Factored Shear (Vu):</strong> {res_ctx.get('v_act',0):,.0f} kg<br>
                <strong>Unbraced Length (Lb):</strong> {res_ctx.get('Lb',0):.2f} m
            </div>
        </div>

        <h3 style="background-color:#1e3a8a; color:white; padding:8px; font-size:16px; margin-bottom:10px;">2. STABILITY & STRENGTH CHECK</h3>
        <table style="width:100%; border-collapse:collapse; text-align:center;">
            <tr style="background-color:#e5e7eb; font-weight:bold;">
                <td style="border:1px solid #9ca3af; padding:8px;">Check Item</td>
                <td style="border:1px solid #9ca3af; padding:8px;">Demand</td>
                <td style="border:1px solid #9ca3af; padding:8px;">Capacity</td>
                <td style="border:1px solid #9ca3af; padding:8px;">Ratio</td>
                <td style="border:1px solid #9ca3af; padding:8px;">Result</td>
            </tr>
            <tr>
                <td style="border:1px solid #d1d5db; padding:8px; text-align:left;">Flexural (Moment)</td>
                <td style="border:1px solid #d1d5db;">{res_ctx.get('m_act',0):,.0f}</td>
                <td style="border:1px solid #d1d5db;">{res_ctx.get('mn',0):,.0f}</td>
                <td style="border:1px solid #d1d5db; font-weight:bold; color:{'red' if r_m > 1 else 'black'}">{r_m:.2f}</td>
                <td style="border:1px solid #d1d5db;">{'✅' if r_m<=1 else '❌'}</td>
            </tr>
            <tr>
                <td style="border:1px solid #d1d5db; padding:8px; text-align:left;">Shear Strength</td>
                <td style="border:1px solid #d1d5db;">{res_ctx.get('v_act',0):,.0f}</td>
                <td style="border:1px solid #d1d5db;">{res_ctx.get('vn',0):,.0f}</td>
                <td style="border:1px solid #d1d5db; font-weight:bold; color:{'red' if r_v > 1 else 'black'}">{r_v:.2f}</td>
                <td style="border:1px solid #d1d5db;">{'✅' if r_v<=1 else '❌'}</td>
            </tr>
            <tr>
                <td style="border:1px solid #d1d5db; padding:8px; text-align:left;">Deflection</td>
                <td style="border:1px solid #d1d5db;">{res_ctx.get('defl_act',0):.2f}</td>
                <td style="border:1px solid #d1d5db;">{res_ctx.get('defl_all',0):.2f}</td>
                <td style="border:1px solid #d1d5db; font-weight:bold; color:{'red' if r_d > 1 else 'black'}">{r_d:.2f}</td>
                <td style="border:1px solid #d1d5db;">{'✅' if r_d<=1 else '❌'}</td>
            </tr>
        </table>

        <h3 style="background-color:#1e3a8a; color:white; padding:8px; font-size:16px; margin-bottom:10px; margin-top:20px;">3. CONNECTION DESIGN</h3>
        <div style="border:1px dashed #6b7280; padding:15px; background-color:#f9fafb;">
            {conn_txt}
        </div>

        <div style="display:flex; justify-content:space-between; margin-top:50px; padding-top:20px;">
            <div style="text-align:center; width:40%; border-top:1px solid black; padding-top:10px;">
                ({eng_name})<br><strong>Structural Engineer</strong>
            </div>
            <div style="text-align:center; width:40%; border-top:1px solid black; padding-top:10px;">
                (...........................................)<br><strong>Approved By</strong>
            </div>
        </div>
        
        <div style="text-align:center; font-size:12px; color:#9ca3af; margin-top:30px;">
            Generated by Streamlit Steel Design App | {now_str}
        </div>
    </div>
    """
    
    # --- 4. RENDER & DOWNLOAD ---
    st.markdown(html_code, unsafe_allow_html=True)
    
    st.markdown("###")
    # ปุ่ม Download
    b64 = base64.b64encode(html_code.encode()).decode()
    href = f'<a href="data:text/html;base64,{b64}" download="Steel_Report_{sec_name}.html">' \
           f'<button style="background-color:#2563eb; color:white; padding:12px 25px; border:none; border-radius:6px; cursor:pointer; font-weight:bold; font-size:16px;">' \
           f'📥 Download Report as HTML</button></a>'
    st.markdown(href, unsafe_allow_html=True)
    st.caption("Tip: Download ไฟล์ HTML แล้วเปิดด้วย Chrome/Edge เพื่อสั่ง Print to PDF")
