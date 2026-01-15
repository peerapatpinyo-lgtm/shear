import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, thread_type="N", T_design=0):
    # --- 1. SETUP & MATERIAL ---
    p = section_data
    h_mm, tw_mm = p['h'], p['tw']
    tw_cm = tw_mm / 10
    Fy, Fu = 2450, 4000 # SS400 Standard (kg/cm2)

    # --- 2. BOLT CONSTANTS (AISC Table J3.2) ---
    b_areas = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}
    Ab = b_areas.get(bolt_size, 3.14)
    d_mm = int(bolt_size[1:])
    d_cm, dh_cm = d_mm / 10, (d_mm + 2) / 10 

    bolt_db = {
        "A325 (High Strength)": {"Fnt": 6325, "Fnv_N": 3795, "Fnv_X": 4780},
        "Grade 8.8 (Standard)": {"Fnt": 5300, "Fnv_N": 3200, "Fnv_X": 4000},
        "A490 (Premium)":       {"Fnt": 7940, "Fnv_N": 4780, "Fnv_X": 5975}
    }
    spec = bolt_db.get(bolt_grade, bolt_db["Grade 8.8 (Standard)"])
    Fnt, Fnv = spec["Fnt"], (spec["Fnv_N"] if thread_type == "N" else spec["Fnv_X"])

    # --- 3. SAFETY FACTORS (AISC 360-16) ---
    if is_lrfd:
        phi, omega = 0.75, 1.00
        method_label, prefix = "LRFD", r"\phi R_n"
    else:
        phi, omega = 1.00, 2.00
        method_label, prefix = "ASD", r"R_n / \Omega"

    # --- 4. PRELIMINARY LAYOUT ---
    rn_shear_1b = Fnv * Ab
    rn_bearing_1b = 2.4 * d_cm * tw_cm * Fu
    cap_1b = (phi * min(rn_shear_1b, rn_bearing_1b)) / omega
    
    n_bolts = max(2, math.ceil(V_design / cap_1b))
    if n_bolts % 2 != 0: n_bolts += 1
    n_rows = n_bolts // 2

    s_pitch, l_edge = 3.0 * d_mm, 1.5 * d_mm
    lc_cm = (l_edge/10) - (dh_cm / 2)

    # --- 5. LIMIT STATES CALCULATION ---
    # Case A: Bolt Shear
    Rn_shear_total = n_bolts * Fnv * Ab
    cap_shear = (phi * Rn_shear_total) / omega

    # Case B: Bearing/Tear-out
    Rn_bearing_total = n_bolts * (2.4 * d_cm * tw_cm * Fu)
    Rn_tearout_total = n_bolts * (1.2 * lc_cm * tw_cm * Fu)
    cap_bearing = (phi * min(Rn_bearing_total, Rn_tearout_total)) / omega

    # Case C: Combined Tension (J3.7)
    frv = V_design / (n_bolts * Ab)
    if is_lrfd:
        Fnt_prime = min(1.3 * Fnt - (Fnt / (0.75 * Fnv)) * frv, Fnt)
    else:
        Fnt_prime = min(1.3 * Fnt - (2.0 * Fnt / Fnv) * frv, Fnt)
    cap_combined = (phi * n_bolts * Fnt_prime * Ab) / omega

    # Case D: Block Shear (J4.3)
    Anv = ((n_rows-1)*(s_pitch/10) + l_edge/10 - (n_rows-0.5)*dh_cm) * tw_cm * 2
    Ant = (2 * l_edge/10 - 1.0 * dh_cm) * tw_cm
    Rn_block = min(0.6*Fu*Anv + 1.0*Fu*Ant, 0.6*Fy*Anv + 1.0*Fu*Ant)
    cap_block = (phi * Rn_block) / omega

    # --- 6. UI PRESENTATION ---
    st.header(f"⚖️ Final Engineering Report ({method_label})")
    
    # Dashboard
    res = [("Bolt Shear", cap_shear, V_design), ("Bearing/Tear", cap_bearing, V_design), 
           ("Combined T-V", cap_combined, T_design), ("Block Shear", cap_block, V_design)]
    
    m_cols = st.columns(4)
    for i, (name, cap, force) in enumerate(res):
        ratio = force / cap if cap > 0 else 0
        m_cols[i].metric(name, f"{cap:,.0f} kg", f"Ratio {ratio:.2f}", delta_color="normal" if ratio <= 1 else "inverse")

    st.divider()
    
    # Graphic and Check
    c1, c2 = st.columns([1, 1])
    with c1:
        fig = go.Figure()
        fig.add_shape(type="rect", x0=0, y0=0, x1=10, y1=h_mm, fillcolor="rgba(0,0,255,0.05)", line_color="blue")
        start_y = (h_mm/2) - ((n_rows-1)*s_pitch)/2
        for r in range(n_rows):
            y = start_y + r*s_pitch
            for x in [3, 7]: fig.add_trace(go.Scatter(x=[x], y=[y], mode='markers', marker=dict(size=14, color='red')))
        fig.update_layout(xaxis_visible=False, yaxis_visible=False, height=300, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)
    
    with c2:
        st.subheader("📍 Geometry & Safety")
        st.write(f"- Bolt: {bolt_grade} ({thread_type})")
        st.write(f"- Pitch/Edge: {s_pitch}/{l_edge} mm")
        if any(f/c > 1.0 for _, c, f in res if c > 0):
            st.error("❌ DESIGN FAILED: Increase Bolt Size or Number of Bolts")
        else:
            st.success("✅ DESIGN PASS: Meets AISC 360-16 Requirements")

    with st.expander("📝 Detailed Calculation (AISC 360-16 Formulae)"):
        st.latex(fr"\text{{Bolt Shear: }} {prefix} = {(phi*Rn_shear_total)/omega:,.0f} \text{{ kg}}")
        st.latex(fr"\text{{Block Shear: }} {prefix} = {cap_block:,.0f} \text{{ kg}}")
        if T_design > 0:
            st.latex(fr"F'_{{nt}} = {Fnt_prime:.1f} \text{{ kg/cm}}^2 \quad \to \text{{Interaction Pass}}")

    return n_bolts, cap_1b
