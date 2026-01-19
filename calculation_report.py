# calculation_report.py
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

    # 🔥 ปรับแก้ฟังก์ชันแสดงผลให้อ่านง่ายขึ้น (ไม่ต้องใช้ aligned)
    def show_calc(title, symbol, formula, sub_str, result_val, unit, phi_factor=None, note=""):
        lines.append(f"**{title}** {note}")
        
        # แปลงเครื่องหมายคูณ * เป็น \times เพื่อความสวยงามในสมการ
        clean_formula = formula.replace("*", " \\times ")
        clean_sub = str(sub_str).replace("*", " \\times ")
        
        # แสดงผลทีละบรรทัด (อ่านง่ายกว่า และไม่พังง่าย)
        lines.append(f"$$ {symbol} = {clean_formula} $$")
        lines.append(f"$$ = {clean_sub} $$")
        lines.append(f"$$ = \\mathbf{{{result_val:,.2f}}} \\text{{ {unit} }} $$")
        
        if phi_factor:
            design_val = result_val * phi_factor
            phi_str = "0.90" if phi_factor == 0.90 else "0.75"
            if not is_lrfd: phi_str = "1/\\Omega"
            
            lines.append(f"> **Design Strength:** ${design_sym} = {phi_str} \\times {result_val:,.2f} = \\mathbf{{{design_val:,.2f}}}$ **{unit}**")
            lines.append("")
            
        lines.append("") # เว้นบรรทัด
        return result_val * (phi_factor if phi_factor else 1.0)

    def check_ratio(demand, capacity, label):
        ratio = demand / capacity if capacity > 0 else 999
        status = "✅ PASS" if ratio <= 1.0 else "❌ FAIL"
        color = "green" if ratio <= 1.0 else "red"
        # ใช้ HTML Bar เพื่อความชัดเจน
        lines.append(f"<div style='background-color:#f3f4f6; padding:8px; border-radius:4px; border-left:4px solid {color}; font-family:monospace;'>")
        lines.append(f"Check {label}: {demand:.2f} / {capacity:.2f} = <b>{ratio:.2f}</b> <span style='color:{color}; float:right;'>{status}</span>")
        lines.append("</div>")
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
    
    lines.append("#### 1. Design Inputs")
    lines.append(f"- **Design Load:** $V_u = {V_load:.2f}$ kN, $T_u = {T_load:.2f}$ kN")
    lines.append(f"- **Plate:** $t = {t_pl}$ mm, $H = {h_pl}$ mm ({material_grade})")
    lines.append(f"- **Bolts:** {n_bolts} nos. M{d} ({bolt_grade}), Area $A_b = {Ab:.1f}$ mm²")
    
    # ==========================================
    # 2. BOLT FORCE ANALYSIS
    # ==========================================
    h2("2. Bolt Force Analysis (Elastic Method)")
    
    # Eccentricity
    sv = bolts['s_v']; sh = bolts.get('s_h', 0)
    e1 = plate.get('e1', 0)
    x_bar = ((cols - 1) * sh) / 2 if cols > 1 else 0
    e_total = e1 + x_bar
    
    show_calc("Eccentricity (e)", "e", "e_1 + x_{bar}", f"{e1} + {x_bar}", e_total, "mm")
    
    # Moment
    Mu = V_load * e_total / 1000.0
    show_calc("Moment (Mu)", "M_u", "V_u \\times e", f"{V_load:.2f} \\times {e_total}/1000", Mu, "kN-m")
    
    # Inertia Sum r^2
    sum_r2 = 0
    col_start = -x_bar
    row_start = -((rows - 1) * sv) / 2
    
    for c in range(cols):
        for r in range(rows):
            dx = col_start + (c * sh)
            dy = row_start + (r * sv)
            sum_r2 += dx**2 + dy**2
            
    show_calc("Polar Inertia (Sum r^2)", "\\Sigma (x^2 + y^2)", "\\text{sum of all bolts}", f"{sum_r2:,.0f}", sum_r2, "mm^2")

    # Resultant Forces
    # Simplified vector combination for critical bolt
    Rv_direct = V_load / n_bolts
    Rv_moment = (Mu * 1000 * x_bar) / sum_r2 if sum_r2 > 0 else 0 
    Rh_moment = (Mu * 1000 * ((rows-1)*sv)/2) / sum_r2 if sum_r2 > 0 else 0
    
    V_ub = math.sqrt((Rv_direct + Rv_moment)**2 + Rh_moment**2)
    show_calc("Max Shear per Bolt (V_ub)", "V_{ub}", "\\sqrt{(V/n + R_{ym})^2 + (R_{xm})^2}", 
              f"\\sqrt{{({Rv_direct:.2f}+{Rv_moment:.2f})^2 + {Rh_moment:.2f}^2}}", V_ub, "kN")
    
    T_ub = T_load / n_bolts
    if T_load > 0:
        show_calc("Max Tension per Bolt (T_ub)", "T_{ub}", "T_u / n", f"{T_load:.2f} / {n_bolts}", T_ub, "kN")

    # ==========================================
    # 3. BOLT CAPACITY
    # ==========================================
    h2("3. Bolt Capacity Checks")
    
    # 3.1 Shear
    Fnv = bolts['Fnv']
    Rn_shear = Fnv * Ab / 1000.0
    cap_shear = show_calc("Bolt Shear Strength", "R_n", "F_{nv} A_b", 
                          f"{Fnv} \\times {Ab:.1f} / 1000", Rn_shear, "kN", phi_r)
    check_ratio(V_ub, cap_shear, "Bolt Shear")

    # 3.2 Tension
    if T_load > 0:
        h3("Combined Tension & Shear")
        frv = (V_ub * 1000) / Ab
        # show_calc("Shear Stress", "f_{rv}", "V_{ub} / A_b", f"{V_ub:.2f} \\times 1000 / {Ab:.1f}", frv, "MPa")
        
        Fnt = bolts.get('Fnt', Fnv*1.3)
        Fnt_prime = 1.3 * Fnt - (Fnt / (phi_r * Fnv)) * frv
        Fnt_prime = min(max(Fnt_prime, 0), Fnt)
        
        show_calc("Reduced Tension Stress (F'nt)", "F'_{nt}", 
                  "1.3F_{nt} - \\frac{F_{nt}}{\\phi F_{nv}}f_{rv}",
                  f"1.3({Fnt}) - \\dots({frv:.1f})", Fnt_prime, "MPa")
        
        Rn_tens = Fnt_prime * Ab / 1000.0
        cap_tens = show_calc("Bolt Tension Strength", "R_n", "F'_{nt} A_b",
                             f"{Fnt_prime:.1f} \\times {Ab:.1f} / 1000", Rn_tens, "kN", phi_r)
        check_ratio(T_ub, cap_tens, "Bolt Tension")

    # 3.3 Bearing
    h3("Bearing Strength (Plate)")
    lv = plate.get('lv', 35)
    Lc = lv - (d+2)/2.0
    show_calc("Clear Distance (Lc)", "L_c", "l_v - d_{hole}/2", f"{lv} - {(d+2)}/2", Lc, "mm")
    
    Rn_br1 = (1.2 * Lc * t_pl * Fu_pl) / 1000.0
    Rn_br2 = (2.4 * d * t_pl * Fu_pl) / 1000.0
    Rn_br = min(Rn_br1, Rn_br2)
    
    show_calc("Bearing Strength", "R_n", "\\min(1.2 L_c t F_u, 2.4 d t F_u)", 
              f"\\min({Rn_br1:.1f}, {Rn_br2:.1f})", Rn_br, "kN", phi_b)
    check_ratio(V_ub, Rn_br*phi_b, "Bolt Bearing")

    # ==========================================
    # 4. PLATE CAPACITY
    # ==========================================
    h2("4. Plate Capacity Checks")
    
    # 4.1 Yielding
    Ag = h_pl * t_pl
    show_calc("Gross Area (Ag)", "A_g", "H \\times t", f"{h_pl} \\times {t_pl}", Ag, "mm^2")
    
    Rn_yld = Fy_pl * Ag / 1000.0
    cap_yld = show_calc("Shear Yielding", "R_n", "0.60 F_y A_g", 
                        f"0.60({Fy_pl})({Ag}) / 1000", Rn_yld, "kN", phi_y)
    check_ratio(V_load, cap_yld, "Plate Yield")
    
    # 4.2 Rupture
    An = (h_pl - (rows * (d+2))) * t_pl
    show_calc("Net Area (An)", "A_n", "(H - n_{row} d_{hole}) t", 
              f"({h_pl} - {rows}\\times{d+2})({t_pl})", An, "mm^2")
              
    Rn_rup = 0.60 * Fu_pl * An / 1000.0
    cap_rup = show_calc("Shear Rupture", "R_n", "0.60 F_u A_n", 
                        f"0.60({Fu_pl})({An}) / 1000", Rn_rup, "kN", phi_r)
    check_ratio(V_load, cap_rup, "Plate Rupture")
    
    # 4.3 Block Shear
    h3("Block Shear (Plate)")
    Agv = (lv + (rows-1)*sv) * t_pl
    Anv = Agv - ((rows-0.5)*(d+2)*t_pl)
    Ant = (plate.get('l_side', 35) - 0.5*(d+2)) * t_pl
    
    lines.append(f"- Shear Areas: $A_{{gv}} = {Agv:.0f}, A_{{nv}} = {Anv:.0f}$ mm²")
    lines.append(f"- Tension Area: $A_{{nt}} = {Ant:.0f}$ mm²")
    
    Rn_bs1 = (0.6 * Fu_pl * Anv + 1.0 * Fu_pl * Ant)/1000.0
    Rn_bs2 = (0.6 * Fy_pl * Agv + 1.0 * Fu_pl * Ant)/1000.0
    Rn_bs = min(Rn_bs1, Rn_bs2)
    
    show_calc("Block Shear Strength", "R_n", "\\min(R_{n1}, R_{n2})", 
              f"\\min({Rn_bs1:.1f}, {Rn_bs2:.1f})", Rn_bs, "kN", phi_r)
    check_ratio(V_load, Rn_bs*phi_r, "Block Shear")
    
    # ==========================================
    # 5. WELD CHECK
    # ==========================================
    h2("5. Weld Capacity")
    w_sz = plate['weld_size']
    Lw = h_pl * 2
    
    Rn_weld = 0.60 * 480 * (0.707 * w_sz * Lw) / 1000.0
    cap_weld = show_calc("Weld Strength", "R_n", "0.60 F_{exx} (0.707 w L)",
                         f"0.60(480)(0.707 \\times {w_sz} \\times {Lw}) / 1000", Rn_weld, "kN", phi_w)
    
    R_total = math.sqrt(V_load**2 + T_load**2)
    check_ratio(R_total, cap_weld, "Weld Group")

    return "\n".join(lines)
