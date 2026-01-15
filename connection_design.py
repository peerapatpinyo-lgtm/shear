# connection_design.py (V21 - Precision Structural Engineering)
import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    """
    T_design: แรงดึง (Tension) ที่เพิ่มเข้ามา (ถ้าไม่มีให้เป็น 0)
    """
    p = section_data
    h_mm, tw_mm = p['h'], p['tw']
    tw_cm = tw_mm / 10
    Fy, Fu = 2450, 4000 # SS400 (kg/cm2)

    # 1. BOLT DATA
    b_areas = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}
    Ab = b_areas.get(bolt_size, 3.14)
    d_mm = int(bolt_size[1:])
    d_cm = d_mm / 10

    # Nominal Stress (AISC Table J3.2)
    bolt_map = {"A325 (High Strength)": 3795, "Grade 8.8 (Standard)": 3200, "A490 (Premium)": 4780}
    Fnv = bolt_map.get(bolt_grade, 3795) # Nominal Shear Stress
    Fnt = Fnv * 1.33 # Nominal Tensile Stress (Approx)

    # 2. SEPARATION OF ASD vs LRFD (AISC 360-16 Chapter J)
    if is_lrfd:
        phi = 0.75
        omega = 1.0
        method_label = "LRFD"
        calc_prefix = r"\phi R_n = 0.75 \times"
    else:
        phi = 1.0
        omega = 2.0
        method_label = "ASD"
        calc_prefix = r"R_n / \Omega = R_n / 2.00 ="

    # 3. CALCULATE BOLT CAPACITY
    # --- Shear Capacity ---
    rn_shear = Fnv * Ab
    cap_shear_1b = (phi * rn_shear) / omega
    
    # --- Tension Capacity ---
    rn_tension = Fnt * Ab
    cap_tension_1b = (phi * rn_tension) / omega

    # --- Preliminary Bolt Count ---
    n_bolts = max(2, math.ceil(V_design / cap_shear_1b))
    if n_bolts % 2 != 0: n_bolts += 1
    n_rows = n_bolts // 2

    # 4. COMBINED SHEAR & TENSION (AISC J3.7)
    frv = V_design / (n_bolts * Ab) # Required shear stress
    if T_design > 0:
        # F'nt = 1.3Fnt - (Fnt/(phi*Fnv))*frv <= Fnt
        # นี่คือจุดที่วิศวกรต้องเช็ค Interaction Curve
        Fnt_prime = min(1.3 * Fnt - (Fnt / (0.75 * Fnv)) * frv, Fnt) if is_lrfd else min(1.3 * Fnt - (2.0 * Fnt / Fnv) * frv, Fnt)
        rn_combined = Fnt_prime * Ab
        cap_combined = (phi * rn_combined) / omega
    else:
        cap_combined = cap_tension_1b

    # 5. UI DISPLAY
    st.subheader(f"📊 ผลการวิเคราะห์แบบ {method_label} (AISC 360-16)")
    
    col1, col2, col3 = st.columns(3)
    
    # Shear Ratio
    v_ratio = V_design / (cap_shear_1b * n_bolts)
    col1.metric("Shear Ratio", f"{v_ratio:.3f}", delta="SAFE" if v_ratio <= 1 else "OVERLOAD", delta_color="normal" if v_ratio <= 1 else "inverse")
    
    # Tension Ratio (ถ้ามี)
    t_ratio = T_design / (cap_combined * n_bolts) if T_design > 0 else 0
    col2.metric("Tension Ratio", f"{t_ratio:.3f}", delta="SAFE" if t_ratio <= 1 else "OVERLOAD", delta_color="normal" if t_ratio <= 1 else "inverse")

    # Final Status
    is_safe = v_ratio <= 1 and t_ratio <= 1
    if is_safe:
        st.success("✅ จุดต่อนี้ปลอดภัยตามมาตรฐาน")
    else:
        st.error("❌ Ratio เกิน! โปรดดูคำแนะนำด้านล่าง")

    # 6. DETAILED CALCULATION (แยกสูตร ASD/LRFD ชัดเจน)
    with st.expander(f"📝 รายการคำนวณละเอียดระบบ {method_label}"):
        st.markdown(f"#### 1. แรงเฉือน (Shear) - บท J3.6")
        st.latex(fr"R_n = F_{{nv}} A_b = {Fnv} \times {Ab} = {rn_shear:,.0f} \text{{ kg/bolt}}")
        st.latex(fr"{calc_prefix} {rn_shear:,.0f} = {cap_shear_1b:,.0f} \text{{ kg/bolt}}")
        
        if T_design > 0:
            st.markdown(f"#### 2. แรงดึงร่วม (Combined Tension) - บท J3.7")
            st.latex(fr"f_{{rv}} = V_u / (N A_b) = {frv:.1f} \text{{ kg/cm}}^2")
            st.latex(fr"F'_{{nt}} = \text{{Interaction Formula per AISC J3.7}} = {Fnt_prime:.1f} \text{{ kg/cm}}^2")
            st.latex(fr"{calc_prefix} (F'_{{nt}} A_b) = {cap_combined:,.0f} \text{{ kg/bolt}}")

    # 7. ข้อแนะนำสำหรับวิศวกร (เมื่อ Ratio เกิน)
    if not is_safe:
        st.warning("### 💡 ข้อแนะนำในการแก้ไข (Engineering Recommendations)")
        st.markdown("""
        1. **เพิ่มจำนวนน็อต (Increase N):** เป็นวิธีที่ง่ายที่สุดในการกระจายแรงเฉือน
        2. **เปลี่ยนเกรดน็อต (Upgrade Bolt Grade):** ขยับจาก Grade 8.8 เป็น A325 หรือ A490 เพื่อเพิ่มค่า $F_{nv}$
        3. **เพิ่มขนาดน็อต (Increase Diameter):** การเปลี่ยนจาก M16 เป็น M20 จะเพิ่มพื้นที่หน้าตัด $A_b$ เกือบ 2 เท่า
        4. **เปลี่ยนประเภทจุดต่อ (Connection Type):** หาก Bearing บน Web เกิน ให้เพิ่มแผ่น Doubler Plate หรือใช้ Fin Plate ที่หนาขึ้น
        5. **เช็คระยะขอบ (Edge Distance):** หาก Block Shear เกิน ให้เพิ่มระยะขอบ $L_e$ เพื่อเพิ่มพื้นที่รับแรงเฉือนของเนื้อเหล็ก
        """)

    return n_bolts, cap_shear_1b
