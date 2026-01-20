# report_generator.py
# Version: 6.0 (Detailed Engineering Edition)
import streamlit as st
from datetime import datetime

def render_report_tab(beam_data, conn_data):
    # --- 1. ส่วนหัวและ Input ---
    st.markdown("## 📑 รายงานตรวจสอบความมั่นคงแข็งแรง (Structural Report)")
    st.caption("Detailed Calculation Report according to AISC 360-22")

    with st.expander("📝 ตั้งค่าข้อมูลโครงการ", expanded=True):
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

    # --- 2. ดึงข้อมูลตัวแปร (Data Extraction) ---
    sec_name = beam_data.get('sec_name', '-')
    span = beam_data.get('user_span', 0)
    fy = beam_data.get('Fy', 0)
    
    # แรง (Demand) & กำลัง (Capacity)
    m_act = beam_data.get('m_act', 0)
    m_cap = beam_data.get('mn', 0)
    ratio_m = beam_data.get('ratio_m', 0)

    v_act = beam_data.get('v_act', 0)
    v_cap = beam_data.get('vn', 0)
    ratio_v = beam_data.get('ratio_v', 0)

    d_act = beam_data.get('defl_act', 0)
    d_all = beam_data.get('defl_all', 0)
    ratio_d = beam_data.get('ratio_d', 0)

    # คุณสมบัติหน้าตัด (สมมติว่ามีการส่งมา หรือใช้ค่า default เพื่อโชว์ตัวอย่าง)
    # ในการใช้งานจริง ควรดึงจาก beam_data ที่คำนวณมา
    area = beam_data.get('area', 0)
    ix = beam_data.get('Ix', 0)
    zx = beam_data.get('Zx', 0)
    
    # สถานะ
    max_ratio = max(ratio_m, ratio_v, ratio_d)
    is_pass = max_ratio <= 1.0
    curr_date = datetime.now().strftime("%d/%m/") + str(datetime.now().year + 543)

    st.divider()

    # --- 3. ส่วนหัวรายงาน (Header) ---
    st.title(f"🏗️ {project_name}")
    col_h1, col_h2, col_h3 = st.columns([2, 1, 1])
    col_h1.markdown(f"**เจ้าของงาน:** {owner_name}")
    col_h2.markdown(f"**วิศวกร:** {engineer_name}")
    col_h3.markdown(f"**วันที่:** {curr_date}")

    # Banner สรุปผล
    if is_pass:
        st.success(f"### ✅ ผลการตรวจสอบ: ผ่านเกณฑ์ (PASSED)\nโครงสร้างมีความแข็งแรงปลอดภัย อัตราส่วนการใช้งานสูงสุด **{max_ratio:.2f}** ({max_ratio*100:.0f}%)")
    else:
        st.error(f"### ❌ ผลการตรวจสอบ: ไม่ผ่านเกณฑ์ (FAILED)\nโครงสร้างรับน้ำหนักเกินพิกัด กรุณาแก้ไขแบบ")

    # --- 4. แยก Tab การแสดงผล ---
    tab_summary, tab_detail, tab_conn = st.tabs(["📊 สรุปผล (Summary)", "🧮 รายการคำนวณละเอียด (Calculation)", "🔩 ข้อมูลจุดต่อ (Connection)"])

    # === TAB 1: สรุปผล (Executive Summary) ===
    with tab_summary:
        st.markdown("### 1. ข้อมูลการออกแบบ (Design Data)")
        c_sum1, c_sum2, c_sum3 = st.columns(3)
        c_sum1.metric("หน้าตัดเหล็ก (Section)", str(sec_name))
        c_sum2.metric("เกรดเหล็ก (Fy)", f"{fy:,} ksc")
        c_sum3.metric("ความยาวคาน (Span)", f"{span} m.")

        st.markdown("### 2. ตารางสรุปอัตราส่วนความปลอดภัย (Safety Ratio)")
        results = [
            {"รายการ": "1. โมเมนต์ดัด (Moment)", "Demand": f"{m_act:,.0f} kg-m", "Capacity": f"{m_cap:,.0f} kg-m", "Ratio": ratio_m, "Result": "ผ่าน" if ratio_m<=1 else "ไม่ผ่าน"},
            {"รายการ": "2. แรงเฉือน (Shear)", "Demand": f"{v_act:,.0f} kg", "Capacity": f"{v_cap:,.0f} kg", "Ratio": ratio_v, "Result": "ผ่าน" if ratio_v<=1 else "ไม่ผ่าน"},
            {"รายการ": "3. การแอ่นตัว (Deflection)", "Demand": f"{d_act:.2f} cm", "Capacity": f"{d_all:.2f} cm", "Ratio": ratio_d, "Result": "ผ่าน" if ratio_d<=1 else "ไม่ผ่าน"},
        ]
        
        # จัด Format สีในตารางเองไม่ได้ใน st.table แบบ Native แต่แสดงข้อมูลได้ชัดเจน
        st.table(results)

    # === TAB 2: รายการคำนวณละเอียด (Detailed Calculation) ===
    with tab_detail:
        st.info("💡 ส่วนนี้แสดงรายละเอียดที่มาของตัวเลข เพื่อใช้ประกอบการตรวจสอบทางวิศวกรรม")

        # 2.1 คุณสมบัติหน้าตัด
        st.markdown("#### 2.1 คุณสมบัติหน้าตัด (Section Properties)")
        col_prop1, col_prop2, col_prop3 = st.columns(3)
        with col_prop1:
            st.markdown(f"**Area (เนื้อที่หน้าตัด):**")
            st.code(f"A = {area:.2f} cm²")
        with col_prop2:
            st.markdown(f"**Moment of Inertia (โมเมนต์ความเฉื่อย):**")
            st.code(f"Ix = {ix:,.0f} cm⁴")
        with col_prop3:
            st.markdown(f"**Plastic Modulus (โมดูลัสพลาสติก):**")
            st.code(f"Zx = {zx:,.0f} cm³")

        st.divider()

        # 2.2 การตรวจสอบโมเมนต์
        st.markdown("#### 2.2 การตรวจสอบกำลังรับแรงดัด (Flexural Strength Check)")
        st.markdown("พิจารณาตามมาตรฐาน AISC 360-22 บท F (Design for Flexure)")
        
        c_cal1, c_cal2 = st.columns([1, 1.5])
        with c_cal1:
            st.latex(r"M_u \leq \phi M_n")
            st.caption("เงื่อนไขความปลอดภัย")
        with c_cal2:
            # แสดงสูตรอย่างง่าย (Yielding Limit State)
            st.latex(r"\phi M_n = 0.90 \times F_y \times Z_x")
            st.write(f"**แทนค่า:** $0.90 \\times {fy} \\times {zx} / 100$ (แปลงหน่วย)")
            st.write(f"**= {m_cap:,.0f} kg-m** (Capacity)")
        
        check_m = "✅ OK" if ratio_m <= 1 else "❌ FAILED"
        st.write(f"**ตรวจสอบ:** $M_u ({m_act:,.0f}) / \\phi M_n ({m_cap:,.0f}) = \\mathbf{{{ratio_m:.2f}}}$ ... {check_m}")

        st.divider()

        # 2.3 การตรวจสอบแรงเฉือน
        st.markdown("#### 2.3 การตรวจสอบกำลังรับแรงเฉือน (Shear Strength Check)")
        st.markdown("พิจารณาตามมาตรฐาน AISC 360-22 บท G (Design for Shear)")
        
        c_cal3, c_cal4 = st.columns([1, 1.5])
        with c_cal3:
             st.latex(r"V_u \leq \phi V_n")
        with c_cal4:
             st.latex(r"\phi V_n = 1.00 \times 0.60 \times F_y \times A_w")
             st.write(f"**= {v_cap:,.0f} kg** (Capacity)")

        check_v = "✅ OK" if ratio_v <= 1 else "❌ FAILED"
        st.write(f"**ตรวจสอบ:** $V_u ({v_act:,.0f}) / \\phi V_n ({v_cap:,.0f}) = \\mathbf{{{ratio_v:.2f}}}$ ... {check_v}")

        st.divider()
        
        # 2.4 การแอ่นตัว
        st.markdown("#### 2.4 การตรวจสอบระยะแอ่นตัว (Deflection Check)")
        st.write(f"**เกณฑ์ที่ยอมให้ (Allowable):** $L/{span*100/d_all:.0f}$ = {d_all:.2f} cm")
        st.write(f"**เกิดขึ้นจริง (Actual):** {d_act:.2f} cm")
        check_d = "✅ OK" if ratio_d <= 1 else "❌ FAILED"
        st.write(f"**ผลลัพธ์:** {check_d}")

    # === TAB 3: ข้อมูลจุดต่อ (Connection) ===
    with tab_conn:
        conn_type = conn_data.get('type', 'ยังไม่ได้ระบุ')
        conn_summ = conn_data.get('summary', 'ไม่มีข้อมูล')
        
        st.markdown(f"### รูปแบบจุดต่อ: {conn_type}")
        st.info(f"📋 **รายละเอียด:** {conn_summ}")
        
        if conn_type == "Shear Tab (Simple)":
            st.markdown("""
            **ข้อแนะนำการทำงาน:**
            * ใช้ลวดเชื่อมเกรด E70xx
            * น็อตสกรูใช้เกรด A325 (High Strength Bolt) ระบุขนาดตามแบบ
            * รอยเชื่อมต้องมีความสม่ำเสมอ ไม่มีรูพรุน
            """)
        elif conn_type == "End Plate (Moment)":
            st.markdown("""
            **ข้อแนะนำการทำงาน:**
            * ต้องขันน็อตให้แน่นตาม Torque ที่กำหนด (Pretensioned)
            * แผ่นเหล็ก End Plate ต้องแนบสนิทกับเสา
            * ตรวจสอบรอยเชื่อมแบบ Penetration (ซึมลึก) อย่างเคร่งครัด
            """)

    st.markdown("---")
    
    # --- 5. ส่วนลงนาม (Signature) ---
    st.markdown("#### ✒️ การรับรองเอกสาร (Certification)")
    col_sign1, col_sign2 = st.columns(2)
    
    with col_sign1:
        st.markdown("<br><br>......................................................", unsafe_allow_html=True)
        st.markdown(f"**({engineer_name})**")
        st.caption("วิศวกรผู้ออกแบบ (Structural Engineer)")
        st.caption(f"วันที่: {curr_date}")
        
    with col_sign2:
        st.markdown("<br><br>......................................................", unsafe_allow_html=True)
        st.markdown(f"**({owner_name})**")
        st.caption("ผู้อำนวยการโครงการ / ผู้ตรวจสอบ (Approved By)")
        st.caption(f"วันที่: {curr_date}")

    st.caption(f"Generated by Beam Insight Engine | Ref: AISC 360-22 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
