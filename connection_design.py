import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, thread_type="N", T_design=0):
    p = section_data
    h_mm, tw_mm, tf_mm = p['h'], p['tw'], p['tf']
    tw_cm = tw_mm / 10
    Fy, Fu = 2450, 4000 # SS400 (kg/cm2)

    # 1. BOLT DATA & NOMINAL STRESS
    b_areas = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}
    Ab = b_areas.get(bolt_size, 3.14)
    d_mm = int(bolt_size[1:])
    d_cm, dh_cm = d_mm / 10, (d_mm + 2) / 10 

    bolt_db = {
        "A325 (High Strength)": {"Fnt": 6325, "Fnv_N": 3795, "Fnv_X": 4780},
        "Grade 8.8 (Standard)": {"Fnt": 5300, "Fnv_N": 3200, "Fnv_X": 4000},
        "A490 (Premium)":       {"Fnt": 7940, "Fnv_N": 4780, "Fnv_X": 5975}
    }
    spec = bolt_db.get(bolt_grade)
    Fnt = spec["Fnt"]
    Fnv = spec["Fnv_N"] if thread_type == "N" else spec["Fnv_X"]

    # 2. DESIGN PHILOSOPHY SEPARATION
    if is_lrfd:
        phi, omega = 0.75, 1.00
        phi_y, omega_y = 1.00, 1.00
        method_label = "LRFD"
        prefix = r"\phi R_n"
    else:
        phi, omega = 1.00, 2.00
        phi_y, omega_y = 1.00, 1.50
        method_label = "ASD"
        prefix = r"R_n / \Omega"

    # 3. CAPACITY CALCULATION
    rn_shear_1b = Fnv * Ab
    rn_bearing_1b = 2.4 * d_cm * tw_cm * Fu
    limit_1b = min(rn_shear_1b, rn_bearing_1b)
    cap_1b = (phi * limit_1b) / omega
    
    n_bolts = max(2, math.ceil(V_design / cap_1b))
    if n_bolts % 2 != 0: n_bolts += 1
    n_rows = n_bolts // 2

    # 4. GEOMETRY & LIMIT STATES
    s_pitch = 3.0 * d_mm
    l_edge = 1.5 * d_mm
    lc_cm = (l_edge/10) - (dh_cm / 2)

    # Combined Tension (J3.7)
    frv = V_design / (n_bolts * Ab)
    if is_lrfd:
        Fnt_prime = min(1.3 * Fnt - (Fnt / (0.75 * Fnv)) * frv, Fnt)
    else:
        Fnt_prime = min(1.3 * Fnt - (2.0 * Fnt / Fnv) * frv, Fnt)
    cap_combined = (phi * n_bolts * Fnt_prime * Ab) / omega

    # Block Shear (J4.3)
    Anv = ((n_rows-1)*(s_pitch/10) + l_edge/10 - (n_rows-0.5)*dh_cm) * tw_cm * 2
    Ant = (2 * l_edge/10 - 1.0 * dh_cm) * tw_cm
    Rn_block = min(0.6*Fu*Anv + 1.0*Fu*Ant, 0.6*Fy*Anv + 1.0*Fu*Ant)
    
    # --- DEFINING ALL CAPACITIES ---
    cap_shear_total = (phi * n_bolts * rn_shear_1b) / omega
    cap_bearing_total = (phi * n_bolts * min(rn_bearing_1b, 1.2 * lc_cm * tw_cm * Fu)) / omega
    cap_block = (phi * Rn_block) / omega  # แก้ไข Error: นิยามตัวแปรให้ครบถ้วน
    cap_yield = (phi_y * 0.6 * Fy * (h_mm * tw_mm / 100)) / omega_y

    # --- UI RENDERING ---
    st.header(f"⚖️ {method_label} Analysis Report (AISC 360-16)")
    
    cols = st.columns(4)
    res_list = [
        ("Bolt Shear", cap_shear_total, V_design),
        ("Bearing/Tear", cap_bearing_total, V_design),
        ("Combined T-V", cap_combined, T_design),
        ("Block Shear", cap_block, V_design)
    ]
    for i, (name, cap, force) in enumerate(res_list):
        ratio = force / cap if cap > 0 else 0
        cols[i].metric(name, f"{cap:,.0f} kg", f"Ratio {ratio:.2f}", delta_color="normal" if ratio <= 1 else "inverse")

    st.divider()
    c1, c2 = st.columns([1.2, 1])
    with c1:
        # Plotly Sketch
        fig = go.Figure()
        fig.add_shape(type="rect", x0=0, y0=0, x1=10, y1=h_mm, fillcolor="rgba(0,0,255,0.05)", line_color="blue")
        start_y = (h_mm/2) - ((n_rows-1)*s_pitch)/2
        for r in range(n_rows):
            y = start_y + r*s_pitch
            for x in [3, 7]: fig.add_trace(go.Scatter(x=[x], y=[y], mode='markers', marker=dict(size=14, color='red', line=dict(width=2, color='white'))))
        fig.update_layout(xaxis_visible=False, yaxis_visible=False, height=350, margin=dict(l=0,r=0,t=10,b=10), title="Bolt Pattern Layout")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("### 📏 Layout Verification")
        st.write(f"- **Pitch (s):** {s_pitch} mm (Min: {2.67*d_mm:.1f})")
        st.write(f"- **Edge (le):** {l_edge} mm (Min: AISC Table J3.4)")
        st.write(f"- **Thread Type:** {thread_type} ($F_{{nv}} = {Fnv}$ kg/cm²)")
        if any(f/c > 1 for _, c, f in res_list if c > 0):
            st.error("⚠️ Design Capacity Exceeded")
        else:
            st.success("✅ Structural Pass")

    # 5. DETAILED CALCULATION NOTES
    with st.expander("📖 รายการคำนวณละเอียด (Detailed Step-by-Step)", expanded=True):
        st.markdown(f"#### 1. Bolt Shear Strength (J3.6)")
        st.latex(fr"R_n = F_{{nv}} A_b N_b = {Fnv} \cdot {Ab} \cdot {n_bolts} = {n_bolts*rn_shear_1b:,.0f} \text{{ kg}}")
        if is_lrfd:
            st.latex(fr"\phi R_n = 0.75 \times {n_bolts*rn_shear_1b:,.0f} = {cap_shear_total:,.0f} \text{{ kg}}")
        else:
            st.latex(fr"R_n / \Omega = {n_bolts*rn_shear_1b:,.0f} / 2.00 = {cap_shear_total:,.0f} \text{{ kg}}")

        

        st.markdown(f"#### 2. Block Shear Rupture (J4.3)")
        st.write(f"Net Shear Area ($A_{{nv}}$): {Anv:.2f} cm² | Net Tension Area ($A_{{nt}}$): {Ant:.2f} cm²")
        st.latex(fr"R_n = \min(0.6 F_u A_{{nv}} + U_{{bs}} F_u A_{{nt}}, 0.6 F_y A_{{nv}} + U_{{bs}} F_u A_{{nt}}) = {Rn_block:,.0f} \text{{ kg}}")
        if is_lrfd:
            st.latex(fr"\phi R_n = 0.75 \times {Rn_block:,.0f} = {cap_block:,.0f} \text{{ kg}}")
        else:
            st.latex(fr"R_n / \Omega = {Rn_block:,.0f} / 2.00 = {cap_block:,.0f} \text{{ kg}}")
            
        

    return n_bolts, cap_1b
