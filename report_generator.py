# report_generator.py
# Version: 14.3 (Final Fix: Pre-initialized Variables)
import streamlit as st
from datetime import datetime
import math

def render_report_tab(beam_data, conn_data):
    # =========================================================
    # 0. ประกาศตัวแปรทั้งหมดไว้ก่อน (กัน Error 100%)
    # =========================================================
    sec_name = "-"
    d = 0.0
    tw = 0.0
    Aw = 0.0   # <--- สร้างรอไว้เลย
    fy = 0.0
    fu = 0.0
    Vn_raw = 0.0
    V_capacity = 0.0
    V_design = 0.0
    bolt_dia_mm = 20
    plate_t_mm = 10
    num_bolts_final = 0
    ratio = 0.0
    method_txt = "LRFD"
    is_lrfd = True
    
    # ตัวแปรผลลัพธ์การคำนวณ Bolt
    Rn_bolt = 0.0
    Rn_bearing = 0.0
    req_bolts_final = 0.0
    
    # --- 1. ส่วนตั้งค่าเอกสาร ---
    st.markdown("### 🖨️ รายการคำนวณออกแบบจุดต่อ (Auto-Connection Design)")
    
    with st.expander("⚙️ ตั้งค่าหัวกระดาษ", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            project = st.text_input("ชื่อโครงการ", value="โครงการก่อสร้างอาคารเหล็ก")
            owner = st.text_input("เจ้าของงาน", value="บจก. สยามเอ็นจิเนียริ่ง")
        with c2:
            engineer = st.text_input("วิศวกรผู้ออกแบบ", value="นายคำนวณ แม่นยำ (สย.)")
            doc_ref = st.text_input("เลขที่เอกสาร", value=f"CALC-{datetime.now().strftime('%y%m%d')}")

    # --- 2. ดึงข้อมูลและคำนวณ (Data Extraction & Logic) ---
    if beam_data:
        try:
            # ดึงข้อมูลดิบ
            sec_name = beam_data.get('sec_name', 'Unknown')
            h_val = float(beam_data.get('h', 400)) # mm
            tw_val = float(beam_data.get('tw', 8)) # mm
            fy = float(beam_data.get('Fy', 2500))
            fu = float(beam_data.get('Fu', 4100))
            is_lrfd = beam_data.get('is_lrfd', True)

            # แปลงหน่วยและคำนวณตัวแปรเรขาคณิต
            d = h_val / 10.0   # cm
            tw = tw_val / 10.0 # cm
            Aw = d * tw        # cm2 (คำนวณค่าจริงตรงนี้)
            
            # คำนวณ Vn (Shear Capacity)
            Vn_raw = 0.60 * fy * Aw
            
            if is_lrfd:
                phi_v = 1.00
                V_capacity = phi_v * Vn_raw
                method_txt = "LRFD (phi=1.00)"
            else:
                omg_v = 1.50
                V_capacity = Vn_raw / omg_v
                method_txt = "ASD (Omega=1.50)"
            
            # คำนวณ V_req (75% Rule)
            V_design = 0.75 * V_capacity
            
            # คำนวณ Bolt (M20 A325)
            bolt_area_cm2 = (math.pi * (bolt_dia_mm/10)**2) / 4
            Fnv = 3300 # ksc
            
            # Bolt Shear Strength
            if is_lrfd:
                phi_bolt = 0.75
                Rn_bolt = phi_bolt * Fnv * bolt_area_cm2
            else:
                omg_bolt = 2.00
                Rn_bolt = (Fnv * bolt_area_cm2) / omg_bolt
            
            # Plate Bearing Strength
            plate_t_cm = plate_t_mm / 10.0
            if is_lrfd:
                phi_br = 0.75
                Rn_bearing = phi_br * (2.4 * (bolt_dia_mm/10) * plate_t_cm * fu)
            else:
                omg_br = 2.00
                Rn_bearing = (2.4 * (bolt_dia_mm/10) * plate_t_cm * fu) / omg_br
            
            # Final Bolt Count
            capacity_per_bolt = min(Rn_bolt, Rn_bearing)
            if capacity_per_bolt > 0:
                req_bolts_final = V_design / capacity_per_bolt
                num_bolts_final = max(2, math.ceil(req_bolts_final))
                total_capacity = num_bolts_final * capacity_per_bolt
                ratio = V_design / total_capacity
            
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการคำนวณ: {e}")

    else:
        st.warning("⚠️ กรุณากดคำนวณที่ Tab 1 ก่อน (No Beam Data)")
        return

    # =========================================================
    # 3. ส่วนแสดงผลรายงาน (REPORT RENDERING)
    # =========================================================
    st.markdown("---")
    
    with st.container(border=True):
        
        # --- HEADER ---
        st.markdown(f"""
        <div style="border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px;">
            <table style="width:100%;">
                <tr>
                    <td style="width:70%;">
                        <h2 style="margin:0; color:#000;">รายการคำนวณจุดต่อ (Connection Design)</h2>
                        <span style="font-size:12px; color:#555;">Ref: AISC 360-16 | Method: 75% of Beam Capacity</span>
                    </td>
                    <td style="width:30%; text-align:right;">
                        <b>Doc Ref:</b> {doc_ref}<br>
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
        st.write(f"**Section:** {sec_name} (Fy = {fy:,.0f} ksc)")
        
        st.markdown("**1.1 พื้นที่รับแรงเฉือน (Shear Area, Aw):**")
        # ตรงนี้ Aw จะไม่ error แล้ว เพราะประกาศไว้เป็น 0.0 ตั้งแต่ต้นไฟล์ ถ้าคำนวณผิดก็จะได้ 0.0
        st.latex(rf"A_w = d \times t_w = {d:.2f} \times {tw:.2f} = {Aw:.2f} \text{ cm}^2")
        
        st.markdown("**1.2 กำลังรับแรงเฉือนระบุ (Nominal Shear Strength, Vn):**")
        st.latex(rf"V_n = 0.6 \times F_y \times A_w = 0.6 \times {fy:.0f} \times {Aw:.2f} = {Vn_raw:,.0f} \text{ kg}")
        
        st.markdown(f"**1.3 กำลังรับแรงเฉือนที่ยอมให้ (Design Capacity, {'$\phi V_n$' if is_lrfd else '$V_n/\Omega$'}):**")
        if is_lrfd:
            st.latex(rf"\phi V_n = 1.00 \times {Vn_raw:,.0f} = \mathbf{{{V_capacity:,.0f} \text{{ kg}}}}")
        else:
            st.latex(rf"V_n / \Omega = {Vn_raw:,.0f} / 1.50 = \mathbf{{{V_capacity:,.0f} \text{{ kg}}}}")
            
        st.divider()

        # --- STEP 2: DESIGN FORCE ---
        st.markdown("#### 2. แรงกระทำสำหรับออกแบบจุดต่อ (Design Force)")
        st.info("💡 Condition: 75% of Beam Shear Capacity")
        st.latex(rf"V_{{req}} = 0.75 \times {V_capacity:,.0f} = \mathbf{{{V_design:,.0f} \text{{ kg}}}}")
        
        st.divider()

        # --- STEP 3: BOLT DESIGN ---
        st.markdown("#### 3. ออกแบบปริมาณน๊อต (Bolt Calculation)")
        st.markdown(f"**Spec:** Bolt **M{bolt_dia_mm} (A325)** | **Plate:** {plate_t_mm} mm")
        
        st.markdown("**3.1 กำลังรับแรงเฉือน (Shear Capacity per Bolt):**")
        st.latex(rf"R_{{bolt}} = \mathbf{{{Rn_bolt:,.0f} \text{{ kg/bolt}}}}")
            
        st.markdown("**3.2 กำลังรับแรงแบกทาน (Bearing Capacity per Bolt):**")
        st.latex(rf"R_{{bearing}} = \mathbf{{{Rn_bearing:,.0f} \text{{ kg/bolt}}}}")
        
        st.markdown("**3.3 จำนวนน๊อตที่ต้องการ (Required Bolts):**")
        st.latex(rf"N = \frac{{{V_design:,.0f}}}{{\min({Rn_bolt:,.0f}, {Rn_bearing:,.0f})}} = {req_bolts_final:.2f} \rightarrow \text{{Use }} \mathbf{{{num_bolts_final} \text{{ PCS.}}}}")
        
        st.divider()

        # --- STEP 4: SUMMARY & SKETCH ---
        st.markdown("#### 4. รายละเอียดการก่อสร้าง (Construction Sketch)")
        
        col_res1, col_res2 = st.columns([1.5, 2])
        with col_res1:
            st.success(f"##### ✅ SUMMARY: {num_bolts_final} Bolts")
            st.markdown(f"""
            - **Bolt:** M20 A325
            - **Plate:** 10 mm
            - **Weld:** 6 mm Fillet
            """)
        
        with col_res2:
            # Draw ASCII
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
{ascii_plate}    |  t = {plate_t_mm} mm     |
    +-----------------+
            """, language="text")

        st.markdown("---")
        st.markdown("<br>..................................................<br>Signature", unsafe_allow_html=True)
