import streamlit as st
import math
import drawing_utils as dw

# ==========================================
# 🧮 ENGINEERING FORMULAS
# ==========================================
def get_bolt_area(d):
    return math.pi * (d**2) / 4

def calculate_capacity(inputs, plate_geom, V_load, method, mat_grade):
    """
    คำนวณกำลังรับน้ำหนักของจุดต่อ (Shear Connection)
    Ref: AISC 360-16 / EIT (Simplified)
    """
    results = {}
    
    # 1. Constants & Factors
    is_lrfd = (method == "LRFD")
    phi = 0.75 if is_lrfd else 1.0/2.0  # For Rupture
    phi_y = 0.90 if is_lrfd else 1.0/1.67 # For Yielding
    phi_b = 0.75 if is_lrfd else 1.0/2.0  # For Bolt Shear
    phi_w = 0.75 if is_lrfd else 1.0/2.0  # For Weld
    
    # Material Properties (Estimated)
    if "SS400" in mat_grade: Fy, Fu = 245, 400
    elif "SM520" in mat_grade: Fy, Fu = 355, 520
    else: Fy, Fu = 250, 400 # A36 default
    
    # Bolt Properties (A325/8.8)
    Fnv = 372 # MPa (Approx for A325/8.8 Shear)
    
    # Geometry
    d = inputs['d']
    t = inputs['t']
    n_bolts = inputs['rows'] * inputs['cols']
    h_plate = plate_geom['h']
    Ag = h_plate * t # Gross Area
    Anv = (h_plate - (inputs['rows'] * (d+2))) * t # Net Area Shear
    
    # ----------------------------------------
    # CHECK 1: BOLT SHEAR
    # ----------------------------------------
    Ab = get_bolt_area(d)
    Rn_bolt = Fnv * Ab * n_bolts / 1000.0 # kN to kg later
    Cap_Bolt = (phi_b * Rn_bolt) * 1000 / 9.81 # Convert N -> kg
    results['Bolt Shear'] = Cap_Bolt

    # ----------------------------------------
    # CHECK 2: PLATE SHEAR YIELDING
    # ----------------------------------------
    Rn_y = 0.60 * Fy * Ag / 1000.0
    Cap_Yield = (phi_y * Rn_y) * 1000 / 9.81
    results['Plate Yield'] = Cap_Yield

    # ----------------------------------------
    # CHECK 3: PLATE SHEAR RUPTURE
    # ----------------------------------------
    Rn_u = 0.60 * Fu * Anv / 1000.0
    Cap_Rup = (phi * Rn_u) * 1000 / 9.81
    results['Plate Rupture'] = Cap_Rup

    # ----------------------------------------
    # CHECK 4: BEARING (At Bolt Holes)
    # ----------------------------------------
    # Lc = distance from edge to hole or hole to hole
    # Simplified: Use edge distance (lv) as worst case
    Lc = inputs['lv'] - (d+2)/2
    Rn_brg_1 = 1.2 * Lc * t * Fu
    Rn_brg_2 = 2.4 * d * t * Fu
    Rn_brg = min(Rn_brg_1, Rn_brg_2) * n_bolts / 1000.0
    Cap_Brg = (phi_b * Rn_brg) * 1000 / 9.81
    results['Bearing'] = Cap_Brg
    
    # ----------------------------------------
    # CHECK 5: WELD CAPACITY (Fillet Weld)
    # ----------------------------------------
    w_sz = inputs['weld_size']
    L_weld = h_plate * 2 # Weld both sides of plate (for Fin)
    if "End" in plate_geom['type']: 
        L_weld = (plate_geom['w']*2) + (plate_geom['h']*2) # All around (Simplification)
        
    Fexx = 480 # E70 electrode
    Rn_w = 0.60 * Fexx * (0.707 * w_sz) * L_weld / 1000.0
    Cap_Weld = (phi_w * Rn_w) * 1000 / 9.81
    results['Weld Strength'] = Cap_Weld

    # ----------------------------------------
    # SUMMARY
    # ----------------------------------------
    min_cap = min(results.values())
    ratio = V_load / min_cap if min_cap > 0 else 999
    
    return {
        'checks': results,
        'capacity': min_cap,
        'ratio': ratio,
        'status': "PASS" if ratio <= 1.0 else "FAIL"
    }

def calculate_plate_geometry(conn_type, user_inputs):
    """(Logic เดิม) คำนวณ Geometry"""
    rows, cols = user_inputs['rows'], user_inputs['cols']
    sv, sh = user_inputs['s_v'], user_inputs['s_h']
    lv, leh = user_inputs['lv'], user_inputs['leh']
    e1, setback = user_inputs['e1'], user_inputs['setback']
    
    # Height
    bolt_group_h = (rows - 1) * sv
    calc_h = bolt_group_h + (2 * lv)
    
    # Width
    calc_w = 0
    if "Fin" in conn_type:
        bolt_group_w = (cols - 1) * sh
        calc_w = setback + e1 + bolt_group_w + leh
    elif "End" in conn_type:
        calc_w = sh + (2 * leh)
    elif "Double" in conn_type:
        calc_w = e1 + leh 

    return {'h': calc_h, 'w': calc_w, 'type': conn_type}

# ==========================================
# 🖥️ RENDER UI
# ==========================================
def render_connection_tab(V_design_from_tab1, default_bolt_size, method, is_lrfd, section_data, conn_type, default_bolt_grade, default_mat_grade):
    
    st.markdown(f"### 🔩 Detail Design: {conn_type}")
    
    col_input, col_draw = st.columns([1, 2])
    
    # --- LEFT: INPUTS & CALCULATIONS ---
    with col_input:
        with st.container():
            st.info(f"**Design Load (Vu): {V_design_from_tab1:,.0f} kg**", icon="🏋️")
            
            with st.expander("1. Bolt Configuration", expanded=True):
                c1, c2 = st.columns(2)
                d_bolt = c1.selectbox("Bolt Size", [12, 16, 20, 22, 24], index=2)
                rows = c2.number_input("Rows", 2, 20, 3)
                cols = 1
                if "End" in conn_type:
                    cols = 2
                    st.caption("Cols: 2 (Fixed for End Plate)")
                else:
                    cols = st.number_input("Cols", 1, 5, 1)

                c3, c4 = st.columns(2)
                s_v = c3.number_input("Pitch (Vert)", 30, 150, 70)
                s_h = c4.number_input("Pitch/Gauge (Horiz)", 30, 150, 60)

            with st.expander("2. Plate & Weld", expanded=True):
                c1, c2 = st.columns(2)
                t_plate = c1.number_input("Plate t (mm)", 4.0, 50.0, 9.0)
                weld_sz = c2.number_input("Weld Size (mm)", 3.0, 20.0, 6.0)
                
                st.markdown("---")
                st.caption("Edge Distances")
                k1, k2 = st.columns(2)
                lv = k1.number_input("Vert. Edge (lv)", 25, 100, 40)
                leh = k2.number_input("Horiz. Edge (leh)", 25, 100, 40)
                
                k3, k4 = st.columns(2)
                e1 = k3.number_input("Beam-Bolt (e1)", 30, 100, 40, disabled=("End" in conn_type))
                setback = k4.number_input("Setback", 0, 50, 10, disabled=("End" in conn_type))

            # Pack Inputs
            user_inputs = {
                'd': d_bolt, 'rows': rows, 'cols': cols, 's_v': s_v, 's_h': s_h,
                't': t_plate, 'weld_size': weld_sz,
                'lv': lv, 'leh': leh, 'e1': e1, 'setback': setback, 'grade': default_bolt_grade
            }
            
            # --- AUTO CALC & CHECK ---
            plate_geom = calculate_plate_geometry(conn_type, user_inputs)
            calc_res = calculate_capacity(user_inputs, plate_geom, V_design_from_tab1, method, default_mat_grade)
            
            # --- DISPLAY RESULTS CARD ---
            st.markdown("---")
            status_color = "green" if calc_res['status'] == "PASS" else "red"
            st.markdown(f"#### Status: :{status_color}[{calc_res['status']}] (Ratio {calc_res['ratio']:.2f})")
            
            # Progress Bar style visualization
            for check_name, cap_val in calc_res['checks'].items():
                ratio = V_design_from_tab1 / cap_val
                bar_color = "red" if ratio > 1.0 else "green"
                st.write(f"**{check_name}**: {cap_val:,.0f} kg")
                st.progress(min(ratio, 1.0))
                if ratio > 1.0:
                    st.caption(f"⚠️ Failed (Ratio {ratio:.2f})")

    # --- RIGHT: DRAWINGS ---
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
            
    return plate_geom, user_inputs
