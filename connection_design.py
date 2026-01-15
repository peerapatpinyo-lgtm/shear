import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    # --- 1. DATA PREPARATION ---
    # ดึงค่าจากหน้าตัดคาน (Beam) และกำหนดค่าเสา (Column) เบื้องต้น
    p = section_data
    h_beam = float(p.get('h', 300))
    tw_beam = float(p.get('tw', 8))
    Fy, Fu = 2450, 4000  # SS400 (kg/cm2)
    
    st.markdown("### 🏗️ Connection & Member Geometry")
    
    # --- 2. LAYOUT INPUTS (Customizable & Precise) ---
    c1, c2, c3 = st.columns(3)
    with c1:
        n_bolt_rows = st.number_input("Number of Bolt Rows (Vertical)", 2, 12, 3)
        n_bolt_cols = st.number_input("Number of Bolt Columns (Horizontal)", 1, 2, 1)
    with c2:
        s_pitch_v = st.number_input("Vertical Pitch (mm)", 50.0, 150.0, 75.0, 5.0)
        s_pitch_h = st.number_input("Horizontal Pitch (mm)", 0.0, 150.0, 50.0, 5.0) if n_bolt_cols > 1 else 0
    with c3:
        l_edge_top = st.number_input("Top/Bottom Edge (mm)", 30.0, 100.0, 40.0, 5.0)
        l_edge_side = st.number_input("Side Margin to Edge (mm)", 30.0, 100.0, 40.0, 5.0)

    c4, c5 = st.columns(2)
    with c4:
        ecc_weld_to_bolt1 = st.number_input("Weld to First Bolt Line (e1, mm)", 40.0, 200.0, 60.0, 5.0)
    with c5:
        t_plate_mm = st.number_input("Fin Plate Thickness (mm)", 6.0, 40.0, 10.0, 1.0)

    # --- 3. GEOMETRY VALIDATION ---
    n_bolts = n_bolt_rows * n_bolt_cols
    plate_h = (n_bolt_rows - 1) * s_pitch_v + (2 * l_edge_top)
    plate_w = ecc_weld_to_bolt1 + (n_bolt_cols - 1) * s_pitch_h + l_edge_side
    
    # ตรวจสอบว่าแผ่นเหล็กใหญ่เกินคานไหม
    if plate_h > (h_beam - 50): # ให้เหลือระยะ Top/Bottom Cope อย่างน้อย 25mm
        st.warning(f"⚠️ Fin Plate Height ({plate_h}mm) เกือบเท่าหรือเกินความลึกคาน ({h_beam}mm). กรุณาลดระยะห่างหรือจำนวนน็อต")

    # --- 4. FORCE ANALYSIS (ECCENTRICITY) ---
    # หาระยะเยื้องศูนย์รวม (e) จากรอยเชื่อมถึงจุดศูนย์กลางกลุ่มน็อต
    e_total_mm = ecc_weld_to_bolt1 + ((n_bolt_cols - 1) * s_pitch_h / 2)
    e_cm = e_total_mm / 10
    
    # Elastic Method: Ip = sum(x^2 + y^2)
    x_coords = [(c - (n_bolt_cols-1)/2) * (s_pitch_h/10) for c in range(n_bolt_cols)]
    y_coords = [(r - (n_bolt_rows-1)/2) * (s_pitch_v/10) for r in range(n_bolt_rows)]
    Ip = sum([x**2 for x in x_coords]) * n_bolt_rows + sum([y**2 for y in y_coords]) * n_bolt_cols
    
    V_dir = V_design / n_bolts
    # คำนวณแรงที่ Bolt ตัวไกลที่สุด (Critical Bolt)
    max_x = max([abs(x) for x in x_coords]) if n_bolt_cols > 1 else 0
    max_y = max([abs(y) for y in y_coords])
    V_ecc_x = (V_design * e_cm * max_y) / Ip if Ip > 0 else 0
    V_ecc_y = (V_design * e_cm * max_x) / Ip if Ip > 0 else 0
    V_resultant = math.sqrt((V_dir + V_ecc_y)**2 + V_ecc_x**2)

    # --- 5. CAPACITY CALCULATIONS ---
    # Bolt Shear
    bolt_db = {"Grade 8.8 (Standard)": 3200, "A325 (High Strength)": 3795} # Fnv (N)
    Fnv = bolt_db.get(bolt_grade, 3200)
    d_mm = int(bolt_size[1:])
    Ab = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}.get(bolt_size, 3.14)
    
    phi, omega = (0.75, 1.00) if is_lrfd else (1.00, 2.00)
    Cap_bolt_shear = (phi * n_bolts * Fnv * Ab) / omega

    # --- 6. VISUALIZATION (DETAILED SHOP DRAWING) ---
    st.divider()
    st.subheader("📐 Structural Layout Drawing")
    
    fig = go.Figure()
    # 1. Column (Represented as a vertical boundary)
    fig.add_shape(type="rect", x0=-20, y0=-50, x1=0, y1=plate_h + 50, fillcolor="darkslategrey", line_color="black")
    fig.add_annotation(x=-10, y=plate_h/2, text="COLUMN FACE", textangle=-90, font=dict(color="white"))
    
    # 2. Beam Outline (Phantom lines)
    fig.add_shape(type="rect", x0=2, y0=(plate_h/2 - h_beam/2), x1=plate_w + 50, y1=(plate_h/2 + h_beam/2), 
                 line=dict(color="grey", width=2, dash="dash"), fillcolor="rgba(200,200,200,0.1)")
    fig.add_annotation(x=plate_w, y=plate_h/2 + h_beam/2 - 15, text="BEAM WEB OUTLINE", font=dict(color="grey"))

    # 3. Fin Plate
    fig.add_shape(type="rect", x0=0, y0=0, x1=plate_w, y1=plate_h, fillcolor="rgba(37, 99, 235, 0.2)", line_color="blue", line_width=2)
    fig.add_annotation(x=plate_w/2, y=plate_h + 20, text=f"FIN PLATE ({t_plate_mm}mm THK)", font=dict(color="blue", size=14))

    # 4. Bolts & Dimension Lines
    for r in range(n_bolt_rows):
        for c in range(n_bolt_cols):
            bx = ecc_weld_to_bolt1 + c * s_pitch_h
            by = l_edge_top + r * s_pitch_v
            fig.add_trace(go.Scatter(x=[bx], y=[by], mode='markers', marker=dict(size=12, color='red', line=dict(width=2, color='white'))))

    # Dimensions
    fig.add_annotation(x=ecc_weld_to_bolt1/2, y=-25, text=f"e1={ecc_weld_to_bolt1}", showarrow=True, arrowhead=2)
    if n_bolt_cols > 1: fig.add_annotation(x=ecc_weld_to_bolt1 + s_pitch_h/2, y=-25, text=f"sh={s_pitch_h}", showarrow=True)
    fig.add_annotation(x=plate_w + 40, y=l_edge_top + s_pitch_v/2, text=f"sv={s_pitch_v}", textangle=-90, showarrow=True)
    
    fig.update_layout(xaxis_visible=False, yaxis_visible=False, height=600, plot_bgcolor='white', margin=dict(l=50,r=50,t=50,b=50))
    st.plotly_chart(fig, use_container_width=True)

    # --- 7. DETAILED CALCULATION REPORT ---
    st.markdown("---")
    st.subheader("📑 Engineering Verification Report")
    
    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.info(f"**Total Design Shear ($V_{{u}}$ or $V_{{a}}$):** {V_design:,.0f} kg")
        st.write(f"Eccentricity ($e$): {e_total_mm:.1f} mm")
        st.write(f"Max Resultant Force on Bolt: **{V_resultant:,.1f} kg/bolt**")
    
    with col_res2:
        r_shear = (V_resultant * n_bolts) / Cap_bolt_shear
        st.metric("Bolt Group Shear Ratio", f"{r_shear:.2f}", 
                  delta="PASS" if r_shear <= 1.0 else "OVERLOAD", 
                  delta_color="normal" if r_shear <= 1.0 else "inverse")

    with st.expander("แสดงที่มาของแรงและสูตรการคำนวณ (Traceability)"):
        st.latex(fr"V_{{direct}} = V / N = {V_design} / {n_bolts} = {V_dir:,.1f} \text{{ kg}}")
        st.latex(fr"M = V \cdot e = {V_design} \cdot {e_cm} = {V_design * e_cm:,.0f} \text{{ kg-cm}}")
        st.latex(fr"I_p = \sum(x^2 + y^2) = {Ip:.2f} \text{{ cm}}^2")
        st.latex(fr"V_{{resultant}} = \sqrt{{(V_{{dir}} + V_{{ecc,y}})^2 + V_{{ecc,x}}^2}} = {V_total_bolt if 'V_total_bolt' in locals() else V_resultant:,.1f} \text{{ kg}}")
        

    return n_bolts, Cap_bolt_shear
