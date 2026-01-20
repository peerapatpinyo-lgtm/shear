# report_generator.py
# Version: 15.1 (Restored - The Best Stable Version)
import streamlit as st
from datetime import datetime
import math

def render_report_tab(beam_data, conn_data):
    # =========================================================
    # 1. การจัดการข้อมูลและการคำนวณ (Calculation Section)
    # =========================================================
    
    # 🚨 CHECK POINT: ถ้าไม่มีข้อมูลคาน ให้หยุดทำงาน
    if not beam_data:
        st.warning("⚠️ ไม่พบข้อมูลคาน กรุณากลับไปกดคำนวณที่ Tab 1 ก่อน")
        return

    # 📥 ดึงข้อมูล (Safe Extraction)
    try:
        sec_name = beam_data.get('sec_name', 'Unknown')
        h_val = float(beam_data.get('h', 0) or 400)
        tw_val = float(beam_data.get('tw', 0) or 8)
        fy = float(beam_data.get('Fy', 0) or 2500)
        fu = float(beam_data.get('Fu', 0) or 4100)
        is_lrfd = beam_data.get('is_lrfd', True)
    except:
        h_val, tw_val, fy, fu = 400.0, 8.0, 2500.0, 4100.0
        sec_name = "Default Section"
        is_lrfd = True

    # 🧮 คำนวณตัวแปรพื้นฐาน
    d = h_val / 10.0      # cm
    tw = tw_val / 10.0    # cm
    Aw = d * tw           # cm2

    # 🧮 คำนวณกำลังคาน (Beam Capacity)
    Vn_raw = 0.60 * fy * Aw
    
    if is_lrfd:
        phi_v = 1.00
        V_capacity = phi_v * Vn_raw
        method_txt = "LRFD (phi=1.00)"
    else:
        omg_v = 1.50
        V_capacity = Vn_raw / omg_v
        method_txt = "ASD (Omega=1.50)"

    # 🧮 คำนวณแรงออกแบบ (75% Rule)
    V_design = 0.75 * V_capacity

    # 🧮 คำนวณน๊อต (Bolt Calculation)
    bolt_dia_mm = 20
    plate_t_mm = 10
    
    bolt_area_cm2 = (math.pi * (bolt_dia_mm/10)**2) / 4
    Fnv = 3300 # ksc
    
    # Shear Strength
    if is_lrfd:
        phi_bolt = 0.75
        Rn_bolt = phi_bolt * Fnv * bolt_area_cm2
    else:
        omg_bolt = 2.00
        Rn_bolt = (Fnv * bolt_area_cm2) / omg_bolt
        
    # Bearing Strength
    plate_t_cm = plate_t_mm / 10.0
    if is_lrfd:
        phi_br = 0.75
        Rn_bearing = phi_br * (2.4 * (bolt_dia_mm/10) * plate_t_cm * fu)
    else:
        omg_br = 2.00
        Rn_bearing = (2.4 * (bolt_dia_mm/10) * plate_t_cm * fu) / omg_br
        
    # Final Calculation
    capacity_per_bolt = min(Rn_bolt, Rn_bearing)
    
    if capacity_per_bolt > 0:
        req_bolts_final = V_design / capacity_per_bolt
    else:
        req_bolts_final = 99.0
        
    num_bolts_final = max(2, math.ceil(req_bolts_final))
    
    total_capacity = num_bolts_final * capacity_per_bolt
    ratio = V_design / total_capacity if total_capacity > 0 else 0

    # =========================================================
    # 2. การแสดงผล (Rendering Section)
    # =========================================================
    
    st.markdown("### 🖨️ รายการคำนวณออกแบบจุดต่อ (Auto-Connection Design)")
    
    with st.expander("⚙️ ตั้งค่าหัวกระดาษ", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            project = st.text_input("ชื่อโครงการ", value="โครงการก่อสร้างอาคารเหล็ก")
        with c2:
            engineer = st.text_input("วิศวกรผู้ออกแบบ", value="นายคำนวณ แม่นยำ (สย.)")
    
    doc_ref = f"CALC-{datetime.now().strftime('%y%m%d')}"
    
    st.markdown("---")
    with st.container(border=True):
        
        # --- HEADER ---
        st.markdown(f"""
        <div style="border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px;">
            <h3 style="margin:0; color:#000;">รายการคำนวณจุดต่อ (Connection Design)</h3>
            <span style="font-size:12px; color:#555;">Ref: AISC 360-16 | Method: 75% of Beam Capacity ({method_txt})</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.write(f"**PROJECT:** {project} | **ENGINEER:** {engineer} | **DATE:** {datetime.now().strftime('%d/%m/%Y')}")
        st.divider()

        # --- STEP 1: BEAM CAPACITY ---
        st.markdown("#### 1. คำนวณกำลังรับแรงเฉือนของคาน (Beam Shear Capacity)")
        st.write(f"**Section:** {sec_name} (Fy = {fy:,.0f} ksc)")
        
        # Syntax ที่ถูกต้องและปลอดภัยที่สุด
        st.markdown("**1.1 พื้นที่รับแรงเฉือน (Shear Area, Aw):**")
        st.latex(rf"A_w = d \times t_w = {d:.2f} \times {tw:.2f} = {Aw:.2f} \text{{ cm}}^2")
        
        st.markdown("**1.2 กำลังรับแรงเฉือนระบุ (Nominal Shear Strength, Vn):**")
        st.latex(rf"V_n = 0.6 \times F_y \times A_w = 0.6 \times {fy:.0f} \times {Aw:.2f} = {Vn_raw:,.0f} \text{{ kg}}")
        
        st.markdown(f"**1.3 กำลังรับแรงเฉือนที่ยอมให้ (Design Capacity):**")
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

        # --- STEP 3: BOLT ---
        st.markdown("#### 3. ออกแบบปริมาณน๊อต (Bolt Calculation)")
        st.markdown(f"**Spec:** Bolt **M{bolt_dia_mm} (A325)**")
        
        st.markdown("**3.1 กำลังรับแรงเฉือน (Shear Capacity per Bolt):**")
        st.latex(rf"R_{{bolt}} = \mathbf{{{Rn_bolt:,.0f} \text{{ kg/bolt}}}}")
            
        st.markdown("**3.2 กำลังรับแรงแบกทาน (Bearing Capacity per Bolt):**")
        st.latex(rf"R_{{bearing}} = \mathbf{{{Rn_bearing:,.0f} \text{{ kg/bolt}}}}")
        
        st.markdown("**3.3 จำนวนน๊อตที่ต้องการ (Required Bolts):**")
        st.latex(rf"N = \frac{{{V_design:,.0f}}}{{\min({Rn_bolt:,.0f}, {Rn_bearing:,.0f})}} = {req_bolts_final:.2f} \rightarrow \text{{Use }} \mathbf{{{num_bolts_final} \text{{ PCS.}}}}")
        
        st.divider()

        # --- STEP 4: SUMMARY ---
        st.markdown("#### 4. สรุปรายละเอียด (Summary)")
        c_res1, c_res2 = st.columns([1.5, 2])
        
        with c_res1:
            st.success(f"##### ✅ Use: {num_bolts_final} Bolts")
            st.write(f"- Bolt: M20 A325")
            st.write(f"- Plate t: {plate_t_mm} mm")
            st.write(f"- Ratio: {ratio:.2f}")

        with c_res2:
            qty = int(num_bolts_final)
            rows = math.ceil(qty / 2)
            sketch = ("(X)   (X)\n" * rows) if qty > 1 else "(X)\n"
            st.code(f"PLATE SKETCH:\n-----------\n{sketch}-----------", language="text")

    st.markdown("---")
