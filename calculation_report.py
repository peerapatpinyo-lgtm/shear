import math

def generate_report(V_load, T_load, beam, plate, bolts, cope, is_lrfd, material_grade, bolt_grade):
    """
    Generate Professional Structural Calculation Report
    Standard: AISC 360-16
    Style: Senior Engineer / Academic Step-by-Step
    """
    
    # --- 1. DESIGN PARAMETERS & CONSTANTS ---
    method = "LRFD" if is_lrfd else "ASD"
    
    if is_lrfd:
        phi_y, phi_r, phi_b, phi_w = 0.90, 0.75, 0.75, 0.75
        cap_label = "Design Strength (\\phi R_n)"
        load_label = "Factored Load (V_u)"
    else:
        om_y, om_r, om_b, om_w = 1.67, 2.00, 2.00, 2.00
        cap_label = "Allowable Strength (R_n/\\Omega)"
        load_label = "Service Load (V_a)"

    # --- 2. GEOMETRIC PROPERTIES ---
    d_bolt = bolts['d']
    d_hole = d_bolt + 2.0 # Standard hole
    rows = bolts['rows']
    cols = bolts['cols']
    n_bolts = rows * cols
    
    t_plt = plate['t']
    Fy = plate['Fy']
    Fu = plate['Fu']
    h_plate = plate['h']
    
    # --- HELPER: FORMATTING FUNCTION ---
    def render_check(Rn_kN, limit_state_type, demand):
        """Standardized Capacity Check Block"""
        if is_lrfd:
            factor = phi_y if limit_state_type == 'yield' else (phi_b if limit_state_type == 'bolt' else phi_r)
            capacity = Rn_kN * factor
            eq_str = f"\\phi R_n = {factor:.2f} ( {Rn_kN:.2f} )"
        else:
            omega = om_y if limit_state_type == 'yield' else (om_b if limit_state_type == 'bolt' else om_r)
            capacity = Rn_kN / omega
            eq_str = f"\\frac{{R_n}}{{\\Omega}} = \\frac{{{Rn_kN:.2f}}}{{{omega:.2f}}}"
            
        ratio = demand / capacity if capacity > 0 else 999
        status = "✅ OK" if ratio <= 1.0 else "❌ N.G."
        
        # Markdown Block
        block = []
        block.append(f"> **Check:**")
        block.append(f"> $$ {cap_label} = {eq_str} = \\mathbf{{{capacity:.2f} \\text{{ kN}}}} $$")
        block.append(f"> $$ \\text{{Ratio}} = \\frac{{{demand:.2f}}}{{{capacity:.2f}}} = \\mathbf{{{ratio:.2f}}} \\quad [{status}] $$")
        return "\n".join(block)

    lines = []
    
    # =================================================
    # HEADER SECTION
    # =================================================
    lines.append(f"# 🏗️ CONNECTION DESIGN REPORT ({method})")
    lines.append("---")
    lines.append("### 📋 Design Parameters")
    lines.append(f"**1. Loading**")
    lines.append(f"- Shear Demand ($V_{{req}}$): **{V_load:.2f} kN**")
    lines.append(f"")
    lines.append(f"**2. Component Properties**")
    lines.append(f"- **Plate:** {material_grade} ($F_y={Fy}$ MPa, $F_u={Fu}$ MPa), $t={t_plt}$ mm, $h={h_plate}$ mm")
    lines.append(f"- **Bolts:** {n_bolts} nos. M{d_bolt} (Grade {bolt_grade}), Hole $\\phi {d_hole}$ mm")
    lines.append("---")
    lines.append("")

    # =================================================
    # 1. BOLT SHEAR (AISC J3.6)
    # =================================================
    lines.append("### 1. Bolt Shear Strength")
    lines.append("*Reference: AISC Spec. Section J3.6*")
    
    Ab = math.pi * d_bolt**2 / 4
    Fnv = bolts['Fnv']
    Rn_shear = (Fnv * Ab * n_bolts) / 1000.0
    
    lines.append(f"**Step 1: Determine Nominal Strength ($R_n$)**")
    lines.append(f"$$ R_n = F_{{nv}} A_b N_b $$")
    lines.append(f"Where:")
    lines.append(f"- $F_{{nv}} = {Fnv}$ MPa (Nominal Shear Stress)")
    lines.append(f"- $A_b = \\frac{{\\pi ({d_bolt})^2}}{{4}} = {Ab:.1f} \\text{{ mm}}^2$ (Bolt Area)")
    
    lines.append(f"**Substitution:**")
    lines.append(f"$$ R_n = {Fnv} \\times {Ab:.1f} \\times {n_bolts} = {Rn_shear*1000:,.0f} \\text{{ N}} $$")
    lines.append(f"$$ R_n = {Rn_shear:.2f} \\text{{ kN}} $$")
    
    lines.append(render_check(Rn_shear, 'bolt', V_load))
    lines.append("---")
    lines.append("")

    # =================================================
    # 2. BOLT BEARING (AISC J3.10)
    # =================================================
    lines.append("### 2. Bolt Bearing & Tearout")
    lines.append("*Reference: AISC Spec. Section J3.10*")
    lines.append("Checks are performed for edge bolts and inner bolts separately.")
    
    lc_edge = plate['lv'] - (d_hole / 2.0)
    lc_inner = bolts['s_v'] - d_hole
    max_bear_load = 2.4 * d_bolt * t_plt * Fu
    
    lines.append(f"**Step 1: Calculate Clear Distances ($l_c$)**")
    lines.append(f"- Edge Bolts: $l_{{c,edge}} = {plate['lv']} - ({d_hole}/2) = {lc_edge:.1f}$ mm")
    if rows > 1:
        lines.append(f"- Inner Bolts: $l_{{c,in}} = {bolts['s_v']} - {d_hole} = {lc_inner:.1f}$ mm")
    
    lines.append(f"")
    lines.append(f"**Step 2: Calculate Nominal Strength per Bolt ($r_n$)**")
    lines.append(f"Formula: $r_n = \\min(1.2 l_c t F_u, \\; 2.4 d t F_u)$")
    lines.append(f"Upper Limit ($2.4 d t F_u$) = $2.4({d_bolt})({t_plt})({Fu}) = {max_bear_load/1000:.2f}$ kN")
    
    # Edge Calc
    rn_edge_val = 1.2 * lc_edge * t_plt * Fu
    rn_edge = min(rn_edge_val, max_bear_load)
    lines.append(f"- **Edge Bolt:** $1.2({lc_edge:.1f})({t_plt})({Fu}) = {rn_edge_val/1000:.2f}$ kN")
    lines.append(f"  $\\rightarrow r_{{n,edge}} = \\mathbf{{{rn_edge/1000:.2f} \\text{{ kN}}}}$")
    
    # Inner Calc
    rn_inner = 0
    if rows > 1:
        rn_inner_val = 1.2 * lc_inner * t_plt * Fu
        rn_inner = min(rn_inner_val, max_bear_load)
        lines.append(f"- **Inner Bolt:** $1.2({lc_inner:.1f})({t_plt})({Fu}) = {rn_inner_val/1000:.2f}$ kN")
        lines.append(f"  $\\rightarrow r_{{n,in}} = \\mathbf{{{rn_inner/1000:.2f} \\text{{ kN}}}}$")
    
    # Summation
    Rn_bearing = ((rn_edge * cols) + (rn_inner * (rows - 1) * cols)) / 1000.0
    lines.append(f"")
    lines.append(f"**Step 3: Total Nominal Strength ($R_n$)**")
    lines.append(f"$$ R_n = \\Sigma r_n = ({cols} \\times {rn_edge/1000:.2f}) + ({cols*(rows-1)} \\times {rn_inner/1000:.2f}) $$")
    lines.append(f"$$ R_n = {Rn_bearing:.2f} \\text{{ kN}} $$")
    
    lines.append(render_check(Rn_bearing, 'rupture', V_load))
    lines.append("---")
    lines.append("")

    # =================================================
    # 3. SHEAR YIELDING (AISC J4.2)
    # =================================================
    lines.append("### 3. Plate Shear Yielding")
    lines.append("*Reference: AISC Spec. Section J4.2(a)*")
    
    Ag = h_plate * t_plt
    Rn_yield = 0.60 * Fy * Ag / 1000.0
    
    lines.append(f"**Step 1: Gross Area ($A_g$)**")
    lines.append(f"$$ A_g = h \\cdot t = {h_plate} \\times {t_plt} = {Ag:.0f} \\text{{ mm}}^2 $$")
    
    lines.append(f"**Step 2: Nominal Strength ($R_n$)**")
    lines.append(f"$$ R_n = 0.60 F_y A_g $$")
    lines.append(f"$$ R_n = 0.60 ({Fy}) ({Ag:.0f}) = {Rn_yield:.2f} \\text{{ kN}} $$")
    
    lines.append(render_check(Rn_yield, 'yield', V_load))
    lines.append("---")
    lines.append("")

    # =================================================
    # 4. SHEAR RUPTURE (AISC J4.2)
    # =================================================
    lines.append("### 4. Plate Shear Rupture")
    lines.append("*Reference: AISC Spec. Section J4.2(b)*")
    
    Anv = (h_plate - (rows * d_hole)) * t_plt
    Rn_rup = 0.60 * Fu * Anv / 1000.0
    
    lines.append(f"**Step 1: Net Shear Area ($A_{{nv}}$)**")
    lines.append(f"$$ A_{{nv}} = [h - n_{{row}}(d_h)] \\cdot t $$")
    lines.append(f"$$ A_{{nv}} = [{h_plate} - {rows}({d_hole})] ({t_plt}) = {Anv:.0f} \\text{{ mm}}^2 $$")
    
    lines.append(f"**Step 2: Nominal Strength ($R_n$)**")
    lines.append(f"$$ R_n = 0.60 F_u A_{{nv}} $$")
    lines.append(f"$$ R_n = 0.60 ({Fu}) ({Anv:.0f}) = {Rn_rup:.2f} \\text{{ kN}} $$")
    
    lines.append(render_check(Rn_rup, 'rupture', V_load))
    lines.append("---")
    lines.append("")

    # =================================================
    # 5. BLOCK SHEAR (AISC J4.3)
    # =================================================
    lines.append("### 5. Block Shear Strength")
    lines.append("*Reference: AISC Spec. Section J4.3*")
    lines.append("Failure path involves shear yielding/rupture along the length and tension rupture across the width.")

    L_gv = plate['lv'] + (rows - 1) * bolts['s_v']
    Agv = L_gv * t_plt * cols
    Anv_bs = (L_gv - (rows - 0.5) * d_hole) * t_plt * cols
    Ant_bs = (plate['l_side'] - 0.5 * d_hole) * t_plt * cols
    Ubs = 1.0
    
    lines.append(f"**Step 1: Calculate Geometric Areas**")
    lines.append(f"* **Gross Shear Area ($A_{{gv}}$):** ${L_gv} \\times {t_plt} \\times {cols} = {Agv:.0f} \\text{{ mm}}^2$")
    lines.append(f"* **Net Shear Area ($A_{{nv}}$):** $({L_gv} - {rows-0.5}({d_hole})) \\times {t_plt} \\times {cols} = {Anv_bs:.0f} \\text{{ mm}}^2$")
    lines.append(f"* **Net Tension Area ($A_{{nt}}$):** $({plate['l_side']} - 0.5({d_hole})) \\times {t_plt} \\times {cols} = {Ant_bs:.0f} \\text{{ mm}}^2$")
    
    term1 = (0.6 * Fu * Anv_bs) + (Ubs * Fu * Ant_bs)
    term2 = (0.6 * Fy * Agv) + (Ubs * Fu * Ant_bs)
    Rn_bs = min(term1, term2) / 1000.0
    
    lines.append(f"")
    lines.append(f"**Step 2: Calculate Failure Modes**")
    lines.append(f"$$ R_n = \\min \\begin{{cases}} 0.6 F_u A_{{nv}} + U_{{bs}} F_u A_{{nt}} \\\\ 0.6 F_y A_{{gv}} + U_{{bs}} F_u A_{{nt}} \\end{{cases}} $$")
    
    lines.append(f"**Substitution:**")
    lines.append(f"- **Mode 1 (Shear Rupture):** $0.6({Fu})({Anv_bs:.0f}) + 1.0({Fu})({Ant_bs:.0f}) = \\mathbf{{{term1/1000:.1f} \\text{{ kN}}}}$")
    lines.append(f"- **Mode 2 (Shear Yield):** $0.6({Fy})({Agv:.0f}) + 1.0({Fu})({Ant_bs:.0f}) = \\mathbf{{{term2/1000:.1f} \\text{{ kN}}}}$")
    
    lines.append(f"$$ R_n = \\min({term1/1000:.1f}, {term2/1000:.1f}) = {Rn_bs:.2f} \\text{{ kN}} $$")
    
    lines.append(render_check(Rn_bs, 'rupture', V_load))
    lines.append("---")
    
    # =================================================
    # SUMMARY TABLE
    # =================================================
    lines.append("### 📝 Design Summary")
    lines.append(f"| Limit State | Capacity ({'ϕRn' if is_lrfd else 'Rn/Ω'}) | Demand | Ratio | Result |")
    lines.append("| :--- | :---: | :---: | :---: | :---: |")
    
    def get_row(name, Rn_val, type_mode):
        if is_lrfd:
            fac = phi_y if type_mode == 'yield' else (phi_b if type_mode == 'bolt' else phi_r)
            cap = Rn_val * fac
        else:
            om = om_y if type_mode == 'yield' else (om_b if type_mode == 'bolt' else om_r)
            cap = Rn_val / om
        
        r = V_load / cap if cap > 0 else 999
        s = "✅ PASS" if r <= 1.0 else "❌ FAIL"
        return f"| {name} | {cap:.2f} kN | {V_load:.2f} kN | {r:.2f} | {s} |"

    lines.append(get_row("Bolt Shear", Rn_shear, 'bolt'))
    lines.append(get_row("Bolt Bearing", Rn_bearing, 'rupture'))
    lines.append(get_row("Plate Yield", Rn_yield, 'yield'))
    lines.append(get_row("Plate Rupture", Rn_rup, 'rupture'))
    lines.append(get_row("Block Shear", Rn_bs, 'rupture'))
    
    lines.append("")
    all_ratios = [
        V_load/(Rn_shear*(phi_b if is_lrfd else 1/om_b)),
        V_load/(Rn_bearing*(phi_r if is_lrfd else 1/om_r)),
        V_load/(Rn_yield*(phi_y if is_lrfd else 1/om_y)),
        V_load/(Rn_rup*(phi_r if is_lrfd else 1/om_r)),
        V_load/(Rn_bs*(phi_r if is_lrfd else 1/om_r))
    ]
    max_r = max(all_ratios)
    
    lines.append(f"**Conclusion:** The connection {'✅ PASSES' if max_r <= 1.0 else '❌ FAILS'} with a maximum utilization ratio of **{max_r:.2f}**.")

    return "\n".join(lines)
