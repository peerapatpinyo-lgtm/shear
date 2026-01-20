# report_generator.py
# Version: 14.0 (Auto-Design: 75% Capacity Rule with Full Calc)
import streamlit as st
from datetime import datetime
import math

def render_report_tab(beam_data, conn_data):
    # --- 1. ส่วนตั้งค่าเอกสาร ---
    st.markdown("### 🖨️ รายการคำนวณออกแบบจุดต่อ (Auto-Connection Design)")
    st.caption("ออกแบบจุดต่ออัตโนมัติด้วยเกณฑ์ 75% ของกำลังรับแรงเฉือนคาน (75% Beam Shear Capacity Rule)")
    
    with st.expander("⚙️ ตั้งค่าหัวกระดาษ", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            project = st.text_input("ชื่อโครงการ", value="โครงการก่อสร้างอาคารเหล็ก")
            owner = st.text_input("เจ้าของงาน", value="บจก. สยามเอ็นจิเนียริ่ง")
        with c2:
            engineer = st.text_input("วิศวกรผู้ออกแบบ", value="นายคำนวณ แม่นยำ (สย.)")
            doc_ref = st.text_input("เลขที่เอกสาร", value=f"CALC-{datetime.now().strftime('%y%m%d')}")

    if not beam_data:
        st.error("⚠️ ไม่พบข้อมูลคาน (กรุณาเลือกขนาดเหล็กที่ Tab 1)")
        return

    # =========================================================
    # 🧠 ส่วนคำนวณวิศวกรรม (ENGINEERING CALCULATION CORE)
    # =========================================================
    
    # 1. ดึงข้อมูลหน้าตัดคาน
    sec_name = beam_data.get('sec_name', '-')
    d = beam_data.get('h', 400) / 10.0   # cm (Depth)
    tw = beam_data.get('tw', 8) / 10.0   # cm (Web Thickness)
    fy = beam_data.get('Fy', 2500)       # ksc
    fu = beam_data.get('Fu', 4100)       # ksc (สมมติถ้าไม่มี)
    is_lrfd = beam_data.get('is_lrfd', True)
    
    # 2. คำนวณ Shear Capacity ของคาน (Vn)
    # สูตร: Vn = 0.6 * Fy * Aw
    Aw = d * tw # พื้นที่รับแรงเฉือน (cm2)
    Vn_raw = 0.60 * fy * Aw
    
    if is_lrfd:
        phi_v = 1.00
        V_capacity = phi_v * Vn_raw
        method_txt = "LRFD (phi=1.00)"
    else:
        omg_v = 1.50
        V_capacity = Vn_raw / omg_v
        method_txt = "ASD (Omega=1.50)"
        
    # 3. คำนวณแรงออกแบบจุดต่อ (Design Force) ตามกฎ 75%
    # V_conn = 75% of V_capacity
    V_design = 0.75 * V_capacity
    
    # 4. ออกแบบน๊อต (Bolt Design)
    # สมมติใช้ Bolt M20 Grade A325 (มาตรฐานนิยม)
    bolt_dia_mm = 20
    bolt_area_cm2 = (math.pi * (bolt_dia_mm/10)**2) / 4
    
    # กําลังรับแรงเฉือนของ Bolt (Shear Strength per Bolt)
    # Fnv = 372 MPa approx 3,793 ksc (A325 Threads Included)
    # คิด conservative ที่ 3,300 ksc (Allowable/Factored) เพื่อความปลอดภัยใน Code ตัวอย่าง
    if is_lrfd:
        phi_bolt = 0.75
        Fnv = 3300 # ksc (Nominal Shear Stress)
        Rn_bolt = phi_bolt * Fnv * bolt_area_cm2
    else:
        omg_bolt = 2.00
        Fnv = 3300
        Rn_bolt = (Fnv * bolt_area_cm2) / omg_bolt
        
    # จำนวนน๊อตที่ต้องการ
    req_bolts = V_design / Rn_bolt
    num_bolts = max(2, math.ceil(req_bolts)) # ขั้นต่ำ 2 ตัว
    
    # 5. ตรวจสอบ Plate (Bearing Check & Shear Check) แบบย่อ
    # สมมติ Plate หนา 10mm
    plate_t_mm = 10
    plate_t_cm = 1.0
    
    # กำลังรับแรงแบกทาน (Bearing Capacity) ที่รูเจาะ
    # Rn = 2.4 * d * t * Fu
    if is_lrfd:
        phi_br = 0.75
        Rn_bearing = phi_br * (2.4 * (bolt_dia_mm/10) * plate_t_cm * fu)
    else:
        omg_br = 2.00
        Rn_bearing = (2.4 * (bolt_dia_mm/10) * plate_t_cm * fu) / omg_br
        
    # เช็คว่าอะไรวิกฤตกว่ากันระหว่าง Shear Bolt กับ Bearing Plate
    capacity_per_bolt = min(Rn_bolt, Rn_bearing)
    
    # คำนวณใหม่หาก Bearing control (กรณีเพลทบาง)
    req_bolts_final = V_design / capacity_per_bolt
    num_bolts_final = max(2, math.ceil(req_bolts_final))
    
    total_capacity = num_bolts_final * capacity_per_bolt
    ratio = V_design / total_capacity

    # =========================================================
    # 📄 ส่วนแสดงผลรายงาน (REPORT RENDERING)
    # =========================================================
    st.markdown("---")
    
    # สร้าง Container กระดาษ A4
    with st.container(border=True):
        
        # --- HEADER ---
        st.markdown(f"""
        <div style="border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px;">
            <table style="width:100%;">
                <tr>
                    <td style="width:70%;">
                        <h2 style="margin:0; color:#000;">รายการคำนวณจุดต่อ (Connection Design)</h2>
                        <span style="font-size:12px; color:#555;">Design Method: {method_txt} | 75% Capacity Rule</span>
                    </td>
                    <td style="width:30%; text-align:right;">
                        <b>Doc:</b> {doc_ref}<br>
                        <b>Date:</b> {datetime.now().strftime('%d/%m/%Y')}
                    </td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
        st.write(f"**PROJECT:** {project} | **ENGINEER:** {engineer}")
        st.divider()

        # --- STEP 1: BEAM SHEAR CAPACITY ---
        st.markdown("#### 1. คำนวณกำลังรับแรงเฉือนของคาน (Beam Shear Capacity)")
        st.write(f"**Section:** {sec_name} (Fy = {fy:,} ksc, Fu = {fu:,} ksc)")
        st.write(f"**Dimensions:** Depth (d) = {d} cm, Web Thickness (tw) = {tw} cm")
        
        st.markdown("**1.1 พื้นที่รับแรงเฉือน (Shear Area, Aw):**")
        st.latex(rf"A_w = d \times t_w = {d} \times {tw} = {Aw:.2f} \text{ cm}^2")
        
        st.markdown("**1.2 กำลังรับแรงเฉือนระบุ (Nominal Shear Strength, Vn):**")
        st.latex(rf"V_n = 0.6 \times F_y \times A_w = 0.6 \times {fy} \times {Aw:.2f} = {Vn_raw:,.0f} \text{ kg}")
        
        st.markdown(f"**1.3 กำลังรับแรงเฉือนที่ยอมให้ (Design Capacity, {'$\phi V_n$' if is_lrfd else '$V_n/\Omega$'}):**")
        if is_lrfd:
            st.latex(rf"\phi V_n = 1.00 \times {Vn_raw:,.0f} = \mathbf{{{V_capacity:,.0f} \text{{ kg}}}}")
        else:
            st.latex(rf"V_n / \Omega = {Vn_raw:,.0f} / 1.50 = \mathbf{{{V_capacity:,.0f} \text{{ kg}}}}")
            
        st.divider()

        # --- STEP 2: DESIGN FORCE ---
        st.markdown("#### 2. แรงกระทำสำหรับออกแบบจุดต่อ (Design Force for Connection)")
        st.info("💡 ใช้เกณฑ์ 75% ของกำลังรับแรงเฉือนคาน ตามข้อกำหนด")
        st.latex(rf"V_{{req}} = 0.75 \times V_{{capacity}}")
        st.latex(rf"V_{{req}} = 0.75 \times {V_capacity:,.0f} = \mathbf{{{V_design:,.0f} \text{{ kg}}}}")
        
        st.divider()

        # --- STEP 3: BOLT DESIGN ---
        st.markdown("#### 3. ออกแบบปริมาณน๊อต (Bolt Calculation)")
        st.markdown(f"**เลือกใช้:** High Strength Bolt **M{bolt_dia_mm} (A325)**")
        st.markdown(f"**พื้นที่หน้าตัดน๊อต ($A_b$):** {bolt_area_cm2:.2f} cm²")
        
        st.markdown("**3.1 กำลังรับแรงเฉือนต่อน๊อต 1 ตัว (Shear Capacity per Bolt):**")
        if is_lrfd:
            st.latex(rf"\phi R_n = 0.75 \times 3300 \times {bolt_area_cm2:.2f} = \mathbf{{{Rn_bolt:,.0f} \text{{ kg/bolt}}}}")
        else:
            st.latex(rf"R_n/\Omega = (3300 \times {bolt_area_cm2:.2f}) / 2.0 = \mathbf{{{Rn_bolt:,.0f} \text{{ kg/bolt}}}}")
            
        st.markdown("**3.2 ตรวจสอบแรงแบกทานที่รูเจาะ (Bearing Check @ t=10mm):**")
        st.latex(rf"R_{{bearing}} = \mathbf{{{Rn_bearing:,.0f} \text{{ kg/bolt}}}}")
        
        st.markdown("**3.3 กำลังรับแรงวิกฤต (Governing Capacity per Bolt):**")
        st.write(f"เลือกค่าน้อยสุดระหว่าง Shear และ Bearing: **{capacity_per_bolt:,.0f} kg/bolt**")

        st.markdown("**3.4 จำนวนน๊อตที่ต้องการ (Required Bolts):**")
        st.latex(rf"N = \frac{{V_{{req}}}}{{R_{{bolt}}}} = \frac{{{V_design:,.0f}}}{{{capacity_per_bolt:,.0f}}} = {req_bolts_final:.2f} \rightarrow \text{{Use }} \mathbf{{{num_bolts_final} \text{{ PCS.}}}}")
        
        st.divider()

        # --- STEP 4: SUMMARY & SKETCH ---
        st.markdown("#### 4. สรุปรายละเอียดการก่อสร้าง (Construction Detail)")
        
        col_res1, col_res2 = st.columns([1.5, 2])
        with col_res1:
            st.success(f"##### ✅ สรุปจำนวน: {num_bolts_final} ตัว (M20 A325)")
            st.markdown(f"""
            - **Plate Thickness:** 10 mm (Min)
            - **Weld Size:** 6 mm (Fillet)
            - **Bolt Grade:** A325 / 8.8
            - **Demand/Cap Ratio:** {ratio:.2f}
            """)
        
        with col_res2:
            st.markdown("**Layout Sketch (การจัดเรียง):**")
            # Logic วาดรูป
            qty = num_bolts_final
            cols = 2 if qty >= 4 else 1
            rows = math.ceil(qty / cols)
            
            ascii_plate = ""
            for r in range(rows):
                line = "   |"
                for c in range(cols):
                    if (r * cols + c) < qty:
                         line += "  (X)  "
                    else:
                         line += "       "
                line += "|\n"
                ascii_plate += line
            
            st.code(f"""
    +-----------------+
    |  SHEAR PLATE    |
{ascii_plate}    |  t = 10 mm      |
    +-----------------+
   {rows} Rows x {cols} Cols
            """, language="text")

        # --- FOOTER ---
        st.markdown("---")
        st.markdown(f"**Note:** การคำนวณนี้เป็นการตรวจสอบเบื้องต้นสำหรับจุดต่อรับแรงเฉือน (Shear Connection) เท่านั้น")
        st.markdown("<br><br>..................................................<br>วิศวกรผู้ออกแบบ", unsafe_allow_html=True)
