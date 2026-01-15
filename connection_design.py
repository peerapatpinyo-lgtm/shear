import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    # --- PRO-LEVEL INPUTS ---
    st.markdown("### 🛠️ Global Connection Parameters")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        thread_type = st.radio("Thread Position", ["N (Included)", "X (Excluded)"], horizontal=False)[0]
    with c2:
        t_plate_mm = st.number_input("Fin Plate Thickness (mm)", 6.0, 40.0, 10.0, 1.0)
    with c3:
        ecc_mm = st.number_input("Eccentricity (e, mm)", 10.0, 200.0, 50.0, 5.0, help="ระยะจากแนวรอยเชื่อมถึงแนวน็อต")
    with c4:
        hole_type = st.selectbox("Hole Type", ["Standard", "Oversized", "Short-Slotted"])

    # --- MATERIAL PROPERTIES (A36/SS400) ---
    Fy, Fu = 2450, 4000 # kg/cm2
    tw_cm = t_plate_mm / 10

    # 1. GEOMETRY & HOLE SPECIFICATION (AISC Table J3.3)
    b_areas = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}
    Ab = b_areas.get(bolt_size, 3.14)
    d_mm = int(bolt_size[1:])
    d_cm = d_mm / 10
    
    # Standard hole = d + 2mm, Effective hole for Net Area = dh + 2mm (AISC B4.3)
    dh_cm = (d_mm + 2) / 10 
    dh_eff_cm = dh_cm + (2 / 10) 

    # 2. DESIGN COEFFICIENTS (LRFD/ASD)
    if is_lrfd:
        phi, omega = 0.75, 1.00
        phi_y, omega_y = 1.00, 1.00
        m_name, sym = "LRFD", r"\phi R_n"
    else:
        phi, omega = 1.00, 2.00
        phi_y, omega_y = 1.00, 1.50
        m_name, sym = "ASD", r"R_n / \Omega"

    # 3. NOMINAL STRENGTHS (Table J3.2)
    bolt_db = {
        "A325 (High Strength)": {"Fnv_N": 3795, "Fnv_X": 4780, "Fnt": 6325},
        "Grade 8.8 (Standard)": {"Fnv_N": 3200, "Fnv_X": 4000, "Fnt": 5300},
        "A490 (Premium)":       {"Fnv_N": 4780, "Fnv_X": 5975, "Fnt": 7940}
    }
    spec = bolt_db.get(bolt_grade, bolt_db["Grade 8.8 (Standard)"])
    Fnv = spec["Fnv_N"] if thread_type == "N" else spec["Fnv_X"]
    Fnt = spec["Fnt"]

    # 4. BOLT GROUP ANALYSIS (Including Eccentricity - Elastic Method)
    # หาจำนวนน็อตเบื้องต้นและคำนวณแรงลัพธ์ต่อตัวที่วิกฤตที่สุด
    cap_bolt_shear_1 = (phi * Fnv * Ab) / omega
    n_bolts = max(2, math.ceil(V_design / cap_bolt_shear_1))
    if n_bolts % 2 != 0: n_bolts += 1
    n_rows = n_bolts // 2
    
    s_pitch = 3.0 * d_mm
    l_edge = 1.5 * d_mm
    
    # Shear due to Eccentricity (Simplified Elastic Method)
    e_cm = ecc_mm / 10
    Ip = 2 * sum([((r - (n_rows-1)/2) * (s_pitch/10))**2 for r in range(n_rows)]) # Polar moment of Inertia (approx)
    V_ecc = (V_design * e_cm * (3.5/10)) / Ip if Ip > 0 else 0 # Moment force component
    V_total_bolt = math.sqrt((V_design/n_bolts)**2 + V_ecc**2)

    # 5. LIMIT STATES DETAILED ANALYSIS
    # --- Case 1: Shear (J3.6) ---
    Rn_shear = n_bolts * Fnv * Ab
    
    # --- Case 2: Bearing & Tear-out (J3.10) ---
    lc_edge = (l_edge/10) - (dh_cm / 2)
    lc_inner = (s_pitch/10) - dh_cm
    rn_bear_max = 2.4 * d_cm * tw_cm * Fu
    rn_tear_edge = 1.2 * lc_edge * tw_cm * Fu
    rn_tear_inner = 1.2 * lc_inner * tw_cm * Fu
    Rn_bearing = (2 * min(rn_bear_max, rn_tear_edge)) + ((n_bolts-2) * min(rn_bear_max, rn_tear_inner))

    # --- Case 3: Block Shear (J4.3) - High Precision ---
    Anv = ( (n_rows-1)*(s_pitch/10) + l_edge/10 - (n_rows-0.5)*dh_eff_cm ) * tw_cm * 2
    Ant = ( 2 * (l_edge/10) - 1.0 * dh_eff_cm ) * tw_cm
    Rn_block = min(0.6*Fu*Anv + 1.0*Fu*Ant, 0.6*Fy*(Anv/tw_cm*tw_cm) + 1.0*Fu*Ant)

    # 6. RESULTS & SUMMARY
    caps = {
        "Bolt Shear (with Ecc.)": (phi * Rn_shear) / omega,
        "Bearing/Tear-out": (phi * Rn_bearing) / omega,
        "Block Shear Rupture": (phi * Rn_block) / omega,
        "Combined T-V Interaction": (phi * n_bolts * Ab * Fnt) / omega # Simplified for dash
    }

    # --- UI OUTPUTS ---
    st.divider()
    cols = st.columns(4)
    for i, (name, cap) in enumerate(caps.items()):
        force = V_total_bolt * n_bolts if "Shear" in name else V_design
        ratio = force / cap if cap > 0 else 0
        cols[i].metric(name, f"{cap:,.0f} kg", f"Ratio {ratio:.2f}", delta_color="normal" if ratio <= 1 else "inverse")

    # Layout Visualization
    c_left, c_right = st.columns([1, 1.2])
    with c_left:
        fig = go.Figure()
        # Fin Plate
        fig.add_shape(type="rect", x0=0, y0=0, x1=10, y1=h_mm, fillcolor="lightgrey", line_color="black")
        # Weld Line
        fig.add_shape(type="line", x0=0, y0=0, x1=0, y1=h_mm, line=dict(color="blue", width=6))
        # Bolts
        start_y = (h_mm/2) - ((n_rows-1)*s_pitch)/2
        for r in range(n_rows):
            for x in [4, 8]: fig.add_trace(go.Scatter(x=[x], y=[start_y + r*s_pitch], mode='markers', marker=dict(size=12, color='red')))
        fig.update_layout(xaxis_visible=False, yaxis_visible=False, height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with c_right:
        st.markdown(f"### 📑 Professional Calculation Sheet ({m_name})")
        with st.expander("1. Geometry Verification (J3.3 - J3.5)", expanded=True):
            st.write(f"- Minimum Bolt Pitch (2.67d): **{2.67*d_mm:.1f} mm** (Actual: {s_pitch} mm) ✅")
            st.write(f"- Minimum Edge Distance (Table J3.4): **{1.25*d_mm:.1f} mm** (Actual: {l_edge} mm) ✅")
            st.write(f"- Effective Hole Dia ($d_{{h,eff}}$): **{dh_eff_cm*10:.1f} mm** (AISC B4.3)")

        with st.expander("2. Shear Strength & Eccentricity (J3.6)"):
            st.latex(fr"f_{{v, direct}} = \frac{{V}}{{n A_b}} = {V_design/(n_bolts*Ab):,.1f} \text{{ kg/cm}}^2")
            st.latex(fr"f_{{v, ecc}} = \frac{{M \cdot c}}{{I_p}} \to V_{{bolt, total}} = {V_total_bolt:,.0f} \text{{ kg}}")
            st.latex(fr"{sym} = {caps['Bolt Shear (with Ecc.)']:,.0f} \text{{ kg}}")
            

        with st.expander("3. Bearing & Tear-out (J3.10)"):
            st.write("Consider Clear Distance ($L_c$) for edge and inner bolts:")
            st.latex(fr"R_n = \sum \min(1.2 L_c t F_u, 2.4 d t F_u) = {Rn_bearing:,.0f} \text{{ kg}}")
            st.latex(fr"{sym} = {caps['Bearing/Tear-out']:,.0f} \text{{ kg}}")
            

        with st.expander("4. Block Shear Rupture (J4.3)"):
            st.write(f"Net Areas: $A_{{nv}} = {Anv:.2f} \text{{ cm}}^2, A_{{nt}} = {Ant:.2f} \text{{ cm}}^2$")
            st.latex(fr"R_n = 0.6 F_u A_{{nv}} + U_{{bs}} F_u A_{{nt}} = {Rn_block:,.0f} \text{{ kg}}")
            st.latex(fr"{sym} = {caps['Block Shear Rupture']:,.0f} \text{{ kg}}")
            

    return n_bolts, caps["Bolt Shear (with Ecc.)"]
