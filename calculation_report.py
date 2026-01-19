# calculation_report.py
import math

def generate_report(V_load, T_load, beam, plate, bolts, cope, is_lrfd=True, material_grade="A36", bolt_grade="A325"):
    
    # ==========================================
    # 1. Helper Functions
    # ==========================================
    lines = []

    def add_header(text):
        lines.append(f"\n### {text}\n")

    def add_sub_header(text):
        lines.append(f"\n#### {text}\n")

    def add_latex(symbol, eq_text, sub_text, result, unit, is_pass=None):
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
        
        if is_pass is not None:
             status = "✅ OK" if is_pass else "❌ FAIL"
             color = "green" if is_pass else "red"
             lines.append(f"<span style='color:{color}; font-weight:bold'>{status}</span>")
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
    # 2. Setup Parameters & Constants
    # ==========================================
    if is_lrfd:
        method_str = "LRFD"
        f_v, f_y, f_r, f_w, f_b = 0.75, 0.90, 0.75, 0.75, 0.75
        kv_sym = "\\phi R_n"
        fmt_phi = lambda t: "0.75" if t in ['v','r','w','b'] else "0.90"
    else:
        method_str = "ASD" # Simple ASD conversion for display
        f_v, f_y, f_r, f_w, f_b = 0.50, 0.60, 0.50, 0.50, 0.50 
        kv_sym = "R_n / \\Omega"
        fmt_phi = lambda t: "\\Omega"

    # Unpack Data
    d = bolts['d']; h_hole = d + 2
    n_rows = bolts['rows']; n_cols = bolts['cols']
    n_total = n_rows * n_cols
    s_v = bolts['s_v']; s_h = bolts.get('s_h', 0)
    Fnv = bolts['Fnv']
    Fnt = bolts.get('Fnt', Fnv * 1.3) # Approx Fnt if not sent

    # Plate
    t_pl = plate['t']; h_pl = plate['h']
    w_pl = plate.get('w', 0)
    Fy_pl = plate['Fy']; Fu_pl = plate['Fu']
    e1 = plate.get('e1', 0); lv = plate.get('lv', 0)

    # Beam (Web)
    t_web = beam['tw']
    Fy_beam = beam.get('Fy', 250) # Default A36
    Fu_beam = beam['Fu']
    
    # Cope Data
    has_cope = cope['has_cope']
    dc = cope['dc'] # Cope Depth
    c_len = cope['c'] # Cope Length

    # ==========================================
    # 3. Report Header
    # ==========================================
    lines.append(f"# 🏗️ Advanced Connection Report ({method_str})")
    lines.append("---")
    
    lines.append("#### 📐 Design Loads")
    lines.append(f"- **Shear ($V_u$):** {V_load:.2f} kN")
    lines.append(f"- **Axial Tension ($T_u$):** {T_load:.2f} kN")
    
    lines.append("\n#### 🧱 Geometry Check")
    if has_cope:
        lines.append(f"- **Coped Beam:** Depth $d_c={dc}$ mm, Length $c={c_len}$ mm")
    else:
        lines.append("- **Coped Beam:** No (Uncoped)")
        
    lines.append(f"- **Plate:** {h_pl}x{w_pl}x{t_pl} mm ({material_grade})")
    lines.append(f"- **Bolts:** {n_total} x M{d} ({bolt_grade})")
    lines.append("---")

    # ==========================================
    # 4. Analysis: Bolt Forces
    # ==========================================
    add_header("1. Force Analysis (Eccentric + Tension)")
    
    # 1. Shear per Bolt (Elastic Method for Eccentricity)
    x_bar = ((n_cols - 1) * s_h) / 2 if n_cols > 1 else 0
    eccentricity = e1 + x_bar
    Mu_mm = V_load * eccentricity
    
    sum_r2 = 0; crit_x, crit_y = 0, 0
    row_start = -((n_rows - 1) * s_v) / 2
    col_start = -x_bar
    
    for c in range(n_cols):
        for r in range(n_rows):
            dx = col_start + (c * s_h); dy = row_start + (r * s_v)
            r_sq = dx**2 + dy**2
            sum_r2 += r_sq
            if r_sq >= (crit_x**2 + crit_y**2): crit_x, crit_y = abs(dx), abs(dy)

    Rv_direct = V_load / n_total
    Rv_moment = (Mu_mm * crit_x) / sum_r2 if sum_r2 > 0 else 0
    Rh_moment = (Mu_mm * crit_y) / sum_r2 if sum_r2 > 0 else 0
    
    V_res_bolt = math.sqrt((Rv_direct + Rv_moment)**2 + Rh_moment**2) # Resultant Shear
    T_res_bolt = T_load / n_total # Tension per bolt

    lines.append(f"- Eccentricity $e = {eccentricity:.1f}$ mm")
    lines.append(f"- Resultant Shear per Bolt ($V_{{ub}}$): **{V_res_bolt:.2f} kN**")
    lines.append(f"- Tension per Bolt ($T_{{ub}}$): **{T_res_bolt:.2f} kN**")

    # ==========================================
    # 5. Capacity Checks
    # ==========================================
    lines.append("---")
    add_header("2. Capacity Checks")

    # ------------------------------------------
    # 2.1 Bolt Interaction (Shear + Tension)
    # ------------------------------------------
    add_sub_header("2.1 Bolt Interaction (Shear + Tension)")
    Ab = (math.pi * d**2) / 4
    
    # Shear Capacity
    Rn_v = Fnv * Ab / 1000.0; cap_v = Rn_v * f_v
    
    # Tension Capacity (Modified by Shear stress)
    if T_load > 0:
        # AISC Interaction: F'nt = 1.3Fnt - (Fnt/phi*Fnv)*fv <= Fnt
        fv = (V_res_bolt * 1000) / Ab # MPa
        # Stress limit check
        limit_Fnt = Fnt
        mod_Fnt = 1.3 * Fnt - (Fnt / (f_v * Fnv)) * fv
        Fnt_prime = min(max(mod_Fnt, 0), limit_Fnt)
        
        Rn_t = Fnt_prime * Ab / 1000.0
        cap_t = Rn_t * f_v # Note: Phi for tension in bolts is usually same as shear (0.75)
        
        lines.append(f"Shear Stress $f_v = {fv:.1f}$ MPa")
        add_latex(f"F'_{{nt}}", "1.3F_{nt} - \\frac{F_{nt}}{\\phi F_{nv}} f_v", 
                  f"\\min({mod_Fnt:.1f}, {limit_Fnt})", Fnt_prime, "MPa")
        
        add_html_bar("Bolt Tension (Combined)", T_res_bolt, cap_t)
        
        # Check Prying Action (Simplified)
        add_sub_header("2.1.1 Prying Action Check")
        # Simplified AISC check: t_req to eliminate prying
        # b_prime approx distance from bolt center to face of web/weld
        # Assume b_prime = e1 - weld_size - (bolt_dia/2) approx? Or just e1/2
        b_prime = 35 # Assumed generic lever arm for prying
        try:
            p = s_v / n_rows # Tributary length per bolt
            t_req_prying = math.sqrt((4.44 * T_res_bolt * 1000 * b_prime) / (p * Fy_pl))
            
            lines.append(f"Approx. required thickness to ignore prying ($t_{{req}}$):")
            lines.append(f"$$ t_{{req}} = \\sqrt{{\\frac{{4.44 T_{{ub}} b'}}{{p F_y}}}} = {t_req_prying:.2f} \\text{{ mm}} $$")
            
            if t_pl < t_req_prying:
                lines.append(f"⚠️ **Warning:** Plate thickness ({t_pl} mm) < {t_req_prying:.2f} mm. **Prying forces exist!**")
                lines.append("Bolt tension capacity should be reduced or plate thickened.")
                # Reduce Cap T artificially for warning
                cap_t = cap_t * 0.7 
                add_html_bar("Bolt Tension (w/ Prying Penalty)", T_res_bolt, cap_t)
            else:
                 lines.append("✅ **OK:** Plate is thick enough. Prying action is negligible.")

    else:
        # Pure Shear
        add_latex(kv_sym, f"{fmt_phi('v')} F_{{nv}} A_b", f"{fmt_phi('v')} ({Fnv}) ({Ab:.1f})/1000", cap_v, "kN")
        add_html_bar("Bolt Shear", V_res_bolt, cap_v)

    # ------------------------------------------
    # 2.2 Beam Side Checks (Coped Beam)
    # ------------------------------------------
    add_sub_header("2.2 Beam Web Checks (Critical for Coped Beam)")
    
    # 1. Bearing on Beam Web
    Rn_br_wb = (2.4 * d * t_web * Fu_beam) / 1000.0; cap_br_wb = Rn_br_wb * f_b
    add_html_bar("Beam Web Bearing", V_res_bolt, cap_br_wb)

    if has_cope:
        lines.append("**[Coped Beam Analysis]**")
        
        # 2. Block Shear on Beam Web
        # Area definitions specific to Beam Web
        # Agv: Shear area along the bolts
        # Anv: Net shear area
        # Ant: Net tension area (horizontal from last bolt to end of beam)
        
        # Geometry for Beam Web Block Shear
        # Top edge distance on beam = dc + (something). 
        # Actually, for coped beam, the failure path is usually block shear L-shape.
        
        # Let's assume standard Block Shear Path on the Web
        # Top of web is now lower.
        ev_beam = lv # Assume same vertical edge dist as plate for simplicity or user input
        eh_beam = 40 # Standard end distance on beam
        
        Agv_bm = (ev_beam + (n_rows-1)*s_v) * t_web
        Anv_bm = (Agv_bm/t_web - (n_rows-0.5)*h_hole) * t_web
        Ant_bm = (eh_beam - 0.5*h_hole) * t_web
        
        Rn_blk_1 = (0.6 * Fu_beam * Anv_bm + 1.0 * Fu_beam * Ant_bm) / 1000.0
        Rn_blk_2 = (0.6 * Fy_beam * Agv_bm + 1.0 * Fu_beam * Ant_bm) / 1000.0
        cap_blk_bm = min(Rn_blk_1, Rn_blk_2) * f_r
        
        add_latex(kv_sym + "_{BS}", "\\text{Block Shear (Beam Web)}", 
                  f"\\min({Rn_blk_1:.1f}, {Rn_blk_2:.1f}) \\times {fmt_phi('r')}", cap_blk_bm, "kN")
        add_html_bar("Beam Web Block Shear", V_load, cap_blk_bm)
        
        # 3. Shear Yielding of Coped Area
        # Reduced web depth = Total Depth - dc (Approx calculation)
        # Using a simplified check for Shear on Net Section of Web
        h_remain = (n_rows * s_v + 2*lv) # Approximate remaining web height engaging
        Rn_yld_web = 0.6 * Fy_beam * (h_remain * t_web) / 1000.0
        cap_yld_web = Rn_yld_web * f_y
        
        lines.append(f"Remaining Web Depth approx: {h_remain} mm")
        add_html_bar("Coped Web Shear Yield", V_load, cap_yld_web)
        
    else:
        lines.append("Beam is uncoped. Web checks usually governed by bearing.")

    # ------------------------------------------
    # 2.3 Plate Checks (Standard)
    # ------------------------------------------
    add_sub_header("2.3 Plate Capacity")
    
    # Yield
    Ag_pl = h_pl * t_pl
    cap_yld_pl = (0.6 * Fy_pl * Ag_pl / 1000.0) * f_y
    add_html_bar("Plate Shear Yield", V_load, cap_yld_pl)
    
    # Rupture
    An_pl = (h_pl - (n_rows * h_hole)) * t_pl
    cap_rup_pl = (0.6 * Fu_pl * An_pl / 1000.0) * f_r
    add_html_bar("Plate Shear Rupture", V_load, cap_rup_pl)

    # Block Shear Plate
    l_side = plate['l_side']
    Agv_pl = (lv + (n_rows - 1) * s_v) * t_pl
    Anv_pl = (Agv_pl/t_pl - (n_rows - 0.5) * h_hole) * t_pl
    Ant_pl = (l_side - 0.5 * h_hole) * t_pl
    
    Rn_blk_pl1 = (0.6 * Fu_pl * Anv_pl + 1.0 * Fu_pl * Ant_pl) / 1000.0
    Rn_blk_pl2 = (0.6 * Fy_pl * Agv_pl + 1.0 * Fu_pl * Ant_pl) / 1000.0
    cap_blk_pl = min(Rn_blk_pl1, Rn_blk_pl2) * f_r
    add_html_bar("Plate Block Shear", V_load, cap_blk_pl)
    
    # Weld
    w_sz = plate['weld_size']
    L_weld = h_pl * 2
    cap_weld = (0.6 * 480 * 0.707 * w_sz * L_weld / 1000.0) * f_w
    add_html_bar("Weld Strength", math.sqrt(V_load**2 + T_load**2), cap_weld) # Resultant load for weld

    return "\n".join(lines)
