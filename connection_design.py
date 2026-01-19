import streamlit as st
import math
import pandas as pd
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

AISC_MIN_EDGE = {12: 20, 16: 22, 20: 34, 22: 38, 24: 42, 27: 48, 30: 52}

# ==========================================
# 🧮 1. ENGINEERING LOGIC (CORE)
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
    warnings = []
    d = inputs['d']
    min_edge = AISC_MIN_EDGE.get(d, d * 1.75)
    
    if inputs['lv'] < min_edge or inputs['leh'] < min_edge:
        warnings.append(f"⚠️ ระยะขอบน้อยกว่ามาตรฐาน (Min {min_edge} mm)")
        
    min_spacing = 2.67 * d
    if inputs['s_v'] < min_spacing:
        warnings.append(f"⚠️ ระยะห่างรูเจาะ (Pitch) ชิดเกินไป (Min {min_spacing:.1f} mm)")
    
    if inputs['cols'] > 1 and inputs['s_h'] < min_spacing:
        warnings.append(f"⚠️ ระยะห่างแถว (Gauge) ชิดเกินไป (Min {min_spacing:.1f} mm)")

    return warnings

def calculate_comprehensive_check(inputs, plate_geom, V_load_kg, T_load_kg, mat_grade, bolt_data):
    """
    Main Logic รวม Basic + Advanced Checks
    (ปรับปรุงให้ตรงกับ Detailed Report)
    """
    
    # 1. Setup Parameters
    method_raw = st.session_state.get('design_method', 'LRFD (Limit State)')
    is_lrfd = "LRFD" in method_raw
    if is_lrfd:
        phi = {'y': 0.90, 'r': 0.75, 'w': 0.75} # y=Yield, r=Rupture, w=Weld
    else:
        phi = {'y': 1/1.5, 'r': 1/2.0, 'w': 1/2.0} # ASD Factors approx

    if "SS400" in mat_grade: Fy, Fu = 24.5, 41.0   
    elif "SM520" in mat_grade: Fy, Fu = 36.0, 53.0
    else: Fy, Fu = 25.0, 41.0 # A36 approx

    # Basic Vars
    d = inputs['d']
    d_hole = d + 2.0
    t = inputs['t']
    rows, cols = inputs['rows'], inputs['cols']
    n_bolts = rows * cols
    
    check_list = [] # เก็บผลลัพธ์เป็น list ของ dict

    # --- CHECK 1: Bolt Shear ---
    Fnv_kg = bolt_data['Fnv'] / 9.81
    Ab = (math.pi * d**2) / 4
    Rn_shear = Fnv_kg * Ab * n_bolts
    Cap_Shear = Rn_shear * phi['r']
    check_list.append({
        "Item": "1. Bolt Shear",
        "Capacity": Cap_Shear,
        "Demand": V_load_kg,
        "Type": "Shear"
    })

    # --- CHECK 2: Bolt Tension (if any) ---
    if T_load_kg > 0:
        Fnt_kg = bolt_data['Fnt'] / 9.81
        Rn_ten = Fnt_kg * Ab * n_bolts
        Cap_Ten = Rn_ten * phi['r']
        check_list.append({
            "Item": "2. Bolt Tension",
            "Capacity": Cap_Ten,
            "Demand": T_load_kg,
            "Type": "Tension"
        })
        
        # Interaction
        r_v = V_load_kg / Cap_Shear
        r_t = T_load_kg / Cap_Ten
        int_val = r_v**2 + r_t**2
        check_list.append({
            "Item": "3. Bolt Interaction",
            "Capacity": 1.0, # Ratio Limit
            "Demand": int_val, # Actual Ratio Sum
            "IsRatio": True,
            "Type": "Combined"
        })

    # --- CHECK 3: Bolt Bearing & Tearout ---
    lc_edge = inputs['lv'] - (d_hole / 2.0)
    lc_inner = inputs['s_v'] - d_hole
    rn_edge = min(1.2 * lc_edge * t * Fu, 2.4 * d * t * Fu)
    rn_inner = min(1.2 * lc_inner * t * Fu, 2.4 * d * t * Fu)
    
    if rows >= 2:
        Rn_bearing = (2 * rn_edge + (rows - 2) * rn_inner) * cols
    else:
        Rn_bearing = rn_edge * cols
    
    Cap_Bearing = Rn_bearing * phi['r']
    check_list.append({
        "Item": "4. Bolt Bearing",
        "Capacity": Cap_Bearing,
        "Demand": V_load_kg,
        "Type": "Shear"
    })

    # --- CHECK 4: Plate Shear Yielding ---
    Agv = plate_geom['h'] * t
    Rn_y = 0.60 * Fy * Agv
    Cap_Yield = Rn_y * phi['y']
    check_list.append({
        "Item": "5. Plate Shear Yielding",
        "Capacity": Cap_Yield,
        "Demand": V_load_kg,
        "Type": "Shear"
    })

    # --- CHECK 5: Plate Shear Rupture (Net Section) ---
    Anv_plate = (plate_geom['h'] - (rows * d_hole)) * t
    Rn_rup = 0.60 * Fu * Anv_plate
    Cap_Rupture = Rn_rup * phi['r']
    check_list.append({
        "Item": "6. Plate Shear Rupture",
        "Capacity": Cap_Rupture,
        "Demand": V_load_kg,
        "Type": "Shear"
    })

    # --- CHECK 6: Block Shear ---
    L_shear = (rows - 1) * inputs['s_v'] + inputs['lv']
    Agv_bs = L_shear * t * cols 
    Anv_bs = (L_shear - (rows - 0.5) * d_hole) * t * cols
    Ant_bs = (inputs['leh'] - 0.5 * d_hole) * t * cols
    Ubs = 1.0 
    
    Rn_bs1 = 0.6 * Fu * Anv_bs + Ubs * Fu * Ant_bs
    Rn_bs2 = 0.6 * Fy * Agv_bs + Ubs * Fu * Ant_bs
    Rn_bs = min(Rn_bs1, Rn_bs2)
    Cap_Block = Rn_bs * phi['r']
    
    check_list.append({
        "Item": "7. Block Shear",
        "Capacity": Cap_Block,
        "Demand": V_load_kg,
        "Type": "Shear"
    })

    # --- CHECK 7: Weld Strength ---
    w_sz = inputs['weld_size']
    L_weld = plate_geom['h'] * 2 
    Fexx = 49.0 # E70xx
    Rn_weld = 0.60 * Fexx * 0.707 * w_sz * L_weld
    Cap_Weld = Rn_weld * phi['w']
    check_list.append({
        "Item": "8. Weld Strength",
        "Capacity": Cap_Weld,
        "Demand": V_load_kg,
        "Type": "Shear"
    })

    # --- Summary ---
    df_res = pd.DataFrame(check_list)
    
    # Calculate Ratios
    def calc_ratio(row):
        if row.get('IsRatio'): return row['Demand'] # Already a ratio
        if row['Capacity'] == 0: return 999
        return row['Demand'] / row['Capacity']

    df_res['Ratio'] = df_res.apply(calc_ratio, axis=1)
    df_res['Status'] = df_res['Ratio'].apply(lambda x: "PASS" if x <= 1.0 else "FAIL")
    
    # Max Ratio
    max_ratio = df_res['Ratio'].max()
    
    return {
        'df': df_res,
        'ratio': max_ratio,
        'status': "PASS" if max_ratio <= 1.0 else "FAIL"
    }

# ==========================================
# ⚡ 2. SMART AUTO-OPTIMIZER
# ==========================================
def run_optimization(V_target, T_target, mat_grade, bolt_grade_name, conn_type, current_inputs, 
                     fixed_bolt=None, strategy="Min Weight"):
    
    if fixed_bolt: candidate_bolts = [fixed_bolt]
    else: candidate_bolts = [16, 20, 24, 27, 30]
        
    candidate_rows = range(2, 7)
    candidate_thk = [6, 9, 10, 12, 16, 19, 20, 25] 
    
    valid_designs = []
    bolt_db_data = BOLT_DB[bolt_grade_name]
    
    for d in candidate_bolts:
        for r in candidate_rows:
            approx_cap = (d**2/100) * 2.0 * r 
            if approx_cap < (V_target/1000): continue

            for t in candidate_thk:
                temp_inputs = current_inputs.copy()
                temp_inputs.update({
                    'd': d, 'rows': r, 'cols': 1, 't': t,
                    's_v': 3.0 * d, 'lv': 1.5 * d, 'leh': 1.5 * d, 's_h': 0,
                    'weld_size': max(5, t-2)
                })

                geom = calculate_plate_geometry(conn_type, temp_inputs)
                if check_geometry_compliance(temp_inputs): continue 

                bolt_data_calc = bolt_db_data.copy() 
                res = calculate_comprehensive_check(temp_inputs, geom, V_target, T_target, mat_grade, bolt_data_calc)
                
                if res['status'] == "PASS" and res['ratio'] >= 0.40:
                    vol_mm3 = geom['h'] * geom['w'] * t
                    weight = (vol_mm3 / 1e9) * 7850 
                    
                    if strategy == "Min Weight (ประหยัดเหล็ก)": score = weight
                    else: score = r * 100 + weight 
                    
                    valid_designs.append({
                        'Bolt': d, 'Rows': r, 'Thk': t,
                        'Weight': weight, 'Ratio': res['ratio'],
                        'Score': score, 'Params': temp_inputs 
                    })

    if not valid_designs: return None
    df = pd.DataFrame(valid_designs)
    df = df.sort_values(by=['Score', 'Ratio'], ascending=[True, False])
    return df.head(5) 

# ==========================================
# 🖥️ 3. UI RENDERING
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
        
        # --- IMPROVED OPTIMIZER UI ---
        with st.expander("⚡ AI Auto-Optimizer (ผู้ช่วยออกแบบ)", expanded=False):
            st.caption("ระบบจะค้นหาแบบที่ประหยัดที่สุด โดยใช้ระยะมาตรฐาน")
            c_fil1, c_fil2, c_fil3 = st.columns([1.5, 1.2, 1])
            with c_fil1: opt_strategy = st.radio("เป้าหมาย:", ["Min Weight (ประหยัดเหล็ก)", "Min Bolts (ประหยัดแรงงาน)"])
            with c_fil2:
                lock_bolt = st.checkbox("Lock Size?", value=False)
                curr_d = st.session_state.get('auto_d', default_bolt_size) 
                if lock_bolt: st.caption(f"🔒 M{curr_d}")
            with c_fil3:
                st.write("") 
                run_opt = st.button("🚀 RUN AI", type="primary")

            if run_opt:
                with st.spinner("🤖 AI Engineer is calculating..."):
                    defaults = {
                        'cols': 1, 's_h': 0, 'weld_size': 6, 
                        'e1': 40, 'setback': 10, 'T_load': 0,
                        'cope': {'has_cope': False, 'dc': 0, 'c': 0}
                    }
                    results_df = run_optimization(V_design_kg, 0, sel_mat_grade, bolt_grade_name, conn_type, 
                        defaults, fixed_bolt=curr_d if lock_bolt else None, strategy=opt_strategy)
                    
                    if results_df is not None:
                        st.session_state['opt_results'] = results_df
                        st.success(f"✅ Found {len(results_df)} valid designs!")
                    else: st.warning("❌ ไม่พบแบบที่ผ่านเกณฑ์")

            if 'opt_results' in st.session_state:
                res_df = st.session_state['opt_results']
                if not pd.api.types.is_numeric_dtype(res_df['Bolt']): # Safety Check
                    del st.session_state['opt_results']
                    st.rerun()

                st.markdown("#### 🏆 Top Recommendations")
                for index, row in res_df.iterrows():
                    desc = f"M{row['Bolt']:.0f} x {row['Rows']:.0f} rows (Plt {row['Thk']:.0f}mm)"
                    if st.button(f"👉 Apply: {desc} ({row['Ratio']:.2f})", key=f"btn_apply_{index}"):
                        p = row['Params']
                        st.session_state['auto_d'] = int(p['d'])
                        st.session_state['auto_rows'] = int(p['rows'])
                        st.session_state['auto_t'] = float(p['t'])
                        st.session_state['auto_sv'] = float(p['s_v'])
                        st.session_state['auto_lv'] = float(p['lv'])
                        st.rerun()

        # Thread Condition
        st.write("---")
        thread_cond = st.radio("Shear Plane:", ["Threads Included (N)", "Threads Excluded (X)"], horizontal=True)
        final_Fnv = selected_bolt['Fnv'] 
        if "Excluded" in thread_cond:
            if "8.8" in bolt_grade_name or "A325" in bolt_grade_name: final_Fnv = 457
            elif "10.9" in bolt_grade_name or "A490" in bolt_grade_name: final_Fnv = 579
            else: final_Fnv = final_Fnv * 1.25
        
        # Tabs
        in_tab1, in_tab2, in_tab3 = st.tabs(["📏 Geometry", "📐 Detailing", "⚙️ Advanced"])

        with in_tab1:
            c1, c2 = st.columns(2)
            def_d = st.session_state.pop('auto_d', 20)
            def_t = st.session_state.pop('auto_t', 9.0)
            def_rows = st.session_state.pop('auto_rows', 3)
            
            bolt_opts = [12, 16, 20, 22, 24, 27, 30]
            try: d_idx = bolt_opts.index(def_d)
            except: d_idx = 2

            d_bolt = c1.selectbox("Bolt Size (mm)", bolt_opts, index=d_idx)
            t_plate = c2.number_input("Plate Thk (t)", 4.0, 50.0, float(def_t), step=1.0)
            
            c3, c4 = st.columns(2)
            rows = c3.number_input("Rows", 2, 20, int(def_rows))
            cols = 2 if "End" in conn_type else c4.number_input("Cols", 1, 4, 1)

        with in_tab2:
            def_sv = st.session_state.pop('auto_sv', 70.0)
            def_lv = st.session_state.pop('auto_lv', 35.0)
            c1, c2 = st.columns(2)
            s_v = c1.number_input("Pitch (sv)", 30.0, 200.0, float(def_sv), step=5.0)
            s_h = c2.number_input("Gauge (sh)", 0.0, 200.0, 0.0 if cols==1 else 70.0, disabled=(cols==1), step=5.0)
            c3, c4 = st.columns(2)
            lv = c3.number_input("Edge V (lv)", 20.0, 150.0, float(def_lv), step=5.0)
            leh = c4.number_input("Edge H (leh)", 20.0, 150.0, float(def_lv), step=5.0)
            
            st.divider()
            k1, k2 = st.columns(2)
            weld_sz = k1.number_input("Weld Size", 3.0, 20.0, 6.0, step=1.0)
            is_end = "End" in conn_type
            e1 = k2.number_input("Eccentricity (e1)", 30.0, 150.0, 40.0, disabled=is_end, step=5.0)
            setback = st.number_input("Setback", 0.0, 50.0, 10.0, disabled=is_end) if not is_end else 0

        with in_tab3:
            st.info("Additional Forces")
            T_design_kg = st.number_input("Axial Tension (kg)", 0.0, 50000.0, 0.0, step=100.0)
            has_cope = st.checkbox("Coped Beam? (บากคาน)", value=False)
            if has_cope:
                cc1, cc2 = st.columns(2)
                cope_d = cc1.number_input("Cope Depth (dc)", 0.0, 200.0, 30.0)
                cope_c = cc2.number_input("Cope Length (c)", 0.0, 200.0, 100.0)
            else: cope_d, cope_c = 0, 0

        # Gather Inputs & Calculate
        user_inputs = {
            'd': d_bolt, 'rows': rows, 'cols': cols, 's_v': s_v, 's_h': s_h,
            't': t_plate, 'weld_size': weld_sz,
            'lv': lv, 'leh': leh, 'e1': e1, 'setback': setback,
            'T_load': T_design_kg, 
            'cope': {'has_cope': has_cope, 'dc': cope_d, 'c': cope_c}
        }
        
        plate_geom = calculate_plate_geometry(conn_type, user_inputs)
        geom_warnings = check_geometry_compliance(user_inputs)
        if geom_warnings:
            for w in geom_warnings: st.warning(w)

        bolt_data_for_calc = selected_bolt.copy()
        bolt_data_for_calc['Fnv'] = final_Fnv
        
        # 🔥 CALL COMPREHENSIVE CHECK
        check_res = calculate_comprehensive_check(
            user_inputs, plate_geom, V_design_kg, T_design_kg, 
            sel_mat_grade, bolt_data_for_calc
        )
        
        # --- 📊 NEW DISPLAY: SUMMARY TABLE ---
        st.divider()
        st.subheader("📊 Design Summary Check")

        df_show = check_res['df'][['Item', 'Capacity', 'Demand', 'Ratio', 'Status']].copy()
        
        # Formatting for Display
        df_show['Capacity'] = df_show['Capacity'].apply(lambda x: f"{x:,.0f}" if x < 99999 else "-")
        df_show['Demand'] = df_show['Demand'].apply(lambda x: f"{x:,.0f}")
        
        # Logic for coloring
        def highlight_status(val):
            color = '#ffcccb' if val == 'FAIL' else '#d1fae5'
            return f'background-color: {color}'

        st.dataframe(
            df_show.style.applymap(highlight_status, subset=['Status'])
                   .format({"Ratio": "{:.2f}"}),
            use_container_width=True,
            hide_index=True
        )

        max_ratio = check_res['ratio']
        if max_ratio <= 1.0:
            st.success(f"✅ DESIGN PASS (Utility Ratio: {max_ratio:.2f})")
        else:
            st.error(f"❌ DESIGN FAIL (Utility Ratio: {max_ratio:.2f})")

    with col_draw:
        t1, t2, t3 = st.tabs(["🖼️ Front View", "📐 Side View", "🔝 Plan View"])
        with t1: st.plotly_chart(dw.create_front_view(section_data, plate_geom, user_inputs), use_container_width=True)
        with t2: st.plotly_chart(dw.create_side_view(section_data, plate_geom, user_inputs), use_container_width=True)
        with t3: st.plotly_chart(dw.create_plan_view(section_data, plate_geom, user_inputs), use_container_width=True)

    # Report Gen
    st.markdown("---")
    if st.button("📄 Generate Calculation Report", type="primary", use_container_width=True):
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
