import math

def generate_report(V_load, beam, plate, bolts, is_lrfd=True, material_grade="A36", bolt_grade="A325"):
    """
    สร้างรายงานคำนวณแบบละเอียด (Step-by-Step Calculation Note)
    """
    
    # =================================================================================
    # 1. PREPARE DATA & CONSTANTS
    # =================================================================================
    
    # --- Factors (AISC 360-16) ---
    if is_lrfd:
        method_txt = "LRFD (Load and Resistance Factor Design)"
        phi_v = 0.75  # Bolts
        phi_y = 0.90  # Yielding
        phi_r = 0.75  # Rupture
        phi_w = 0.75  # Weld
        
        # Helper to format LRFD Equation
        def render_eq(symbol, formula, sub_str, res_val, unit="kN"):
            return f"""
**{symbol}** (Ref: AISC):
$$ {formula} $$
$$ = {sub_str} $$
$$ = \\mathbf{{{res_val:.2f}}} \\text{{ {unit} }} $$
"""
        factor_label = r"\phi"
        factor_val_v = phi_v
    else:
        method_txt = "ASD (Allowable Strength Design)"
        om_v = 2.00
        om_y = 1.50
        om_r = 2.00
        om_w = 2.00
        
        # Helper to format ASD Equation
        def render_eq(symbol, formula, sub_str, res_val, unit="kN"):
            return f"""
**{symbol}** (Ref: AISC):
$$ {formula} $$
$$ = {sub_str} $$
$$ = \\mathbf{{{res_val:.2f}}} \\text{{ {unit} }} $$
"""
        factor_label = r"\Omega"
        factor_val_v = 1.0/om_v # Just for calculation logic

    # --- Geometry & Materials ---
    d = bolts['d']
    h_hole = d + 2 # Standard hole size
    n_rows = bolts['rows']
    n_cols = bolts['cols']
    n_total = n_rows * n_cols
    s_v = bolts['s_v']
    s_h = bolts.get('s_h', 0)
    
    t_pl = plate['t']
    h_pl = plate['h']
    Fy_pl = plate['Fy']
    Fu_pl = plate['Fu']
    
    # Beam Web Data (for Bearing check)
    t_web = beam['tw']
    Fu_beam = beam['Fu']
    
    Fnv = bolts['Fnv']
    
    # =================================================================================
    # 2. PERFORM CALCULATIONS
    # =================================================================================

    # --- 2.1 Bolt Shear (Elastic Method) ---
    Ab = (math.pi * d**2) / 4
    
    # Centroid Calculation
    if n_cols > 1: x_bar = ((n_cols - 1) * s_h) / 2
    else: x_bar = 0
    y_bar = ((n_rows - 1) * s_v) / 2 # Local coordinate center

    # Eccentricity
    e_dist = plate['e1'] # Distance from weld to first bolt line
    eccentricity = e_dist + x_bar
    Mu = V_load * eccentricity / 1000.0 # kN-m -> Used for reference
    Mu_mm = V_load * eccentricity       # kN-mm
    
    # Polar Moment of Inertia (J) - sum(x^2 + y^2)
    sum_r2 = 0
    crit_x, crit_y = 0, 0
    
    # Loop to find J and Critical Bolt Coordinates (relative to centroid)
    row_start = -((n_rows - 1) * s_v) / 2
    col_start = -x_bar
    
    for c in range(n_cols):
        for r in range(n_rows):
            dx = col_start + (c * s_h)
            dy = row_start + (r * s_v)
            sum_r2 += (dx**2 + dy**2)
            # Critical bolt is the furthest one (Top-Right usually)
            if (dx**2 + dy**2) >= (crit_x**2 + crit_y**2):
                crit_x, crit_y = abs(dx), abs(dy)
    
    # Forces on Critical Bolt
    # 1. Direct Shear
    Rv_direct = V_load / n_total
    
    # 2. Torsional Shear (Elastic)
    # F = M * r / J  => Fx = M*y/J, Fy = M*x/J
    if sum_r2 > 0:
        Rv_moment = (Mu_mm * crit_x) / sum_r2 # Vertical Component
        Rh_moment = (Mu_mm * crit_y) / sum_r2 # Horizontal Component
    else:
        Rv_moment, Rh_moment = 0, 0
        
    R_total_v = Rv_direct + Rv_moment
    R_total_h = Rh_moment
    V_resultant = math.sqrt(R_total_v**2 + R_total_h**2)
    
    # Capacity: Bolt Shear
    Rn_bolt_nom = (Fnv * Ab) / 1000.0 # kN
    if is_lrfd:
        cap_bolt = phi_v * Rn_bolt_nom
        txt_bolt_eq = r"\phi R_n = \phi F_{nv} A_b"
        txt_bolt_sub = f"{phi_v} \\times {Fnv} \\times {Ab:.2f}/1000"
    else:
        cap_bolt = Rn_bolt_nom / om_v
        txt_bolt_eq = r"R_n / \Omega = (F_{nv} A_b) / \Omega"
        txt_bolt_sub = f"({Fnv} \\times {Ab:.2f}/1000) / {om_v}"

    # --- 2.2 Bolt Bearing (J3.10) ---
    # Check both Plate and Beam Web
    # Formula: Rn = 1.2 Lc t Fu <= 2.4 d t Fu (Simplified to 2.4dtFu for this report or user standard)
    # Using 2.4 d t Fu (Tearout not checked explicitly in this simplified version, assuming spacing is adequate)
    
    # Plate Bearing
    Rn_bear_pl_nom = (2.4 * d * t_pl * Fu_pl) / 1000.0
    # Beam Web Bearing
    Rn_bear_web_nom = (2.4 * d * t_web * Fu_beam) / 1000.0
    
    if is_lrfd:
        cap_bear_pl = phi_v * Rn_bear_pl_nom
        cap_bear_web = phi_v * Rn_bear_web_nom
        bear_factor = phi_v
        bear_factor_txt = r"\phi"
    else:
        cap_bear_pl = Rn_bear_pl_nom / om_v
        cap_bear_web = Rn_bear_web_nom / om_v
        bear_factor = 1.0/om_v
        bear_factor_txt = r"1/\Omega"

    cap_bear_min = min(cap_bear_pl, cap_bear_web)
    
    # --- 2.3 Plate Yielding (J4.2) ---
    Ag = h_pl * t_pl
    Rn_yld_nom = (0.60 * Fy_pl * Ag) / 1000.0
    
    if is_lrfd:
        cap_yld = phi_y * Rn_yld_nom
        txt_yld_eq = r"\phi R_n = \phi (0.60 F_y A_g)"
        txt_yld_sub = f"{phi_y} \\times 0.60 \\times {Fy_pl} \\times {Ag:.0f}/1000"
    else:
        cap_yld = Rn_yld_nom / om_y
        txt_yld_eq = r"R_n/\Omega = (0.60 F_y A_g)/\Omega"
        txt_yld_sub = f"(0.60 \\times {Fy_pl} \\times {Ag:.0f}/1000) / {om_y}"

    # --- 2.4 Plate Rupture (J4.3) ---
    An = (h_pl - (n_rows * h_hole)) * t_pl
    Rn_rup_nom = (0.60 * Fu_pl * An) / 1000.0
    
    if is_lrfd:
        cap_rup = phi_r * Rn_rup_nom
        txt_rup_eq = r"\phi R_n = \phi (0.60 F_u A_{nv})"
        txt_rup_sub = f"{phi_r} \\times 0.60 \\times {Fu_pl} \\times {An:.0f}/1000"
    else:
        cap_rup = Rn_rup_nom / om_r
        txt_rup_eq = r"R_n/\Omega = (0.60 F_u A_{nv})/\Omega"
        txt_rup_sub = f"(0.60 \\times {Fu_pl} \\times {An:.0f}/1000) / {om_r}"

    # --- 2.5 Block Shear (J4.3) ---
    # Assuming standard pattern: Shear vertical, Tension horizontal
    lv = plate['lv'] # Edge distance vertical
    l_side = plate['l_side'] # Edge horizontal (perp to force)
    
    Agv = (lv + (n_rows - 1) * s_v) * t_pl
    Anv = (Agv/t_pl - (n_rows - 0.5) * h_hole) * t_pl
    Ant = (l_side - 0.5 * h_hole) * t_pl
    
    term1 = 0.6 * Fu_pl * Anv
    term2 = Fu_pl * Ant # Ubs = 1.0 assumed
    
    Rn_blk_1 = (term1 + term2) / 1000.0
    Rn_blk_2 = (0.6 * Fy_pl * Agv + term2) / 1000.0 # Upper limit
    Rn_blk_nom = min(Rn_blk_1, Rn_blk_2)
    
    if is_lrfd:
        cap_blk = phi_r * Rn_blk_nom
        txt_blk_eq = r"\phi R_n = \phi \min [0.6 F_u A_{nv} + U_{bs} F_u A_{nt} \le 0.6 F_y A_{gv} + U_{bs} F_u A_{nt}]"
        txt_blk_sub = f"{phi_r} \\times \\min [{Rn_blk_1:.1f}, {Rn_blk_2:.1f}]"
    else:
        cap_blk = Rn_blk_nom / om_r
        txt_blk_eq = r"R_n/\Omega"
        txt_blk_sub = f"\\min [{Rn_blk_1:.1f}, {Rn_blk_2:.1f}] / {om_r}"

    # --- 2.6 Weld Strength (J2.4) ---
    w_sz = plate['weld_size']
    L_weld = h_pl * 2 # Two sides
    Rn_weld_nom = (0.60 * 480 * 0.707 * w_sz * L_weld) / 1000.0
    
    if is_lrfd:
        cap_weld = phi_w * Rn_weld_nom
        txt_weld_eq = r"\phi R_n = \phi (0.6 F_{exx} (0.707 w) L)"
        txt_weld_sub = f"{phi_w} \\times 0.6 \\times 480 \\times 0.707 \\times {w_sz} \\times {L_weld}/1000"
    else:
        cap_weld = Rn_weld_nom / om_w
        txt_weld_eq = r"R_n/\Omega = (0.6 F_{exx} (0.707 w) L) / \Omega"
        txt_weld_sub = f"(0.6 \\times 480 \\times 0.707 \\times {w_sz} \\times {L_weld}/1000) / {om_w}"

    # =================================================================================
    # 3. GENERATE MARKDOWN REPORT
    # =================================================================================
    
    # Ratios
    r_bolt = V_resultant / cap_bolt
    r_bear = V_resultant / cap_bear_min
    r_yld = V_load / cap_yld
    r_rup = V_load / cap_rup
    r_blk = V_load / cap_blk
    r_weld = V_load / cap_weld
    
    max_ratio = max(r_bolt, r_bear, r_yld, r_rup, r_blk, r_weld)
    status_icon = "✅ PASS" if max_ratio <= 1.0 else "❌ FAIL"
    
    md = []
    
    # Header
    md.append(f"# 📐 Connection Calculation Report")
    md.append(f"**Method:** {method_txt} | **Status:** {status_icon}")
    md.append("---")
    
    # 1. Design Parameters
    md.append("### 1. Design Parameters (ข้อมูลการออกแบบ)")
    col1_txt = f"""
    - **Design Load ($V_u$):** {V_load:.2f} kN
    - **Eccentricity ($e$):** {eccentricity:.1f} mm
    - **Member Grade:** {material_grade}
    """
    col2_txt = f"""
    - **Plate:** {t_pl} mm $\\times$ {h_pl} mm ($F_y={Fy_pl}, F_u={Fu_pl}$)
    - **Beam Web:** {t_web} mm ($F_u={Fu_beam}$)
    - **Bolts:** {bolts['size'] if 'size' in bolts else d}mm {bolt_grade} ({n_rows}R x {n_cols}C)
    """
    md.append(col1_txt + col2_txt)
    md.append("---")
    
    # 2. Bolt Analysis
    md.append("### 2. Bolt Group Analysis (Elastic Method)")
    md.append(f"> _Reference: AISC Manual Part 7, Elastic Method_")
    
    md.append(f"**Geometric Properties:**")
    md.append(f"- Polar Moment of Inertia ($J = \sum r^2$): **{sum_r2:,.0f} mm²**")
    md.append(f"- Critical Bolt Coord: ($x={crit_x:.1f}, y={crit_y:.1f}$)")
    md.append(f"**Force Demand on Critical Bolt:**")
    
    md.append(r"$$ R_{direct} = V_u / n = " + f"{V_load:.2f}/{n_total} = {Rv_direct:.2f} \\text{{ kN}} $$")
    
    if sum_r2 > 0:
        md.append(r"$$ R_{moment,x} = \frac{Pe \cdot y}{J} = " + f"\\frac{{{Mu_mm:.0f} \\cdot {crit_y}}}{{{sum_r2:.0f}}} = {Rh_moment:.2f} \\text{{ kN}} $$")
        md.append(r"$$ R_{moment,y} = \frac{Pe \cdot x}{J} = " + f"\\frac{{{Mu_mm:.0f} \\cdot {crit_x}}}{{{sum_r2:.0f}}} = {Rv_moment:.2f} \\text{{ kN}} $$")
    
    md.append(f"**Resultant Load ($V_{{bolt}}$):**")
    md.append(r"$$ V_{bolt} = \sqrt{(R_{dir} + R_{my})^2 + (R_{mx})^2} = \mathbf{" + f"{V_resultant:.2f}" + r"} \text{ kN} $$")
    
    # 3. Capacity Checks
    md.append("---")
    md.append("### 3. Capacity Checks (ตรวจสอบกำลัง)")

    # 3.1 Bolt Shear
    md.append(f"#### 3.1 Bolt Shear Strength (AISC J3.6)")
    md.append(f"- $F_{{nv}} = {Fnv}$ MPa, $A_b = {Ab:.1f}$ mm²")
    md.append(render_eq("Shear Capacity", txt_bolt_eq, txt_bolt_sub, cap_bolt))
    md.append(f"**Ratio:** ${V_resultant:.2f} / {cap_bolt:.2f} = {r_bolt:.2f}$  " + ("✅" if r_bolt<=1 else "❌"))

    # 3.2 Bearing
    md.append(f"#### 3.2 Bearing Strength (AISC J3.10)")
    md.append(f"> _Considering both Plate ({t_pl}mm) and Beam Web ({t_web}mm)_")
    md.append(f"- Plate Capacity: ${bear_factor_txt} \\times 2.4 d t_{{pl}} F_u = {cap_bear_pl:.2f}$ kN")
    md.append(f"- Web Capacity: ${bear_factor_txt} \\times 2.4 d t_{{w}} F_u = {cap_bear_web:.2f}$ kN")
    md.append(f"**Governing Capacity:** $\\mathbf{{{cap_bear_min:.2f}}}$ **kN**")
    md.append(f"**Ratio:** ${V_resultant:.2f} / {cap_bear_min:.2f} = {r_bear:.2f}$  " + ("✅" if r_bear<=1 else "❌"))

    # 3.3 Plate Yielding
    md.append(f"#### 3.3 Plate Shear Yielding (AISC J4.2)")
    md.append(render_eq("Yield Capacity", txt_yld_eq, txt_yld_sub, cap_yld))
    md.append(f"**Ratio:** ${V_load:.2f} / {cap_yld:.2f} = {r_yld:.2f}$  " + ("✅" if r_yld<=1 else "❌"))
    
    # 3.4 Plate Rupture
    md.append(f"#### 3.4 Plate Shear Rupture (AISC J4.3)")
    md.append(render_eq("Rupture Capacity", txt_rup_eq, txt_rup_sub, cap_rup))
    md.append(f"**Ratio:** ${V_load:.2f} / {cap_rup:.2f} = {r_rup:.2f}$  " + ("✅" if r_rup<=1 else "❌"))

    # 3.5 Block Shear
    md.append(f"#### 3.5 Block Shear Strength (AISC J4.3)")
    md.append(render_eq("Block Shear Capacity", txt_blk_eq, txt_blk_sub, cap_blk))
    md.append(f"**Ratio:** ${V_load:.2f} / {cap_blk:.2f} = {r_blk:.2f}$  " + ("✅" if r_blk<=1 else "❌"))

    # 3.6 Weld
    md.append(f"#### 3.6 Weld Strength (AISC J2.4)")
    md.append(render_eq("Weld Capacity", txt_weld_eq, txt_weld_sub, cap_weld))
    md.append(f"**Ratio:** ${V_load:.2f} / {cap_weld:.2f} = {r_weld:.2f}$  " + ("✅" if r_weld<=1 else "❌"))

    # Summary Table
    md.append("---")
    md.append("### 🏁 Summary of Results")
    
    summary_md = f"""
| Check Item | Demand ($V_u$ or $V_b$) | Capacity ($\phi R_n$) | Ratio | Result |
| :--- | :---: | :---: | :---: | :---: |
| **Bolt Shear** | {V_resultant:.2f} | {cap_bolt:.2f} | **{r_bolt:.2f}** | {"✅" if r_bolt<=1 else "❌"} |
| **Bolt Bearing** | {V_resultant:.2f} | {cap_bear_min:.2f} | **{r_bear:.2f}** | {"✅" if r_bear<=1 else "❌"} |
| **Plate Yielding** | {V_load:.2f} | {cap_yld:.2f} | **{r_yld:.2f}** | {"✅" if r_yld<=1 else "❌"} |
| **Plate Rupture** | {V_load:.2f} | {cap_rup:.2f} | **{r_rup:.2f}** | {"✅" if r_rup<=1 else "❌"} |
| **Block Shear** | {V_load:.2f} | {cap_blk:.2f} | **{r_blk:.2f}** | {"✅" if r_blk<=1 else "❌"} |
| **Weld Strength** | {V_load:.2f} | {cap_weld:.2f} | **{r_weld:.2f}** | {"✅" if r_weld<=1 else "❌"} |
    """
    md.append(summary_md)
    
    return "\n".join(md)
