# connection_design.py (V13 - Updated Calculation Logic)
import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade):
    """
    ฟังก์ชันคำนวณจุดต่อตามมาตรฐาน AISC 360
    V_design: แรงเฉือนออกแบบ (kg)
    bolt_grade: เกรดน็อตที่เลือก (A325, 8.8, A490)
    """
    p = section_data
    h_mm, tw_mm = p['h'], p['tw']
    tw_cm = tw_mm / 10
    
    # 1. ข้อมูล Bolt (Area & Nominal Stress ตามมาตรฐาน AISC)
    b_areas = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}
    b_area = b_areas.get(bolt_size, 3.14)
    dia_cm = int(bolt_size[1:]) / 10

    # กำหนดค่า Fnv (Nominal Shear Stress - Threads Included: N-Type)
    # ค่ามาตรฐาน AISC 360: A325 = 54 ksi (~3795 ksc), A490 = 68 ksi (~4780 ksc)
    bolt_stress_map = {
        "A325 (High Strength)": 3795,
        "Grade 8.8 (Standard)": 3200,
        "A490 (Premium)": 4780
    }
    F_nv = bolt_stress_map.get(bolt_grade, 3795)

    # 2. ปัจจัยความปลอดภัย (Safety/Resistance Factors)
    if is_lrfd:
        phi_shear = 0.75
        phi_bearing = 0.75
        v_bolt_shear = phi_shear * (F_nv * b_area)
        # Bearing: Rn = 2.4 * d * t * Fu (SS400 Fu ~ 4000 ksc)
        v_bolt_bearing = phi_bearing * (2.4 * dia_cm * tw_cm * 4000)
    else:
        omega_shear = 2.00
        omega_bearing = 2.00
        v_bolt_shear = (F_nv * b_area) / omega_shear
        v_bolt_bearing = (2.4 * dia_cm * tw_cm * 4000) / omega_bearing

    # กำลังสุทธิของ Bolt 1 ตัว (ค่าน้อยสุดระหว่าง Shear และ Bearing)
    v_bolt_cap = min(v_bolt_shear, v_bolt_bearing)
    
    # 3. การลดทอนกำลัง (Reduction Factors)
    reduction = 0.85 if conn_type == "Beam-to-Beam" else 1.0
    v_final_cap = v_bolt_cap * reduction

    # 4. จำนวนน็อต
    req_bolt_calc = V_design / v_final_cap
    n_bolts = math.ceil(req_bolt_calc)
    if n_bolts < 2: n_bolts = 2
    if n_bolts % 2 != 0: n_bolts += 1 

    # 5. Layout Check
    n_rows = int(n_bolts / 2)
    pitch, edge = 3.0 * (dia_cm * 10), 1.5 * (dia_cm * 10)
    h_req = (n_rows - 1) * pitch + (2 * edge)
    h_avail = h_mm - (2 * p['tf']) - (40 if conn_type == "Beam-to-Beam" else 20)
    is_ok = h_req <= h_avail

    # --- UI Rendering ---
    st.markdown(f"### 🔩 {conn_type} Analysis")
    
    c1, c2 = st.columns([1, 1.2])
    with c1:
        st.success(f"Bolt Grade: {bolt_grade}")
        st.write(f"**Calculated Capacity:**")
        st.write(f"- Shear Limit: {v_bolt_shear:,.0f} kg")
        st.write(f"- Bearing Limit: {v_bolt_bearing:,.0f} kg")
        
        st.divider()
        st.metric("Final Bolt Strength", f"{v_final_cap:,.0f} kg/ea")
        st.metric("Required Quantity", f"{n_bolts} Nos")
        
        if not is_ok:
            st.error(f"❌ Layout Fail: Web height insufficient (Req: {h_req}mm > Avail: {h_avail}mm)")
        else:
            st.info(f"✅ Layout OK (Used: {h_req}mm / Avail: {h_avail}mm)")

    with c2:
        # Drawing Logic (คงเดิมแต่ปรับตำแหน่ง)
        fig = go.Figure()
        # Support
        fig.add_shape(type="rect", x0=-120, y0=-20, x1=-100, y1=h_mm+20, fillcolor="#475569")
        # Beam Web
        fig.add_shape(type="rect", x0=-100, y0=0, x1=150, y1=h_mm, line_color="RoyalBlue", fillcolor="rgba(65, 105, 225, 0.1)")
        # Bolts
        start_y = (h_mm/2) - ((n_rows-1)*pitch)/2
        for r in range(n_rows):
            y = start_y + r*pitch
            for x in [-75, -45]:
                fig.add_trace(go.Scatter(x=[x], y=[y], mode='markers', marker=dict(size=12, color='#ef4444', line=dict(width=1, color='white'))))
        
        fig.update_layout(showlegend=False, height=350, margin=dict(l=0,r=0,t=0,b=0), xaxis_visible=False, yaxis_visible=False, plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)

    return n_bolts, v_final_cap
