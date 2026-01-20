# ==========================================
# 📄 BEAM INSIGHT - REPORT GENERATOR MODULE
# ==========================================
# Filename: report_generator.py
# Version: 3.5 (Thai Professional + Safety Focus)
# Description: Generates HTML reports with layman-friendly terms
# ==========================================

import streamlit as st
from datetime import datetime
import base64

def render_report_tab(beam_data, conn_data):
    """
    Render Professional Engineering Report (Thai Friendly Version)
    รับค่าจาก:
    - beam_data: ข้อมูลการคำนวณคาน (จาก Tab 1)
    - conn_data: ข้อมูลจุดต่อ (จาก Tab 2)
    """
    
    # --- 1. ส่วนตั้งค่าข้อมูลโครงการ (User Input) ---
    st.markdown("### 🖨️ ออกแบบเอกสารรายงาน (Report Setup)")
    st.caption("กรอกข้อมูลโครงการเพื่อสร้างเอกสารสำหรับส่งมอบงาน")
    
    with st.expander("📝 แก้ไขข้อมูลหัวกระดาษ (คลิก)", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            project_name = st.text_input("ชื่อโครงการ/อาคาร", value="โครงการก่อสร้างชั้นลอยเก็บสินค้า")
            owner_name = st.text_input("เจ้าของอาคาร/ลูกค้า", value="คุณสมชาย ใจดี")
        with c2:
            engineer_name = st.text_input("วิศวกรผู้ออกแบบ", value="นายก่อสร้าง รักดี (สย. xxxxx)")
            doc_no = st.text_input("เลขที่เอกสาร", value=f"STR-{datetime.now().strftime('%y%m%d')}-01")

    st.divider()

    # --- 2. ตรวจสอบและดึงข้อมูล (Data Extraction) ---
    if not beam_data:
        st.warning("⚠️ ไม่พบข้อมูลผลการคำนวณ (กรุณากดคำนวณที่ Tab 1 ก่อน)")
        return

    # ดึงค่าตัวแปร (ใช้ .get เพื่อป้องกัน Error)
    sec_name = beam_data.get('sec_name', '-')
    span = beam_data.get('user_span', 0)
    fy = beam_data.get('Fy', 0)
    
    # ดึงค่าแรง (Demand) และ กำลัง (Capacity)
    m_act = beam_data.get('m_act', 0)
    m_cap = beam_data.get('mn', 0) 
    ratio_m = beam_data.get('ratio_m', 0)

    v_act = beam_data.get('v_act', 0)
    v_cap = beam_data.get('vn', 0) 
    ratio_v = beam_data.get('ratio_v', 0)

    d_act = beam_data.get('defl_act', 0)
    d_all = beam_data.get('defl_all', 0)
    ratio_d = beam_data.get('ratio_d', 0)

    # --- 3. ประมวลผลสถานะ (Logic & Human Language) ---
    max_ratio = max(ratio_m, ratio_v, ratio_d)
    is_pass = max_ratio <= 1.0
    
    if is_pass:
        # กรณีผ่าน
        status_text = "อนุมัติ / APPROVED"
        status_color = "#166534" # เขียวเข้ม
        bg_status = "#f0fdf4"    # พื้นหลังเขียวอ่อน
        stamp_border = "double"
        summary_header = "✅ ผลการตรวจสอบ: โครงสร้างมีความมั่นคงแข็งแรง"
        summary_msg = f"""
        จากการวิเคราะห์โครงสร้างพบว่า หน้าตัดเหล็ก <b>{sec_name}</b> สามารถรับน้ำหนักบรรทุกที่กำหนดได้ดีเยี่ยม 
        โดยมีอัตราส่วนการรับแรงสูงสุดเพียง <b>{max_ratio*100:.0f}%</b> ของพิกัดที่ยอมให้ <br>
        (หมายความว่าโครงสร้างยังรับน้ำหนักได้อีก {100-(max_ratio*100):.0f}%)
        """
    else:
        # กรณีไม่ผ่าน
        status_text = "ไม่อนุมัติ / REJECTED"
        status_color = "#dc2626" # แดงเข้ม
        bg_status = "#fef2f2"    # พื้นหลังแดงอ่อน
        stamp_border = "solid"
        summary_header = "❌ ผลการตรวจสอบ: โครงสร้างไม่ปลอดภัย"
        
        # หาสาเหตุเป็นภาษาคน
        reasons = []
        if ratio_m > 1: reasons.append("คานรับแรงดัดไม่ไหว (เสี่ยงหักกลาง)")
        if ratio_v > 1: reasons.append("คานรับแรงเฉือนไม่ไหว (เสี่ยงขาดที่ขั้ว)")
        if ratio_d > 1: reasons.append("คานมีการแอ่นตัวมากเกินไป (ตกท้องช้าง)")
        
        reason_str = " และ ".join(reasons)
        summary_msg = f"""
        <b>ไม่แนะนำให้ก่อสร้าง</b> เนื่องจาก: {reason_str} <br>
        <u>คำแนะนำ:</u> กรุณาเพิ่มขนาดเหล็กให้ใหญ่ขึ้น หรือ ลดระยะห่างระหว่างเสา (Span)
        """

    # ข้อมูลจุดต่อ
    conn_type = conn_data.get('type', '-')
    conn_summ = conn_data.get('summary', 'รอการออกแบบ')
    curr_date = datetime.now().strftime("%d/%m/") + str(datetime.now().year + 543)

    # --- 4. สร้าง HTML Template (Layout & Design) ---
    html_report = f"""
    <link href="https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&display=swap" rel="stylesheet">
    
    <div style="
        font-family: 'Sarabun', sans-serif;
        width: 100%;
        max-width: 800px;
        background-color: white;
        padding: 40px;
        margin: auto;
        border: 1px solid #d1d5db;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        color: #1f2937;
        position: relative;
    ">
        <div style="
            position: absolute;
            top: 20px;
            right: 20px;
            border: 3px {stamp_border} {status_color};
            color: {status_color};
            padding: 10px 20px;
            font-size: 18px;
            font-weight: bold;
            transform: rotate(-10deg);
            opacity: 0.8;
            letter-spacing: 2px;
        ">{status_text}</div>

        <div style="display:flex; align-items:center; border-bottom: 3px double #374151; padding-bottom: 20px; margin-bottom: 25px;">
            <div style="
                width: 70px; 
                height: 70px; 
                background-color: #eff6ff; 
                border-radius: 50%; 
                display:flex; 
                align-items:center; 
                justify-content:center; 
                font-size:35px; 
                margin-right: 20px;
                border: 2px solid #2563eb;
            ">🏗️</div>
            
            <div style="flex-grow: 1;">
                <h1 style="margin:0; font-size:24px; color:#1e3a8a;">
                    รายงานตรวจสอบความมั่นคงแข็งแรงโครงสร้าง
                </h1>
                <h2 style="margin:5px 0 0 0; font-size:16px; color:#4b5563; font-weight:normal;">
                    Structural Design & Safety Verification Report
                </h2>
                <div style="font-size:12px; color:#6b7280; margin-top:8px; background-color:#f3f4f6; padding:4px 8px; border-radius:4px; display:inline-block;">
                    ✅ ออกแบบตามมาตรฐานความปลอดภัยสากล (AISC 360-22 Specification)
                </div>
            </div>
        </div>

        <table style="width:100%; border-collapse: collapse; margin-bottom: 25px; font-size:14px;">
            <tr>
                <td style="font-weight:bold; width:120px; padding:5px;">ชื่อโครงการ:</td>
                <td style="border-bottom:1px dotted #9ca3af; color:#111827;">{project_name}</td>
                <td style="font-weight:bold; width:100px; padding:5px; padding-left:20px;">เลขที่เอกสาร:</td>
                <td style="border-bottom:1px dotted #9ca3af; color:#111827;">{doc_no}</td>
            </tr>
            <tr>
                <td style="font-weight:bold; padding:5px;">เจ้าของงาน:</td>
                <td style="border-bottom:1px dotted #9ca3af; color:#111827;">{owner_name}</td>
                <td style="font-weight:bold; padding:5px; padding-left:20px;">วันที่ตรวจสอบ:</td>
                <td style="border-bottom:1px dotted #9ca3af; color:#111827;">{curr_date}</td>
            </tr>
        </table>

        <div style="background-color:#f8fafc; padding:15px; border-radius:8px; margin-bottom:20px; border:1px solid #e2e8f0;">
            <h3 style="margin:0 0 10px 0; font-size:16px; color:#1e40af; border-bottom:1px solid #cbd5e1; padding-bottom:5px;">
                1. รายละเอียดวัสดุที่ใช้ (Design Parameters)
            </h3>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 20px; font-size:14px;">
                <div>
                    <b>🔹 เหล็กรูปพรรณ (Section):</b> <span style="font-size:16px; font-weight:bold; color:#000;">{sec_name}</span><br>
                    <span style="font-size:12px; color:#666;">(เกรดความแข็งแรง Fy = {fy:,} ksc)</span>
                </div>
                <div>
                    <b>🔹 ความยาวคาน (Span):</b> {span} เมตร<br>
                    <b>🔹 จุดค้ำยันด้านข้าง (Lb):</b> {beam_data.get('Lb', 0):.2f} เมตร
                </div>
            </div>
        </div>

        <h3 style="margin:0 0 10px 0; font-size:16px; color:#1e40af;">
            2. ผลการวิเคราะห์กำลังรับน้ำหนัก (Safety Check)
        </h3>
        <table style="width:100%; border-collapse: collapse; text-align:center; font-size:14px; margin-bottom:25px;">
            <thead>
                <tr style="background-color:#475569; color:white;">
                    <th style="padding:10px; border:1px solid #64748b; width:40%;">รายการตรวจสอบ</th>
                    <th style="padding:10px; border:1px solid #64748b;">แรงที่เกิดขึ้นจริง<br>(Demand)</th>
                    <th style="padding:10px; border:1px solid #64748b;">รับได้สูงสุด<br>(Capacity)</th>
                    <th style="padding:10px; border:1px solid #64748b;">ผลลัพธ์</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="border:1px solid #cbd5e1; padding:8px; text-align:left;">
                        <b>1. การรับแรงดัด (Moment)</b><br>
                        <span style="font-size:12px; color:#6b7280;">⚠️ ความเสี่ยง: คานหักหรืองอตัว</span>
                    </td>
                    <td style="border:1px solid #cbd5e1;">{m_act:,.0f} kg-m</td>
                    <td style="border:1px solid #cbd5e1;">{m_cap:,.0f} kg-m</td>
                    <td style="border:1px solid #cbd5e1;">
                        {f'<span style="color:green; font-weight:bold;">✅ ปลอดภัย</span>' if ratio_m <= 1 else f'<span style="color:red; font-weight:bold;">❌ อันตราย</span>'}
                    </td>
                </tr>
                <tr style="background-color:#f9fafb;">
                    <td style="border:1px solid #cbd5e1; padding:8px; text-align:left;">
                        <b>2. การรับแรงเฉือน (Shear)</b><br>
                        <span style="font-size:12px; color:#6b7280;">⚠️ ความเสี่ยง: คานขาดออกจากกัน</span>
                    </td>
                    <td style="border:1px solid #cbd5e1;">{v_act:,.0f} kg</td>
                    <td style="border:1px solid #cbd5e1;">{v_cap:,.0f} kg</td>
                    <td style="border:1px solid #cbd5e1;">
                        {f'<span style="color:green; font-weight:bold;">✅ ปลอดภัย</span>' if ratio_v <= 1 else f'<span style="color:red; font-weight:bold;">❌ อันตราย</span>'}
                    </td>
                </tr>
                <tr>
                    <td style="border:1px solid #cbd5e1; padding:8px; text-align:left;">
                        <b>3. การแอ่นตัว (Deflection)</b><br>
                        <span style="font-size:12px; color:#6b7280;">⚠️ ความเสี่ยง: คานตกท้องช้าง/สั่นไหว</span>
                    </td>
                    <td style="border:1px solid #cbd5e1;">{d_act:.2f} cm</td>
                    <td style="border:1px solid #cbd5e1;">{d_all:.2f} cm (Max)</td>
                    <td style="border:1px solid #cbd5e1;">
                        {f'<span style="color:green; font-weight:bold;">✅ ผ่านเกณฑ์</span>' if ratio_d <= 1 else f'<span style="color:red; font-weight:bold;">❌ ตกท้องช้าง</span>'}
                    </td>
                </tr>
            </tbody>
        </table>

        <div style="border: 2px solid {status_color}; background-color: {bg_status}; padding:20px; border-radius:10px; margin-bottom:30px;">
            <div style="font-weight:bold; color:{status_color}; font-size:18px; margin-bottom:10px;">
                {summary_header}
            </div>
            <div style="font-size:14px; line-height:1.6; color:#374151;">
                {summary_msg}
            </div>
            <hr style="border:0; border-top:1px dashed #cbd5e1; margin:15px 0;">
            <div style="font-size:13px; color:#4b5563;">
                <b>🔩 หมายเหตุงานจุดต่อ (Connection):</b> เลือกใช้แบบ {conn_type} ({conn_summ})
            </div>
        </div>

        <div style="display:flex; justify-content: space-between; margin-top:60px;">
            <div style="text-align:center; width:45%;">
                <div style="border-bottom:1px solid #000; height:30px;"></div>
                <div style="margin-top:8px; font-weight:bold;">{engineer_name}</div>
                <div style="font-size:12px; color:#666;">วิศวกรโครงสร้าง (Structural Engineer)</div>
            </div>
            <div style="text-align:center; width:45%;">
                <div style="border-bottom:1px solid #000; height:30px;"></div>
                <div style="margin-top:8px; font-weight:bold;">(.......................................................)</div>
                <div style="font-size:12px; color:#666;">ผู้ตรวจสอบ / เจ้าของโครงการ (Inspector)</div>
            </div>
        </div>
        
        <div style="text-align:center; font-size:11px; color:#9ca3af; margin-top:50px;">
            เอกสารนี้สร้างโดยระบบอัตโนมัติ Beam Insight Hybrid Engine | ข้อมูล ณ วันที่ {datetime.now().strftime("%d/%m/%Y %H:%M")}
        </div>
    </div>
    """

    # --- 5. แสดงผลบนหน้าเว็บ ---
    st.markdown(html_report, unsafe_allow_html=True)
    
    st.markdown("###")
    col_dl1, col_dl2 = st.columns([1, 2])
    
    with col_dl1:
        # สร้างปุ่มดาวน์โหลด
        b64 = base64.b64encode(html_report.encode()).decode()
        file_name = f"Safety_Report_{sec_name}_{datetime.now().strftime('%Y%m%d')}.html"
        href = f'<a href="data:text/html;base64,{b64}" download="{file_name}">' \
               f'<button style="width:100%; background-color:#2563eb; color:white; padding:12px; border:none; border-radius:6px; cursor:pointer; font-weight:bold; font-size:16px; box-shadow: 0 4px 6px rgba(37, 99, 235, 0.3);">' \
               f'📥 ดาวน์โหลดเอกสาร (HTML)</button></a>'
        st.markdown(href, unsafe_allow_html=True)

    with col_dl2:
         st.markdown("""
         <div style="background-color:#f0f9ff; padding:10px; border-radius:6px; font-size:14px; color:#0369a1; border:1px solid #bae6fd;">
            ℹ️ <b>วิธีบันทึกเป็น PDF:</b> กดปุ่มดาวน์โหลด > เปิดไฟล์ด้วย Chrome > กด Ctrl+P (Print) > เลือก "Save as PDF"
         </div>
         """, unsafe_allow_html=True)

# End of report_generator.py
