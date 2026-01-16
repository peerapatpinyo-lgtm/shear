# connection_design.py
import streamlit as st
import math
import drawing_utils as dw

# ==========================================
# 🧮 ENGINEERING CALCULATION LOGIC
# ==========================================

def calculate_capacity(inputs, plate_geom, V_load, mat_grade):
    """
    คำนวณกำลังรับน้ำหนักจริง โดยอ้างอิง Method (ASD/LRFD) จาก Tab 1
    """
    # 1. ดึง Method จาก Session State (Link กับ Tab 1)
    method_raw = st.session_state.get('design_method', 'LRFD (Limit State)')
    is_lrfd = "LRFD" in method_raw
    
    results = {}
    
    # 2. กำหนดค่าตัวคูณความปลอดภัย (Factors) ตามมาตรฐาน AISC 360
    if is_lrfd:
        phi_y = 0.90   # Yielding
        phi_r = 0.75   # Rupture / Bolt / Weld
        phi_b = 0.75   # Bearing
        method_name = "LRFD"
    else:
        # สำหรับ ASD ใช้ 1/Omega
        phi_y = 1.0 / 1.50   # Ω = 1.50
        phi_r = 1.0 / 2.00   # Ω = 2.00
        phi_b = 1.0 / 2.00    
        method_name = "ASD"

    # 3. Material Properties
    if "SS400" in mat_grade: Fy, Fu = 245, 400
    elif "SM520" in mat_grade: Fy, Fu = 355, 520
    else: Fy, Fu = 250, 400 

    # 4. BOLT SHEAR (Single Shear)
    d = inputs['d']
    Ab = (math.pi * d**2) / 4
    n_bolts = inputs['rows'] * inputs['cols']
    # Fnv = 372 MPa (A325 Threads included)
    Rn_bolt = (372 * Ab * n_bolts) / 1000.0 
    Cap_Bolt = (Rn_bolt * phi_r) * 1000 / 9.81 
    results['Bolt Shear'] = Cap_Bolt

    # 5. PLATE SHEAR (ใช้ค่า s_v เป็นระยะเรียง)
    s = inputs['s_v']    
    lv = inputs['lv']    
    t = inputs['t']
    h_p = plate_geom['h']
    
    # Shear Yielding
    Agv = h_p * t
    Rn_y = (0.60 * Fy * Agv) / 1000.0
    results['Plate Yielding'] = (Rn_y * phi_y) * 1000 / 9.81

    # Shear Rupture (Net Area หักรูเจาะ d+2mm)
    Anv = (h_p - (inputs['rows'] * (d + 2))) * t
    Rn_r = (0.60 * Fu * Anv) / 1000.0
    results['Plate Rupture'] = (Rn_r * phi_r) * 1000 / 9.81

    # 6. BLOCK SHEAR
    # ระยะทางเดินแรงเฉือนแนวดิ่ง
    shear_path = ((inputs['rows'] - 1) * s) + lv
    Anv_block = (shear_path - (inputs['rows'] - 0.5) * (d + 2)) * t
    Rn_block = (0.6 * Fu * Anv_block) / 1000.0 
    results['Block Shear'] = (Rn_block * phi_r) * 1000 / 9.81

    # 7. WELD CAPACITY
    w_sz = inputs['weld_size']
    L_weld = h_p * 2 
    Rn_weld = (0.60 * 480 * 0.707 * w_sz * L_weld) / 1000.0
    results['Weld Strength'] = (Rn_weld * phi_r) * 1000 / 9.81

    # 8. Summary
    min_cap = min(results.values())
    ratio = V_load / min_cap if min_cap > 0 else 0
    
    return {
        'checks': results,
        'capacity': min_cap,
        'ratio': ratio,
        'status': "PASS" if ratio <= 1.0 else "FAIL",
        'method_used': method_name
    }

def calculate_plate_geometry(conn_type, user_inputs):
    rows, cols = user_inputs['rows'], user_inputs['cols']
    sv, sh = user_inputs['s_v'], user_inputs['s_h']
    lv, leh = user_inputs['lv'], user_inputs['leh']
    e1, setback = user_inputs['e1'], user_inputs['setback']
    
    calc_h = (2 * lv) + ((rows - 1) * sv)
    
    if "Fin" in conn_type:
        calc_w = setback + e1 + ((cols - 1) * sh) + leh
    elif "End" in conn_type:
        calc_w = (2 * leh) + sh
    else: # Double Angle
        calc_w = e1 + leh 

    return {'h': calc_h, 'w': calc_w, 'type': conn_type}

# ==========================================
# 🖥️ UI RENDERING
# ==========================================

def render_connection_tab(V_design_from_tab1, default_bolt_size, method, is_lrfd, section_data, conn_type, default_bolt_grade, default_mat_grade):
    
    current_method = st.session_state.get('design_method', method)
    
    st.markdown(f"### 🔩 Detail Design: {conn_type}")
    st.caption(f"Linked Method: **{current_method}**")

    col_input, col_draw = st.columns([1, 2])
    
    with col_input:
        st.markdown(f"""
        <div style="background-color:#f0f7ff; padding:15px; border-radius:10px; border-left:5px solid #2563eb;">
            <small>DESIGN SHEAR LOAD:</small><br>
            <strong style="font-size:20px; color:#1e40af;">{V_design_from_tab1:,.0f} kg</strong>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("1. Bolt Configuration", expanded=True):
            c1, c2 = st.columns(2)
            d_bolt = c1.selectbox("Bolt Size (mm)", [12, 16, 20, 22, 24, 27, 30], index=2)
            rows = c2.number_input("Rows", 2, 15, 3)
            
            if "End" in conn_type or "Double" in conn_type:
                cols = 2
                st.info("Columns: 2 (Fixed)")
            else:
                cols = st.number_input("Cols", 1, 4, 1)

            c3, c4 = st.columns(2)
            s_v = c3.number_input("Pitch s (mm)", 30, 200, 75)
            
            # --- FIX StreamlitValueBelowMinError ---
            if cols > 1:
                s_h = c4.number_input("Gauge g (mm)", 30, 200, 75)
            else:
                s_h = 0
                c4.number_input("Gauge g (mm)", 0, 0, 0, disabled=True)

        with st.expander("2. Plate & Weld", expanded=True):
            c1, c2 = st.columns(2)
            t_plate = c1.number_input("Plate t (mm)", 4, 40, 9)
            weld_sz = c2.number_input("Weld Size (mm)", 3, 20, 6)
            
            st.divider()
            k1, k2 = st.columns(2)
            lv = k1.number_input("lv (Edge Vert.)", 25, 150, 40)
            leh = k2.number_input("leh (Edge Horiz.)", 25, 150, 40)
            
            k3, k4 = st.columns(2)
            e1 = k3.number_input("e1 (Bolt to Beam)", 30, 150, 40, disabled=("End" in conn_type))
            setback = k4.number_input("Setback", 0, 50, 10, disabled=("End" in conn_type))

        user_inputs = {
            'd': d_bolt, 'rows': rows, 'cols': cols, 's_v': s_v, 's_h': s_h,
            't': t_plate, 'weld_size': weld_sz,
            'lv': lv, 'leh': leh, 'e1': e1, 'setback': setback
        }
        
        plate_geom = calculate_plate_geometry(conn_type, user_inputs)
        calc_res = calculate_capacity(user_inputs, plate_geom, V_design_from_tab1, default_mat_grade)
        
        st.divider()
        status_color = "green" if calc_res['status'] == "PASS" else "red"
        st.markdown(f"#### Status: :{status_color}[{calc_res['status']}]")
        st.write(f"**Capacity:** {calc_res['capacity']:,.0f} kg")
        st.write(f"**Ratio:** {calc_res['ratio']:.2f}")

    with col_draw:
        t_front, t_side, t_plan = st.tabs(["Front", "Side", "Plan"])
        with t_front:
            st.plotly_chart(dw.create_front_view(section_data, plate_geom, user_inputs), use_container_width=True)
        with t_side:
            st.plotly_chart(dw.create_side_view(section_data, plate_geom, user_inputs), use_container_width=True)
        with t_plan:
            st.plotly_chart(dw.create_plan_view(section_data, plate_geom, user_inputs), use_container_width=True)
            
    return plate_geom, user_inputs
