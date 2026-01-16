import math

def generate_report(V_load, beam, plate, bolts, is_lrfd=True, material_grade="A36", bolt_grade="A325"):
    
    # --- 1. EXTRACT DATA & PRE-CALC ---
    d = bolts['d']             # Bolt diameter (mm)
    h_hole = d + 2             # Hole size (mm)
    n_rows = bolts['rows']
    n_cols = bolts['cols']
    n_total = n_rows * n_cols
    s_v = bolts['s_v']         # Pitch V
    
    t_pl = plate['t']
    h_pl = plate['h']
    w_pl = plate['w']
    lv = plate['lv']           # Edge V (Top/Bottom)
    l_side = plate['l_side']   # Edge H (Side)
    weld_size = plate['weld_size']
    
    Fy = plate['Fy']
    Fu = plate['Fu']
    Fnv = bolts['Fnv']
    Fexx = 480 # E70xx
    
    # --- 2. DEFINE FACTORS & STRINGS ---
    if is_lrfd:
        method = "LRFD"
        load_sym = "V_u"
        phi_v, phi_y, phi_r, phi_w = 0.75, 1.00, 0.75, 0.75
        
        # Helper strings for LaTeX display
        f_shear = r"\phi R_n"
        f_yield = r"\phi R_n"
        f_rup   = r"\phi R_n"
        
        def calc_res(Rn, phi): return phi * Rn
        def fmt_eq(Rn, phi, res): return fr"{phi} \times {Rn:.2f} = \mathbf{{{res:.2f}}}"
        
    else:
        method = "ASD"
        load_sym = "V_a"
        om_v, om_y, om_r, om_w = 2.00, 1.50, 2.00, 2.00
        
        f_shear = r"R_n / \Omega"
        f_yield = r"R_n / \Omega"
        f_rup   = r"R_n / \Omega"
        
        def calc_res(Rn, om): return Rn / om
        def fmt_eq(Rn, om, res): return fr"\frac{{{Rn:.2f}}}{{{om}}} = \mathbf{{{res:.2f}}}"

    # =========================================================================
    # 3. DETAILED CALCULATIONS
    # =========================================================================

    # --- 3.1 Bolt Shear ---
    Ab = (math.pi * d**2) / 4
    Rn_shear = (Fnv * Ab * n_total) / 1000 # kN
    cap_shear = calc_res(Rn_shear, phi_v if is_lrfd else om_v)
    str_shear = fmt_eq(Rn_shear, phi_v if is_lrfd else om_v, cap_shear)

    # --- 3.2 Bolt Bearing ---
    # Formula: 2.4 * d * t * Fu
    Rn_bear = (2.4 * d * t_pl * Fu * n_total) / 1000 # kN
    cap_bear = calc_res(Rn_bear, phi_v if is_lrfd else om_v)
    str_bear = fmt_eq(Rn_bear, phi_v if is_lrfd else om_v, cap_bear)

    # --- 3.3 Plate Yield (Gross) ---
    Ag = h_pl * t_pl
    Rn_yld = (0.60 * Fy * Ag) / 1000
    cap_yld = calc_res(Rn_yld, phi_y if is_lrfd else om_y)
    str_yld = fmt_eq(Rn_yld, phi_y if is_lrfd else om_y, cap_yld)

    # --- 3.4 Plate Rupture (Net) ---
    An = (h_pl - (n_rows * h_hole)) * t_pl
    Rn_rup = (0.60 * Fu * An) / 1000
    cap_rup = calc_res(Rn_rup, phi_r if is_lrfd else om_r)
    str_rup = fmt_eq(Rn_rup, phi_r if is_lrfd else om_r, cap_rup)

    # --- 3.5 Block Shear (Complex) ---
    # Areas
    L_gv = (n_rows - 1) * s_v + lv
    Agv = L_gv * t_pl
    Anv = (L_gv - (n_rows - 0.5) * h_hole) * t_pl
    Ant = (l_side - 0.5 * h_hole) * t_pl
    Ubs = 1.0
    
    # Terms
    term1_val = (0.6 * Fu * Anv + Ubs * Fu * Ant) / 1000
    term2_val = (0.6 * Fy * Agv + Ubs * Fu * Ant) / 1000
    Rn_blk = min(term1_val, term2_val)
    
    cap_blk = calc_res(Rn_blk, phi_r if is_lrfd else om_r)
    str_blk = fmt_eq(Rn_blk, phi_r if is_lrfd else om_r, cap_blk)

    # --- 3.6 Weld ---
    L_weld = h_pl * 2
    Rn_weld = (0.6 * Fexx * 0.707 * weld_size * L_weld) / 1000
    cap_weld = calc_res(Rn_weld, phi_w if is_lrfd else om_w)
    str_weld = fmt_eq(Rn_weld, phi_w if is_lrfd else om_w, cap_weld)

    # =========================================================================
    # 4. REPORT TEXT GENERATION
    # =========================================================================
    
    # Determine Status
    all_caps = [cap_shear, cap_bear, cap_yld, cap_rup, cap_blk, cap_weld]
    min_cap = min(all_caps)
    ratio = V_load / min_cap if min_cap > 0 else 999
    
    pass_icon = "✅ PASS" if ratio <= 1.0 else "❌ FAIL"
    pass_color = "green" if ratio <= 1.0 else "red"

    # LaTeX Strings
    report_md = f"""
### 📝 Detailed Calculation Report ({method})

**1. Design Parameters**
* **Load ({load_sym}):** {V_load:.2f} kN
* **Material:** {material_grade} ($F_y={Fy}, F_u={Fu}$ MPa)
* **Bolt:** {n_total} x M{d} ({bolt_grade}, $F_{{nv}}={Fnv}$ MPa)
* **Plate:** {h_pl:.0f}x{w_pl:.0f}x{t_pl:.0f} mm
* **Geometry:** Pitch=$s_v$, Edge=$l_v$, Side=$l_{{side}}$

---

#### 2. Connection Strength Checks

**2.1 Bolt Shear Strength**
* Area ($A_b$) = $\\frac{{\\pi \cdot {d}^2}}{{4}} = {Ab:.1f} \\text{{ mm}}^2$
* Nominal Strength ($R_n$):
$$ R_n = F_{{nv}} A_b N_b = {Fnv} \\times {Ab:.1f} \\times {n_total} = {Rn_shear:.2f} \\text{{ kN}} $$
* Design Strength:
$$ {f_shear} = {str_shear} $$

**2.2 Bolt Bearing Strength**
* Nominal Strength ($R_n$) per AISC J3.10:
$$ R_n = 2.4 d t F_u N_b = 2.4({d})({t_pl})({Fu})({n_total}) = {Rn_bear:.2f} \\text{{ kN}} $$
* Design Strength:
$$ {f_shear} = {str_bear} $$

**2.3 Plate Shear Yielding (Gross Section)**
* Gross Area ($A_g$) = $h \cdot t = {h_pl} \\times {t_pl} = {Ag:.0f} \\text{{ mm}}^2$
* Nominal Strength ($R_n$):
$$ R_n = 0.6 F_y A_g = 0.6({Fy})({Ag:.0f}) = {Rn_yld:.2f} \\text{{ kN}} $$
* Design Strength:
$$ {f_yield} = {str_yld} $$

**2.4 Plate Shear Rupture (Net Section)**
* Hole Dia ($d_h$) = {h_hole:.1f} mm
* Net Area ($A_n$) = $(h - N_{{row}} d_h) t = ({h_pl} - {n_rows}({h_hole:.1f}))({t_pl}) = {An:.0f} \\text{{ mm}}^2$
* Nominal Strength ($R_n$):
$$ R_n = 0.6 F_u A_n = 0.6({Fu})({An:.0f}) = {Rn_rup:.2f} \\text{{ kN}} $$
* Design Strength:
$$ {f_rup} = {str_rup} $$

**2.5 Block Shear Rupture**
* **Areas:**
    * $A_{{gv}} = ({L_gv:.1f})({t_pl}) = {Agv:.0f} \\text{{ mm}}^2$
    * $A_{{nv}} = [{L_gv:.1f} - ({n_rows}-0.5){h_hole:.1f}]({t_pl}) = {Anv:.0f} \\text{{ mm}}^2$
    * $A_{{nt}} = [{l_side:.1f} - 0.5({h_hole:.1f})]({t_pl}) = {Ant:.0f} \\text{{ mm}}^2$
* **Calculation Terms:**
    1.  $0.6 F_u A_{{nv}} + U_{{bs}} F_u A_{{nt}} = {term1_val:.2f} \\text{{ kN}}$
    2.  $0.6 F_y A_{{gv}} + U_{{bs}} F_u A_{{nt}} = {term2_val:.2f} \\text{{ kN}}$
* Nominal Strength ($R_n = \\min(1, 2)$): **{Rn_blk:.2f} kN**
* Design Strength:
$$ {f_rup} = {str_blk} $$

**2.6 Weld Strength**
* Total Length ($L_w$) = $2 \\times {h_pl} = {L_weld:.0f} \\text{{ mm}}$
* Nominal Strength ($R_n$):
$$ R_n = 0.6 F_{{exx}} (0.707 w) L_w = 0.6(480)(0.707 \cdot {weld_size})({L_weld}) = {Rn_weld:.2f} \\text{{ kN}} $$
* Design Strength:
$$ {f_yield} = {str_weld} $$

---

#### 🏁 Final Summary
**(Detailed table available on the left dashboard)**

**Status:** <span style='color:{pass_color}; font-size:16px; font-weight:bold;'>{pass_icon}</span>
**Utilization Ratio:** <span style='background-color:{pass_color}; color:white; padding:2px 6px; border-radius:4px;'>{ratio:.2f}</span>
    """
    
    return report_md
