# connection_design.py (V23 - Final Structural Mastery)
import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, thread_type="N", T_design=0):
    """
    V_design: Force (kg)
    T_design: Tension Force (kg)
    thread_type: "N" (Threads included in shear plane) หรือ "X" (Threads excluded)
    """
    p = section_data
    h_mm, tw_mm = p['h'], p['tw']
    tw_cm = tw_mm / 10
    Fy, Fu = 2450, 4000 # SS400 (kg/cm2)

    # 1. BOLT DATA & NOMINAL STRESS (AISC Table J3.2)
    # เราจะใช้ค่า Nominal Stress ในหน่วย kg/cm2 (แปลงจาก ksi)
    b_areas = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}
    Ab = b_areas.get(bolt_size, 3.14)
    d_mm = int(bolt_size[1:])
    d_cm = d_mm / 10
    dh_cm = (d_mm + 2) / 10 

    # Bolt Database (Fnv changes by Thread Type N/X)
    bolt_db = {
        "A325 (High Strength)": {"Fnt": 6325, "Fnv_N": 3795, "Fnv_X": 4780},
        "Grade 8.8 (Standard)": {"Fnt": 5300, "Fnv_N": 3200, "Fnv_X": 4000},
        "A490 (Premium)":       {"Fnt": 7940, "Fnv_N": 4780, "Fnv_X": 5975}
    }
    spec = bolt_db.get(bolt_grade)
    Fnt = spec["Fnt"]
    Fnv = spec["Fnv_N"] if thread_type == "N" else spec["Fnv_X"]

    # 2. DESIGN PARAMETERS (AISC 360-16 Chapter J)
    if is_lrfd:
        phi = 0.75      # Rupture/Shear/Bearing
        omega = 1.00
        method_label = "LRFD"
        # LaTeX Components
        phi_omega_symbol = r"\phi"
        phi_omega_val = "0.75"
        op_symbol = r"\times"
    else:
        phi = 1.00
        omega = 2.00    # Rupture/Shear/Bearing
        method_label = "ASD"
        # LaTeX Components
        phi_omega_symbol = r"\Omega"
        phi_omega_val = "2.00"
        op_symbol = r"/"

    # 3. NOMINAL STRENGTH CALCULATION
    rn_shear_1b = Fnv * Ab
    rn_tension_1b = Fnt * Ab
    
    # 4. INITIAL BOLT QUANTITY (Based on Shear & Bearing)
    rn_bearing_1b = 2.4 * d_cm * tw_cm * Fu
    limit_1b = min(rn_shear_1b, rn_bearing_1b)
    cap_1b = (phi * limit_1b) / omega
    
    n_bolts = max(2, math.ceil(V_design / cap_1b))
    if n_bolts % 2 != 0: n_bolts += 1
    n_rows = n_bolts // 2

    # 5. COMBINED FORCE INTERACTION (AISC J3.7)
    frv = V_design / (n_bolts * Ab) # Required shear stress
    if is_lrfd:
        # LRFD: F'nt = 1.3Fnt - (Fnt/(phi*Fnv))*frv <= Fnt
        Fnt_prime = min(1.3 * Fnt - (Fnt / (0.75 * Fnv)) * frv, Fnt)
    else:
        # ASD: F'nt = 1.3Fnt - (Omega*Fnt/Fnv)*frv <= Fnt
        Fnt_prime = min(1.3 * Fnt - (2.0 * Fnt / Fnv) * frv, Fnt)
    
    Rn_combined = n_bolts * Fnt_prime * Ab
    cap_combined = (phi * Rn_combined) / omega

    # 6. DISPLAY RESULTS
    st.subheader(f"🏗️ Engineering Report: {method_label} Analysis")
    st.caption(f"Referenced Specification: ANSI/AISC 360-16 | Thread Type: {thread_type}")

    # Layout Metrics
    m1, m2, m3, m4 = st.columns(4)
    v_cap_total = (phi * n_bolts * limit_1b) / omega
    v_ratio = V_design / v_cap_total
    
    m1.metric("Bolt Shear Cap.", f"{v_cap_total:,.0f} kg", f"Ratio: {v_ratio:.2f}")
    m2.metric("Combined T-V Cap.", f"{cap_combined:,.0f} kg", f"Ratio: {T_design/cap_combined:.2f}" if T_design > 0 else "0.00")
    m3.metric("Fnv Used", f"{Fnv} kg/cm²", f"Type {thread_type}")
    m4.metric("Bolt Count", f"{n_bolts} Nos.", f"{n_rows} Rows")

    # 7. THE MASTER CALCULATION NOTE
    st.markdown("---")
    with st.expander("📖 รายการคำนวณฉบับสมบูรณ์ (Detailed Engineering Calculation)", expanded=True):
        
        # Section 1: Shear
        st.markdown(f"#### 1. Bolt Shear Rupture (AISC Section J3.6)")
        st.latex(fr"R_n = F_{{nv}} A_b N_b = {Fnv} \cdot {Ab:.2f} \cdot {n_bolts} = {n_bolts*rn_shear_1b:,.0f} \text{{ kg}}")
        if is_lrfd:
            st.latex(fr"\phi R_n = {phi_omega_val} {op_symbol} {n_bolts*rn_shear_1b:,.0f} = {v_cap_total:,.0f} \text{{ kg}}")
        else:
            st.latex(fr"R_n / {phi_omega_symbol} = {n_bolts*rn_shear_1b:,.0f} {op_symbol} {phi_omega_val} = {v_cap_total:,.0f} \text{{ kg}}")

        # Section 2: Interaction
        if T_design > 0:
            st.markdown(f"#### 2. Combined Shear and Tension (AISC Section J3.7)")
            st.latex(fr"f_{{rv}} = V_u / (N A_b) = {frv:.1f} \text{{ kg/cm}}^2")
            if is_lrfd:
                st.latex(fr"F'_{{nt}} = 1.3F_{{nt}} - \frac{{F_{{nt}}}}{{\phi F_{{nv}}}} f_{{rv}} \leq F_{{nt}}")
                st.latex(fr"F'_{{nt}} = 1.3({Fnt}) - \frac{{{Fnt}}}{{0.75 \cdot {Fnv}}} ({frv:.1f}) = {Fnt_prime:.1f} \text{{ kg/cm}}^2")
            else:
                st.latex(fr"F'_{{nt}} = 1.3F_{{nt}} - \frac{{\Omega F_{{nt}}}}{{F_{{nv}}}} f_{{rv}} \leq F_{{nt}}")
                st.latex(fr"F'_{{nt}} = 1.3({Fnt}) - \frac{{2.0 \cdot {Fnt}}}{{{Fnv}}} ({frv:.1f}) = {Fnt_prime:.1f} \text{{ kg/cm}}^2")
            
            st.latex(fr"\text{{Available Tension}} = {cap_combined:,.0f} \text{{ kg}}")

    # 8. RECOMMENDATION ENGINE
    if v_ratio > 1.0 or (T_design/cap_combined if T_design > 0 else 0) > 1.0:
        st.error("❗ Ratio เกินมาตรฐาน: โปรดพิจารณาเปลี่ยนเกรดน็อตเป็น A490 หรือเพิ่มขนาดเป็น M24")
    
    return n_bolts, cap_1b
