# calculation_report.py
import math

def generate_report(V_load, beam, plate, bolts, is_lrfd=True, material_grade="A36", bolt_grade="A325"):
    
    # ==========================================
    # 1. Helper Functions
    # ==========================================
    lines = []

    def add_header(text):
        lines.append(f"\n### {text}\n")

    def add_sub_header(text):
        lines.append(f"\n#### {text}\n")

    def add_latex(symbol, eq_text, sub_text, result, unit):
        lines.append(f"**{symbol}**")
        lines.append("")      
        lines.append("$$")    
        lines.append("\\begin{aligned}")
        lines.append(f"{symbol} &= {eq_text} \\\\")
        
        if sub_text:
            lines.append(f"&= {sub_text} \\\\")
            
        lines.append(f"&= \\mathbf{{{result:,.2f}}} \\text{{ {unit} }}")
        lines.append("\\end{aligned}")
        lines.append("$$")    
        lines.append("")      

    def add_html_bar(label, demand, capacity):
        if capacity == 0: ratio = 999.0
        else: ratio = demand / capacity
        
        color = "#15803d" if ratio <= 1.0 else "#b91c1c" 
        icon = "✅ PASS" if ratio <= 1.0 else "❌ FAIL"
        
        html_code = f"<div style='margin:10px 0px; padding:10px; background-color:#f0f2f6; border-radius:5px; border-left:5px solid {color};'><strong>Check {label}:</strong> {demand:.2f} / {capacity:.2f} = <strong>{ratio:.2f}</strong> &nbsp; <span style='color:{color}; font-weight:bold'>[{icon}]</span></div>"
        lines.append(html_code)
        lines.append("")

    # ==========================================
    # 2. Setup Parameters
    # ==========================================
    if is_lrfd:
        method_str = "LRFD"
        f_v, f_y, f_r, f_w = 0.75, 0.90, 0.75, 0.75
        kv_sym = "\\phi R_n"
        fmt_phi = lambda t: "0.75" if t in ['v','r','w'] else "0.90"
    else:
        method_str = "ASD"
        f_v, f_y, f_r, f_w = 1/2.0, 1/1.5, 1/2.0, 1/2.0
        kv_sym = "R_n / \\Omega"
        fmt_phi = lambda t: "1/2.00" if t in ['v','r','w'] else "1/1.50"

    # Unpack Data
    d = bolts['d']; h_hole = d + 2
    n_rows = bolts['rows']; n_cols = bolts['cols']
    s_v = bolts['s_v']; s_h = bolts.get('s_h', 0)
    
    # Plate & Dimensions
    t_pl = plate['t']; h_pl = plate['h']
    w_pl = plate.get('w', 0) # [NEW] รับค่า width
    Fy_pl = plate['Fy']; Fu_pl = plate['Fu']
    
    # Edge Distances
    e1 = plate.get('e1', 0)
    lv = plate.get('lv', 0)
    l_side = plate.get('l_side', 0) # This is leh

    t_web = beam['tw']; Fu_beam = beam['Fu']
    Fnv = bolts['Fnv']
    w_sz = plate['weld_size']

    # ==========================================
    # 3. Build Report Content
    # ==========================================
    
    # --- Header Summary ---
    lines.append(f"# 📐 Calculation Report ({method_str})")
    lines.append("---")
    
    # [NEW] แสดงขนาด Plate และระยะต่างๆ ให้ครบ
    lines.append("#### 🧱 Geometry & Material Summary")
    lines.append(f"- **Plate Size ($H \\times W \\times t$):** {h_pl:.0f} x {w_pl:.0f} x {t_pl:.0f} mm")
    lines.append(f"- **Bolt Config:** M{d} (Grade {bolt_grade}), {n_rows} Rows x {n_cols} Cols")
    lines.append(f"- **Detailing:** Pitch $s_v={s_v}$, Gauge $s_h={s_h}$ mm")
    lines.append(f"- **Edges:** Top/Bot $l_v={lv}$, Horizontal $l_h={l_side}$, $e_1={e1}$ mm")
    lines.append(f"- **Weld Size:** {w_sz} mm (E70XX)")
    lines.append(f"- **Design Load ($V_u$):** {V_load:.2f} kN")
    lines.append("---")

    # --- 1. Analysis ---
    add_header("1. Bolt Group Analysis")
    
    # Geometric Properties
    x_bar = ((n_cols - 1) * s_h) / 2 if n_cols > 1 else 0
    eccentricity = e1 + x_bar
    Mu_mm = V_load * eccentricity
    
    sum_r2 = 0
    crit_x, crit_y = 0, 0
    row_start = -((n_rows - 1) * s_v) / 2
    col_start = -x_bar
    
    for c in range(n_cols):
        for r in range(n_rows):
            dx = col_start + (c * s_h); dy = row_start + (r * s_v)
            r_sq = dx**2 + dy**2
            sum_r2 += r_sq
            if r_sq >= (crit_x**2 + crit_y**2): crit_x, crit_y = abs(dx), abs(dy)

    lines.append(f"Eccentricity $e = e_1 + x_{{bar}} = {e1:.1f} + {x_bar:.1f} = {eccentricity:.1f}$ mm")
    add_latex("J", "\\sum (x^2 + y^2)", None, sum_r2, "mm^2")

    # Force Demand
    Rv_direct = V_load / (n_rows * n_cols)
    Rv_moment = (Mu_mm * crit_x) / sum_r2 if sum_r2 > 0 else 0
    Rh_moment = (Mu_mm * crit_y) / sum_r2 if sum_r2 > 0 else 0
    V_res = math.sqrt((Rv_direct + Rv_moment)**2 + Rh_moment**2)
    
    add_sub_header("Force Demand on Critical Bolt")
    lines.append(f"Critical Bolt at: $(x,y) = ({crit_x:.1f}, {crit_y:.1f})$")
    
    lines.append("$$")
    lines.append("\\begin{aligned}")
    lines.append(f"R_{{vx}} &= {Rh_moment:.2f} \\text{{ kN}} \\\\")
    lines.append(f"R_{{vy}} &= {Rv_direct:.2f} + {Rv_moment:.2f} = {(Rv_direct+Rv_moment):.2f} \\text{{ kN}} \\\\")
    lines.append(f"V_r &= \\sqrt{{{Rh_moment:.2f}^2 + {(Rv_direct+Rv_moment):.2f}^2}} = \\mathbf{{{V_res:.2f}}} \\text{{ kN}}")
    lines.append("\\end{aligned}")
    lines.append("$$")

    # --- 2. Checks ---
    lines.append("---")
    add_header("2. Capacity Checks")

    # 2.1 Bolt Shear
    add_sub_header("2.1 Bolt Shear Strength")
    Ab = (math.pi * d**2) / 4
    cap_bolt = (Fnv * Ab / 1000.0) * f_v
    add_latex(kv_sym, f"{fmt_phi('v')} F_{{nv}} A_b", f"{fmt_phi('v')} ({Fnv}) ({Ab:.1f})/1000", cap_bolt, "kN")
    add_html_bar("Bolt Shear", V_res, cap_bolt)

    # 2.2 Bearing (Plate & Web)
    add_sub_header("2.2 Bearing Strength")
    Rn_br_pl = (2.4 * d * t_pl * Fu_pl) / 1000.0; cap_br_pl = Rn_br_pl * f_v
    Rn_br_wb = (2.4 * d * t_web * Fu_beam) / 1000.0; cap_br_wb = Rn_br_wb * f_v
    cap_br_min = min(cap_br_pl, cap_br_wb)

    lines.append(f"- Plate Bearing Capacity: **{cap_br_pl:.2f} kN**")
    lines.append(f"- Web Bearing Capacity: **{cap_br_wb:.2f} kN**")
    lines.append(f"**Governing Capacity:** $\\mathbf{{{cap_br_min:.2f}}}$ **kN**")
    add_html_bar("Bearing", V_res, cap_br_min)

    # 2.3 Yielding
    add_sub_header("2.3 Plate Shear Yielding (Gross)")
    Ag = h_pl * t_pl
    cap_yld = (0.6 * Fy_pl * Ag / 1000.0) * f_y
    add_latex(kv_sym, f"{fmt_phi('y')} 0.6 F_y A_g", f"{fmt_phi('y')} (0.6) ({Fy_pl}) ({Ag:.0f})/1000", cap_yld, "kN")
    add_html_bar("Yielding", V_load, cap_yld)

    # 2.4 Rupture
    add_sub_header("2.4 Plate Shear Rupture (Net)")
    An = (h_pl - (n_rows * h_hole)) * t_pl
    cap_rup = (0.6 * Fu_pl * An / 1000.0) * f_r
    add_latex(kv_sym, f"{fmt_phi('r')} 0.6 F_u A_n", f"{fmt_phi('r')} (0.6) ({Fu_pl}) ({An:.0f})/1000", cap_rup, "kN")
    add_html_bar("Rupture", V_load, cap_rup)

    # 2.5 Block Shear
    add_sub_header("2.5 Block Shear Strength")
    lv_val, leh_val = lv, l_side
    Agv = (lv_val + (n_rows - 1) * s_v) * t_pl
    Anv = (Agv/t_pl - (n_rows - 0.5) * h_hole) * t_pl
    Ant = (leh_val - 0.5 * h_hole) * t_pl
    
    Rn_blk_1 = (0.6 * Fu_pl * Anv + 1.0 * Fu_pl * Ant) / 1000.0
    Rn_blk_2 = (0.6 * Fy_pl * Agv + 1.0 * Fu_pl * Ant) / 1000.0
    Rn_blk = min(Rn_blk_1, Rn_blk_2)
    cap_blk = Rn_blk * f_r

    lines.append(f"Areas: $A_{{gv}}={Agv:.0f}, A_{{nv}}={Anv:.0f}, A_{{nt}}={Ant:.0f}$ mm²")
    add_latex(kv_sym, "\\min(R_{n1}, R_{n2})", f"{fmt_phi('r')} \\min({Rn_blk_1:.1f}, {Rn_blk_2:.1f})", cap_blk, "kN")
    add_html_bar("Block Shear", V_load, cap_blk)

    # 2.6 Weld
    add_sub_header("2.6 Weld Strength")
    L_weld = h_pl * 2
    cap_weld = (0.6 * 480 * 0.707 * w_sz * L_weld / 1000.0) * f_w
    add_latex(kv_sym, f"{fmt_phi('w')} 0.6 F_{{exx}} (0.707 w) L", f"{fmt_phi('w')} ... ({L_weld:.0f})", cap_weld, "kN")
    add_html_bar("Weld", V_load, cap_weld)

    return "\n".join(lines)
