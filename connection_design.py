import streamlit as st
import math
import drawing_utils as dw
import calculation_report as cr 

# ==========================================
# 🗄️ 0. DATABASES (THAI & STANDARDS)
# ==========================================

# Database เกรดน็อตที่ใช้จริงในไทย (Strength หน่วย MPa)
BOLT_DB = {
    "Grade 8.8 (ISO)":   {"Fnv": 372, "Fnt": 620, "Fu": 800,  "Desc": "น็อตรับแรงดึงสูง (นิยมสุดในไทย)"},
    "A325 (ASTM)":       {"Fnv": 372, "Fnt": 620, "Fu": 825,  "Desc": "น็อตโครงสร้าง มาตรฐานอเมริกา"},
    "F10T (JIS)":        {"Fnv": 469, "Fnt": 780, "Fu": 1000, "Desc": "น็อต T.C. Bolt (หัวกลม) มาตรฐานญี่ปุ่น"},
    "Grade 10.9 (ISO)":  {"Fnv": 469, "Fnt": 780, "Fu": 1000, "Desc": "น็อตรับแรงดึงสูงมาก (เทียบเท่า A490)"},
    "A490 (ASTM)":       {"Fnv": 469, "Fnt": 780, "Fu": 1035, "Desc": "น็อตรับแรงสูงพิเศษ"},
    "Grade 4.6 (ISO)":   {"Fnv": 165, "Fnt": 310, "Fu": 400,  "Desc": "น็อตดำ/น็อตชุบ (ห้ามใช้รับแรงหลัก)"},
}

# ==========================================
# 🧮 1. ENGINEERING LOGIC
# ==========================================

def calculate_plate_geometry(conn_type, user_inputs):
    """คำนวณขนาดแผ่นเหล็ก (กว้าง x สูง) อัตโนมัติ"""
    rows, cols = user_inputs['rows'], user_inputs['cols']
    sv, sh = user_inputs['s_v'], user_inputs['s_h']
    lv, leh = user_inputs['lv'], user_inputs['leh']
    e1, setback = user_inputs['e1'], user_inputs['setback']
    
    # ความสูง (Height)
    calc_h = (2 * lv) + ((rows - 1) * sv)
    
    # ความกว้าง (Width) ขึ้นอยู่กับประเภท
    if "Fin" in conn_type:
        calc_w = setback + e1 + ((cols - 1) * sh) + leh
    elif "End" in conn_type:
         calc_w = (2 * leh) + sh
    else: 
        calc_w = e1 + leh 
        
    return {'h': calc_h, 'w': calc_w, 'type': conn_type}

def calculate_quick_check(inputs, plate_geom, V_load_kg, T_load_kg, mat_grade, bolt_data):
    """คำนวณ Quick Check สำหรับแสดงผลหน้าจอทันที"""
    
    # 1. Setup Phi Factors
    method_raw = st.session_state.get('design_method', 'LRFD (Limit State)')
    is_lrfd = "LRFD" in method_raw
    if is_lrfd:
        phi_y, phi_r, phi_w = 0.90, 0.75, 0.75
    else:
        phi_y, phi_r, phi_w = 1/1.50, 1/2.00, 1/2.00

    # 2. Material Strength lookup
    if "SS400" in mat_grade: Fy, Fu = 24.5, 41.0   # kg/mm2 approx
    elif "SM520" in mat_grade: Fy, Fu = 36.0, 53.0
    else: Fy, Fu = 25.0, 41.0 # Default A36

    # 3. Bolt Properties (From DB & Condition)
    # Convert MPa to kg/mm2 roughly for Quick Check (MPa / 9.81)
    Fnv_kg = bolt_data['Fnv'] / 9.81
    Fnt_kg = bolt_data['Fnt'] / 9.81
    
    d = inputs['d']
    n_bolts = inputs['rows'] * inputs['cols']
    t = inputs['t']
    
    results = {}

    # --- Check 1: Bolt Shear & Tension ---
    Ab = (math.pi * d**2) / 4
    Rn_shear_total = Fnv_kg * Ab * n_bolts * phi_r
    
    if T_load_kg > 0:
        # Combined Check (Simplified Circular Interaction)
        Rn_tension_total = Fnt_kg * Ab * n_bolts * phi_r
        
        ratio_v = V_load_kg / Rn_shear_total
        ratio_t = T_load_kg / Rn_tension_total
        
        # Interaction formula: (V/Vn)^2 + (T/Tn)^2 <= 1.0
        interaction = ratio_v**2 + ratio_t**2
        
        # Store for display
        results['Bolt Interaction'] = 1.0 / interaction if interaction > 0 else 999
        min_cap_bolt = Rn_shear_total # Just for reference in display
    else:
        results['Bolt Shear'] = Rn_shear_total
        min_cap_bolt = Rn_shear_total

    # --- Check 2: Plate Yield ---
    h_p = plate_geom['h']
    # Gross Yielding
    results['Plate Yielding'] = 0.60 * Fy * (h_p * t) * phi_y

    # --- Check 3: Weld ---
    w_sz = inputs['weld_size']
    L_weld = h_p * 2 # 2 sides
    Fexx = 49.0 # E70 electrode (approx 480 MPa)
    
    # Resultant load for weld
    R_load = math.sqrt(V_load_kg**2 + T_load_kg**2)
    Rn_weld = 0.60 * Fexx * 0.707 * w_sz * L_weld * phi_w
    results['Weld Strength'] = Rn_weld

    # Determine Final Status
    if T_load_kg > 0:
        ratio = interaction if 'interaction' in locals() else 0
        limit_check = 1.0
    else:
        min_cap = min(results.values())
        ratio = V_load_kg / min_cap if min_cap > 0 else 999
        limit_check = 1.0
    
    return {
        'checks': results,
        'ratio': ratio,
        'status': "PASS" if ratio <= 1.0 else "FAIL"
    }

# ==========================================
# 🖥️ 2. UI RENDERING (MAIN FUNCTION)
# ==========================================

def render_connection_tab(V_design_from_tab1, default_bolt_size, method, is_lrfd, section_data, conn_type, default_bolt_grade, default_mat_grade):
    
    V_design_kg = V_design_from_tab1
    current_method = st.session_state.get('design_method', method)
    
    # --- Layout Structure ---
    col_input, col_draw = st.columns([1, 1.8])
    
    with col_input:
        # Display Load Header
        st.markdown(f"""
        <div style="background-color:#eff6ff; padding:15px; border-radius:8px; border-left:5px solid #3b82f6; margin-bottom:15px;">
            <div style="font-size:12px; color:#6b7280; font-weight:bold;">DESIGN SHEAR ({current_method})</div>
            <div style="font-size:26px; font-weight:800; color:#1e3a8a;">{V_design_kg:,.0f} kg</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("##### 🛠️ Design Parameters")
        
        # 1. Section & Material Inputs
        row_mat = st.columns(2)
        
        # Bolt Grade Selection (Thai Database)
        bolt_grade_name = row_mat[0].selectbox("🔩 Bolt Grade", list(BOLT_DB.keys()), index=0)
        selected_bolt = BOLT_DB[bolt_grade_name]
        
        # Plate Material
        mat_options = ["SS400 (Fy 245)", "SM520 (Fy 355)", "A36 (Fy 250)"]
        def_idx = 0
        if "SM520" in default_mat_grade: def_idx = 1
        elif "A36" in default_mat_grade: def_idx = 2
        sel_mat_grade = row_mat[1].selectbox("🛡️ Plate Grade", mat_options, index=def_idx)
        
        # ---------------------------------------------------------
        # ⚙️ Thread Condition Logic (รวม/ไม่รวมเกลียว)
        # ---------------------------------------------------------
        st.write("---")
        st.caption("⚙️ Bolt Condition (เงื่อนไขเกลียว)")
        thread_cond = st.radio(
            "Shear Plane Condition:",
            ["Threads Included (N) - เกลียวอยู่ในระนาบตัด", 
             "Threads Excluded (X) - เกลียวอยู่นอกระนาบตัด"],
            index=0, # Default เป็น N (Safe ไว้ก่อน)
            horizontal=True
        )

        # คำนวณ Fnv จริง
        final_Fnv = selected_bolt['Fnv'] 
        if "Excluded" in thread_cond:
            # เพิ่ม Strength กรณีเกลียวอยู่นอกระนาบ (Type X)
            if "Grade 8.8" in bolt_grade_name or "A325" in bolt_grade_name:
                final_Fnv = 457 # (372 -> 457 MPa)
            elif "Grade 10.9" in bolt_grade_name or "A490" in bolt_grade_name:
                final_Fnv = 579 # (469 -> 579 MPa)
            else:
                final_Fnv = final_Fnv * 1.25 # เผื่อไว้สำหรับเกรดอื่น

        st.info(f"ℹ️ **Design Strength:** $F_{{nv}} = {final_Fnv}$ MPa ({'Type X' if 'Excluded' in thread_cond else 'Type N'})")
        # ---------------------------------------------------------

        # 2. Tabs for Configuration
        in_tab1, in_tab2, in_tab3 = st.tabs(["📏 Geometry", "📐 Detailing", "⚙️ Advanced"])

        # TAB 1: Geometry
        with in_tab1:
            c1, c2 = st.columns(2)
            d_bolt = c1.selectbox("Bolt Size (mm)", [12, 16, 20, 22, 24, 27, 30], index=2)
            t_plate = c2.number_input("Plate Thk (t)", 4.0, 50.0, 9.0, step=1.0)
            c3, c4 = st.columns(2)
            rows = c3.number_input("Rows", 2, 20, 3)
            cols = 2 if "End" in conn_type else c4.number_input("Cols", 1, 4, 1)

        # TAB 2: Detailing
        with in_tab2:
            c1, c2 = st.columns(2)
            s_v = c1.number_input("Pitch (sv)", 30.0, 200.0, 70.0, step=5.0)
            s_h = c2.number_input("Gauge (sh)", 0.0, 200.0, 0.0 if cols==1 else 70.0, disabled=(cols==1), step=5.0)
            c3, c4 = st.columns(2)
            lv = c3.number_input("Edge V (lv)", 20.0, 150.0, 35.0, step=5.0)
            leh = c4.number_input("Edge H (leh)", 20.0, 150.0, 35.0, step=5.0)
            
            st.divider()
            k1, k2 = st.columns(2)
            weld_sz = k1.number_input("Weld Size", 3.0, 20.0, 6.0, step=1.0)
            is_end = "End" in conn_type
            e1 = k2.number_input("Eccentricity (e1)", 30.0, 150.0, 40.0, disabled=is_end, step=5.0)
            setback = st.number_input("Setback", 0.0, 50.0, 10.0, disabled=is_end) if not is_end else 0

        # TAB 3: Advanced (Cope & Tension)
        with in_tab3:
            st.info("Additional Forces & Beam Checks")
            
            # Axial Load
            T_design_kg = st.number_input("Axial Tension (kg)", 0.0, 50000.0, 0.0, step=100.0, help="แรงดึงตามแนวแกน (ถ้ามี)")
            
            # Coped Beam
            has_cope = st.checkbox("Coped Beam? (บากคาน)", value=False)
            if has_cope:
                cc1, cc2 = st.columns(2)
                cope_d = cc1.number_input("Cope Depth (dc)", 0.0, 200.0, 30.0)
                cope_c = cc2.number_input("Cope Length (c)", 0.0, 200.0, 100.0)
            else:
                cope_d, cope_c = 0, 0

        # Gather Inputs for Logic
        user_inputs = {
            'd': d_bolt, 'rows': rows, 'cols': cols, 's_v': s_v, 's_h': s_h,
            't': t_plate, 'weld_size': weld_sz,
            'lv': lv, 'leh': leh, 'e1': e1, 'setback': setback,
            'T_load': T_design_kg, 
            'cope': {'has_cope': has_cope, 'dc': cope_d, 'c': cope_c}
        }
        
        # Calculate Geometry
        plate_geom = calculate_plate_geometry(conn_type, user_inputs)
        
        # Prepare Bolt Data with *Modified* Fnv for Quick Check
        bolt_data_for_calc = selected_bolt.copy()
        bolt_data_for_calc['Fnv'] = final_Fnv

        # Run Quick Check
        check_res = calculate_quick_check(
            user_inputs, plate_geom, V_design_kg, T_design_kg, 
            sel_mat_grade, bolt_data_for_calc
        )
        
        # --- Display Quick Results ---
        st.divider()
        st.subheader("🏁 Quick Status")
        
        for k, v in check_res['checks'].items():
            if k == "Bolt Interaction":
                 # Interaction Check (Value is Ratio approx)
                 status_txt = "✅ PASS" if v >= 1.0 else "❌ FAIL"
                 st.write(f"{status_txt} **{k}** (Combined Check)")
            else:
                # Force Check
                if T_design_kg > 0 and k == 'Bolt Shear': continue # Skip individual if combined
                
                # Check Weld resultant
                limit = math.sqrt(V_design_kg**2 + T_design_kg**2) if "Weld" in k else V_design_kg
                
                icon = "✅" if v >= limit else "❌"
                st.write(f"{icon} **{k}:** {v:,.0f} kg")
        
        # Final Ratio Display
        ratio_val = check_res['ratio']
        ratio_color = "red" if ratio_val > 1.0 else "green"
        st.markdown(f"**Utility Ratio:** :{ratio_color}[{ratio_val:.2f}]")

    # --- Drawing Area ---
    with col_draw:
        t1, t2, t3 = st.tabs(["🖼️ Front View", "📐 Side View", "🔝 Plan View"])
        with t1: st.plotly_chart(dw.create_front_view(section_data, plate_geom, user_inputs), use_container_width=True)
        with t2: st.plotly_chart(dw.create_side_view(section_data, plate_geom, user_inputs), use_container_width=True)
        with t3: st.plotly_chart(dw.create_plan_view(section_data, plate_geom, user_inputs), use_container_width=True)

    # ==========================================
    # 📄 REPORT GENERATION
    # ==========================================
    st.markdown("---")
    if st.button("📄 Generate Calculation Report", type="primary", use_container_width=True):
        
        # 1. Convert Units (kg -> kN)
        V_kN = V_design_kg * 9.81 / 1000.0
        T_kN = T_design_kg * 9.81 / 1000.0
        
        # 2. Material Parsing
        is_sm520 = "SM520" in sel_mat_grade
        Fy_plate = 355 if is_sm520 else 245
        Fu_plate = 520 if is_sm520 else 400
        
        # 3. Bolt Parsing (ส่งค่าที่ปรับ Fnv แล้ว)
        bolt_dict = {
            'd': d_bolt, 
            'rows': rows, 
            'cols': cols, 
            's_v': s_v, 
            's_h': s_h,
            'Fnv': final_Fnv,        # <--- Critical: ใช้ค่า Fnv ที่ผ่าน Logic เกลียวแล้ว
            'Fnt': selected_bolt['Fnt'],
            'Fu':  selected_bolt['Fu']
        }

        # 4. Beam & Plate Data
        beam_dict = { 
            'tw': section_data.get('tw', 6), 
            'Fy': section_data.get('Fy', 245), 
            'Fu': section_data.get('Fu', 400)
        }
        
        plate_dict = {
            't': t_plate, 'h': plate_geom['h'], 'w': plate_geom['w'],
            'Fy': Fy_plate, 'Fu': Fu_plate, 'weld_size': weld_sz,
            'e1': e1, 'lv': lv, 'l_side': leh
        }
        
        # 5. Call Report Generator
        try:
            report_md = cr.generate_report(
                V_load=V_kN,
                T_load=T_kN,
                beam=beam_dict,
                plate=plate_dict,
                bolts=bolt_dict,
                cope=user_inputs['cope'],
                is_lrfd=is_lrfd,
                material_grade=sel_mat_grade, 
                bolt_grade=bolt_grade_name 
            )
            
            with st.container():
                st.success("✅ Detailed Calculation Report Created!")
                with st.expander("📜 View Full Calculation Note", expanded=True):
                    st.markdown(report_md)
        except Exception as e:
            st.error(f"❌ Error generating report: {e}")
