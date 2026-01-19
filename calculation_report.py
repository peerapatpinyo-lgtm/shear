# calculation_report.py
import math

def generate_report(V_load, beam, plate, bolts, is_lrfd=True, material_grade="A36", bolt_grade="A325"):
    
    # =================================================================================
    # 🎨 HELPER: FORMATTING ENGINE (Fix LaTeX Escaping)
    # =================================================================================
    def header(title):
        return f"\n### {title}\n"

    def sub_header(title, ref=""):
        ref_text = f" *(Ref: AISC 360-16, {ref})*" if ref else ""
        return f"\n#### {title}{ref_text}\n"

    def calc_block(symbol, description, formula_tex, sub_tex, result, unit):
        """
        Render LaTeX using explicit double backslashes to prevent Python string escaping issues.
        We use standard '$$' blocks with 'aligned' environment.
        """
        # หมายเหตุ: ใน Python f-string:
        # \\  -> กลายเป็น \ ใน LaTeX (สำหรับคำสั่งเช่น \phi)
        # \\\\ -> กลายเป็น \\ ใน LaTeX (สำหรับการขึ้นบรรทัดใหม่)
        
        latex_str = f"""
$$
\\begin{{aligned}}
{symbol} &= {formula_tex} \\\\
&= {sub_tex} \\\\
&= \\mathbf{{{result:,.2f}}} \\text{{ {unit} }}
\\end{{aligned}}
$$
"""
        return f"**{description}**\n{latex_str}\n"

    def ratio_bar(demand, capacity, label="Ratio"):
        if capacity == 0:
            ratio = 999
        else:
            ratio = demand / capacity
            
        color = "#15803d" if ratio <= 1.0 else "#b91c1c" # Green / Red
        icon = "✅ PASS" if ratio <= 1.0 else "❌ FAIL"
        
        # ใช้ HTML progress bar ง่ายๆ เพื่อความสวยงามและอ่านง่าย
        return f"""
> **Check {label}:** ${demand:.2f} / {capacity:.2f} = \\mathbf{{{ratio:.2f}}}$ &nbsp; <span style='color:{color}; font-weight:bold'>[{icon}]</span>
"""

    # =================================================================================
    # 1. SETUP PARAMETERS & FACTORS
    # =================================================================================
    
    if is_lrfd:
        method_name = "LRFD (Limit State Design)"
        f_v = 0.75; f_y = 0.90; f_r = 0.75; f_w = 0.75
        
        # LaTeX Symbols (Must escape backslashes!)
        phi_sym = r"\phi"
        kv_sym = r"\phi R_n"
        
        get_f = lambda t: f_v if t=='v' else (f_y if t=='y' else (f_r if t=='r' else f_w))
        fmt_f = lambda t: f"{get_f(t)}"
    else:
        method_name = "ASD (Allowable Strength Design)"
        om_v = 2.00; om_y = 1.50; om_r = 2.00; om_w = 2.00
        
        phi_sym = r"\Omega"
        kv_sym = r"R_n / \Omega"
        
        get_f = lambda t: 1.0/om_v if t=='v' else (1.0/om_y if t=='y' else (1.0/om_r if t=='r' else 1.0/om_w))
        fmt_f = lambda t: f"1/{om_v if t=='v' else (om_y if t=='y' else (om_r if t=='r' else om_w))}"

    # Extract Data
    d = bolts['d']
    h_hole = d + 2
    n_rows = bolts['rows']
    n_cols = bolts['cols']
    n_total = n_rows * n_cols
    s_v = bolts['s_v']
    s_h = bolts.get('s_h', 0)
    
    t_pl = plate['t']; h_pl = plate['h']
    Fy_pl = plate['Fy']; Fu_pl = plate['Fu']
    t_web = beam['tw']; Fu_beam = beam['Fu']
    Fnv = bolts['Fnv']
    w_sz = plate['weld_size']

    md = [] 

    # =================================================================================
    # 2. REPORT HEADER
    # =================================================================================
    md.append(f"# 📐 CALCULATION REPORT")
    md.append(f"**Design Method:** {method_name} | **Standard:** AISC 360-16")
    md.append("---")
    
    col1 = f"""
**LOADS:**
- Shear Load ($V_u$): **{V_load:.2f} kN**

**MEMBERS:**
- Plate: {t_pl} mm thick ($F_y={Fy_pl}, F_u={Fu_pl}$)
- Beam Web: {t_web} mm thick ($F_u={Fu_beam}$)
    """
    col2 = f"""
**BOLT GROUP:**
- Size: M{d} ({bolt_grade})
- Arr.: {n_rows} Rows x {n_cols} Cols
- Pitch: {s_v} mm
    """
    md.append(col1 + "\n\n" + col2)
    md.append("---")

    # =================================================================================
    # 3. ANALYSIS: BOLT GROUP (ELASTIC METHOD)
    # =================================================================================
    md.append(header("1. Bolt Group Analysis (Elastic Method)"))
    
    # 3.1 Properties
    if n_cols > 1: x_bar = ((n_cols - 1) * s_h) / 2
    else: x_bar = 0
    
    e_dist = plate['e1']
    eccentricity = e_dist + x_bar
    Mu_mm = V_load * eccentricity
    
    # Calculate J
    sum_r2 = 0
    crit_x, crit_y = 0, 0
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

    md.append(sub_header("Geometric Properties"))
    
    # Note: Use \\sum for summation symbol in LaTeX within Python string
    md.append(calc_block("e", "Eccentricity", "e_{dist} + x_{bar}", f"{e_dist} + {x_bar}", eccentricity, "mm"))
    md.append(calc_block("J", "Polar Moment of Inertia", "\\sum (x^2 + y^2)", f"{sum_r2:,.0f}", sum_r2, "mm^2"))

    # 3.2 Force Demand
    Rv_direct = V_load / n_total
    if sum_r2 > 0:
        Rv_moment = (Mu_mm * crit_x) / sum_r2
        Rh_moment = (Mu_mm * crit_y) / sum_r2
    else:
        Rv_moment, Rh_moment = 0, 0
    
    V_res = math.sqrt((Rv_direct + Rv_moment)**2 + Rh_moment**2)

    md.append(sub_header("Force Demand on Critical Bolt"))
    md.append(f"- Critical Bolt Position: $(x,y) = ({crit_x:.1f}, {crit_y:.1f})$ mm")
    
    # Component Forces (Manual LaTeX construction for clarity)
    md.append(f"**Component Forces:**")
    
    # Horizontal
    md.append(f"$$ R_{{vx}} = \\frac{{M \\cdot y}}{{J}} = \\frac{{{Mu_mm:.0f} \\cdot {crit_y:.1f}}}{{{sum_r2:.0f}}} = \\mathbf{{{Rh_moment:.2f}}} \\text{{ kN}} $$")
    
    # Vertical
    md.append(f"$$ R_{{vy}} = \\frac{{V}}{{n}} + \\frac{{M \\cdot x}}{{J}} = {Rv_direct:.2f} + {Rv_moment:.2f} = \\mathbf{{{(Rv_direct+Rv_moment):.2f}}} \\text{{ kN}} $$")

    # Resultant
    md.append(calc_block("V_{r}", "Resultant Shear Force", "\\sqrt{R_{vx}^2 + R_{vy}^2}", 
                         f"\\sqrt{{{Rh_moment:.2f}^2 + {(Rv_direct+Rv_moment):.2f}^2}}", V_res, "kN"))

    # =================================================================================
    # 4. CAPACITY CHECKS
    # =================================================================================
    md.append("---")
    md.append(header("2. Capacity Checks"))

    # --- 4.1 Bolt Shear ---
    md.append(sub_header("2.1 Bolt Shear Strength", "J3.6"))
    Ab = (math.pi * d**2) / 4
    Rn_bolt = (Fnv * Ab) / 1000.0
    cap_bolt = Rn_bolt * get_f('v')
    
    eq_bs = f"{fmt_f('v')} \\cdot F_{{nv}} A_b" if is_lrfd else f"\\frac{{F_{{nv}} A_b}}{{{om_v}}}"
    sub_bs = f"{fmt_f('v')} \\cdot {Fnv} \\cdot {Ab:.1f}/1000"
    
    md.append(calc_block(kv_sym, "Bolt Shear Capacity", eq_bs, sub_bs, cap_bolt, "kN"))
    md.append(ratio_bar(V_res, cap_bolt, "Bolt Shear"))

    # --- 4.2 Bearing ---
    md.append(sub_header("2.2 Bolt Bearing Strength", "J3.10"))
    md.append("*Checking minimum of Plate and Beam Web.*")
    
    # Plate
    Rn_br_pl = (2.4 * d * t_pl * Fu_pl) / 1000.0
    cap_br_pl = Rn_br_pl * get_f('v')
    
    # Web
    Rn_br_wb = (2.4 * d * t_web * Fu_beam) / 1000.0
    cap_br_wb = Rn_br_wb * get_f('v')
    
    cap_br_min = min(cap_br_pl, cap_br_wb)
    
    # Display simplified bearing check
    md.append(f"**Plate Bearing ($t={t_pl}$):**")
    md.append(f"$$ {kv_sym} = {fmt_f('v')} \\cdot 2.4({d})({t_pl})({Fu_pl})/1000 = \\mathbf{{{cap_br_pl:.2f}}} \\text{{ kN}} $$")
    
    md.append(f"**Web Bearing ($t={t_web}$):**")
    md.append(f"$$ {kv_sym} = {fmt_f('v')} \\cdot 2.4({d})({t_web})({Fu_beam})/1000 = \\mathbf{{{cap_br_wb:.2f}}} \\text{{ kN}} $$")
    
    md.append(f"\n**Governing Capacity:** $\\mathbf{{{cap_br_min:.2f}}}$ **kN**")
    md.append(ratio_bar(V_res, cap_br_min, "Bearing"))

    # --- 4.3 Plate Checks ---
    md.append(sub_header("2.3 Plate Shear Yielding", "J4.2"))
    Ag = h_pl * t_pl
    Rn_yld = (0.60 * Fy_pl * Ag) / 1000.0
    cap_yld = Rn_yld * get_f('y')
    
    eq_yld = f"{fmt_f('y')} \\cdot 0.6 F_y A_g" if is_lrfd else f"\\frac{{0.6 F_y A_g}}{{{om_y}}}"
    sub_yld = f"{fmt_f('y')} \\cdot 0.6 ({Fy_pl}) ({Ag:.0f})/1000"
    
    md.append(calc_block(kv_sym, "Yielding Capacity (Gross)", eq_yld, sub_yld, cap_yld, "kN"))
    md.append(ratio_bar(V_load, cap_yld, "Yielding"))

    md.append(sub_header("2.4 Plate Shear Rupture", "J4.3"))
    An = (h_pl - (n_rows * h_hole)) * t_pl
    Rn_rup = (0.60 * Fu_pl * An) / 1000.0
    cap_rup = Rn_rup * get_f('r')
    
    eq_rup = f"{fmt_f('r')} \\cdot 0.6 F_u A_{{nv}}" if is_lrfd else f"\\frac{{0.6 F_u A_{{nv}}}}{{{om_r}}}"
    sub_rup = f"{fmt_f('r')} \\cdot 0.6 ({Fu_pl}) ({An:.0f})/1000"
    
    md.append(calc_block(kv_sym, "Rupture Capacity (Net)", eq_rup, sub_rup, cap_rup, "kN"))
    md.append(ratio_bar(V_load, cap_rup, "Rupture"))

    # --- 4.4 Block Shear ---
    md.append(sub_header("2.5 Block Shear", "J4.3"))
    
    lv = plate['lv']; l_side = plate['l_side']
    Agv = (lv + (n_rows - 1) * s_v) * t_pl
    Anv = (Agv/t_pl - (n_rows - 0.5) * h_hole) * t_pl
    Ant = (l_side - 0.5 * h_hole) * t_pl
    
    md.append(f"- Areas: $A_{{gv}}={Agv:.0f}, A_{{nv}}={Anv:.0f}, A_{{nt}}={Ant:.0f}$ mm²")
    
    term1 = 0.6 * Fu_pl * Anv
    term2 = 1.0 * Fu_pl * Ant 
    term3 = 0.6 * Fy_pl * Agv
    
    Rn_blk_1 = (term1 + term2) / 1000.0
    Rn_blk_2 = (term3 + term2) / 1000.0
    Rn_blk = min(Rn_blk_1, Rn_blk_2)
    cap_blk = Rn_blk * get_f('r')
    
    eq_blk = r"\min [0.6 F_u A_{nv} + U_{bs} F_u A_{nt}, \quad 0.6 F_y A_{gv} + U_{bs} F_u A_{nt}]"
    sub_blk = f"\\min [{Rn_blk_1:.1f}, {Rn_blk_2:.1f}]"
    
    md.append(calc_block("R_n", "Nominal Block Shear", eq_blk, sub_blk, Rn_blk, "kN"))
    md.append(f"**Design Capacity ({kv_sym}):** ${fmt_f('r')} \\cdot {Rn_blk:.2f} = \\mathbf{{{cap_blk:.2f}}}$ **kN**")
    md.append(ratio_bar(V_load, cap_blk, "Block Shear"))

    # --- 4.5 Weld ---
    md.append(sub_header("2.6 Weld Strength", "J2.4"))
    L_weld = h_pl * 2
    Rn_weld = (0.60 * 480 * 0.707 * w_sz * L_weld) / 1000.0
    cap_weld = Rn_weld * get_f('w')
    
    eq_w = f"{fmt_f('w')} \\cdot 0.6 F_{{exx}} (0.707 w) L" if is_lrfd else f"\\frac{{...}}{{{om_w}}}"
    sub_w = f"{fmt_f('w')} \\cdot 0.4242 (480) ({w_sz}) ({L_weld}) / 1000"
    
    md.append(calc_block(kv_sym, "Weld Capacity", eq_w, sub_w, cap_weld, "kN"))
    md.append(ratio_bar(V_load, cap_weld, "Weld"))

    return "\n".join(md)
