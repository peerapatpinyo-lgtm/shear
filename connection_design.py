import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    """
    V_design: Force (kg)
    T_design: Tension Force (kg)
    """
    # --- INTERNAL REVIEW: THREAD CONDITION SELECTION ---
    # วิศวกรต้องสามารถเลือกได้ว่าจะให้เกลียวอยู่ในระนาบแรงเฉือน (N) หรือไม่ (X)
    thread_type = st.radio(
        "Select Thread Condition (AISC Table J3.2):",
        options=["N (Threads Included)", "X (Threads Excluded)"],
        index=0,
        horizontal=True,
        help="N: เกลียวอยู่ในระนาบแรงเฉือน (กำลังต่ำกว่า) | X: เกลียวนอกระนาบแรงเฉือน (กำลังสูงกว่า)"
    )[0] # เก็บค่าแค่ 'N' หรือ 'X'

    p = section_data
    h_mm, tw_mm, tf_mm = p['h'], p['tw'], p['tf']
    tw_cm = tw_mm / 10
    Fy, Fu = 2450, 4000 # SS400 (kg/cm2)

    # 1. BOLT & HOLE GEOMETRY (AISC Table J3.3)
    b_areas = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}
    Ab = b_areas.get(bolt_size, 3.14)
    d_mm = int(bolt_size[1:])
    d_cm = d_mm / 10
    dh_cm = (d_mm + 2) / 10 # Standard Hole (d+2mm)

    # 2. NOMINAL STRENGTHS (AISC Table J3.2)
    # ทวนสอบ: ค่า Fnv ต้องเปลี่ยนตาม Thread Condition (N/X)
    bolt_map = {
        "A325 (High Strength)": {"Fnv_N": 3795, "Fnv_X": 4780, "Fnt": 6325},
        "Grade 8.8 (Standard)": {"Fnv_N": 3200, "Fnv_X": 4000, "Fnt": 5300},
        "A490 (Premium)":       {"Fnv_N": 4780, "Fnv_X": 5975, "Fnt": 7940}
    }
    spec = bolt_map.get(bolt_grade, bolt_map["Grade 8.8 (Standard)"])
    Fnv = spec["Fnv_N"] if thread_type == "N" else spec["Fnv_X"]
    Fnt = spec["Fnt"]

    # 3. DESIGN PHILOSOPHY (LRFD vs ASD) - เด็ดขาดตาม AISC Chapter J
    if is_lrfd:
        phi, omega = 0.75, 1.00
        phi_y, omega_y = 1.00, 1.00
        method_name = "LRFD (Load and Resistance Factor Design)"
        calc_prefix = r"\phi R_n = 0.75 \times"
    else:
        phi, omega = 1.00, 2.00
        phi_y, omega_y = 1.00, 1.50
        method_name = "ASD (Allowable Strength Design)"
        calc_prefix = r"R_n / \Omega = R_n / 2.00 ="

    # 4. INITIAL BOLT CALCULATION
    rn_shear_1b = Fnv * Ab
    rn_bearing_1b = 2.4 * d_cm * tw_cm * Fu
    cap_1b_shear = (phi * min(rn_shear_1b, rn_bearing_1b)) / omega
    
    n_bolts = max(2, math.ceil(V_design / cap_1b_shear))
    if n_bolts % 2 != 0: n_bolts += 1
    n_rows = n_bolts // 2

    # 5. SPACING & LAYOUT (AISC J3.3)
    s_pitch = 3.0 * d_mm
    l_edge = 1.5 * d_mm
    lc_cm = (l_edge/10) - (dh_cm / 2)

    # 6. LIMIT STATES ANALYSIS
    # --- Case 1: Bolt Shear (J3.6) ---
    Rn_bolt_shear = n_bolts * Fnv * Ab
    # --- Case 2: Combined Shear & Tension (J3.7) ---
    frv = V_design / (n_bolts * Ab) 
    if is_lrfd:
        Fnt_prime = min(1.3 * Fnt - (Fnt / (0.75 * Fnv)) * frv, Fnt)
    else:
        Fnt_prime = min(1.3 * Fnt - (2.0 * Fnt / Fnv) * frv, Fnt)
    Rn_combined = n_bolts * Fnt_prime * Ab
    
    # --- Case 3: Bearing & Tear-out (J3.10) ---
    Rn_bearing_gov = n_bolts * min(2.4 * d_cm * tw_cm * Fu, 1.2 * lc_cm * tw_cm * Fu)

    # --- Case 4: Block Shear (J4.3) ---
    Anv = ((n_rows-1)*(s_pitch/10) + l_edge/10 - (n_rows-0.5)*dh_cm) * tw_cm * 2
    Ant = (2 * l_edge/10 - 1.0 * dh_cm) * tw_cm
    Rn_block = min(0.6*Fu*Anv + 1.0*Fu*Ant, 0.6*Fy*Anv + 1.0*Fu*Ant)

    # 7. CAPACITY SUMMARY
    caps = {
        "Bolt Shear": (phi * Rn_bolt_shear) / omega,
        "Bearing/Tear-out": (phi * Rn_bearing_gov) / omega,
        "Block Shear": (phi * Rn_block) / omega,
        "Combined T-V": (phi * Rn_combined) / omega,
        "Web Yielding": (phi_y * 0.6 * Fy * (h_mm * tw_mm / 100)) / omega_y
    }

    # --- UI RENDERING ---
    st.title(f"🔍 {method_name}")
    st.info(f"Analysis Reference: AISC 360-16 | Bolt: {bolt_grade} ({thread_type})")

    # Dashboard Metrics
    cols = st.columns(len(caps))
    for i, (name, val) in enumerate(caps.items()):
        force = V_design if name != "Combined T-V" else T_design
        ratio = force / val if val > 0 else 0
        color = "normal" if ratio <= 1.0 else "inverse"
        cols[i].metric(name, f"{val:,.0f} kg", f"Ratio {ratio:.2f}", delta_color=color)

    # Sketch Section (คงไว้ตามที่คุณชอบ)
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
        fig.update_layout(xaxis_visible=False, yaxis_visible=False, height=350, margin=dict(l=0,r=0,t=0,b=0), plot_bgcolor='white', title="Bolt Layout Sketch")
        st.plotly_chart(fig, use_container_width=True)
    with c_info:
        st.markdown("### 📏 Layout Check")
        st.write(f"- **Bolt Size:** {bolt_size} (Type {thread_type})")
        st.write(f"- **$F_{{nv}}$ Used:** {Fnv} kg/cm²")
        st.write(f"- **Pitch (s):** {s_pitch} mm")
        st.write(f"- **Edge (le):** {l_edge} mm")

    # 8. STEP-BY-STEP CALCULATION NOTE
    st.markdown("---")
    st.subheader("📝 รายการคำนวณแยกสูตรตามระบบที่เลือก (Calculation Detail)")

    # Section 1: Shear
    with st.expander("STEP 1: Bolt Shear (AISC J3.6)", expanded=True):
        st.latex(fr"F_{{nv}} = {Fnv} \text{{ kg/cm}}^2 \quad (\text{{Condition: }} {thread_type})")
        st.latex(fr"R_n = F_{{nv}} A_b N_b = {Fnv} \cdot {Ab} \cdot {n_bolts} = {Rn_bolt_shear:,.0f} \text{{ kg}}")
        st.latex(fr"{calc_prefix} {Rn_bolt_shear:,.0f} = {caps['Bolt Shear']:,.0f} \text{{ kg}}")
        

    # Section 2: Combined Force
    with st.expander("STEP 2: Combined Shear & Tension (AISC J3.7)"):
        st.latex(fr"f_{{rv}} = V / (N A_b) = {frv:.1f} \text{{ kg/cm}}^2")
        if is_lrfd:
            st.latex(fr"F'_{{nt}} = 1.3F_{{nt}} - \frac{{F_{{nt}}}}{{\phi F_{{nv}}}} f_{{rv}} = {Fnt_prime:.1f} \text{{ kg/cm}}^2")
            st.latex(fr"\phi R_n = 0.75 (F'_{{nt}} A_b N_b) = {caps['Combined T-V']:,.0f} \text{{ kg}}")
        else:
            st.latex(fr"F'_{{nt}} = 1.3F_{{nt}} - \frac{{\Omega F_{{nt}}}}{{F_{{nv}}}} f_{{rv}} = {Fnt_prime:.1f} \text{{ kg/cm}}^2")
            st.latex(fr"R_n / \Omega = \frac{{F'_{{nt}} A_b N_b}}{{2.00}} = {caps['Combined T-V']:,.0f} \text{{ kg}}")
        

    # Section 3: Block Shear
    with st.expander("STEP 3: Block Shear Rupture (AISC J4.3)"):
        st.write(f"Net Shear Area (Anv): {Anv:.2f} cm² | Net Tension Area (Ant): {Ant:.2f} cm²")
        st.latex(fr"R_n = \min(0.6 F_u A_{{nv}} + U_{{bs}} F_u A_{{nt}}, 0.6 F_y A_{{nv}} + U_{{bs}} F_u A_{{nt}}) = {Rn_block:,.0f} \text{{ kg}}")
        st.latex(fr"{calc_prefix} {Rn_block:,.0f} = {caps['Block Shear']:,.0f} \text{{ kg}}")
        

    # 9. ENGINEERING RECOMMENDATIONS
    max_ratio = max([V_design/v if name != "Combined T-V" else T_design/v for name, v in caps.items()])
    if max_ratio > 1.0:
        st.error(f"### ⚠️ Ratio เกินมาตรฐาน ({max_ratio:.2f})")
        st.markdown(f"**Engineering Strategy:** พิจารณาเปลี่ยนเป็น **Type X** หรือเพิ่มความหนาของแผ่นเหล็ก")

    return n_bolts, cap_1b_shear
