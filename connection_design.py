# connection_design.py (V15 - Ultimate Standard Version)
import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade):
    p = section_data
    h_mm, tw_mm, tf_mm = p['h'], p['tw'], p['tf']
    tw_cm = tw_mm / 10
    
    # 1. ข้อมูลพื้นฐาน
    b_areas = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}
    b_area = b_areas.get(bolt_size, 3.14)
    dia_mm = int(bolt_size[1:])
    dia_cm = dia_mm / 10
    hole_dia_mm = dia_mm + 2 # รูเจาะมาตรฐาน +2mm

    # Material Properties
    bolt_stress_map = {"A325 (High Strength)": 3795, "Grade 8.8 (Standard)": 3200, "A490 (Premium)": 4780}
    F_nv = bolt_stress_map.get(bolt_grade, 3795)
    Fu_plate = 4000 # SS400 Ultimate
    Fy_plate = 2450 # SS400 Yield

    # 2. Factors
    phi = 0.75 if is_lrfd else 1.0
    omega = 1.0 if is_lrfd else 2.00
    phi_v = 1.0 if is_lrfd else 1.0 # สำหรับ Yielding
    omega_v = 1.0 if is_lrfd else 1.5

    # 3. Calculation Limit States
    # CASE A: Bolt Shear (น็อตขาด)
    v_shear_bolt = (phi * F_nv * b_area) / omega
    
    # CASE B: Plate Bearing (รูเจาะยับ)
    v_bearing_bolt = (phi * 2.4 * dia_cm * tw_cm * Fu_plate) / omega

    # CASE C: Block Shear (เหล็ก Web ฉีกขาดเป็นบง)
    # สมมติ Layout มาตรฐานเพื่อประเมิน Block Shear เบื้องต้น
    v_bolt_cap = min(v_shear_bolt, v_bearing_bolt)
    reduction = 0.85 if conn_type == "Beam-to-Beam" else 1.0
    
    req_bolt_calc = V_design / (v_bolt_cap * reduction)
    n_bolts = max(2, math.ceil(req_bolt_calc))
    if n_bolts % 2 != 0: n_bolts += 1
    n_rows = n_bolts // 2

    # Layout Parameters
    pitch = 3.0 * dia_mm
    edge_dist = 1.5 * dia_mm
    
    # Block Shear Calculation (Simplified for Web)
    Ant = (2 * edge_dist - hole_dia_mm) * tw_mm / 100 # Net area tension
    Anv = ((n_rows-1)*pitch + edge_dist - (n_rows-0.5)*hole_dia_mm) * tw_mm / 100 * 2 # Net area shear
    Rn_block = (0.6 * Fu_plate * Anv + 1.0 * Fu_plate * Ant) # Ubs = 1.0
    v_block_shear = (phi * Rn_block) / omega

    # 4. Final Governing Strength
    total_bolt_cap = v_bolt_cap * n_bolts * reduction
    is_safe = total_bolt_cap >= V_design and v_block_shear >= V_design

    # --- UI ---
    st.markdown(f"### 🔩 Comprehensive Connection Check: {sec_name}")
    
    cols = st.columns(4)
    limit_states = [
        ("Bolt Shear", v_shear_bolt * n_bolts, "Bolt Rupture"),
        ("Bearing", v_bearing_bolt * n_bolts, "Plate Crushing"),
        ("Block Shear", v_block_shear, "Web Tear-out"),
        ("Web Yielding", (phi_v * 0.6 * Fy_plate * (h_mm-2*tf_mm)*tw_mm/100)/omega_v, "Shear Yielding")
    ]

    for i, (name, cap, fail_mode) in enumerate(limit_states):
        with cols[i]:
            ratio = V_design / cap
            color = "green" if ratio <= 1.0 else "red"
            st.markdown(f"""
            <div style="text-align:center; padding:10px; border:1px solid #ddd; border-radius:10px;">
                <small>{name}</small><br>
                <b style="color:{color}; font-size:18px;">{cap:,.0f} kg</b><br>
                <small style="color:#888;">Ratio: {ratio:.2f}</small>
            </div>
            """, unsafe_allow_html=True)

    # --- Calculation Detail Expander ---
    st.divider()
    with st.expander("🔍 VIEW ALL LIMIT STATE EQUATIONS (AISC 360)"):
        st.subheader("1. Bolt Shear Strength")
        st.latex(fr"R_n = F_{{nv}} A_b \cdot N_{{bolts}}")
        
        st.subheader("2. Bearing Strength on Web")
        st.latex(fr"R_n = (2.4 d t F_u) \cdot N_{{bolts}}")
        st.caption("ตรวจสอบการยุบตัวของขอบรูเจาะเหล็ก Web")

        st.subheader("3. Block Shear Rupture")
        st.latex(fr"R_n = 0.6 F_u A_{{nv}} + U_{{bs}} F_u A_{{nt}}")
        
        st.caption("ตรวจสอบการฉีกขาดของกลุ่มน็อตออกจากแผ่น Web")

        st.subheader("4. Dimensional Limits (Checks)")
        c1, c2, c3 = st.columns(3)
        c1.metric("Min Pitch (3d)", f"{3*dia_mm} mm", f"{pitch} mm (OK)")
        c2.metric("Min Edge (1.5d)", f"{1.5*dia_mm} mm", f"{edge_dist} mm (OK)")
        c3.metric("Max Pitch", "300 mm", f"{pitch} mm (OK)")

    return n_bolts, v_bolt_cap
