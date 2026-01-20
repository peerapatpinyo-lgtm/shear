# report_generator.py
# Version: 7.0 (Visual Dashboard & Deep Detail)
import streamlit as st
from datetime import datetime

def render_report_tab(beam_data, conn_data):
    # --- 1. ส่วนหัวและ Input ---
    st.markdown("## 📑 รายงานตรวจสอบความมั่นคงแข็งแรง (Structural Report)")
    st.caption("Detailed Calculation Report according to AISC 360-22 (LRFD Method)")

    with st.expander("📝 ตั้งค่าข้อมูลโครงการ (Project Info)", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            project_name = st.text_input("ชื่อโครงการ", value="โครงการก่อสร้างชั้นลอยโกดังสินค้า")
            owner_name = st.text_input("เจ้าของโครงการ", value="บริษัท สยามอุตสาหกรรม จำกัด")
        with c2:
            engineer_name = st.text_input("วิศวกรผู้ออกแบบ", value="นายสมชาย ใจดี (สย. 12345)")
            doc_no = st.text_input("เลขที่เอกสาร", value=f"CALC-{datetime.now().strftime('%Y%m%d')}-01")

    if not beam_data:
        st.warning("⚠️ กรุณากดคำนวณที่ Tab 1 ก่อนครับ")
        return

    # --- 2. ดึงข้อมูล (Extraction) ---
    sec_name = beam_data.get('sec_name', '-')
    span = beam_data.get('user_span', 0)
    fy = beam_data.get('Fy', 0)
    
    # Load & Capacity
    m_act = beam_data.get('m_act', 0)
    m_cap = beam_data.get('mn', 0)
    ratio_m = beam_data.get('ratio_m', 0)

    v_act = beam_data.get('v_act', 0)
    v_cap = beam_data.get('vn', 0)
    ratio_v = beam_data.get('ratio_v', 0)

    d_act = beam_data.get('defl_act', 0)
    d_all = beam_data.get('defl_all', 0)
    ratio_d = beam_data.get('ratio_d', 0)

    # Section Properties (สมมติค่าหรือดึงจาก Database)
    area = beam_data.get('area', 0)
    ix = beam_data.get('Ix', 0)
    zx = beam_data.get('Zx', 0)
    bf = beam_data.get('bf', 0) # ความกว้างปีก
    d = beam_data.get('d', 0)   # ความลึกคาน
    
    # ประมวลผลสถานะ
    max_ratio = max(ratio_m, ratio_v, ratio_d)
    is_pass = max_ratio <= 1.0
    curr_date = datetime.now().strftime("%d/%m/") + str(datetime.now().year + 543)

    st.divider()

    # --- 3. ส่วนหัวรายงาน (Header) ---
    st.header(f"🏗️ {project_name}")
    st.markdown(f"**เจ้าของงาน:** {owner_name} | **วิศวกร:** {engineer_name} | **วันที่:** {curr_date}")

    # Banner สถานะรวม
    if is_pass:
        st.success(f"### ✅ ผลสรุป: โครงสร้างปลอดภัย (APPROVED)\nใช้งานไป **{max_ratio*100:.1f}%** ของขีดจำกัดสูงสุด (Safety Margin = {100-(max_ratio*100):.1f}%)")
    else:
        st.error(f"### ❌ ผลสรุป: อันตราย/ไม่ผ่านเกณฑ์ (REJECTED)\nโครงสร้างรับน้ำหนักเกินพิกัด **{(max_ratio-1)*100:.1f}%** กรุณาแก้ไขแบบทันที")

    # --- 4. Tab System ---
    tab_dashboard, tab_detail, tab_conn = st.tabs([
        "📊 แดชบอร์ดความปลอดภัย (Visual)", 
        "🧮 รายการคำนวณวิศวกรรม (Detailed)", 
        "🔩 รายละเอียดวัสดุและจุดต่อ (Specs)"
    ])

    # === TAB 1: Visual Dashboard (เข้าใจง่าย) ===
    with tab_dashboard:
        st.markdown("#### ประสิทธิภาพการรับน้ำหนัก (Utilization Ratio)")
        st.caption("แถบสีแสดงเปอร์เซ็นต์การใช้งานโครงสร้าง (ยิ่งน้อยยิ่งปลอดภัย)")

        # Helper function สร้าง Progress Bar
        def create_progress(label, act, cap, unit, ratio, desc):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{label}** ({desc})")
                bar_val = min(ratio, 1.0)
                bar_color = "green" if ratio <= 0.8 else ("orange" if ratio <= 1.0 else "red")
                st.progress(bar_val, text=f"ใช้งาน {ratio*100:.1f}%")
            with col2:
                st.metric(label="Demand / Capacity", value=f"{ratio:.2f}", delta_color="inverse" if ratio > 1 else "normal")
                st.caption(f"{act:,.0f} / {cap:,.0f} {unit}")

        # 1. Moment
        create_progress("1. แรงดัด (Moment)", m_act, m_cap, "kg-m", ratio_m, 
                        "แรงที่พยายามหักกลางคาน")
        
        # 2. Shear
        create_progress("2. แรงเฉือน (Shear)", v_act, v_cap, "kg", ratio_v, 
                        "แรงที่พยายามตัดคานขาดที่ขั้ว")
        
        # 3. Deflection
        st.markdown("---")
        col_d1, col_d2 = st.columns([3, 1])
        with col_d1:
            st.markdown(f"**3. การแอ่นตัว (Deflection)** (อาการตกท้องช้าง)")
            bar_val_d = min(ratio_d, 1.0)
            st.progress(bar_val_d, text=f"แอ่นจริง {d_act:.2f} cm / ยอมให้ {d_all:.2f} cm")
        with col_d2:
            st.metric("Ratio", f"{ratio_d:.2f}")

    # === TAB 2: Engineering Calculation (ละเอียด) ===
    with tab_detail:
        st.info("ℹ️ ส่วนนี้แสดงสูตรและที่มาของการคำนวณตามมาตรฐาน AISC 360-22")
        
        with st.expander("1. สมมติฐานการออกแบบ (Design Criteria)", expanded=True):
            st.markdown(f"""
            * **มาตรฐาน:** AISC 360-22 (Specification for Structural Steel Buildings)
            * **วิธีคำนวณ:** LRFD (Load and Resistance Factor Design) หรือ ASD ตามการตั้งค่า
            * **ประเภทหน้าตัด:** {sec_name} (Compact Section)
            * **ความยาวช่วงคาน (L):** {span:.2f} เมตร
            * **การค้ำยันด้านข้าง (Lb):** {beam_data.get('Lb', 0):.2f} เมตร (Unbraced Length)
            """)

        st.markdown("#### 2. การตรวจสอบการรับแรงดัด (Flexural Check)")
        st.latex(r"\text{Condition: } M_u \leq \phi M_n")
        
        c_m1, c_m2 = st.columns(2)
        with c_m1:
            st.markdown("**Load Effect (Demand):**")
            st.write(f"$M_u$ = {m_act:,.2f} kg-m")
            st.caption("คำนวณจากน้ำหนักบรรทุกคงที่ + น้ำหนักบรรทุกจร")
        with c_m2:
            st.markdown("**Design Strength (Capacity):**")
            st.write(f"$\\phi M_n$ = {m_cap:,.2f} kg-m")
            st.caption(f"คำนวณจาก $0.9 F_y Z_x$ หรือ $C_b$ factor")
        
        st.markdown("#### 3. การตรวจสอบแรงเฉือน (Shear Check)")
        st.latex(r"\text{Condition: } V_u \leq \phi V_n")
        st.write(f"$V_u$ (แรงที่เกิด) = {v_act:,.0f} kg  |  $\\phi V_n$ (รับได้) = {v_cap:,.0f} kg")

        st.markdown("#### 4. การตรวจสอบระยะแอ่น (Serviceability)")
        st.markdown(f"เกณฑ์มาตรฐาน $L/{span*100/d_all:.0f}$ (สำหรับคานทั่วไป)")
        st.write(f"ระยะแอ่นที่เกิดขึ้นจริง $\\Delta_{{actual}}$ = **{d_act:.2f} cm**")
        st.write(f"ระยะแอ่นที่ยอมให้ $\\Delta_{{allow}}$ = **{d_all:.2f} cm**")

    # === TAB 3: Specification & Connection (สเปก) ===
    with tab_conn:
        c_spec1, c_spec2 = st.columns(2)
        with c_spec1:
            st.markdown("### 🧱 ข้อมูลวัสดุ (Material)")
            st.markdown(f"""
            * **เหล็กเกรด:** {beam_data.get('grade', 'SS400/A36')}
            * **จุดคลาก ($F_y$):** {fy:,} ksc (kg/cm²)
            * **แรงดึงประลัย ($F_u$):** {beam_data.get('Fu', 4100):,} ksc
            * **โมดูลัสยืดหยุ่น ($E$):** 2,040,000 ksc
            """)
        
        with c_spec2:
            st.markdown("### 📐 มิติหน้าตัด (Dimension)")
            st.markdown(f"""
            * **ความลึก (d):** {d} mm
            * **ปีกกว้าง (bf):** {bf} mm
            * **เนื้อที่ (Area):** {area} cm²
            * **Modulus ($Z_x$):** {zx} cm³
            """)

        st.divider()
        
        conn_type = conn_data.get('type', 'ยังไม่ระบุ')
        st.markdown(f"### 🔩 รายละเอียดจุดต่อ (Connection Detail)")
        st.info(f"รูปแบบที่เลือก: **{conn_type}**")
        
        st.table({
            "รายการ": ["เกรดน็อตสกรู (Bolt)", "เกรดลวดเชื่อม (Electrode)", "ขนาดรอยเชื่อม (Weld Size)"],
            "รายละเอียด": ["ASTM A325 / F10T (High Strength)", "E70xx (Low Hydrogen)", "6mm (Fillet Weld) รอบรอยต่อ"]
        })
        st.caption("*หมายเหตุ: รายละเอียดจุดต่อเป็นข้อแนะนำเบื้องต้น ผู้ควบคุมงานต้องตรวจสอบหน้างานจริง")

    # --- Footer ---
    st.markdown("---")
    st.markdown("#### 📝 บันทึกข้อเสนอแนะ (Remarks)")
    st.text_area("หมายเหตุเพิ่มเติมจากวิศวกร:", height=100, placeholder="เช่น เหล็กต้องทาสีกันสนิม 2 รอบ หรือ ต้องค้ำยันระหว่างเทคอนกรีต...")

    col_sign1, col_sign2 = st.columns(2)
    with col_sign1:
        st.markdown("<br>__________________________", unsafe_allow_html=True)
        st.markdown(f"**{engineer_name}**")
        st.caption("วิศวกรโครงสร้าง (Structural Engineer)")
    with col_sign2:
        st.markdown("<br>__________________________", unsafe_allow_html=True)
        st.markdown(f"**{owner_name}**")
        st.caption("ผู้อนุมัติ (Authorized Signature)")

    st.markdown("""
    <style>
    .stProgress > div > div > div > div {
        background-color: #1e3a8a;
    }
    </style>
    """, unsafe_allow_html=True)
