import streamlit as st
import drawing_utils as dw

def calculate_plate_geometry(conn_type, user_inputs):
    """
    คำนวณ Geometry ที่ใช้ก่อสร้างจริง
    """
    rows = user_inputs['rows']
    cols = user_inputs['cols']
    sv = user_inputs['s_v']
    sh = user_inputs['s_h']
    
    lv = user_inputs['lv']   # Vertical Edge (Top/Bottom)
    leh = user_inputs['leh'] # Horizontal Edge (Tail)
    e1 = user_inputs['e1']   # Distance from Beam End to First Bolt
    setback = user_inputs['setback']
    
    # 1. Height Calculation (Common for all)
    # H = (Space between top and bottom bolts) + 2 * Edge Distance
    bolt_group_h = (rows - 1) * sv
    calc_h = bolt_group_h + (2 * lv)
    
    # 2. Width Calculation
    calc_w = 0
    if "Fin" in conn_type:
        # Width = Setback + e1 + Bolt Group Width + Edge Distance
        bolt_group_w = (cols - 1) * sh
        # Fin Plate Total Width from Column Face
        # Structure: [Column] --(Setback)-- [Beam Start] --(e1)-- [First Bolt] ... [Last Bolt] --(leh)-- [End]
        # BUT: For Fin plate, usually e1 is dist from Beam End to Bolt.
        # So Plate Width = Setback + e1 + bolt_group_w + leh
        calc_w = setback + e1 + bolt_group_w + leh
        
    elif "End" in conn_type:
        # Width = Gauge + 2 * Horizontal Edge
        calc_w = sh + (2 * leh)
        
    elif "Double" in conn_type:
        # Width of angle leg on web = e1 + leh
        calc_w = e1 + leh # (Simplified)

    return {
        'h': calc_h,
        'w': calc_w,
        'type': conn_type
    }

def render_connection_tab(V_design_from_tab1, default_bolt_size, method, is_lrfd, section_data, conn_type, default_bolt_grade, default_mat_grade):
    
    st.markdown(f"### 🔩 Detail Design: {conn_type}")
    
    # --- Layout ---
    col_settings, col_visuals = st.columns([1, 2])
    
    with col_settings:
        st.info("🛠️ **Construction Parameters**")
        
        with st.expander("1. Bolt Layout", expanded=True):
            c1, c2 = st.columns(2)
            d_bolt = c1.selectbox("Bolt Size (mm)", [12, 16, 20, 24, 30], index=2)
            bolt_grade = c2.selectbox("Grade", ["A325", "A490", "8.8"], index=0)
            
            c3, c4 = st.columns(2)
            rows = c3.number_input("Rows (แถว)", 2, 20, 3)
            if "End" in conn_type:
                cols = 2
                c4.markdown("**Cols:** 2 (Fixed)")
            else:
                cols = c4.number_input("Cols (คอลัมน์)", 1, 10, 1)
            
            c5, c6 = st.columns(2)
            s_v = c5.number_input("Pitch (Vert.)", 40, 200, 70, help="ระยะห่างแนวดิ่ง (mm)")
            s_h = c6.number_input("Gauge/Pitch (Horiz.)", 40, 200, 90, help="ระยะห่างแนวนอน (mm)")

        with st.expander("2. Plate & Welds", expanded=True):
            t_plate = st.number_input("Plate Thickness (t)", 6.0, 50.0, 10.0, step=1.0)
            weld_sz = st.number_input("Weld Size (mm)", 3.0, 20.0, 6.0, step=1.0, help="ขนาดขาเชื่อม (Leg Size)")
            
            st.markdown("---")
            st.caption("📏 **Distances (Construction)**")
            
            k1, k2 = st.columns(2)
            lv = k1.number_input("Vert. Edge (Lv)", 20, 100, 40, help="ขอบบน/ล่าง ถึงรูเจาะ")
            leh = k2.number_input("Horiz. Edge (Le)", 20, 100, 40, help="ขอบข้าง ถึงรูเจาะ")
            
            k3, k4 = st.columns(2)
            e1 = k3.number_input("Beam End to Bolt (e1)", 20, 100, 40, disabled=("End" in conn_type))
            setback = k4.number_input("Gap / Setback", 0, 50, 10, disabled=("End" in conn_type))

        # Pack Inputs
        user_inputs = {
            'd': d_bolt, 'grade': bolt_grade,
            'rows': rows, 'cols': cols,
            's_v': s_v, 's_h': s_h,
            't': t_plate, 'weld_size': weld_sz,
            'lv': lv, 'leh': leh,
            'e1': e1, 'setback': setback
        }

        # Auto Calculate Plate Size
        plate_geom = calculate_plate_geometry(conn_type, user_inputs)
        
        # Display Result Box
        st.success(f"""
        **Plate Dimensions:**
        \nSIZE: **{plate_geom['w']:.0f} x {plate_geom['h']:.0f}** mm
        \nTHK: **{t_plate}** mm
        """)

    with col_visuals:
        tab_front, tab_side, tab_plan = st.tabs(["Front View", "Side View", "Plan View"])
        
        # Draw Real-time
        with tab_front:
            fig1 = dw.create_front_view(section_data, plate_geom, user_inputs)
            st.plotly_chart(fig1, use_container_width=True)
            
        with tab_side:
            fig2 = dw.create_side_view(section_data, plate_geom, user_inputs)
            st.plotly_chart(fig2, use_container_width=True)
            
        with tab_plan:
            fig3 = dw.create_plan_view(section_data, plate_geom, user_inputs)
            st.plotly_chart(fig3, use_container_width=True)
            
    return plate_geom, user_inputs
