import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    # --- 1. INITIAL DATA & MATERIAL ---
    p = section_data
    h_beam = float(p.get('h', 300))
    tw_beam = float(p.get('tw', 8)) 
    Fy, Fu = 2450, 4000  # SS400 (kg/cm2)
    
    st.markdown(f"### ⚙️ Connection Setup ({'LRFD' if is_lrfd else 'ASD'})")
    
    # --- 2. INPUT LAYOUT ---
    c1, c2, c3 = st.columns(3)
    with c1:
        n_rows = st.number_input("จำนวนน็อต (แนวดิ่ง)", 2, 12, 3)
        n_cols = st.number_input("จำนวนน็อต (แนวนอน)", 1, 2, 1)
        t_plate_mm = st.number_input("ความหนาแผ่นประกับ (mm)", 6.0, 40.0, 10.0, 1.0)
    with c2:
        s_v = st.number_input("Vertical Pitch (mm)", 50.0, 150.0, 75.0, 5.0)
        s_h = st.number_input("Horizontal Pitch (mm)", 0.0, 150.0, 50.0, 5.0) if n_cols > 1 else 0
        l_edge_v = st.number_input("Vertical Edge (mm)", 30.0, 100.0, 40.0, 5.0)
    with c3:
        e1_mm = st.number_input("รอยเชื่อมถึงน็อตแถวแรก (mm)", 40.0, 200.0, 60.0, 5.0)
        l_side = st.number_input("Side Margin (mm)", 30.0, 100.0, 40.0, 5.0)
        thread_type = st.radio("Thread Position", ["N", "X"], horizontal=True)

    # --- 3. GEOMETRY & CONSTANTS (FIXED DECLARED) ---
    d_mm = int(bolt_size[1:])
    d_cm = d_mm / 10
    tw_cm = t_plate_mm / 10
    tw_beam_cm = tw_beam / 10
    Ab = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}.get(bolt_size, 3.14)
    dh_cm = (d_mm + 2) / 10
    
    n_total = n_rows * n_cols
    plate_h = (n_rows - 1) * s_v + (2 * l_edge_v)
    plate_w = e1_mm + (n_cols - 1) * s_h + l_side

    # --- 4. DYNAMIC METHOD LINKAGE (CRITICAL FIX) ---
    if is_lrfd:
        phi_val, omega_val = 0.75, 1.00
        m_tag = "LRFD"
        formula_prefix = r"\phi R_n ="
        method_eqn = rf"0.75 \times R_n"
    else:
        phi_val, omega_val = 1.00, 2.00
        m_tag = "ASD"
        formula_prefix = r"R_n / \Omega ="
        method_eqn = rf"R_n / 2.00"

    # --- 5. FORCE ANALYSIS (ECCENTRICITY) ---
    e_total_cm = (e1_mm + (n_cols-1)*s_h/2) / 10
    y_coords = [(r - (n_rows-1)/2) * (s_v/10) for r in range(n_rows)]
    x_coords = [(c - (n_cols-1)/2) * (s_h/10) for c in range(n_cols)]
    Ip = (sum([y**2 for y in y_coords]) * n_cols) + (sum([x**2 for x in x_coords]) * n_rows)
    
    V_dir = V_design / n_total
    V_ecc_x = (V_design * e_total_cm * max([abs(y) for y in y_coords])) / Ip if Ip > 0 else 0
    V_ecc_y = (V_design * e_total_cm * max([abs(x) for x in x_coords])) / Ip if Ip > 0 else 0
    V_res = math.sqrt((V_dir + V_ecc_y)**2 + V_ecc_x**2)

    # --- 6. CAPACITY CALCULATIONS ---
    # Bolt Shear
    bolt_map = {"Grade 8.8 (Standard)": {"N": 3200, "X": 4000}, "A325 (High Strength)": {"N": 3795, "X": 4780}}
    Fnv = bolt_map.get(bolt_grade, bolt_map["Grade 8.8 (Standard)"]).get(thread_type)
    m_shear = 2.0 if "Double" in conn_type else 1.0
    Rn_shear = n_total * Fnv * Ab * m_shear
    Cap_shear = (phi_val * Rn_shear) / omega_val

    # Bearing
    t_min_cm = min(tw_cm, tw_beam_cm)
    lc_edge = (l_edge_v/10) - (dh_cm/2)
    lc_inner = (s_v/10) - dh_cm
    Rn_bear = (n_cols * 2 * min(1.2*lc_edge*t_min_cm*Fu, 2.4*d_cm*t_min_cm*Fu)) + \
              (n_cols * (n_rows-2) * min(1.2*lc_inner*t_min_cm*Fu, 2.4*d_cm*t_min_cm*Fu))
    Cap_bear = (phi_val * Rn_bear) / omega_val

    # --- 7. DRAWING ---
    st.divider()
    st.subheader(f"🎨 Structural Layout Detail ({m_tag})")
    fig = go.Figure()
    fig.add_shape(type="rect", x0=-40, y0=-50, x1=0, y1=plate_h+50, fillcolor="#2c3e50")
    fig.add_annotation(x=-20, y=plate_h/2, text="COLUMN FACE", textangle=-90, font=dict(color="white"))
    fig.add_shape(type="rect", x0=0, y0=0, x1=plate_w, y1=plate_h, fillcolor="rgba(52, 152, 219, 0.2)", line_color="#2980b9")
    for r in range(n_rows):
        for c in range(n_cols):
            bx, by = e1_mm + c*s_h, l_edge_v + r*s_v
            fig.add_trace(go.Scatter(x=[bx], y=[by], mode='markers', marker=dict(size=14, color='#e74c3c')))
    fig.update_layout(height=500, plot_bgcolor='white', xaxis_visible=False, yaxis_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # --- 8. DYNAMIC CALCULATION REPORT ---
    st.title(f"📄 Detailed Calculation Report ({m_tag})")
    
    with st.expander("1. Analysis of Applied Force (Demand)", expanded=True):
        st.write(f"V_design = {V_design:,.0f} kg, Eccentricity (e) = {e_total_cm:.2f} cm")
        st.latex(fr"V_{{resultant}} = {V_res:,.1f} \text{{ kg/bolt}}")

    with st.expander(f"2. Bolt Shear Strength ({m_tag})"):
        st.write(f"เกรดน็อต: {bolt_grade}, หน้าเฉือน: {m_shear}")
        st.latex(fr"R_n = N \times F_{{nv}} \times A_b \times m = {Rn_shear:,.0f} \text{{ kg}}")
        st.latex(fr"{formula_prefix} {method_eqn} = {Cap_shear:,.0f} \text{{ kg}}")
        st.write(f"**Ratio:** {(V_res * n_total) / Cap_shear:.2f}")

    with st.expander(f"3. Bearing Strength ({m_tag})"):
        st.write(f"วิเคราะห์ที่ความหนาวิกฤต (t_min): {t_min_cm*10:.1f} mm")
        st.latex(fr"R_n = {Rn_bear:,.0f} \text{{ kg}}")
        st.latex(fr"{formula_prefix} {method_eqn} = {Cap_bear:,.0f} \text{{ kg}}")
        st.write(f"**Ratio:** {V_design / Cap_bear:.2f}")

    return n_total, Cap_shear
