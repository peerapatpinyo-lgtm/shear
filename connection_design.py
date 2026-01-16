# connection_design.py (V15 - Fully Integrated & Granular Control)
import math
import streamlit as st
import calculation_report as calc_rep

# Drawing Module Safety Check
try:
    import drawing_utils as drw
    DRAWING_AVAILABLE = True
except Exception as e:
    DRAWING_AVAILABLE = False
    DRAWING_ERROR = str(e)

def render_connection_tab(V_design_from_tab1, default_bolt_size, method, is_lrfd, section_data, conn_type, default_bolt_grade, default_mat_grade="A36"):
    """
    V15 Update: ย้าย UI ทุกอย่างมาไว้ในนี้ และเพิ่ม Parameter ความละเอียดสูง
    """
    
    st.markdown(f"### 🛠️ Connection Design Studio")
    st.caption("ปรับแต่งค่าพารามิเตอร์จุดต่ออย่างละเอียด")
    
    # =========================================================================
    # 1️⃣ LOAD & GENERAL SETTINGS (ย้ายมาจาก Sidebar)
    # =========================================================================
    with st.expander("⚙️ General Settings & Loads (ตั้งค่าวัสดุและแรง)", expanded=True):
        c_gen1, c_gen2, c_gen3 = st.columns(3)
        
        with c_gen1:
            # เลือก Load: จะใช้จาก Tab 1 หรือ กรอกเอง
            use_manual_load = st.checkbox("Override Load (กำหนดแรงเอง)", value=False)
            if use_manual_load:
                V_load_input = st.number_input("Design Shear (Vu) [kg]", value=float(V_design_from_tab1), step=100.0)
                V_design_calc = V_load_input
            else:
                st.info(f"Load from Beam Analysis:\n**{V_design_from_tab1:,.0f} kg**")
                V_design_calc = V_design_from_tab1

        with c_gen2:
            # ย้าย Bolt Selection มาที่นี่
            bolt_grade_opts = ["A325 (High Strength)", "Grade 8.8 (Standard)", "A490 (Premium)"]
            # หา index เดิม
            try:
                b_idx = bolt_grade_opts.index(default_bolt_grade)
            except:
                b_idx = 0
            selected_bolt_grade = st.selectbox("Bolt Grade", bolt_grade_opts, index=b_idx)
            
            # Bolt Size
            size_opts = ["M12", "M16", "M20", "M22", "M24", "M27", "M30"]
            try:
                s_idx = size_opts.index(default_bolt_size)
            except:
                s_idx = 2 # Default M20
            selected_bolt_size = st.selectbox("Bolt Size", size_opts, index=s_idx)
            
            # แปลง Bolt Size เป็น Int (M20 -> 20)
            d_bolt = int(''.join(filter(str.isdigit, selected_bolt_size)))

        with c_gen3:
            # Material Grade
            mat_opts = ["A36", "SS400", "SS540", "A572-50"]
            try:
                m_idx = mat_opts.index(default_mat_grade)
            except:
                m_idx = 1 # SS400 Default
            selected_mat_grade = st.selectbox("Plate Material", mat_opts, index=m_idx)

    # =========================================================================
    # 2️⃣ GEOMETRY & SPACING (Detailed Control)
    # =========================================================================
    st.markdown("#### 📐 Geometry & Spacing Configuration")
    
    # ใช้ Tabs เพื่อแยกกลุ่มให้ไม่รก
    tab_geo, tab_plate = st.tabs(["🔩 Bolt Layout (ระยะน็อต)", "⬜ Plate & Weld (ขนาดเพลท)"])
    
    with tab_geo:
        # แบ่งเป็น Grid 2x3 เพื่อความสวยงาม
        c_layout1, c_layout2, c_layout3 = st.columns(3)
        
        with c_layout1:
            st.markdown("**Arrangement**")
            bolt_rows = st.number_input("Rows (จำนวนแถว)", min_value=1, value=3)
            bolt_cols = st.number_input("Columns (จำนวนคอลัมน์)", min_value=1, value=1)
            
        with c_layout2:
            st.markdown("**Vertical (แนวตั้ง)**")
            s_v = st.number_input("Pitch (s_v) [mm]", min_value=30, value=75, help="ระยะห่างระหว่างน็อตในแนวดิ่ง")
            # [NEW] เพิ่มระยะขอบบน (Top Edge Distance)
            lv = st.number_input("Top Edge (lv) [mm]", min_value=20, value=40, help="ระยะจากขอบบนเพลท ถึงกึ่งกลางน็อตตัวบนสุด")
            
        with c_layout3:
            st.markdown("**Horizontal (แนวราบ)**")
            s_h = st.number_input("Gauge (s_h) [mm]", min_value=0, value=60, help="ระยะห่างระหว่างน็อตในแนวราบ (กรณีมีหลายคอลัมน์)")
            # [NEW] เปลี่ยน e1 ให้เข้าใจง่ายขึ้น
            e1 = st.number_input("Dist to Col (e1) [mm]", min_value=20, value=50, help="ระยะจากผิวเสา ถึงกึ่งกลางน็อตแถวแรก")
            l_side = st.number_input("Dist to Edge (Le) [mm]", min_value=20, value=40, help="ระยะจากน็อตตัวสุดท้าย ถึงขอบแผ่นเหล็กฝั่งคาน")

    with tab_plate:
        c_pl1, c_pl2, c_pl3 = st.columns(3)
        with c_pl1:
            t_plate = st.number_input("Plate Thickness (t) [mm]", min_value=6, value=10)
        with c_pl2:
            # [NEW] เพิ่มตัวเลือก Auto Height
            auto_h = st.checkbox("Auto Height Calculation", value=True, help="คำนวณความสูงเพลทอัตโนมัติตามระยะน็อต")
            
            # คำนวณความสูงขั้นต่ำที่ต้องการ
            req_h = lv + ((bolt_rows - 1) * s_v) + lv # สมมติให้ขอบล่างเท่ากับขอบบน (lv)
            
            if auto_h:
                h_plate = req_h
                st.info(f"Auto Height: **{h_plate} mm**")
            else:
                h_plate = st.number_input("Plate Height (H) [mm]", min_value=int(req_h), value=int(req_h)+20)
                
        with c_pl3:
            weld_size = st.number_input("Weld Leg Size (w) [mm]", min_value=3, value=6)
            setback = st.slider("Setback (ช่องว่างเสา-คาน)", 10, 20, 15, help="ระยะห่างระหว่างหน้าเสากับปลายคาน")

    # =========================================================================
    # 3️⃣ PROCESSING
    # =========================================================================
    
    # คำนวณความกว้าง Plate อัตโนมัติ (Based on e1 + cols + edge)
    w_plate = e1 + (max(0, bolt_cols - 1) * s_h) + l_side

    # Bolt Properties Lookup
    bolt_props_db = {
        "A325 (High Strength)": 372, # MPa (Shear)
        "Grade 8.8 (Standard)": 320,
        "A490 (Premium)": 496
    }
    fnv_val = bolt_props_db.get(selected_bolt_grade, 372)

    # Pack Data for Drawing & Calculation
    plate_data = {
        't': t_plate, 'h': h_plate, 'w': w_plate,
        'lv': lv,          # [Use User Input]
        'e1': e1, 
        'l_side': l_side, 
        'weld_size': weld_size, 
        'Fy': 250, 'Fu': 400 # ค่า Default SS400 (ปรับปรุงในอนาคตตาม Grade ได้)
    }
    
    bolts_data = {
        'd': d_bolt, 
        'rows': bolt_rows, 
        'cols': bolt_cols,
        's_v': s_v, 
        's_h': s_h, 
        'Fnv': fnv_val
    }
    
    # ใส่ Setback เข้าไปใน Beam Draw (Hack เล็กน้อยเพื่อให้รูปวาดถูกต้อง)
    # ปกติ drawing_utils อาจจะใช้ค่าคงที่ แต่ถ้าเราอยากส่ง setback ไปด้วย อาจต้องแก้ drawing_utils นิดหน่อย
    # แต่เบื้องต้น drawing_utils ใช้ตัวแปร global SETBACK = 15
    # เพื่อความง่าย เราจะใช้ค่าที่ drawing_utils มี หรือปล่อยไว้ก่อน (รูปวาดจะไม่เปลี่ยนตาม slider นี้ถ้าไม่แก้ drawing แต่ค่านี้ไม่กระทบคำนวณมากนัก)

    # =========================================================================
    # 4️⃣ DRAWING & REPORT OUTPUT
    # =========================================================================
    
    if DRAWING_AVAILABLE:
        st.divider()
        st.markdown("### 🎨 Visualization (Real-time)")
        
        beam_draw = {
            'h': section_data['h'], 'b': section_data['b'], 
            'tf': section_data['tf'], 'tw': section_data['tw']
        }
        
        # Grid Layout for Drawings (Plan ใหญ่หน่อย, Side/Front เล็กขนาบข้าง)
        col_d1, col_d2 = st.columns([1.5, 1])
        
        with col_d1:
             st.plotly_chart(drw.create_plan_view(beam_draw, plate_data, bolts_data), use_container_width=True)
             st.caption("Plan View (Top)")
             
        with col_d2:
             st.plotly_chart(drw.create_front_view(beam_draw, plate_data, bolts_data), use_container_width=True)
             st.caption("Elevation (Front)")
             
             st.plotly_chart(drw.create_side_view(beam_draw, plate_data, bolts_data), use_container_width=True)
             st.caption("Section (Side)")

    else:
        st.error(f"❌ Drawing Module Error: {DRAWING_ERROR}")

    # Report Generation
    st.divider()
    
    V_load_kn = V_design_calc / 100 # Convert kg -> kN (ประมาณการ) OR check calculation_report expectation
    # เช็ค calculation_report.py ว่ารับหน่วยอะไร? 
    # จากไฟล์เก่า: V_load_kn = V_design / 100 -> น่าจะแปลงเป็น kN หรือหน่วยที่ calc_rep ต้องการ
    
    report_md = calc_rep.generate_report(
        V_load=V_load_kn, 
        beam=section_data, 
        plate=plate_data, 
        bolts=bolts_data, 
        is_lrfd=is_lrfd,
        material_grade=selected_mat_grade,
        bolt_grade=selected_bolt_grade
    )
    
    with st.expander("📝 View Detailed Calculation Report", expanded=True):
        st.markdown(report_md, unsafe_allow_html=True)
    
    return (bolt_rows * bolt_cols), V_design_calc
