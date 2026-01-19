import math

def generate_report(V_load, beam, plate, bolts, is_lrfd=True, material_grade="A36", bolt_grade="A325"):
    
    lines = []

    # ฟังก์ชันช่วย: สร้างสมการแบบบังคับ $$ เสมอ
    def add_latex(title, math_content):
        lines.append(f"**{title}**")
        # บังคับขึ้นบรรทัดใหม่ ใส่ $$ ครอบเนื้อหา แล้วปิดท้ายด้วย $$
        lines.append("\n$$") 
        lines.append(math_content)
        lines.append("$$\n")

    # ฟังก์ชันช่วย: สร้างแถบสี HTML
    def add_html_bar(label, demand, capacity):
        if capacity == 0: ratio = 999.0
        else: ratio = demand / capacity
        
        color = "#15803d" if ratio <= 1.0 else "#b91c1c" # เขียว/แดง
        icon = "✅ PASS" if ratio <= 1.0 else "❌ FAIL"
        
        # HTML บรรทัดเดียว
        html = f"""<div style='margin: 10px 0px; padding: 10px; background-color: #f0f2f6; border-radius: 5px; border-left: 5px solid {color};'><strong>Check {label}:</strong> {demand:.2f} / {capacity:.2f} = <strong>{ratio:.2f}</strong> &nbsp; <span style='color:{color}; font-weight:bold'>[{icon}]</span></div>"""
        lines.append(html)

    # --- 1. เตรียมตัวแปร (เหมือนเดิม) ---
    if is_lrfd:
        f_v, f_y, f_r, f_w = 0.75, 0.90, 0.75, 0.75
        kv_sym = "\\phi R_n"
    else:
        f_v, f_y, f_r, f_w = 1/2.0, 1/1.5, 1/2.0, 1/2.0
        kv_sym = "R_n / \\Omega"

    d = bolts['d']; h_hole = d + 2
    n_rows = bolts['rows']; n_cols = bolts['cols']
    s_v = bolts['s_v']; s_h = bolts.get('s_h', 0)
    t_pl = plate['t']; h_pl = plate['h']
    Fy_pl = plate['Fy']; Fu_pl = plate['Fu']
    t_web = beam['tw']; Fu_beam = beam['Fu']
    Fnv = bolts['Fnv']; w_sz = plate['weld_size']

    # --- 2. เขียนรายงาน ---
    lines.append(f"### Calculation Report")
    lines.append("---")

    # คำนวณ Inertia
    x_bar = ((n_cols - 1) * s_h) / 2 if n_cols > 1 else 0
    e_dist = plate['e1']; eccentricity = e_dist + x_bar
    sum_r2 = 0; crit_x, crit_y = 0, 0
    row_start = -((n_rows - 1) * s_v) / 2; col_start = -x_bar
    
    for c in range(n_cols):
        for r in range(n_rows):
            dx = col_start + (c * s_h); dy = row_start + (r * s_v)
            r_sq = dx**2 + dy**2
            sum_r2 += r_sq
            if r_sq >= (crit_x**2 + crit_y**2): crit_x, crit_y = abs(dx), abs(dy)

    # จุดที่แก้: ใส่ string ของ LaTeX เพียวๆ แล้วให้ฟังก์ชัน add_latex ครอบ $$ ให้
    latex_J = f"""
    \\begin{{aligned}} 
    J &= \\sum (x^2 + y^2) \\\\ 
    &= {sum_r2:,.0f} \\text{{ mm}}^2 
    \\end{{aligned}}
    """
    add_latex("Polar Moment of Inertia", latex_J)

    # คำนวณ Force
    Mu_mm = V_load * eccentricity
    Rv_direct = V_load / (n_rows * n_cols)
    Rv_moment = (Mu_mm * crit_x) / sum_r2 if sum_r2 > 0 else 0
    Rh_moment = (Mu_mm * crit_y) / sum_r2 if sum_r2 > 0 else 0
    V_res = math.sqrt((Rv_direct + Rv_moment)**2 + Rh_moment**2)

    latex_force = f"""
    \\begin{{aligned}}
    R_{{vx}} &= {Rh_moment:.2f} \\text{{ kN}} \\\\
    R_{{vy}} &= {Rv_direct:.2f} + {Rv_moment:.2f} = {(Rv_direct+Rv_moment):.2f} \\text{{ kN}} \\\\
    V_r &= \\sqrt{{{Rh_moment:.2f}^2 + {(Rv_direct+Rv_moment):.2f}^2}} = \\mathbf{{{V_res:.2f}}} \\text{{ kN}}
    \\end{{aligned}}
    """
    add_latex("Force Demand on Critical Bolt", latex_force)

    # Checks
    lines.append("---")
    lines.append("### Capacity Checks")

    # Bolt Shear
    Ab = (math.pi * d**2) / 4; Rn_bolt = (Fnv * Ab)/1000; cap_bolt = Rn_bolt * f_v
    latex_bolt = f"{kv_sym} = {cap_bolt:.2f} \\text{{ kN}}"
    add_latex("Bolt Shear Strength", latex_bolt)
    add_html_bar("Bolt Shear", V_res, cap_bolt)

    # Weld
    L_weld = h_pl * 2; Rn_weld = (0.6 * 480 * 0.707 * w_sz * L_weld)/1000; cap_weld = Rn_weld * f_w
    latex_weld = f"{kv_sym} = {cap_weld:.2f} \\text{{ kN}}"
    add_latex("Weld Strength", latex_weld)
    add_html_bar("Weld", V_load, cap_weld)

    return "\n".join(lines)
