import math

def generate_report(V_load, T_load, beam, plate, bolts, cope, is_lrfd=True, material_grade="A36", bolt_grade="A325"):
    
    lines = []
    
    # ==========================================
    # 0. SETUP & HELPER FUNCTIONS
    # ==========================================
    
    if is_lrfd:
        method = "LRFD"
        phi_y = 0.90; phi_r = 0.75; phi_w = 0.75; phi_b = 0.75
        design_sym = "\\phi R_n"
    else:
        method = "ASD"
        phi_y = 1/1.67; phi_r = 1/2.00; phi_w = 1/2.00; phi_b = 1/2.00
        design_sym = "R_n / \\Omega"

    def h2(text): lines.append(f"\n## {text}\n")
    def h3(text): lines.append(f"\n### {text}\n")
    def divider(): lines.append("---")

    # 🔥 ฟังก์ชันพระเอก: แสดง สูตร -> แทนค่า -> คำตอบ
    def show_calc(title, symbol, formula, sub_str, result_val, unit, phi_factor=None, note=""):
        lines.append(f"**{title}** {note}")
        lines.append("$$")
        lines.append("\\begin{aligned}")
        lines.append(f"{symbol} &= {formula} \\\\")
        lines.append(f"&= {sub_str} \\\\")
        lines.append(f"&= \\mathbf{{{result_val:,.2f}}} \\text{{ {unit} }}")
        
        if phi_factor:
            design_val = result_val * phi_factor
            phi_str = "0.90" if phi_factor == 0.90 else "0.75" # Display string
            if not is_lrfd: phi_str = "1/\\Omega" # ASD display
            
            lines.append(f"\\\\ \\therefore {design_sym} &= {phi_str} \\times {result_val:,.2f} \\\\")
            lines.append(f"&= \\mathbf{{{design_val:,.2f}}} \\text{{ {unit} }}")
            
        lines.append("\\end{aligned}")
        lines.append("$$")
        return result_val * (phi_factor if phi_factor else 1.0)

    def check_ratio(demand, capacity, label):
        ratio = demand / capacity if capacity > 0 else 999
        status = "✅ PASS" if ratio <= 1.0 else "❌ FAIL"
        color = "green" if ratio <= 1.0 else "red"
        lines.append(f"> **Check {label}:** ${demand:.2f} / {capacity:.2f} = {ratio:.2f}$ ... <span style='color:{color}; font-weight:bold'>{status}</span>")
        lines.append("")

    # ==========================================
    # 1. INPUT PARAMETERS
    # ==========================================
    lines.append(f"# 🏗️ Detailed Calculation Report ({method})")
    lines.append("---")
    
    # Unpack Data
    d = bolts['d']
    Ab = (math.pi * d**2)/4
    rows = bolts['rows']; cols = bolts['cols']
    n_bolts = rows * cols
    
    t_pl = plate['t']; h_pl = plate['h']
    Fy_pl = plate['Fy']; Fu_pl = plate['Fu']
    
    # Header Info
    lines.append("#### 1. Design Inputs")
    lines.append(f"- **Loads:** $V_u = {V_load:.2f}$ kN, $T_u = {T_load:.2f}$ kN")
    lines.append(f"- **Plate Material:** $F_y = {Fy_pl}$ MPa, $F_u = {Fu_pl}$ MPa, $t = {t_pl}$ mm")
    lines.append(f"- **Bolts:** {n_bolts} x M{d} ({bolt_grade}), Area $A_b = {Ab:.1f}$ mm²")
    
    # ==========================================
    # 2. BOLT FORCES (ELASTIC ANALYSIS)
    # ==========================================
    h2("2. Bolt Force Analysis (Elastic Method)")
    
    # Eccentricity
    sv = bolts['s_v']; sh = bolts.get('s_h', 0)
    e1 = plate.get('e1', 0)
    x_bar = ((cols - 1) * sh) / 2 if cols > 1 else 0
    e_total = e1 + x_bar
    
    show_calc("Eccentricity ($e$)", "e", "e_1 + x_{bar}", f"{e1} + {x_bar}", e_total, "mm")
    
    # Moment
    Mu = V_load * e_total / 1000.0
    show_calc("Moment ($M_u$)", "M_u", "V_u \\times e", f"{V_load:.2f} \\times {e_total}/1000", Mu, "kN-m")
    
    # Inertia Sum r^2
    sum_r2 = 0; r_max_val = 0
    col_start = -x_bar
    row_start = -((rows - 1) * sv) / 2
    
    # Loop to calculate r^2
    r_details = []
    for c in range(cols):
        for r in range(rows):
            dx = col_start + (c * sh)
            dy = row_start + (r * sv)
            r2 = dx**2 + dy**2
            sum_r2 += r2
            if math.sqrt(r2) > r_max_val: r_max_val = math.sqrt(r2)
            
    show_calc("Polar Inertia ($\\Sigma r^2$)", "\\Sigma (x^2 + y^2)", "\\text{sum of all bolts}", f"{sum_r2:,.0f}", sum_r2, "mm^2")

    # Forces
    Rv_direct = V_load / n_bolts
    Rv_moment = (Mu * 1000 * x_bar) / sum_r2 if sum_r2 > 0 else 0 # Simplified component for corner bolt
    Rh_moment = (Mu * 1000 * ((rows-1)*sv)/2) / sum_r2 if sum_r2 > 0 else 0
    
    lines.append("**Resultant Shear per Bolt ($V_{ub}$):**")
    lines.append("$$ V_{ub} = \\sqrt{(V/n + R_{ym})^2 + (R_{xm})^2} $$")
    
    V_ub = math.sqrt((Rv_direct + Rv_moment)**2 + Rh_moment**2)
    show_calc("Max Bolt Shear", "V_{ub}", "\\text{Vector Sum}", 
              f"\\sqrt{{({Rv_direct:.2f}+{Rv_moment:.2f})^2 + {Rh_moment:.2f}^2}}", V_ub, "kN")
    
    T_ub = T_load / n_bolts
    if T_load > 0:
        show_calc("Max Bolt Tension", "T_{ub}", "T_u / n", f"{T_load:.2f} / {n_bolts}", T_ub, "kN")

    # ==========================================
    # 3. BOLT CAPACITY
    # ==========================================
    h2("3. Bolt Capacity Checks")
    
    # 3.1 Shear
    Fnv = bolts['Fnv']
    Rn_shear = Fnv * Ab / 1000.0
    cap_shear = show_calc("Bolt Shear Strength", "R_n", "F_{nv} \\times A_b", 
                          f"{Fnv} \\times {Ab:.1f} / 1000", Rn_shear, "kN", phi_r)
    check_ratio(V_ub, cap_shear, "Bolt Shear")

    # 3.2 Tension Interaction (if applicable)
    if T_load > 0:
        h3("Combined Tension & Shear")
        frv = (V_ub * 1000) / Ab
        show_calc("Shear Stress", "f_{rv}", "V_{ub} / A_b", f"{V_ub:.2f} \\times 1000 / {Ab:.1f}", frv, "MPa")
        
        Fnt = bolts.get('Fnt', Fnv*1.3)
        Fnt_prime = 1.3 * Fnt - (Fnt / (phi_r * Fnv)) * frv
        Fnt_prime = min(max(Fnt_prime, 0), Fnt)
        
        show_calc("Reduced Tension Stress", "F'_{nt}", 
                  "1.3F_{nt} - \\frac{F_{nt}}{\\phi F_{nv}}f_{rv}",
                  f"1.3({Fnt}) - \\frac{{{Fnt}}}{{0.75 \\times {Fnv}}}({frv:.1f})",
                  Fnt_prime, "MPa")
        
        Rn_tens = Fnt_prime * Ab / 1000.0
        cap_tens = show_calc("Bolt Tension Strength", "R_n", "F'_{nt} \\times A_b",
                             f"{Fnt_prime:.1f} \\times {Ab:.1f} / 1000", Rn_tens, "kN", phi_r)
        check_ratio(T_ub, cap_tens, "Bolt Tension")

    # 3.3 Bearing
    h3("Bearing Strength (Plate)")
    lv = plate.get('lv', 35)
    Lc = lv - (d+2)/2.0
    show_calc("Clear Distance ($L_c$)", "L_c", "l_v - d_h/2", f"{lv} - {(d+2)}/2", Lc, "mm")
    
    Rn_br1 = (1.2 * Lc * t_pl * Fu_pl) / 1000.0
    Rn_br2 = (2.4 * d * t_pl * Fu_pl) / 1000.0
    Rn_br = min(Rn_br1, Rn_br2)
    
    show_calc("Bearing (Tearout)", "R_{n1}", "1.2 L_c t F_u", f"1.2({Lc:.1f})({t_pl})({Fu_pl})/1000", Rn_br1, "kN")
    show_calc("Bearing (Deformation)", "R_{n2}", "2.4 d t F_u", f"2.4({d})({t_pl})({Fu_pl})/1000", Rn_br2, "kN")
    
    cap_br = Rn_br * phi_b
    lines.append(f"$\\therefore \\phi R_n = {phi_b} \\times \\min({Rn_br1:.1f}, {Rn_br2:.1f}) = \\mathbf{{{cap_br:.2f}}}$ **kN**")
    check_ratio(V_ub, cap_br, "Bolt Bearing")

    # ==========================================
    # 4. PLATE CAPACITY
    # ==========================================
    h2("4. Plate Capacity Checks")
    
    # 4.1 Yielding
    Ag = h_pl * t_pl
    Rn_yld = Fy_pl * Ag / 1000.0
    show_calc("Gross Area ($A_g$)", "A_g", "h \\times t", f"{h_pl} \\times {t_pl}", Ag, "mm^2")
    cap_yld = show_calc("Shear Yielding", "R_n", "0.60 F_y A_g", 
                        f"0.60({Fy_pl})({Ag}) / 1000", Rn_yld, "kN", phi_y)
    check_ratio(V_load, cap_yld, "Plate Yield")
    
    # 4.2 Rupture
    An = (h_pl - (rows * (d+2))) * t_pl
    Rn_rup = 0.60 * Fu_pl * An / 1000.0
    show_calc("Net Area ($A_n$)", "A_n", "(h - n_{row} d_h) t", 
              f"({h_pl} - {rows}\\times{d+2})({t_pl})", An, "mm^2")
    cap_rup = show_calc("Shear Rupture", "R_n", "0.60 F_u A_n", 
                        f"0.60({Fu_pl})({An}) / 1000", Rn_rup, "kN", phi_r)
    check_ratio(V_load, cap_rup, "Plate Rupture")
    
    # 4.3 Block Shear
    h3("Block Shear (Plate)")
    # Areas
    Agv = (lv + (rows-1)*sv) * t_pl
    Anv = Agv - ((rows-0.5)*(d+2)*t_pl)
    Ant = (plate.get('l_side', 35) - 0.5*(d+2)) * t_pl
    
    lines.append(f"- $A_{{gv}} = ({lv} + {rows-1}\\times{sv})({t_pl}) = {Agv:.0f}$ mm²")
    lines.append(f"- $A_{{nv}} = {Agv:.0f} - ({rows}-0.5)({d+2})({t_pl}) = {Anv:.0f}$ mm²")
    lines.append(f"- $A_{{nt}} = ({plate.get('l_side',35)} - 0.5({d+2}))({t_pl}) = {Ant:.0f}$ mm²")
    
    term1 = 0.6 * Fu_pl * Anv
    term2 = 1.0 * Fu_pl * Ant
    Rn_bs1 = (term1 + term2)/1000.0
    
    term3 = 0.6 * Fy_pl * Agv
    Rn_bs2 = (term3 + term2)/1000.0
    
    show_calc("Case 1 (Rupture+Rupture)", "R_{n1}", "0.6 F_u A_{nv} + U_{bs} F_u A_{nt}", 
              f"(0.6 \\times {Fu_pl} \\times {Anv:.0f} + 1.0 \\times {Fu_pl} \\times {Ant:.0f})/1000", Rn_bs1, "kN")
              
    show_calc("Case 2 (Yield+Rupture)", "R_{n2}", "0.6 F_y A_{gv} + U_{bs} F_u A_{nt}", 
              f"(0.6 \\times {Fy_pl} \\times {Agv:.0f} + 1.0 \\times {Fu_pl} \\times {Ant:.0f})/1000", Rn_bs2, "kN")
    
    Rn_bs = min(Rn_bs1, Rn_bs2)
    cap_bs = Rn_bs * phi_r
    lines.append(f"$\\therefore \\phi R_n = {phi_r} \\times {Rn_bs:.2f} = \\mathbf{{{cap_bs:.2f}}}$ **kN**")
    check_ratio(V_load, cap_bs, "Block Shear")
    
    # ==========================================
    # 5. WELD CHECK
    # ==========================================
    h2("5. Weld Capacity")
    w_sz = plate['weld_size']
    Lw = h_pl * 2
    Fw = 0.60 * 480 # E70 electrode strength approx
    
    show_calc("Weld Area ($A_w$)", "A_w", "0.707 \\times w \\times L", 
              f"0.707 \\times {w_sz} \\times {Lw}", 0.707*w_sz*Lw, "mm^2")
              
    Rn_weld = Fw * (0.707 * w_sz * Lw) / 1000.0
    cap_weld = show_calc("Weld Strength", "R_n", "0.60 F_{exx} A_w",
                         f"0.60(480)({0.707*w_sz*Lw:.1f}) / 1000", Rn_weld, "kN", phi_w)
    
    R_resultant = math.sqrt(V_load**2 + T_load**2)
    check_ratio(R_resultant, cap_weld, "Weld Group")

    return "\n".join(lines)
