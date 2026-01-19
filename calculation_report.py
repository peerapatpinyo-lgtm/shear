import math

def generate_report(V_load, beam, plate, bolts, is_lrfd=True, material_grade="A36", bolt_grade="A325"):
    
    # List สำหรับเก็บข้อความทีละบรรทัด (ตัดปัญหาเรื่องย่อหน้า)
    lines = []

    # --- Helper Function: สร้างสมการ LaTeX ---
    def add_latex(title, content):
        lines.append(f"**{title}**")
        lines.append("")    # เว้นบรรทัด
        lines.append("$$")  # เปิด Block สมการ
        lines.append(content)
        lines.append("$$")  # ปิด Block สมการ
        lines.append("")    # เว้นบรรทัด

    # --- Helper Function: สร้างแถบสี HTML ---
    def add_html_bar(label, demand, capacity):
        if capacity == 0: ratio = 999.0
        else: ratio = demand / capacity
        
        color = "#15803d" if ratio <= 1.0 else "#b91c1c" # Green / Red
        icon = "✅ PASS" if ratio <= 1.0 else "❌ FAIL"
        
        # HTML Code (เขียนบรรทัดเดียว ไม่ต้องย่อหน้า)
        html = f"<div style='margin: 10px 0px; padding: 10px; background-color: #f0f2f6; border-radius: 5px; border-left: 5px solid {color};'><strong>Check {label}:</strong> {demand:.2f} / {capacity:.2f} = <strong>{ratio:.2f}</strong> &nbsp; <span style='color:{color}; font-weight:bold'>[{icon}]</span></div>"
        lines.append(html)
        lines.append("")

    # --- 1. Setup Parameters ---
    if is_lrfd:
        method_str = "LRFD"
        f_v, f_y, f_r, f_w = 0.75, 0.90, 0.75, 0.75
        kv_sym = "\\phi R_n"
    else:
        method_str = "ASD"
        f_v, f_y, f_r, f_w = 1/2.0, 1/1.5, 1/2.0, 1/2.0
        kv_sym = "R_n / \\Omega"

    d = bolts['d']; h_hole = d + 2
    n_rows = bolts['rows']; n_cols = bolts['cols']
    t_pl = plate['t']; h_pl = plate['h']
    Fy_pl = plate['Fy']; Fu_pl = plate['Fu']
    t_web = beam['tw']; Fu_beam = beam['Fu']
    Fnv = bolts['Fnv']; w_sz = plate['weld_size']

    # --- 2. Build Report ---
    lines.append(f"### Calculation Report ({method_str})")
    lines.append("---")

    # Analysis
    x_bar = ((n_cols - 1) * bolts.get('s_h',0)) / 2 if n_cols > 1 else 0
    eccentricity = plate['e1'] + x_bar
    sum_r2 = 0; crit_x, crit_y = 0, 0
    row_start = -((n_rows - 1) * bolts['s_v']) / 2; col_start = -x_bar
    
    for c in range(n_cols):
        for r in range(n_rows):
            dx = col_start + (c * bolts.get('s_h',0)); dy = row_start + (r * bolts['s_v'])
            r_sq = dx**2 + dy**2
            sum_r2 += r_sq
            if r_sq >= (crit_x**2 + crit_y**2): crit_x, crit_y = abs(dx), abs(dy)

    tex_J = f"J = \\sum (x^2 + y^2) = {sum_r2:,.0f} \\text{{ mm}}^2"
    add_latex("Polar Moment of Inertia", tex_J)

    # Force
    Mu_mm = V_load * eccentricity
    Rv_direct = V_load / (n_rows * n_cols)
    Rv_moment = (Mu_mm * crit_x) / sum_r2 if sum_r2 > 0 else 0
    Rh_moment = (Mu_mm * crit_y) / sum_r2 if sum_r2 > 0 else 0
    V_res = math.sqrt((Rv_direct + Rv_moment)**2 + Rh_moment**2)

    tex_force = f"""
    \\begin{{aligned}}
    R_{{vx}} &= {Rh_moment:.2f} \\text{{ kN}} \\\\
    R_{{vy}} &= {(Rv_direct+Rv_moment):.2f} \\text{{ kN}} \\\\
    V_r &= \\mathbf{{{V_res:.2f}}} \\text{{ kN}}
    \\end{{aligned}}
    """
    add_latex("Force Demand", tex_force)

    lines.append("---")
    lines.append("### Capacity Checks")

    # Bolt Shear
    Ab = (math.pi * d**2) / 4
    cap_bolt = (Fnv * Ab / 1000.0) * f_v
    add_latex("Bolt Shear Strength", f"{kv_sym} = {cap_bolt:.2f} \\text{{ kN}}")
    add_html_bar("Bolt Shear", V_res, cap_bolt)

    # Weld
    L_weld = h_pl * 2
    cap_weld = (0.6 * 480 * 0.707 * w_sz * L_weld / 1000.0) * f_w
    add_latex("Weld Strength", f"{kv_sym} = {cap_weld:.2f} \\text{{ kN}}")
    add_html_bar("Weld", V_load, cap_weld)

    return "\n".join(lines)
