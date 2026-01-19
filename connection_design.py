import streamlit as st
import math
import drawing_utils as dw
import calculation_report as cr 

# ==========================================
# 🗄️ 0. DATABASES (THAI & STANDARDS)
# ==========================================

BOLT_DB = {
    "Grade 8.8 (ISO)":   {"Fnv": 372, "Fnt": 620, "Fu": 800,  "Desc": "น็อตรับแรงดึงสูง (นิยมสุดในไทย)"},
    "A325 (ASTM)":       {"Fnv": 372, "Fnt": 620, "Fu": 825,  "Desc": "น็อตโครงสร้าง มาตรฐานอเมริกา"},
    "F10T (JIS)":        {"Fnv": 469, "Fnt": 780, "Fu": 1000, "Desc": "น็อต T.C. Bolt (หัวกลม) มาตรฐานญี่ปุ่น"},
    "Grade 10.9 (ISO)":  {"Fnv": 469, "Fnt": 780, "Fu": 1000, "Desc": "น็อตรับแรงดึงสูงมาก (เทียบเท่า A490)"},
    "A490 (ASTM)":       {"Fnv": 469, "Fnt": 780, "Fu": 1035, "Desc": "น็อตรับแรงสูงพิเศษ"},
    "Grade 4.6 (ISO)":   {"Fnv": 165, "Fnt": 310, "Fu": 400,  "Desc": "น็อตดำ/น็อตชุบ (ห้ามใช้รับแรงหลัก)"},
}

# ตารางระยะขอบต่ำสุด (AISC Table J3.4) หน่วย mm
# Key: Bolt Diameter, Value: Min Edge Distance
AISC_MIN_EDGE = {12: 20, 16: 22, 20: 34, 22: 38, 24: 42, 27: 48, 30: 52}

# ==========================================
# 🧮 1. ENGINEERING LOGIC (ADVANCED)
# ==========================================

def calculate_plate_geometry(conn_type, user_inputs):
    """คำนวณขนาดแผ่นเหล็ก (กว้าง x สูง) อัตโนมัติ"""
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

def check_geometry_compliance(inputs):
    """ฟังก์ชันตรวจสอบระยะตามมาตรฐาน (Code Check)"""
    warnings = []
    d = inputs['d']
    min_edge = AISC_MIN_EDGE.get(d, d * 1.75) # Fallback if not in table
    
    # 1. Edge Distance Check
    if inputs['lv'] < min_edge or inputs['leh'] < min_edge:
        warnings.append(f"⚠️ ระยะขอบน้อยกว่ามาตรฐาน (Min {min_edge} mm)")
        
    # 2. Spacing Check (Min 2.67d, Preferred 3d)
    min_spacing = 2.67 * d
    pref_spacing = 3.0 * d
    if inputs['s_v'] < min_spacing:
        warnings.append(f"⚠️ ระยะห่างรูเจาะ (Pitch) ชิดเกินไป (Min {min_spacing:.1f} mm)")
    
    if inputs['cols'] > 1 and inputs['s_h'] < min_spacing:
        warnings.append(f"⚠️ ระยะห่างแถว (Gauge) ชิดเกินไป (Min {min_spacing:.1f} mm)")

    return warnings

def calculate_advanced_checks(inputs, plate_geom, V_load, Fy, Fu, phi_factors):
    """
    คำนวณ Advanced Failure Modes:
    1. Bearing & Tearout
    2. Block Shear
    3. Plate Flexure
    """
    phi_r = phi_factors['phi_r'] # 0.75 for LRFD
    phi_y = phi_factors['phi_y'] # 0.90 for LRFD
    
    d = inputs['d']
    d_hole = d + 2.0 # Standard hole size
    t = inputs['t']
    rows = inputs['rows']
    cols = inputs['cols']
    
    adv_results = {}
    
    # --- 1. Bolt Bearing & Tearout (AISC J3.10) ---
    # คำนวณระยะ Lc สำหรับน็อตตัวริมและตัวใน
    lc_edge = inputs['lv'] - (d_hole / 2.0)
    lc_inner = inputs['s_v'] - d_hole
    
    # กำลังรับแรงต่อตัว (Rn)
    # Tearout Limit: 1.2 * Lc * t * Fu
    # Bearing Limit: 2.4 * d * t * Fu
    rn_edge = min(1.2 * lc_edge * t * Fu, 2.4 * d * t * Fu)
    rn_inner = min(1.2 * lc_inner * t * Fu, 2.4 * d * t * Fu)
    
    # รวมกำลังรับแรงทั้งหมด
    # สมมติ Column เดียว: 2 ตัวริม (บน/ล่าง) + (Rows-2) ตัวใน
    # ถ้ามีหลาย Column ก็คูณจำนวน Column
    if rows >= 2:
        total_rn_bearing = (2 * rn_edge + (rows - 2) * rn_inner) * cols
    else:
        total_rn_bearing = rn_edge * cols
        
    adv_results['Bolt Bearing'] = total_rn_bearing * phi_r

    # --- 2. Block Shear (AISC J4.3) ---
    # สมมติการวิบัติรูปตัว U หรือ L (Shear ตามแนวตั้ง + Tension ตามแนวนอน)
    # Agv = Gross area in shear
    # Anv = Net area in shear
    # Ant = Net area in tension
    
    # Shear Length (ความยาวแนวเชื่อมถึงน็อตตัวสุดท้าย)
    L_shear = (rows - 1) * inputs['s_v'] + inputs['lv']
    Agv = L_shear * t * cols # คิดทุก col (Simplified)
    Anv = (L_shear - (rows - 0.5) * d_hole) * t * cols
    
    # Tension Length (ระยะขอบแนวนอน)
    Ant = (inputs['leh'] - 0.5 * d_hole) * t * cols
    
    Ubs = 1.0 # Uniform tension stress
    
    # Rn = min(0.6*Fu*Anv + Ubs*Fu*Ant, 0.6*Fy*Agv + Ubs*Fu*Ant)
    Rn_block_1 = 0.6 * Fu * Anv + Ubs * Fu * Ant
    Rn_block_2 = 0.6 * Fy * Agv + Ubs * Fu * Ant
    
    adv_results['Block Shear'] = min(Rn_block_1, Rn_block_2) * phi_r

    # --- 3. Plate Flexure (Gross Yielding due to Eccentricity) ---
    # สำหรับ Fin Plate หรือแผ่นที่มีความเยื้องศูนย์
    if inputs['e1'] > 0:
        Mu = V_load * inputs['e1'] # Moment = V * e
        Z_gross = (t * plate_geom['h']**2) / 4.0 # Plastic Modulus of Plate
        Mn = Fy * Z_gross
        
        # แปลงกลับเป็น V ที่รับได้เพื่อให้เทียบง่ายๆ (V_cap = Mn / e)
        # ใช้ 0.90 สำหรับ Yielding
        if inputs['e1'] > 0:
            adv_results['Plate Flexure'] = (Mn * phi_y) / inputs['e1']
        else:
            adv_results['Plate Flexure'] = 999999
    
    return adv_results

def calculate_quick_check(inputs, plate_geom, V_load_kg, T_load_kg, mat_grade, bolt_data):
    """Main Logic รวม Basic + Advanced Checks"""
    
    # 1. Setup Phi Factors
    method_raw = st.session_state.get('design_method', 'LRFD (Limit State)')
    is_lrfd = "LRFD" in method_raw
    if is_lrfd:
        factors = {'phi_y': 0.90, 'phi_r': 0.75, 'phi_w': 0.75}
    else:
        factors = {'phi_y': 1/1.5, 'phi_r': 1/2.0, 'phi_w': 1/2.0}

    # 2. Material
    if "SS400" in mat_grade: Fy, Fu = 24.5, 41.0   
    elif "SM520" in mat_grade: Fy, Fu = 36.0, 53.0
    else: Fy, Fu = 25.0, 41.0 

    # 3. Basic Checks
    Fnv_kg = bolt_data['Fnv'] / 9.81
    Fnt_kg = bolt_data['Fnt'] / 9.81
    d = inputs['d']
    n_bolts = inputs['rows'] * inputs['cols']
    t = inputs['t']
    
    results = {}
    
    # Bolt Shear & Tension
    Ab = (math.pi * d**2) / 4
    Rn_shear_total = Fnv_kg * Ab * n_bolts * factors['phi_r']
    
    if T_load_kg > 0:
        Rn_tension_total = Fnt_kg * Ab * n_bolts * factors['phi_r']
        ratio_v = V_load_kg / Rn_shear_total
        ratio_t = T_load_kg / Rn_tension_total
        interaction = ratio_v**2 + ratio_t**2
        results['Bolt Interaction'] = 1.0 / interaction if interaction > 0 else 999
    else:
        results['Bolt Shear'] = Rn_shear_total

    # Plate Yield (Shear Yielding)
    h_p = plate_geom['h']
    results['Plate Yield (Shear)'] = 0.60 * Fy * (h_p * t) * factors['phi_y']

    # Weld Check
    w_sz = inputs['weld_size']
    L_weld = h_p * 2 
    Fexx = 49.0 
    Rn_weld = 0.60 * Fexx * 0.707 * w_sz * L_weld * factors['phi_w']
    results['Weld Strength'] = Rn_weld
    
    # --- 4. Call Advanced Checks ---
    adv_checks = calculate_advanced_checks(inputs, plate_geom, V_load_kg, Fy, Fu, factors)
    results.update(adv_checks) # รวมผลลัพธ์เข้าไป

    # 5. Determine Final Status
    if T_load_kg > 0:
        limit_check = 1.0
        ratio = interaction if 'interaction' in locals() else 0
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
# 🖥️ 2. UI RENDERING (UPDATED)
# ==========================================

def render_connection_tab(V_design_from_tab1, default_bolt_size, method, is_lrfd, section_data, conn_type, default_bolt_grade, default_mat_grade):
    
    V_design_kg = V_design_from_tab1
    current_method = st.session_state.get('design_method', method)
    
    col_input, col_draw = st.columns([1, 1.8])
    
    with col_input:
        st.markdown(f"""
        <div style="background-color:#eff6ff; padding:15px; border-radius:8px; border-left:5px solid #3b82f6; margin-bottom:15px;">
            <div style="font-size:12px; color:#6b7280; font-weight:bold;">DESIGN SHEAR ({current_method})</div>
            <div style="font-size:26px; font-weight:800; color:#1e3a8a;">{V_design_kg:,.0f} kg</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("##### 🛠️ Design Parameters")
        
        row_mat = st.columns(2)
        bolt_grade_name = row_mat[0].selectbox("🔩 Bolt Grade", list(BOLT_DB.keys()), index=0)
        selected_bolt = BOLT_DB[bolt_grade_name]
        
        mat_options = ["SS400 (Fy 245)", "SM520 (Fy 355)", "A36 (Fy 250)"]
        sel_mat_grade = row_mat[1].selectbox("🛡️ Plate Grade", mat_options)
        
        # Thread Condition
        st.write("---")
        st.caption("⚙️ Bolt Condition")
        thread_cond = st.radio("Shear Plane Condition:", ["Threads Included (N)", "Threads Excluded (X)"], index=0, horizontal=True)

        # Fnv Logic
        final_Fnv = selected_bolt['Fnv'] 
        if "Excluded" in thread_cond:
            if "Grade 8.8" in bolt_grade_name or "A325" in bolt_grade_name: final_Fnv = 457
            elif "Grade 10.9" in bolt_grade_name or "A490" in bolt_grade_name: final_Fnv = 579
            else: final_Fnv = final_Fnv * 1.25

        st.info(f"ℹ️ **Design Strength:** $F_{{nv}} = {final_Fnv}$ MPa")

        # Tabs
        in_tab1, in_tab2, in_tab3 = st.tabs(["📏 Geometry", "📐 Detailing", "⚙️ Advanced"])

        with in_tab1:
            c1, c2 = st.columns(2)
            d_bolt = c1.selectbox("Bolt Size (mm)", [12, 16, 20, 22, 24, 27, 30], index=2)
            t_plate = c2.number_input("Plate Thk (t)", 4.0, 50.0, 9.0, step=1.0)
            c3, c4 = st.columns(2)
            rows = c3.number_input("Rows", 2, 20, 3)
            cols = 2 if "End" in conn_type else c4.number_input("Cols", 1, 4, 1)

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

        with in_tab3:
            st.info("Additional Forces & Checks")
            T_design_kg = st.number_input("Axial Tension (kg)", 0.0, 50000.0, 0.0, step=100.0)
            has_cope = st.checkbox("Coped Beam? (บากคาน)", value=False)
            if has_cope:
                cc1, cc2 = st.columns(2)
                cope_d = cc1.number_input("Cope Depth (dc)", 0.0, 200.0, 30.0)
                cope_c = cc2.number_input("Cope Length (c)", 0.0, 200.0, 100.0)
            else:
                cope_d, cope_c = 0, 0

        # Gather Inputs
        user_inputs = {
            'd': d_bolt, 'rows': rows, 'cols': cols, 's_v': s_v, 's_h': s_h,
            't': t_plate, 'weld_size': weld_sz,
            'lv': lv, 'leh': leh, 'e1': e1, 'setback': setback,
            'T_load': T_design_kg, 
            'cope': {'has_cope': has_cope, 'dc': cope_d, 'c': cope_c}
        }
        
        plate_geom = calculate_plate_geometry(conn_type, user_inputs)
        
        # Check Compliance (Standard Checks)
        geom_warnings = check_geometry_compliance(user_inputs)
        if geom_warnings:
            with st.expander("⚠️ Standard Warnings", expanded=True):
                for w in geom_warnings: st.warning(w)

        # Run Calculations
        bolt_data_for_calc = selected_bolt.copy()
        bolt_data_for_calc['Fnv'] = final_Fnv
        check_res = calculate_quick_check(
            user_inputs, plate_geom, V_design_kg, T_design_kg, 
            sel_mat_grade, bolt_data_for_calc
        )
        
        # --- Display Results ---
        st.divider()
        st.subheader("🏁 Quick Status")
        
        # แยกหมวดหมู่การแสดงผล
        basic_keys = ['Bolt Shear', 'Plate Yield (Shear)', 'Weld Strength', 'Bolt Interaction']
        adv_keys = ['Bolt Bearing', 'Block Shear', 'Plate Flexure']
        
        # 1. Basic Checks
        for k in basic_keys:
            if k in check_res['checks']:
                val = check_res['checks'][k]
                if k == 'Bolt Interaction':
                     st.write(f"{'✅ PASS' if val >= 1.0 else '❌ FAIL'} **{k}**")
                else:
                    limit = math.sqrt(V_design_kg**2 + T_design_kg**2) if "Weld" in k else V_design_kg
                    icon = "✅" if val >= limit else "❌"
                    st.write(f"{icon} **{k}:** {val:,.0f} kg")

        # 2. Critical Limit States (Advanced)
        st.markdown("---")
        st.caption("🚨 Critical Limit States (Advanced)")
        for k in adv_keys:
            if k in check_res['checks']:
                val = check_res['checks'][k]
                icon = "✅" if val >= V_design_kg else "❌"
                st.write(f"{icon} **{k}:** {val:,.0f} kg")

        # Final Ratio
        ratio_val = check_res['ratio']
        ratio_color = "red" if ratio_val > 1.0 else "green"
        st.markdown(f"**Utility Ratio:** :{ratio_color}[{ratio_val:.2f}]")

    with col_draw:
        t1, t2, t3 = st.tabs(["🖼️ Front View", "📐 Side View", "🔝 Plan View"])
        with t1: st.plotly_chart(dw.create_front_view(section_data, plate_geom, user_inputs), use_container_width=True)
        with t2: st.plotly_chart(dw.create_side_view(section_data, plate_geom, user_inputs), use_container_width=True)
        with t3: st.plotly_chart(dw.create_plan_view(section_data, plate_geom, user_inputs), use_container_width=True)

    # Report Gen
    st.markdown("---")
    if st.button("📄 Generate Calculation Report", type="primary", use_container_width=True):
        # ... (Report generation code remains mostly same, just pass updated checks if needed) ...
        # For simplicity, keeping the report call structure same as user has it working.
        # Ideally, you'd pass the new failure modes to the report generator too.
        
        V_kN = V_design_kg * 9.81 / 1000.0
        T_kN = T_design_kg * 9.81 / 1000.0
        is_sm520 = "SM520" in sel_mat_grade
        Fy_plate = 355 if is_sm520 else 245
        Fu_plate = 520 if is_sm520 else 400
        
        bolt_dict = {
            'd': d_bolt, 'rows': rows, 'cols': cols, 's_v': s_v, 's_h': s_h,
            'Fnv': final_Fnv, 'Fnt': selected_bolt['Fnt'], 'Fu':  selected_bolt['Fu']
        }
        beam_dict = { 'tw': section_data.get('tw', 6), 'Fy': section_data.get('Fy', 245), 'Fu': section_data.get('Fu', 400) }
        plate_dict = {
            't': t_plate, 'h': plate_geom['h'], 'w': plate_geom['w'],
            'Fy': Fy_plate, 'Fu': Fu_plate, 'weld_size': weld_sz,
            'e1': e1, 'lv': lv, 'l_side': leh
        }
        
        try:
            report_md = cr.generate_report(
                V_load=V_kN, T_load=T_kN, beam=beam_dict, plate=plate_dict,
                bolts=bolt_dict, cope=user_inputs['cope'], is_lrfd=is_lrfd,
                material_grade=sel_mat_grade, bolt_grade=bolt_grade_name 
            )
            with st.container():
                st.success("✅ Detailed Calculation Report Created!")
                with st.expander("📜 View Full Calculation Note", expanded=True):
                    st.markdown(report_md)
        except Exception as e:
            st.error(f"❌ Error generating report: {e}")
