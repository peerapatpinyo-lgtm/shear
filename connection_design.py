# connection_design.py (V18 - The Ultimate Structural Manual Edition)
import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade):
    p = section_data
    h_mm, tw_mm, tf_mm = p['h'], p['tw'], p['tf']
    tw_cm, h_cm = tw_mm / 10, h_mm / 10
    
    # 1. ข้อมูล Bolt & Material (AISC Table J3.2)
    b_areas = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}
    Ab = b_areas.get(bolt_size, 3.14)
    d = int(bolt_size[1:]) / 10  # d in cm
    dh = (int(bolt_size[1:]) + 2) / 10 # hole diameter in cm

    # Steel SS400: Fy = 2450, Fu = 4000 kg/cm2
    Fy, Fu = 2450, 4000
    
    # Fnv (Nominal Shear Stress) จาก AISC Table J3.2
    bolt_map = {"A325 (High Strength)": 3795, "Grade 8.8 (Standard)": 3200, "A490 (Premium)": 4780}
    Fnv = bolt_map.get(bolt_grade, 3795)

    # 2. Safety Factors แยกตาม Method (AISC 360-16)
    if is_lrfd:
        phi_bolt, phi_plate, phi_yield = 0.75, 0.75, 1.00
        omega_bolt, omega_plate, omega_yield = 1.00, 1.00, 1.00
        method_title = "LRFD (Limit State Design)"
    else:
        phi_bolt, phi_plate, phi_yield = 1.00, 1.00, 1.00
        omega_bolt, omega_plate, omega_yield = 2.00, 2.00, 1.50
        method_title = "ASD (Allowable Strength Design)"

    # 3. คำนวณเบื้องต้นเพื่อหาจำนวนน็อต
    # Bolt Shear Strength per bolt
    rn_shear = Fnv * Ab
    # Bearing Strength (Governing by 2.4dtFu)
    rn_bearing = 2.4 * d * tw_cm * Fu
    
    # Nominal Strength per bolt (k)
    rn_nominal = min(rn_shear, rn_bearing)
    bolt_capacity = (phi_bolt * rn_nominal) / omega_bolt
    
    # จำนวนน็อต
    n_bolts = max(2, math.ceil(V_design / bolt_capacity))
    if n_bolts % 2 != 0: n_bolts += 1
    n_rows = n_bolts // 2

    # Layout: ระยะห่างมาตรฐาน
    s = 3.0 * (d * 10)     # Pitch
    le = 1.5 * (d * 10)    # Edge distance
    lc = le - (dh * 10 / 2) # Clear distance for tear-out

    # 4. Limit States Calculation (Full Detailed)
    
    # CASE 1: Bolt Shear (J3.6)
    Rn_shear = n_bolts * Fnv * Ab
    
    # CASE 2: Bearing & Tear-out (J3.10)
    # Bearing: 2.4dtFu | Tear-out: 1.2Lc*t*Fu
    Rn_bearing = n_bolts * (2.4 * d * tw_cm * Fu)
    Rn_tearout = n_bolts * (1.2 * (lc/10) * tw_cm * Fu)
    Rn_bearing_gov = min(Rn_bearing, Rn_tearout)

    # CASE 3: Block Shear Rupture (J4.3)
    # Ant: Net Tension Area, Anv: Net Shear Area
    Ant = (2 * le/10 - 1.0 * dh) * tw_cm
    Anv = ((n_rows-1)*s/10 + le/10 - (n_rows-0.5)*dh) * tw_cm * 2
    # Rn = 0.6FuAnv + Ubs*Fu*Ant <= 0.6FyAnv + Ubs*Fu*Ant
    term1 = 0.6 * Fu * Anv + 1.0 * Fu * Ant
    term2 = 0.6 * Fy * Anv + 1.0 * Fu * Ant
    Rn_block = min(term1, term2)

    # CASE 4: Web Shear Yielding (G2.1)
    Rn_yield = 0.6 * Fy * (h_cm * tw_cm)

    # Apply Method Factors
    cap_shear = (phi_bolt * Rn_shear) / omega_bolt
    cap_bearing = (phi_plate * Rn_bearing_gov) / omega_plate
    cap_block = (phi_plate * Rn_block) / omega_plate
    cap_yield = (phi_yield * Rn_yield) / omega_yield

    # --- UI Rendering ---
    st.markdown(f"## 🏗️ {method_title} Detailed Report")
    
    # Dashboard แสดงผลลัพธ์
    c1, c2, c3, c4 = st.columns(4)
    for col, (name, cap) in zip([c1,c2,c3,c4], [("Bolt Shear", cap_shear), ("Bearing", cap_bearing), ("Block Shear", cap_block), ("Web Yield", cap_yield)]):
        ratio = V_design / cap
        color = "green" if ratio <= 1.0 else "red"
        col.metric(name, f"{cap:,.0f} kg", f"Ratio: {ratio:.2f}", delta_color="inverse" if ratio > 1 else "normal")

    st.divider()

    # Calculation Note แยก LRFD/ASD
    st.subheader("📝 รายการคำนวณแบบแยกสมการ (AISC 360-16)")
    
    with st.expander("STEP 1: Bolt Shear Rupture (Chapter J3.6)"):
        st.write(f"Bolt Size: {bolt_size} | Area ($A_b$): {Ab} cm² | $F_{{nv}}$: {Fnv} kg/cm²")
        st.latex(fr"R_n = F_{{nv}} \cdot A_b \cdot N = {Fnv} \cdot {Ab} \cdot {n_bolts} = {Rn_shear:,.0f} \text{{ kg}}")
        if is_lrfd:
            st.latex(fr"\phi R_n = 0.75 \cdot {Rn_shear:,.0f} = {cap_shear:,.0f} \text{{ kg}} \quad (\text{{Pass}} \text{{ if }} \geq {V_design})")
        else:
            st.latex(fr"R_n / \Omega = {Rn_shear:,.0f} / 2.00 = {cap_shear:,.0f} \text{{ kg}} \quad (\text{{Pass}} \text{{ if }} \geq {V_design})")

    with st.expander("STEP 2: Bearing & Tear-out (Chapter J3.10)"):
        st.write(f"Thickness ($t_w$): {tw_mm} mm | Edge distance ($L_e$): {le} mm")
        st.latex(fr"R_{{n(bearing)}} = 2.4 \cdot d \cdot t \cdot F_u = 2.4 \cdot {d} \cdot {tw_cm} \cdot {Fu} \cdot {n_bolts} = {Rn_bearing:,.0f} \text{{ kg}}")
        st.latex(fr"R_{{n(tear-out)}} = 1.2 \cdot L_c \cdot t \cdot F_u = 1.2 \cdot {lc/10:.2f} \cdot {tw_cm} \cdot {Fu} \cdot {n_bolts} = {Rn_tearout:,.0f} \text{{ kg}}")
        governing_rn = min(Rn_bearing, Rn_tearout)
        st.write(f"Governing $R_n = {governing_rn:,.0f} \text{{ kg}}$")
        if is_lrfd: st.latex(fr"\phi R_n = 0.75 \cdot {governing_rn:,.0f} = {cap_bearing:,.0f} \text{{ kg}}")
        else: st.latex(fr"R_n / \Omega = {governing_rn:,.0f} / 2.00 = {cap_bearing:,.0f} \text{{ kg}}")

    with st.expander("STEP 3: Block Shear Rupture (Chapter J4.3)"):
        
        st.write(f"Net Shear Area ($A_{{nv}}$): {Anv:.2f} cm² | Net Tension Area ($A_{{nt}}$): {Ant:.2f} cm²")
        st.latex(fr"R_n = \min(0.6 F_u A_{{nv}} + U_{{bs}} F_u A_{{nt}}, 0.6 F_y A_{{nv}} + U_{{bs}} F_u A_{{nt}})")
        st.latex(fr"R_n = {Rn_block:,.0f} \text{{ kg}}")
        if is_lrfd: st.latex(fr"\phi R_n = 0.75 \cdot {Rn_block:,.0f} = {cap_block:,.0f} \text{{ kg}}")
        else: st.latex(fr"R_n / \Omega = {Rn_block:,.0f} / 2.00 = {cap_block:,.0f} \text{{ kg}}")

    with st.expander("STEP 4: Spacing & Edge Distance Check"):
        
        st.write(f"- **Min Spacing (2.67d):** {2.67*d*10:.1f} mm | **Used:** {s} mm ✅")
        st.write(f"- **Min Edge Distance:** จากตาราง J3.4 คือประมาณ 1.25d-1.5d | **Used:** {le} mm ✅")

    # ส่วน Drawing
    st.divider()
    fig = go.Figure()
    # Support & Beam Drawing (Simplified)
    fig.add_shape(type="rect", x0=-10, y0=0, x1=20, y1=h_mm, fillcolor="rgba(0,0,255,0.1)", line_color="blue")
    start_y = (h_mm/2) - ((n_rows-1)*s)/2
    for r in range(n_rows):
        y = start_y + r*s
        for x in [2, 7]: # สองแถว
            fig.add_trace(go.Scatter(x=[x], y=[y], mode='markers', marker=dict(size=10, color='red')))
    fig.update_layout(title="Connection Layout Sketch", height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    return n_bolts, bolt_capacity
