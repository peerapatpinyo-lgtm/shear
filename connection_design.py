# connection_design.py (V13.2 - Fixed Arguments & Return Data)
import streamlit as st
import math
import pandas as pd
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
# ✅ แก้ไข: ลบ bolt_size, bolt_grade ออกจาก input arguments
def render_connection_tab(V_design, method, is_lrfd, section_data, conn_type, T_design=0):
    
    st.markdown(f"### 📐 Design Detail: **{conn_type}**")
    
    # ดึงค่าหน้าตัดคาน
    h, b, tw, tf = section_data['h'], section_data['b'], section_data['tw'], section_data['tf']

    # =========================================================================
    # 1. INPUTS (ย้ายการเลือก Bolt มาไว้ที่นี่ เพื่อลดความซ้ำซ้อน)
    # =========================================================================
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.caption("🔩 Bolt Configuration")
        # ✅ Select Box ย้ายมาอยู่ในนี้
        selected_grade_name = st.selectbox("Bolt Grade", list(BOLT_GRADES.keys()), index=0)
        selected_size_str = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)
        
        # Parse Bolt Data
        d_mm = int(selected_size_str[1:])  # "M20" -> 20
        Ab = (math.pi * (d_mm/10)**2) / 4  # cm²
        
        # Get Strength
        grade_props = BOLT_GRADES[selected_grade_name]
        Fnv = grade_props["Fnv"]
        
        st.info(f"Bolt Area: {Ab:.2f} cm² | Shear Strength: {Fnv} ksc")

    with c2:
        st.caption("📏 Layout")
        n_rows = st.number_input("Rows", min_value=2, max_value=20, value=3)
        n_cols = st.number_input("Cols", min_value=1, max_value=4, value=2)
        n_total = n_rows * n_cols

    with c3:
        st.caption("🏗️ Plate Design")
        t_plate = st.selectbox("Plate Thickness (mm)", [6, 9, 10, 12, 16, 20, 25], index=2)
        fy_plate = st.number_input("Plate Fy (ksc)", value=2500)

    st.divider()

    # =========================================================================
    # 2. CALCULATION (Capacity Check)
    # =========================================================================
    
    # Factor Adjustments
    phi = 0.75 if is_lrfd else 1.0   # LRFD Resistance Factor
    omega = 1.0 if is_lrfd else 2.0  # ASD Safety Factor (Simplified)
    
    # 2.1 Shear Capacity of Bolts
    # Nominal Shear Strength (Rn) = Fnv * Ab * Ns (Number of shear planes)
    # Note: Fin Plate = Single Shear (Ns=1), Double Angle = Double Shear (Ns=2)
    shear_plane = 2 if "Double" in conn_type else 1
    
    Rn_bolt = Fnv * Ab * shear_plane  # per bolt
    
    if is_lrfd:
        cap_per_bolt = phi * Rn_bolt
    else:
        cap_per_bolt = Rn_bolt / omega  # ASD
        
    total_bolt_capacity = cap_per_bolt * n_total
    
    # 2.2 Dimensions Check
    # Minimum spacing (pitch) approx 3d
    min_pitch = 3 * d_mm
    s_v = max(min_pitch, 70) # Vertical spacing
    s_h = max(min_pitch, 60) # Horizontal spacing
    edge_dist = max(1.5 * d_mm, 40)
    
    # Plate Dimensions
    h_plate = (n_rows - 1) * s_v + 2 * edge_dist
    w_plate = (n_cols - 1) * s_h + 2 * edge_dist + 10 # +10 gap
    
    # Check if plate fits in beam web (T distance)
    h_clear = h - 2*(tf + 10) # fillet approx
    plate_status = "OK" if h_plate <= h_clear else "TOO HIGH"
    plate_color = "green" if plate_status == "OK" else "red"

    # =========================================================================
    # 3. DISPLAY RESULTS & DRAWINGS
    # =========================================================================
    
    # --- RESULT METRICS ---
    col_res1, col_res2, col_res3 = st.columns(3)
    
    ratio = V_design / total_bolt_capacity
    status_icon = "✅" if ratio <= 1.0 else "❌"
    
    col_res1.metric("Load Demand (Vu)", f"{V_design:,.0f} kg")
    col_res2.metric("Bolt Capacity (Rn)", f"{total_bolt_capacity:,.0f} kg", f"{status_icon} Ratio: {ratio:.2f}")
    col_res3.metric("Plate Height Check", f"{h_plate:.0f} mm", f"{plate_status} (Max {h_clear:.0f})", delta_color="normal" if plate_status=="OK" else "inverse")

    # --- DRAWING DATA PREPARATION ---
    beam_draw = {'h': h, 'b': b, 'tw': tw, 'tf': tf}
    plate_draw = {
        'w': w_plate, 'h': h_plate, 't': t_plate, 
        'l_side': w_plate, 'e1': edge_dist, 'lv': edge_dist
    }
    bolts_draw = {
        'd': d_mm, 'rows': n_rows, 'cols': n_cols, 
        's_v': s_v, 's_h': s_h
    }

    # --- PLOTLY DRAWINGS ---
    t1, t2, t3 = st.tabs(["Plan View (Top)", "Elevation (Front)", "Section (Side)"])
    
    with t1:
        st.plotly_chart(dwg.create_plan_view(beam_draw, plate_draw, bolts_draw), use_container_width=True)
    with t2:
        st.plotly_chart(dwg.create_front_view(beam_draw, plate_draw, bolts_draw), use_container_width=True)
    with t3:
        st.plotly_chart(dwg.create_side_view(beam_draw, plate_draw, bolts_draw), use_container_width=True)

    # =========================================================================
    # 4. ✅ RETURN DATA (สำคัญมาก: ส่งค่ากลับไปให้ App หลักใช้ต่อ)
    # =========================================================================
    return {
        'qty': n_total,
        'capacity': total_bolt_capacity,
        'bolt_data': {
            'd': d_mm,
            'grade_name': selected_grade_name,
            'Fnv': Fnv,
            'rows': n_rows,
            'cols': n_cols,
            's_v': s_v,
            's_h': s_h
        }
    }
