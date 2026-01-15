import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    # --- STEP 1: MEMBER DATA & MATERIAL ---
    p = section_data
    h_beam = float(p.get('h', 300))
    tw_beam_mm = float(p.get('tw', 8))
    Fy, Fu = 2450, 4000  # SS400 Material Properties (kg/cm2)
    
    st.markdown("### 🔩 Fin Plate Design & Detailing")
    
    # --- STEP 2: USER INPUTS (LAYOUT & GEOMETRY) ---
    c1, c2, c3 = st.columns(3)
    with c1:
        n_rows = st.number_input("จำนวนแถวน็อต (แนวดิ่ง)", 2, 12, 3)
        n_cols = st.number_input("จำนวนแถวน็อต (แนวนอน)", 1, 2, 1)
        t_plate_mm = st.number_input("ความหนาแผ่นประกับ (t_p, mm)", 6.0, 40.0, 10.0, 1.0)
    with c2:
        s_v = st.number_input("Vertical Pitch (s_v, mm)", 50.0, 150.0, 75.0, 5.0)
        s_h = st.number_input("Horizontal Pitch (s_h, mm)", 0.0, 150.0, 50.0, 5.0) if n_cols > 1 else 0
        l_edge_v = st.number_input("Vertical Edge Dist. (l_ev, mm)", 30.0, 100.0, 40.0, 5.0)
    with c3:
        e1_mm = st.number_input("Weld to 1st Bolt Line (e1, mm)", 40.0, 200.0, 60.0, 5.0)
        l_side = st.number_input("Plate Side Margin (l_es, mm)", 30.0, 100.0, 40.0, 5.0)
        thread_type = st.radio("Thread Condition", ["N", "X"], horizontal=True)

    # --- STEP 3: CORE ENGINEERING VARIABLES (CRITICAL SEQUENCE) ---
    # บรรทัดเหล่านี้ต้องมาก่อนการคำนวณ Strength เสมอ
    d_mm = int(bolt_size[1:])
    d_cm = d_mm / 10
    tw_cm = t_plate_mm / 10
    Ab = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}.get(bolt_size, 3.14)
    dh_cm = (d_mm + 2) / 10 
    dh_eff_cm = dh_cm + 0.2 # AISC B4.3b (+2mm for Net Area calculation)
    
    n_total = n_rows * n_cols
    plate_h = (n_rows - 1) * s_v + (2 * l_edge_v)
    plate_w = e1_mm + (n_cols - 1) * s_h + l_side

    # --- STEP 4: BOLT GROUP ECCENTRICITY ANALYSIS ---
    e_total_cm = (e1_mm + (n_cols-1)*s_h/2) / 10
    y_coords = [(r - (n_rows-1)/2) * (s_v/10) for r in range(n_rows)]
    x_coords = [(c - (n_cols-1)/2) * (s_h/10) for c in range(n_cols)]
    
    # Polar Moment of Inertia (Ip = Σx² + Σy²)
    Ip = (sum([y**2 for y in y_coords]) * n_cols) + (sum([x**2 for x in x_coords]) * n_rows)
    
    V_dir = V_design / n_total
    V_ecc_x = (V_design * e_total_cm * max([abs(y) for y in y_coords])) / Ip if Ip > 0 else 0
    V_ecc_y = (V_design * e_total_cm * max([abs(x) for x in x_coords])) / Ip if Ip > 0 else 0
    V_res = math.sqrt((V_dir + V_ecc_y)**2 + V_ecc_x**2)

    # --- STEP 5: LIMIT STATE CAPACITIES (AISC 360-16) ---
    phi, omega = (0.75, 1.00) if is_lrfd else (1.00, 2.00)
    m_tag = "LRFD" if is_lrfd else "ASD"
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

    # --- STEP 6: VISUALIZATION & SHOP DETAIL ---
    st.divider()
    st.subheader("🎨 Structural Detail & Drawing")
    fig = go.Figure()
    
    # ColumnFace
    fig.add_shape(type="rect", x0=-40, y0=-50, x1=0, y1=plate_h+50, fillcolor="#34495e", line_color="black")
    fig.add_annotation(x=-20, y=plate_h/2, text="COLUMN FACE", textangle=-90, font=dict(color="white"))
    
    # Beam Web Trace
    fig.add_shape(type="rect", x0=2, y0=(plate_h/2 - h_beam/2), x1=plate_w+60, y1=(plate_h/2 + h_beam/2), 
                 line=dict(color="rgba(0,0,0,0.3)", width=1, dash="dot"))
    fig.add_annotation(x=plate_w, y=plate_h/2 + h_beam/2 + 10, text=f"BEAM WEB (h={h_beam})", font=dict(size=10))

    # Fin Plate
    fig.add_shape(type="rect", x0=0, y0=0, x1=plate_w, y1=plate_h, fillcolor="rgba(41, 128, 185, 0.2)", line_color="#2980b9", line_width=2)
    
    # Bolt Markers
    for r in range(n_rows):
        for c in range(n_cols):
            bx, by = e1_mm + c*s_h, l_edge_v + r*s_v
            fig.add_trace(go.Scatter(x=[bx], y=[by], mode='markers+text', text=[f"B{r+1}"], 
                                     marker=dict(size=12, color='#c0392b', line=dict(width=2, color='white'))))
    
    # Dimensions
    fig.add_annotation(x=e1_mm/2, y=-25, text=f"e1={e1_mm}", showarrow=True)
    fig.add_annotation(x=plate_w+35, y=l_edge_v+s_v/2, text=f"Pitch={s_v}", textangle=90, showarrow=True)
    fig.update_layout(height=600, plot_bgcolor='white', xaxis_visible=False, yaxis_visible=False, margin=dict(l=60,r=60,t=60,b=60))
    st.plotly_chart(fig, use_container_width=True)

    # --- STEP 7: COMPREHENSIVE CALCULATION SHEET ---
    st.title(f"📄 Calculation Sheet: Fin Plate Connection ({m_tag})")
    st.info(f"**Plate Required:** {t_plate_mm}mm THK. x {plate_w:.0f}mm (W) x {plate_h:.0f}mm (H)")

    with st.expander("1. Analysis of Forces (Demand)", expanded=True):
        st.write(f"แรงเฉือนออกแบบ (V): **{V_design:,.0f} kg**")
        st.latex(fr"V_{{direct}} = V / N = {V_design} / {n_total} = {V_dir:,.1f} \text{{ kg/bolt}}")
        st.latex(fr"M_{{ecc}} = V \cdot e = {V_design} \cdot {e_total_cm:.2f} = {V_design*e_total_cm:,.0f} \text{{ kg-cm}}")
        st.latex(fr"V_{{resultant}} = \sqrt{{(V_{{dir}} + V_{{ecc,y}})^2 + V_{{ecc,x}}^2}} = {V_res:,.1f} \text{{ kg/bolt}}")
        st.write(f"*(วิเคราะห์แรงต่อน็อต 1 ตัวที่วิกฤตที่สุด โดยรวมผลจากความเยื้องศูนย์)*")

    with st.expander("2. Bolt Shear Strength (AISC J3.6)"):
        st.latex(fr"R_n = F_{{nv}} \cdot A_b \cdot N = {Fnv} \cdot {Ab} \cdot {n_total} = {n_total*Fnv*Ab:,.0f} \text{{ kg}}")
        st.latex(fr"{sym} = {Cap_shear:,.0f} \text{{ kg}}")
        r_s = (V_res * n_total) / Cap_shear
        st.write(f"**Demand/Capacity Ratio (Shear):** {r_s:.2f}")

    with st.expander("3. Bearing & Tear-out Strength (AISC J3.10)"):
        st.write(f"Clear Distance Check: $L_{{c,edge}} = {lc_edge:.2f}$ cm, $L_{{c,inner}} = {lc_inner:.2f}$ cm")
        st.latex(fr"R_n = \sum \min(1.2 L_c t F_u, 2.4 d t F_u) = {Rn_bear:,.0f} \text{{ kg}}")
        st.latex(fr"{sym} = {Cap_bear:,.0f} \text{{ kg}}")
        r_b = V_design / Cap_bear
        st.write(f"**Demand/Capacity Ratio (Bearing):** {r_b:.2f}")
        

    with st.expander("4. Block Shear Rupture (AISC J4.3)"):
        st.write(f"Shear Area ($A_{{nv}}$): {Anv:.2f} cm² | Tension Area ($A_{{nt}}$): {Ant:.2f} cm²")
        st.latex(fr"R_n = \min(0.6 F_u A_{{nv}} + U_{{bs}} F_u A_{{nt}}, 0.6 F_y A_{{gv}} + U_{{bs}} F_u A_{{nt}}) = {Rn_bs:,.0f} \text{{ kg}}")
        st.latex(fr"{sym} = {Cap_bs:,.0f} \text{{ kg}}")
        r_bs = V_design / Cap_bs
        st.write(f"**Demand/Capacity Ratio (Block Shear):** {r_bs:.2f}")
        

    return n_total, Cap_shear
