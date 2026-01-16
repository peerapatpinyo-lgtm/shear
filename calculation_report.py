import math

def generate_report(V_load, beam, plate, bolts, is_lrfd=True, material_grade="A36", bolt_grade="A325"):
    
    # --- 1. EXTRACT DATA ---
    d = bolts['d']             
    h_hole = d + 2             
    n_rows = bolts['rows']
    n_cols = bolts['cols']
    n_total = n_rows * n_cols
    s_v = bolts['s_v']         
    s_h = bolts.get('s_h', 0)  # Pitch Horizontal
    
    t_pl = plate['t']
    h_pl = plate['h']
    e_dist = plate['e1']       # Distance from weld to first bolt line
    
    # Beam Data (For Web Check)
    t_web = beam['tw'] if beam else 8 # Default fallback
    Fu_beam = beam['Fu'] if beam else 400 
    
    Fy_pl = plate['Fy']
    Fu_pl = plate['Fu']
    Fnv = bolts['Fnv']
    Fexx = 480 
    
    # --- 2. FACTORS ---
    if is_lrfd:
        method = "LRFD"
        phi_v, phi_y, phi_r, phi_w = 0.75, 1.00, 0.75, 0.75
        def calc_res(Rn, phi): return phi * Rn
        def fmt_eq(Rn, phi, res): return fr"{phi} \times {Rn:.2f} = \mathbf{{{res:.2f}}}"
    else:
        method = "ASD"
        om_v, om_y, om_r, om_w = 2.00, 1.50, 2.00, 2.00
        def calc_res(Rn, om): return Rn / om
        def fmt_eq(Rn, om, res): return fr"\frac{{{Rn:.2f}}}{{{om}}} = \mathbf{{{res:.2f}}}"

    # =========================================================================
    # 3. ADVANCED CALCULATIONS
    # =========================================================================

    # --- 3.1 Bolt Shear with Eccentricity (Elastic Method) ---
    Ab = (math.pi * d**2) / 4
    
    # 1. Find Centroid
    # X-coord relative to first column
    if n_cols > 1:
        x_bar = ((n_cols - 1) * s_h) / 2
    else:
        x_bar = 0
    
    # Eccentricity (e) = Distance from Weld (Support) to Centroid
    eccentricity = e_dist + x_bar
    Moment = V_load * eccentricity # kN-mm
    
    # 2. Polar Moment of Inertia (J)
    # Sum(x^2 + y^2) for all bolts relative to centroid
    sum_r2 = 0
    max_r = 0 # To find critical bolt
    
    # Loop through all bolt positions to calculate J
    # Assume centroid is at (0,0) locally for calculation
    row_start = -((n_rows - 1) * s_v) / 2
    col_start = -x_bar
    
    for c in range(n_cols):
        for r in range(n_rows):
            dx = col_start + (c * s_h)
            dy = row_start + (r * s_v)
            dist_sq = dx**2 + dy**2
            sum_r2 += dist_sq
            max_r = max(max_r, math.sqrt(dist_sq))
            
    # 3. Forces on Critical Bolt (Furthest from centroid)
    # Direct Shear
    Rv_direct = V_load / n_total
    
    # Moment Shear (Elastic Method)
    # Force = M * r / J
    # Decompose to H and V components: Fx = M*y/J, Fy = M*x/J
    # Critical bolt is at corner.
    crit_x = x_bar # Abs distance from centroid X
    crit_y = ((n_rows - 1) * s_v) / 2 # Abs distance from centroid Y
    
    if sum_r2 > 0:
        Rv_moment = (Moment * crit_x) / sum_r2 # Vertical component due to Moment
        Rh_moment = (Moment * crit_y) / sum_r2 # Horizontal component due to Moment
    else:
        Rv_moment = 0
        Rh_moment = 0
        
    # Resultant Force on Critical Bolt
    R_total_v = Rv_direct + Rv_moment
    R_total_h = Rh_moment
    V_resultant = math.sqrt(R_total_v**2 + R_total_h**2)
    
    # Capacity Check
    Rn_bolt_nominal = (Fnv * Ab) / 1000 # kN per bolt
    cap_bolt_single = calc_res(Rn_bolt_nominal, phi_v if is_lrfd else om_v)
    
    # --- 3.2 Bolt Bearing (Plate & Beam Web) ---
    # Plate Bearing
    Rn_bear_pl = (2.4 * d * t_pl * Fu_pl) / 1000 # per bolt
    cap_bear_pl_single = calc_res(Rn_bear_pl, phi_v if is_lrfd else om_v)
    
    # Beam Web Bearing (New Check!)
    Rn_bear_web = (2.4 * d * t_web * Fu_beam) / 1000 # per bolt
    cap_bear_web_single = calc_res(Rn_bear_web, phi_v if is_lrfd else om_v)
    
    # Min Bearing Capacity
    cap_bear_min_single = min(cap_bear_pl_single, cap_bear_web_single)

    # --- 3.3 Plate Checks (Standard) ---
    Ag = h_pl * t_pl
    Rn_yld = (0.60 * Fy_pl * Ag) / 1000
    cap_yld = calc_res(Rn_yld, phi_y if is_lrfd else om_y)

    An = (h_pl - (n_rows * h_hole)) * t_pl
    Rn_rup = (0.60 * Fu_pl * An) / 1000
    cap_rup = calc_res(Rn_rup, phi_r if is_lrfd else om_r)
    
    # Block Shear
    lv = plate['lv']
    l_side = plate['l_side']
    L_gv = (n_rows - 1) * s_v + lv
    Agv = L_gv * t_pl
    Anv = (L_gv - (n_rows - 0.5) * h_hole) * t_pl
    Ant = (l_side - 0.5 * h_hole) * t_pl
    
    Rn_blk = min(0.6 * Fu_pl * Anv + Fu_pl * Ant, 0.6 * Fy_pl * Agv + Fu_pl * Ant) / 1000
    cap_blk = calc_res(Rn_blk, phi_r if is_lrfd else om_r)

    # --- 3.4 Weld Strength ---
    L_weld = h_pl * 2
    weld_size = plate['weld_size']
    Rn_weld = (0.6 * Fexx * 0.707 * weld_size * L_weld) / 1000
    cap_weld = calc_res(Rn_weld, phi_w if is_lrfd else om_w)

    # =========================================================================
    # 4. REPORT GENERATION
    # =========================================================================
    
    # Ratio Calculation
    ratio_bolt = V_resultant / cap_bolt_single
    ratio_bear = V_resultant / cap_bear_min_single # Conservative: use V_res check against bearing
    ratio_yld = V_load / cap_yld
    ratio_rup = V_load / cap_rup
    ratio_blk = V_load / cap_blk
    ratio_weld = V_load / cap_weld
    
    max_ratio = max(ratio_bolt, ratio_bear, ratio_yld, ratio_rup, ratio_blk, ratio_weld)
    pass_icon = "✅ PASS" if max_ratio <= 1.0 else "❌ FAIL"
    color = "green" if max_ratio <= 1.0 else "red"

    report_md = f"""
### 📝 Senior Engineer Calculation Report ({method})

**1. Design Loads & Geometry**
* **Load ($V_u$):** {V_load:.2f} kN
* **Eccentricity ($e$):** {eccentricity:.1f} mm (Support to Bolt Centroid)
* **Moment ($M_u$):** $V_u \times e = {V_load:.2f} \times {eccentricity:.1f} / 1000 = {Moment/1000:.2f}$ kN-m
* **Member:** Plate {t_pl}mm ($F_u={Fu_pl}$), Beam Web {t_web}mm ($F_u={Fu_beam}$)

---

#### 2. Advanced Bolt Analysis (Elastic Method)
**2.1 Resultant Force on Critical Bolt**
The bolt group is subjected to Shear ($V$) and Moment ($M$).
* Polar Moment of Inertia ($\sum r^2$): {sum_r2:.0f} mm²
* **Direct Shear ($F_v$):** $V / n = {V_load:.2f} / {n_total} = {Rv_direct:.2f}$ kN
* **Shear from Moment ($F_m$):**
  * Vertical ($F_{{my}}$): $(M \cdot c_x) / \sum r^2 = {Rv_moment:.2f}$ kN
  * Horizontal ($F_{{mx}}$): $(M \cdot c_y) / \sum r^2 = {Rh_moment:.2f}$ kN
* **Resultant Force ($R_{{u,bolt}}$):** $\sqrt{{(F_v + F_{{my}})^2 + F_{{mx}}^2}} = \\mathbf{{{V_resultant:.2f} \\text{{ kN}}}}$

**2.2 Bolt Shear Capacity**
* Single Bolt Capacity ($\phi R_n$): **{cap_bolt_single:.2f} kN**
* Ratio: ${V_resultant:.2f} / {cap_bolt_single:.2f} = $ **{ratio_bolt:.2f}**

**2.3 Bearing & Tearout Check**
* Plate Bearing Cap: {cap_bear_pl_single:.2f} kN/bolt
* Beam Web Bearing Cap: {cap_bear_web_single:.2f} kN/bolt
* Governing Capacity: **{cap_bear_min_single:.2f} kN/bolt**
* Ratio: ${V_resultant:.2f} / {cap_bear_min_single:.2f} = $ **{ratio_bear:.2f}**

---

#### 3. Plate & Weld Checks
**3.1 Plate Yielding (Gross)**
$$ {fmt_eq(Rn_yld, phi_y if is_lrfd else om_y, cap_yld)} \\text{{ kN}} $$ (Ratio: {ratio_yld:.2f})

**3.2 Plate Rupture (Net)**
$$ {fmt_eq(Rn_rup, phi_r if is_lrfd else om_r, cap_rup)} \\text{{ kN}} $$ (Ratio: {ratio_rup:.2f})

**3.3 Block Shear**
$$ R_n = {Rn_blk:.2f} \\text{{ kN}} $$
$$ {fmt_eq(Rn_blk, phi_r if is_lrfd else om_r, cap_blk)} \\text{{ kN}} $$ (Ratio: {ratio_blk:.2f})

**3.4 Weld Strength**
$$ R_n = {Rn_weld:.2f} \\text{{ kN}} $$
$$ {fmt_eq(Rn_weld, phi_w if is_lrfd else om_w, cap_weld)} \\text{{ kN}} $$ (Ratio: {ratio_weld:.2f})

---

#### 🏁 Summary
**Status:** <span style='color:{color}; font-size:16px; font-weight:bold;'>{pass_icon}</span> (Max Ratio: {max_ratio:.2f})
    """
    return report_md
