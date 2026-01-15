import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    # --- 1. INITIAL DATA LINKAGE (ดึงข้อมูลจากหน้าหลัก) ---
    p = section_data
    h_beam = float(p.get('h', 300))
    tw_beam = float(p.get('tw', 8)) # ความหนาเอวคาน (mm)
    Fy, Fu = 2450, 4000  # มาตรฐานเหล็ก SS400 (kg/cm2)
    
    st.markdown("### ⚙️ Connection & Member Setup")
    
    # --- 2. LAYOUT & PLATE INPUTS ---
    c1, c2, c3 = st.columns(3)
    with c1:
        n_rows = st.number_input("จำนวนน็อต (แนวดิ่ง)", 2, 12, 3)
        n_cols = st.number_input("จำนวนน็อต (แนวนอน)", 1, 2, 1)
        t_plate_mm = st.number_input("ความหนาแผ่นประกับ (t_p, mm)", 6.0, 40.0, 10.0, 1.0)
    with c2:
        s_v = st.number_input("Vertical Pitch (s_v, mm)", 50.0, 150.0, 75.0, 5.0)
        s_h = st.number_input("Horizontal Pitch (s_h, mm)", 0.0, 150.0, 50.0, 5.0) if n_cols > 1 else 0
        l_edge_v = st.number_input("Vertical Edge (l_ev, mm)", 30.0, 100.0, 40.0, 5.0)
    with c3:
        e1_mm = st.number_input("รอยเชื่อมถึงน็อตแถวแรก (e1, mm)", 40.0, 200.0, 60.0, 5.0)
        l_side = st.number_input("ระยะขอบข้างแผ่น (mm)", 30.0, 100.0, 40.0, 5.0)
        thread_type = st.radio("Thread Condition", ["N", "X"], horizontal=True)

    # --- 3. CORE VARIABLES (DECLARED BEFORE CALCULATIONS) ---
    d_mm = int(bolt_size[1:])
    d_cm = d_mm / 10
    tw_cm = t_plate_mm / 10
    tw_beam_cm = tw_beam / 10 # <--- แก้ไขจุดนี้ให้ชื่อตัวแปรชัดเจน
    Ab = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}.get(bolt_size, 3.14)
    dh_cm = (d_mm + 2) / 10
    dh_eff_cm = dh_cm + 0.2
    
    n_total = n_rows * n_cols
    plate_h = (n_rows - 1) * s_v + (2 * l_edge_v)
    plate_w = e1_mm + (n_cols - 1) * s_h + l_side

    # --- 4. DESIGN METHOD LINKAGE (ASD vs LRFD) ---
    if is_lrfd:
        phi, omega = 0.75, 1.00
        m_tag, sym = "LRFD", r"\phi R_n"
    else:
        phi, omega = 1.00, 2.00
        m_tag, sym = "ASD", r"R_n / \Omega"

    # --- 5. SHEAR PLANE LINKAGE (Single vs Double Shear) ---
    shear_multiplier = 2.0 if "Double" in conn_type else 1.0

    # --- 6. FORCE ANALYSIS (ECCENTRICITY) ---
    e_total_cm = (e1_mm + (n_cols-1)*s_h/2) / 10
    y_coords = [(r - (n_rows-1)/2) * (s_v/10) for r in range(n_rows)]
    x_coords = [(c - (n_cols-1)/2) * (s_h/10) for c in range(n_cols)]
    Ip = (sum([y**2 for y in y_coords]) * n_cols) + (sum([x**2 for x in x_coords]) * n_rows)
    
    V_dir = V_design / n_total
    V_ecc_x = (V_design * e_total_cm * max([abs(y) for y in y_coords])) / Ip if Ip > 0 else 0
    V_ecc_y = (V_design * e_total_cm * max([abs(x) for x in x_coords])) / Ip if Ip > 0 else 0
    V_res = math.sqrt((V_dir + V_ecc_y)**2 + V_ecc_x**2)

    # --- 7. CAPACITY CALCULATIONS ---
    # 7.1 Bolt Shear
    bolt_map = {"Grade 8.8 (Standard)": {"N": 3200, "X": 4000}, "A325 (High Strength)": {"N": 3795, "X": 4780}}
    Fnv = bolt_map.get(bolt_grade, bolt_map["Grade 8.8 (Standard)"]).get(thread_type)
    Rn_shear_total = n_total * Fnv * Ab * shear_multiplier
    Cap_shear = (phi * Rn_shear_total) / omega

    # 7.2 Bearing & Tear-out (เช็คทั้งแผ่นเหล็กและเอวคาน)
    t_min_cm = min(tw_cm, tw_beam_cm)
    lc_edge = (l_edge_v/10) - (dh_cm/2)
    lc_inner = (s_v/10) - dh_cm
    Rn_bear = (n_cols * 2 * min(1.2*lc_edge*t_min_cm*Fu, 2.4*d_cm*t_min_cm*Fu)) + \
              (n_cols * (n_rows-2) * min(1.2*lc_inner*t_min_cm*Fu, 2.4*d_cm*t_min_cm*Fu))
    Cap_bear = (phi * Rn_bear) / omega

    # --- 8. DETAILED DRAWING ---
    st.divider()
    st.subheader(f"🎨 Structural Layout Detail ({conn_type})")
    fig = go.Figure()
    # Drawing: Column (Dark Gray)
    fig.add_shape(type="rect", x0=-40, y0=-50, x1=0, y1=plate_h+50, fillcolor="#2c3e50")
    fig.add_annotation(x=-20, y=plate_h/2, text="COLUMN FACE", textangle=-90, font=dict(color="white"))
    # Drawing: Fin Plate (Light Blue)
    fig.add_shape(type="rect", x0=0, y0=0, x1=plate_w, y1=plate_h, fillcolor="rgba(52, 152, 219, 0.2)", line_color="#2980b9")
    # Bolt Markers & Labels
    for r in range(n_rows):
        for c in range(n_cols):
            bx, by = e1_mm + c*s_h, l_edge_v + r*s_v
            fig.add_trace(go.Scatter(x=[bx], y=[by], mode='markers+text', text=[f"B{r+1}"], marker=dict(size=14, color='#e74c3c')))
    
    # Dimension Lines (e1, pitch)
    fig.add_annotation(x=e1_mm/2, y=-25, text=f"e1={e1_mm}", showarrow=True)
    fig.add_annotation(x=plate_w+35, y=l_edge_v+s_v/2, text=f"Pitch={s_v}", textangle=90, showarrow=True)
    fig.update_layout(height=550, plot_bgcolor='white', xaxis_visible=False, yaxis_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # --- 9. FULL CALCULATION REPORT ---
    st.title(f"📄 Detailed Calculation Report ({m_tag})")
    st.success(f"**Plate Order Size:** {t_plate_mm}mm x {plate_w:.0f}mm x {plate_h:.0f}mm")

    with st.expander("1. Load Distribution Analysis (Demand)", expanded=True):
        st.write(f"V_design = {V_design:,.0f} kg")
        st.latex(fr"V_{{direct/bolt}} = V / N = {V_design} / {n_total} = {V_dir:,.1f} \text{{ kg}}")
        st.latex(fr"V_{{res/bolt}} = \sqrt{{(V_{{dir}} + V_{{ecc,y}})^2 + V_{{ecc,x}}^2}} = {V_res:,.1f} \text{{ kg}}")
        st.caption("แรงวิกฤตต่อน็อต 1 ตัวถูกคำนวณจากแรงเฉือนแนวดิ่งรวมกับแรงบิดจากระยะเยื้องศูนย์")

    with st.expander(f"2. Bolt Shear Strength (AISC J3.6)"):
        st.latex(fr"R_n = N \cdot F_{{nv}} \cdot A_b \cdot m = {n_total} \cdot {Fnv} \cdot {Ab} \cdot {shear_multiplier} = {Rn_shear_total:,.0f} \text{{ kg}}")
        st.latex(fr"{sym} = {Cap_shear:,.0f} \text{{ kg}}")
        st.write(f"**Ratio (Shear):** {(V_res * n_total) / Cap_shear:.2f}")

    with st.expander(f"3. Bearing & Tear-out Capacity (AISC J3.10)"):
        st.write(f"Check based on $t_{{min}}$ ({t_min_cm*10:.1f} mm) between Plate and Beam Web")
        st.latex(fr"R_n = \sum \min(1.2 L_c t F_u, 2.4 d t F_u) = {Rn_bear:,.0f} \text{{ kg}}")
        st.latex(fr"{sym} = {Cap_bear:,.0f} \text{{ kg}}")
        st.write(f"**Ratio (Bearing):** {V_design / Cap_bear:.2f}")

    return n_total, Cap_shear
