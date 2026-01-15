# connection_design.py (V22 - Professional Structural Engineer Edition)
import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    """
    V_design: Force (kg)
    T_design: Tension Force (kg) - เพิ่ม Input แรงดึงเข้ามา
    """
    p = section_data
    h_mm, tw_mm, tf_mm = p['h'], p['tw'], p['tf']
    tw_cm = tw_mm / 10
    Fy, Fu = 2450, 4000 # SS400 (kg/cm2)

    # 1. BOLT & HOLE GEOMETRY (AISC Table J3.3)
    b_areas = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}
    Ab = b_areas.get(bolt_size, 3.14)
    d_mm = int(bolt_size[1:])
    d_cm = d_mm / 10
    dh_cm = (d_mm + 2) / 10 # Standard Hole (d+2mm)

    # 2. NOMINAL STRENGTHS (AISC Table J3.2)
    # Fnv: Shear (Threads included), Fnt: Tension
    bolt_map = {
        "A325 (High Strength)": {"Fnv": 3795, "Fnt": 6325},
        "Grade 8.8 (Standard)": {"Fnv": 3200, "Fnt": 5300},
        "A490 (Premium)": {"Fnv": 4780, "Fnt": 7940}
    }
    spec = bolt_map.get(bolt_grade, bolt_map["A325 (High Strength)"])
    Fnv, Fnt = spec["Fnv"], spec["Fnt"]

    # 3. DESIGN PHILOSOPHY (LRFD vs ASD) - เด็ดขาดตาม AISC Chapter J
    if is_lrfd:
        phi = 0.75      # Rupture/Shear/Bearing
        phi_y = 1.00    # Yielding
        omega = 1.00
        omega_y = 1.00
        method_name = "LRFD (Load and Resistance Factor Design)"
        status_text = "Required Strength (Ru)"
    else:
        phi = 1.00
        phi_y = 1.00
        omega = 2.00    # Rupture/Shear/Bearing
        omega_y = 1.50  # Yielding
        method_name = "ASD (Allowable Strength Design)"
        status_text = "Allowable Strength (Rn/Ω)"

    # 4. INITIAL BOLT CALCULATION
    rn_shear_1b = Fnv * Ab
    rn_bearing_1b = 2.4 * d_cm * tw_cm * Fu
    # กำลังต่อตัว (Governing Shear/Bearing)
    cap_1b_shear = (phi * min(rn_shear_1b, rn_bearing_1b)) / omega
    
    n_bolts = max(2, math.ceil(V_design / cap_1b_shear))
    if n_bolts % 2 != 0: n_bolts += 1
    n_rows = n_bolts // 2

    # 5. SPACING & LAYOUT (AISC J3.3)
    s_pitch = 3.0 * d_mm
    l_edge = 1.5 * d_mm
    lc_cm = (l_edge/10) - (dh_cm / 2) # Clear distance

    # 6. LIMIT STATES ANALYSIS
    # --- Case 1: Bolt Shear (J3.6) ---
    Rn_bolt_shear = n_bolts * Fnv * Ab
    # --- Case 2: Bolt Tension (J3.6) ---
    Rn_bolt_tension = n_bolts * Fnt * Ab
    # --- Case 3: Combined Shear & Tension (J3.7) ---
    frv = V_design / (n_bolts * Ab) # Required shear stress
    if is_lrfd:
        Fnt_prime = min(1.3 * Fnt - (Fnt / (phi * Fnv)) * frv, Fnt)
    else:
        Fnt_prime = min(1.3 * Fnt - (omega * Fnt / Fnv) * frv, Fnt)
    Rn_combined = n_bolts * Fnt_prime * Ab
    
    # --- Case 4: Bearing & Tear-out (J3.10) ---
    Rn_bear = n_bolts * (2.4 * d_cm * tw_cm * Fu)
    Rn_tear = n_bolts * (1.2 * lc_cm * tw_cm * Fu)
    Rn_bearing_gov = min(Rn_bear, Rn_tear)

    # --- Case 5: Block Shear (J4.3) ---
    Anv = ((n_rows-1)*(s_pitch/10) + l_edge/10 - (n_rows-0.5)*dh_cm) * tw_cm * 2
    Ant = (2 * l_edge/10 - 1.0 * dh_cm) * tw_cm
    Rn_block = min(0.6*Fu*Anv + 1.0*Fu*Ant, 0.6*Fy*Anv + 1.0*Fu*Ant)

    # 7. CAPACITY SUMMARY
    caps = {
        "Bolt Shear": (phi * Rn_bolt_shear) / omega,
        "Bearing/Tear-out": (phi * Rn_bearing_gov) / omega,
        "Block Shear": (phi * Rn_block) / omega,
        "Combined T-V": (phi * Rn_combined) / omega,
        "Web Yielding": (phi_y * 0.6 * Fy * (h_mm * tw_mm / 100)) / omega_y
    }

    # --- UI RENDERING ---
    st.title(f"🔍 {method_name}")
    st.info(f"Analysis Reference: AISC 360-16 Chapter J | Bolt: {bolt_grade}")

    # Dashboard Metrics
    cols = st.columns(len(caps))
    for i, (name, val) in enumerate(caps.items()):
        force = V_design if "Shear" in name or "Web" in name or "Bearing" in name or "Block" in name else T_design
        ratio = force / val if val > 0 else 0
        color = "normal" if ratio <= 1.0 else "inverse"
        cols[i].metric(name, f"{val:,.0f} kg", f"Ratio {ratio:.2f}", delta_color=color)

    # 8. STEP-BY-STEP CALCULATION NOTE
    st.markdown("---")
    st.subheader("📝 รายการคำนวณแยกสูตรตามระบบที่เลือก (Calculation Detail)")

    # Section 1: Shear
    with st.expander("STEP 1: Bolt Shear (AISC J3.6)", expanded=True):
        st.latex(fr"F_{{nv}} = {Fnv} \text{{ kg/cm}}^2, \quad A_b = {Ab} \text{{ cm}}^2")
        st.latex(fr"R_n = F_{{nv}} A_b N_b = {Fnv} \cdot {Ab} \cdot {n_bolts} = {Rn_bolt_shear:,.0f} \text{{ kg}}")
        if is_lrfd:
            st.latex(fr"\phi R_n = 0.75 \cdot {Rn_bolt_shear:,.0f} = {caps['Bolt Shear']:,.0f} \text{{ kg}}")
        else:
            st.latex(fr"R_n / \Omega = {Rn_bolt_shear:,.0f} / 2.00 = {caps['Bolt Shear']:,.0f} \text{{ kg}}")

    # Section 2: Combined Force
    with st.expander("STEP 2: Combined Shear & Tension (AISC J3.7)"):
        st.latex(fr"f_{{rv}} = V / (N A_b) = {frv:.1f} \text{{ kg/cm}}^2")
        if is_lrfd:
            st.latex(fr"F'_{{nt}} = 1.3F_{{nt}} - \frac{{F_{{nt}}}}{{\phi F_{{nv}}}} f_{{rv}} = 1.3({Fnt}) - \frac{{{Fnt}}}{{0.75 \cdot {Fnv}}} ({frv:.1f}) = {Fnt_prime:.1f} \text{{ kg/cm}}^2")
            st.latex(fr"\phi R_n = 0.75 (F'_{{nt}} A_b N_b) = {caps['Combined T-V']:,.0f} \text{{ kg}}")
        else:
            st.latex(fr"F'_{{nt}} = 1.3F_{{nt}} - \frac{{\Omega F_{{nt}}}}{{F_{{nv}}}} f_{{rv}} = 1.3({Fnt}) - \frac{{2.0 \cdot {Fnt}}}{{{Fnv}}} ({frv:.1f}) = {Fnt_prime:.1f} \text{{ kg/cm}}^2")
            st.latex(fr"R_n / \Omega = (F'_{{nt}} A_b N_b) / 2.00 = {caps['Combined T-V']:,.0f} \text{{ kg}}")

    # Section 3: Block Shear
    with st.expander("STEP 3: Block Shear Rupture (AISC J4.3)"):
        
        st.write(f"Net Shear Area (Anv): {Anv:.2f} cm² | Net Tension Area (Ant): {Ant:.2f} cm²")
        st.latex(fr"R_n = \min(0.6 F_u A_{{nv}} + U_{{bs}} F_u A_{{nt}}, 0.6 F_y A_{{nv}} + U_{{bs}} F_u A_{{nt}})")
        st.latex(fr"R_n = {Rn_block:,.0f} \text{{ kg}}")

    # 9. ENGINEERING RECOMMENDATIONS
    max_ratio = max([V_design/v if "Combined" not in k else T_design/v for k, v in caps.items()])
    if max_ratio > 1.0:
        st.error(f"### ⚠️ Ratio เกินมาตรฐาน ({max_ratio:.2f})")
        st.markdown(f"""
        **ข้อแนะนำทางวิศวกรรมเพื่อแก้ไขจุดต่อ:**
        - **หาก Bolt Shear เกิน:** เพิ่มจำนวนน็อต หรือ เปลี่ยนจาก **Thread Included (N)** เป็น **Thread Excluded (X)** เพื่อใช้ค่า $F_{{nv}}$ ที่สูงขึ้น
        - **หาก Bearing/Tear-out เกิน:** เพิ่มความหนาของแผ่น Web หรือเพิ่มระยะขอบ ($L_e$)
        - **หาก Combined เกิน:** ลดแรงดึงที่เกิดขึ้น หรือใช้น็อตเกรดสูงขึ้น เช่น **A490**
        """)

    return n_bolts, cap_1b_shear
