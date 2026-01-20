# report_generator.py
# Version: 3.6 (Fix Rendering Issue)
import streamlit as st
from datetime import datetime
import base64

def render_report_tab(beam_data, conn_data):
    # --- 1. ส่วนตั้งค่า (User Input) ---
    st.markdown("### 🖨️ ออกแบบเอกสารรายงาน (Report Setup)")
    
    with st.expander("📝 แก้ไขข้อมูลหัวกระดาษ (คลิก)", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            project_name = st.text_input("ชื่อโครงการ", value="โครงการก่อสร้างชั้นลอยโกดังสินค้า")
            owner_name = st.text_input("เจ้าของโครงการ", value="บริษัท สยามอุตสาหกรรม จำกัด")
        with c2:
            engineer_name = st.text_input("วิศวกรผู้ออกแบบ", value="นายสมชาย ใจดี (สย. 12345)")
            doc_no = st.text_input("เลขที่เอกสาร", value="CALC-2024-001")

    st.divider()

    # --- 2. เตรียมข้อมูล ---
    if not beam_data:
        st.warning("⚠️ ไม่พบข้อมูลการคำนวณ กรุณากลับไปกดคำนวณที่ Tab 1 ก่อนครับ")
        return

    # ดึงค่าตัวแปร
    sec_name = beam_data.get('sec_name', '-')
    span = beam_data.get('user_span', 0)
    fy = beam_data.get('Fy', 0)
    
    m_act = beam_data.get('m_act', 0)
    m_cap = beam_data.get('mn', 0)
    ratio_m = beam_data.get('ratio_m', 0)

    v_act = beam_data.get('v_act', 0)
    v_cap = beam_data.get('vn', 0)
    ratio_v = beam_data.get('ratio_v', 0)

    d_act = beam_data.get('defl_act', 0)
    d_all = beam_data.get('defl_all', 0)
    ratio_d = beam_data.get('ratio_d', 0)

    # คำนวณสถานะ
    max_ratio = max(ratio_m, ratio_v, ratio_d)
    is_pass = max_ratio <= 1.0
    curr_date = datetime.now().strftime("%d/%m/") + str(datetime.now().year + 543)

    if is_pass:
        status_text = "อนุมัติ / APPROVED"
        status_color = "#166534" # เขียว
        bg_color = "#f0fdf4"
        stamp_border = "double"
        summary_head = "✅ ผลการตรวจสอบ: ผ่านเกณฑ์ความปลอดภัย"
        summary_msg = f"โครงสร้างสามารถรับน้ำหนักได้ตามมาตรฐาน โดยใช้อัตราส่วนกำลังเพียง {max_ratio*100:.0f}% ของพิกัดที่ยอมให้"
    else:
        status_text = "ไม่อนุมัติ / REJECTED"
        status_color = "#dc2626" # แดง
        bg_color = "#fef2f2"
        stamp_border = "solid"
        summary_head = "❌ ผลการตรวจสอบ: ไม่ผ่านเกณฑ์"
        summary_msg = "โครงสร้างรับน้ำหนักเกินพิกัด (Overload) กรุณาเพิ่มขนาดหน้าตัดเหล็ก หรือลดระยะช่วงพาด"

    conn_summ = conn_data.get('summary', 'รอการออกแบบจุดต่อ')

    # --- 3. สร้าง HTML Template (ต้องชิดซ้ายสุดเพื่อไม่ให้เพี้ยน) ---
    # สังเกต: ผมลบย่อหน้าหน้าบรรทัด HTML ออกหมดเพื่อให้ชัวร์ว่า Render ติดแน่นอน
    html_content = f"""
<div style="font-family: 'Sarabun', sans-serif; padding: 40px; border: 1px solid #ddd; background: white; max-width: 800px; margin: auto; position: relative; color: #333;">
    
    <div style="position: absolute; top: 20px; right: 20px; border: 3px {stamp_border} {status_color}; color: {status_color}; padding: 10px 20px; font-weight: bold; transform: rotate(-5deg); font-size: 18px;">
        {status_text}
    </div>

    <div style="border-bottom: 3px double #333; padding-bottom: 20px; margin-bottom: 30px;">
        <h1 style="margin:0; color:#1e3a8a; font-size: 24px;">รายงานตรวจสอบความมั่นคงแข็งแรง</h1>
        <div style="color:#555; font-size: 14px;">Structural Safety Verification Report (Ref: AISC 360-22)</div>
    </div>

    <table style="width:100%; margin-bottom: 20px; font-size: 14px;">
        <tr>
            <td style="font-weight:bold; width: 120px;">ชื่อโครงการ:</td>
            <td style="border-bottom: 1px dotted #ccc;">{project_name}</td>
        </tr>
        <tr>
            <td style="font-weight:bold;">เจ้าของงาน:</td>
            <td style="border-bottom: 1px dotted #ccc;">{owner_name}</td>
        </tr>
        <tr>
            <td style="font-weight:bold;">วิศวกร:</td>
            <td style="border-bottom: 1px dotted #ccc;">{engineer_name}</td>
        </tr>
    </table>

    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
        <h3 style="margin:0 0 10px 0; font-size: 16px; border-bottom: 1px solid #ddd;">1. ข้อมูลการออกแบบ</h3>
        <p style="margin: 5px 0; font-size: 14px;">
            <b>หน้าตัดเหล็ก:</b> {sec_name} (Fy = {fy:,} ksc)<br>
            <b>ความยาวคาน:</b> {span} ม. | <b>ระยะค้ำยัน (Lb):</b> {beam_data.get('Lb', 0):.2f} ม.
        </p>
    </div>

    <h3 style="font-size: 16px;">2. ผลการตรวจสอบกำลังรับน้ำหนัก</h3>
    <table style="width:100%; border-collapse: collapse; text-align: center; font-size: 14px; margin-bottom: 20px;">
        <tr style="background: #333; color: white;">
            <th style="padding: 8px;">รายการตรวจสอบ</th>
            <th style="padding: 8px;">แรงที่เกิด</th>
            <th style="padding: 8px;">แรงที่รับได้</th>
            <th style="padding: 8px;">ผลลัพธ์</th>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: left;">โมเมนต์ดัด (Moment)</td>
            <td style="border: 1px solid #ddd;">{m_act:,.0f}</td>
            <td style="border: 1px solid #ddd;">{m_cap:,.0f}</td>
            <td style="border: 1px solid #ddd; color: {'green' if ratio_m<=1 else 'red'}; font-weight: bold;">
                {'ผ่าน' if ratio_m<=1 else 'ไม่ผ่าน'} ({ratio_m:.2f})
            </td>
        </tr>
        <tr>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: left;">แรงเฉือน (Shear)</td>
            <td style="border: 1px solid #ddd;">{v_act:,.0f}</td>
            <td style="border: 1px solid #ddd;">{v_cap:,.0f}</td>
            <td style="border: 1px solid #ddd; color: {'green' if ratio_v<=1 else 'red'}; font-weight: bold;">
                {'ผ่าน' if ratio_v<=1 else 'ไม่ผ่าน'} ({ratio_v:.2f})
            </td>
        </tr>
         <tr>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: left;">การแอ่นตัว (Deflection)</td>
            <td style="border: 1px solid #ddd;">{d_act:.2f}</td>
            <td style="border: 1px solid #ddd;">{d_all:.2f}</td>
            <td style="border: 1px solid #ddd; color: {'green' if ratio_d<=1 else 'red'}; font-weight: bold;">
                {'ผ่าน' if ratio_d<=1 else 'ไม่ผ่าน'} ({ratio_d:.2f})
            </td>
        </tr>
    </table>

    <div style="background-color: {bg_color}; border: 1px solid {status_color}; padding: 15px; border-radius: 8px;">
        <div style="font-weight: bold; color: {status_color};">{summary_head}</div>
        <div style="font-size: 14px; margin-top: 5px;">{summary_msg}</div>
        <div style="font-size: 12px; color: #666; margin-top: 10px; border-top: 1px dashed #ccc; padding-top: 5px;">
            หมายเหตุจุดต่อ: {conn_summ}
        </div>
    </div>

    <div style="text-align: center; margin-top: 50px; display: flex; justify-content: space-around;">
        <div>
            <div style="height: 40px; border-bottom: 1px solid #333; width: 150px; margin: auto;"></div>
            <div style="font-size: 12px; margin-top: 5px;">{engineer_name}<br>(วิศวกรผู้ออกแบบ)</div>
        </div>
        <div>
            <div style="height: 40px; border-bottom: 1px solid #333; width: 150px; margin: auto;"></div>
            <div style="font-size: 12px; margin-top: 5px;">ผู้อำนวยการ / ผู้ตรวจสอบ<br>(Approved By)</div>
        </div>
    </div>

</div>
    """

    # --- 4. แสดงผล (จุดสำคัญคือบรรทัดนี้ครับ!) ---
    st.markdown(html_content, unsafe_allow_html=True)
    
    # ปุ่มดาวน์โหลด
    st.markdown("###")
    b64 = base64.b64encode(html_content.encode()).decode()
    href = f'<a href="data:text/html;base64,{b64}" download="Structural_Report.html">' \
           f'<button style="background:#2563eb; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer;">' \
           f'📥 ดาวน์โหลดรายงาน (HTML)</button></a>'
    st.markdown(href, unsafe_allow_html=True)
