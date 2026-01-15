# calculation_report.py
import math

def generate_report(V_load, beam, plate, bolts, is_lrfd=True, material_grade="A36", bolt_grade="A325"):
    
    # --- 1. Setup Parameters ---
    d = bolts['d']
    h_hole = d + 2 
    n_rows = bolts['rows']
    n_cols = bolts['cols']
    n_total = n_rows * n_cols
    
    t_pl = plate['t']
    h_pl = plate['h']
    lv = plate['lv'] 
    l_side = plate['l_side'] 
    weld_size = plate['weld_size']
    
    # 🆕 DYNAMIC MATERIAL PROPERTIES
    Fy_pl = plate['Fy']  
    Fu_pl = plate['Fu']  
    Fnv = bolts['Fnv']   
    Fexx = 480  

    # --- 2. Setup Factors (ASD vs LRFD) ---
    if is_lrfd:
        method_name = "LRFD"
        load_symbol = "V_u"
        
        # Factors
        phi_shear = 0.75
        phi_yield = 1.00
        phi_rupture = 0.75
        phi_weld = 0.75
        
        # Function to apply factor
        def apply_factor(Rn, phi, type="shear"):
            return phi * Rn, fr"\phi R_n", fr"{phi} \cdot {Rn:.2f}"
            
    else: # ASD
        method_name = "ASD"
        load_symbol = "V_a"
        
        # Factors
        om_shear = 2.00
        om_yield = 1.50
        om_rupture = 2.00
        om_weld = 2.00
        
        # Function to apply factor
        def apply_factor(Rn, omega, type="shear"):
            return Rn / omega, fr"\frac{{R_n}}{{\Omega}}", fr"\frac{{{Rn:.2f}}}{{{omega}}}"

    # =========================================================================
    # 3. CALCULATIONS
    # =========================================================================
    
    # --- 3.1 Bolt Shear ---
    Ab = (math.pi * d**2) / 4
    Rn_shear_total = (Fnv * Ab * n_total) / 1000
    if is_lrfd: cap_bolt_shear, str_f_bs, str_c_bs = apply_factor(Rn_shear_total, phi_shear)
    else:       cap_bolt_shear, str_f_bs, str_c_bs = apply_factor(Rn_shear_total, om_shear)

    # --- 3.2 Bolt Bearing ---
    Rn_bearing_total = (2.4 * d * t_pl * Fu_pl * n_total) / 1000
    if is_lrfd: cap_bearing, str_f_br, str_c_br = apply_factor(Rn_bearing_total, phi_shear)
    else:       cap_bearing, str_f_br, str_c_br = apply_factor(Rn_bearing_total, om_shear)

    # --- 3.3 Plate Shear Yielding (Gross Section) ---
    Ag_shear = h_pl * t_pl
    Rn_y = 0.60 * Fy_pl * Ag_shear / 1000
    if is_lrfd: cap_yield, str_f_y, str_c_y = apply_factor(Rn_y, phi_yield)
    else:       cap_yield, str_f_y, str_c_y = apply_factor(Rn_y, om_yield)

    # --- 3.4 Plate Shear Rupture (Net Section) ---
    An_shear = (h_pl - (n_rows * h_hole)) * t_pl
    Rn_r = 0.60 * Fu_pl * An_shear / 1000
    if is_lrfd: cap_rupture, str_f_r, str_c_r = apply_factor(Rn_r, phi_rupture)
    else:       cap_rupture, str_f_r, str_c_r = apply_factor(Rn_r, om_rupture)

    # --- 3.5 Block Shear Rupture (AISC J4.3) ---
    L_gv = (n_rows - 1) * bolts['s_v'] + lv 
    Agv = L_gv * t_pl
    Anv = (L_gv - (n_rows - 0.5) * h_hole) * t_pl
    Ant = (l_side - 0.5 * h_hole) * t_pl
    Ubs = 1.0 
    
    term1 = 0.6 * Fu_pl * Anv + Ubs * Fu_pl * Ant
    term2 = 0.6 * Fy_pl * Agv + Ubs * Fu_pl * Ant
    Rn_block = min(term1, term2) / 1000
    
    if is_lrfd: cap_block, str_f_bl, str_c_bl = apply_factor(Rn_block, phi_rupture)
    else:       cap_block, str_f_bl, str_c_bl = apply_factor(Rn_block, om_rupture)

    # --- 3.6 Weld Strength ---
    L_weld = h_pl * 2 
    Rn_weld = (0.6 * Fexx * 0.707 * weld_size * L_weld) / 1000
    
    if is_lrfd: cap_weld, str_f_wd, str_c_wd = apply_factor(Rn_weld, phi_weld)
    else:       cap_weld, str_f_wd, str_c_wd = apply_factor(Rn_weld, om_weld)

    # --- 4. SUMMARY & RESULT ---
    capacities = {
        "Bolt Shear": cap_bolt_shear,
        "Bolt Bearing": cap_bearing,
        "Plate Yielding": cap_yield,
        "Plate Rupture": cap_rupture,
        "Block Shear": cap_block,
        "Weld Strength": cap_weld
    }
    
    min_cap_val = min(capacities.values())
    governing_mode = min(capacities, key=capacities.get)
    ratio = V_load / min_cap_val if min_cap_val > 0 else 999
    
    if ratio <= 1.0:
        status = "✅ PASS"
        color = "green"
    else:
        status = "❌ FAIL"
        color = "red"

    # --- 5. REPORT GENERATION ---
    report = f"""
### 📝 Detailed Calculation Report ({method_name})

**Design Parameters:**
- Load (${load_symbol}$): **{V_load:.2f} kN**
- Plate: {h_pl:.0f}x{plate['w']:.0f}x{t_pl:.0f} mm ({material_grade})
- Bolts: {n_total} x M{d} ({bolt_grade})
- Weld: Fillet {weld_size} mm (E70xx)

---

#### 1. Bolt Checks
**1.1 Bolt Shear ({str_f_bs})**
$$ R_n = {Rn_shear_total:.2f} \\text{{ kN}} $$
$$ {str_f_bs} = {str_c_bs} = \\mathbf{{{cap_bolt_shear:.2f} \\text{{ kN}}}} $$

**1.2 Bolt Bearing ({str_f_br})**
$$ {str_f_br} = {str_c_br} = \\mathbf{{{cap_bearing:.2f} \\text{{ kN}}}} $$

---

#### 2. Plate Checks
**2.1 Shear Yielding (Gross) ({str_f_y})**
$$ A_g = {Ag_shear:.0f} \\text{{ mm}}^2 $$
$$ {str_f_y} = {str_c_y} = \\mathbf{{{cap_yield:.2f} \\text{{ kN}}}} $$

**2.2 Shear Rupture (Net) ({str_f_r})**
$$ A_n = {An_shear:.0f} \\text{{ mm}}^2 $$
$$ {str_f_r} = {str_c_r} = \\mathbf{{{cap_rupture:.2f} \\text{{ kN}}}} $$

**2.3 Block Shear Rupture ({str_f_bl})** ⚠️ *Critical*
- Shear Area: $A_{{gv}}={Agv:.0f}, A_{{nv}}={Anv:.0f}$ mm²
- Tension Area: $A_{{nt}}={Ant:.0f}$ mm²
$$ R_n = \\min(0.6 F_u A_{{nv}} + U_{{bs}} F_u A_{{nt}}, 0.6 F_y A_{{gv}} + U_{{bs}} F_u A_{{nt}}) = {Rn_block:.2f} \\text{{ kN}} $$
$$ {str_f_bl} = {str_c_bl} = \\mathbf{{{cap_block:.2f} \\text{{ kN}}}} $$

---

#### 3. Weld Checks
**3.1 Fillet Weld Strength ({str_f_wd})**
- Weld Size ($D$): {weld_size} mm
- Total Length ($L_w$): {h_pl:.0f} x 2 = {L_weld:.0f} mm
$$ R_n = 0.6 F_{{exx}} (0.707 D) L_w = {Rn_weld:.2f} \\text{{ kN}} $$
$$ {str_f_wd} = {str_c_wd} = \\mathbf{{{cap_weld:.2f} \\text{{ kN}}}} $$

---

#### 🏁 Final Summary
**Status: <span style='color:{color}'>{status}</span>**

| Limit State | Capacity (kN) | Ratio |
| :--- | :---: | :---: |
| Bolt Shear | {cap_bolt_shear:.2f} | {V_load/cap_bolt_shear if cap_bolt_shear > 0 else 0:.2f} |
| Bolt Bearing | {cap_bearing:.2f} | {V_load/cap_bearing if cap_bearing > 0 else 0:.2f} |
| Plate Yielding | {cap_yield:.2f} | {V_load/cap_yield if cap_yield > 0 else 0:.2f} |
| Plate Rupture | {cap_rupture:.2f} | {V_load/cap_rupture if cap_rupture > 0 else 0:.2f} |
| Block Shear | {cap_block:.2f} | {V_load/cap_block if cap_block > 0 else 0:.2f} |
| Weld Strength | {cap_weld:.2f} | {V_load/cap_weld if cap_weld > 0 else 0:.2f} |

👉 **Governing Case:** {governing_mode} (Capacity = **{min_cap_val:.2f} kN**)
**Utilization Ratio:** **{ratio:.2f}**
    """
    
    return report
