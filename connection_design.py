import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    
    # ==========================================
    # 1. PARSE CONNECTION TYPE (แกะรหัสจากชื่อที่เลือก)
    # ==========================================
    # ตรวจสอบว่าต้องใช้ m = 1 (Single) หรือ m = 2 (Double)
    is_double_shear = "Double" in conn_type
    shear_planes = 2.0 if is_double_shear else 1.0
    
    # ตรวจสอบว่าเป็นจุดต่อเข้ากับ "เสา" หรือ "คาน" (เพื่อวาดรูปให้ถูก)
    is_beam_to_beam = "Beam to Beam" in conn_type
    support_label = "Primary Beam (Girder)" if is_beam_to_beam else "Column"

    # ==========================================
    # 2. SETUP CALCULATION LOGIC
    # ==========================================
    if is_lrfd:
        method_name = "LRFD"
        # สร้าง Template สูตร LRFD: phi * Rn
        # แสดงผล: phi Rn = 0.75 * ...
        eq_template = lambda Rn: fr"\phi R_n = 0.75 \times {Rn:,.0f}"
        get_capacity = lambda Rn: 0.75 * Rn
    else:
        method_name = "ASD"
        # สร้าง Template สูตร ASD: Rn / Omega
        # แสดงผล: Rn / Omega = ... / 2.00
        eq_template = lambda Rn: fr"\frac{{R_n}}{{\Omega}} = \frac{{{Rn:,.0f}}}{{2.00}}"
        get_capacity = lambda Rn: Rn / 2.00

    # ==========================================
    # 3. INPUTS & GEOMETRY
    # ==========================================
    # แสดงหัวข้อให้เห็นชัดๆ ว่าโปรแกรมรับค่า conn_type มาถูกตัว
    st.markdown(f"### 🔗 Connection Design: **{conn_type}**")
    st.caption(f"Config: {shear_planes} Shear Plane(s) | Support: {support_label}")

    p = section_data
    h_beam = float(p.get('h', 300))
    tw_beam_mm = float(p.get('tw', 8)) 
    Fy, Fu = 2450, 4000  # ksc (SS400)

    # Input Layout
    c1, c2, c3 = st.columns(3)
    with c1:
        n_rows = st.number_input("Bolt Rows (V)", 2, 12, 3)
        n_cols = st.number_input("Bolt Cols (H)", 1, 2, 1)
        t_plate_mm = st.number_input("Plate Thickness (mm)", 6.0, 50.0, 10.0)
    with c2:
        s_v = st.number_input("Vertical Pitch (mm)", 50.0, 150.0, 75.0)
        s_h = st.number_input("Horiz. Pitch (mm)", 0.0, 150.0, 50.0) if n_cols > 1 else 0
        l_edge_v = st.number_input("Vert. Edge (mm)", 30.0, 100.0, 40.0)
    with c3:
        e1_mm = st.number_input("Weld-to-Bolt (e1, mm)", 40.0, 200.0, 60.0)
        l_side = st.number_input("Side Margin (mm)", 30.0, 100.0, 40.0)
        thread_type = st.radio("Thread Condition", ["N (Included)", "X (Excluded)"], index=0)
        # แปลงค่า Radio เป็น N/X
        th_cond = "N" if "N" in thread_type else "X"

    # Pre-calc constants
    d_mm = int(bolt_size[1:])
    d_cm = d_mm / 10
    Ab = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}.get(bolt_size, 3.14)
    dh_cm = (d_mm + 2) / 10
    
    # ==========================================
    # 4. ANALYSIS (Eccentric Check)
    # ==========================================
    n_total = n_rows * n_cols
    plate_h = (n_rows - 1) * s_v + (2 * l_edge_v)
    plate_w = e1_mm + (n_cols - 1) * s_h + l_side
    
    # Elastic Method (Simplified)
    e_total_cm = (e1_mm + (n_cols-1)*s_h/2) / 10
    
    # Inertia
    y_coords = [(r - (n_rows-1)/2) * (s_v/10) for r in range(n_rows)]
    x_coords = [(c - (n_cols-1)/2) * (s_h/10) for c in range(n_cols)]
    Ip = (sum([y**2 for y in y_coords]) * n_cols) + (sum([x**2 for x in x_coords]) * n_rows)
    
    V_dir = V_design / n_total
    V_ecc_x = (V_design * e_total_cm * max([abs(y) for y in y_coords])) / Ip if Ip > 0 else 0
    V_ecc_y = (V_design * e_total_cm * max([abs(x) for x in x_coords])) / Ip if Ip > 0 else 0
    V_res = math.sqrt((V_dir + V_ecc_y)**2 + V_ecc_x**2)

    # ==========================================
    # 5. CAPACITIES
    # ==========================================
    
    # --- SHEAR ---
    bolt_db = {"Grade 8.8 (Standard)": {"N": 3200, "X": 4000}, "A325 (High Strength)": {"N": 3795, "X": 4780}, "A490 (Premium)": {"N": 4920, "X": 6200}}
    # ดึงค่า Fnv ตามเกรดที่เลือก
    base_grade = bolt_grade.split(" (")[0] if "(" in bolt_grade else bolt_grade # Handle naming mismatch
    # Fallback logic if dictionary key mismatch
    if "8.8" in bolt_grade: Fnv = bolt_db["Grade 8.8 (Standard)"][th_cond]
    elif "A325" in bolt_grade: Fnv = bolt_db["A325 (High Strength)"][th_cond]
    else: Fnv = bolt_db["Grade 8.8 (Standard)"][th_cond]

    # สูตรคำนวณ Rn Shear (ใช้ shear_planes ที่แกะมาจาก conn_type)
    Rn_shear = n_total * Fnv * Ab * shear_planes

    # --- BEARING ---
    tw_plate_cm = t_plate_mm / 10
    tw_beam_cm = tw_beam_mm / 10
    t_crit_cm = min(tw_plate_cm, tw_beam_cm) # ใช้ความหนาน้อยสุด
    
    lc_edge = (l_edge_v/10) - (dh_cm/2)
    lc_inner = (s_v/10) - dh_cm
    
    Rn_bear_unit_edge = min(1.2*lc_edge*t_crit_cm*Fu, 2.4*d_cm*t_crit_cm*Fu)
    Rn_bear_unit_inner = min(1.2*lc_inner*t_crit_cm*Fu, 2.4*d_cm*t_crit_cm*Fu)
    
    if n_rows > 2:
        Rn_bear = (n_cols * 2 * Rn_bear_unit_edge) + (n_cols * (n_rows-2) * Rn_bear_unit_inner)
    else:
        Rn_bear = n_total * Rn_bear_unit_edge

    # --- FINAL DESIGN STRENGTH ---
    Design_Shear = get_capacity(Rn_shear)
    Design_Bear = get_capacity(Rn_bear)

    # ==========================================
    # 6. VISUALIZATION (Dynamic Support)
    # ==========================================
    st.divider()
    c_draw, c_calc = st.columns([1, 1.3])
    
    with c_draw:
        st.subheader("📐 Connection Detail")
        fig = go.Figure()
        
        # 1. วาด SUPPORT (Column หรือ Main Beam) ตาม conn_type
        if is_beam_to_beam:
             # วาดรูปแทน Main Beam (สีม่วง)
             fig.add_shape(type="rect", x0=-20, y0=-50, x1=0, y1=plate_h+50, fillcolor="#8e44ad", line_color="black")
             fig.add_annotation(x=-10, y=plate_h/2, text="Main Beam", showarrow=False, textangle=-90, font=dict(color="white"))
        else:
             # วาดรูปแทน Column (สีเทาเข้ม)
             fig.add_shape(type="rect", x0=-40, y0=-50, x1=0, y1=plate_h+50, fillcolor="#2c3e50", line_color="black")
             fig.add_annotation(x=-20, y=plate_h/2, text="Column", showarrow=False, textangle=-90, font=dict(color="white"))

        # 2. วาด Secondary Beam (เส้นประ)
        fig.add_shape(type="rect", x0=5, y0=(plate_h-h_beam)/2, x1=plate_w+50, y1=(plate_h+h_beam)/2, line=dict(color="gray", dash="dash"))
        
        # 3. วาด Plate (สีฟ้า)
        fig.add_shape(type="rect", x0=0, y0=0, x1=plate_w, y1=plate_h, fillcolor="rgba(41, 128, 185, 0.4)", line_color="#2980b9")
        
        # 4. วาด Bolts (จุดสีแดง)
        for r in range(n_rows):
            for c in range(n_cols):
                 fig.add_trace(go.Scatter(x=[e1_mm + c*s_h], y=[l_edge_v + r*s_v], mode='markers', marker=dict(size=10, color='#c0392b')))

        fig.update_layout(height=400, margin=dict(l=10,r=10,t=20,b=20), xaxis_visible=False, yaxis_visible=False)
        st.plotly_chart(fig, use_container_width=True)

    with c_calc:
        st.subheader(f"📝 Calculation Report ({method_name})")
        
        # Section 1: Demand
        with st.expander("1. Force Analysis (Demand)", expanded=True):
            st.write(f"V_design = {V_design:,.0f} kg")
            st.latex(fr"V_{{res}} = {V_res:,.0f} \text{{ kg/bolt}}")

        # Section 2: Shear Check (Dynamic Formula)
        pass_s = (V_res * n_total) <= Design_Shear
        icon_s = "✅" if pass_s else "❌"
        with st.expander(f"2. Bolt Shear {icon_s}", expanded=True):
            st.write(f"Shear Plane ($m$): **{shear_planes:.1f}** ({'Double' if is_double_shear else 'Single'})")
            st.latex(fr"R_n = N \cdot F_{{nv}} \cdot A_b \cdot m")
            st.latex(fr"R_n = {n_total} \cdot {Fnv} \cdot {Ab} \cdot {shear_planes} = {Rn_shear:,.0f}")
            
            # Link จุดสำคัญ: ใช้ Template แสดงสูตรตาม ASD/LRFD
            st.latex(f"{eq_template(Rn_shear)} = \mathbf{{{Design_Shear:,.0f}}} \\text{{ kg}}")
            
            ratio_s = (V_res * n_total) / Design_Shear
            st.metric("Shear Ratio", f"{ratio_s:.2f}", delta_color="inverse" if ratio_s > 1 else "normal")
            

        # Section 3: Bearing Check
        pass_b = V_design <= Design_Bear
        icon_b = "✅" if pass_b else "❌"
        with st.expander(f"3. Bearing Capacity {icon_b}", expanded=True):
            st.latex(fr"R_n = {Rn_bear:,.0f}")
            st.latex(f"{eq_template(Rn_bear)} = \mathbf{{{Design_Bear:,.0f}}} \\text{{ kg}}")
            st.metric("Bearing Ratio", f"{V_design / Design_Bear:.2f}")

    return n_total, Design_Shear
