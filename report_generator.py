# report_generator.py
# Version 3.0: Thai Professional Edition
import streamlit as st
from datetime import datetime
import base64

def render_report_tab(beam_data, conn_data):
    """
    Render Professional Engineering Report (Thai Language Version)
    """
    # --- 1. ส่วนหัวและตั้งค่า (User Input) ---
    st.markdown("### 📑 ออกแบบรายการคำนวณ (Report Generation)")
    st.caption("ระบบจะดึงค่าจากการคำนวณใน Tab ก่อนหน้ามาสร้างเป็นรายงานภาษาไทยโดยอัตโนมัติ")
    st.markdown("---")

    # กล่องตั้งค่าข้อมูลโครงการ
    with st.expander("📝 แก้ไขหัวกระดาษ (คลิกเพื่อเปิด)", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            project_name = st.text_input("ชื่อโครงการ (Project)", value="โครงการก่อสร้างชั้นลอยโกดังสินค้า")
            owner_name = st.text_input("เจ้าของโครงการ (Owner)", value="บริษัท สยามอุตสาหกรรม จำกัด")
        with c2:
            engineer_name = st.text_input("วิศวกรผู้ออกแบบ (Engineer)", value="นายสมชาย ใจดี (สย. 12345)")
            doc_no = st.text_input("เลขที่เอกสาร (Doc No.)", value="CALC-2024-001")

    # --- 2. เตรียมข้อมูล (Data Preparation) ---
    if not beam_data:
        st.warning("⚠️ ไม่พบข้อมูลการคำนวณ กรุณากลับไปกดคำนวณที่ Tab 1 ก่อนครับ")
        return

    # ดึงค่าตัวแปร
    sec_name = beam_data.get('sec_name', '-')
    span = beam_data.get('user_span', 0)
    fy = beam_data.get('Fy', 0)
    
    # ดึงค่าแรงและการตรวจสอบ
    m_act = beam_data.get('m_act', 0)
    m_cap = beam_data.get('mn', 0)  # ใช้ key 'mn' ตามที่ส่งมา
    ratio_m = beam_data.get('ratio_m', 0)

    v_act = beam_data.get('v_act', 0)
    v_cap = beam_data.get('vn', 0)  # ใช้ key 'vn' ตามที่ส่งมา
    ratio_v = beam_data.get('ratio_v', 0)

    d_act = beam_data.get('defl_act', 0)
    d_all = beam_data.get('defl_all', 0)
    ratio_d = beam_data.get('ratio_d', 0)

    # ประมวลผลสถานะ (Logic)
    max_ratio = max(ratio_m, ratio_v, ratio_d)
    is_pass = max_ratio <= 1.0
    
    # ข้อความสรุปผล (Human Language)
    if is_pass:
        status_text = "อนุมัติ / APPROVED"
        status_color = "#166534" # Green
        stamp_border = "double"
        summary_msg = f"✅ **ผลการตรวจสอบ: ผ่านเกณฑ์มาตรฐาน** <br>โครงสร้างสามารถรับน้ำหนักได้ปลอดภัย โดยมีอัตราส่วนการใช้งานสูงสุดที่ {max_ratio:.2f} (คิดเป็น {max_ratio*100:.0f}% ของกำลังรับน้ำหนัก)"
    else:
        status_text = "ไม่อนุมัติ / REJECTED"
        status_color = "#dc2626" # Red
        stamp_border = "solid"
        
        # หาสาเหตุที่ไม่ผ่าน
        reasons = []
        if ratio_m > 1: reasons.append("โมเมนต์ดัดเกินพิกัด (คานรับแรงดัดไม่ไหว)")
        if ratio_v > 1: reasons.append("แรงเฉือนเกินพิกัด (คานขาด)")
        if ratio_d > 1: reasons.append("ระยะแอ่นตัวเกินกำหนด (คานตกท้องช้าง)")
        reason_str = ", ".join(reasons)
        summary_msg = f"❌ **ผลการตรวจสอบ: ไม่ผ่านเกณฑ์** <br>เนื่องจาก: {reason_str} <br>คำแนะนำ: กรุณาเพิ่มขนาดหน้าตัดเหล็ก หรือลดระยะช่วงพาด (Span)"

    # ข้อมูลจุดต่อ (Connection)
    conn_summary = conn_data.get('summary', 'ยังไม่ได้ออกแบบจุดต่อ')
    conn_type = conn_data.get('type', '-')

    # วันที่ปัจจุบัน
    curr_date = datetime.now().strftime("%d/%m/") + str(datetime.now().year + 543) # พ.ศ.

    # --- 3. สร้าง HTML Template (Design) ---
    # ใช้ CSS จัดหน้าให้เหมือนกระดาษ A4 จริงๆ
    html_report = f"""
    <link href="https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&display=swap" rel="stylesheet">
    <div style="
        font-family: 'Sarabun', sans-serif;
        width: 100%;
        max-width: 800px;
        background-color: white;
        padding: 40px;
        margin: auto;
        border: 1px solid #e5e7eb;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        color: #333;
        position: relative;
    ">
        <div style="
            position: absolute;
            top: 30px;
            right: 30px;
            border: 3px {stamp_border} {status_color};
            color: {status_color};
            padding: 10px 20px;
            font-size: 20px;
            font-weight: bold;
            transform: rotate(-5deg);
            opacity: 0.9;
        ">{status_text}</div>

        <div style="text-align:center; border-bottom: 2px solid #333; padding-bottom: 15px; margin-bottom: 20px;">
            <h2 style="margin:0; color:#000;">รายการคำนวณโครงสร้างเหล็กรูปพรรณ</h2>
            <div style="font-size:14px; color:#555;">อ้างอิงมาตรฐาน: AISC 360-22 (Specification for Structural Steel Buildings)</div>
        </div>

        <table style="width:100%; border-collapse: collapse; margin-bottom: 20px; font-size:14px;">
            <tr>
                <td style="font-weight:bold; width:120px;">ชื่อโครงการ:</td>
                <td style="border-bottom:1px dotted #999;">{project_name}</td>
                <td style="font-weight:bold; width:100px; padding-left:20px;">เลขที่เอกสาร:</td>
                <td style="border-bottom:1px dotted #999;">{doc_no}</td>
            </tr>
            <tr>
                <td style="font-weight:bold;">เจ้าของงาน:</td>
                <td style="border-bottom:1px dotted #999;">{owner_name}</td>
                <td style="font-weight:bold; padding-left:20px;">วันที่:</td>
                <td style="border-bottom:1px dotted #999;">{curr_date}</td>
            </tr>
        </table>

        <div style="background-color:#f3f4f6; padding:10px; border-radius:4px; margin-bottom:15px;">
            <h3 style="margin:0 0 10px 0; font-size:16px; border-bottom:1px solid #ccc; padding-bottom:5px;">1. ข้อมูลการออกแบบ (Design Parameters)</h3>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size:14px;">
                <div>
                    <b>ขนาดหน้าตัด (Section):</b> <span style="color:#0044cc; font-weight:bold;">{sec_name}</span><br>
                    <b>เกรดเหล็ก (Steel Grade):</b> Fy = {fy:,} ksc<br>
                    <b>ความยาวคาน (Span):</b> {span} เมตร
                </div>
                <div>
                    <b>โมเมนต์ดัดที่เกิดขึ้น (Mu):</b> {m_act:,.0f} kg-m<br>
                    <b>แรงเฉือนที่เกิดขึ้น (Vu):</b> {v_act:,.0f} kg<br>
                    <b>ระยะค้ำยันด้านข้าง (Lb):</b> {beam_data.get('Lb', 0):.2f} เมตร
                </div>
            </div>
        </div>

        <h3 style="margin:0 0 10px 0; font-size:16px;">2. ผลการตรวจสอบกำลังรับน้ำหนัก (Structural Check)</h3>
        <table style="width:100%; border-collapse: collapse; text-align:center; font-size:14px; margin-bottom:20px;">
            <thead>
                <tr style="background-color:#374151; color:white;">
                    <th style="padding:8px; border:1px solid #666;">รายการตรวจสอบ<br>(Check Item)</th>
                    <th style="padding:8px; border:1px solid #666;">แรงที่เกิดขึ้น<br>(Demand)</th>
                    <th style="padding:8px; border:1px solid #666;">กำลังที่รับได้<br>(Capacity)</th>
                    <th style="padding:8px; border:1px solid #666;">อัตราส่วน<br>(Ratio)</th>
                    <th style="padding:8px; border:1px solid #666;">ผลลัพธ์<br>(Result)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="border:1px solid #ccc; padding:8px; text-align:left;"><b>โมเมนต์ดัด (Flexural)</b><br><span style="font-size:12px; color:#666;">ตรวจสอบการรับแรงดัด</span></td>
                    <td style="border:1px solid #ccc;">{m_act:,.0f}</td>
                    <td style="border:1px solid #ccc;">{m_cap:,.0f}</td>
                    <td style="border:1px solid #ccc; font-weight:bold; color:{'red' if ratio_m > 1 else 'black'}">{ratio_m:.2f}</td>
                    <td style="border:1px solid #ccc;">{'✅ ผ่าน' if ratio_m<=1 else '❌ ไม่ผ่าน'}</td>
                </tr>
                <tr style="background-color:#f9fafb;">
                    <td style="border:1px solid #ccc; padding:8px; text-align:left;"><b>แรงเฉือน (Shear)</b><br><span style="font-size:12px; color:#666;">ตรวจสอบการรับแรงตัดขาด</span></td>
                    <td style="border:1px solid #ccc;">{v_act:,.0f}</td>
                    <td style="border:1px solid #ccc;">{v_cap:,.0f}</td>
                    <td style="border:1px solid #ccc; font-weight:bold; color:{'red' if ratio_v > 1 else 'black'}">{ratio_v:.2f}</td>
                    <td style="border:1px solid #ccc;">{'✅ ผ่าน' if ratio_v<=1 else '❌ ไม่ผ่าน'}</td>
                </tr>
                <tr>
                    <td style="border:1px solid #ccc; padding:8px; text-align:left;"><b>การแอ่นตัว (Deflection)</b><br><span style="font-size:12px; color:#666;">ตรวจสอบระยะตกท้องช้าง</span></td>
                    <td style="border:1px solid #ccc;">{d_act:.2f} cm</td>
                    <td style="border:1px solid #ccc;">{d_all:.2f} cm</td>
                    <td style="border:1px solid #ccc; font-weight:bold; color:{'red' if ratio_d > 1 else 'black'}">{ratio_d:.2f}</td>
                    <td style="border:1px solid #ccc;">{'✅ ผ่าน' if ratio_d<=1 else '❌ ไม่ผ่าน'}</td>
                </tr>
            </tbody>
        </table>

        <div style="border: 2px solid {status_color}; background-color: {'#f0fdf4' if is_pass else '#fef2f2'}; padding:15px; border-radius:8px; margin-bottom:30px;">
            <div style="font-weight:bold; color:{status_color}; font-size:16px; margin-bottom:5px;">สรุปผลวิศวกรรม (Engineering Summary):</div>
            <div style="font-size:14px; line-height:1.6;">{summary_msg}</div>
            <hr style="border:0; border-top:1px dashed #ccc; margin:10px 0;">
            <div style="font-size:13px; color:#555;">
                <b>ข้อมูลจุดต่อ (Connection):</b> ประเภท {conn_type} | {conn_summary}
            </div>
        </div>

        <div style="display:flex; justify-content: space-between; margin-top:50px;">
            <div style="text-align:center; width:45%;">
                <div style="border-bottom:1px solid #000; height:30px;"></div>
                <div style="margin-top:5px; font-weight:bold;">{engineer_name}</div>
                <div style="font-size:12px;">วิศวกรผู้ออกแบบ (Structural Engineer)</div>
            </div>
            <div style="text-align:center; width:45%;">
                <div style="border-bottom:1px solid #000; height:30px;"></div>
                <div style="margin-top:5px; font-weight:bold;">(.......................................................)</div>
                <div style="font-size:12px;">ผู้อำนวยการโครงการ / ผู้ตรวจสอบ (Approved By)</div>
            </div>
        </div>
        
        <div style="text-align:center; font-size:10px; color:#999; margin-top:40px;">
            เอกสารนี้สร้างโดยระบบอัตโนมัติ Beam Insight Hybrid Engine | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        </div>
    </div>
    """

    # --- 4. แสดงผลและปุ่มดาวน์โหลด ---
    # แสดงตัวอย่างบนหน้าเว็บ
    st.markdown(html_report, unsafe_allow_html=True)
    
    st.markdown("###")
    col_d1, col_d2 = st.columns([1, 2])
    with col_d1:
        # แปลง HTML เป็นไฟล์ดาวน์โหลด
        b64 = base64.b64encode(html_report.encode()).decode()
        file_name = f"Calculation_Report_{sec_name}_{datetime.now().strftime('%Y%m%d')}.html"
        href = f'<a href="data:text/html;base64,{b64}" download="{file_name}">' \
               f'<button style="width:100%; background-color:#2563eb; color:white; padding:12px; border:none; border-radius:6px; cursor:pointer; font-weight:bold; font-size:16px;">' \
               f'📥 ดาวน์โหลดรายงาน (HTML)</button></a>'
        st.markdown(href, unsafe_allow_html=True)
    
    with col_d2:
        st.info("💡 **Tips:** ดาวน์โหลดไฟล์ HTML แล้วเปิดด้วย Google Chrome > คลิกขวา > สั่งพิมพ์ (Print) > เลือก **Save as PDF** เพื่อให้ได้เอกสาร PDF ที่สวยงาม")
