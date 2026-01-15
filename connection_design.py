import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    # --- 1. SETTINGS & PARAMETERS ---
    p = section_data
    h_beam = float(p.get('h', 300))
    Fy, Fu = 2450, 4000  # SS400 (kg/cm2)
    
    st.markdown("### 🔩 Connection Layout & Plate Geometry")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        t_plate_mm = st.number_input("Plate Thickness (mm)", 6.0, 50.0, 10.0, 1.0)
    with c2:
        s_pitch = st.number_input("Bolt Pitch (mm)", 40.0, 150.0, 75.0, 5.0)
    with c3:
        l_edge_v = st.number_input("Edge Dist. (Vertical, mm)", 30.0, 100.0, 40.0, 5.0)
    with c4:
        l_edge_h = st.number_input("Side Margin (Horizontal, mm)", 30.0, 100.0, 40.0, 5.0)

    ecc_mm = st.number_input("Eccentricity (e, mm) - จากรอยเชื่อมถึงแนวน็อต", 40.0, 200.0, 60.0, 5.0)
    thread_type = st.radio("Thread Position", ["N (Included)", "X (Excluded)"], horizontal=True)[0]

    # --- 2. BOLT & HOLE GEOMETRY ---
    d_mm = int(bolt_size[1:])
    d_cm = d_mm / 10
    Ab = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}.get(bolt_size, 3.14)
    dh_cm = (d_mm + 2) / 10 
    dh_eff_cm = dh_cm + (2/10) # AISC B4.3b (+2mm for Rupture check)

    # --- 3. SAFETY FACTORS (LRFD/ASD) ---
    phi, omega = (0.75, 1.00) if is_lrfd else (1.00, 2.00)
    m_name = "LRFD" if is_lrfd else "ASD"
    sym = r"\phi R_n" if is_lrfd else r"R_n / \Omega"

    # --- 4. NOMINAL STRENGTHS ---
    bolt_db = {
        "A325 (High Strength)": {"Fnv_N": 3795, "Fnv_X": 4780},
        "Grade 8.8 (Standard)": {"Fnv_N": 3200, "Fnv_X": 4000}
    }
    spec = bolt_db.get(bolt_grade, bolt_db["Grade 8.8 (Standard)"])
    Fnv = spec["Fnv_N"] if thread_type == "N" else spec["Fnv_X"]

    # --- 5. FORCE ANALYSIS (THE ORIGIN OF V) ---
    # คำนวณจำนวนน็อตเบื้องต้น
    n_bolts = max(2, math.ceil(V_design / ((phi * Fnv * Ab) / omega)))
    if n_bolts % 2 != 0: n_bolts += 1
    n_rows = n_bolts // 1 # เรียงแถวเดียว (Single line bolt)
    
    # คำนวณขนาดแผ่นเหล็ก
    plate_h = (n_rows - 1) * s_pitch + (2 * l_edge_v)
    plate_w = ecc_mm + l_edge_h
    
    # Eccentricity Effect: V_resultant = V_direct + V_ecc
    e_cm = ecc_mm / 10
    # Ip = sum(y^2) ของน็อตแต่ละตัวรอบจุดหมุน
    y_coords = [(r - (n_rows-1)/2) * (s_pitch/10) for r in range(n_rows)]
    Ip = sum([y**2 for y in y_coords])
    
    V_dir = V_design / n_bolts
    V_ecc = (V_design * e_cm * max([abs(y) for y in y_coords])) / Ip if Ip > 0 else 0
    V_total = math.sqrt(V_dir**2 + V_ecc**2)

    # --- 6. LIMIT STATE CALCULATIONS ---
    tw_cm = t_plate_mm / 10
    # 6.1 Bolt Shear
    Rn_shear = n_bolts * Fnv * Ab
    Cap_shear = (phi * Rn_shear) / omega
    
    # 6.2 Bearing/Tear-out
    lc_edge = (l_edge_v/10) - (dh_cm/2)
    lc_inner = (s_pitch/10) - dh_cm
    Rn_bear = (1 * min(1.2*lc_edge*tw_cm*Fu, 2.4*d_cm*tw_cm*Fu)) + \
              ((n_bolts-1) * min(1.2*lc_inner*tw_cm*Fu, 2.4*d_cm*tw_cm*Fu))
    Cap_bear = (phi * Rn_bear) / omega

    # --- 7. UI RENDERING ---
    st.divider()
    st.title(f"📄 Shop Drawing & Analysis Report ({m_name})")
    
    c_left, c_right = st.columns([1.5, 1])
    with c_left:
        # Drawing with Plotly
        fig = go.Figure()
        fig.add_shape(type="rect", x0=0, y0=0, x1=plate_w, y1=plate_h, fillcolor="rgba(100,100,100,0.1)", line_color="black")
        fig.add_shape(type="line", x0=0, y0=0, x1=0, y1=plate_h, line=dict(color="blue", width=8)) # Weld
        for r in range(n_rows):
            y_pos = l_edge_v + r*s_pitch
            fig.add_trace(go.Scatter(x=[ecc_mm], y=[y_pos], mode='markers+text', text=[f"B{r+1}"], marker=dict(size=14, color='red')))
        
        # Annotations (Dimensions)
        fig.add_annotation(x=ecc_mm/2, y=plate_h+10, text=f"e={ecc_mm}", showarrow=False)
        fig.add_annotation(x=plate_w+10, y=l_edge_v/2, text=f"Edge={l_edge_v}", showarrow=False, textangle=90)
        fig.update_layout(height=500, xaxis_title="Width (mm)", yaxis_title="Height (mm)", plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)

    with c_right:
        st.info(f"**Plate Order Size:**\n\n{t_plate_mm}mm THK. x {plate_w:.0f}mm x {plate_h:.0f}mm")
        st.write(f"**Bolt Info:** {n_bolts} nos. {bolt_size} ({bolt_grade})")
        
        # Display Ratios
        r_shear = (V_total * n_bolts) / Cap_shear
        r_bear = V_design / Cap_bear
        st.metric("Bolt Shear Ratio", f"{r_shear:.2f}", delta="Check" if r_shear <= 1 else "Fail", delta_color="normal" if r_shear <= 1 else "inverse")
        st.metric("Bearing Ratio", f"{r_bear:.2f}", delta="Check" if r_bear <= 1 else "Fail", delta_color="normal" if r_bear <= 1 else "inverse")

    # --- 8. DETAILED TRACEABILITY ---
    st.markdown("### 📝 รายการคำนวณแบบละเอียด (Traceable Calculation)")
    
    with st.expander("ที่มาของแรงกระทำ (Source of Forces)", expanded=True):
        st.write(f"1. แรงเฉือนแนวดิ่ง (Direct Shear): $V = {V_design:,.0f}$ kg")
        st.write(f"2. ระยะเยื้องศูนย์ (Eccentricity): $e = {ecc_mm}$ mm")
        st.latex(fr"V_{{direct/bolt}} = \frac{{{V_design}}}{{{n_bolts}}} = {V_dir:,.1f} \text{{ kg}}")
        st.latex(fr"V_{{ecc/bolt}} = \frac{{V \cdot e \cdot y_{{max}}}}{{I_p}} = {V_ecc:,.1f} \text{{ kg}}")
        st.latex(fr"V_{{resultant}} = \sqrt{{V_{{dir}}^2 + V_{{ecc}}^2}} = {V_total:,.1f} \text{{ kg/bolt}}")
        st.caption("แรงนี้จะถูกนำไปเช็คกับกำลังรับแรงเฉือนของ Bolt (Bolt Shear Capacity)")

    with st.expander("รายละเอียดกำลังของแผ่นเหล็ก (Plate Capacity Detail)"):
        st.write(f"**Bearing & Tear-out (AISC J3.10):**")
        st.write(f"- ความหนาแผ่น ($t$): {t_plate_mm} mm")
        st.write(f"- ระยะขอบถึงรูเจาะ ($L_{{c,edge}}$): {lc_edge:.2f} cm")
        st.latex(fr"R_n = \sum \min(1.2 L_c t F_u, 2.4 d t F_u) = {Rn_bear:,.0f} \text{{ kg}}")
        st.latex(fr"Ratio = \frac{{{V_design}}}{{{Cap_bear:,.0f}}} = {r_bear:.2f}")

    return n_bolts, Cap_shear
