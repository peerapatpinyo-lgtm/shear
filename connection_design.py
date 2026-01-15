import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    # --- UI INPUTS: SPECIFICATION ---
    st.subheader("🛠️ Connection Specifications")
    c1, c2, c3 = st.columns(3)
    with c1:
        thread_type = st.radio("Thread Condition", ["N", "X"], horizontal=True, help="N: Included, X: Excluded")
    with c2:
        t_plate_mm = st.number_input("Plate Thickness (mm)", min_value=6.0, max_value=50.0, value=10.0, step=1.0)
    with c3:
        bolt_grade_label = st.write(f"Grade: **{bolt_grade}**")

    # --- MATERIAL & CONSTANTS ---
    p = section_data
    h_mm = p['h']
    tw_cm = t_plate_mm / 10  # ใช้ความหนาแผ่นที่เลือกมาคำนวณ
    Fy, Fu = 2450, 4000      # SS400 (kg/cm2)

    # 1. BOLT & HOLE GEOMETRY (AISC Table J3.3)
    b_areas = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}
    Ab = b_areas.get(bolt_size, 3.14)
    d_mm = int(bolt_size[1:])
    d_cm = d_mm / 10
    dh_cm = (d_mm + 2) / 10 # Standard Hole (d+2mm)

    # 2. NOMINAL STRESSES (AISC Table J3.2)
    bolt_map = {
        "A325 (High Strength)": {"Fnv_N": 3795, "Fnv_X": 4780, "Fnt": 6325},
        "Grade 8.8 (Standard)": {"Fnv_N": 3200, "Fnv_X": 4000, "Fnt": 5300},
        "A490 (Premium)":       {"Fnv_N": 4780, "Fnv_X": 5975, "Fnt": 7940}
    }
    spec = bolt_map.get(bolt_grade, bolt_map["Grade 8.8 (Standard)"])
    Fnv = spec["Fnv_N"] if thread_type == "N" else spec["Fnv_X"]
    Fnt = spec["Fnt"]

    # 3. DESIGN PHILOSOPHY
    if is_lrfd:
        phi, omega = 0.75, 1.00
        phi_y, omega_y = 1.00, 1.00
        m_name, sym = "LRFD", r"\phi R_n = 0.75 \times"
    else:
        phi, omega = 1.00, 2.00
        phi_y, omega_y = 1.00, 1.50
        m_name, sym = "ASD", r"R_n / \Omega = R_n / 2.00 ="

    # 4. CAPACITY CALCULATIONS
    # Initial Bolt Selection
    cap_bolt_shear_1 = (phi * Fnv * Ab) / omega
    n_bolts = max(2, math.ceil(V_design / cap_bolt_shear_1))
    if n_bolts % 2 != 0: n_bolts += 1
    n_rows = n_bolts // 2

    # Spacing & Distances
    s_pitch = 3.0 * d_mm
    l_edge = 1.5 * d_mm
    lc_edge_cm = (l_edge/10) - (dh_cm / 2) # Clear distance for edge bolt
    lc_inner_cm = (s_pitch/10) - dh_cm      # Clear distance for inner bolts

    # --- LIMIT STATES ---
    # Case 1: Bolt Shear (J3.6)
    Rn_shear = n_bolts * Fnv * Ab
    
    # Case 2: Bearing & Tear-out (J3.10)
    # Rn = 1.2 * Lc * t * Fu <= 2.4 * d * t * Fu
    rn_tear_edge = 1.2 * lc_edge_cm * tw_cm * Fu
    rn_tear_inner = 1.2 * lc_inner_cm * tw_cm * Fu
    rn_bearing_max = 2.4 * d_cm * tw_cm * Fu
    
    # รวมกำลัง Bearing ของน็อตทุกตัว (สมมติ 2 ตัวเป็น Edge, ที่เหลือเป็น Inner)
    Rn_bearing_total = (2 * min(rn_tear_edge, rn_bearing_max)) + ((n_bolts - 2) * min(rn_tear_inner, rn_bearing_max))

    # Case 3: Block Shear (J4.3)
    Agv = ( (n_rows-1)*s_pitch + l_edge ) / 10 * tw_cm * 2 # Gross area shear
    Anv = ( (n_rows-1)*(s_pitch/10) + l_edge/10 - (n_rows-0.5)*dh_cm ) * tw_cm * 2 # Net area shear
    Ant = ( 2 * (l_edge/10) - 1.0 * dh_cm ) * tw_cm # Net area tension (2 lines)
    Rn_block = min(0.6*Fu*Anv + 1.0*Fu*Ant, 0.6*Fy*Agv + 1.0*Fu*Ant)

    # Case 4: Combined Force (J3.7)
    frv = V_design / (n_bolts * Ab)
    if is_lrfd:
        Fnt_prime = min(1.3 * Fnt - (Fnt / (0.75 * Fnv)) * frv, Fnt)
    else:
        Fnt_prime = min(1.3 * Fnt - (2.0 * Fnt / Fnv) * frv, Fnt)
    Rn_combined = n_bolts * Fnt_prime * Ab

    # 5. SUMMARY DICT
    caps = {
        "Bolt Shear": (phi * Rn_shear) / omega,
        "Bearing/Tear-out": (phi * Rn_bearing_total) / omega,
        "Block Shear": (phi * Rn_block) / omega,
        "Combined T-V": (phi * Rn_combined) / omega
    }

    # --- UI RENDERING ---
    st.divider()
    m_cols = st.columns(len(caps))
    for i, (name, val) in enumerate(caps.items()):
        force = V_design if name != "Combined T-V" else T_design
        ratio = force / val if val > 0 else 0
        m_cols[i].metric(name, f"{val:,.0f} kg", f"Ratio {ratio:.2f}", delta_color="normal" if ratio <= 1 else "inverse")

    # Graphic & Calculations
    c_left, c_right = st.columns([1, 1.2])
    with c_left:
        fig = go.Figure()
        fig.add_shape(type="rect", x0=0, y0=0, x1=10, y1=h_mm, fillcolor="rgba(30, 41, 59, 0.05)", line_color="#1e293b")
        start_y = (h_mm/2) - ((n_rows-1)*s_pitch)/2
        for r in range(n_rows):
            y = start_y + r*s_pitch
            for x in [3, 7]: fig.add_trace(go.Scatter(x=[x], y=[y], mode='markers', marker=dict(size=15, color='#ef4444')))
        fig.update_layout(xaxis_visible=False, yaxis_visible=False, height=400, margin=dict(l=10,r=10,t=10,b=10), title=f"Fin Plate: {t_plate_mm} mm")
        st.plotly_chart(fig, use_container_width=True)

    with c_right:
        st.markdown(f"### 📝 Detailed Calculation ({m_name})")
        
        with st.expander("1. Bolt Strength (Shear & Combined)", expanded=True):
            st.latex(fr"F_{{nv}} = {Fnv}, \quad F_{{nt}} = {Fnt} \text{{ kg/cm}}^2")
            st.latex(fr"R_n = N_b A_b F_{{nv}} = {Rn_shear:,.0f} \text{{ kg}}")
            st.latex(fr"{sym} {Rn_shear:,.0f} = {caps['Bolt Shear']:,.0f} \text{{ kg}}")
            if T_design > 0:
                st.write("**Combined Tension & Shear (J3.7):**")
                st.latex(fr"f_{{rv}} = {frv:.1f} \text{{ kg/cm}}^2 \to F'_{{nt}} = {Fnt_prime:.1f} \text{{ kg/cm}}^2")
                st.latex(fr"{sym} (N_b A_b F'_{{nt}}) = {caps['Combined T-V']:,.0f} \text{{ kg}}")
                

        with st.expander("2. Bearing & Tear-out (J3.10)"):
            st.write(f"Clear distances: $L_{{c,edge}}$ = {lc_edge_cm:.2f} cm, $L_{{c,inner}}$ = {lc_inner_cm:.2f} cm")
            st.latex(fr"R_n = \sum \min(1.2 L_c t F_u, 2.4 d t F_u)")
            st.latex(fr"R_n = {Rn_bearing_total:,.0f} \text{{ kg}}")
            st.latex(fr"{sym} {Rn_bearing_total:,.0f} = {caps['Bearing/Tear-out']:,.0f} \text{{ kg}}")
            

        with st.expander("3. Block Shear Rupture (J4.3)"):
            st.write(f"Areas: $A_{{nv}}$ = {Anv:.2f} cm², $A_{{nt}}$ = {Ant:.2f} cm²")
            st.latex(fr"R_n = [0.6 F_u A_{{nv}} + U_{{bs}} F_u A_{{nt}}] \leq [0.6 F_y A_{{gv}} + U_{{bs}} F_u A_{{nt}}]")
            st.latex(fr"R_n = {Rn_block:,.0f} \text{{ kg}}")
            st.latex(fr"{sym} {Rn_block:,.0f} = {caps['Block Shear']:,.0f} \text{{ kg}}")
            

    return n_bolts, caps["Bolt Shear"]
