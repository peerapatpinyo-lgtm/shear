import math

def generate_report(V_load, beam, plate, bolts, is_lrfd=True, material_grade="A36", bolt_grade="A325"):
    """
    สร้างรายการคำนวณรองรับทั้ง ASD และ LRFD
    """
    
    # --- 1. Setup Parameters & Factors ---
    d = bolts['d']
    n_rows = bolts['rows']
    n_cols = bolts['cols']
    n_total = n_rows * n_cols
    t_pl = plate['t']
    
    # Material Props (สมมติ)
    Fy_pl = 250
    Fu_pl = 400
    Fnv = 372 # A325N Shear

    # === 🔑 KEY LOGIC: ASD vs LRFD ===
    if is_lrfd:
        method_name = "LRFD"
        load_symbol = "V_u"
        
        # Resistance Factors (phi)
        phi_shear = 0.75
        phi_bearing = 0.75
        
        # Strings for display
        factor_str_shear = r"\phi R_n"
        calc_str_shear = f"{phi_shear} \\cdot R_n"
        
        factor_str_bearing = r"\phi R_n"
        calc_str_bearing = f"{phi_bearing} \\cdot R_n"
        
    else: # ASD
        method_name = "ASD"
        load_symbol = "V_a"
        
        # Safety Factors (Omega)
        omega_shear = 2.00
        omega_bearing = 2.00
        
        # Strings for display
        factor_str_shear = r"R_n / \Omega"
        calc_str_shear = f"R_n / {omega_shear}"
        
        factor_str_bearing = r"R_n / \Omega"
        calc_str_bearing = f"R_n / {omega_bearing}"

    # --- 2. Calculations ---

    # 2.1 Bolt Shear
    Ab = (math.pi * d**2) / 4
    Rn_shear_bolt = Fnv * Ab / 1000 # Nominal kN per bolt
    Rn_shear_total = Rn_shear_bolt * n_total # Nominal Total
    
    # Apply Factor
    if is_lrfd:
        cap_shear = phi_shear * Rn_shear_total
    else:
        cap_shear = Rn_shear_total / omega_shear

    # 2.2 Bolt Bearing
    # สูตรพื้นฐาน Rn = 2.4 * d * t * Fu
    Rn_bearing_per_bolt = 2.4 * d * t_pl * Fu_pl / 1000 # Nominal kN per bolt
    Rn_bearing_total = Rn_bearing_per_bolt * n_total # Nominal Total
    
    # Apply Factor
    if is_lrfd:
        cap_bearing = phi_bearing * Rn_bearing_total
    else:
        cap_bearing = Rn_bearing_total / omega_bearing

    # 2.3 Check Results
    capacity = min(cap_shear, cap_bearing)
    ratio = V_load / capacity if capacity > 0 else 999
    status = "✅ PASS" if ratio <= 1.0 else "❌ FAIL"
    color = "green" if ratio <= 1.0 else "red"

    # --- 3. Generate Markdown ---
    report = f"""
### 📝 Calculation Report ({method_name})

**Design Parameters:**
- Method: **{method_name}**
- Load (${load_symbol}$): **{V_load:.2f} kN**
- Bolts: {n_total} x M{d} ({bolt_grade})
- Plate: t={t_pl} mm ({material_grade})

---

#### 1. Bolt Shear Capacity
ตรวจสอบกำลังรับแรงเฉือนของน็อต (Shear Check)

* Nominal Strength ($R_n$):
$$ R_n = F_{{nv}} A_b n = {Fnv} \cdot {(Ab/1000):.2f} \cdot {n_total} = {Rn_shear_total:.2f} \\text{{ kN}} $$

**Design Strength ({factor_str_shear}):**
$$ {factor_str_shear} = {calc_str_shear} = \\mathbf{{{cap_shear:.2f} \\text{{ kN}}}} $$

---

#### 2. Bolt Bearing on Plate
ตรวจสอบแรงแบกทาน (Bearing Check)

* Nominal Strength ($R_n$):
$$ R_n = 2.4 d t F_u n = 2.4 \cdot {d} \cdot {t_pl} \cdot {Fu_pl} \cdot {n_total} / 1000 = {Rn_bearing_total:.2f} \\text{{ kN}} $$

**Design Strength ({factor_str_bearing}):**
$$ {factor_str_bearing} = {calc_str_bearing} = \\mathbf{{{cap_bearing:.2f} \\text{{ kN}}}} $$

---

#### 🏁 Summary
**Status: <span style='color:{color}'>{status}</span>**
- Demand (${load_symbol}$): {V_load:.2f} kN
- Capacity ({factor_str_shear}): {capacity:.2f} kN
- **Utilization Ratio:** {ratio:.2f}
    """
    
    return report
