import streamlit as st
import math
import drawing_utils as dw
import calculation_report as cr 

# ==========================================
# 🧮 1. ENGINEERING LOGIC (QUICK CHECK)
# ==========================================
def calculate_quick_check(inputs, plate_geom, V_load_kg, mat_grade):
    """
    คำนวณเบื้องต้นสำหรับแสดง Status Bar ด้านซ้าย (หน่วย kg)
    """
    method_raw = st.session_state.get('design_method', 'LRFD (Limit State)')
    is_lrfd = "LRFD" in method_raw
    
    if is_lrfd:
        phi_y, phi_r, phi_b, phi_w = 0.90, 0.75, 0.75, 0.75
    else:
        # ASD Equivalent Phi
        phi_y, phi_r, phi_b, phi_w = 1/1.50, 1/2.00, 1/2.00, 1/2.00

    # Material (Estimated ksc -> kg/mm2)
    if "SS400" in mat_grade: Fy, Fu = 24.5, 41.0
    elif "SM520" in mat_grade: Fy, Fu = 36.0, 53.0
    else: Fy, Fu = 25.0, 41.0 # A36 Default

    d = inputs['d']
    n_bolts = inputs['rows'] * inputs['cols']
    t = inputs['t']
    
    results = {}

    # 1. Bolt Shear (Simple) - kg
    Ab = (math.pi * d**2) / 4
    Fnv = 38.0 # Approx A325 (kg/mm2)
    Rn_bolt = Fnv * Ab * n_bolts
    results['Bolt Shear'] = Rn_bolt * phi_r

    # 2. Plate Shear Yielding - kg
    h_p = plate_geom['h']
    Rn_yld = 0.60 * Fy * (h_p * t)
    results['Plate Yielding'] = Rn_yld * phi_y

    # 3. Plate Rupture - kg
    h_hole = d + 2
    An = (h_p - (inputs['rows'] * h_hole)) * t
    Rn_rup = 0.60 * Fu * An
    results['Plate Rupture'] = Rn_rup * phi_r
    
    # 4. Weld - kg
    w_sz = inputs['weld_size']
    L_weld = h_p * 2
    Fexx = 49.0 # E70xx
    Rn_weld = 0.60 * Fexx * 0.707 * w_sz * L_weld
    results['Weld Strength'] = Rn_weld * phi_w

    min_cap = min(results.values())
    ratio = V_load_kg / min_cap if min_cap > 0 else 999
    
    return {
        'checks': results,
        'capacity': min_cap,
        'ratio': ratio,
        'status': "PASS" if ratio <= 1.0 else "FAIL"
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
    else: 
        calc_w = e1 + leh 

    return {'h': calc_h, 'w': calc_w, 'type': conn_type}

# ==========================================
# 🖥️ 2. UI RENDERING
# ==========================================
def render_connection_tab(V_design_from_tab1, default_bolt_size, method, is_lrfd, section_data, conn_type, default_bolt_grade, default_mat_grade):
    
    # [FIX] Assign ค่ากลับเข้าตัวแปร local
    V_design_kg = V_design_from_tab1
    
    current_method = st.session_state.get('design_method', method)
    
    # --- Layout ---
    col_input, col_draw = st.columns([1, 1.8])
    
    with col_input:
        # Header Box
        st.markdown(f"""
        <div style="background-color:#eff6ff; padding:15px; border-radius:8px; border-left:5px solid #3b82f6; margin-bottom:15px;">
            <div style="font-size:12px; color:#6b7280; font-weight:bold;">DESIGN LOAD ({current_method})</div>
            <div style="font-size:26px; font-weight:800; color:#1e3a8a;">{V_design_kg:,.0f} kg</div>
        </div>
        """, unsafe_allow_html=True)
        
        # UI Tabs แยกหมวดหมู่
        in_tab1, in_tab2 = st.tabs(["🔩 1. Bolt Config", "🛡️ 2. Plate & Load"])

        # --- TAB 1: Bolt Configuration ---
        with in_tab1:
            c1, c2 = st.columns(2)
            d_bolt = c1.selectbox("Size (mm)", [12, 16, 20, 22, 24, 27, 30], index=2)
            rows = c2.number_input("Rows", 2, 20, 3)
            
            if "End" in conn_type:
                cols = 2
                st.info("Cols: 2 (End Plate)")
            else:
                cols = st.number_input("Cols", 1, 4, 1)

            c3, c4 = st.columns(2)
            s_v = c3.number_input("Pitch (sv)", 30, 200, 70)
            s_h = c4.number_input("Gauge (sh)", 0, 200, 0 if cols==1 else 70, disabled=(cols==1))

        # --- TAB 2: Plate & Load Position (Reductions) ---
        with in_tab2:
            st.caption("Plate Dimensions")
            c1, c2 = st.columns(2)
            t_plate = c1.number_input("Thickness (t)", 4, 50, 9)
            weld_sz = c2.number_input("Weld Size", 3, 20, 6)
            
            k1, k2 = st.columns(2)
            lv = k1.number_input("Edge V (lv)", 20, 150, 35)
            leh = k2.number_input("Edge H (leh)", 20, 150, 35)

            # --- SECTION: Load Position & Reductions ---
            st.divider()
            st.markdown("##### 📐 Load Position & Reductions")
            st.caption(f"Determines Eccentricity ($e = e1 + x_{{bar}}$)")
            
            k3, k4 = st.columns(2)
            is_end = "End" in conn_type
            
            # e1 และ setback ย้ายมาอยู่ที่นี่ตาม request
            e1 = k3.number_input("e1 (Bolt-to-Support)", 30, 150, 40, disabled=is_end, help="Distance from Weld/Support to first bolt line.")
            setback = k4.number_input("Setback (Gap)", 0, 50, 10, disabled=is_end, help="Installation clearance.")

        # 2. Gather Inputs
        user_inputs = {
            'd': d_bolt, 'rows': rows, 'cols': cols, 's_v': s_v, 's_h': s_h,
            't': t_plate, 'weld_size': weld_sz,
            'lv': lv, 'leh': leh, 'e1': e1, 'setback': setback
        }
        plate_geom = calculate_plate_geometry(conn_type, user_inputs)
        
        # 3. Quick Check (Status Bar)
        check_res = calculate_quick_check(user_inputs, plate_geom, V_design_kg, default_mat_grade)
        
        st.divider()
        st.subheader("🏁 Quick Status")
        for k, v in check_res['checks'].items():
            icon = "✅" if v >= V_design_kg else "❌"
            st.write(f"{icon} **{k}:** {v:,.0f} kg")
        
        ratio_color = "red" if check_res['ratio'] > 1.0 else "green"
        st.markdown(f"**Ratio:** :{ratio_color}[{check_res['ratio']:.2f}]")

    # --- Drawing Area ---
    with col_draw:
        t1, t2, t3 = st.tabs(["🖼️ Front View", "📐 Side View", "🔝 Plan View"])
        with t1: st.plotly_chart(dw.create_front_view(section_data, plate_geom, user_inputs), use_container_width=True)
        with t2: st.plotly_chart(dw.create_side_view(section_data, plate_geom, user_inputs), use_container_width=True)
        with t3: st.plotly_chart(dw.create_plan_view(section_data, plate_geom, user_inputs), use_container_width=True)

    # --- GENERATE REPORT SECTION ---
    st.markdown("---")
    col_btn, col_info = st.columns([1, 2])
    
    if col_btn.button("📄 Generate Calculation Report", type="primary", use_container_width=True):
        
        # 1. Prepare Data for Report (Unit Conversion: kg -> kN, MPa)
        # Load
        V_kN = V_design_kg * 9.81 / 1000.0
        
        # Material
        is_sm520 = "SM520" in default_mat_grade
        Fy_val = 355 if is_sm520 else 245  # MPa
        Fu_val = 520 if is_sm520 else 400  # MPa
        
        # Beam Data
        beam_dict = {
            'tw': section_data.get('tw', 6),
            'Fu': Fu_val # Assume same grade
        }
        
        # Plate Data
        plate_dict = {
            't': t_plate,
            'h': plate_geom['h'],
            'w': plate_geom['w'],  # <--- [ADDED] เพิ่มบรรทัดนี้แล้วครับ
            'Fy': Fy_val,
            'Fu': Fu_val,
            'weld_size': weld_sz,
            'e1': e1,       # For eccentricity
            'lv': lv,       # For Block Shear
            'l_side': leh   # For Block Shear
        }
        
        # Bolt Data
        # Fnv for A325 approx 372 MPa (Threads included)
        fnv_val = 372 
        bolt_dict = {
            'd': d_bolt,
            'rows': rows,
            'cols': cols,
            's_v': s_v,
            's_h': s_h,
            'Fnv': fnv_val 
        }

        # 2. Call the external report generator
        try:
            report_md = cr.generate_report(
                V_load=V_kN,
                beam=beam_dict,
                plate=plate_dict,
                bolts=bolt_dict,
                is_lrfd=is_lrfd,
                material_grade=default_mat_grade,
                bolt_grade=default_bolt_grade
            )
            
            # 3. Display Result
            with st.container():
                st.success("✅ Report Generated Successfully!")
                with st.expander("📜 View Calculation Note", expanded=True):
                    st.markdown(report_md)
                    
        except Exception as e:
            st.error(f"❌ Error Generating Report: {e}")
