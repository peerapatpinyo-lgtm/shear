# connection_design.py (V17 - Professional Engineering Detailed Calculation)
import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade):
    p = section_data
    h_mm, tw_mm, tf_mm = p['h'], p['tw'], p['tf']
    tw_cm = tw_mm / 10
    
    # 1. Properties & Parameters
    b_areas = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}
    Ab = b_areas.get(bolt_size, 3.14)
    d_bolt_mm = int(bolt_size[1:])
    d_bolt_cm = d_bolt_mm / 10
    d_hole_mm = d_bolt_mm + 2 # Standard Hole
    d_hole_cm = d_hole_mm / 10

    # Material: SS400
    Fy, Fu = 2450, 4000 
    
    # Bolt Stress (Fnv) - AISC Table J3.2 (Threads Included)
    bolt_map = {"A325 (High Strength)": 3795, "Grade 8.8 (Standard)": 3200, "A490 (Premium)": 4780}
    Fnv = bolt_map.get(bolt_grade, 3795)

    # 2. Safety Factors (AISC 360)
    phi_v = 0.75 if is_lrfd else 1.0
    omega_v = 1.0 if is_lrfd else 2.00
    phi_y = 1.00 if is_lrfd else 1.0  # สำหรับ Shear Yielding
    omega_y = 1.0 if is_lrfd else 1.5
    
    # 3. Preliminary Bolt Count
    # Rn = Fnv * Ab (Shear)
    # Rn = 2.4 * d * t * Fu (Bearing)
    rn_shear = Fnv * Ab
    rn_bearing = 2.4 * d_bolt_cm * tw_cm * Fu
    rn_nominal = min(rn_shear, rn_bearing)
    
    # Capacity per bolt based on method
    cap_per_bolt = (phi_v * rn_nominal) / omega_v
    reduction = 0.85 if conn_type == "Beam-to-Beam" else 1.0
    
    n_bolts = max(2, math.ceil(V_design / (cap_per_bolt * reduction)))
    if n_bolts % 2 != 0: n_bolts += 1
    n_rows = n_bolts // 2

    # 4. Geometry Layout
    s_pitch = 3.0 * d_bolt_mm
    l_edge = 1.5 * d_bolt_mm
    h_web = h_mm - 2*tf_mm
    
    # 5. Limit States Calculation (Detailed)
    # --- A: Bolt Shear ---
    Rn_bolt_shear = n_bolts * Fnv * Ab
    # --- B: Bearing & Tear-out ---
    Rn_bearing = n_bolts * (2.4 * d_bolt_cm * tw_cm * Fu)
    Lc = l_edge - (d_hole_mm/2) # Clear distance for tear-out
    Rn_tearout = n_bolts * (1.2 * (Lc/10) * tw_cm * Fu)
    Rn_bearing_final = min(Rn_bearing, Rn_tearout)
    
    # --- C: Block Shear (AISC J4.3) ---
    # Net Area Shear (Anv) & Net Area Tension (Ant)
    Anv = ( (n_rows-1)*s_pitch + l_edge - (n_rows-0.5)*d_hole_mm ) * tw_mm / 100 * 2
    Ant = ( (2 * l_edge) - 1.0 * d_hole_mm ) * tw_mm / 100 
    Rn_block = min(0.6 * Fu * Anv + 1.0 * Fu * Ant, 0.6 * Fy * Anv + 1.0 * Fu * Ant)

    # --- D: Web Shear Yielding ---
    Agv = (h_mm * tw_mm / 100)
    Rn_yield = 0.60 * Fy * Agv

    # Apply Factors to all
    cap_shear = (phi_v * Rn_bolt_shear) / omega_v
    cap_bearing = (phi_v * Rn_bearing_final) / omega_v
    cap_block = (phi_v * Rn_block) / omega_v
    cap_yield = (phi_y * Rn_yield) / omega_y

    # --- UI ---
    st.subheader(f"🔩 Detailed Connection Report ({method})")
    
    # Dashboard
    res_cols = st.columns(4)
    checks = [
        ("Bolt Shear", cap_shear, "J3.6"),
        ("Bearing/Tearout", cap_bearing, "J3.10"),
        ("Block Shear", cap_block, "J4.3"),
        ("Web Yielding", cap_yield, "G2.1")
    ]
    
    for i, (name, cap, code) in enumerate(checks):
        ratio = V_design / cap
        color = "#10b981" if ratio <= 1.0 else "#ef4444"
        res_cols[i].markdown(f"""
        <div style="border:1px solid {color}50; padding:10px; border-radius:8px; background:{color}05; text-align:center;">
            <small style="color:gray;">{code}</small><br><b>{name}</b><br>
            <span style="color:{color}; font-size:18px;">{cap:,.0f} kg</span><br>
            <small>Ratio: {ratio:.3f}</small>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Calculation Expander (The "Deep Dive")
    with st.expander("📖 รายการคำนวณอย่างละเอียด (Calculation Note)"):
        meth_txt = "LRFD (\\phi = 0.75)" if is_lrfd else "ASD (\\Omega = 2.00)"
        st.markdown(f"**Method:** {meth_txt} | **Steel:** SS400 | **Bolt:** {bolt_grade}")
        
        # 1. Bolt Shear
        st.markdown("### 1. Bolt Shear Strength (AISC J3.6)")
        st.latex(fr"R_n = F_{{nv}} A_b \cdot N = {Fnv:,.0f} \cdot {Ab:.2f} \cdot {n_bolts} = {Rn_bolt_shear:,.0f} \text{{ kg}}")
        if is_lrfd: st.latex(fr"\phi R_n = 0.75 \cdot {Rn_bolt_shear:,.0f} = {cap_shear:,.0f} \text{{ kg}}")
        else: st.latex(fr"R_n / \Omega = {Rn_bolt_shear:,.0f} / 2.00 = {cap_shear:,.0f} \text{{ kg}}")

        # 2. Bearing & Tearout
        st.markdown("### 2. Bearing & Tear-out on Web (AISC J3.10)")
        st.latex(fr"R_{{n1}} = 2.4 d t F_u = 2.4 \cdot {d_bolt_cm} \cdot {tw_cm} \cdot {Fu} \cdot {n_bolts} = {Rn_bearing:,.0f} \text{{ kg}}")
        st.latex(fr"R_{{n2}} = 1.2 L_c t F_u = 1.2 \cdot {Lc/10:.2f} \cdot {tw_cm} \cdot {Fu} \cdot {n_bolts} = {Rn_tearout:,.0f} \text{{ kg}}")
        st.write(f"Governing Nominal Strength ($R_n$): **{Rn_bearing_final:,.0f} kg**")

        # 3. Block Shear
        st.markdown("### 3. Block Shear Rupture (AISC J4.3)")
        st.latex(fr"A_{{nv}} = {Anv:.2f} \text{{ cm}}^2, \quad A_{{nt}} = {Ant:.2f} \text{{ cm}}^2")
        st.latex(fr"R_n = [0.6 F_u A_{{nv}} + U_{{bs}} F_u A_{{nt}}] \leq [0.6 F_y A_{{nv}} + U_{{bs}} F_u A_{{nt}}]")
        st.latex(fr"R_n = {Rn_block:,.0f} \text{{ kg}}")
        st.write(f"Design Capacity: **{cap_block:,.0f} kg**")

        # 4. Geometry Check
        st.markdown("### 4. Dimensional Requirements")
        st.write(f"- Standard Hole Diameter: {d_hole_mm} mm")
        st.write(f"- Minimum Pitch (3d): {3*d_bolt_mm} mm | **Used: {s_pitch} mm**")
        st.write(f"- Minimum Edge (1.5d): {1.5*d_bolt_mm} mm | **Used: {l_edge} mm**")

    return n_bolts, cap_per_bolt
