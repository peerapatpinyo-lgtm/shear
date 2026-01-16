# connection_design.py (V13 - Final Fix - Integrated Calculation)
import math
import streamlit as st
import calculation_report as calc_rep  # [Fix #1] Import โมดูลคำนวณที่ถูกต้อง

# พยายาม Import drawing_utils และตรวจสอบ Error
try:
    import drawing_utils as drw
    DRAWING_AVAILABLE = True
except Exception as e:
    DRAWING_AVAILABLE = False
    DRAWING_ERROR = str(e)

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, mat_grade="A36"):
    # [Fix #1 Update] เพิ่ม parameter mat_grade เพื่อรับค่าเกรดเหล็กจาก app.py
    st.subheader(f"🔩 Connection Design: {conn_type}")
    
    # 1. จัดการข้อมูล Bolt Size (M16, M20 -> 16, 20)
    try:
        d = int(''.join(filter(str.isdigit, bolt_size)))
    except:
        d = 20

    # 2. รับ Input จากผู้ใช้ (จัดกลุ่มให้ตรงกับ Drawing Utils)
    col1, col2 = st.columns(2)
    with col1:
        t_plate = st.number_input("Plate Thickness (mm)", min_value=1, value=9)
        h_plate = st.number_input("Plate Height (mm)", min_value=50, value=200)
        weld_size = st.number_input("Weld Size (mm)", min_value=3, value=6)
        e1 = st.number_input("Edge distance from Col (e1) (mm)", min_value=10, value=40)
    
    with col2:
        bolt_rows = st.number_input("Number of Rows", min_value=1, value=3)
        bolt_cols = st.number_input("Number of Columns", min_value=1, value=1)
        s_v = st.number_input("Vertical Spacing (s_v) (mm)", min_value=10, value=75)
        s_h = st.number_input("Horizontal Spacing (s_h) (mm)", min_value=0, value=60)
        l_side = st.number_input("Edge distance to Beam end (mm)", min_value=10, value=40)

    # 3. เตรียม Material & Bolt Properties
    bolt_props = {"A325 (High Strength)": 372, "Grade 8.8 (Standard)": 320, "A490 (Premium)": 496}
    fnv = bolt_props.get(bolt_grade, 372)
    
    # คำนวณความกว้าง Plate อัตโนมัติ (สำคัญมากสำหรับการวาดรูป)
    w_plate = e1 + (max(0, bolt_cols - 1) * s_h) + l_side

    # 4. สร้าง Dictionary ให้ตรงกับ drawing_utils.py เป๊ะๆ
    plate_data = {
        't': t_plate, 'h': h_plate, 'w': w_plate,
        'lv': 40, 'e1': e1, 'l_side': l_side, 
        'weld_size': weld_size, 'Fy': 250, 'Fu': 400
    }
    
    bolts_data = {
        'd': d, 'rows': bolt_rows, 'cols': bolt_cols,
        's_v': s_v, 's_h': s_h, 'Fnv': fnv
    }

    # 5. ส่วนแสดงผล DRAWING (ต้องขึ้นก่อน Report)
    if DRAWING_AVAILABLE:
        st.divider()
        st.subheader("🎨 Engineering Drawing (3 Views)")
        
        # จัดเตรียมข้อมูล Beam
        beam_draw = {
            'h': section_data['h'], 'b': section_data['b'], 
            'tf': section_data['tf'], 'tw': section_data['tw']
        }
        
        # แสดงผล 3 มุม
        c_drw1, c_drw2 = st.columns(2)
        with c_drw1:
            st.plotly_chart(drw.create_plan_view(beam_draw, plate_data, bolts_data), use_container_width=True)
            st.plotly_chart(drw.create_side_view(beam_draw, plate_data, bolts_data), use_container_width=True)
        with c_drw2:
            st.plotly_chart(drw.create_front_view(beam_draw, plate_data, bolts_data), use_container_width=True)
    else:
        st.error(f"❌ Drawing Module Error: {DRAWING_ERROR}")

    # 6. ส่วนคำนวณและสร้าง Report [Fix #1]
    V_load_kn = V_design / 100
    
    # เรียกใช้ฟังก์ชันจาก calculation_report.py แทนฟังก์ชันภายใน
    report_md = calc_rep.generate_report(
        V_load=V_load_kn, 
        beam=section_data, 
        plate=plate_data, 
        bolts=bolts_data, 
        is_lrfd=is_lrfd,
        material_grade=mat_grade,
        bolt_grade=bolt_grade
    )
    
    st.markdown(report_md, unsafe_allow_html=True)
    
    return (bolt_rows * bolt_cols), V_load_kn
