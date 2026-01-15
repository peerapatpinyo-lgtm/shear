import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    # --- 1. GLOBAL VARIABLE INITIALIZATION ---
    p = section_data
    h_mm = float(p.get('h', 300))  # ป้องกัน Error หากไม่มีค่า h
    tw_mm = float(p.get('tw', 10))
    Fy, Fu = 2450, 4000  # SS400 Material (kg/cm2)
    
    # --- 2. INPUT UI & SPECIFICATIONS ---
    st.markdown("### 🛠️ Global Connection Parameters")
    c1, c2, c3 = st.columns(3)
    with c1:
        thread_type = st.radio("Thread Position", ["N (Included)", "X (Excluded)"], horizontal=True)[0]
    with c2:
        t_plate_mm = st.number_input("Fin Plate Thickness (mm)", 6.0, 50.0, float(tw_mm), 1.0)
    with c3:
        ecc_mm = st.number_input("Eccentricity (e, mm)", 0.0, 200.0, 50.0, 5.0, help="ระยะจากแนวรอยเชื่อมถึงแนวน็อต")

    # --- 3. GEOMETRY & HOLE CALCULATION ---
    tw_cm = t_plate_mm / 10
    b_areas = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}
    Ab = b_areas.get(bolt_size, 3.14)
    d_mm = int(bolt_size[1:])
    d_cm = d_mm / 10
    dh_cm = (d_mm + 2) / 10 # รูเจาะมาตรฐาน
    dh_eff_cm = dh_cm + (2/10) # Effective hole สำหรับ Net Area (AISC B4.3b)

    # --- 4. DESIGN COEFFICIENTS (LRFD/ASD) ---
    if is_lrfd:
        phi, omega = 0.75, 1.00
        m_name, sym = "LRFD", r"\phi R_n"
    else:
        phi, omega = 1.00, 2.00
        m_name, sym = "ASD", r"R_n / \Omega"

    # --- 5. NOMINAL STRESSES (Table J3.2) ---
    bolt_db = {
        "A325 (High Strength)": {"Fnv_N": 3795, "Fnv_X": 4780, "Fnt": 6325},
        "Grade 8.8 (Standard)": {"Fnv_N": 3200, "Fnv_X": 4000, "Fnt": 5300},
        "A490 (Premium)":       {"Fnv_N": 4780, "Fnv_X": 5975, "Fnt": 7940}
    }
    spec = bolt_db.get(bolt_grade, bolt_db["Grade 8.8 (Standard)"])
    Fnv = spec["Fnv_N"] if thread_type == "N" else spec["Fnv_X"]
    Fnt = spec["Fnt"]

    # --- 6. BOLT GROUP & ECCENTRICITY ANALYSIS ---
    cap_bolt_shear_1 = (phi * Fnv * Ab) / omega
    n_bolts = max(2, math.ceil(V_design / cap_bolt_shear_1))
    if n_bolts % 2 != 0: n_bolts += 1
    n_rows = n_bolts // 2
    
    s_pitch = 3.0 * d_mm
    l_edge = 1.5 * d_mm
    
    # Elastic Method for Eccentricity (J3.6)
    e_cm = ecc_mm / 10
    # Polar Moment of Inertia of Bolt Group
    Ip = 2 * sum([((r - (n_rows-1)/2) * (s_pitch/10))**2 for r in range(n_rows)])
    V_ecc = (V_design * e_cm * ((n_rows-1)*s_pitch/20)) / Ip if Ip > 0 else 0
    V_total_bolt = math.sqrt((V_design/n_bolts)**2 + V_ecc**2)

    # --- 7. LIMIT STATE CALCULATIONS ---
    # Case 1: Bolt Shear (J3.6)
    Rn_shear_total = n_bolts * Fnv * Ab
    
    # Case 2: Bearing & Tear-out (J3.10)
    lc_edge = (l_edge/10) - (dh_cm / 2)
    lc_inner = (s_pitch/10) - dh_cm
    Rn_bearing = (2 * min(2.4*d_cm*tw_cm*Fu, 1.2*lc_edge*tw_cm*Fu)) + \
                 ((n_bolts-2) * min(2.4*d_cm*tw_cm*Fu, 1.2*lc_inner*tw_cm*Fu))

    # Case 3: Block Shear (J4.3)
    Anv = ( (n_rows-1)*(s_pitch/10) + l_edge/10 - (n_rows-0.5)*dh_eff_cm ) * tw_cm * 2
    Ant = ( 2 * (l_edge/10) - 1.0 * dh_eff_cm ) * tw_cm
    Rn_block = min(0.6*Fu*Anv + 1.0*Fu*Ant, 0.6*Fy*(Anv) + 1.0*Fu*Ant)

    # --- 8. RESULTS SUMMARY ---
    caps = {
        "Bolt Shear (w/ Ecc)": (phi * Rn_shear_total) / omega,
        "Bearing/Tear-out": (phi * Rn_bearing) / omega,
        "Block Shear Rupture": (phi * Rn_block) / omega
    }

    st.divider()
    m_cols = st.columns(3)
    for i, (name, cap) in enumerate(caps.items()):
        force = V_total_bolt * n_bolts if "Shear" in name else V_design
        ratio = force / cap if cap > 0 else 0
        m_cols[i].metric(name, f"{cap:,.0f} kg", f"Ratio {ratio:.2f}", 
                         delta_color="normal" if ratio <= 1.0 else "inverse")

    # --- 9. VISUALIZATION & DETAIL ---
    c_left, c_right = st.columns([1, 1.2])
    with c_left:
        fig = go.Figure()
        fig.add_shape(type="rect", x0=0, y0=0, x1=10, y1=h_mm, fillcolor="rgba(100,100,100,0.1)", line_color="black")
        start_y = (h_mm/2) - ((n_rows-1)*s_pitch)/2
        for r in range(n_rows):
            for x in [3, 7]:
                fig.add_trace(go.Scatter(x=[x], y=[start_y + r*s_pitch], mode='markers', 
                                         marker=dict(size=14, color='red', line=dict(width=2, color='white'))))
        fig.update_layout(xaxis_visible=False, yaxis_visible=False, height=400, showlegend=False, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)

    with c_right:
        st.markdown(f"### 📑 Calculation Detail ({m_name})")
        with st.expander("1. Geometry & Eccentricity", expanded=True):
            st.write(f"- Min Pitch (2.67d): {2.67*d_mm:.1f} mm")
            st.write(f"- Eccentric Shear ($V_{{ecc}}$): {V_ecc:,.1f} kg/bolt")
            st.write(f"- Resultant Force ($V_{{bolt}}$): **{V_total_bolt:,.1f} kg**")
            

        with st.expander("2. Bearing & Tear-out (J3.10)"):
            st.latex(fr"R_n = \sum \min(1.2 L_c t F_u, 2.4 d t F_u) = {Rn_bearing:,.0f} \text{{ kg}}")
            st.latex(fr"{sym} = {caps['Bearing/Tear-out']:,.0f} \text{{ kg}}")
            

        with st.expander("3. Block Shear (J4.3)"):
            st.latex(fr"A_{{nv}} = {Anv:.2f} \text{{ cm}}^2, A_{{nt}} = {Ant:.2f} \text{{ cm}}^2")
            st.latex(fr"R_n = 0.6 F_u A_{{nv}} + U_{{bs}} F_u A_{{nt}} = {Rn_block:,.0f} \text{{ kg}}")
            st.latex(fr"{sym} = {caps['Block Shear Rupture']:,.0f} \text{{ kg}}")
            

    return n_bolts, caps["Bolt Shear (w/ Ecc)"]
