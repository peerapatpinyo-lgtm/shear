import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    # --- 1. INITIAL DATA & CONSTANTS ---
    p = section_data
    h_beam = float(p.get('h', 300))
    Fy, Fu = 2450, 4000  # SS400 (kg/cm2)
    
    # --- 2. INPUT UI: SPECIFICATION ---
    st.markdown("### 🛠️ Detailed Specification")
    c1, c2, c3 = st.columns(3)
    with c1:
        thread_type = st.radio("Thread Position", ["N (Included)", "X (Excluded)"], horizontal=True)[0]
    with c2:
        t_plate_mm = st.number_input("Fin Plate Thickness (mm)", 6.0, 50.0, 10.0, 1.0)
    with c3:
        ecc_mm = st.number_input("Eccentricity (e, mm)", 40.0, 200.0, 60.0, 5.0)

    # --- 3. BOLT & HOLE GEOMETRY ---
    b_areas = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}
    Ab = b_areas.get(bolt_size, 3.14)
    d_mm = int(bolt_size[1:])
    d_cm = d_mm / 10
    dh_cm = (d_mm + 2) / 10 # Standard Hole
    dh_eff_cm = dh_cm + (2/10) # AISC B4.3b (+2mm for Net Area)

    # --- 4. SAFETY FACTORS ---
    if is_lrfd:
        phi, omega = 0.75, 1.00
        phi_y, omega_y = 1.00, 1.00
        m_name, sym = "LRFD", r"\phi R_n"
    else:
        phi, omega = 1.00, 2.00
        phi_y, omega_y = 1.00, 1.50
        m_name, sym = "ASD", r"R_n / \Omega"

    # --- 5. NOMINAL STRENGTHS (Table J3.2) ---
    bolt_db = {
        "A325 (High Strength)": {"Fnv_N": 3795, "Fnv_X": 4780, "Fnt": 6325},
        "Grade 8.8 (Standard)": {"Fnv_N": 3200, "Fnv_X": 4000, "Fnt": 5300},
        "A490 (Premium)":       {"Fnv_N": 4780, "Fnv_X": 5975, "Fnt": 7940}
    }
    spec = bolt_db.get(bolt_grade, bolt_db["Grade 8.8 (Standard)"])
    Fnv = spec["Fnv_N"] if thread_type == "N" else spec["Fnv_X"]
    Fnt = spec["Fnt"]

    # --- 6. PRELIMINARY LAYOUT & ECCENTRICITY ---
    cap_1b = (phi * Fnv * Ab) / omega
    n_bolts = max(2, math.ceil(V_design / cap_1b))
    if n_bolts % 2 != 0: n_bolts += 1
    n_rows = n_bolts // 2
    
    s_pitch = 3.0 * d_mm
    l_edge = 1.5 * d_mm
    plate_h = (n_rows - 1) * s_pitch + (2 * l_edge)
    plate_w = ecc_mm + l_edge # ระยะจากแนวเชื่อมถึงขอบแผ่น
    
    # Eccentricity Check (Elastic Method)
    e_cm = ecc_mm / 10
    Ip = 2 * sum([((r - (n_rows-1)/2) * (s_pitch/10))**2 for r in range(n_rows)])
    V_direct = V_design / n_bolts
    V_ecc = (V_design * e_cm * ((n_rows-1)*s_pitch/20)) / Ip if Ip > 0 else 0
    V_resultant = math.sqrt(V_direct**2 + V_ecc**2)

    # --- 7. LIMIT STATES CALCULATION ---
    # Case 1: Bolt Shear (J3.6)
    Rn_shear = n_bolts * Fnv * Ab
    Cap_shear = (phi * Rn_shear) / omega
    Ratio_shear = (V_resultant * n_bolts) / Cap_shear

    # Case 2: Bearing & Tear-out (J3.10)
    tw_cm = t_plate_mm / 10
    lc_edge = (l_edge/10) - (dh_cm / 2)
    lc_inner = (s_pitch/10) - dh_cm
    Rn_bear_1 = 1.2 * lc_edge * tw_cm * Fu
    Rn_bear_2 = 2.4 * d_cm * tw_cm * Fu
    Rn_bearing_total = (2 * min(Rn_bear_1, Rn_bear_2)) + ((n_bolts-2) * min(1.2*lc_inner*tw_cm*Fu, Rn_bear_2))
    Cap_bearing = (phi * Rn_bearing_total) / omega
    Ratio_bearing = V_design / Cap_bearing

    # Case 3: Block Shear (J4.3)
    Anv = ( (n_rows-1)*(s_pitch/10) + l_edge/10 - (n_rows-0.5)*dh_eff_cm ) * tw_cm * 2
    Ant = ( 2 * (l_edge/10) - 1.0 * dh_eff_cm ) * tw_cm
    Rn_block = min(0.6*Fu*Anv + 1.0*Fu*Ant, 0.6*Fy*(Anv) + 1.0*Fu*Ant)
    Cap_block = (phi * Rn_block) / omega
    Ratio_block = V_design / Cap_block

    # --- 8. UI RENDERING ---
    st.title(f"📄 Full Connection Report ({m_name})")
    
    # 8.1 Sketch & Plate Dimension
    c_left, c_right = st.columns([1.2, 1])
    with c_left:
        fig = go.Figure()
        # Fin Plate Body
        fig.add_shape(type="rect", x0=0, y0=0, x1=plate_w, y1=plate_h, fillcolor="rgba(200,200,200,0.2)", line_color="black")
        # Bolt Drawing
        start_y = l_edge
        for r in range(n_rows):
            for x_pos in [ecc_mm]: # Bolt line
                fig.add_trace(go.Scatter(x=[x_pos], y=[start_y + r*s_pitch], mode='markers+text', 
                                         text=[f"B{r+1}"], textposition="top center",
                                         marker=dict(size=14, color='red', line=dict(width=2, color='white'))))
        # Dimension Lines
        fig.add_annotation(x=ecc_mm/2, y=-15, text=f"e={ecc_mm}", showarrow=False)
        fig.add_annotation(x=plate_w + 15, y=plate_h/2, text=f"H={plate_h}", textangle=-90, showarrow=False)
        fig.update_layout(xaxis_title="Width (mm)", yaxis_title="Height (mm)", height=500, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with c_right:
        st.success(f"**Final Plate Size: {t_plate_mm} x {plate_w:.0f} x {plate_h:.0f} mm**")
        st.markdown("### 📊 Capacity Summary")
        st.write(f"1. **Bolt Shear:** {Cap_shear:,.0f} kg (Ratio: {Ratio_shear:.2f})")
        st.write(f"2. **Bearing:** {Cap_bearing:,.0f} kg (Ratio: {Ratio_bearing:.2f})")
        st.write(f"3. **Block Shear:** {Cap_block:,.0f} kg (Ratio: {Ratio_block:.2f})")
        if any(r > 1 for r in [Ratio_shear, Ratio_bearing, Ratio_block]):
            st.error("⚠️ DESIGN FAILED")
        else:
            st.balloons()

    # 8.2 Detailed Step-by-Step
    st.markdown("---")
    st.subheader("📝 รายการคำนวณละเอียด (Detailed Engineering Note)")
    
    with st.expander("STEP 1: Bolt Group & Eccentricity (AISC J3.6)", expanded=True):
        st.latex(fr"V_{{direct}} = \frac{{{V_design}}}{{{n_bolts}}} = {V_direct:,.1f} \text{{ kg}}")
        st.latex(fr"M_{{ecc}} = V \cdot e = {V_design} \cdot {e_cm} = {V_design*e_cm:,.0f} \text{{ kg-cm}}")
        st.latex(fr"V_{{resultant}} = \sqrt{{V_{{dir}}^2 + V_{{ecc}}^2}} = {V_resultant:,.1f} \text{{ kg/bolt}}")
        st.latex(fr"\text{{Ratio}} = \frac{{{V_resultant} \times {n_bolts}}}{{{Cap_shear:,.0f}}} = {Ratio_shear:.2f}")

    with st.expander("STEP 2: Bearing & Tear-out (J3.10)"):
        st.write(f"Clear Distance Edge ($L_{{c1}}$) = {lc_edge:.2f} cm")
        st.latex(fr"R_{{n,edge}} = \min(1.2 L_{{c1}} t F_u, 2.4 d t F_u) = {min(Rn_bear_1, Rn_bear_2):,.0f} \text{{ kg/bolt}}")
        st.latex(fr"{sym} = {Cap_bearing:,.0f} \text{{ kg}}")
        st.latex(fr"\text{{Ratio}} = \frac{{{V_design}}}{{{Cap_bearing:,.0f}}} = {Ratio_bearing:.2f}")

    with st.expander("STEP 3: Block Shear Rupture (J4.3)"):
        st.latex(fr"A_{{nv}} = {Anv:.2f} \text{{ cm}}^2, \quad A_{{nt}} = {Ant:.2f} \text{{ cm}}^2")
        st.latex(fr"R_n = \min(0.6 F_u A_{{nv}} + U_{{bs}} F_u A_{{nt}}, 0.6 F_y A_{{nv}} + U_{{bs}} F_u A_{{nt}})")
        st.latex(fr"{sym} = {Cap_block:,.0f} \text{{ kg}}")
        st.latex(fr"\text{{Ratio}} = \frac{{{V_design}}}{{{Cap_block:,.0f}}} = {Ratio_block:.2f}")

    return n_bolts, Cap_shear
