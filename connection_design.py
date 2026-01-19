import streamlit as st
import math
import drawing_utils as dw
import calculation_report as cr 

# ==========================================
# 🧮 1. ENGINEERING LOGIC (QUICK CHECK)
# ==========================================
def calculate_quick_check(inputs, plate_geom, V_load_kg, T_load_kg, mat_grade, bolt_grade):
    # Setup Phi
    method_raw = st.session_state.get('design_method', 'LRFD (Limit State)')
    is_lrfd = "LRFD" in method_raw
    if is_lrfd:
        phi_y, phi_r, phi_w = 0.90, 0.75, 0.75
    else:
        phi_y, phi_r, phi_w = 1/1.50, 1/2.00, 1/2.00

    # Material
    if "SS400" in mat_grade: Fy, Fu = 24.5, 41.0
    elif "SM520" in mat_grade: Fy, Fu = 36.0, 53.0
    else: Fy, Fu = 25.0, 41.0 

    # Bolt Strength
    if "A490" in bolt_grade: Fnv = 50.0 
    elif "A307" in bolt_grade: Fnv = 19.0
    else: Fnv = 38.0 

    d = inputs['d']
    n_bolts = inputs['rows'] * inputs['cols']
    t = inputs['t']
    
    results = {}

    # Check 1: Bolt Shear (Interaction if Tension exists)
    Ab = (math.pi * d**2) / 4
    Rn_shear_total = Fnv * Ab * n_bolts * phi_r
    
    if T_load_kg > 0:
        # Simple circular interaction check for quick status
        # (V/Vn)^2 + (T/Tn)^2 <= 1.0
        # Fnt approx 1.3 * Fnv
        Fnt = Fnv * 1.3
        Rn_tension_total = Fnt * Ab * n_bolts * 0.75
        
        ratio_v = V_load_kg / Rn_shear_total
        ratio_t = T_load_kg / Rn_tension_total
        interaction = ratio_v**1.8 + ratio_t**1.8 # Simplified exponent
        results['Bolt Interaction'] = 1.0 / interaction if interaction > 0 else 99999
        # Hack: Storing 'Capacity' as relative unit, or just display Pass/Fail logic
        # Let's just return shear cap for display, but ratio considers interaction
        results['Bolt Combined'] = Rn_shear_total # Placeholder
    else:
        results['Bolt Shear'] = Rn_shear_total

    # Check 2: Plate Yield
    h_p = plate_geom['h']
    results['Plate Yielding'] = 0.60 * Fy * (h_p * t) * phi_y

    # Check 3: Weld
    w_sz = inputs['weld_size']
    L_weld = h_p * 2
    Fexx = 49.0 
    # Check resultant load for weld
    R_load = math.sqrt(V_load_kg**2 + T_load_kg**2)
    Rn_weld = 0.60 * Fexx * 0.707 * w_sz * L_weld * phi_w
    results['Weld Strength'] = Rn_weld

    # Determine Ratio
    if T_load_kg > 0:
        # If combined, use interaction ratio calculated above logic
        # Re-calc for safety
        ratio = interaction if 'interaction' in locals() else 0
        min_cap = Rn_shear_total # Just for display
    else:
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
    
    V_design_kg = V_design_from_tab1
    current_method = st.session_state.get('design_method', method)
    
    # --- Layout ---
    col_input, col_draw = st.columns([1, 1.8])
    
    with col_input:
        st.markdown(f"""
        <div style="background-color:#eff6ff; padding:15px; border-radius:8px; border-left:5px solid #3b82f6; margin-bottom:15px;">
            <div style="font-size:12px; color:#6b7280; font-weight:bold;">DESIGN SHEAR ({current_method})</div>
            <div style="font-size:26px; font-weight:800; color:#1e3a8a;">{V_design_kg:,.0f} kg</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("##### 🛠️ Material & Specs")
        row_mat = st.columns(2)
        sel_bolt_grade = row_mat[0].selectbox("🔩 Bolt Grade", ["A325", "A490", "A307"], index=0)
        
        mat_options = ["SS400 (Fy 2450)", "SM520 (Fy 3550)", "A36 (Fy 2500)"]
        def_idx = 0
        if "SM520" in default_mat_grade: def_idx = 1
        elif "A36" in default_mat_grade: def_idx = 2
        sel_mat_grade = row_mat[1].selectbox("🛡️ Plate Grade", mat_options, index=def_idx)
        
        # Tabs
        in_tab1, in_tab2, in_tab3 = st.tabs(["📏 1. Geometry", "📐 2. Detailing", "⚙️ 3. Advanced"])

        # TAB 1: Geometry
        with in_tab1:
            c1, c2 = st.columns(2)
            d_bolt = c1.selectbox("Bolt Size (mm)", [12, 16, 20, 22, 24, 27, 30], index=2)
            t_plate = c2.number_input("Plate Thk (t)", 4, 50, 9)
            c3, c4 = st.columns(2)
            rows = c3.number_input("Rows", 2, 20, 3)
            cols = 2 if "End" in conn_type else c4.number_input("Cols", 1, 4, 1)

        # TAB 2: Detailing
        with in_tab2:
            c1, c2 = st.columns(2)
            s_v = c1.number_input("Pitch (sv)", 30, 200, 70)
            s_h = c2.number_input("Gauge (sh)", 0, 200, 0 if cols==1 else 70, disabled=(cols==1))
            c3, c4 = st.columns(2)
            lv = c3.number_input("Edge V (lv)", 20, 150, 35)
            leh = c4.number_input("Edge H (leh)", 20, 150, 35)
            st.divider()
            k1, k2 = st.columns(2)
            weld_sz = k1.number_input("Weld Size", 3, 20, 6)
            is_end = "End" in conn_type
            e1 = k2.number_input("Eccentricity (e1)", 30, 150, 40, disabled=is_end)
            setback = st.number_input("Setback", 0, 50, 10, disabled=is_end) if not is_end else 0

        # TAB 3: Advanced (Cope & Tension) [NEW!]
        with in_tab3:
            st.info("Additional Forces & Beam Geometry")
            
            # Axial Load
            T_design_kg = st.number_input("Axial Tension (kg)", 0, 50000, 0, help="Input Tension for combined force check")
            
            # Coped Beam
            has_cope = st.checkbox("Coped Beam? (บากคาน)", value=False)
            if has_cope:
                cc1, cc2 = st.columns(2)
                cope_d = cc1.number_input("Cope Depth (dc)", 0, 200, 30)
                cope_c = cc2.number_input("Cope Length (c)", 0, 200, 100)
            else:
                cope_d, cope_c = 0, 0

        # Gather Inputs
        user_inputs = {
            'd': d_bolt, 'rows': rows, 'cols': cols, 's_v': s_v, 's_h': s_h,
            't': t_plate, 'weld_size': weld_sz,
            'lv': lv, 'leh': leh, 'e1': e1, 'setback': setback,
            'T_load': T_design_kg, # Store T here
            'cope': {'has_cope': has_cope, 'dc': cope_d, 'c': cope_c}
        }
        plate_geom = calculate_plate_geometry(conn_type, user_inputs)
        
        # Quick Check
        check_res = calculate_quick_check(user_inputs, plate_geom, V_design_kg, T_design_kg, sel_mat_grade, sel_bolt_grade)
        
        st.divider()
        st.subheader("🏁 Quick Status")
        for k, v in check_res['checks'].items():
            if k == "Bolt Interaction":
                 # Special display for interaction
                 status = "✅ PASS" if v >= 1.0 else "❌ FAIL"
                 st.write(f"{status} **{k}** (Ratio < 1.0)")
            else:
                # Normal force display
                if T_design_kg > 0 and k == 'Bolt Combined': continue # Skip
                limit = V_design_kg if "Weld" not in k else math.sqrt(V_design_kg**2 + T_design_kg**2)
                icon = "✅" if v >= limit else "❌"
                st.write(f"{icon} **{k}:** {v:,.0f} kg")
        
        ratio_color = "red" if check_res['ratio'] > 1.0 else "green"
        st.markdown(f"**Ratio:** :{ratio_color}[{check_res['ratio']:.2f}]")

    # --- Drawing Area ---
    with col_draw:
        t1, t2, t3 = st.tabs(["🖼️ Front View", "📐 Side View", "🔝 Plan View"])
        with t1: st.plotly_chart(dw.create_front_view(section_data, plate_geom, user_inputs), use_container_width=True)
        with t2: st.plotly_chart(dw.create_side_view(section_data, plate_geom, user_inputs), use_container_width=True)
        with t3: st.plotly_chart(dw.create_plan_view(section_data, plate_geom, user_inputs), use_container_width=True)

    # --- REPORT GENERATION ---
    st.markdown("---")
    if st.button("📄 Generate Calculation Report", type="primary", use_container_width=True):
        
        # Unit Conversion
        V_kN = V_design_kg * 9.81 / 1000.0
        T_kN = T_design_kg * 9.81 / 1000.0
        
        # Material Parsing
        is_sm520 = "SM520" in sel_mat_grade
        Fy_val = 355 if is_sm520 else 245
        Fu_val = 520 if is_sm520 else 400
        
        if "A490" in sel_bolt_grade: fnv_val = 496 
        elif "A307" in sel_bolt_grade: fnv_val = 188 
        else: fnv_val = 372 

        # Beam Data
        is_beam_sm520 = "SM520" in default_mat_grade
        Fu_beam = 520 if is_beam_sm520 else 400
        Fy_beam = 355 if is_beam_sm520 else 245
        beam_dict = { 'tw': section_data.get('tw', 6), 'Fu': Fu_beam, 'Fy': Fy_beam }
        
        plate_dict = {
            't': t_plate, 'h': plate_geom['h'], 'w': plate_geom['w'],
            'Fy': Fy_val, 'Fu': Fu_val, 'weld_size': weld_sz,
            'e1': e1, 'lv': lv, 'l_side': leh
        }
        
        bolt_dict = {
            'd': d_bolt, 'rows': rows, 'cols': cols, 
            's_v': s_v, 's_h': s_h, 'Fnv': fnv_val
        }

        # Call Generator with NEW Parameters
        try:
            report_md = cr.generate_report(
                V_load=V_kN,
                T_load=T_kN,      # <--- NEW
                beam=beam_dict,
                plate=plate_dict,
                bolts=bolt_dict,
                cope=user_inputs['cope'], # <--- NEW
                is_lrfd=is_lrfd,
                material_grade=sel_mat_grade, 
                bolt_grade=sel_bolt_grade     
            )
            
            with st.container():
                st.success("✅ Advanced Report Generated!")
                with st.expander("📜 View Calculation Note", expanded=True):
                    st.markdown(report_md)
        except Exception as e:
            st.error(f"❌ Error: {e}")
