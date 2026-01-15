# connection_design.py (V14 - Detailed Calculation Note)
import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade):
    p = section_data
    h_mm, tw_mm = p['h'], p['tw']
    tw_cm = tw_mm / 10
    
    # 1. ข้อมูลพื้นฐาน
    b_areas = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}
    b_area = b_areas.get(bolt_size, 3.14)
    dia_mm = int(bolt_size[1:])
    dia_cm = dia_mm / 10

    # กำหนดค่า Fnv ตามมาตรฐาน AISC 360 (N-Type)
    bolt_stress_map = {
        "A325 (High Strength)": 3795,
        "Grade 8.8 (Standard)": 3200,
        "A490 (Premium)": 4780
    }
    F_nv = bolt_stress_map.get(bolt_grade, 3795)
    Fu_plate = 4000 # SS400

    # 2. คำนวณ Capacity (Detailed)
    if is_lrfd:
        phi = 0.75
        v_shear_bolt = phi * F_nv * b_area
        v_bearing_bolt = phi * 2.4 * dia_cm * tw_cm * Fu_plate
        method_name = "LRFD (φ = 0.75)"
    else:
        omega = 2.00
        v_shear_bolt = (F_nv * b_area) / omega
        v_bearing_bolt = (2.4 * dia_cm * tw_cm * Fu_plate) / omega
        method_name = "ASD (Ω = 2.00)"

    v_bolt_cap = min(v_shear_bolt, v_bearing_bolt)
    reduction = 0.85 if conn_type == "Beam-to-Beam" else 1.0
    v_final_cap = v_bolt_cap * reduction

    # 3. จำนวนน็อตและการจัดเรียง
    req_bolt_calc = V_design / v_final_cap
    n_bolts = math.ceil(req_bolt_calc)
    if n_bolts < 2: n_bolts = 2
    if n_bolts % 2 != 0: n_bolts += 1 

    n_rows = int(n_bolts / 2)
    pitch = 3.0 * dia_mm
    edge = 1.5 * dia_mm
    h_req = (n_rows - 1) * pitch + (2 * edge)
    h_avail = h_mm - (2 * p['tf']) - (40 if conn_type == "Beam-to-Beam" else 20)
    
    # --- UI RENDERING ---
    st.markdown(f"### 🔩 Connection Design: {bolt_grade} ({method})")
    
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.markdown(f"""
        <div class="detail-card">
            <small>Method: {method_name}</small><br>
            <span style="font-size:14px; color:#6b7280;">Final Capacity per Bolt:</span>
            <div style="font-size:28px; font-weight:700; color:#2563eb;">{v_final_cap:,.0f} kg</div>
            <hr>
            <span style="font-size:14px; color:#6b7280;">Required Bolts:</span>
            <div style="font-size:24px; font-weight:700; color:#1e40af;">{n_bolts} Nos.</div>
        </div>
        """, unsafe_allow_html=True)

        if h_req <= h_avail:
            st.success(f"✅ Geometry Pass: Space {h_req}mm < {h_avail}mm")
        else:
            st.error(f"❌ Geometry Fail: Space {h_req}mm > {h_avail}mm")

    with col2:
        # Drawing
        fig = go.Figure()
        fig.add_shape(type="rect", x0=-120, y0=-20, x1=-100, y1=h_mm+20, fillcolor="#475569")
        fig.add_shape(type="rect", x0=-100, y0=0, x1=150, y1=h_mm, line_color="RoyalBlue", fillcolor="rgba(65, 105, 225, 0.1)")
        start_y = (h_mm/2) - ((n_rows-1)*pitch)/2
        for r in range(n_rows):
            y = start_y + r*pitch
            for x in [-75, -45]:
                fig.add_trace(go.Scatter(x=[x], y=[y], mode='markers', marker=dict(size=12, color='#ef4444', line=dict(width=1, color='white'))))
        fig.update_layout(showlegend=False, height=300, margin=dict(l=0,r=0,t=0,b=0), xaxis_visible=False, yaxis_visible=False, plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)

    # --- DETAILED CALCULATION STEP-BY-STEP ---
    st.divider()
    st.subheader("📝 Detailed Calculation Steps")

    with st.expander("Step 1: Bolt Shear Strength (AISC 360)"):
        st.info(f"**Shear Capacity Check ({'LRFD' if is_lrfd else 'ASD'})**")
        if is_lrfd:
            st.latex(fr"\phi R_n = \phi \cdot F_{{nv}} \cdot A_b")
            st.latex(fr"0.75 \cdot {F_nv:,.0f} \cdot {b_area:.2f} = {v_shear_bolt:,.0f} \text{{ kg}}")
        else:
            st.latex(fr"R_n / \Omega = (F_{{nv}} \cdot A_b) / 2.0")
            st.latex(fr"({F_nv:,.0f} \cdot {b_area:.2f}) / 2.0 = {v_shear_bolt:,.0f} \text{{ kg}}")

    with st.expander("Step 2: Plate Bearing Strength (AISC 360)"):
        st.info(f"**Bearing on Beam Web ({tw_mm} mm)**")
        st.latex(fr"R_n = 2.4 \cdot d \cdot t_w \cdot F_u")
        if is_lrfd:
            st.latex(fr"\phi R_n = 0.75 \cdot (2.4 \cdot {dia_cm:.1f} \cdot {tw_cm:.2f} \cdot 4000)")
            st.latex(fr"= {v_bearing_bolt:,.0f} \text{{ kg}}")
        else:
            st.latex(fr"R_n / \Omega = (2.4 \cdot {dia_cm:.1f} \cdot {tw_cm:.2f} \cdot 4000) / 2.0")
            st.latex(fr"= {v_bearing_bolt:,.0f} \text{{ kg}}")

    with st.expander("Step 3: Governing Strength & Quantity"):
        st.write(f"Governing Strength per Bolt: **{min(v_shear_bolt, v_bearing_bolt):,.0f} kg**")
        if conn_type == "Beam-to-Beam":
            st.warning(f"Coping Reduction Applied: {reduction} (15% reduction)")
        st.latex(fr"n_{{required}} = \frac{{V_{{design}}}}{{V_{{bolt}} \cdot Red.}} = \frac{{{V_design:,.0f}}}{{{v_bolt_cap:,.0f} \cdot {reduction}}} = {req_bolt_calc:.2f}")
        st.write(f"Adopted Quantity: **{n_bolts} Nos.**")

    with st.expander("Step 4: Layout & Pitch Check"):
        st.latex(fr"S_{{pitch}} = 3.0 \cdot d = 3.0 \cdot {dia_mm} = {pitch:.0f} \text{{ mm}}")
        st.latex(fr"L_{{edge}} = 1.5 \cdot d = 1.5 \cdot {dia_mm} = {edge:.0f} \text{{ mm}}")
        st.latex(fr"H_{{required}} = (n_{{row}}-1) \cdot S + 2 \cdot L = ({n_rows}-1) \cdot {pitch} + 2 \cdot {edge} = {h_req:.0f} \text{{ mm}}")
        st.write(f"Available Web Height: **{h_avail:.0f} mm**")

    return n_bolts, v_final_cap
