# connection_design.py (V13.3 - Added Calculation Details)
import streamlit as st
import math
import drawing_utils as dwg

# =============================================================================
# ⚙️ CONSTANTS & DATA
# =============================================================================
BOLT_GRADES = {
    "A325 (High Strength)": {"Fnv": 3720, "Ft": 6200},  # ksc (approx 372 MPa)
    "Grade 8.8 (Standard)": {"Fnv": 3200, "Ft": 5600},
    "A490 (Premium)":       {"Fnv": 4960, "Ft": 7800}
}

# =============================================================================
# 🔧 MAIN FUNCTION
# =============================================================================
def render_connection_tab(V_design, method, is_lrfd, section_data, conn_type, T_design=0):
    
    st.markdown(f"### 📐 Design Detail: **{conn_type}**")
    
    h, b, tw, tf = section_data['h'], section_data['b'], section_data['tw'], section_data['tf']

    # =========================================================================
    # 1. INPUTS
    # =========================================================================
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.caption("🔩 Bolt Configuration")
        selected_grade_name = st.selectbox("Bolt Grade", list(BOLT_GRADES.keys()), index=0)
        selected_size_str = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)
        
        d_mm = int(selected_size_str[1:])
        Ab = (math.pi * (d_mm/10)**2) / 4  # cm²
        grade_props = BOLT_GRADES[selected_grade_name]
        Fnv = grade_props["Fnv"]
        
        st.info(f"Bolt Area: {Ab:.2f} cm² | Shear Strength: {Fnv} ksc")

    with c2:
        st.caption("📏 Layout")
        n_rows = st.number_input("Rows", 2, 20, 3)
        n_cols = st.number_input("Cols", 1, 4, 2)
        n_total = n_rows * n_cols

    with c3:
        st.caption("🏗️ Plate Design")
        t_plate = st.selectbox("Plate Thickness (mm)", [6, 9, 10, 12, 16, 20, 25], index=2)
        fy_plate = st.number_input("Plate Fy (ksc)", value=2500)

    st.divider()

    # =========================================================================
    # 2. CALCULATION LOGIC
    # =========================================================================
    phi = 0.75 if is_lrfd else 1.0
    omega = 2.00 if not is_lrfd else 1.0
    
    # 2.1 Bolt Shear Capacity
    shear_plane = 2 if "Double" in conn_type else 1
    Rn_bolt = Fnv * Ab * shear_plane  # Nominal per bolt
    
    if is_lrfd:
        cap_per_bolt = phi * Rn_bolt
        total_bolt_capacity = cap_per_bolt * n_total
        eq_symbol = r"\phi R_n"
        method_str = "LRFD (phi=0.75)"
    else:
        cap_per_bolt = Rn_bolt / omega
        total_bolt_capacity = cap_per_bolt * n_total
        eq_symbol = r"R_n / \Omega"
        method_str = "ASD (Omega=2.00)"

    # 2.2 Geometry Check
    min_pitch = 3 * d_mm
    s_v = max(min_pitch, 70)
    s_h = max(min_pitch, 60)
    edge_dist = max(1.5 * d_mm, 40)
    
    h_plate = (n_rows - 1) * s_v + 2 * edge_dist
    w_plate = (n_cols - 1) * s_h + 2 * edge_dist + 10
    h_clear = h - 2*(tf + 10)
    plate_status = "OK" if h_plate <= h_clear else "TOO HIGH"

    # =========================================================================
    # 3. DISPLAY RESULTS & DRAWINGS
    # =========================================================================
    col_res1, col_res2, col_res3 = st.columns(3)
    ratio = V_design / total_bolt_capacity
    
    col_res1.metric("Load Demand (Vu)", f"{V_design:,.0f} kg")
    col_res2.metric("Bolt Capacity", f"{total_bolt_capacity:,.0f} kg", f"Ratio: {ratio:.2f}", delta_color="normal" if ratio<=1 else "inverse")
    col_res3.metric("Plate Check", f"{h_plate:.0f} mm", f"{plate_status} (Max {h_clear:.0f})", delta_color="normal" if plate_status=="OK" else "inverse")

    # --- ➕ ADDED: CALCULATION DETAIL SECTION ---
    with st.expander("📄 View Detailed Calculation (Step-by-Step)", expanded=False):
        st.markdown(f"#### 1. Bolt Shear Strength ({method_str})")
        
        st.markdown(r"**Nominal Strength ($R_n$):**")
        st.latex(fr"R_n = F_{{nv}} \times A_b \times N_s")
        st.latex(fr"R_n = {Fnv} \times {Ab:.2f} \times {shear_plane} = {Rn_bolt:,.0f} \text{{ kg/bolt}}")
        
        st.markdown(r"**Design Strength:**")
        if is_lrfd:
            st.latex(fr"\phi R_n = 0.75 \times {Rn_bolt:,.0f} = {cap_per_bolt:,.0f} \text{{ kg/bolt}}")
        else:
            st.latex(fr"\frac{{R_n}}{{\Omega}} = \frac{{{Rn_bolt:,.0f}}}{{2.00}} = {cap_per_bolt:,.0f} \text{{ kg/bolt}}")
            
        st.markdown(f"**Total Capacity ({n_total} Bolts):**")
        st.latex(fr"P_{{allow}} = {cap_per_bolt:,.0f} \times {n_total} = \mathbf{{{total_bolt_capacity:,.0f}}} \text{{ kg}}")
        
        st.markdown("#### 2. Verify Result")
        check_mark = r"\le" if ratio <= 1.0 else r">"
        result_text = r"\text{OK}" if ratio <= 1.0 else r"\text{NOT SAFE}"
        color = "green" if ratio <= 1.0 else "red"
        st.latex(fr"\color{{{color}}}{{ {V_design:,.0f} \text{{ (Load)}} {check_mark} {total_bolt_capacity:,.0f} \text{{ (Cap)}} \rightarrow \mathbf{{{result_text}}} }}")

    # --- DRAWINGS ---
    beam_draw = {'h': h, 'b': b, 'tw': tw, 'tf': tf}
    plate_draw = {'w': w_plate, 'h': h_plate, 't': t_plate, 'l_side': w_plate, 'e1': edge_dist, 'lv': edge_dist}
    bolts_draw = {'d': d_mm, 'rows': n_rows, 'cols': n_cols, 's_v': s_v, 's_h': s_h}

    t1, t2, t3 = st.tabs(["Plan View", "Front View", "Side View"])
    with t1: st.plotly_chart(dwg.create_plan_view(beam_draw, plate_draw, bolts_draw), use_container_width=True)
    with t2: st.plotly_chart(dwg.create_front_view(beam_draw, plate_draw, bolts_draw), use_container_width=True)
    with t3: st.plotly_chart(dwg.create_side_view(beam_draw, plate_draw, bolts_draw), use_container_width=True)

# connection_design.py (Updated Return Section Only)
# ... (Calculations same as before) ...

    # =========================================================================
    # 4. RETURN DATA FOR REPORT
    # =========================================================================
    return {
        'pass': ratio <= 1.0,
        'demand': V_design,
        'qty': nt,
        'conn_type': conn_type,
        'report_data': {
            'method': "LRFD" if is_lrfd else "ASD",
            'bolt_info': f"{nt} x M{d} ({sel_grade})",
            'plate_info': f"t={tp}mm (Fy={Fy_plate} ksc)",
            'cap_shear': Cap_shear_total,
            'Rn_shear': Rn_shear_bolt,
            'cap_bear': Cap_bear_total,
            'Rn_bear': Rn_bear,
            'qty': nt
        }
    }
