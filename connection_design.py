# connection_design.py (V16 - Complete Engineering Check)
import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade):
    """
    ฟังก์ชันคำนวณจุดต่อแบบครบทุกกรณี (Ultimate Checklist)
    """
    p = section_data
    # ดึงค่าต่างๆ มาใช้ (หน่วย mm และ cm)
    h_mm, tw_mm, tf_mm = p['h'], p['tw'], p['tf']
    tw_cm = tw_mm / 10
    
    # 1. ข้อมูล Bolt & Hole
    b_areas = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}
    b_area = b_areas.get(bolt_size, 3.14)
    dia_mm = int(bolt_size[1:])
    dia_cm = dia_mm / 10
    hole_dia_mm = dia_mm + 2 # Standard Hole

    # 2. Material Properties (SS400 & Bolt Grade)
    bolt_stress_map = {
        "A325 (High Strength)": 3795, 
        "Grade 8.8 (Standard)": 3200, 
        "A490 (Premium)": 4780
    }
    F_nv = bolt_stress_map.get(bolt_grade, 3795)
    Fu_plate = 4000 # kg/cm2
    Fy_plate = 2450 # kg/cm2

    # 3. Safety Factors (AISC 360)
    phi = 0.75 if is_lrfd else 1.0
    omega = 1.0 if is_lrfd else 2.00
    
    # --- STEP A: จำนวนน็อตเบื้องต้น ---
    # คำนวณหาแรงที่ Bolt 1 ตัวรับได้ก่อน (Shear vs Bearing)
    v_shear_1bolt = (phi * F_nv * b_area) / omega
    v_bearing_1bolt = (phi * 2.4 * dia_cm * tw_cm * Fu_plate) / omega
    v_single_bolt_cap = min(v_shear_1bolt, v_bearing_1bolt)
    
    reduction = 0.85 if conn_type == "Beam-to-Beam" else 1.0
    req_bolt_calc = V_design / (v_single_bolt_cap * reduction)
    n_bolts = max(2, math.ceil(req_bolt_calc))
    if n_bolts % 2 != 0: n_bolts += 1 # ปรับเป็นเลขคู่
    n_rows = n_bolts // 2

    # 4. Layout & Block Shear Calculation
    pitch = 3.0 * dia_mm
    edge_dist = 1.5 * dia_mm
    
    # Block Shear Rupture (AISC 360 Chapter J)
    # พื้นที่รับแรงดึง (Tension area) และแรงเฉือน (Shear area) ของ Web
    Ant = (2 * edge_dist - 1.0 * hole_dia_mm) * tw_mm / 100 # Net tension (cm2)
    Anv = ((n_rows-1)*pitch + edge_dist - (n_rows-0.5)*hole_dia_mm) * tw_mm / 100 * 2 # Net shear (cm2)
    Rn_block = (0.6 * Fu_plate * Anv + 1.0 * Fu_plate * Ant) 
    v_block_shear = (phi * Rn_block) / omega

    # Shear Yielding of Web
    v_web_yield = ( (0.9 if is_lrfd else 1.0) * 0.6 * Fy_plate * (h_mm * tw_mm / 100) ) / (1.0 if is_lrfd else 1.5)

    # --- UI RENDERING ---
    st.markdown(f"### 🔩 Comprehensive Analysis")
    
    # แสดง Dashboard สรุปทุก Case
    cols = st.columns(4)
    check_list = [
        ("Bolt Shear", v_shear_1bolt * n_bolts, "Bolt Rupture"),
        ("Bearing", v_bearing_1bolt * n_bolts, "Web Crushing"),
        ("Block Shear", v_block_shear, "Web Tear-out"),
        ("Web Yielding", v_web_yield, "Gross Shear")
    ]

    for i, (name, cap, fail_mode) in enumerate(check_list):
        with cols[i]:
            ratio = V_design / cap
            status_color = "#10b981" if ratio <= 1.0 else "#ef4444"
            st.markdown(f"""
            <div style="text-align:center; padding:15px; border:2px solid {status_color}40; border-radius:12px; background:{status_color}05;">
                <small style="color:#6b7280; font-weight:bold;">{name.upper()}</small><br>
                <b style="color:{status_color}; font-size:20px;">{cap:,.0f} kg</b><br>
                <div style="font-size:12px; margin-top:5px; padding:2px; background:{status_color}; color:white; border-radius:4px;">Ratio: {ratio:.3f}</div>
            </div>
            """, unsafe_allow_html=True)

    # Drawing ส่วนจุดต่อ
    st.divider()
    c1, c2 = st.columns([1, 1.5])
    with c1:
        st.info("**Design Summary**")
        st.write(f"- **Bolt Used:** {n_bolts} x {bolt_size} {bolt_grade}")
        st.write(f"- **Design Shear Force ($V_u$):** {V_design:,.0f} kg")
        governing_cap = min([c[1] for c in check_list])
        st.success(f"**Governing Capacity:** {governing_cap:,.0f} kg")
    
    with c2:
        fig = go.Figure()
        fig.add_shape(type="rect", x0=-120, y0=-20, x1=-100, y1=h_mm+20, fillcolor="#475569") # Support
        fig.add_shape(type="rect", x0=-100, y0=0, x1=150, y1=h_mm, line_color="RoyalBlue", fillcolor="rgba(65, 105, 225, 0.1)") # Beam
        start_y = (h_mm/2) - ((n_rows-1)*pitch)/2
        for r in range(n_rows):
            y = start_y + r*pitch
            for x in [-75, -45]:
                fig.add_trace(go.Scatter(x=[x], y=[y], mode='markers', marker=dict(size=12, color='#ef4444', line=dict(width=1, color='white'))))
        fig.update_layout(showlegend=False, height=300, margin=dict(l=0,r=0,t=0,b=0), xaxis_visible=False, yaxis_visible=False, plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)

    # รายการคำนวณละเอียด (LaTeX)
    with st.expander("📝 VIEW DETAILED CALCULATION STEPS"):
        st.subheader("1. Bolt Shear Strength (AISC 360-16)")
        st.latex(fr"R_n = F_{{nv}} A_b = {F_nv:,.0f} \cdot {b_area:.2f} \cdot {n_bolts} = {F_nv*b_area*n_bolts:,.0f} \text{{ kg}}")
        st.latex(fr"\text{{Capacity}} = {v_shear_1bolt * n_bolts:,.0f} \text{{ kg}} ({'LRFD \phi=0.75' if is_lrfd else 'ASD \Omega=2.0'})")

        st.subheader("2. Block Shear Rupture (AISC 360-16 J4.3)")
        
        st.latex(fr"R_n = 0.6 F_u A_{{nv}} + U_{{bs}} F_u A_{{nt}}")
        st.write(f"Net Shear Area ($A_{{nv}}$): {Anv:.2f} cm², Net Tension Area ($A_{{nt}}$): {Ant:.2f} cm²")
        st.latex(fr"R_n = 0.6 \cdot 4000 \cdot {Anv:.2f} + 1.0 \cdot 4000 \cdot {Ant:.2f} = {Rn_block:,.0f} \text{{ kg}}")
        
        st.subheader("3. Dimensional Check")
        st.write(f"- Minimum Pitch (3d): {3*dia_mm} mm | **Used: {pitch} mm**")
        st.write(f"- Minimum Edge Distance (1.5d): {1.5*dia_mm} mm | **Used: {edge_dist} mm**")

    return n_bolts, v_single_bolt_cap * reduction
