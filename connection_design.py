import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    # --- 1. INITIALIZATION & DATA RETRIEVAL ---
    p = section_data
    h_beam = float(p.get('h', 300))
    tw_beam = float(p.get('tw', 8))
    Fy, Fu = 2450, 4000  # SS400 Material (kg/cm2)
    
    st.markdown("### 🏗️ Connection Geometry & Material Input")
    
    # --- 2. LAYOUT INPUTS (Customizable & Precise) ---
    c1, c2, c3 = st.columns(3)
    with c1:
        n_rows = st.number_input("จำนวนแถวน็อต (แนวตั้ง)", 2, 12, 3)
        n_cols = st.number_input("จำนวนแถวน็อต (แนวนอน)", 1, 2, 1)
        t_plate_mm = st.number_input("ความหนาแผ่นเหล็ก (t, mm)", 6.0, 40.0, 10.0, 1.0)
    with c2:
        s_v = st.number_input("ระยะห่างแนวดิ่ง (Vertical Pitch, mm)", 50.0, 150.0, 75.0, 5.0)
        s_h = st.number_input("ระยะห่างแนวนอน (Horizontal Pitch, mm)", 0.0, 150.0, 50.0, 5.0) if n_cols > 1 else 0
        l_edge_v = st.number_input("ระยะขอบบน-ล่าง (Edge V, mm)", 30.0, 100.0, 40.0, 5.0)
    with c3:
        e1_mm = st.number_input("แนวเชื่อมถึงน็อตแถวแรก (e1, mm)", 40.0, 200.0, 60.0, 5.0)
        l_side = st.number_input("ระยะขอบด้านข้าง (Side Margin, mm)", 30.0, 100.0, 40.0, 5.0)
        thread_type = st.radio("Thread Position", ["N", "X"], horizontal=True)

    # --- 3. GEOMETRY & HOLE CALCULATION (CORE LOGIC) ---
    # ประกาศค่าคงที่ที่จำเป็นทั้งหมดก่อนการคำนวณกำลัง
    d_mm = int(bolt_size[1:])
    d_cm = d_mm / 10
    Ab = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}.get(bolt_size, 3.14)
    dh_cm = (d_mm + 2) / 10 
    dh_eff_cm = dh_cm + 0.2 # AISC B4.3b (+2mm for Rupture/Net Area)
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

    # --- 6. VISUALIZATION (FULL SHOP DETAIL) ---
    st.divider()
    st.subheader("🎨 Connection Detail Drawing")
    fig = go.Figure()
    
    # Column (Static Boundary)
    fig.add_shape(type="rect", x0=-40, y0=-50, x1=0, y1=plate_h+50, fillcolor="#2c3e50", line_color="black")
    fig.add_annotation(x=-20, y=plate_h/2, text="COLUMN", textangle=-90, font=dict(color="white"))
    
    # Beam Web Outline (Dashed)
    fig.add_shape(type="rect", x0=2, y0=(plate_h/2 - h_beam/2), x1=plate_w+60, y1=(plate_h/2 + h_beam/2), 
                 line=dict(color="rgba(0,0,0,0.3)", width=1, dash="dot"))
    fig.add_annotation(x=plate_w, y=plate_h/2 + h_beam/2 + 10, text=f"BEAM WEB (h={h_beam})", font=dict(size=10))

    # Fin Plate (Main Object)
    fig.add_shape(type="rect", x0=0, y0=0, x1=plate_w, y1=plate_h, fillcolor="rgba(52, 152, 219, 0.2)", line_color="#2980b9", line_width=3)
    
    # Bolt Locations
    for r in range(n_rows):
        for c in range(n_cols):
            bx, by = e1_mm + c*s_h, l_edge_v + r*s_v
            fig.add_trace(go.Scatter(x=[bx], y=[by], mode='markers+text', text=[f"B{r+1}"], marker=dict(size=14, color='#e74c3c')))
    
    # Dimension Lines
    fig.add_annotation(x=e1_mm/2, y=-25, text=f"e1={e1_mm}", showarrow=True)
    fig.add_annotation(x=plate_w+30, y=l_edge_v+s_v/2, text=f"pitch={s_v}", textangle=90, showarrow=True)
    fig.update_layout(height=600, plot_bgcolor='white', xaxis_visible=False, yaxis_visible=False, margin=dict(l=50,r=50,t=50,b=50))
    st.plotly_chart(fig, use_container_width=True)

    # --- 7. DETAILED ENGINEERING REPORT ---
    st.title(f"📄 Detailed Calculation Sheet ({m_tag})")
    
    with st.expander("STEP 1: Load Distribution & Eccentricity", expanded=True):
        st.write(f"แรงเฉือนที่กำหนด (V): {V_design:,.0f} kg")
        st.latex(fr"V_{{direct/bolt}} = V / N = {V_design} / {n_total} = {V_direct:,.1f} \text{{ kg}}")
        st.latex(fr"V_{{res/bolt}} = \sqrt{{(V_{{dir}} + V_{{ecc,y}})^2 + V_{{ecc,x}}^2}} = {V_res:,.1f} \text{{ kg}}")
        st.info(f"**Plate Size Summary:** {t_plate_mm}mm THK. x {plate_w:.0f}mm (W) x {plate_h:.0f}mm (H)")

    with st.expander("STEP 2: Bolt Shear Check (AISC J3.6)"):
        st.latex(fr"R_n = F_{{nv}} A_b N = {Fnv} \cdot {Ab} \cdot {n_total} = {n_total*Fnv*Ab:,.0f} \text{{ kg}}")
        st.latex(fr"{sym} = {Cap_shear:,.0f} \text{{ kg}}")
        st.write(f"**Ratio:** {(V_res * n_total) / Cap_shear:.2f}")
        

    with st.expander("STEP 3: Bearing & Tear-out Check (AISC J3.10)"):
        st.write(f"Clear Distances: $L_{{c,edge}} = {lc_edge:.2f}$ cm, $L_{{c,inner}} = {lc_inner:.2f}$ cm")
        st.latex(fr"R_n = \sum \min(1.2 L_c t F_u, 2.4 d t F_u) = {Rn_bear:,.0f} \text{{ kg}}")
        st.latex(fr"{sym} = {Cap_bear:,.0f} \text{{ kg}}")
        st.write(f"**Ratio:** {V_design / Cap_bear:.2f}")
        

    with st.expander("STEP 4: Block Shear Rupture (AISC J4.3)"):
        st.latex(fr"A_{{nv}} = {Anv:.2f} \text{{ cm}}^2, \quad A_{{nt}} = {Ant:.2f} \text{{ cm}}^2")
        st.latex(fr"R_n = \min(0.6 F_u A_{{nv}} + U_{{bs}} F_u A_{{nt}}, 0.6 F_y A_{{gv}} + U_{{bs}} F_u A_{{nt}}) = {Rn_bs:,.0f} \text{{ kg}}")
        st.latex(fr"{sym} = {Cap_bs:,.0f} \text{{ kg}}")
        st.write(f"**Ratio:** {V_design / Cap_bs:.2f}")
        

    return n_total, Cap_shear
