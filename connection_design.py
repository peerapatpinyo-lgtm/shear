# connection_design.py (V14 - UI Layout Improvement)
import math
import streamlit as st
import calculation_report as calc_rep

try:
    import drawing_utils as drw
    DRAWING_AVAILABLE = True
except Exception as e:
    DRAWING_AVAILABLE = False
    DRAWING_ERROR = str(e)

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, mat_grade="A36"):
    
    # --- Header Section ---
    st.markdown(f"### 🔩 Connection Design: {conn_type}")
    st.markdown("---") # เส้นขีดคั่น

    # 1. จัดการข้อมูล Bolt Size (แปลง text เป็น int)
    try:
        d = int(''.join(filter(str.isdigit, bolt_size)))
    except:
        d = 20

    # =========================================================================
    # ✨ UI IMPROVEMENT ZONE: จัดกลุ่ม Input ใหม่
    # =========================================================================
    
    # --- GROUP 1: Plate Geometry (ขนาดแผ่นเหล็ก) ---
    st.markdown("#### 1️⃣ Plate Configuration (ขนาดแผ่นเหล็ก)")
    c1, c2, c3 = st.columns(3)
    with c1:
        t_plate = st.number_input("Thickness (mm)", min_value=6, value=9, step=1, help="ความหนาแผ่นเหล็ก (t)")
    with c2:
        h_plate = st.number_input("Plate Height (mm)", min_value=50, value=200, step=10, help="ความสูงแผ่นเหล็ก (h)")
    with c3:
        weld_size = st.number_input("Weld Size (mm)", min_value=3, value=6, step=1, help="ขนาดรอยเชื่อมขา (Leg size)")

    # --- GROUP 2: Bolt Arrangement (การจัดเรียงน็อต) ---
    st.markdown("#### 2️⃣ Bolt Arrangement (จำนวนน็อต)")
    c4, c5 = st.columns(2)
    with c4:
        bolt_rows = st.number_input("Number of Rows (แถวแนวดิ่ง)", min_value=1, value=3, step=1)
    with c5:
        bolt_cols = st.number_input("Number of Columns (แถวแนวราบ)", min_value=1, value=1, step=1)

    # --- GROUP 3: Spacing & Clearances (ระยะห่างต่างๆ) ---
    st.markdown("#### 3️⃣ Spacing & Edge Distances (ระยะห่าง)")
    
    # แถวแรกของระยะห่าง
    c6, c7 = st.columns(2)
    with c6:
        s_v = st.number_input("Vertical Spacing (s_v) (mm)", min_value=30, value=75, step=5, help="ระยะห่างระหว่างน็อตในแนวดิ่ง")
    with c7:
        s_h = st.number_input("Horizontal Spacing (s_h) (mm)", min_value=0, value=60, step=5, help="ระยะห่างระหว่างน็อตในแนวราบ")
    
    # แถวสองของระยะห่าง
    c8, c9 = st.columns(2)
    with c8:
        e1 = st.number_input("Dist. to Column (e1) (mm)", min_value=10, value=40, step=5, help="ระยะจากผิวเสาถึงน็อตตัวแรก")
    with c9:
        l_side = st.number_input("Dist. to Beam End (Edge) (mm)", min_value=10, value=40, step=5, help="ระยะจากน็อตตัวสุดท้ายถึงปลายคาน")

    # =========================================================================
    
    # 3. เตรียม Material & Bolt Properties
    bolt_props = {"A325 (High Strength)": 372, "Grade 8.8 (Standard)": 320, "A490 (Premium)": 496}
    fnv = bolt_props.get(bolt_grade, 372)
    
    # คำนวณความกว้าง Plate อัตโนมัติ
    w_plate = e1 + (max(0, bolt_cols - 1) * s_h) + l_side

    # 4. สร้าง Dictionary ข้อมูล
    plate_data = {
        't': t_plate, 'h': h_plate, 'w': w_plate,
        'lv': 40, 'e1': e1, 'l_side': l_side, 
        'weld_size': weld_size, 'Fy': 250, 'Fu': 400
    }
    
    bolts_data = {
        'd': d, 'rows': bolt_rows, 'cols': bolt_cols,
        's_v': s_v, 's_h': s_h, 'Fnv': fnv
    }

    # 5. แสดงผล DRAWING
    if DRAWING_AVAILABLE:
        st.divider()
        st.markdown("### 🎨 Engineering Drawing")
        
        beam_draw = {
            'h': section_data['h'], 'b': section_data['b'], 
            'tf': section_data['tf'], 'tw': section_data['tw']
        }
        
        # ใช้ Tabs ย่อยสำหรับ Drawing เพื่อประหยัดพื้นที่แนวตั้ง
        tab_plan, tab_side, tab_front = st.tabs(["Plan View (Top)", "Section View (Side)", "Elevation (Front)"])
        
        with tab_plan:
            st.plotly_chart(drw.create_plan_view(beam_draw, plate_data, bolts_data), use_container_width=True)
        with tab_side:
            st.plotly_chart(drw.create_side_view(beam_draw, plate_data, bolts_data), use_container_width=True)
        with tab_front:
            st.plotly_chart(drw.create_front_view(beam_draw, plate_data, bolts_data), use_container_width=True)
            
    else:
        st.error(f"❌ Drawing Module Error: {DRAWING_ERROR}")

    # 6. คำนวณและแสดง Report
    st.divider()
    V_load_kn = V_design / 100
    
    report_md = calc_rep.generate_report(
        V_load=V_load_kn, 
        beam=section_data, 
        plate=plate_data, 
        bolts=bolts_data, 
        is_lrfd=is_lrfd,
        material_grade=mat_grade,
        bolt_grade=bolt_grade
    )
    
    with st.expander("📝 Show Calculation Details", expanded=True):
        st.markdown(report_md, unsafe_allow_html=True)
    
    return (bolt_rows * bolt_cols), V_load_kn
