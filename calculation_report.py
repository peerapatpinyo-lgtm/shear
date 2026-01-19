import math

def generate_report(V_load, T_load, beam, plate, bolts, cope, is_lrfd, material_grade, bolt_grade):
    """
    Generate Professional Structural Calculation Report (Complete with Weld Check)
    Standard: AISC 360-16
    """
    
    # --- 1. DESIGN PARAMETERS & CONSTANTS ---
    method = "LRFD" if is_lrfd else "ASD"
    
    if is_lrfd:
        # Factors
        phi_y = 0.90   # Yielding
        phi_r = 0.75   # Rupture / Bearing / Block Shear
        phi_b = 0.75   # Bolt Shear
        phi_w = 0.75   # Weld Strength (AISC J2.4)
        
        cap_label = "Design Strength (\\phi R_n)"
        load_label = "Factored Load (V_u)"
    else:
        # Factors
        om_y = 1.67
        om_r = 2.00
        om_b = 2.00
        om_w = 2.00    # Weld Strength (AISC J2.4)
        
        cap_label = "Allowable Strength (R_n/\\Omega)"
        load_label = "Service Load (V_a)"

    # --- 2. GEOMETRIC PROPERTIES ---
    d_bolt = bolts['d']
    d_hole = d_bolt + 2.0 
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
            # Select Phi Factor
            if limit_state_type == 'yield': factor = phi_y
            elif limit_state_type == 'weld': factor = phi_w
            elif limit_state_type == 'bolt': factor = phi_b
            else: factor = phi_r # rupture, bearing, block shear
            
            capacity = Rn_kN * factor
            eq_str = f"\\phi R_n = {factor:.2f} ( {Rn_kN:.2f} )"
        else:
            # Select Omega Factor
            if limit_state_type == 'yield': omega = om_y
            elif limit_state_type == 'weld': omega = om_w
            elif limit_state_type == 'bolt': omega = om_b
            else: omega = om_r
            
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
    if plate.get('weld_size', 0) > 0:
        lines.append(f"- **Weld:** Fillet Weld Size $w = {plate['weld_size']}$ mm (E70XX)")
    lines.append("---")
    lines.append("")

    # =================================================
    # 1. BOLT SHEAR
    # =================================================
    lines.append("### 1. Bolt Shear Strength")
    lines.append("*Reference: AISC Spec. Section J3.6*")
    
    Ab = math.pi * d_bolt**2 / 4
    Fnv = bolts['Fnv']
    Rn_shear = (Fnv * Ab * n_bolts) / 1000.0
    
    lines.append(f"**Step 1: Determine Nominal Strength ($R_n$)**")
    lines.append(f"$$ R_n = F_{{nv}} A_b N_b $$")
    lines.append(f"Substitution:")
    lines.append(f"$$ R_n = {Fnv} \\times {Ab:.1f} \\times {n_bolts} = {Rn_shear*1000:,.0f} \\text{{ N}} $$")
    lines.append(f"$$ R_n = {Rn_shear:.2f} \\text{{ kN}} $$")
    
    lines.append(render_check(Rn_shear, 'bolt', V_load))
    lines.append("---")
    lines.append("")

    # =================================================
    # 2. BOLT BEARING
    # =================================================
    lines.append("### 2. Bolt Bearing & Tearout")
    lines.append("*Reference: AISC Spec. Section J3.10*")
    
    lc_edge = plate['lv'] - (d_hole / 2.0)
    lc_inner = bolts['s_v'] - d_hole
    max_bear_load = 2.4 * d_bolt * t_plt * Fu
    
    # Edge Calc
    rn_edge_val = 1.2 * lc_edge * t_plt * Fu
    rn_edge = min(rn_edge_val, max_bear_load)
    
    # Inner Calc
    rn_inner = 0
    if rows > 1:
        rn_inner_val = 1.2 * lc_inner * t_plt * Fu
        rn_inner = min(rn_inner_val, max_bear_load)
    
    # Summation
    Rn_bearing = ((rn_edge * cols) + (rn_inner * (rows - 1) * cols)) / 1000.0
    
    lines.append(f"**Step 1: Clear Distance & Nominal Strength**")
    lines.append(f"- Edge ($l_c={lc_edge:.1f}$): $r_n = \\min(1.2 l_c t F_u, 2.4 d t F_u) = {rn_edge/1000:.2f}$ kN")
    if rows > 1:
        lines.append(f"- Inner ($l_c={lc_inner:.1f}$): $r_n = \\min(1.2 l_c t F_u, 2.4 d t F_u) = {rn_inner/1000:.2f}$ kN")
    
    lines.append(f"")
    lines.append(f"**Step 2: Total Nominal Strength ($R_n$)**")
    lines.append(f"$$ R_n = \\Sigma r_n = {Rn_bearing:.2f} \\text{{ kN}} $$")
    
    lines.append(render_check(Rn_bearing, 'rupture', V_load))
    lines.append("---")
    lines.append("")

    # =================================================
    # 3. PLATE YIELDING
    # =================================================
    lines.append("### 3. Plate Shear Yielding")
    lines.append("*Reference: AISC Spec. Section J4.2(a)*")
    
    Ag = h_plate * t_plt
    Rn_yield = 0.60 * Fy * Ag / 1000.0
    
    lines.append(f"**Step 1: Nominal Strength ($R_n$)**")
    lines.append(f"$$ R_n = 0.60 F_y A_g $$")
    lines.append(f"$$ R_n = 0.60 ({Fy}) ({h_plate}\\times{t_plt}) = {Rn_yield:.2f} \\text{{ kN}} $$")
    
    lines.append(render_check(Rn_yield, 'yield', V_load))
    lines.append("---")
    lines.append("")

    # =================================================
    # 4. PLATE RUPTURE
    # =================================================
    lines.append("### 4. Plate Shear Rupture")
    lines.append("*Reference: AISC Spec. Section J4.2(b)*")
    
    Anv = (h_plate - (rows * d_hole)) * t_plt
    Rn_rup = 0.60 * Fu * Anv / 1000.0
    
    lines.append(f"**Step 1: Nominal Strength ($R_n$)**")
    lines.append(f"$$ R_n = 0.60 F_u A_{{nv}} $$")
    lines.append(f"$$ R_n = 0.60 ({Fu}) ({Anv:.0f}) = {Rn_rup:.2f} \\text{{ kN}} $$")
    
    lines.append(render_check(Rn_rup, 'rupture', V_load))
    lines.append("---")
    lines.append("")

    # =================================================
    # 5. BLOCK SHEAR
    # =================================================
    lines.append("### 5. Block Shear Strength")
    lines.append("*Reference: AISC Spec. Section J4.3*")

    L_gv = plate['lv'] + (rows - 1) * bolts['s_v']
    Agv = L_gv * t_plt * cols
    Anv_bs = (L_gv - (rows - 0.5) * d_hole) * t_plt * cols
    Ant_bs = (plate['l_side'] - 0.5 * d_hole) * t_plt * cols
    Ubs = 1.0
    
    term1 = (0.6 * Fu * Anv_bs) + (Ubs * Fu * Ant_bs)
    term2 = (0.6 * Fy * Agv) + (Ubs * Fu * Ant_bs)
    Rn_bs = min(term1, term2) / 1000.0
    
    lines.append(f"**Step 1: Geometric Areas**")
    lines.append(f"- $A_{{gv}}={Agv:.0f}, A_{{nv}}={Anv_bs:.0f}, A_{{nt}}={Ant_bs:.0f}$ $\\text{{mm}}^2$")
    
    lines.append(f"**Step 2: Nominal Strength ($R_n$)**")
    lines.append(f"$$ R_n = \\min [ 0.6 F_u A_{{nv}} + U_{{bs}} F_u A_{{nt}}, \\; 0.6 F_y A_{{gv}} + U_{{bs}} F_u A_{{nt}} ] $$")
    lines.append(f"$$ R_n = \\min [ {term1/1000:.1f}, {term2/1000:.1f} ] = {Rn_bs:.2f} \\text{{ kN}} $$")
    
    lines.append(render_check(Rn_bs, 'rupture', V_load))
    lines.append("---")
    lines.append("")
    
    # =================================================
    # 6. WELD STRENGTH (AISC J2.4) -- NEW!
    # =================================================
    Rn_weld = 0
    if plate.get('weld_size', 0) > 0:
        lines.append("### 6. Weld Strength")
        lines.append("*Reference: AISC Spec. Section J2.4*")
        
        w_weld = plate['weld_size']
        L_weld = h_plate * 2 # Fillet weld on both sides
        Fexx = 480 # E70XX
        
        # Nominal Strength (N)
        # Rn = 0.60 * Fexx * (0.707 * w) * L
        Rn_weld = (0.60 * Fexx * (0.707 * w_weld) * L_weld) / 1000.0
        
        lines.append(f"**Step 1: Parameters**")
        lines.append(f"- Fillet Weld Size ($w$): {w_weld} mm")
        lines.append(f"- Electrode Strength ($F_{{EXX}}$): {Fexx} MPa (E70XX)")
        lines.append(f"- Effective Length ($L$): $2 \\times {h_plate} = {L_weld:.0f}$ mm (Double sides)")
        
        lines.append(f"")
        lines.append(f"**Step 2: Nominal Strength ($R_n$)**")
        lines.append(f"$$ R_n = 0.60 F_{{EXX}} (0.707 w) L $$")
        lines.append(f"$$ R_n = 0.60 ({Fexx}) (0.707 \\times {w_weld}) ({L_weld:.0f}) $$")
        lines.append(f"$$ R_n = {Rn_weld:.2f} \\text{{ kN}} $$")
        
        lines.append(render_check(Rn_weld, 'weld', V_load))
        lines.append("---")
        lines.append("")

    # =================================================
    # SUMMARY TABLE
    # =================================================
    lines.append("### 📝 Design Summary")
    lines.append(f"| Limit State | Capacity ({'ϕRn' if is_lrfd else 'Rn/Ω'}) | Demand | Ratio | Result |")
    lines.append("| :--- | :---: | :---: | :---: | :---: |")
    
    def get_row(name, Rn_val, type_mode):
        if Rn_val == 0: return None
        
        if is_lrfd:
            fac = phi_y if type_mode == 'yield' else (phi_b if type_mode == 'bolt' else (phi_w if type_mode == 'weld' else phi_r))
            cap = Rn_val * fac
        else:
            om = om_y if type_mode == 'yield' else (om_b if type_mode == 'bolt' else (om_w if type_mode == 'weld' else om_r))
            cap = Rn_val / om
        
        r = V_load / cap if cap > 0 else 999
        s = "✅ PASS" if r <= 1.0 else "❌ FAIL"
        return f"| {name} | {cap:.2f} kN | {V_load:.2f} kN | {r:.2f} | {s} |"

    rows_to_add = [
        ("Bolt Shear", Rn_shear, 'bolt'),
        ("Bolt Bearing", Rn_bearing, 'rupture'),
        ("Plate Yield", Rn_yield, 'yield'),
        ("Plate Rupture", Rn_rup, 'rupture'),
        ("Block Shear", Rn_bs, 'rupture'),
    ]
    if Rn_weld > 0:
        rows_to_add.append(("Weld Strength", Rn_weld, 'weld'))

    ratios = []
    for r_name, r_val, r_type in rows_to_add:
        line_str = get_row(r_name, r_val, r_type)
        if line_str:
            lines.append(line_str)
            # Recalculate ratio for max check
            if is_lrfd:
                fac = phi_y if r_type == 'yield' else (phi_b if r_type == 'bolt' else (phi_w if r_type == 'weld' else phi_r))
                cap = r_val * fac
            else:
                om = om_y if r_type == 'yield' else (om_b if r_type == 'bolt' else (om_w if r_type == 'weld' else om_r))
                cap = r_val / om
            ratios.append(V_load/cap)

    max_r = max(ratios) if ratios else 0
    lines.append("")
    lines.append(f"**Conclusion:** The connection {'✅ PASSES' if max_r <= 1.0 else '❌ FAILS'} with a maximum utilization ratio of **{max_r:.2f}**.")

    return "\n".join(lines)
