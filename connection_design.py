# connection_design.py (V19 - The Gold Standard)
import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade):
    p = section_data
    h_mm, tw_mm, tf_mm = p['h'], p['tw'], p['tf']
    tw_cm, h_cm = tw_mm / 10, h_mm / 10
    
    # 1. BOLT DATA (Reference: AISC Table J3.2)
    b_areas = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}
    Ab = b_areas.get(bolt_size, 3.14)
    d = int(bolt_size[1:]) / 10  # cm
    dh = (int(bolt_size[1:]) + 2) / 10 # hole diameter (standard hole)

    # MATERIAL (SS400 Reference)
    Fy, Fu = 2450, 4000 # kg/cm2

    # Fnv Reference: Table J3.2 (Threads included in shear plane)
    bolt_map = {"A325 (High Strength)": 3795, "Grade 8.8 (Standard)": 3200, "A490 (Premium)": 4780}
    Fnv = bolt_map.get(bolt_grade, 3795)

    # 2. DESIGN PHILOSOPHY SEPARATION (AISC 360 Chapter J)
    if is_lrfd:
        # LRFD: Strength = Phi * Rn
        phi = 0.75 # for Rupture/Shear/Bearing
        phi_y = 1.00 # for Yielding
        omega = 1.00
        label = "LRFD Design (φRn)"
    else:
        # ASD: Strength = Rn / Omega
        phi = 1.00
        omega = 2.00 # for Rupture/Shear/Bearing
        omega_y = 1.50 # for Yielding
        label = "ASD Design (Rn/Ω)"

    # 3. CALCULATE BOLT QUANTITY (Governing Case)
    rn_bolt_shear = Fnv * Ab
    rn_bearing = 2.4 * d * tw_cm * Fu
    rn_single_nom = min(rn_bolt_shear, rn_bearing)
    
    cap_single = (phi * rn_single_nom) / omega
    n_bolts = max(2, math.ceil(V_design / cap_single))
    if n_bolts % 2 != 0: n_bolts += 1
    n_rows = n_bolts // 2

    # LAYOUT (AISC J3.3 & J3.4)
    s = 3.0 * (d * 10)     # Pitch distance
    le = 1.5 * (d * 10)    # Edge distance
    lc = le - (dh * 10 / 2) # Clear distance for tear-out

    # 4. LIMIT STATES ANALYSIS (AISC Chapter J)
    
    # CASE A: Bolt Shear (J3.6)
    Rn_shear = n_bolts * Fnv * Ab
    
    # CASE B: Bearing & Tear-out (J3.10)
    # Rn = 1.2Lc*t*Fu <= 2.4d*t*Fu (Bearing at holes)
    Rn_bearing_total = n_bolts * (2.4 * d * tw_cm * Fu)
    Rn_tearout_total = n_bolts * (1.2 * (lc/10) * tw_cm * Fu)
    Rn_bearing_gov = min(Rn_bearing_total, Rn_tearout_total)

    # CASE C: Block Shear Rupture (J4.3)
    # Anv: Net area subject to shear | Ant: Net area subject to tension
    Ant = (2 * (le/10) - 1.0 * dh) * tw_cm
    Anv = ((n_rows-1)*s/10 + le/10 - (n_rows-0.5)*dh) * tw_cm * 2
    Ubs = 1.0 # Uniform stress distribution
    Rn_block = min(0.6*Fu*Anv + Ubs*Fu*Ant, 0.6*Fy*Anv + Ubs*Fu*Ant)

    # CASE D: Web Shear Yielding (G2.1)
    Rn_yield = 0.6 * Fy * (h_cm * tw_cm)

    # 5. FINAL CAPACITIES BY METHOD
    final_shear = (phi * Rn_shear) / omega
    final_bearing = (phi * Rn_bearing_gov) / omega
    final_block = (phi * Rn_block) / omega
    if is_lrfd: final_yield = (phi_y * Rn_yield) / 1.0
    else: final_yield = (1.0 * Rn_yield) / omega_y

    # --- RENDER UI ---
    st.header(f"⚙️ Connection Design Reference: {label}")
    
    c1, c2, c3, c4 = st.columns(4)
    for col, (name, cap, ref) in zip([c1,c2,c3,c4], 
        [("Bolt Shear", final_shear, "J3.6"), 
         ("Bearing/Tear-out", final_bearing, "J3.10"), 
         ("Block Shear", final_block, "J4.3"), 
         ("Web Yielding", final_yield, "G2.1")]):
        
        ratio = V_design / cap
        st.markdown(f"""
        <div style="text-align:center; padding:10px; border:2px solid {'#ef4444' if ratio > 1 else '#10b981'}40; border-radius:10px;">
            <small style="color:gray;">{ref}</small><br><b>{name}</b><br>
            <h3 style="margin:0; color:{'#ef4444' if ratio > 1 else '#10b981'};">{cap:,.0f} kg</h3>
            <small>Ratio: {ratio:.3f}</small>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # DETAILED CALCULATION NOTES
    with st.expander("📖 รายการคำนวณเชิงลึกแยกตาม AISC 360-16"):
        st.info(f"Design Base: {label} | Bolt Grade: {bolt_grade}")
        
        # Section 1: Shear
        st.subheader("1. Bolt Shear (Chapter J3.6)")
        st.latex(fr"R_n = F_{{nv}} \cdot A_b \cdot N_b = {Fnv} \cdot {Ab} \cdot {n_bolts} = {Rn_shear:,.0f} \text{{ kg}}")
        if is_lrfd: st.latex(fr"\phi R_n = 0.75 \cdot {Rn_shear:,.0f} = {final_shear:,.0f} \text{{ kg}}")
        else: st.latex(fr"R_n/\Omega = {Rn_shear:,.0f}/2.00 = {final_shear:,.0f} \text{{ kg}}")

        # Section 2: Bearing
        st.subheader("2. Bearing & Tear-out (Chapter J3.10)")
        
        st.latex(fr"R_n = \min(2.4 d t F_u, 1.2 L_c t F_u)")
        st.latex(fr"R_n = \min({Rn_bearing_total:,.0f}, {Rn_tearout_total:,.0f}) = {Rn_bearing_gov:,.0f} \text{{ kg}}")
        if is_lrfd: st.latex(fr"\phi R_n = 0.75 \cdot {Rn_bearing_gov:,.0f} = {final_bearing:,.0f} \text{{ kg}}")
        else: st.latex(fr"R_n/\Omega = {Rn_bearing_gov:,.0f}/2.00 = {final_bearing:,.0f} \text{{ kg}}")

        # Section 3: Block Shear
        st.subheader("3. Block Shear Rupture (Chapter J4.3)")
        
        st.latex(fr"R_n = \min(0.6F_u A_{{nv}} + U_{{bs}}F_u A_{{nt}}, 0.6F_y A_{{nv}} + U_{{bs}}F_u A_{{nt}})")
        st.write(f"Net Shear Area ($A_{{nv}}$): {Anv:.2f} cm², Net Tension Area ($A_{{nt}}$): {Ant:.2f} cm²")
        st.latex(fr"R_n = {Rn_block:,.0f} \text{{ kg}}")
        
        # Section 4: Geometry
        st.subheader("4. Dimensional Constraints")
        st.write(f"- Minimum Spacing (J3.3): 2.67d = {2.67*d*10:.1f} mm | **Used: {s} mm**")
        st.write(f"- Minimum Edge Distance (Table J3.4): {le} mm | **Used: {le} mm**")

    return n_bolts, cap_single
