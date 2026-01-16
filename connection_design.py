import streamlit as st
import drawing_utils as dw

def calculate_geometry(con_type, inputs):
    """
    ฟังก์ชันคำนวณขนาด Plate (W, H) อัตโนมัติจากระยะ Bolt
    """
    rows = inputs['rows']
    cols = inputs['cols']
    sv = inputs['s_v']
    sh = inputs['s_h'] # Gauge for End Plate
    
    lv = inputs['lv']   # ระยะขอบแนวตั้ง (Vertical Edge)
    leh = inputs['leh'] # ระยะขอบแนวนอน (Horizontal Edge)
    e1 = inputs['e1']   # ระยะ Bolt ตัวแรก (Setback to bolt)
    setback = inputs['setback']
    
    # 1. คำนวณความสูง (Height)
    # H = (จำนวนช่องว่าง * ระยะห่าง) + (2 * ระยะขอบบนล่าง)
    calc_h = ((rows - 1) * sv) + (2 * lv)

    # 2. คำนวณความกว้าง (Width)
    calc_w = 0
    if "Fin" in con_type:
        # Fin: Setback + e1 + ระยะกลุ่ม Bolt + ขอบท้าย
        bolt_zone_w = (cols - 1) * sh
        calc_w = setback + e1 + bolt_zone_w + leh

    elif "End" in con_type:
        # End Plate: Gauge + (2 * ขอบข้าง)
        calc_w = sh + (2 * leh)

    elif "Double" in con_type:
        # Angle: เอาความยาวขาที่ยึดกับ Web = e1 + leh
        calc_w = e1 + leh 

    return {
        'h': calc_h,
        'w': calc_w,
        't': inputs['t'],
        'type': con_type,
        'lv': lv,
        'e1': e1,
        'setback': setback,
        'leh': leh
    }

def render_connection_tab(V_design_from_tab1, default_bolt_size, method, is_lrfd, section_data, conn_type, default_bolt_grade, default_mat_grade):
    
    st.markdown(f"### 🔩 Design: {conn_type}")
    
    col_input, col_draw = st.columns([1, 2])
    
    # --- INPUTS (LEFT COLUMN) ---
    with col_input:
        with st.expander("1. Bolt Configuration", expanded=True):
            d_bolt = st.selectbox("Bolt Size", [12, 16, 20, 22, 24], index=2)
            
            c1, c2 = st.columns(2)
            rows = c1.number_input("Rows", 2, 10, 3)
            # ถ้าเป็น End Plate บังคับ 2 Cols (ซ้าย/ขวา Web)
            if "End" in conn_type:
                cols = 2
                c2.info("Cols: 2 (Fixed)")
            else:
                cols = c2.number_input("Cols", 1, 5, 1)

            c3, c4 = st.columns(2)
            s_v = c3.number_input("Pitch (Vertical)", 30, 200, 70)
            label_sh = "Gauge" if "End" in conn_type else "Spacing (Horiz)"
            s_h = c4.number_input(label_sh, 30, 200, 90)

        with st.expander("2. Plate Geometry (Auto-Calc)", expanded=True):
            st.caption("Adjust these edge distances, Plate size will update automatically.")
            c1, c2 = st.columns(2)
            lv = c1.number_input("Vert. Edge (lv)", 20, 100, 40)
            leh = c2.number_input("Horiz. Edge (leh)", 20, 100, 40)
            
            c3, c4 = st.columns(2)
            e1 = c3.number_input("Setback to Bolt (e1)", 30, 100, 50, disabled=("End" in conn_type))
            setback = c4.number_input("Gap (Setback)", 0, 50, 15, disabled=("End" in conn_type))
            
            t_plate = st.number_input("Plate Thickness (mm)", 4, 50, 10)

        # Pack User Inputs
        user_inputs = {
            'd': d_bolt, 'rows': rows, 'cols': cols, 's_v': s_v, 's_h': s_h,
            'lv': lv, 'leh': leh, 'e1': e1, 'setback': setback, 't': t_plate
        }

        # 🔥 CALCULATION & CHECK (Basic Placeholder)
        # คำนวณขนาด Plate อัตโนมัติที่นี่
        plate_geom = calculate_geometry(conn_type, user_inputs)
        
        # Simple Capacity Check (Example Logic)
        # Bolt Shear Capacity (Single Shear)
        # A_b = 3.14 * (d_bolt/10)**2 / 4
        # phi = 0.75 if is_lrfd else 1.0/2.0
        # Fnv = 0.45 * 8250 # Example Fnv for A325 roughly
        # Rn_bolt = phi * Fnv * A_b * (rows * cols)
        # ... คุณสามารถใส่ Logic เต็มๆ ของคุณตรงนี้ ...

        st.success(f"📏 Plate Size: **{plate_geom['w']} x {plate_geom['h']} mm**")

    # --- DRAWING (RIGHT COLUMN) ---
    with col_draw:
        tab_front, tab_side, tab_plan = st.tabs(["Front View", "Side View", "Plan View"])
        
        with tab_front:
            fig1 = dw.create_front_view(section_data, plate_geom, user_inputs)
            st.plotly_chart(fig1, use_container_width=True)
            
        with tab_side:
            fig2 = dw.create_side_view(section_data, plate_geom, user_inputs)
            st.plotly_chart(fig2, use_container_width=True)

        with tab_plan:
            fig3 = dw.create_plan_view(section_data, plate_geom, user_inputs)
            st.plotly_chart(fig3, use_container_width=True)
