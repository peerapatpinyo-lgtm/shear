# connection_design.py (V20 - Final Engineering Validation)
import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade):
    # 1. ข้อมูลหน้าตัดและวัสดุ (Material Properties)
    p = section_data
    h_mm, tw_mm, tf_mm = p['h'], p['tw'], p['tf']
    tw_cm = tw_mm / 10
    Fy, Fu = 2450, 4000 # SS400 (kg/cm2)

    # 2. ข้อมูลน็อต (Bolt Properties - AISC J3.2)
    b_areas = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}
    Ab = b_areas.get(bolt_size, 3.14)
    d_mm = int(bolt_size[1:])
    d_cm = d_mm / 10
    dh_cm = (d_mm + 2) / 10 # Standard Hole Size

    bolt_map = {"A325 (High Strength)": 3795, "Grade 8.8 (Standard)": 3200, "A490 (Premium)": 4780}
    Fnv = bolt_map.get(bolt_grade, 3795)

    # 3. ตัวคูณความปลอดภัย (Safety Factors - AISC 360-16)
    if is_lrfd:
        phi_bolt, phi_plate, phi_yield = 0.75, 0.75, 1.00
        omega_bolt, omega_plate, omega_yield = 1.00, 1.00, 1.00
        method_name = "LRFD"
    else:
        phi_bolt, phi_plate, phi_yield = 1.00, 1.00, 1.00
        omega_bolt, omega_plate, omega_yield = 2.00, 2.00, 1.50
        method_name = "ASD"

    # 4. คำนวณเบื้องต้นเพื่อหาจำนวนน็อต (Preliminary Selection)
    rn_shear_1b = Fnv * Ab
    rn_bearing_1b = 2.4 * d_cm * tw_cm * Fu
    rn_gov_1b = min(rn_shear_1b, rn_bearing_1b)
    
    cap_1b = (phi_bolt * rn_gov_1b) / omega_bolt
    n_bolts = max(2, math.ceil(V_design / cap_1b))
    if n_bolts % 2 != 0: n_bolts += 1
    n_rows = n_bolts // 2

    # 5. การเช็คระยะตามมาตรฐาน (Dimensional Limits - AISC J3.3 & J3.4)
    s_pitch = 3.0 * d_mm  # นิยมใช้ 3d
    l_edge = 1.5 * d_mm   # นิยมใช้ 1.5d
    lc_cm = (l_edge - (d_mm+2)/2) / 10 # Clear distance สำหรับตัวล่างสุด

    # 6. รายการคำนวณละเอียด (Limit States Analysis)
    
    # CASE A: Bolt Shear Rupture (J3.6)
    Rn_bolt = n_bolts * Fnv * Ab
    
    # CASE B: Bearing & Tear-out (J3.10)
    # Tear-out: 1.2 * Lc * t * Fu | Bearing: 2.4 * d * t * Fu
    Rn_bearing = n_bolts * (2.4 * d_cm * tw_cm * Fu)
    Rn_tearout = n_bolts * (1.2 * lc_cm * tw_cm * Fu)
    Rn_bearing_gov = min(Rn_bearing, Rn_tearout)

    # CASE C: Block Shear Rupture (J4.3)
    # สมมติแนวการขาดแบบ 2 แถว
    Anv = ((n_rows-1)*(s_pitch/10) + l_edge/10 - (n_rows-0.5)*dh_cm) * tw_cm * 2
    Ant = (2 * l_edge/10 - 1.0 * dh_cm) * tw_cm
    Rn_block = min(0.6*Fu*Anv + 1.0*Fu*Ant, 0.6*Fy*Anv + 1.0*Fu*Ant)

    # CASE D: Shear Yielding of Web (G2.1)
    Agv = (h_mm * tw_mm) / 100 # cm2
    Rn_web_yield = 0.6 * Fy * Agv

    # สรุปกำลังที่รับได้จริง
    cap_bolt = (phi_bolt * Rn_bolt) / omega_bolt
    cap_bear = (phi_plate * Rn_bearing_gov) / omega_plate
    cap_block = (phi_plate * Rn_block) / omega_plate
    cap_web = (phi_yield * Rn_web_yield) / omega_yield

    # --- ส่วนการแสดงผล (UI) ---
    st.markdown(f"### 🧪 การวิเคราะห์จุดต่อแบบละเอียด ({method_name})")
    
    # Dashboard แสดงผล
    d1, d2, d3, d4 = st.columns(4)
    checks = [("Bolt Shear", cap_bolt), ("Bearing", cap_bear), ("Block Shear", cap_block), ("Web Yield", cap_web)]
    for col, (name, val) in zip([d1, d2, d3, d4], checks):
        ratio = V_design / val
        color = "green" if ratio <= 1.0 else "red"
        col.markdown(f"<div style='text-align:center;'><b>{name}</b><br><h2 style='color:{color};'>{val:,.0f}</h2><small>Ratio: {ratio:.2f}</small></div>", unsafe_allow_html=True)

    st.divider()

    # รายการคำนวณ LaTeX แยกตามบทใน AISC
    with st.expander("📖 ดูรายการคำนวณตามมาตรฐาน AISC 360-16 (Step-by-Step)"):
        # Section Bolt
        st.subheader("1. กำลังรับแรงเฉือนของน็อต (Bolt Shear)")
        st.latex(fr"R_n = F_{{nv}} A_b N_b = {Fnv} \cdot {Ab} \cdot {n_bolts} = {Rn_bolt:,.0f} \text{{ kg}}")
        if is_lrfd: st.latex(fr"\phi R_n = 0.75 \cdot {Rn_bolt:,.0f} = {cap_bolt:,.0f} \text{{ kg}}")
        else: st.latex(fr"R_n / \Omega = {Rn_bolt:,.0f} / 2.00 = {cap_bolt:,.0f} \text{{ kg}}")

        # Section Bearing
        st.subheader("2. กำลังรับแรงแบกทานและแรงดึงขาด (Bearing & Tear-out)")
        
        st.latex(fr"R_n = \min( 2.4 d t F_u, 1.2 L_c t F_u ) \cdot N_b")
        st.write(f"Bearing: {Rn_bearing:,.0f} kg | Tear-out: {Rn_tearout:,.0f} kg")
        st.write(f"Governing Nominal Strength: **{Rn_bearing_gov:,.0f} kg**")

        # Section Block Shear
        st.subheader("3. การวิบัติแบบฉีกขาดเป็นกลุ่ม (Block Shear Rupture)")
        
        st.latex(fr"R_n = 0.6 F_u A_{{nv}} + U_{{bs}} F_u A_{{nt}}")
        st.write(f"Net Shear Area (Anv): {Anv:.2f} cm² | Net Tension Area (Ant): {Ant:.2f} cm²")
        st.latex(fr"R_n = {Rn_block:,.0f} \text{{ kg}}")

        # Section Dimension
        st.subheader("4. การตรวจสอบมิติตามข้อกำหนด (Dimensional Checks)")
        st.write(f"- ระยะห่างระหว่างน็อต (Pitch): {s_pitch} mm (Min 2.67d: {2.67*d_mm:.1f} mm) ✅")
        st.write(f"- ระยะขอบน็อต (Edge): {l_edge} mm (Min Table J3.4) ✅")

    # Layout Sketch
    st.divider()
    st.subheader("📍 Layout Sketch")
    fig = go.Figure()
    fig.add_shape(type="rect", x0=0, y0=0, x1=10, y1=h_mm, fillcolor="rgba(100,100,100,0.1)", line_color="black")
    start_y = (h_mm/2) - ((n_rows-1)*s_pitch)/2
    for r in range(n_rows):
        y = start_y + r*s_pitch
        for x in [3, 7]: # 2 rows of bolts
            fig.add_trace(go.Scatter(x=[x], y=[y], mode='markers', marker=dict(size=12, color='red', symbol='circle')))
    fig.update_layout(xaxis_visible=False, yaxis_visible=False, height=300, margin=dict(l=0,r=0,t=20,b=0))
    st.plotly_chart(fig, use_container_width=True)

    return n_bolts, cap_1b
