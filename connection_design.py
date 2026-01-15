import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    # --- 1. การดึงข้อมูลพื้นฐาน (Audit Linkage) ---
    p = section_data
    h_beam = float(p.get('h', 300))
    tw_beam = float(p.get('tw', 8)) 
    Fy, Fu = 2450, 4000  # SS400 (kg/cm2)
    
    st.markdown(f"### ⚙️ Connection Setup & Design ({'LRFD' if is_lrfd else 'ASD'})")
    
    # --- 2. INPUT LAYOUT ---
    c1, c2, c3 = st.columns(3)
    with c1:
        n_rows = st.number_input("จำนวนน็อต (แนวดิ่ง)", 2, 12, 3)
        n_cols = st.number_input("จำนวนน็อต (แนวนอน)", 1, 2, 1)
        t_plate_mm = st.number_input("ความหนาแผ่นประกับ (mm)", 6.0, 40.0, 10.0, 1.0)
    with c2:
        s_v = st.number_input("Vertical Pitch (mm)", 50.0, 150.0, 75.0, 5.0)
        s_h = st.number_input("Horizontal Pitch (mm)", 0.0, 150.0, 50.0, 5.0) if n_cols > 1 else 0
        l_edge_v = st.number_input("Vertical Edge (mm)", 30.0, 100.0, 40.0, 5.0)
    with c3:
        e1_mm = st.number_input("รอยเชื่อมถึงน็อตแถวแรก (mm)", 40.0, 200.0, 60.0, 5.0)
        l_side = st.number_input("Side Margin (mm)", 30.0, 100.0, 40.0, 5.0)
        thread_type = st.radio("Thread Position", ["N", "X"], horizontal=True)

    # --- 3. การประกาศตัวแปรเรขาคณิต (Sequence Check) ---
    d_mm = int(bolt_size[1:])
    d_cm = d_mm / 10
    tw_cm = t_plate_mm / 10
    tw_beam_cm = tw_beam / 10
    Ab = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}.get(bolt_size, 3.14)
    dh_cm = (d_mm + 2) / 10
    
    n_total = n_rows * n_cols
    plate_h = (n_rows - 1) * s_v + (2 * l_edge_v)
    plate_w = e1_mm + (n_cols - 1) * s_h + l_side

    # --- 4. การตั้งค่าตัวแปรตามวิธีออกแบบ (LRFD vs ASD) ---
    # ส่วนนี้จะทำให้ข้อความในสูตร LaTeX เปลี่ยนตามปุ่มที่กด
    if is_lrfd:
        phi_val, omega_val = 0.75, 1.00
        m_tag = "LRFD"
        symbol = r"\phi R_n"
        calc_step = rf"0.75 \times R_n"
    else:
        phi_val, omega_val = 1.00, 2.00
        m_tag = "ASD"
        symbol = r"R_n / \Omega"
        calc_step = rf"R_n / 2.00"

    # --- 5. การวิเคราะห์แรงเยื้องศูนย์ (Eccentricity) ---
    e_total_cm = (e1_mm + (n_cols-1)*s_h/2) / 10
    y_coords = [(r - (n_rows-1)/2) * (s_v/10) for r in range(n_rows)]
    x_coords = [(c - (n_cols-1)/2) * (s_h/10) for c in range(n_cols)]
    Ip = (sum([y**2 for y in y_coords]) * n_cols) + (sum([x**2 for x in x_coords]) * n_rows)
    
    V_dir = V_design / n_total
    V_ecc_x = (V_design * e_total_cm * max([abs(y) for y in y_coords])) / Ip if Ip > 0 else 0
    V_ecc_y = (V_design * e_total_cm * max([abs(x) for x in x_coords])) / Ip if Ip > 0 else 0
    V_res = math.sqrt((V_dir + V_ecc_y)**2 + V_ecc_x**2)

    # --- 6. การคำนวณกำลังรับแรง (Capacities) ---
    # Bolt Shear
    bolt_map = {"Grade 8.8 (Standard)": {"N": 3200, "X": 4000}, "A325 (High Strength)": {"N": 3795, "X": 4780}}
    Fnv = bolt_map.get(bolt_grade, bolt_map["Grade 8.8 (Standard)"]).get(thread_type)
    m_shear = 2.0 if "Double" in conn_type else 1.0
    Rn_shear = n_total * Fnv * Ab * m_shear
    Capacity_Shear = (phi_val * Rn_shear) / omega_val

    # Bearing
    t_min_cm = min(tw_cm, tw_beam_cm)
    lc_edge = (l_edge_v/10) - (dh_cm/2)
    lc_inner = (s_v/10) - dh_cm
    Rn_bear = (n_cols * 2 * min(1.2*lc_edge*t_min_cm*Fu, 2.4*d_cm*t_min_cm*Fu)) + \
              (n_cols * (n_rows-2) * min(1.2*lc_inner*t_min_cm*Fu, 2.4*d_cm*t_min_cm*Fu))
    Capacity_Bear = (phi_val * Rn_bear) / omega_val

    # --- 7. รูปแสดงรายละเอียดเหล็ก (Enhanced Detailing) ---
    st.divider()
    st.subheader(f"🎨 รายละเอียดการจัดวางและขนาดแผ่นเหล็ก ({m_tag})")
    fig = go.Figure()
    # หน้าเสา (Column Face)
    fig.add_shape(type="rect", x0=-40, y0=-50, x1=0, y1=plate_h+50, fillcolor="#2c3e50", line_color="black")
    fig.add_annotation(x=-20, y=plate_h/2, text="COLUMN FACE", textangle=-90, font=dict(color="white"))
    # แผ่นประกับ (Fin Plate)
    fig.add_shape(type="rect", x0=0, y0=0, x1=plate_w, y1=plate_h, fillcolor="rgba(52, 152, 219, 0.2)", line_color="#2980b9", line_width=2)
    # แนวน็อต (Bolts)
    for r in range(n_rows):
        for c in range(n_cols):
            bx, by = e1_mm + c*s_h, l_edge_v + r*s_v
            fig.add_trace(go.Scatter(x=[bx], y=[by], mode='markers+text', text=[f"B{r+1}"], marker=dict(size=14, color='#e74c3c')))
    
    fig.update_layout(height=500, plot_bgcolor='white', xaxis_visible=False, yaxis_visible=False, margin=dict(l=50,r=50,t=50,b=50))
    st.plotly_chart(fig, use_container_width=True)

    # --- 8. รายการคำนวณแบบ DYNAMIC (ปรับเปลี่ยนตาม ASD/LRFD ทันที) ---
    st.title(f"📄 รายการคำนวณละเอียด ({m_tag})")
    st.success(f"**ขนาดแผ่นเหล็ก:** หนา {t_plate_mm} mm x กว้าง {plate_w:.0f} mm x สูง {plate_h:.0f} mm")

    with st.expander("1. การวิเคราะห์แรงกระทำต่อกลุ่มน็อต (Demand Analysis)", expanded=True):
        st.write(f"วิเคราะห์แรงที่น็อตตัวที่วิกฤตที่สุด โดยรวมผลจากความเยื้องศูนย์ $e = {e_total_cm:.2f}$ cm")
        st.latex(fr"V_{{direct}} = {V_design} / {n_total} = {V_dir:,.1f} \text{{ kg}}")
        st.latex(fr"V_{{resultant}} = \sqrt{{(V_{{dir}} + V_{{ecc,y}})^2 + V_{{ecc,x}}^2}} = {V_res:,.1f} \text{{ kg/bolt}}")

    with st.expander(f"2. ตรวจสอบกำลังรับแรงเฉือนของน็อต (Bolt Shear - {m_tag})"):
        st.write(f"ใช้กำลังเฉือน $F_{{nv}} = {Fnv}$ kg/cm² | จำนวนหน้าเฉือน $m = {m_shear}$")
        st.latex(fr"R_n = N_{{bolt}} \times F_{{nv}} \times A_b \times m = {Rn_shear:,.0f} \text{{ kg}}")
        # บรรทัดนี้จะเปลี่ยนสูตรตามวิธีที่เลือกทันที
        st.latex(fr"{symbol} = {calc_step} = {Capacity_Shear:,.0f} \text{{ kg}}")
        ratio_s = (V_res * n_total) / Capacity_Shear
        st.metric("Demand/Capacity Ratio", f"{ratio_s:.2f}", delta="PASS" if ratio_s <= 1 else "FAIL")

    with st.expander(f"3. ตรวจสอบกำลังบดอัดและการฉีกขาด (Bearing & Tear-out - {m_tag})"):
        st.write(f"วิเคราะห์บนความหนาเหล็กที่บางกว่า $t_{{min}} = {t_min_cm*10:.1f}$ mm")
        st.latex(fr"R_n = \sum \min(1.2 L_c t F_u, 2.4 d t F_u) = {Rn_bear:,.0f} \text{{ kg}}")
        # บรรทัดนี้จะเปลี่ยนสูตรตามวิธีที่เลือกทันที
        st.latex(fr"{symbol} = {calc_step} = {Capacity_Bear:,.0f} \text{{ kg}}")
        ratio_b = V_design / Capacity_Bear
        st.metric("Demand/Capacity Ratio", f"{ratio_b:.2f}", delta="PASS" if ratio_b <= 1 else "FAIL")

    return n_total, Capacity_Shear
