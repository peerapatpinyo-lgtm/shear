import math

def generate_report(V_load, beam, plate, bolts, is_lrfd=True, material_grade="A36", bolt_grade="A325"):
    
    # =================================================================================
    # 0. HELPER FUNCTIONS (จัด Format ให้สวยงาม)
    # =================================================================================
    def render_header(title, ref_code):
        return f"\n### {title}\n> **Ref:** AISC 360-16 Section {ref_code}\n"

    def render_math_block(symbol_lhs, formula_tex, sub_tex, result_val, unit, ratio_val=None, cap_chk=None):
        """
        สร้างบล็อกสมการ 3 บรรทัด:
        1. สูตรตัวแปร
        2. การแทนค่าตัวเลข
        3. ผลลัพธ์ตัวหนา
        """
        # Status icon
        status = ""
        if ratio_val is not None:
            pass_fail = "✅ PASS" if ratio_val <= 1.0 else "❌ FAIL"
            status = f"\n**Ratio:** ${ratio_val:.2f}$ $\\rightarrow$ {pass_fail}"

        return f"""
$$ {symbol_lhs} = {formula_tex} $$
$$ = {sub_tex} $$
$$ = \\mathbf{{{result_val:,.2f}}} \\text{{ {unit} }} $$
{status}
---
"""

    # =================================================================================
    # 1. PREPARE PARAMETERS
    # =================================================================================
    
    # --- Factors ---
    if is_lrfd:
        design_method = "LRFD"
        phi_v = 0.75; phi_y = 0.90; phi_r = 0.75; phi_w = 0.75
        factor_sym = r"\phi"
        
        # Lambda functions for display
        get_factor = lambda t: phi_v if t=='v' else (phi_y if t=='y' else (phi_r if t=='r' else phi_w))
        fmt_factor = lambda t: f"{get_factor(t)}"
    else:
        design_method = "ASD"
        om_v = 2.00; om_y = 1.50; om_r = 2.00; om_w = 2.00
        factor_sym = r"\Omega"
        
        get_factor = lambda t: 1/om_v if t=='v' else (1/om_y if t=='y' else (1/om_r if t=='r' else 1/om_w))
        fmt_factor = lambda t: f"1/{om_v if t=='v' else (om_y if t=='y' else (om_r if t=='r' else om_w))}"

    # --- Geometry & Materials ---
    d = bolts['d']
    h_hole = d + 2
    n_rows = bolts['rows']
    n_cols = bolts['cols']
    n_total = n_rows * n_cols
    s_v = bolts['s_v']
    s_h = bolts.get('s_h', 0)
    
    t_pl = plate['t']
    h_pl = plate['h']
    Fy_pl = plate['Fy']; Fu_pl = plate['Fu']
    t_web = beam['tw']; Fu_beam = beam['Fu']
    Fnv = bolts['Fnv']
    
    # =================================================================================
    # 2. CALCULATION LOGIC
    # =================================================================================

    # --- 2.1 Elastic Method Analysis ---
    if n_cols > 1: x_bar = ((n_cols - 1) * s_h) / 2
    else: x_bar = 0
    
    # Eccentricity
    e_dist = plate['e1']
    eccentricity = e_dist + x_bar
    Mu_mm = V_load * eccentricity # kN-mm
    
    # Polar Moment of Inertia (J)
    sum_r2 = 0
    crit_x, crit_y = 0, 0
    
    # Loop for J
    row_start = -((n_rows - 1) * s_v) / 2
    col_start = -x_bar
    for c in range(n_cols):
        for r in range(n_rows):
            dx = col_start + (c * s_h)
            dy = row_start + (r * s_v)
            r_sq = dx**2 + dy**2
            sum_r2 += r_sq
            if r_sq >= (crit_x**2 + crit_y**2):
                crit_x, crit_y = abs(dx), abs(dy)
    
    # Forces
    Rv_direct = V_load / n_total
    if sum_r2 > 0:
        Rv_moment = (Mu_mm * crit_x) / sum_r2
        Rh_moment = (Mu_mm * crit_y) / sum_r2
    else:
        Rv_moment, Rh_moment = 0, 0
        
    V_resultant = math.sqrt((Rv_direct + Rv_moment)**2 + Rh_moment**2)
    
    # --- 2.2 Capacity Calculations ---
    
    # 1. Bolt Shear
    Ab = (math.pi * d**2) / 4
    Rn_bolt = (Fnv * Ab) / 1000.0 # kN
    cap_bolt = Rn_bolt * get_factor('v')
    
    # 2. Bearing (Min of Plate or Web)
    Rn_bear_pl = (2.4 * d * t_pl * Fu_pl) / 1000.0
    Rn_bear_wb = (2.4 * d * t_web * Fu_beam) / 1000.0
    cap_bear_pl = Rn_bear_pl * get_factor('v')
    cap_bear_wb = Rn_bear_wb * get_factor('v')
    cap_bear = min(cap_bear_pl, cap_bear_wb)
    
    # 3. Plate Yielding
    Ag = h_pl * t_pl
    Rn_yld = (0.60 * Fy_pl * Ag) / 1000.0
    cap_yld = Rn_yld * get_factor('y')
    
    # 4. Plate Rupture
    An = (h_pl - (n_rows * h_hole)) * t_pl
    Rn_rup = (0.60 * Fu_pl * An) / 1000.0
    cap_rup = Rn_rup * get_factor('r')
    
    # 5. Block Shear
    lv = plate['lv']; l_side = plate['l_side']
    Agv = (lv + (n_rows - 1) * s_v) * t_pl
    Anv = (Agv/t_pl - (n_rows - 0.5) * h_hole) * t_pl
    Ant = (l_side - 0.5 * h_hole) * t_pl
    
    Rn_blk_1 = (0.6 * Fu_pl * Anv + 1.0 * Fu_pl * Ant) / 1000.0
    Rn_blk_2 = (0.6 * Fy_pl * Agv + 1.0 * Fu_pl * Ant) / 1000.0
    Rn_blk = min(Rn_blk_1, Rn_blk_2)
    cap_blk = Rn_blk * get_factor('r')
    
    # 6. Weld
    w_sz = plate['weld_size']
    L_weld = h_pl * 2
    Rn_weld = (0.60 * 480 * 0.707 * w_sz * L_weld) / 1000.0
    cap_weld = Rn_weld * get_factor('w')

    # =================================================================================
    # 3. GENERATE REPORT TEXT
    # =================================================================================
    md = []
    
    # --- HEADER ---
    md.append(f"# 📝 Calculation Report: {design_method}")
    md.append(f"**Design Load ($V_u$):** {V_load:.2f} kN | **Eccentricity ($e$):** {eccentricity:.1f} mm")
    md.append("---")

    # --- SECTION 1: FORCE ANALYSIS ---
    md.append(render_header("1. Bolt Group Analysis (Elastic Method)", "Manual Part 7"))
    
    md.append(f"**Geometric Properties:**")
    md.append(f"- Polar Moment of Inertia ($J = \sum r^2$): `{sum_r2:,.0f} mm²`")
    md.append(f"- Critical Bolt Coord: `({crit_x:.1f}, {crit_y:.1f})`")
    
    # Show Force Composition clearly
    md.append(f"\n**Force Components:**")
    md.append(f"1. Direct Shear ($V/n$): **{Rv_direct:.2f} kN**")
    md.append(f"2. Moment Shear ($M r / J$): Vert **{Rv_moment:.2f} kN** | Horz **{Rh_moment:.2f} kN**")
    
    # Resultant Formula
    res_eq = r"\sqrt{(F_{vy} + F_{my})^2 + F_{mx}^2}"
    res_sub = f"\\sqrt{{({Rv_direct:.1f} + {Rv_moment:.1f})^2 + {Rh_moment:.1f}^2}}"
    md.append(render_math_block("V_{bolt}", res_eq, res_sub, V_resultant, "kN"))

    # --- SECTION 2: CHECKS ---
    
    # 2.1 Bolt Shear
    md.append(render_header("2. Bolt Shear Strength", "J3.6"))
    f_str = r"\phi F_{nv} A_b" if is_lrfd else r"\frac{F_{nv} A_b}{\Omega}"
    sub_str = f"{fmt_factor('v')} \\times {Fnv} \\times {Ab:.1f}/1000"
    md.append(render_math_block(f"{factor_sym}R_n", f_str, sub_str, cap_bolt, "kN", V_resultant/cap_bolt))

    # 2.2 Bolt Bearing
    md.append(render_header("3. Bolt Bearing Strength", "J3.10"))
    md.append(f"Checking both Plate (t={t_pl}) and Beam Web (t={t_web}). Using Min:")
    
    # Plate Calc
    f_bear = r"\phi (2.4 d t F_u)" if is_lrfd else r"\frac{2.4 d t F_u}{\Omega}"
    sub_bear_pl = f"{fmt_factor('v')} \\times 2.4 \\times {d} \\times {t_pl} \\times {Fu_pl}/1000"
    
    md.append(f"**Case A: Plate Bearing**")
    md.append(f"$$ {factor_sym}R_n = {sub_bear_pl} = \\mathbf{{{cap_bear_pl:.2f}}} \\text{{ kN}} $$")
    
    md.append(f"**Case B: Web Bearing**")
    md.append(f"$$ {factor_sym}R_n = \\mathbf{{{cap_bear_wb:.2f}}} \\text{{ kN}} $$")
    
    md.append(f"\n**Governing Capacity:** **{cap_bear:.2f} kN**")
    ratio_bear = V_resultant / cap_bear
    status_bear = "✅ PASS" if ratio_bear <= 1.0 else "❌ FAIL"
    md.append(f"**Ratio:** ${ratio_bear:.2f}$ $\\rightarrow$ {status_bear}")
    md.append("---")

    # 2.3 Plate Yielding
    md.append(render_header("4. Plate Shear Yielding", "J4.2"))
    f_yld = r"\phi (0.6 F_y A_g)" if is_lrfd else r"\frac{0.6 F_y A_g}{\Omega}"
    sub_yld = f"{fmt_factor('y')} \\times 0.6 \\times {Fy_pl} \\times {Ag:.0f}/1000"
    md.append(render_math_block(f"{factor_sym}R_n", f_yld, sub_yld, cap_yld, "kN", V_load/cap_yld))

    # 2.4 Plate Rupture
    md.append(render_header("5. Plate Shear Rupture", "J4.3"))
    f_rup = r"\phi (0.6 F_u A_{nv})" if is_lrfd else r"\frac{0.6 F_u A_{nv}}{\Omega}"
    sub_rup = f"{fmt_factor('r')} \\times 0.6 \\times {Fu_pl} \\times {An:.0f}/1000"
    md.append(render_math_block(f"{factor_sym}R_n", f_rup, sub_rup, cap_rup, "kN", V_load/cap_rup))

    # 2.5 Block Shear
    md.append(render_header("6. Block Shear", "J4.3"))
    md.append(f"Areas: $A_{{nv}}={Anv:.0f}, A_{{nt}}={Ant:.0f}, A_{{gv}}={Agv:.0f}$ mm²")
    f_blk = r"\phi \min[0.6F_u A_{nv} + U_{bs}F_u A_{nt}, \quad 0.6F_y A_{gv} + U_{bs}F_u A_{nt}]" if is_lrfd else r"\min[...] / \Omega"
    sub_blk = f"{fmt_factor('r')} \\times \\min[{Rn_blk_1:.1f}, {Rn_blk_2:.1f}]"
    md.append(render_math_block(f"{factor_sym}R_n", f_blk, sub_blk, cap_blk, "kN", V_load/cap_blk))
    
    # 2.6 Weld
    md.append(render_header("7. Weld Strength", "J2.4"))
    f_weld = r"\phi (0.6 F_{exx} \cdot 0.707w \cdot L)" if is_lrfd else r"\frac{0.6 F_{exx} \cdot 0.707w \cdot L}{\Omega}"
    sub_weld = f"{fmt_factor('w')} \\times 0.4242 \\times 480 \\times {w_sz} \\times {L_weld}/1000"
    md.append(render_math_block(f"{factor_sym}R_n", f_weld, sub_weld, cap_weld, "kN", V_load/cap_weld))

    return "\n".join(md)
