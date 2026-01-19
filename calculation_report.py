import math

def generate_report(V_load, beam, plate, bolts, is_lrfd=True, material_grade="A36", bolt_grade="A325"):
    """
    Generate calculation report using a List-based approach to ensure perfect Markdown/LaTeX formatting.
    No indentation issues, no syntax conflicts.
    """
    
    # =================================================================================
    # 1. HELPER FUNCTIONS (FORMATTERS)
    # =================================================================================
    def add_latex_block(lines_list, title, symbol, eq_steps, result_val, unit):
        """
        Helper to append a LaTeX block safely without indentation issues.
        eq_steps: List of strings for intermediate steps
        """
        lines_list.append(f"**{title}**")
        lines_list.append("") # Empty line for Markdown separation
        lines_list.append("$$")
        lines_list.append("\\begin{aligned}")
        
        # First line: Symbol = Formula
        # We assume the first element of eq_steps is the formula
        if eq_steps:
            lines_list.append(f"{symbol} &= {eq_steps[0]} \\\\")
            
            # Middle steps
            for step in eq_steps[1:]:
                lines_list.append(f"&= {step} \\\\")
        
        # Final result line
        lines_list.append(f"&= \\mathbf{{{result_val:,.2f}}} \\text{{ {unit} }}")
        
        lines_list.append("\\end{aligned}")
        lines_list.append("$$")
        lines_list.append("") # Empty line after block

    def add_html_bar(lines_list, label, demand, capacity):
        """
        Helper to append HTML progress bar. 
        REQUIRES: unsafe_allow_html=True in st.markdown()
        """
        if capacity == 0:
            ratio = 999.0
        else:
            ratio = demand / capacity

        color = "#15803d" if ratio <= 1.0 else "#b91c1c" # Green / Red
        icon = "✅ PASS" if ratio <= 1.0 else "❌ FAIL"
        
        # Use single line string for HTML to avoid any newline parsing errors
        html_code = (
            f"<div style='margin: 10px 0px; padding: 10px; background-color: #f0f2f6; border-radius: 5px; border-left: 5px solid {color};'>"
            f"<strong>Check {label}:</strong> {demand:.2f} / {capacity:.2f} = <strong>{ratio:.2f}</strong> "
            f"&nbsp; <span style='color:{color}; font-weight:bold'>[{icon}]</span>"
            f"</div>"
        )
        lines_list.append(html_code)
        lines_list.append("")

    # =================================================================================
    # 2. CALCULATION SETUP
    # =================================================================================
    # Factors
    if is_lrfd:
        method_str = "LRFD (Limit State Design)"
        phi = 0.75
        kv_sym = "\\phi R_n"
        # Helper to get specific factor (simplified for standard checks)
        get_f = lambda type_: 0.90 if type_ == 'y' else 0.75
        fmt_f = lambda type_: "0.90" if type_ == 'y' else "0.75"
    else:
        method_str = "ASD (Allowable Strength Design)"
        om = 2.00
        kv_sym = "R_n / \\Omega"
        get_f = lambda type_: 1.0/1.50 if type_ == 'y' else 1.0/2.00
        fmt_f = lambda type_: "1/1.50" if type_ == 'y' else "1/2.00"

    # Unpack Data
    d = bolts['d']
    h_hole = d + 2
    n_rows, n_cols = bolts['rows'], bolts['cols']
    n_total = n_rows * n_cols
    s_v = bolts['s_v']
    s_h = bolts.get('s_h', 0)
    
    t_pl, h_pl = plate['t'], plate['h']
    Fy_pl, Fu_pl = plate['Fy'], plate['Fu']
    t_web, Fu_beam = beam['tw'], beam['Fu']
    Fnv = bolts['Fnv']
    w_sz = plate['weld_size']

    # Initialize the report list
    lines = []

    # =================================================================================
    # 3. REPORT GENERATION (LINE BY LINE)
    # =================================================================================
    
    # --- Header ---
    lines.append(f"# 📐 CALCULATION REPORT")
    lines.append(f"**Design Method:** {method_str} | **Standard:** AISC 360-16")
    lines.append("---")
    
    # --- Input Data Summary ---
    lines.append("### **Design Parameters**")
    lines.append(f"* **Load ($V_u$):** {V_load:.2f} kN")
    lines.append(f"* **Bolt Group:** M{d} ({bolt_grade}), {n_rows} Rows x {n_cols} Columns")
    lines.append(f"* **Plate:** {t_pl} mm thick ($F_y={Fy_pl}, F_u={Fu_pl}$)")
    lines.append("---")

    # --- 1. Analysis ---
    lines.append("### **1. Bolt Group Analysis (Elastic Method)**")
    
    # Geometric Props
    x_bar = ((n_cols - 1) * s_h) / 2 if n_cols > 1 else 0
    e_dist = plate['e1']
    eccentricity = e_dist + x_bar
    Mu_mm = V_load * eccentricity
    
    # Inertia Calculation
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
    
    add_latex_block(lines, "Polar Moment of Inertia (J)", "J", 
                    [r"\sum (x^2 + y^2)", f"{sum_r2:,.0f}"], sum_r2, "mm^2")

    # Force Demand
    Rv_direct = V_load / n_total
    Rv_moment = (Mu_mm * crit_x) / sum_r2 if sum_r2 > 0 else 0
    Rh_moment = (Mu_mm * crit_y) / sum_r2 if sum_r2 > 0 else 0
    V_res = math.sqrt((Rv_direct + Rv_moment)**2 + Rh_moment**2)
    
    lines.append("#### **Force Demand on Critical Bolt**")
    lines.append(f"Critical Bolt Location: $(x, y) = ({crit_x:.1f}, {crit_y:.1f})$ mm")
    
    # Manual LaTeX block for components to ensure clarity
    lines.append("$$")
    lines.append("\\begin{aligned}")
    lines.append(f"R_{{vx}} &= \\frac{{M \\cdot y}}{{J}} = \\frac{{{Mu_mm:.0f} \\cdot {crit_y:.1f}}}{{{sum_r2:.0f}}} = \\mathbf{{{Rh_moment:.2f}}} \\text{{ kN}} \\\\")
    lines.append(f"R_{{vy}} &= \\frac{{V}}{{n}} + \\frac{{M \\cdot x}}{{J}} = {Rv_direct:.2f} + {Rv_moment:.2f} = \\mathbf{{{(Rv_direct+Rv_moment):.2f}}} \\text{{ kN}}")
    lines.append("\\end{aligned}")
    lines.append("$$")
    
    add_latex_block(lines, "Resultant Shear Force", "V_r",
                    [r"\sqrt{R_{vx}^2 + R_{vy}^2}", f"\\sqrt{{{Rh_moment:.2f}^2 + {(Rv_direct+Rv_moment):.2f}^2}}"], 
                    V_res, "kN")

    lines.append("---")
    lines.append("### **2. Capacity Checks**")

    # --- 2.1 Bolt Shear ---
    Ab = (math.pi * d**2) / 4
    Rn_bolt = (Fnv * Ab) / 1000.0
    cap_bolt = Rn_bolt * get_f('v')
    
    add_latex_block(lines, "2.1 Bolt Shear Strength", kv_sym,
                    [f"{fmt_f('v')} F_{{nv}} A_b", f"{fmt_f('v')} ({Fnv}) ({Ab:.1f}) / 1000"], 
                    cap_bolt, "kN")
    add_html_bar(lines, "Bolt Shear", V_res, cap_bolt)

    # --- 2.2 Bearing ---
    lines.append("#### **2.2 Bolt Bearing Strength**")
    
    Rn_br_pl = (2.4 * d * t_pl * Fu_pl) / 1000.0
    cap_br_pl = Rn_br_pl * get_f('v')
    
    Rn_br_wb = (2.4 * d * t_web * Fu_beam) / 1000.0
    cap_br_wb = Rn_br_wb * get_f('v')
    
    cap_br_min = min(cap_br_pl, cap_br_wb)
    
    lines.append(f"- Plate Bearing Capacity: **{cap_br_pl:.2f} kN**")
    lines.append(f"- Web Bearing Capacity: **{cap_br_wb:.2f} kN**")
    lines.append(f"**Governing Capacity:** $\\mathbf{{{cap_br_min:.2f}}}$ **kN**")
    
    add_html_bar(lines, "Bearing", V_res, cap_br_min)

    # --- 2.3 Yielding ---
    Ag = h_pl * t_pl
    Rn_yld = (0.60 * Fy_pl * Ag) / 1000.0
    cap_yld = Rn_yld * get_f('y')
    
    add_latex_block(lines, "2.3 Plate Shear Yielding", kv_sym,
                    [f"{fmt_f('y')} 0.6 F_y A_g", f"{fmt_f('y')} (0.6) ({Fy_pl}) ({Ag:.0f}) / 1000"], 
                    cap_yld, "kN")
    add_html_bar(lines, "Yielding", V_load, cap_yld)

    # --- 2.4 Rupture ---
    An = (h_pl - (n_rows * h_hole)) * t_pl
    Rn_rup = (0.60 * Fu_pl * An) / 1000.0
    cap_rup = Rn_rup * get_f('r')
    
    add_latex_block(lines, "2.4 Plate Shear Rupture", kv_sym,
                    [f"{fmt_f('r')} 0.6 F_u A_{{nv}}", f"{fmt_f('r')} (0.6) ({Fu_pl}) ({An:.0f}) / 1000"], 
                    cap_rup, "kN")
    add_html_bar(lines, "Rupture", V_load, cap_rup)

    # --- 2.5 Block Shear ---
    lines.append("#### **2.5 Block Shear**")
    lv, l_side = plate['lv'], plate['l_side']
    Agv = (lv + (n_rows - 1) * s_v) * t_pl
    Anv = (Agv/t_pl - (n_rows - 0.5) * h_hole) * t_pl
    Ant = (l_side - 0.5 * h_hole) * t_pl
    
    Rn_blk_1 = (0.6 * Fu_pl * Anv + 1.0 * Fu_pl * Ant) / 1000.0
    Rn_blk_2 = (0.6 * Fy_pl * Agv + 1.0 * Fu_pl * Ant) / 1000.0
    Rn_blk = min(Rn_blk_1, Rn_blk_2)
    cap_blk = Rn_blk * get_f('r')
    
    lines.append(f"* Areas: $A_{{gv}}={Agv:.0f}, A_{{nv}}={Anv:.0f}, A_{{nt}}={Ant:.0f}$ mm²")
    add_latex_block(lines, "Block Shear Capacity", kv_sym,
                    [f"{fmt_f('r')} \\min(R_{{n1}}, R_{{n2}})", f"{fmt_f('r')} \\min({Rn_blk_1:.1f}, {Rn_blk_2:.1f})"], 
                    cap_blk, "kN")
    add_html_bar(lines, "Block Shear", V_load, cap_blk)

    # --- 2.6 Weld ---
    L_weld = h_pl * 2
    Rn_weld = (0.60 * 480 * 0.707 * w_sz * L_weld) / 1000.0
    cap_weld = Rn_weld * get_f('w')
    
    add_latex_block(lines, "2.6 Weld Strength", kv_sym,
                   [f"{fmt_f('w')} 0.6 F_{{exx}} (0.707 w) L", f"{fmt_f('w')} (0.2545) (480) ({w_sz}) ({L_weld}) / 1000"],
                   cap_weld, "kN")
    add_html_bar(lines, "Weld", V_load, cap_weld)

    # JOIN ALL LINES
    return "\n".join(lines)
