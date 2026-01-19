import math

def generate_report(V_load, T_load, beam, plate, bolts, cope, is_lrfd, material_grade, bolt_grade):
    """
    Generate Detailed Calculation Report with Formulas & Substitution
    Standard: AISC 360-16
    """
    
    # --- 1. SETUP FACTORS ---
    method = "LRFD" if is_lrfd else "ASD"
    
    if is_lrfd:
        phi_y, phi_r, phi_b, phi_w = 0.90, 0.75, 0.75, 0.75
        lab_cap = "Design Strength (ϕRn)"
        lab_dem = "Factored Load (Ru)"
    else:
        om_y, om_r, om_b, om_w = 1.67, 2.00, 2.00, 2.00
        lab_cap = "Allowable Strength (Rn/Ω)"
        lab_dem = "Service Load (Ra)"

    # --- 2. PREPARE VARIABLES ---
    d = bolts['d']
    d_hole = d + 2.0 # Standard hole size
    rows = bolts['rows']
    cols = bolts['cols']
    n_bolts = rows * cols
    
    t_plt = plate['t']
    Fy = plate['Fy']
    Fu = plate['Fu']
    h_plate = plate['h']
    
    # --- HELPER: FORMAT CAPACITY ---
    def fmt_cap(Rn_kN, type_mode):
        if is_lrfd:
            fac = phi_y if type_mode == 'yield' else (phi_b if type_mode == 'bolt' else phi_r)
            if type_mode == 'weld': fac = phi_w
            return Rn_kN * fac, f"ϕR_n = {fac:.2f} \\times {Rn_kN:.2f}"
        else:
            om = om_y if type_mode == 'yield' else (om_b if type_mode == 'bolt' else om_r)
            if type_mode == 'weld': om = om_w
            return Rn_kN / om, f"R_n / \Omega = {Rn_kN:.2f} / {om:.2f}"

    lines = []
    lines.append(f"# 🏗️ DETAILED CALCULATION ({method})")
    lines.append(f"**Material:** {material_grade} ($F_y={Fy}, F_u={Fu}$ MPa)")
    lines.append(f"**Bolt:** {bolt_grade} M{d} ($A_b={math.pi*d**2/4:.1f} mm^2$)")
    lines.append(f"**Load:** Shear V = {V_load:.2f} kN")
    lines.append("---")

    # =================================================
    # 1. BOLT SHEAR
    # =================================================
    lines.append("### 1. Bolt Shear Strength")
    lines.append("Limit state of bolt shear:")
    lines.append("$$ R_n = F_{nv} \\times A_b \\times N_{bolts} $$")
    
    Ab = math.pi * d**2 / 4
    Fnv = bolts['Fnv']
    Rn_shear = (Fnv * Ab * n_bolts) / 1000.0
    
    lines.append(f"$$ R_n = {Fnv} \\times {Ab:.1f} \\times {n_bolts} = {Rn_shear*1000:,.0f} \\text{ N} = \\mathbf{{{Rn_shear:.2f} \\text{ kN}}} $$")
    
    Cap_Shear, Eq_Cap = fmt_cap(Rn_shear, 'bolt')
    ratio_shear = V_load / Cap_Shear
    status = "✅ OK" if ratio_shear <= 1.0 else "❌ FAIL"
    
    lines.append(f"- **Capacity:** $ {Eq_Cap} = \\mathbf{{{Cap_Shear:.2f} \\text{ kN}}} $")
    lines.append(f"- **Demand:** $ V = {V_load:.2f} \\text{ kN} $")
    lines.append(f"- **Ratio:** $ {ratio_shear:.2f} $ {status}")
    lines.append("")

    # =================================================
    # 2. BEARING & TEAROUT
    # =================================================
    lines.append("### 2. Bolt Bearing & Tearout")
    lines.append("Check both edge bolt and inner bolts (if any).")
    lines.append("$$ R_n = 1.2 l_c t F_u \\leq 2.4 d t F_u $$")
    
    # Calc Lc
    lc_edge = plate['lv'] - (d_hole / 2.0)
    lc_inner = bolts['s_v'] - d_hole
    max_bear = 2.4 * d * t_plt * Fu
    
    # Edge Bolt
    rn_edge_raw = 1.2 * lc_edge * t_plt * Fu
    rn_edge = min(rn_edge_raw, max_bear)
    
    lines.append(f"**Edge Bolt ($l_c = {lc_edge:.1f}$ mm):**")
    lines.append(f"$$ r_{{n,edge}} = \\min(1.2({lc_edge:.1f})({t_plt})({Fu}), 2.4({d})({t_plt})({Fu})) $$")
    lines.append(f"$$ r_{{n,edge}} = \\min({rn_edge_raw/1000:.1f}, {max_bear/1000:.1f}) = {rn_edge/1000:.2f} \\text{ kN/bolt} $$")
    
    # Inner Bolt
    if rows > 1:
        rn_inner_raw = 1.2 * lc_inner * t_plt * Fu
        rn_inner = min(rn_inner_raw, max_bear)
        lines.append(f"**Inner Bolt ($l_c = {lc_inner:.1f}$ mm):**")
        lines.append(f"$$ r_{{n,in}} = \\min(1.2({lc_inner:.1f})({t_plt})({Fu}), 2.4({d})({t_plt})({Fu})) $$")
        lines.append(f"$$ r_{{n,in}} = {rn_inner/1000:.2f} \\text{ kN/bolt} $$")
    else:
        rn_inner = 0
        lines.append("*(No inner bolts)*")

    # Total
    Rn_bearing = ((rn_edge * cols) + (rn_inner * (rows - 1) * cols)) / 1000.0
    lines.append(f"$$ R_{{n,total}} = ({cols} \\times \\text{edge}) + ({cols*(rows-1)} \\times \\text{inner}) = \\mathbf{{{Rn_bearing:.2f} \\text{ kN}}} $$")
    
    Cap_Bear, Eq_Cap = fmt_cap(Rn_bearing, 'rupture')
    ratio_bear = V_load / Cap_Bear
    status = "✅ OK" if ratio_bear <= 1.0 else "❌ FAIL"
    
    lines.append(f"- **Capacity:** $ {Eq_Cap} = \\mathbf{{{Cap_Bear:.2f} \\text{ kN}}} $")
    lines.append(f"- **Ratio:** $ {ratio_bear:.2f} $ {status}")
    lines.append("")

    # =================================================
    # 3. PLATE SHEAR YIELDING
    # =================================================
    lines.append("### 3. Plate Shear Yielding")
    lines.append("$$ R_n = 0.60 F_y A_g $$")
    
    Ag = h_plate * t_plt
    Rn_yield = 0.60 * Fy * Ag / 1000.0
    
    lines.append(f"- Gross Area $A_g = {h_plate} \\times {t_plt} = {Ag:.0f} \\text{ mm}^2$")
    lines.append(f"$$ R_n = 0.60 \\times {Fy} \\times {Ag} = \\mathbf{{{Rn_yield:.2f} \\text{ kN}}} $$")
    
    Cap_Yield, Eq_Cap = fmt_cap(Rn_yield, 'yield')
    ratio_yield = V_load / Cap_Yield
    status = "✅ OK" if ratio_yield <= 1.0 else "❌ FAIL"
    
    lines.append(f"- **Capacity:** $ {Eq_Cap} = \\mathbf{{{Cap_Yield:.2f} \\text{ kN}}} $")
    lines.append(f"- **Ratio:** $ {ratio_yield:.2f} $ {status}")
    lines.append("")

    # =================================================
    # 4. PLATE SHEAR RUPTURE
    # =================================================
    lines.append("### 4. Plate Shear Rupture")
    lines.append("$$ R_n = 0.60 F_u A_{nv} $$")
    
    Anv = (h_plate - (rows * d_hole)) * t_plt
    Rn_rup = 0.60 * Fu * Anv / 1000.0
    
    lines.append(f"- Net Area $A_{{nv}} = ({h_plate} - {rows}({d_hole}))({t_plt}) = {Anv:.0f} \\text{ mm}^2$")
    lines.append(f"$$ R_n = 0.60 \\times {Fu} \\times {Anv} = \\mathbf{{{Rn_rup:.2f} \\text{ kN}}} $$")
    
    Cap_Rup, Eq_Cap = fmt_cap(Rn_rup, 'rupture')
    ratio_rup = V_load / Cap_Rup
    status = "✅ OK" if ratio_rup <= 1.0 else "❌ FAIL"
    
    lines.append(f"- **Capacity:** $ {Eq_Cap} = \\mathbf{{{Cap_Rup:.2f} \\text{ kN}}} $")
    lines.append(f"- **Ratio:** $ {ratio_rup:.2f} $ {status}")
    lines.append("")

    # =================================================
    # 5. BLOCK SHEAR
    # =================================================
    lines.append("### 5. Block Shear")
    lines.append("$$ R_n = \\min [ 0.6 F_u A_{nv} + U_{bs} F_u A_{nt}, 0.6 F_y A_{gv} + U_{bs} F_u A_{nt} ] $$")
    
    # Geometry
    L_gv = plate['lv'] + (rows - 1) * bolts['s_v']
    Agv = L_gv * t_plt * cols
    Anv = (L_gv - (rows - 0.5) * d_hole) * t_plt * cols
    Ant = (plate['l_side'] - 0.5 * d_hole) * t_plt * cols
    Ubs = 1.0
    
    lines.append(f"- Shear Gross $A_{{gv}} = {Agv:.0f} \\text{ mm}^2$")
    lines.append(f"- Shear Net $A_{{nv}} = {Anv:.0f} \\text{ mm}^2$")
    lines.append(f"- Tension Net $A_{{nt}} = {Ant:.0f} \\text{ mm}^2$")
    
    term1 = (0.6 * Fu * Anv) + (Ubs * Fu * Ant)
    term2 = (0.6 * Fy * Agv) + (Ubs * Fu * Ant)
    Rn_bs = min(term1, term2) / 1000.0
    
    lines.append(f"$$ Term 1 (Rupture) = 0.6({Fu})({Anv:.0f}) + 1.0({Fu})({Ant:.0f}) = {term1/1000:.1f} \\text{ kN} $$")
    lines.append(f"$$ Term 2 (Yield) = 0.6({Fy})({Agv:.0f}) + 1.0({Fu})({Ant:.0f}) = {term2/1000:.1f} \\text{ kN} $$")
    lines.append(f"$$ R_n = \\min({term1/1000:.1f}, {term2/1000:.1f}) = \\mathbf{{{Rn_bs:.2f} \\text{ kN}}} $$")
    
    Cap_BS, Eq_Cap = fmt_cap(Rn_bs, 'rupture')
    ratio_bs = V_load / Cap_BS
    status = "✅ OK" if ratio_bs <= 1.0 else "❌ FAIL"
    
    lines.append(f"- **Capacity:** $ {Eq_Cap} = \\mathbf{{{Cap_BS:.2f} \\text{ kN}}} $")
    lines.append(f"- **Ratio:** $ {ratio_bs:.2f} $ {status}")
    lines.append("")

    # =================================================
    # SUMMARY
    # =================================================
    lines.append("### 📝 Conclusion")
    all_ratios = [ratio_shear, ratio_bear, ratio_yield, ratio_rup, ratio_bs]
    max_ratio = max(all_ratios)
    lines.append(f"**Max Utility Ratio:** {max_ratio:.2f} ({'PASSED' if max_ratio<=1.0 else 'FAILED'})")
    lines.append(f"> Note: Demand ($V={V_load:.2f}$ kN) is constant. Safety factors are applied to Capacity.")

    return "\n".join(lines)
