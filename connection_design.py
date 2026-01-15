import streamlit as st
import drawing_utils as du 
import calculation_report as calc 

# --- 🆕 DATABASE วัสดุ ---
STEEL_GRADES = {
    "A36 (ASTM)":  {"Fy": 250, "Fu": 400},
    "SS400 (JIS)": {"Fy": 245, "Fu": 400},
    "SM520 (JIS)": {"Fy": 355, "Fu": 520},
    "A572 Gr.50":  {"Fy": 345, "Fu": 450}
}

BOLT_GRADES = {
    "A325 (ASTM)": {"Fnv": 372},   # Shear Strength (N)
    "A490 (ASTM)": {"Fnv": 469},
    "Gr. 8.8 (ISO)": {"Fnv": 375}, # approx 0.6 * 800 * reduction
    "F10T (JIS)":  {"Fnv": 380}    # Common practice
}

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade_input, T_design=0): 
    # bolt_grade_input ของเดิมอาจจะไม่ได้ใช้แล้ว เพราะเราจะเลือกใหม่ในนี้

    st.markdown(f"### 📐 Design Detail: **{conn_type}**")
    
    # =========================================================================
    # 1. INPUTS
    # =========================================================================
    c1, c2, c3 = st.columns(3)
    d_mm = int(bolt_size[1:])
    
    with c1:
        st.caption("🔩 Bolt Config")
        # 🆕 เลือกเกรดน็อต
        selected_bolt_grade = st.selectbox("Bolt Grade", list(BOLT_GRADES.keys()), index=0)
        n_rows = st.number_input("Rows", 2, 20, 3)
        n_cols = st.number_input("Cols", 1, 4, 2)
    
    with c2:
        st.caption("📏 Spacing (mm)")
        min_pitch = 3 * d_mm
        s_v = st.number_input("Pitch V", float(min_pitch), 300.0, float(max(75, min_pitch)))
        s_h = st.number_input("Pitch H", float(min_pitch), 150.0, float(max(60, min_pitch)))
        
    with c3:
        st.caption("🧱 Plate & Material")
        # 🆕 เลือกเกรดเหล็ก
        selected_steel_grade = st.selectbox("Plate Grade", list(STEEL_GRADES.keys()), index=0)
        t_plate = st.number_input("Thickness", 6.0, 40.0, 10.0)
        weld_size = st.selectbox("Weld Size (mm)", [4, 6, 8, 10, 12], index=1)
        e1_mm = st.number_input("Gap to Bolt (e1)", 10.0, 100.0, 50.0)

    # ดึงค่า Property จาก Database
    fy_val = STEEL_GRADES[selected_steel_grade]["Fy"]
    fu_val = STEEL_GRADES[selected_steel_grade]["Fu"]
    fnv_val = BOLT_GRADES[selected_bolt_grade]["Fnv"]

    st.divider()
    
    # ... (ส่วน Code คำนวณขนาดเพลท และ Drawing เหมือนเดิมเป๊ะ ไม่ต้องแก้) ...
    # ... (ก๊อปปี้ส่วน Plate Dimensions, Data Packaging, Drawing มาวางตรงนี้) ...

    # --- ส่วน Custom Plate Dimensions (เหมือนเดิม) ---
    st.markdown("##### 📏 Plate Dimensions (Customizable)")
    c4, c5 = st.columns(2)
    req_h = (n_rows - 1) * s_v + 80 
    req_w = e1_mm + (n_cols - 1) * s_h + 40
    with c4:
        plate_h = st.number_input(f"Plate Height (Min {req_h:.0f})", min_value=float(req_h), value=float(req_h), step=10.0)
    with c5:
        plate_w = st.number_input(f"Plate Width (Min {req_w:.0f})", min_value=float(req_w), value=float(req_w), step=5.0)

    # --- Data Packaging (เหมือนเดิม แต่เพิ่ม weld_size) ---
    real_lv = (plate_h - (n_rows - 1) * s_v) / 2
    l_side = plate_w - (e1_mm + (n_cols - 1) * s_h)

    beam_data = {
        'h': float(section_data.get('h', 350)), 
        'b': float(section_data.get('b', 175)), 
        'tf': float(section_data.get('tf', 11)), 
        'tw': float(section_data.get('tw', 7))
    }
    plate_data = {
        'h': plate_h, 'w': plate_w, 't': t_plate, 
        'e1': e1_mm, 'lv': real_lv, 'l_side': l_side,
        'weld_size': weld_size,
        'Fy': fy_val, 'Fu': fu_val # 🆕 ส่งค่า Material Property ไปด้วย
    }
    bolt_data = {
        'd': d_mm, 'rows': n_rows, 'cols': n_cols, 
        's_v': s_v, 's_h': s_h,
        'Fnv': fnv_val # 🆕 ส่งค่า Bolt Strength ไปด้วย
    }

    # ... (Drawing Part เหมือนเดิม) ...
    # ...

    # --- 4. CALCULATION REPORT ---
    st.divider()
    st.markdown("### 🧮 Calculation Results")
    
    report_markdown = calc.generate_report(
        V_load=V_design,
        beam=beam_data,
        plate=plate_data,
        bolts=bolt_data,
        is_lrfd=is_lrfd,
        material_grade=selected_steel_grade, # ส่งชื่อเกรดไปโชว์
        bolt_grade=selected_bolt_grade       # ส่งชื่อเกรดไปโชว์
    )
    
    with st.expander("📄 Click to view full calculation details", expanded=True):
        st.markdown(report_markdown, unsafe_allow_html=True)

    return n_rows*n_cols, 10000
