# report_generator.py
# Version: 9.0 (Full Specification Edition)
import streamlit as st
from datetime import datetime

def render_report_tab(beam_data, conn_data):
    # --- 1. ส่วนตั้งค่า (Input) ---
    st.markdown("### 📄 พิมพ์รายงานรายการคำนวณ")
    
    with st.expander("🛠️ ตั้งค่าหัวกระดาษ", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            project = st.text_input("โครงการ", value="งานโครงสร้างเหล็กชั้นลอย")
            owner = st.text_input("เจ้าของงาน", value="คุณสมศักดิ์ รักดี")
        with c2:
            engineer = st.text_input("วิศวกรผู้ออกแบบ", value="นายก่อสร้าง มั่นคง (สย.XXXX)")
            date_str = datetime.now().strftime("%d/%m/%Y")

    if not beam_data:
        st.warning("⚠️ กรุณากดคำนวณที่ Tab 1 ก่อนครับ")
        return

    # --- 2. เตรียมข้อมูล ---
    # ดึงค่าตัวแปรคาน
    sec = beam_data.get('sec_name', '-')
    span = beam_data.get('user_span', 0)
    fy = beam_data.get('Fy', 0)
    
    m_act, m_cap = beam_data.get('m_act', 0), beam_data.get('mn', 0)
    v_act, v_cap = beam_data.get('v_act', 0), beam_data.get('vn', 0)
    d_act, d_all = beam_data.get('defl_act', 0), beam_data.get('defl_all', 0)
    
    r_m, r_v, r_d = beam_data.get('ratio_m', 0), beam_data.get('ratio_v', 0), beam_data.get('ratio_d', 0)
    max_r = max(r_m, r_v, r_d)
    is_pass = max_r <= 1.0

    # ดึงข้อมูลจุดต่อ
    conn_type = conn_data.get('type', '-')
    conn_summ = conn_data.get('summary', '-')

    # --- 3. ส่วนแสดงผลจำลองกระดาษ A4 ---
    st.markdown("---")
    
    with st.container(border=True):
        
        # 3.1 หัวกระดาษ (Header)
        st.markdown(f"""
        <div style="text-align: center; border-bottom: 3px double #333; padding-bottom: 15px; margin-bottom: 20px;">
            <h2 style="margin: 0; color: #1e3a8a;">รายการคำนวณโครงสร้าง (Structural Calculation)</h2>
            <p style="margin: 5px; color: #555; font-size: 14px;">มาตรฐานอ้างอิง: AISC 360-16 (LRFD/ASD Specification)</p>
        </div>
        """, unsafe_allow_html=True)

        # ข้อมูลโครงการ
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.markdown(f"**โครงการ:** {project}")
            st.markdown(f"**เจ้าของงาน:** {owner}")
        with col_info2:
            st.markdown(f"**วิศวกร:** {engineer}")
            st.markdown(f"**วันที่:** {date_str}")
        
        st.markdown("---")

        # 3.2 ข้อมูลการออกแบบ (Design Criteria)
        st.markdown("#### 1. ข้อมูลการออกแบบ (Design Criteria)")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown(f"""
            * **หน้าตัดเหล็ก:** {sec}
            * **กำลังจุดคลาก (Fy):** {fy:,} ksc
            """)
        with col_d2:
            st.markdown(f"""
            * **ความยาวคาน (Span):** {span:.2f} m.
            * **ระยะค้ำยัน (Lb):** {beam_data.get('Lb', 0):.2f} m.
            """)

        # 3.3 ตารางผลการคำนวณ (Results Table)
        st.markdown("#### 2. ผลการตรวจสอบกำลังรับน้ำหนัก (Beam Analysis)")
        
        # Header Row
        h1, h2, h3, h4, h5 = st.columns([2, 1.5, 1.5, 1, 1])
        h1.markdown("**รายการตรวจสอบ**")
        h2.markdown("**Demand**")
        h3.markdown("**Capacity**")
        h4.markdown("**Ratio**")
        h5.markdown("**ผลลัพธ์**")
        st.markdown("<hr style='margin: 5px 0; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)

        # Rows
        def row(label, act, cap, unit, ratio):
            c1, c2, c3, c4, c5 = st.columns([2, 1.5, 1.5, 1, 1])
            c1.markdown(label)
            c2.markdown(f"{act:,.2f} {unit}")
            c3.markdown(f"{cap:,.2f} {unit}")
            c4.markdown(f"{ratio:.2f}")
            c5.markdown(f"{'✅ ผ่าน' if ratio <=1 else '❌ ไม่ผ่าน'}")

        row("1. โมเมนต์ดัด (Moment)", m_act, m_cap, "kg-m", r_m)
        row("2. แรงเฉือน (Shear)", v_act, v_cap, "kg", r_v)
        row("3. การแอ่นตัว (Deflection)", d_act, d_all, "cm", r_d)

        st.markdown("---")

        # 3.4 รายละเอียดจุดต่อ (Connection Specification) - ส่วนที่เพิ่มใหม่!
        st.markdown("#### 3. รายละเอียดจุดต่อและข้อกำหนดวัสดุ (Connection Specs)")
        
        with st.container():
            col_c1, col_c2 = st.columns([1.5, 2])
            
            with col_c1:
                st.markdown(f"**รูปแบบจุดต่อ:** {conn_type}")
                st.info(f"📋 **สรุปผลออกแบบ:**\n{conn_summ}")
            
            with col_c2:
                st.markdown("**ข้อกำหนดวัสดุประกอบ (Standard Specifications):**")
                st.markdown("""
                - **น็อตสกรู (Bolts):** ASTM A325 / ISO 8.8 (High Strength)
                - **ลวดเชื่อม (Electrodes):** E70xx (Low Hydrogen) 
                - **รูเจาะ (Holes):** Standard Hole (ขนาดน็อต + 1.5-2 มม.)
                - **การติดตั้ง:** ขันแน่นพอตึงมือ (Snug-tightened) หรือตามระบุในแบบ
                """)

        st.markdown("---")

        # 3.5 สรุปและลงนาม
        if is_pass:
            st.success(f"**บทสรุปทางวิศวกรรม:** โครงสร้างมีความมั่นคงแข็งแรง (PASSED) | Safety Ratio = {max_r:.2f}")
        else:
            st.error(f"**บทสรุปทางวิศวกรรม:** โครงสร้างไม่ผ่านเกณฑ์ (FAILED) | กรุณาแก้ไขแบบ")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        s1, s2 = st.columns(2)
        with s1:
            st.markdown("..........................................................")
            st.markdown(f"({engineer})")
            st.markdown("วิศวกรผู้ออกแบบ (Structural Engineer)")
        with s2:
            st.markdown("..........................................................")
            st.markdown(f"({owner})")
            st.markdown("ผู้ตรวจสอบ / ผู้อนุมัติ (Approved By)")
            
        st.caption(f"Generated by Structural Insight Engine | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
