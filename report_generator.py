# report_generator.py
# Version: 8.0 (Official Document Style - Clean & Formal)
import streamlit as st
from datetime import datetime

def render_report_tab(beam_data, conn_data):
    # --- 1. ส่วนตั้งค่า (Input) ---
    st.markdown("### 📄 พิมพ์รายงานรายการคำนวณ")
    
    with st.expander("🛠️ ตั้งค่าหัวกระดาษ", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            project = st.text_input("โครงการ", value="ก่อสร้างโรงจอดรถโครงสร้างเหล็ก")
            owner = st.text_input("เจ้าของงาน", value="คุณสมศักดิ์ รักดี")
        with c2:
            engineer = st.text_input("วิศวกรผู้ออกแบบ", value="นายก่อสร้าง มั่นคง (สย.XXXX)")
            date_str = datetime.now().strftime("%d/%m/%Y")

    if not beam_data:
        st.warning("⚠️ กรุณากดคำนวณที่ Tab 1 ก่อนครับ")
        return

    # --- 2. เตรียมข้อมูล ---
    # ดึงค่าตัวแปร
    sec = beam_data.get('sec_name', '-')
    span = beam_data.get('user_span', 0)
    fy = beam_data.get('Fy', 0)
    
    # ผลลัพธ์
    m_act, m_cap = beam_data.get('m_act', 0), beam_data.get('mn', 0)
    v_act, v_cap = beam_data.get('v_act', 0), beam_data.get('vn', 0)
    d_act, d_all = beam_data.get('defl_act', 0), beam_data.get('defl_all', 0)
    
    r_m, r_v, r_d = beam_data.get('ratio_m', 0), beam_data.get('ratio_v', 0), beam_data.get('ratio_d', 0)
    max_r = max(r_m, r_v, r_d)
    is_pass = max_r <= 1.0

    # --- 3. ส่วนแสดงผลจำลองกระดาษ A4 (Container) ---
    st.markdown("---")
    
    # สร้างกรอบเอกสาร
    with st.container(border=True):
        
        # 3.1 หัวกระดาษ (Header)
        st.markdown(f"""
        <div style="text-align: center; border-bottom: 2px solid black; padding-bottom: 10px; margin-bottom: 20px;">
            <h2 style="margin: 0; color: black;">รายการคำนวณโครงสร้างคานเหล็ก</h2>
            <p style="margin: 5px; color: #555;">STRUCTURAL STEEL BEAM DESIGN CALCULATION</p>
        </div>
        """, unsafe_allow_html=True)

        # ข้อมูลโครงการ
        st.markdown(f"""
        **โครงการ:** {project}  
        **เจ้าของงาน:** {owner}  
        **วิศวกรผู้ออกแบบ:** {engineer}  
        **วันที่คำนวณ:** {date_str}
        """)
        
        st.markdown("---")

        # 3.2 ข้อมูลการออกแบบ (Design Data)
        st.markdown("#### 1. ข้อมูลการออกแบบ (Design Criteria)")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown(f"""
            * **หน้าตัดเหล็ก:** {sec}
            * **มาตรฐานเหล็ก:** JIS / ASTM
            * **กำลังจุดคลาก (Fy):** {fy:,} ksc
            """)
        with col_d2:
            st.markdown(f"""
            * **ความยาวคาน (Span):** {span:.2f} m.
            * **ระยะค้ำยัน (Lb):** {beam_data.get('Lb', 0):.2f} m.
            * **มาตรฐานการออกแบบ:** AISC 360-16 (LRFD)
            """)

        # 3.3 ตารางผลการคำนวณ (Results Table)
        st.markdown("#### 2. ผลการตรวจสอบกำลังรับน้ำหนัก (Calculation Results)")
        
        # ใช้ Column เพื่อจัด Layout แบบตารางที่สะอาดตา
        # Header Row
        h1, h2, h3, h4, h5 = st.columns([2, 1.5, 1.5, 1, 1])
        h1.markdown("**รายการตรวจสอบ**")
        h2.markdown("**แรงที่เกิด (Mu/Vu)**")
        h3.markdown("**แรงที่รับได้ (Mn/Vn)**")
        h4.markdown("**Ratio**")
        h5.markdown("**ผลลัพธ์**")
        st.markdown("<hr style='margin: 5px 0; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)

        # Row 1: Moment
        r1_1, r1_2, r1_3, r1_4, r1_5 = st.columns([2, 1.5, 1.5, 1, 1])
        r1_1.markdown("1. โมเมนต์ดัด (Moment)")
        r1_2.markdown(f"{m_act:,.2f} kg-m")
        r1_3.markdown(f"{m_cap:,.2f} kg-m")
        r1_4.markdown(f"{r_m:.2f}")
        r1_5.markdown(f"{'✅ ผ่าน' if r_m <=1 else '❌ ไม่ผ่าน'}")

        # Row 2: Shear
        r2_1, r2_2, r2_3, r2_4, r2_5 = st.columns([2, 1.5, 1.5, 1, 1])
        r2_1.markdown("2. แรงเฉือน (Shear)")
        r2_2.markdown(f"{v_act:,.2f} kg")
        r2_3.markdown(f"{v_cap:,.2f} kg")
        r2_4.markdown(f"{r_v:.2f}")
        r2_5.markdown(f"{'✅ ผ่าน' if r_v <=1 else '❌ ไม่ผ่าน'}")

        # Row 3: Deflection
        r3_1, r3_2, r3_3, r3_4, r3_5 = st.columns([2, 1.5, 1.5, 1, 1])
        r3_1.markdown("3. การแอ่นตัว (Deflection)")
        r3_2.markdown(f"{d_act:.2f} cm")
        r3_3.markdown(f"{d_all:.2f} cm")
        r3_4.markdown(f"{r_d:.2f}")
        r3_5.markdown(f"{'✅ ผ่าน' if r_d <=1 else '❌ ไม่ผ่าน'}")

        st.markdown("---")

        # 3.4 สรุปผล (Conclusion)
        if is_pass:
            st.success(f"**บทสรุป: โครงสร้างมีความมั่นคงแข็งแรง (PASSED)** | อัตราส่วนการรับแรงสูงสุด = {max_r:.2f}")
        else:
            st.error(f"**บทสรุป: โครงสร้างไม่ผ่านเกณฑ์ (FAILED)** | กรุณาเพิ่มขนาดหน้าตัดหรือลดระยะช่วงพาด")
        
        st.markdown(f"**หมายเหตุจุดต่อ:** {conn_data.get('summary', '-')}")

        # 3.5 ส่วนลงนาม
        st.markdown("<br><br>", unsafe_allow_html=True)
        s1, s2 = st.columns(2)
        with s1:
            st.markdown("..........................................................")
            st.markdown(f"({engineer})")
            st.markdown("วิศวกรผู้ออกแบบ")
        with s2:
            st.markdown("..........................................................")
            st.markdown(f"({owner})")
            st.markdown("ผู้อนุมัติโครงการ")
