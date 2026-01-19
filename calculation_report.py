import math

def generate_report(V_load, T_load, beam, plate, bolts, cope, is_lrfd, material_grade, bolt_grade):
    """
    Generate Markdown Calculation Report (Strict AISC Format)
    Units: Forces in kN, Dimensions in mm
    """
    
    # --- 1. SET FACTORS ---
    method = "LRFD" if is_lrfd else "ASD"
    
    if is_lrfd:
        # Phi factors
        phi_y = 0.90
        phi_r = 0.75
        phi_w = 0.75
        phi_b = 0.75
        lab_cap = "Design Strength (ϕRn)"
        lab_dem = "Factored Load (Ru)"
    else:
        # Omega factors (ASD)
        om_y = 1.67
        om_r = 2.00
        om_w = 2.00
        om_b = 2.00
        lab_cap = "Allowable Strength (Rn/Ω)"
        lab_dem = "Service Load (Ra)"

    # --- 2. PREPARE VARIABLES ---
    # Unpack for clarity
    d = bolts['d']
    rows = bolts['rows']
    cols = bolts['cols']
    n_bolts = rows * cols
    
    t_plt = plate['t']
    Fy_plt = plate['Fy']
    Fu_plt = plate['Fu']
    
    # --- 3. START REPORT ---
    lines = []
    lines.append(f"# 🏗️ CONNECTION DESIGN REPORT ({method})")
    lines.append(f"**Material:** {material_grade} | **Bolt:** {bolt_grade} (M{d})")
    lines.append(f"**Load:** Shear V = {V_load:.2f} kN | Tension T = {T_load:.2f} kN")
    lines.append("---")

    # =================================================
    # CHECK 1: BOLT SHEAR
    # =================================================
    lines.append("### 1. Bolt Shear Strength")
    Ab = math.pi * d**2 / 4
    Fnv = bolts['Fnv']
    
    Rn_shear = Fnv * Ab * n_bolts / 1000.0 # kN (Total)
    
    if is_lrfd:
        Cap_Shear = phi_b * Rn_shear
    else:
        Cap_Shear = Rn_shear / om_b
        
    ratio_shear = V_load / Cap_Shear
    status_shear = "✅ PASS" if ratio_shear <= 1.0 else "❌ FAIL"

    lines.append(f"- **Nominal Strength ($R_n$):** {Rn_shear:.2f} kN")
    lines.append(f"- **{lab_cap}:** {Cap_Shear:.2f} kN")
    lines.append(f"- **{lab_dem}:** {V_load:.2f} kN")  # <--- FIX: Show Input Load directly
    lines.append(f"- **Ratio:** {ratio_shear:.2f}  [{status_shear}]")
    lines.append("")

    # =================================================
    # CHECK 2: BOLT BEARING & TEAROUT
    # =================================================
    lines.append("### 2. Bolt Bearing & Tearout")
    d_hole = d + 2.0
    lc_edge = plate['lv'] - (d_hole / 2.0)
    lc_inner = bolts['s_v'] - d_hole
    
    # Rn per bolt (N)
    rn_edge = min(1.2 * lc_edge * t_plt * Fu_plt, 2.4 * d * t_plt * Fu_plt)
    rn_inner = min(1.2 * lc_inner * t_plt * Fu_plt, 2.4 * d * t_plt * Fu_plt)
    
    if rows >= 2:
        Rn_bearing_total = (rn_edge + (rows - 1) * rn_inner) * cols
    else:
        Rn_bearing_total = rn_edge * cols
        
    Rn_bearing_kN = Rn_bearing_total / 1000.0
    
    if is_lrfd:
        Cap_Bearing = phi_r * Rn_bearing_kN
    else:
        Cap_Bearing = Rn_bearing_kN / om_r # Use Omega = 2.00 for Bearing
        
    ratio_bear = V_load / Cap_Bearing
    status_bear = "✅ PASS" if ratio_bear <= 1.0 else "❌ FAIL"

    lines.append(f"- **Nominal Strength ($R_n$):** {Rn_bearing_kN:.2f} kN")
    lines.append(f"- **{lab_cap}:** {Cap_Bearing:.2f} kN")
    lines.append(f"- **{lab_dem}:** {V_load:.2f} kN") # <--- FIX: Same Demand
    lines.append(f"- **Ratio:** {ratio_bear:.2f}  [{status_bear}]")
    lines.append("")

    # =================================================
    # CHECK 3: PLATE SHEAR YIELDING
    # =================================================
    lines.append("### 3. Plate Shear Yielding")
    Agv = plate['h'] * t_plt
    Rn_yield = 0.60 * Fy_plt * Agv / 1000.0
    
    if is_lrfd:
        Cap_Yield = phi_y * Rn_yield
    else:
        Cap_Yield = Rn_yield / om_y # Use Omega = 1.67
        
    ratio_yield = V_load / Cap_Yield
    status_yield = "✅ PASS" if ratio_yield <= 1.0 else "❌ FAIL"

    lines.append(f"- **Nominal Strength ($R_n$):** {Rn_yield:.2f} kN")
    lines.append(f"- **{lab_cap}:** {Cap_Yield:.2f} kN")
    lines.append(f"- **{lab_dem}:** {V_load:.2f} kN") # <--- FIX: Same Demand
    lines.append(f"- **Ratio:** {ratio_yield:.2f}  [{status_yield}]")
    lines.append("")

    # =================================================
    # CHECK 4: PLATE SHEAR RUPTURE
    # =================================================
    lines.append("### 4. Plate Shear Rupture")
    Anv = (plate['h'] - (rows * d_hole)) * t_plt
    Rn_rup = 0.60 * Fu_plt * Anv / 1000.0
    
    if is_lrfd:
        Cap_Rup = phi_r * Rn_rup
    else:
        Cap_Rup = Rn_rup / om_r # Use Omega = 2.00
        
    ratio_rup = V_load / Cap_Rup
    status_rup = "✅ PASS" if ratio_rup <= 1.0 else "❌ FAIL"

    lines.append(f"- **Nominal Strength ($R_n$):** {Rn_rup:.2f} kN")
    lines.append(f"- **{lab_cap}:** {Cap_Rup:.2f} kN")
    lines.append(f"- **{lab_dem}:** {V_load:.2f} kN") # <--- FIX: Same Demand
    lines.append(f"- **Ratio:** {ratio_rup:.2f}  [{status_rup}]")
    lines.append("")

    # =================================================
    # CHECK 5: BLOCK SHEAR
    # =================================================
    lines.append("### 5. Block Shear Strength")
    # Geometry recalculation for Report clarity
    L_gv = plate['lv'] + (rows - 1) * bolts['s_v']
    Agv_bs = L_gv * t_plt * cols
    Anv_bs = (L_gv - (rows - 0.5) * d_hole) * t_plt * cols
    Ant_bs = (plate['l_side'] - 0.5 * d_hole) * t_plt * cols
    Ubs = 1.0
    
    term1 = (0.6 * Fu_plt * Anv_bs) + (Ubs * Fu_plt * Ant_bs)
    term2 = (0.6 * Fy_plt * Agv_bs) + (Ubs * Fu_plt * Ant_bs)
    Rn_bs = min(term1, term2) / 1000.0
    
    if is_lrfd:
        Cap_BS = phi_r * Rn_bs
    else:
        Cap_BS = Rn_bs / om_r # Use Omega = 2.00
        
    ratio_bs = V_load / Cap_BS
    status_bs = "✅ PASS" if ratio_bs <= 1.0 else "❌ FAIL"

    lines.append(f"- **Nominal Strength ($R_n$):** {Rn_bs:.2f} kN")
    lines.append(f"- **{lab_cap}:** {Cap_BS:.2f} kN")
    lines.append(f"- **{lab_dem}:** {V_load:.2f} kN") # <--- FIX: Same Demand
    lines.append(f"- **Ratio:** {ratio_bs:.2f}  [{status_bs}]")
    lines.append("")
    
    # =================================================
    # SUMMARY
    # =================================================
    lines.append("### 📝 Conclusion")
    max_ratio = max(ratio_shear, ratio_bear, ratio_yield, ratio_rup, ratio_bs)
    final_status = "PASSED" if max_ratio <= 1.0 else "FAILED"
    
    lines.append(f"The connection design has **{final_status}** with a maximum Utility Ratio of **{max_ratio:.2f}**.")
    
    return "\n".join(lines)
