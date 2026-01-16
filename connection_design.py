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
        # สำหรับ ASD ในเชิงคำนวณ เราจะใช้ 1/Omega
        phi_y = 1.0 / 1.50   # Ω = 1.50
        phi_r = 1.0 / 2.00   # Ω = 2.00
        phi_b = 1.0 / 2.00    
        method_name = "ASD"

    # 3. Material Properties (kN/mm2 หรือ MPa)
    if "SS400" in mat_grade: Fy, Fu = 245, 400
    elif "SM520" in mat_grade: Fy, Fu = 355, 520
    else: Fy, Fu = 250, 400 # Default A36

    # 4. BOLT SHEAR (Single Shear)
    # อ้างอิงน็อต Grade 8.8 / A325: Fnv = 372 MPa (รวม Thread)
    d = inputs['d']
    Ab = (math.pi * d**2) / 4
    n_bolts = inputs['rows'] * inputs['cols']
    Rn_bolt = (372 * Ab * n_bolts) / 1000.0 # เปลี่ยนเป็น kN
    # แปลง kN เป็น kg (คูณ 1000 หาร 9.81)
    Cap_Bolt = (Rn_bolt * phi_r) * 1000 / 9.81 
    results['Bolt Shear'] = Cap_Bolt

    # 5. PLATE SHEAR (ใช้ค่า s และ lv ตามที่คุณย้ำ)
    s = inputs['s_v']    # Spacing (ระยะเรียง)
    lv = inputs['lv']    # Vertical Edge (ระยะขอบ)
    t = inputs['t']
    h_p = plate_geom['h']
    
    # Shear Yielding (Gross Area)
    Agv = h_p * t
    Rn_y = (0.60 * Fy * Agv) / 1000.0
    results['Plate Yielding'] = (Rn_y * phi_y) * 1000 / 9.81

    # Shear Rupture (Net Area - หักรูเจาะ d+2mm)
    Anv = (h_p - (inputs['rows'] * (d + 2))) * t
    Rn_r = (0.60 * Fu * Anv) / 1000.0
    results['Plate Rupture'] = (Rn_r * phi_r) * 1000 / 9.81

    # 6. BLOCK SHEAR (พฤติกรรมฉีกขาดผ่านรูน็อตถึงขอบ)
    # แนวเฉือน L = (n-1)*s + lv
    shear_path = ((inputs['rows'] - 1) * s) + lv
    Anv_block = (shear_path - (inputs['rows'] - 0.5) * (d + 2)) * t
    # คิดเฉพาะ Shear Rupture ส่วนที่ง่ายที่สุดตามหนังสือ
    Rn_block = (0.6 * Fu * Anv_block) / 1000.0 
    results['Block Shear'] = (Rn_block * phi_r) * 1000 / 9.81

    # 7. WELD CAPACITY (Fillet Weld E70)
    w_sz = inputs['weld_size']
    L_weld = h_p * 2 # เชื่อม 2 ฝั่งแผ่นเพลท
    # Rn = 0.60 * Fexx * 0.707 * a * L
    Rn_weld = (0.60 * 480 * 0.707 * w_sz * L_weld) / 1000.0
    results['Weld Strength'] = (Rn_weld * phi_r) * 1000 / 9.81

    # 8. สรุปผลการคำนวณ
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
    """คำนวณขนาดแผ่นเหล็กอัตโนมัติจากระยะเรียงและระยะขอบ"""
    rows, cols = user_inputs['rows'], user_inputs['cols']
    sv, sh = user_inputs['s_v'], user_inputs['s_h']
    lv, leh = user_inputs['lv'], user_inputs['leh']
    e1, setback = user_inputs['e1'], user_inputs['setback']
    
    # ความสูงเพลท: ระยะขอบบน + ระยะห่างระหว่างน็อต + ระยะขอบล่าง
    calc_h = (2 * lv) + ((rows - 1) * sv)
    
    # ความกว้างเพลท
    if "Fin" in conn_type:
        calc_w = setback + e1 + ((cols - 1) * sh) + leh
    elif "End" in conn_type:
        calc_w = (2 * leh) + sh
    else: # Double Angle
        calc_w = e1 + leh 

    return {'h': calc_h, 'w': calc_w, 'type': conn_type}

# ==========================================
# 🖥️ UI RENDERING FOR TAB 2
# ==========================================

def render_connection_tab(V_design_from_tab1, default_bolt_size, method, is_lrfd, section_data, conn_type, default_bolt_grade, default_mat_grade):
    
    # ใช้ค่า Method จาก Session State เพื่อยืนยันการ Link
    current_method = st.session_state.get('design_method', method)
    
    st.markdown(f"### ⚙️ Detail Design: {conn_type}")
    st.caption(f"Calculated based on **{current_method}** from Analysis Tab")

    col_input, col_draw = st.columns([1, 2])
    
    # --- ส่วนที่ 1: ฝั่งรับค่า INPUTS ---
    with col_input:
        st.markdown(f"""
        <div style="background-color:#f0f7ff; padding:15px; border-radius:10px; border-left:5px solid #2563eb;">
            <small>DESIGN SHEAR LOAD (Vu/Va):</small><br>
            <strong style="font-size:20px; color:#1e40af;">{V_design_from_tab1:,.0f} kg</strong>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("1. Bolt Configuration", expanded=True):
            c1, c2 = st.columns(2)
            d_bolt = c1.selectbox("Bolt Size (mm)", [12, 16, 20, 22, 24, 27, 30], index=2)
            rows = c2.number_input("Rows (แนวตั้ง)", 2, 15, 3)
            
            if "End" in conn_type or "Double" in conn_type:
                cols = 2
                st.caption("Columns: 2 (Fixed)")
            else:
                cols = st.number_input("Cols (แนวนอน)", 1, 4, 1)

            c3, c4 = st.columns(2)
            s_v = c3.number_input("Pitch s (mm)", 30, 200, 75)
            s_h = c4.number_input("Gauge g (mm)", 30, 200, 75 if cols > 1 else 0)

        with st.expander("2. Plate & Weld Detail", expanded=True):
            c1, c2 = st.columns(2)
            t_plate = c1.number_input("Plate Thickness (mm)", 4, 40, 9)
            weld_sz = c2.number_input("Weld Size (mm)", 3, 20, 6)
            
            st.divider()
            st.caption("Edge Distance & Geometry")
            k1, k2 = st.columns(2)
            lv = k1.number_input("Vert. Edge lv (mm)", 25, 150, 40)
            leh = k2.number_input("Horiz. Edge leh (mm)", 25, 150, 40)
            
            k3, k4 = st.columns(2)
            # ระยะจากศูนย์กลางน็อตถึงปลายคาน (e1) และช่องว่าง (setback)
            e1 = k3.number_input("Bolt to Beam e1", 30, 150, 40, disabled=("End" in conn_type))
            setback = k4.number_input("Setback (gap)", 0, 50, 10, disabled=("End" in conn_type))

        # รวบรวม Inputs ทั้งหมด
        user_inputs = {
            'd': d_bolt, 'rows': rows, 'cols': cols, 's_v': s_v, 's_h': s_h,
            't': t_plate, 'weld_size': weld_sz,
            'lv': lv, 'leh': leh, 'e1': e1, 'setback': setback
        }
        
        # --- คำนวณทันทีเมื่อ Input เปลี่ยน ---
        plate_geom = calculate_plate_geometry(conn_type, user_inputs)
        calc_res = calculate_capacity(user_inputs, plate_geom, V_design_from_tab1, default_mat_grade)
        
        # --- ส่วนแสดงผลสถานะ PASS / FAIL ---
        st.divider()
        status_color = "green" if calc_res['status'] == "PASS" else "red"
        st.markdown(f"#### Capacity Status: :{status_color}[{calc_res['status']}]")
        st.markdown(f"**Total Capacity:** {calc_res['capacity']:,.0f} kg (Ratio: {calc_res['ratio']:.2f})")
        
        # Progress Bars แยกตามแต่ละจุดตรวจสอบ
        for check_name, cap_val in calc_res['checks'].items():
            check_ratio = V_design_from_tab1 / cap_val if cap_val > 0 else 0
            bar_color = "red" if check_ratio > 1.0 else "green"
            st.write(f"• {check_name}")
            st.progress(min(check_ratio, 1.0))
            st.caption(f"Cap: {cap_val:,.0f} kg | Ratio: {check_ratio:.2f}")

    # --- ส่วนที่ 2: ฝั่งแสดงรูป DRAWING ---
    with col_draw:
        t_front, t_side, t_plan = st.tabs(["🖼️ Front View", "📏 Side View", "📐 Plan View"])
        
        with t_front:
            fig_f = dw.create_front_view(section_data, plate_geom, user_inputs)
            st.plotly_chart(fig_f, use_container_width=True)
            
        with t_side:
            fig_s = dw.create_side_view(section_data, plate_geom, user_inputs)
            st.plotly_chart(fig_s, use_container_width=True)

        with t_plan:
            fig_p = dw.create_plan_view(section_data, plate_geom, user_inputs)
            st.plotly_chart(fig_p, use_container_width=True)
            
    return plate_geom, user_inputs
