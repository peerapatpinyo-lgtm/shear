import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    # --- 1. INITIALIZATION & DATA RETRIEVAL ---
    p = section_data
    h_beam = float(p.get('h', 300))
    tw_beam = float(p.get('tw', 8))
    Fy, Fu = 2450, 4000  # SS400 (kg/cm2)
    
    st.markdown("### 🏗️ Connection Layout & Material Specification")
    
    # --- 2. USER INPUTS (Customizable Geometry) ---
    c1, c2, c3 = st.columns(3)
    with c1:
        n_rows = st.number_input("Bolt Rows (Vertical)", 2, 12, 3)
        n_cols = st.number_input("Bolt Columns (Horizontal)", 1, 2, 1)
        t_plate_mm = st.number_input("Plate Thickness (t, mm)", 6.0, 40.0, 10.0, 1.0)
    with c2:
        s_v = st.number_input("Vertical Pitch (mm)", 50.0, 150.0, 75.0, 5.0)
        s_h = st.number_input("Horizontal Pitch (mm)", 0.0, 150.0, 50.0, 5.0) if n_cols > 1 else 0
        l_edge_v = st.number_input("Top/Bottom Edge (mm)", 30.0, 100.0, 40.0, 5.0)
    with c3:
        e1_mm = st.number_input("Weld to 1st Bolt Line (mm)", 40.0, 200.0, 60.0, 5.0)
        l_side = st.number_input("Side Margin (mm)", 30.0, 100.0, 40.0, 5.0)
        thread_type = st.radio("Thread Position", ["N", "X"], horizontal=True)

    # --- 3. GEOMETRY & HOLE CALCULATION (CRITICAL VARIABLES) ---
    d_mm = int(bolt_size[1:])
    d_cm = d_mm / 10 # <--- FIX: DECLARED EARLY
    Ab = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}.get(bolt_size, 3.14)
    dh_cm = (d_mm + 2) / 10
    dh_eff_cm = dh_cm + 0.2 # AISC B4.3b (+2mm for Net Area)
    tw_cm = t_plate_mm / 10

    n_total = n_rows * n_cols
    plate_h = (n_rows - 1) * s_v + (2 * l_edge_v)
    plate_w = e1_mm + (n_cols - 1) * s_h + l_side

    # --- 4. FORCE ANALYSIS (ECCENTRICITY) ---
    e_total_cm = (e1_mm + (n_cols-1)*s_h/2) / 10
    y_coords = [(r - (n_rows-1)/2) * (s_v/10) for r in range(n_rows)]
    x_coords = [(c - (n_cols-1)/2) * (s_h/10) for c in range(n_cols)]
    Ip = (sum([y**2 for y in y_coords]) * n_cols) + (sum([x**2 for x in x_coords]) * n_rows)
    
    V_direct = V_design / n_total
    V_ecc_x = (V_design * e_total_cm * max([abs(y) for y in y_coords])) / Ip if Ip > 0 else 0
    V_ecc_y = (V_design * e_total_cm * max([abs(x) for x in x_coords])) / Ip if Ip > 0 else 0
    V_res = math.sqrt((V_direct + V_ecc_y)**2 + V_ecc_x**2)

    # --- 5. CAPACITY DESIGN (AISC 360-16) ---
    phi, omega = (0.75, 1.00) if is_lrfd else (1.00, 2.00)
    sym = r"\phi R_n" if is_lrfd else r"R_n / \Omega"
    
    # 5.1 Bolt Shear (J3.6)
    bolt_map = {"Grade 8.8 (Standard)": {"N": 3200, "X": 4000}, "A325 (High Strength)": {"N": 3795, "X": 4780}}
    Fnv = bolt_map.get(bolt_grade, bolt_map["Grade 8.8 (Standard)"]).get(thread_type)
    Cap_shear = (phi * n_total * Fnv * Ab) / omega

    # 5.2 Bearing & Tear-out (J3.10)
    lc_edge = (l_edge_v/10) - (dh_cm/2)
    lc_inner = (s_v/10) - dh_cm
    Rn_bear = (n_cols * 2 * min(1.2*lc_edge*tw_cm*Fu, 2.4*d_cm*tw_cm*Fu)) + \
              (n_cols * (n_rows-2) * min(1.2*lc_inner*tw_cm*Fu, 2.4*d_cm*tw_cm*Fu))
    Cap_bear = (phi * Rn_bear) / omega

    # 5.3 Block Shear (J4.3)
    Anv = (plate_h/10 - l_edge_v/10 - (n_rows-0.5)*dh_eff_cm) * tw_cm
    Ant = (plate_w/10 - e1_mm/10 - (n_cols-0.5)*dh_eff_cm) * tw_cm
    Rn_bs = min(0.6*Fu*Anv + 1.0*Fu*Ant, 0.6*Fy*(Anv) + 1.0*Fu*Ant)
    Cap_bs = (phi * Rn_bs) / omega

    # --- 6. VISUALIZATION (STRUCTURAL DETAIL) ---
    st.divider()
    st.subheader("🎨 Structural Detail Drawing")
    fig = go.Figure()
    # Drawing Beam Outline & Plate... (Omitted for brevity, but same high-detail logic as V37)
    # [Insert Plotly Drawing Code from V37 here]
    
    # --- 7. DETAILED REPORT ---
    st.title(f"📄 Engineering Calculation Sheet ({'LRFD' if is_lrfd else 'ASD'})")
    
    with st.expander("📍 Force Analysis & Source of V", expanded=True):
        st.write(f"แรงเฉือนรวมที่จุดต่อ (V): **{V_design:,.0f} kg**")
        st.latex(fr"V_{{direct/bolt}} = \frac{{{V_design}}}{{{n_total}}} = {V_direct:,.1f} \text{{ kg}}")
        st.latex(fr"V_{{resultant/bolt}} = {V_res:,.1f} \text{{ kg}} \quad \text{{(รวมผลจาก Eccentricity } e={e_total_cm:.1f} \text{{ cm)}}")

    with st.expander("📝 Bolt Shear Verification (AISC J3.6)"):
        st.latex(fr"F_{{nv}} = {Fnv} \text{{ kg/cm}}^2, \quad A_b = {Ab} \text{{ cm}}^2")
        st.latex(fr"R_n = F_{{nv}} A_b N = {n_total*Fnv*Ab:,.0f} \text{{ kg}}")
        st.latex(fr"{sym} = {Cap_shear:,.0f} \text{{ kg}}")
        st.write(f"**Demand Ratio:** {(V_res * n_total) / Cap_shear:.2f}")

    with st.expander("📝 Bearing & Tear-out Verification (AISC J3.10)"):
        st.latex(fr"R_n = \sum \min(1.2 L_c t F_u, 2.4 d t F_u) = {Rn_bear:,.0f} \text{{ kg}}")
        st.latex(fr"{sym} = {Cap_bear:,.0f} \text{{ kg}}")
        st.write(f"**Demand Ratio:** {V_design / Cap_bear:.2f}")
        

    with st.expander("📝 Block Shear Verification (AISC J4.3)"):
        st.latex(fr"A_{{nv}} = {Anv:.2f} \text{{ cm}}^2, \quad A_{{nt}} = {Ant:.2f} \text{{ cm}}^2")
        st.latex(fr"R_n = \min(0.6 F_u A_{{nv}} + U_{{bs}} F_u A_{{nt}}, 0.6 F_y A_{{gv}} + U_{{bs}} F_u A_{{nt}}) = {Rn_bs:,.0f} \text{{ kg}}")
        st.latex(fr"{sym} = {Cap_bs:,.0f} \text{{ kg}}")
        st.write(f"**Demand Ratio:** {V_design / Cap_bs:.2f}")
        

    return n_total, Cap_shear
