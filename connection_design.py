import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    # --- 1. DATA PREPARATION & AUDIT ---
    # ดึงข้อมูลหน้าตัดและความแข็งวัสดุ (SS400)
    p = section_data
    h_beam = float(p.get('h', 300))
    tw_beam_mm = float(p.get('tw', 8)) 
    Fy, Fu = 2450, 4000  # ksc
    
    # --- 2. DYNAMIC INPUT UI (จัดวาง Layout แบบมืออาชีพ) ---
    st.markdown(f"### 🛠️ Connection Configuration: **{conn_type}**")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        n_rows = st.number_input("Bolt Rows (Vertical)", 2, 12, 3, help="จำนวนแถวน็อตในแนวดิ่ง")
        n_cols = st.number_input("Bolt Columns (Horizontal)", 1, 2, 1, help="จำนวนแถวน็อตในแนวนอน")
        t_plate_mm = st.number_input("Plate Thickness (mm)", 6.0, 50.0, 10.0, 1.0)
    with c2:
        s_v = st.number_input("Vertical Pitch (s_v, mm)", 50.0, 150.0, 75.0, 5.0)
        s_h = st.number_input("Horizontal Pitch (s_h, mm)", 0.0, 150.0, 50.0, 5.0) if n_cols > 1 else 0
        l_edge_v = st.number_input("Edge Distance (Lev, mm)", 30.0, 100.0, 40.0, 5.0)
    with c3:
        e1_mm = st.number_input("Weld to Bolt (e1, mm)", 40.0, 200.0, 60.0, 5.0)
        l_side = st.number_input("Side Margin (Les, mm)", 30.0, 100.0, 40.0, 5.0)
        thread_type = st.radio("Thread Condition", ["N", "X"], horizontal=True, help="N=รวมเกลียวในระนาบเฉือน, X=ไม่รวม")

    # --- 3. CRITICAL GEOMETRY CALCULATION ---
    # แปลงหน่วยและเตรียมตัวแปร "ทั้งหมด" ก่อนคำนวณกำลัง
    d_mm = int(bolt_size[1:])
    d_cm = d_mm / 10
    Ab = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}.get(bolt_size, 3.14)
    tw_plate_cm = t_plate_mm / 10
    tw_beam_cm = tw_beam_mm / 10
    dh_cm = (d_mm + 2) / 10       # Hole diameter
    
    # ขนาดแผ่นเหล็กจริง
    plate_h = (n_rows - 1) * s_v + (2 * l_edge_v)
    plate_w = e1_mm + (n_cols - 1) * s_h + l_side
    n_total = n_rows * n_cols

    # --- 4. THE CORE FIX: DYNAMIC LATEX TEMPLATES ---
    # หัวใจสำคัญของการแก้ปัญหา: สร้าง String Template ตามโหมดที่เลือก
    if is_lrfd:
        # LRFD: คูณด้วย 0.75
        method_label = "LRFD (Load & Resistance Factor Design)"
        phi_val = 0.75
        omega_val = 1.00 # ไม่ใช้ใน LRFD
        
        # สร้างก้อน LaTeX สำหรับการแสดงผลแบบคูณ
        # ผลลัพธ์: \phi R_n = 0.75 x Rn
        latex_template = lambda Rn_val: fr"\phi R_n = {phi_val} \times {Rn_val:,.0f}" 
        design_capacity = lambda Rn: phi_val * Rn
        
    else:
        # ASD: หารด้วย 2.00
        method_label = "ASD (Allowable Strength Design)"
        phi_val = 1.00 # ไม่ใช้ใน ASD
        omega_val = 2.00
        
        # สร้างก้อน LaTeX สำหรับการแสดงผลแบบเศษส่วน
        # ผลลัพธ์: Rn / \Omega = Rn / 2.00
        latex_template = lambda Rn_val: fr"\frac{{R_n}}{{\Omega}} = \frac{{{Rn_val:,.0f}}}{{{omega_val:.2f}}}"
        design_capacity = lambda Rn: Rn / omega_val

    # --- 5. FORCE ANALYSIS (ELASTIC METHOD) ---
    e_total_cm = (e1_mm + (n_cols-1)*s_h/2) / 10
    # Centroid & Inertia Calculation
    y_coords = [(r - (n_rows-1)/2) * (s_v/10) for r in range(n_rows)]
    x_coords = [(c - (n_cols-1)/2) * (s_h/10) for c in range(n_cols)]
    Ip = (sum([y**2 for y in y_coords]) * n_cols) + (sum([x**2 for x in x_coords]) * n_rows)
    
    # Resultant Force Calculation
    V_dir = V_design / n_total
    V_ecc_x = (V_design * e_total_cm * max([abs(y) for y in y_coords])) / Ip if Ip > 0 else 0
    V_ecc_y = (V_design * e_total_cm * max([abs(x) for x in x_coords])) / Ip if Ip > 0 else 0
    V_res = math.sqrt((V_dir + V_ecc_y)**2 + V_ecc_x**2)

    # --- 6. NOMINAL STRENGTH CALCULATIONS (Rn) ---
    
    # 6.1 Bolt Shear (Rn)
    shear_planes = 2.0 if "Double" in conn_type else 1.0
    bolt_map = {"Grade 8.8 (Standard)": {"N": 3200, "X": 4000}, "A325 (High Strength)": {"N": 3795, "X": 4780}}
    Fnv = bolt_map.get(bolt_grade, bolt_map["Grade 8.8 (Standard)"]).get(thread_type)
    Rn_shear = n_total * Fnv * Ab * shear_planes
    
    # 6.2 Bearing (Rn) - เช็คตัวที่บางที่สุด (Critical Element)
    t_critical_cm = min(tw_plate_cm, tw_beam_cm)
    lc_edge = (l_edge_v/10) - (dh_cm/2)
    lc_inner = (s_v/10) - dh_cm
    # Bearing formula per bolt summation
    Rn_bear = (n_cols * 2 * min(1.2*lc_edge*t_critical_cm*Fu, 2.4*d_cm*t_critical_cm*Fu)) + \
              (n_cols * (n_rows-2) * min(1.2*lc_inner*t_critical_cm*Fu, 2.4*d_cm*t_critical_cm*Fu))

    # --- 7. FINAL DESIGN CAPACITIES (ใช้ฟังก์ชัน Dynamic ที่สร้างไว้) ---
    Design_Shear = design_capacity(Rn_shear)
    Design_Bear = design_capacity(Rn_bear)

    # --- 8. VISUALIZATION & REPORT ---
    st.divider()
    
    # ส่วนแสดงผลกราฟิก
    col_draw, col_calc = st.columns([1, 1.5])
    
    with col_draw:
        st.subheader("📐 Drawing Detail")
        fig = go.Figure()
        # Shapes: Column, Beam(dashed), Plate
        fig.add_shape(type="rect", x0=-40, y0=-50, x1=0, y1=plate_h+50, fillcolor="#2c3e50", line_color="black") # Column
        fig.add_shape(type="rect", x0=0, y0=0, x1=plate_w, y1=plate_h, fillcolor="rgba(41, 128, 185, 0.3)", line_color="#2980b9") # Plate
        fig.add_shape(type="rect", x0=5, y0=(plate_h-h_beam)/2, x1=plate_w+50, y1=(plate_h+h_beam)/2, line=dict(color="gray", dash="dash")) # Beam Web
        
        # Bolt holes
        for r in range(n_rows):
            for c in range(n_cols):
                 fig.add_trace(go.Scatter(x=[e1_mm + c*s_h], y=[l_edge_v + r*s_v], mode='markers', marker=dict(size=12, color='#c0392b')))
        
        fig.update_layout(height=400, margin=dict(l=20,r=20,t=20,b=20), xaxis_visible=False, yaxis_visible=False)
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Plate Size: {t_plate_mm}x{plate_w:.0f}x{plate_h:.0f} mm")

    with col_calc:
        st.subheader(f"📝 Calculation Report: {method_label}")
        
        # --- Section 1: Demand ---
        with st.expander("1. Force Analysis (Demand)", expanded=True):
            st.write(f"V_design = {V_design:,.0f} kg | Eccentricity (e) = {e_total_cm:.2f} cm")
            st.latex(fr"V_{{res}} = \sqrt{{(V_{{dir}} + V_{{ecc,y}})^2 + V_{{ecc,x}}^2}} = \mathbf{{{V_res:,.0f}}} \text{{ kg/bolt}}")
            st.progress(min(V_res * n_total / Design_Shear, 1.0))

        # --- Section 2: Bolt Shear ---
        with st.expander(f"2. Bolt Shear Capacity ({'PASS' if (V_res*n_total) <= Design_Shear else 'FAIL'})", expanded=True):
            st.latex(fr"R_n = {n_total} \times {Fnv} \times {Ab} \times {shear_planes} = {Rn_shear:,.0f} \text{{ kg}}")
            # *** จุดทีเด็ด: เรียกใช้ Template Dynamic ตรงนี้ ***
            st.latex(f"{latex_template(Rn_shear)} = \mathbf{{{Design_Shear:,.0f}}} \\text{{ kg}}")
            
            ratio_s = (V_res * n_total) / Design_Shear
            st.caption(f"Demand / Capacity Ratio = {ratio_s:.2f}")

        # --- Section 3: Bearing ---
        with st.expander(f"3. Bearing Capacity ({'PASS' if V_design <= Design_Bear else 'FAIL'})", expanded=True):
            st.write(f"Check at min thickness ($t_{{min}}$) = {t_critical_cm*10:.1f} mm")
            st.latex(fr"R_n = \sum \min(...) = {Rn_bear:,.0f} \text{{ kg}}")
             # *** จุดทีเด็ด: เรียกใช้ Template Dynamic ตรงนี้ ***
            st.latex(f"{latex_template(Rn_bear)} = \mathbf{{{Design_Bear:,.0f}}} \\text{{ kg}}")
            
            ratio_b = V_design / Design_Bear
            st.caption(f"Demand / Capacity Ratio = {ratio_b:.2f}")
            
    return n_total, Design_Shear
