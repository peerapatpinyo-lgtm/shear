import math

def generate_report(V_load, beam, plate, bolts, is_lrfd=True, material_grade="A36", bolt_grade="A325"):
    
    # --- HELPER: สร้าง String แบบ List เพื่อความชัวร์เรื่องบรรทัด ---
    def calc_block(symbol, description, formula_tex, sub_tex, result, unit):
        # บังคับ $$ ขึ้นบรรทัดใหม่ และจบด้วย $$ บรรทัดใหม่
        lines = [
            f"**{description}**",
            "",
            "$$",
            "\\begin{aligned}",
            f"{symbol} &= {formula_tex} \\\\",
            f"&= {sub_tex} \\\\",
            f"&= \\mathbf{{{result:,.2f}}} \\text{{ {unit} }}",
            "\\end{aligned}",
            "$$",
            ""
        ]
        return "\n".join(lines)

    def ratio_bar(demand, capacity, label="Ratio"):
        if capacity == 0: ratio = 999.0
        else: ratio = demand / capacity
            
        color = "#15803d" if ratio <= 1.0 else "#b91c1c" # Green / Red
        icon = "✅ PASS" if ratio <= 1.0 else "❌ FAIL"
        
        # HTML ก้อนเดียว จบในบรรทัดเดียว (ตัดปัญหา Newline)
        return f"""<div style="margin-top:5px; margin-bottom:15px; padding:10px; background-color:#f0f2f6; border-radius:5px;"><strong>Check {label}:</strong> {demand:.2f} / {capacity:.2f} = <strong>{ratio:.2f}</strong> &nbsp; <span style='color:{color}; font-weight:bold'>[{icon}]</span></div>"""

    # --- 1. SETUP ---
    if is_lrfd:
        method_name = "LRFD (Limit State Design)"
        f_v, f_y, f_r, f_w = 0.75, 0.90, 0.75, 0.75
        kv_sym = "\\phi R_n"
        get_f = lambda t: 0.75 if t in ['v','r','w'] else 0.90
        fmt_f = lambda t: f"{get_f(t)}"
    else:
        method_name = "ASD (Allowable Strength Design)"
        om_v, om_y, om_r, om_w = 2.00, 1.50, 2.00, 2.00
        kv_sym = "R_n / \\Omega"
        get_f = lambda t: 1.0/2.00 if t!='y' else 1.0/1.50
        fmt_f = lambda t: "1/2.00" if t!='y' else "1/1.50"

    # Unpack Data
    d = bolts['d']; h_hole = d + 2
    n_rows = bolts['rows']; n_cols = bolts['cols']; n_total = n_rows * n_cols
    s_v = bolts['s_v']; s_h = bolts.get('s_h', 0)
    t_pl = plate['t']; h_pl = plate['h']
    Fy_pl = plate['Fy']; Fu_pl = plate['Fu']
    t_web = beam['tw']; Fu_beam = beam['Fu']
    Fnv = bolts['Fnv']; w_sz = plate['weld_size']

    report = []

    # --- 2. HEADER ---
    report.append(f"# 📐 CALCULATION REPORT")
    report.append(f"**Design Method:** {method_name}")
    report.append("---")
    report.append(f"- **Load ($V_u$):** {V_load:.2f} kN")
    report.append(f"- **Bolt:** M{d} ({n_rows}x{n_cols}) | **Plate:** {t_pl} mm")
    report.append("---")

    # --- 3. ANALYSIS ---
    report.append("### 1. Bolt Group Analysis")
    
    # Centroid & Eccentricity
    x_bar = ((n_cols - 1) * s_h) / 2 if n_cols > 1 else 0
    e_dist = plate['e1']
    eccentricity = e_dist + x_bar
    Mu_mm = V_load * eccentricity
    
    # Inertia (J)
    sum_r2 = 0; crit_x, crit_y = 0, 0
    row_start = -((n_rows - 1) * s_v) / 2
    col_start = -x_bar
    for c in range(n_cols):
        for r in range(n_rows):
            dx = col_start + (c * s_h); dy = row_start + (r * s_v)
            r_sq = dx**2 + dy**2
            sum_r2 += r_sq
            if r_sq >= (crit_x**2 + crit_y**2): crit_x, crit_y = abs(dx), abs(dy)

    report.append(calc_block("J", "Polar Moment of Inertia", "\\sum (x^2 + y^2)", f"{sum_r2:,.0f}", sum_r2, "mm^2"))

    # Force Demand
    Rv_direct = V_load / n_total
    Rv_moment = (Mu_mm * crit_x) / sum_r2 if sum_r2 > 0 else 0
    Rh_moment = (Mu_mm * crit_y) / sum_r2 if sum_r2 > 0 else 0
    V_res = math.sqrt((Rv_direct + Rv_moment)**2 + Rh_moment**2)

    report.append("#### Force Demand on Critical Bolt")
    report.append(f"- Critical Bolt: $(x,y) = ({crit_x:.1f}, {crit_y:.1f})$ mm")
    
    # Component Forces (เขียนสดเพื่อความแม่นยำ)
    report.append("$$")
    report.append("\\begin{aligned}")
    report.append(f"R_{{vx}} &= \\frac{{{Mu_mm:.0f} \\cdot {crit_y:.1f}}}{{{sum_r2:.0f}}} = \\mathbf{{{Rh_moment:.2f}}} \\text{{ kN}} \\\\")
    report.append(f"R_{{vy}} &= {Rv_direct:.2f} + {Rv_moment:.2f} = \\mathbf{{{(Rv_direct+Rv_moment):.2f}}} \\text{{ kN}}")
    report.append("\\end{aligned}")
    report.append("$$")
    
    report.append(calc_block("V_{r}", "Resultant Shear Force", "\\sqrt{R_{vx}^2 + R_{vy}^2}", f"{V_res:.2f}", V_res, "kN"))

    # --- 4. CHECKS ---
    report.append("---")
    report.append("### 2. Capacity Checks")

    # Bolt Shear
    Ab = (math.pi * d**2) / 4; Rn_bolt = (Fnv * Ab) / 1000.0; cap_bolt = Rn_bolt * get_f('v')
    report.append(calc_block(kv_sym, "2.1 Bolt Shear Strength", f"{fmt_f('v')} F_{{nv}} A_b", f"{cap_bolt:.2f}", cap_bolt, "kN"))
    report.append(ratio_bar(V_res, cap_bolt, "Bolt Shear"))

    # Bearing
    Rn_br_pl = (2.4 * d * t_pl * Fu_pl) / 1000.0; cap_br_pl = Rn_br_pl * get_f('v')
    Rn_br_wb = (2.4 * d * t_web * Fu_beam) / 1000.0; cap_br_wb = Rn_br_wb * get_f('v')
    cap_br_min = min(cap_br_pl, cap_br_wb)
    
    report.append("#### 2.2 Bolt Bearing Strength")
    report.append(f"$$ {kv_sym} (Plate) = \\mathbf{{{cap_br_pl:.2f}}} \\text{{ kN}} $$")
    report.append(f"$$ {kv_sym} (Web) = \\mathbf{{{cap_br_wb:.2f}}} \\text{{ kN}} $$")
    report.append(ratio_bar(V_res, cap_br_min, "Bearing"))

    # Yielding & Rupture
    Ag = h_pl * t_pl; Rn_yld = (0.6 * Fy_pl * Ag)/1000; cap_yld = Rn_yld * get_f('y')
    An = (h_pl - (n_rows * h_hole)) * t_pl; Rn_rup = (0.6 * Fu_pl * An)/1000; cap_rup = Rn_rup * get_f('r')

    report.append(calc_block(kv_sym, "2.3 Shear Yielding", f"{fmt_f('y')} 0.6 F_y A_g", f"{cap_yld:.2f}", cap_yld, "kN"))
    report.append(ratio_bar(V_load, cap_yld, "Yielding"))
    
    report.append(calc_block(kv_sym, "2.4 Shear Rupture", f"{fmt_f('r')} 0.6 F_u A_n", f"{cap_rup:.2f}", cap_rup, "kN"))
    report.append(ratio_bar(V_load, cap_rup, "Rupture"))

    return "\n".join(report)
