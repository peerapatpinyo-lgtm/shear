import math

def generate_report(V_load, T_load, beam, plate, bolts, cope, is_lrfd, material_grade, bolt_grade):
    """
    Generate Calculation Report - MAXIMUM SPACING EDITION
    Standard: AISC 360-16
    Layout: Aggressive line breaks for readability.
    """
    
    # --- 1. SETUP CONSTANTS ---
    method = "LRFD" if is_lrfd else "ASD"
    
    if is_lrfd:
        phi_y, phi_r, phi_b, phi_w = 0.90, 0.75, 0.75, 0.75
        cap_lab = "Design Strength (\\phi R_n)"
    else:
        om_y, om_r, om_b, om_w = 1.67, 2.00, 2.00, 2.00
        cap_lab = "Allowable Strength (R_n/\\Omega)"

    # --- 2. PRE-CALC GEOMETRY ---
    d_bolt = bolts['d']
    d_hole = d_bolt + 2.0 
    rows = bolts['rows']
    cols = bolts['cols']
    n_bolts = rows * cols
    
    t_plt = plate['t']
    Fy = plate['Fy']
    Fu = plate['Fu']
    h_plate = plate['h']
    
    # --- HELPER: CHECK BLOCK ---
    def render_check(Rn_kN, mode, demand):
        if is_lrfd:
            fac = phi_y if mode == 'yield' else (phi_b if mode == 'bolt' else (phi_w if mode == 'weld' else phi_r))
            cap = Rn_kN * fac
            eq = f"\\phi R_n = {fac:.2f} \\times {Rn_kN:.2f}"
        else:
            om = om_y if mode == 'yield' else (om_b if mode == 'bolt' else (om_w if mode == 'weld' else om_r))
            cap = Rn_kN / om
            eq = f"R_n / \\Omega = {Rn_kN:.2f} / {om:.2f}"
            
        ratio = demand / cap if cap > 0 else 999
        res = "✅ OK" if ratio <= 1.0 else "❌ FAIL"
        
        blk = []
        blk.append(f"> **Check:**")
        blk.append(f"> $$ {cap_lab} = {eq} = \\mathbf{{{cap:.2f} \\text{{ kN}}}} $$")
        blk.append(">") # Empty line in quote
        blk.append(f"> $$ \\text{{Ratio}} = \\frac{{{demand:.2f}}}{{{cap:.2f}}} = \\mathbf{{{ratio:.2f}}} \\quad [{res}] $$")
        return "\n".join(blk)

    lines = []
    
    # =================================================
    # HEADER
    # =================================================
    lines.append(f"# 🏗️ CONNECTION REPORT ({method})")
    lines.append("---")
    lines.append(f"**Input Data:**")
    lines.append(f"")
    lines.append(f"- **Load ($V_u$):** {V_load:.2f} kN")
    lines.append(f"")
    lines.append(f"- **Plate:** {material_grade} ($t={t_plt}$ mm)")
    lines.append(f"")
    lines.append(f"- **Bolts:** {n_bolts} x M{d_bolt} (Grade {bolt_grade})")
    lines.append("---")
    lines.append("")

    # =================================================
    # 1. BOLT SHEAR
    # =================================================
    lines.append("### 1. Bolt Shear Strength")
    lines.append("*Ref: AISC J3.6*")
    lines.append("")
    
    Ab = math.pi * d_bolt**2 / 4
    Fnv = bolts['Fnv']
    Rn_shear = (Fnv * Ab * n_bolts) / 1000.0
    
    lines.append("**Formula:**")
    lines.append("$$ R_n = F_{nv} \\times A_b \\times N_{bolts} $$")
    lines.append("")
    
    lines.append("**Substitution:**")
    lines.append(f"$$ R_n = {Fnv} \\times {Ab:.1f} \\times {n_bolts} $$")
    lines.append("")
    
    lines.append("**Result:**")
    lines.append(f"$$ R_n = {Rn_shear:.2f} \\text{{ kN}} $$")
    lines.append("")
    
    lines.append(render_check(Rn_shear, 'bolt', V_load))
    lines.append("---")
    lines.append("")

    # =================================================
    # 2. BOLT BEARING
    # =================================================
    lines.append("### 2. Bolt Bearing")
    lines.append("*Ref: AISC J3.10*")
    lines.append("")

    lc_edge = plate['lv'] - (d_hole / 2.0)
    lc_inner = bolts['s_v'] - d_hole
    max_bear = 2.4 * d_bolt * t_plt * Fu
    
    # --- Edge ---
    lines.append(f"**(a) Edge Bolts ($l_c = {lc_edge:.1f}$ mm):**")
    lines.append("")
    lines.append("$$ r_n = 1.2 l_c t F_u $$")
    lines.append("")
    
    rn_edge_val = 1.2 * lc_edge * t_plt * Fu
    lines.append(f"$$ = 1.2 ({lc_edge:.1f}) ({t_plt}) ({Fu}) $$")
    lines.append("")
    lines.append(f"$$ = {rn_edge_val/1000:.2f} \\text{{ kN}} $$")
    lines.append("")
    
    rn_edge = min(rn_edge_val, max_bear)
    lines.append(f"Limited to $2.4 d t F_u = {max_bear/1000:.2f}$ kN")
    lines.append(f"$\\rightarrow \\mathbf{{r_{{n,edge}} = {rn_edge/1000:.2f} \\text{{ kN}}}}$")
    lines.append("")
    
    # --- Inner ---
    rn_inner = 0
    if rows > 1:
        lines.append(f"**(b) Inner Bolts ($l_c = {lc_inner:.1f}$ mm):**")
        lines.append("")
        lines.append("$$ r_n = 1.2 l_c t F_u $$")
        lines.append("")
        
        rn_inner_val = 1.2 * lc_inner * t_plt * Fu
        lines.append(f"$$ = 1.2 ({lc_inner:.1f}) ({t_plt}) ({Fu}) $$")
        lines.append("")
        lines.append(f"$$ = {rn_inner_val/1000:.2f} \\text{{ kN}} $$")
        lines.append("")
        
        rn_inner = min(rn_inner_val, max_bear)
        lines.append(f"Limited to $2.4 d t F_u = {max_bear/1000:.2f}$ kN")
        lines.append(f"$\\rightarrow \\mathbf{{r_{{n,in}} = {rn_inner/1000:.2f} \\text{{ kN}}}}$")
        lines.append("")

    # --- Total ---
    Rn_bearing = ((rn_edge * cols) + (rn_inner * (rows - 1) * cols)) / 1000.0
    lines.append("**Total Nominal Strength:**")
    lines.append("")
    lines.append(f"$$ R_n = \\Sigma r_n = {Rn_bearing:.2f} \\text{{ kN}} $$")
    lines.append("")
    
    lines.append(render_check(Rn_bearing, 'rupture', V_load))
    lines.append("---")
    lines.append("")

    # =================================================
    # 3. YIELDING
    # =================================================
    lines.append("### 3. Plate Shear Yielding")
    lines.append("*Ref: AISC J4.2(a)*")
    lines.append("")
    
    Ag = h_plate * t_plt
    Rn_yield = 0.60 * Fy * Ag / 1000.0
    
    lines.append("**Formula:**")
    lines.append("$$ R_n = 0.60 F_y A_g $$")
    lines.append("")
    
    lines.append("**Substitution:**")
    lines.append(f"$$ R_n = 0.60 ({Fy}) ({Ag:.0f}) $$")
    lines.append("")
    
    lines.append("**Result:**")
    lines.append(f"$$ R_n = {Rn_yield:.2f} \\text{{ kN}} $$")
    lines.append("")
    
    lines.append(render_check(Rn_yield, 'yield', V_load))
    lines.append("---")
    lines.append("")

    # =================================================
    # 4. RUPTURE
    # =================================================
    lines.append("### 4. Plate Shear Rupture")
    lines.append("*Ref: AISC J4.2(b)*")
    lines.append("")
    
    Anv = (h_plate - (rows * d_hole)) * t_plt
    Rn_rup = 0.60 * Fu * Anv / 1000.0
    
    lines.append("**Formula:**")
    lines.append("$$ R_n = 0.60 F_u A_{nv} $$")
    lines.append("")
    
    lines.append("**Substitution:**")
    lines.append(f"$$ R_n = 0.60 ({Fu}) ({Anv:.0f}) $$")
    lines.append("")
    
    lines.append("**Result:**")
    lines.append(f"$$ R_n = {Rn_rup:.2f} \\text{{ kN}} $$")
    lines.append("")
    
    lines.append(render_check(Rn_rup, 'rupture', V_load))
    lines.append("---")
    lines.append("")

    # =================================================
    # 5. BLOCK SHEAR
    # =================================================
    lines.append("### 5. Block Shear")
    lines.append("*Ref: AISC J4.3*")
    lines.append("")

    # Geometry
    L_gv = plate['lv'] + (rows - 1) * bolts['s_v']
    Agv = L_gv * t_plt * cols
    Anv_bs = (L_gv - (rows - 0.5) * d_hole) * t_plt * cols
    Ant_bs = (plate['l_side'] - 0.5 * d_hole) * t_plt * cols
    
    lines.append("**Areas:**")
    lines.append(f"- Shear Gross ($A_{{gv}}$): {Agv:.0f} mm²")
    lines.append(f"- Shear Net ($A_{{nv}}$): {Anv_bs:.0f} mm²")
    lines.append(f"- Tension Net ($A_{{nt}}$): {Ant_bs:.0f} mm²")
    lines.append("")
    
    term1 = (0.6 * Fu * Anv_bs) + (1.0 * Fu * Ant_bs)
    term2 = (0.6 * Fy * Agv) + (1.0 * Fu * Ant_bs)
    Rn_bs = min(term1, term2) / 1000.0
    
    lines.append("**Term 1 (Rupture):**")
    lines.append("$$ 0.6 F_u A_{nv} + U_{bs} F_u A_{nt} $$")
    lines.append("")
    lines.append(f"$$ = 0.6({Fu})({Anv_bs:.0f}) + 1.0({Fu})({Ant_bs:.0f}) $$")
    lines.append("")
    lines.append(f"$$ = {term1/1000:.1f} \\text{{ kN}} $$")
    lines.append("")
    
    lines.append("**Term 2 (Yield):**")
    lines.append("$$ 0.6 F_y A_{gv} + U_{bs} F_u A_{nt} $$")
    lines.append("")
    lines.append(f"$$ = 0.6({Fy})({Agv:.0f}) + 1.0({Fu})({Ant_bs:.0f}) $$")
    lines.append("")
    lines.append(f"$$ = {term2/1000:.1f} \\text{{ kN}} $$")
    lines.append("")
    
    lines.append("**Governing Value:**")
    lines.append(f"$$ R_n = \\min({term1/1000:.1f}, {term2/1000:.1f}) $$")
    lines.append("")
    lines.append(f"$$ = \\mathbf{{{Rn_bs:.2f} \\text{{ kN}}}} $$")
    lines.append("")
    
    lines.append(render_check(Rn_bs, 'rupture', V_load))
    lines.append("---")
    lines.append("")

    # =================================================
    # 6. WELD (IF ANY)
    # =================================================
    Rn_weld = 0
    if plate.get('weld_size', 0) > 0:
        lines.append("### 6. Weld Strength")
        lines.append("*Ref: AISC J2.4*")
        lines.append("")
        
        w = plate['weld_size']
        L = h_plate * 2
        Fexx = 480
        Rn_weld = (0.6 * Fexx * 0.707 * w * L) / 1000.0
        
        lines.append("**Formula:**")
        lines.append("$$ R_n = 0.60 F_{EXX} (0.707 w) L $$")
        lines.append("")
        
        lines.append("**Substitution:**")
        lines.append(f"$$ R_n = 0.60 ({Fexx}) (0.707 \\times {w}) ({L}) $$")
        lines.append("")
        
        lines.append("**Result:**")
        lines.append(f"$$ R_n = {Rn_weld:.2f} \\text{{ kN}} $$")
        lines.append("")
        
        lines.append(render_check(Rn_weld, 'weld', V_load))
        lines.append("---")
        lines.append("")

    # =================================================
    # SUMMARY
    # =================================================
    lines.append("### 📝 Conclusion")
    lines.append("")
    
    ratios = []
    
    def add_sum(name, Rn, mode):
        if Rn == 0: return
        if is_lrfd:
            fac = phi_y if mode == 'yield' else (phi_b if mode == 'bolt' else (phi_w if mode == 'weld' else phi_r))
            cap = Rn * fac
        else:
            om = om_y if mode == 'yield' else (om_b if mode == 'bolt' else (om_w if mode == 'weld' else om_r))
            cap = Rn / om
        
        r = V_load / cap
        ratios.append(r)
        lines.append(f"- **{name}:** Ratio = {r:.2f} ({'✅' if r<=1 else '❌'})")
        lines.append("") # Empty line between list items

    add_sum("Bolt Shear", Rn_shear, 'bolt')
    add_sum("Bolt Bearing", Rn_bearing, 'rupture')
    add_sum("Plate Yield", Rn_yield, 'yield')
    add_sum("Plate Rupture", Rn_rup, 'rupture')
    add_sum("Block Shear", Rn_bs, 'rupture')
    if Rn_weld > 0:
        add_sum("Weld Strength", Rn_weld, 'weld')

    lines.append("---")
    max_r = max(ratios) if ratios else 0
    res_txt = "PASSED" if max_r <= 1.0 else "FAILED"
    lines.append(f"## Overall Status: {res_txt} (Max Ratio: {max_r:.2f})")

    return "\n".join(lines)
