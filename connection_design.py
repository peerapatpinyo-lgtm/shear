# connection_design.py (V24 - Complete Mastery & Full Components)
import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, thread_type="N", T_design=0):
    p = section_data
    h_mm, tw_mm, tf_mm = p['h'], p['tw'], p['tf']
    tw_cm = tw_mm / 10
    Fy, Fu = 2450, 4000 # SS400 (kg/cm2)

    # 1. BOLT DATA & NOMINAL STRESS (AISC Table J3.2)
    b_areas = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}
    Ab = b_areas.get(bolt_size, 3.14)
    d_mm = int(bolt_size[1:])
    d_cm, dh_cm = d_mm / 10, (d_mm + 2) / 10 

    # Bolt Database: แปรผันตามเกรดและตำแหน่งเกลียว (N/X)
    bolt_db = {
        "A325 (High Strength)": {"Fnt": 6325, "Fnv_N": 3795, "Fnv_X": 4780},
        "Grade 8.8 (Standard)": {"Fnt": 5300, "Fnv_N": 3200, "Fnv_X": 4000},
        "A490 (Premium)":       {"Fnt": 7940, "Fnv_N": 4780, "Fnv_X": 5975}
    }
    spec = bolt_db.get(bolt_grade)
    Fnt = spec["Fnt"]
    Fnv = spec["Fnv_N"] if thread_type == "N" else spec["Fnv_X"]

    # 2. DESIGN PHILOSOPHY SEPARATION (AISC 360-16)
    if is_lrfd:
        phi, omega = 0.75, 1.00
        phi_y, omega_y = 1.00, 1.00
        method_label = "LRFD"
        calc_symbol = r"\phi R_n = 0.75 \times"
    else:
        phi, omega = 1.00, 2.00
        phi_y, omega_y = 1.00, 1.50
        method_label = "ASD"
        calc_symbol = r"R_n / \Omega = R_n / 2.00 ="

    # 3. NOMINAL STRENGTH CALCULATION
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

    # Combined Force Interaction (J3.7)
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
    cap_block = (phi * Rn_block) / omega

    # --- UI RENDERING ---
    st.header(f"🏗️ Full Connection Report: {method_label}")
    st.info(f"Bolt Grade: {bolt_grade} | Condition: {thread_type} | Steel: SS400")

    # Metrics Dashboard
    m1, m2, m3, m4 = st.columns(4)
    v_ratio = V_design / (cap_1b * n_bolts)
    t_ratio = T_design / cap_combined if T_design > 0 else 0
    m1.metric("Shear Ratio", f"{v_ratio:.3f}", delta="SAFE" if v_ratio <= 1 else "OVER", delta_color="normal" if v_ratio <= 1 else "inverse")
    m2.metric("Tension Ratio", f"{t_ratio:.3f}", delta="SAFE" if t_ratio <= 1 else "OVER", delta_color="normal" if t_ratio <= 1 else "inverse")
    m3.metric("Fnv", f"{Fnv}", f"Type {thread_type}")
    m4.metric("Bolt Count", f"{n_bolts}", f"{n_rows} Rows")

    # Sketch Section (กลับมาแล้ว!)
    st.divider()
    c_draw, c_info = st.columns([1.5, 1])
    with c_draw:
        fig = go.Figure()
        fig.add_shape(type="rect", x0=0, y0=0, x1=10, y1=h_mm, fillcolor="rgba(37, 99, 235, 0.1)", line_color="#2563eb")
        start_y = (h_mm/2) - ((n_rows-1)*s_pitch)/2
        for r in range(n_rows):
            y = start_y + r*s_pitch
            for x in [3, 7]:
                fig.add_trace(go.Scatter(x=[x], y=[y], mode='markers', marker=dict(size=14, color='#ef4444', line=dict(width=2, color='white'))))
        fig.update_layout(xaxis_visible=False, yaxis_visible=False, height=350, margin=dict(l=0,r=0,t=0,b=0), plot_bgcolor='white', title="Connection Sketch (Plan)")
        st.plotly_chart(fig, use_container_width=True)
    with c_info:
        st.markdown("### 📏 Layout Check")
        st.write(f"- **Pitch (s):** {s_pitch} mm (Min: {2.67*d_mm:.1f})")
        st.write(f"- **Edge (le):** {l_edge} mm (Min: J3.4)")
        if v_ratio > 1 or t_ratio > 1:
            st.error("⚠️ Design Overloaded!")
        else:
            st.success("✅ Geometry & Strength Pass")

    # Detailed Calculation (Step-by-Step แยก ASD/LRFD)
    st.divider()
    with st.expander("📖 รายการคำนวณอย่างละเอียด (Full Step-by-Step Note)", expanded=True):
        # 1. Bolt Shear
        st.markdown("#### 1. Bolt Shear Strength (J3.6)")
        st.latex(fr"R_n = F_{{nv}} A_b N_b = {Fnv} \times {Ab:.2f} \times {n_bolts} = {n_bolts*rn_shear_1b:,.0f} \text{{ kg}}")
        st.latex(fr"{calc_symbol} {n_bolts*rn_shear_1b:,.0f} = {cap_1b*n_bolts:,.0f} \text{{ kg}}")

        # 2. Combined Tension
        if T_design > 0:
            st.markdown("#### 2. Combined Shear & Tension (J3.7)")
            if is_lrfd:
                st.latex(fr"F'_{{nt}} = 1.3F_{{nt}} - \frac{{F_{{nt}}}}{{\phi F_{{nv}}}} f_{{rv}} = {Fnt_prime:.1f} \text{{ kg/cm}}^2")
            else:
                st.latex(fr"F'_{{nt}} = 1.3F_{{nt}} - \frac{{\Omega F_{{nt}}}}{{F_{{nv}}}} f_{{rv}} = {Fnt_prime:.1f} \text{{ kg/cm}}^2")
            st.latex(fr"{calc_symbol} (F'_{{nt}} A_b N_b) = {cap_combined:,.0f} \text{{ kg}}")

        # 3. Block Shear
        st.markdown("#### 3. Block Shear Rupture (J4.3)")
        st.latex(fr"R_n = \min(0.6F_u A_{{nv}} + U_{{bs}}F_u A_{{nt}}, 0.6F_y A_{{nv}} + U_{{bs}}F_u A_{{nt}}) = {Rn_block:,.0f} \text{{ kg}}")
        st.latex(fr"{calc_symbol} {Rn_block:,.0f} = {cap_block:,.0f} \text{{ kg}}")

    return n_bolts, cap_1b
