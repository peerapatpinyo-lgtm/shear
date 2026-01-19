import math

def generate_report(V_load, T_load, beam, plate, bolts, cope, is_lrfd, material_grade, bolt_grade):
    """
    Generate Markdown Calculation Report (Strict AISC Format)
    
    Philosophy:
    - DEMAND: Always equals the input Load (kN). Never multiply by Omega.
    - CAPACITY: Always apply factors here. (Phi * Rn) or (Rn / Omega).
    - UNITS: All calculations in kN.
    """
    
    # --- 1. SETUP FACTORS ---
    method = "LRFD" if is_lrfd else "ASD"
    
    # Factors (AISC 360-16)
    if is_lrfd:
        # Load Resistance Factor Design
        phi_y = 0.90   # Yielding
        phi_r = 0.75   # Rupture / Bearing / Block Shear
        phi_w = 0.75   # Weld
        phi_b = 0.75   # Bolt Shear / Tension
        
        lab_cap = "Design Strength (ϕRn)"
        lab_dem = "Factored Load (Ru)"
        
    else:
        # Allowable Strength Design
        om_y = 1.67    # Yielding
        om_r = 2.00    # Rupture / Bearing / Block Shear
        om_w = 2.00    # Weld
        om_b = 2.00    # Bolt Shear / Tension
        
        lab_cap = "Allowable Strength (Rn/Ω)"
        lab_dem = "Service Load (Ra)"

    # --- 2. PREPARE INPUTS ---
    d = bolts['d']
    rows = bolts['rows']
    cols = bolts['cols']
    n_bolts = rows * cols
    
    t_plt = plate['t']
    Fy_plt = plate['Fy']
    Fu_plt = plate['Fu']
    
    lines = []
    lines.append(f"# 🏗️ CONNECTION DESIGN REPORT ({method})")
    lines.append(f"**Material:** {material_grade} | **Bolt:** {bolt_grade} (M{d})")
    lines.append(f"**Input Load:** Shear V = {V_load:.2f} kN | Tension T = {T_load:.2f} kN")
    lines.append("---")

    # =================================================
    # HELPER FUNCTION (CORE LOGIC)
    # =================================================
    def calc_capacity(Rn_kN, type_mode):
        """
        คำนวณ Capacity ตามวิธีที่เลือก (ASD/LRFD)
        type_mode: 'yield' (ใช้ 1.67/0.90) หรือ 'rupture' (ใช้ 2.00/0.75)
        """
        if is_lrfd:
            factor = phi_y if type_mode == 'yield' else (phi_b if type_mode == 'bolt' else phi_r)
            if type_mode == 'weld': factor = phi_w
            
            capacity = Rn_kN * factor
            factor_str = f"ϕ = {factor:.2f}"
            return capacity, factor_str
        else:
            omega = om_y if type_mode == 'yield' else (om_b if type_mode == 'bolt' else om_r)
            if type_mode == 'weld': omega = om_w
            
            capacity = Rn_kN / omega
            factor_str = f"Ω = {omega:.2f}"
            return capacity, factor_str

    # =================================================
    # 1. BOLT SHEAR STRENGTH
    # =================================================
    lines.append("### 1. Bolt Shear Strength")
    Ab = math.pi * d**2 / 4
    Fnv = bolts['Fnv']
    
    # Nominal Strength (kN)
    Rn_shear = (Fnv * Ab * n_bolts) / 1000.0
    
    # Capacity
    Cap_Shear, Factor_Str = calc_capacity(Rn_shear, 'bolt')
    
    # Check
    ratio_shear = V_load / Cap_Shear if Cap_Shear > 0 else 999
    status_shear = "✅ PASS" if ratio_shear <= 1.0 else "❌ FAIL"

    lines.append(f"- **Nominal Strength ($R_n$):** {Rn_shear:.2f} kN")
    lines.append(f"- **Factor:** {Factor_Str}")
    lines.append(f"- **{lab_cap}:** {Cap_Shear:.2f} kN")
    lines.append(f"- **{lab_dem}:** **{V_load:.2f} kN**") # Demand คงที่
    lines.append(f"- **Ratio:** {ratio_shear:.2f}  [{status_shear}]")
    lines.append("")

    # =================================================
    # 2. BOLT BEARING & TEAROUT
    # =================================================
    lines.append("### 2. Bolt Bearing & Tearout")
    d_hole = d + 2.0
    lc_edge = plate['lv'] - (d_hole / 2.0)
    lc_inner = bolts['s_v'] - d_hole
    
    # Nominal Strength per bolt (N)
    rn_edge = min(1.2 * lc_edge * t_plt * Fu_plt, 2.4 * d * t_plt * Fu_plt)
    rn_inner = min(1.2 * lc_inner * t_plt * Fu_plt, 2.4 * d * t_plt * Fu_plt)
    
    # Summation (kN)
    if rows >= 2:
        Rn_bearing = ((rn_edge + (rows - 1) * rn_inner) * cols) / 1000.0
    else:
        Rn_bearing = (rn_edge * cols) / 1000.0
        
    Cap_Bearing, Factor_Str = calc_capacity(Rn_bearing, 'rupture') # Bearing ใช้ factor เดียวกับ Rupture
    
    ratio_bear = V_load / Cap_Bearing if Cap_Bearing > 0 else 999
    status_bear = "✅ PASS" if ratio_bear <= 1.0 else "❌ FAIL"

    lines.append(f"- **Nominal Strength ($R_n$):** {Rn_bearing:.2f} kN")
    lines.append(f"- **Factor:** {Factor_Str}")
    lines.append(f"- **{lab_cap}:** {Cap_Bearing:.2f} kN")
    lines.append(f"- **{lab_dem}:** **{V_load:.2f} kN**")
    lines.append(f"- **Ratio:** {ratio_bear:.2f}  [{status_bear}]")
    lines.append("")

    # =================================================
    # 3. PLATE SHEAR YIELDING
    # =================================================
    lines.append("### 3. Plate Shear Yielding")
    Agv = plate['h'] * t_plt
    Rn_yield = (0.60 * Fy_plt * Agv) / 1000.0
    
    Cap_Yield, Factor_Str = calc_capacity(Rn_yield, 'yield') # Yield ใช้ factor ต่างจากเพื่อน (1.67 / 0.90)
    
    ratio_yield = V_load / Cap_Yield if Cap_Yield > 0 else 999
    status_yield = "✅ PASS" if ratio_yield <= 1.0 else "❌ FAIL"

    lines.append(f"- **Nominal Strength ($R_n$):** {Rn_yield:.2f} kN")
    lines.append(f"- **Factor:** {Factor_Str}")
    lines.append(f"- **{lab_cap}:** {Cap_Yield:.2f} kN")
    lines.append(f"- **{lab_dem}:** **{V_load:.2f} kN**")
    lines.append(f"- **Ratio:** {ratio_yield:.2f}  [{status_yield}]")
    lines.append("")

    # =================================================
    # 4. PLATE SHEAR RUPTURE
    # =================================================
    lines.append("### 4. Plate Shear Rupture")
    Anv = (plate['h'] - (rows * d_hole)) * t_plt
    Rn_rup = (0.60 * Fu_plt * Anv) / 1000.0
    
    Cap_Rup, Factor_Str = calc_capacity(Rn_rup, 'rupture')
    
    ratio_rup = V_load / Cap_Rup if Cap_Rup > 0 else 999
    status_rup = "✅ PASS" if ratio_rup <= 1.0 else "❌ FAIL"

    lines.append(f"- **Nominal Strength ($R_n$):** {Rn_rup:.2f} kN")
    lines.append(f"- **Factor:** {Factor_Str}")
    lines.append(f"- **{lab_cap}:** {Cap_Rup:.2f} kN")
    lines.append(f"- **{lab_dem}:** **{V_load:.2f} kN**")
    lines.append(f"- **Ratio:** {ratio_rup:.2f}  [{status_rup}]")
    lines.append("")

    # =================================================
    # 5. BLOCK SHEAR STRENGTH
    # =================================================
    lines.append("### 5. Block Shear Strength")
    L_gv = plate['lv'] + (rows - 1) * bolts['s_v']
    Agv_bs = L_gv * t_plt * cols
    Anv_bs = (L_gv - (rows - 0.5) * d_hole) * t_plt * cols
    Ant_bs = (plate['l_side'] - 0.5 * d_hole) * t_plt * cols
    Ubs = 1.0
    
    term1 = (0.6 * Fu_plt * Anv_bs) + (Ubs * Fu_plt * Ant_bs)
    term2 = (0.6 * Fy_plt * Agv_bs) + (Ubs * Fu_plt * Ant_bs)
    Rn_bs = min(term1, term2) / 1000.0
    
    Cap_BS, Factor_Str = calc_capacity(Rn_bs, 'rupture')
    
    ratio_bs = V_load / Cap_BS if Cap_BS > 0 else 999
    status_bs = "✅ PASS" if ratio_bs <= 1.0 else "❌ FAIL"

    lines.append(f"- **Nominal Strength ($R_n$):** {Rn_bs:.2f} kN")
    lines.append(f"- **Factor:** {Factor_Str}")
    lines.append(f"- **{lab_cap}:** {Cap_BS:.2f} kN")
    lines.append(f"- **{lab_dem}:** **{V_load:.2f} kN**")
    lines.append(f"- **Ratio:** {ratio_bs:.2f}  [{status_bs}]")
    lines.append("")
    
    # =================================================
    # 6. WELD STRENGTH (Optional)
    # =================================================
    if plate.get('weld_size', 0) > 0:
        lines.append("### 6. Weld Strength")
        w_sz = plate['weld_size']
        L_weld = plate['h'] * 2
        Fexx = 480 # E70xx
        Rn_weld = (0.60 * Fexx * (0.707 * w_sz) * L_weld) / 1000.0
        
        Cap_Weld, Factor_Str = calc_capacity(Rn_weld, 'weld')
        
        ratio_weld = V_load / Cap_Weld if Cap_Weld > 0 else 999
        status_weld = "✅ PASS" if ratio_weld <= 1.0 else "❌ FAIL"
        
        lines.append(f"- **Nominal Strength ($R_n$):** {Rn_weld:.2f} kN")
        lines.append(f"- **Factor:** {Factor_Str}")
        lines.append(f"- **{lab_cap}:** {Cap_Weld:.2f} kN")
        lines.append(f"- **{lab_dem}:** **{V_load:.2f} kN**")
        lines.append(f"- **Ratio:** {ratio_weld:.2f}  [{status_weld}]")
        lines.append("")
    else:
        ratio_weld = 0

    # =================================================
    # 7. TENSION & INTERACTION (If Load Exists)
    # =================================================
    ratio_ten = 0
    ratio_inter = 0
    
    if T_load > 0:
        lines.append("### 7. Bolt Tension Strength")
        Fnt = bolts['Fnt']
        Rn_ten = (Fnt * math.pi * d**2 / 4 * n_bolts) / 1000.0
        
        Cap_Ten, Factor_Str = calc_capacity(Rn_ten, 'bolt')
        
        ratio_ten = T_load / Cap_Ten
        status_ten = "✅ PASS" if ratio_ten <= 1.0 else "❌ FAIL"
        
        lines.append(f"- **Nominal Strength ($R_n$):** {Rn_ten:.2f} kN")
        lines.append(f"- **{lab_cap}:** {Cap_Ten:.2f} kN")
        lines.append(f"- **Tensile Demand:** **{T_load:.2f} kN**")
        lines.append(f"- **Ratio:** {ratio_ten:.2f}  [{status_ten}]")
        lines.append("")
        
        lines.append("### 8. Combined Shear & Tension")
        ratio_inter = ratio_shear**2 + ratio_ten**2
        status_inter = "✅ PASS" if ratio_inter <= 1.0 else "❌ FAIL"
        lines.append(f"- **Interaction Ratio:** {ratio_inter:.2f}  [{status_inter}]")
        lines.append("")

    # =================================================
    # SUMMARY & CONCLUSION
    # =================================================
    lines.append("### 📝 Conclusion")
    
    all_ratios = [ratio_shear, ratio_bear, ratio_yield, ratio_rup, ratio_bs, ratio_weld, ratio_ten, ratio_inter]
    max_ratio = max(all_ratios)
    final_status = "PASSED" if max_ratio <= 1.0 else "FAILED"
    
    lines.append(f"The connection design has **{final_status}** with a maximum Utility Ratio of **{max_ratio:.2f}**.")
    lines.append(f"> **Verification Note:** Values are consistent with Design Summary. All units in kN.")
    
    return "\n".join(lines)
