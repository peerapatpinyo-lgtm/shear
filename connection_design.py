import streamlit as st
import math
import drawing_utils as dwg

# =============================================================================
# ⚙️ CONSTANTS
# =============================================================================
BOLT_GRADES = {
    "A325 (High Strength)": {"Fnv": 3720, "Ft": 6200, "Fu_bolt": 8400}, 
    "Grade 8.8 (Standard)": {"Fnv": 3200, "Ft": 5600, "Fu_bolt": 8000},
    "A490 (Premium)":       {"Fnv": 4960, "Ft": 7800, "Fu_bolt": 10500}
}

def render_connection_tab(V_design, method, is_lrfd, section_data, conn_type, T_design=0):
    st.markdown(f"### 📐 Design Detail: **{conn_type}**")
    
    # Beam Properties
    h, tw, tf = section_data['h'], section_data['tw'], section_data['tf']
    Fu_beam = 4100 # Assumed Ultimate Strength for SS400/A36
    
    # =========================================================================
    # 1. INPUTS
    # =========================================================================
    c1, c2, c3 = st.columns(3)
    with c1:
        st.caption("🔩 Bolt Config")
        sel_grade = st.selectbox("Bolt Grade", list(BOLT_GRADES.keys()))
        sel_size = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)
        
        # Variable Standardization
        d_mm = int(sel_size[1:]) # Diameter in mm
        Ab = (math.pi * (d_mm/10)**2) / 4 # Area in cm^2
        props = BOLT_GRADES[sel_grade]
    
    with c2:
        st.caption("📏 Layout")
        n_rows = st.number_input("Rows", 2, 20, 3)
        n_cols = st.number_input("Cols", 1, 4, 2)
        n_total = n_rows * n_cols # ✅ Define n_total here clearly
        
    with c3:
        st.caption("🏗️ Plate Data")
        tp = st.selectbox("Plate Thick (mm)", [6, 9, 10, 12, 16, 20, 25], index=2)
        Fy_plate = st.number_input("Plate Fy (ksc)", value=2500)
        Fu_plate = 4100 # Assumed Ultimate

    st.divider()

    # =========================================================================
    # 2. CALCULATION ENGINE
    # =========================================================================
    
    # Factors
    phi_shear = 0.75; phi_bear = 0.75; phi_yield = 0.90
    om_shear = 2.00;  om_bear = 2.00;  om_yield = 1.67
    
    def get_cap(Rn, phi, omega):
        return (phi * Rn) if is_lrfd else (Rn / omega)

    # 2.1 Bolt Shear Strength
    shear_plane = 2 if "Double" in conn_type else 1
    Rn_shear_bolt = props["Fnv"] * Ab * shear_plane # per bolt
    Cap_shear_total = get_cap(Rn_shear_bolt, phi_shear, om_shear) * n_total

    # 2.2 Bolt Bearing Strength (on Plate)
    # Dimensions
    min_pitch = 3 * d_mm
    s_v = max(min_pitch, 70)
    s_h = max(min_pitch, 60)
    edge = max(1.5 * d_mm, 40)
    
    # Lc Calculation (Clear distance)
    # Lc_edge = Distance from hole edge to plate edge
    Lc_edge = edge - (d_mm + 2)/2  # mm
    # Lc_inner = Distance between holes
    Lc_inner = s_v - (d_mm + 2)    # mm
    
    # Convert to cm for calculation (Formula usually in kg, cm)
    # AISC: Rn = 1.2 Lc t Fu <= 2.4 d t Fu
    
    # Bearing per bolt (Edge)
    Rn_bear_edge = 1.2 * (Lc_edge/10) * (tp/10) * Fu_plate
    Rn_bear_max = 2.4 * (d_mm/10) * (tp/10) * Fu_plate
    Rn_bear_edge = min(Rn_bear_edge, Rn_bear_max)
    
    # Bearing per bolt (Inner)
    Rn_bear_inner = 1.2 * (Lc_inner/10) * (tp/10) * Fu_plate
    Rn_bear_inner = min(Rn_bear_inner, Rn_bear_max)
    
    # Total Bearing Capacity (Simplified conservatively using edge for top row, inner for others if any)
    # For strict calculation: 2 edge bolts + (n_total-2) inner bolts
    # Simplified: Use average or min. Let's use min for safety.
    Rn_bear_avg = Rn_bear_edge 
    Cap_bear_total = get_cap(Rn_bear_avg, phi_bear, om_bear) * n_total

    # 2.3 Plate Shear Yielding (Gross Section)
    h_plate = (n_rows - 1) * s_v + 2 * edge
    Ag_shear = (h_plate/10) * (tp/10) # cm2
    Rn_yield = 0.60 * Fy_plate * Ag_shear
    Cap_yield = get_cap(Rn_yield, phi_yield, om_yield)

    # --- FIND GOVERNING CASE ---
    results = {
        "Bolt Shear": Cap_shear_total,
        "Bolt Bearing": Cap_bear_total,
        "Plate Shear Yield": Cap_yield
    }
    min_cap = min(results.values())
    gov_mode = min(results, key=results.get)
    
    ratio = V_design / min_cap
    is_pass = ratio <= 1.0

    # =========================================================================
    # 3. DISPLAY RESULTS & DRAWINGS
    # =========================================================================
    c_res1, c_res2, c_res3 = st.columns(3)
    c_res1.metric("Load Demand (Vu)", f"{V_design:,.0f} kg")
    c_res2.metric("Design Capacity", f"{min_cap:,.0f} kg", f"Ratio: {ratio:.2f}", 
                  delta_color="normal" if is_pass else "inverse")
    c_res3.metric("Governing Mode", gov_mode, "Controls Design")

    # EXPANDER: Detailed Calc
    with st.expander("📄 View Detailed Engineering Calculations", expanded=False):
        st.markdown("#### 1. Connection Capacity Checks")
        
        # Table
        st.markdown(f"""
        | Failure Mode | Capacity ($R_n/\Omega$ or $\phi R_n$) | Demand ($V_u$) | Ratio | Status |
        |---|---|---|---|---|
        | **Bolt Shear** | **{Cap_shear_total:,.0f}** | {V_design:,.0f} | {V_design/Cap_shear_total:.2f} | {'✅' if V_design<=Cap_shear_total else '❌'} |
        | **Bolt Bearing** | **{Cap_bear_total:,.0f}** | {V_design:,.0f} | {V_design/Cap_bear_total:.2f} | {'✅' if V_design<=Cap_bear_total else '❌'} |
        | **Plate Yield** | **{Cap_yield:,.0f}** | {V_design:,.0f} | {V_design/Cap_yield:.2f} | {'✅' if V_design<=Cap_yield else '❌'} |
        """)

        st.markdown("---")
        st.markdown("#### 2. Calculation Reference")
        st.latex(fr"R_{{n,shear}} = F_{{nv}} A_b N_s = {props['Fnv']} \times {Ab:.2f} \times {shear_plane} = {Rn_shear_bolt:,.0f} \text{{ kg/bolt}}")

    # Drawings
    w_plate = (n_cols - 1) * s_h + 2 * edge + 10
    beam_d = {'h': h, 'b': 100, 'tw': tw, 'tf': tf}
    plate_d = {'w': w_plate, 'h': h_plate, 't': tp, 'l_side': w_plate, 'e1': edge, 'lv': edge}
    bolt_d = {'d': d_mm, 'rows': n_rows, 'cols': n_cols, 's_v': s_v, 's_h': s_h}
    
    t1, t2 = st.tabs(["Elevation", "Section"])
    with t1: st.plotly_chart(dwg.create_front_view(beam_d, plate_d, bolt_d), use_container_width=True)
    with t2: st.plotly_chart(dwg.create_side_view(beam_d, plate_d, bolt_d), use_container_width=True)

    # =========================================================================
    # 4. RETURN DATA (Fixed Variable Names)
    # =========================================================================
    return {
        'pass': is_pass,
        'demand': V_design,
        'qty': n_total,        # ✅ ใช้ n_total ตรงนี้ (แก้จาก nt ที่ error)
        'conn_type': conn_type,
        'report_data': {
            'method': "LRFD" if is_lrfd else "ASD",
            'bolt_info': f"{n_total} x M{d_mm} ({sel_grade})",
            'plate_info': f"t={tp}mm (Fy={Fy_plate} ksc)",
            'cap_shear': Cap_shear_total,
            'Rn_shear': Rn_shear_bolt,
            'cap_bear': Cap_bear_total,
            'Rn_bear': Rn_bear_avg,
            'qty': n_total
        }
    }
