import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    # --- 1. DATA LINKAGE AUDIT ---
    p = section_data
    h_beam = float(p.get('h', 300))
    tw_beam_mm = float(p.get('tw', 8)) 
    Fy, Fu = 2450, 4000  # SS400 (kg/cm2)
    
    st.markdown(f"### ⚙️ Connection Design Logic: **{('LRFD' if is_lrfd else 'ASD')}**")
    
    # --- 2. INPUT PANEL ---
    c1, c2, c3 = st.columns(3)
    with c1:
        n_rows = st.number_input("จำนวนแถวน็อต (V)", 2, 12, 3)
        n_cols = st.number_input("จำนวนแถวน็อต (H)", 1, 2, 1)
        t_plate_mm = st.number_input("Plate Thickness (mm)", 6.0, 40.0, 10.0)
    with c2:
        s_v = st.number_input("Vertical Pitch (mm)", 50.0, 150.0, 75.0)
        s_h = st.number_input("Horizontal Pitch (mm)", 0.0, 150.0, 50.0) if n_cols > 1 else 0
        l_edge_v = st.number_input("Top/Bottom Edge (mm)", 30.0, 100.0, 40.0)
    with c3:
        e1_mm = st.number_input("Weld to Bolt Line (mm)", 40.0, 200.0, 60.0)
        l_side = st.number_input("Side Margin (mm)", 30.0, 100.0, 40.0)
        thread_type = st.radio("Thread Position", ["N", "X"], horizontal=True)

    # --- 3. PARAMETER DEFINITION (CRITICAL SEQUENCE) ---
    d_mm = int(bolt_size[1:])
    d_cm = d_mm / 10
    tw_cm = t_plate_mm / 10
    tw_beam_cm = tw_beam_mm / 10
    Ab = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}.get(bolt_size, 3.14)
    dh_cm = (d_mm + 2) / 10
    dh_eff_cm = dh_cm + 0.2
    
    n_total = n_rows * n_cols
    plate_h = (n_rows - 1) * s_v + (2 * l_edge_v)
    plate_w = e1_mm + (n_cols - 1) * s_h + l_side

    # --- 4. ASD vs LRFD SWITCH (DYNAMIC LABELS) ---
    if is_lrfd:
        phi, omega = 0.75, 1.00
        sym_cap = r"\phi R_n"
        method_text = "LRFD"
        factor_str = r"0.75 \times"
    else:
        phi, omega = 1.00, 2.00
        sym_cap = r"R_n / \Omega"
        method_text = "ASD"
        factor_str = r"R_n / 2.00"

    # --- 5. ECCENTRIC SHEAR ANALYSIS (ELASTIC METHOD) ---
    e_total_cm = (e1_mm + (n_cols-1)*s_h/2) / 10
    y_coords = [(r - (n_rows-1)/2) * (s_v/10) for r in range(n_rows)]
    x_coords = [(c - (n_cols-1)/2) * (s_h/10) for c in range(n_cols)]
    Ip = (sum([y**2 for y in y_coords]) * n_cols) + (sum([x**2 for x in x_coords]) * n_rows)
    
    V_dir = V_design / n_total
    M_ecc = V_design * e_total_cm
    V_ecc_x = (M_ecc * max([abs(y) for y in y_coords])) / Ip if Ip > 0 else 0
    V_ecc_y = (M_ecc * max([abs(x) for x in x_coords])) / Ip if Ip > 0 else 0
    V_res = math.sqrt((V_dir + V_ecc_y)**2 + V_ecc_x**2)

    # --- 6. CAPACITIES (LINKED TO INPUTS) ---
    bolt_map = {"Grade 8.8 (Standard)": {"N": 3200, "X": 4000}, "A325 (High Strength)": {"N": 3795, "X": 4780}}
    Fnv = bolt_map.get(bolt_grade, bolt_map["Grade 8.8 (Standard)"]).get(thread_type)
    m_shear = 2.0 if "Double" in conn_type else 1.0
    Rn_shear = n_total * Fnv * Ab * m_shear
    phiRn_shear = (phi * Rn_shear) / omega

    t_min_cm = min(tw_cm, tw_beam_cm)
    lc_edge = (l_edge_v/10) - (dh_cm/2)
    lc_inner = (s_v/10) - dh_cm
    Rn_bear = (n_cols * 2 * min(1.2*lc_edge*t_min_cm*Fu, 2.4*d_cm*t_min_cm*Fu)) + \
              (n_cols * (n_rows-2) * min(1.2*lc_inner*t_min_cm*Fu, 2.4*d_cm*t_min_cm*Fu))
    phiRn_bear = (phi * Rn_bear) / omega

    # --- 7. VISUAL DETAIL (DETAILED SKETCH) ---
    st.divider()
    st.subheader("🖼️ Detail Drawing (Scale Representation)")
    fig = go.Figure()
    # เสา
    fig.add_shape(type="rect", x0=-40, y0=-50, x1=0, y1=plate_h+50, fillcolor="#34495e", line_color="black")
    # คาน (เส้นประ)
    fig.add_shape(type="rect", x0=5, y0=(plate_h/2 - h_beam/2), x1=plate_w+50, y1=(plate_h/2 + h_beam/2), line=dict(color="gray", dash="dash"))
    # แผ่น Fin Plate
    fig.add_shape(type="rect", x0=0, y0=0, x1=plate_w, y1=plate_h, fillcolor="rgba(52, 152, 219, 0.3)", line_color="#2980b9", line_width=2)
    # น็อต
    for r in range(n_rows):
        for c in range(n_cols):
            fig.add_trace(go.Scatter(x=[e1_mm + c*s_h], y=[l_edge_v + r*s_v], mode='markers', marker=dict(size=12, color='#e74c3c')))
    
    fig.update_layout(height=500, plot_bgcolor='white', xaxis_visible=False, yaxis_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # --- 8. DETAILED CALCULATION SHEET (STRICT DYNAMIC) ---
    st.title(f"📄 Calculation Sheet ({method_text})")
    
    with st.expander("STEP 1: Load & Eccentricity Analysis", expanded=True):
        st.latex(fr"V_{{design}} = {V_design:,.0f} \text{{ kg}}, \quad e = {e_total_cm:.2f} \text{{ cm}}")
        st.latex(fr"V_{{resultant}} = \sqrt{{(V_{{dir}} + V_{{ecc,y}})^2 + V_{{ecc,x}}^2}} = {V_res:,.1f} \text{{ kg/bolt}}")
        

    with st.expander(f"STEP 2: Bolt Shear Check ({method_text})"):
        st.write(f"Bolt Grade: {bolt_grade} | Plane: {'Single' if m_shear==1 else 'Double'}")
        st.latex(fr"R_n = N \times F_{{nv}} \times A_b \times m = {Rn_shear:,.0f} \text{{ kg}}")
        # นี่คือจุดที่สูตรจะเปลี่ยนตามการกดปุ่มทันที
        st.latex(fr"{sym_cap} = {factor_str} {Rn_shear:,.0f} = {phiRn_shear:,.0f} \text{{ kg}}")
        st.metric("Ratio", f"{(V_res*n_total)/phiRn_shear:.2f}")
        

    with st.expander(f"STEP 3: Bearing & Tear-out Check ({method_text})"):
        st.write(f"t_min = {t_min_cm*10:.1f} mm (min of Plate and Beam Web)")
        st.latex(fr"R_n = \sum \min(1.2 L_c t F_u, 2.4 d t F_u) = {Rn_bear:,.0f} \text{{ kg}}")
        st.latex(fr"{sym_cap} = {factor_str} {Rn_bear:,.0f} = {phiRn_bear:,.0f} \text{{ kg}}")
        st.metric("Ratio", f"{V_design/phiRn_bear:.2f}")
        

    return n_total, phiRn_shear
