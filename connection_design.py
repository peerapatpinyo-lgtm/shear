import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    # --- 1. INITIALIZATION & MATERIAL ---
    p = section_data
    h_beam = float(p.get('h', 300))  # ความลึกคาน
    tw_beam = float(p.get('tw', 8))  # ความหนาเอวคาน
    Fy, Fu = 2450, 4000  # มาตรฐาน SS400 (kg/cm2)
    
    st.markdown("### 🏗️ Connection Layout & Plate Setup")
    
    # --- 2. INPUT UI (CUSTOMIZABLE LAYOUT) ---
    c1, c2, c3 = st.columns(3)
    with c1:
        n_rows = st.number_input("จำนวนแถวน็อต (แนวดิ่ง)", 2, 12, 3)
        n_cols = st.number_input("จำนวนแถวน็อต (แนวนอน)", 1, 2, 1)
        t_plate_mm = st.number_input("ความหนาแผ่นเหล็ก (t, mm)", 6.0, 40.0, 10.0, 1.0)
    with c2:
        s_v = st.number_input("ระยะห่างแนวดิ่ง (Pitch V, mm)", 50.0, 150.0, 75.0, 5.0)
        s_h = st.number_input("ระยะห่างแนวนอน (Pitch H, mm)", 0.0, 150.0, 50.0, 5.0) if n_cols > 1 else 0
        l_edge_v = st.number_input("ระยะขอบบน-ล่าง (Edge V, mm)", 30.0, 100.0, 40.0, 5.0)
    with c3:
        e1_mm = st.number_input("รอยเชื่อมถึงน็อตตัวแรก (e1, mm)", 40.0, 200.0, 60.0, 5.0)
        l_side = st.number_input("ระยะขอบข้างแผ่น (Side, mm)", 30.0, 100.0, 40.0, 5.0)
        thread_type = st.radio("Thread Position", ["N", "X"], horizontal=True)

    # --- 3. GEOMETRY & HOLE CALCULATION (VERIFIED PRE-DECLARATION) ---
    d_mm = int(bolt_size[1:])
    d_cm = d_mm / 10
    Ab = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}.get(bolt_size, 3.14)
    dh_cm = (d_mm + 2) / 10 
    dh_eff_cm = dh_cm + 0.2  # Effective hole สำหรับ Net Area
    tw_cm = t_plate_mm / 10

    n_total = n_rows * n_cols
    plate_h = (n_rows - 1) * s_v + (2 * l_edge_v)
    plate_w = e1_mm + (n_cols - 1) * s_h + l_side

    # --- 4. FORCE ANALYSIS (SOURCE OF V & ECCENTRICITY) ---
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
    
    # 5.1 Bolt Shear
    bolt_map = {"Grade 8.8 (Standard)": {"N": 3200, "X": 4000}, "A325 (High Strength)": {"N": 3795, "X": 4780}}
    Fnv = bolt_map.get(bolt_grade, bolt_map["Grade 8.8 (Standard)"]).get(thread_type)
    Cap_shear_total = (phi * n_total * Fnv * Ab) / omega

    # 5.2 Bearing & Tear-out
    lc_edge = (l_edge_v/10) - (dh_cm/2)
    lc_inner = (s_v/10) - dh_cm
    Rn_bear = (n_cols * 2 * min(1.2*lc_edge*tw_cm*Fu, 2.4*d_cm*tw_cm*Fu)) + \
              (n_cols * (n_rows-2) * min(1.2*lc_inner*tw_cm*Fu, 2.4*d_cm*tw_cm*Fu))
    Cap_bear = (phi * Rn_bear) / omega

    # --- 6. SHOP DRAWING VISUALIZATION ---
    st.divider()
    st.subheader("🎨 Structural & Plate Detail")
    fig = go.Figure()
    
    # Column Boundary
    fig.add_shape(type="rect", x0=-40, y0=-50, x1=0, y1=plate_h+50, fillcolor="#2c3e50", line_color="black")
    fig.add_annotation(x=-20, y=plate_h/2, text="COLUMN", textangle=-90, font=dict(color="white"))
    
    # Beam Web Trace
    fig.add_shape(type="rect", x0=2, y0=(plate_h/2 - h_beam/2), x1=plate_w+60, y1=(plate_h/2 + h_beam/2), 
                 line=dict(color="rgba(0,0,0,0.3)", width=1, dash="dot"))
    fig.add_annotation(x=plate_w, y=plate_h/2 + h_beam/2 + 10, text=f"BEAM WEB (h={h_beam})")

    # Fin Plate
    fig.add_shape(type="rect", x0=0, y0=0, x1=plate_w, y1=plate_h, fillcolor="rgba(52, 152, 219, 0.15)", line_color="#2980b9", line_width=2)
    
    # Bolt Markers
    for r in range(n_rows):
        for c in range(n_cols):
            bx, by = e1_mm + c*s_h, l_edge_v + r*s_v
            fig.add_trace(go.Scatter(x=[bx], y=[by], mode='markers+text', text=[f"B{r+1}"], marker=dict(size=14, color='#e74c3c')))
    
    # Dimensioning annotations
    fig.add_annotation(x=e1_mm/2, y=-25, text=f"e1={e1_mm}", showarrow=True)
    fig.add_annotation(x=plate_w+35, y=l_edge_v+s_v/2, text=f"Pitch={s_v}", textangle=90, showarrow=True)
    fig.update_layout(height=600, plot_bgcolor='white', xaxis_visible=False, yaxis_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # --- 7. FULL DETAILED CALCULATION SHEET ---
    st.title(f"📄 Engineering Calculation Report ({m_tag})")
    
    st.success(f"**Plate Summary:** THK {t_plate_mm} mm x Width {plate_w:.0f} mm x Height {plate_h:.0f} mm")

    with st.expander("STEP 1: Load Analysis & Resultant Force", expanded=True):
        st.write(f"แรงเฉือนป้อนเข้า (Design Shear, V): **{V_design:,.0f} kg**")
        st.latex(fr"V_{{direct/bolt}} = V / N = {V_design} / {n_total} = {V_direct:,.1f} \text{{ kg}}")
        st.latex(fr"V_{{resultant/bolt}} = \sqrt{{(V_{{dir}} + V_{{ecc,y}})^2 + V_{{ecc,x}}^2}} = {V_res:,.1f} \text{{ kg}}")
        st.write(f"*(วิเคราะห์แรงลัพธ์ต่อน็อต 1 ตัว โดยรวมผลจากระยะเยื้องศูนย์ $e = {e_total_cm:.1f}$ cm)*")
        

    with st.expander("STEP 2: Bolt Shear Capacity (AISC J3.6)"):
        st.latex(fr"R_n = F_{{nv}} \times A_b \times N_{{bolt}} = {Fnv} \times {Ab} \times {n_total} = {n_total*Fnv*Ab:,.0f} \text{{ kg}}")
        st.latex(fr"{sym} = {Cap_shear_total:,.0f} \text{{ kg}}")
        r_s = (V_res * n_total) / Cap_shear_total
        st.metric("Bolt Shear Ratio", f"{r_s:.2f}", delta="PASS" if r_s <= 1 else "FAIL")

    with st.expander("STEP 3: Bearing & Tear-out Capacity (AISC J3.10)"):
        st.write(f"ความหนาแผ่นเหล็ก ($t$): {t_plate_mm} mm | ขนาดน็อต ($d$): {d_mm} mm")
        st.latex(fr"R_n = \sum \min(1.2 L_c t F_u, 2.4 d t F_u) = {Rn_bear:,.0f} \text{{ kg}}")
        st.latex(fr"{sym} = {Cap_bear:,.0f} \text{{ kg}}")
        r_b = V_design / Cap_bear
        st.metric("Bearing Ratio", f"{r_b:.2f}", delta="PASS" if r_b <= 1 else "FAIL")
        

    return n_total, Cap_shear_total
