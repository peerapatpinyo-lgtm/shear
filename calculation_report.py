import math

def generate_report(V_load, beam, plate, bolts, is_lrfd=True, material_grade="A36", bolt_grade="A325"):
    """
    สร้างรายการคำนวณรองรับทั้ง ASD และ LRFD (แก้ไข LaTeX Formatting)
    """
    
    # --- 1. Setup Parameters ---
    d = bolts['d']
    n_rows = bolts['rows']
    n_cols = bolts['cols']
    n_total = n_rows * n_cols
    t_pl = plate['t']
    
    # Material Props (สมมติ)
    Fy_pl = 250
    Fu_pl = 400
    Fnv = 372 

    # --- 2. Setup Factors (ASD vs LRFD) ---
    if is_lrfd:
        method_name = "LRFD"
        load_symbol = "V_u"
        
        # Factors
        phi_shear = 0.75
        phi_bearing = 0.75
        
        # Logic for Calculation
        cap_shear_factor = phi_shear
        cap_bearing_factor = phi_bearing
        
        # LaTeX Strings (ใส่ $ รอไว้เลย เพื่อความชัวร์)
        # Shear
        str_Rn_shear = r"\phi R_n"  
        str_calc_shear = f"{phi_shear} \\cdot R_n"
        
        # Bearing
        str_Rn_bearing = r"\phi R_n"
        str_calc_bearing = f"{phi_bearing} \\cdot R_n"
        
    else: # ASD
        method_name = "ASD"
        load_symbol = "V_a"
        
        # Factors
        omega_shear = 2.00
        omega_bearing = 2.00
        
        # Logic for Calculation
        cap_shear_factor = 1/omega_shear
        cap_bearing_factor = 1/omega_bearing
        
        # LaTeX Strings (ใช้ \frac เพื่อให้เป็นเศษส่วนสวยๆ)
        # Shear
        str_Rn_shear = r"\frac{R_n}{\Omega}"
        str_calc_shear = f"\\frac{{R_n}}{{{omega_shear}}}"
        
        # Bearing
        str_Rn_bearing = r"\frac{R_n}{\Omega}"
        str_calc_bearing = f"\\frac{{R_n}}{{{omega_bearing}}}"

    # --- 3. Calculations ---

    # 3.1 Bolt Shear
    Ab = (math.pi * d**2) / 4
    Rn_shear_bolt = Fnv * Ab / 1000 
    Rn_shear_total = Rn_shear_bolt * n_total 
    
    # Final Capacity
    design_shear = Rn_shear_total * cap_shear_factor

    # 3.2 Bolt Bearing
    Rn_bearing_per_bolt = 2.4 * d * t_pl * Fu_pl / 1000
    Rn_bearing_total = Rn_bearing_per_bolt * n_total
    
    # Final Capacity
    design_bearing = Rn_bearing_total * cap_bearing_factor

    # 3.3 Check Results
    capacity = min(design_shear, design_bearing)
    ratio = V_load / capacity if capacity > 0 else 999
    
    if ratio <= 1.0:
        status = "✅ PASS"
        status_color = "green"
    else:
        status = "❌ FAIL"
        status_color = "red"

    # --- 4. Generate Markdown Report ---
    # สังเกตการใช้ $...$ ในส่วนแสดงผล
    
    report = f"""
### 📝 Calculation Report ({method_name})

**Design Parameters:**
- Method: **{method_name}**
- Load (${load_symbol}$): **{V_load:.2f} kN**
- Bolts: {n_total} x M{d} ({bolt_grade})
- Plate: t={t_pl} mm ({material_grade})

---

#### 1. Bolt Shear Capacity
ตรวจสอบกำลังรับแรงเฉือนของน็อต (Shear)

* Bolt Area ($A_b$): {Ab:.2f} mm²
* Nominal Strength ($R_n$): {Rn_shear_total:.2f} kN

**Design Strength (${str_Rn_shear}$):**
$$ {str_Rn_shear} = {str_calc_shear} = \\mathbf{{{design_shear:.2f} \\text{{ kN}}}} $$

---

#### 2. Bolt Bearing on Plate
ตรวจสอบแรงแบกทานบนแผ่นเหล็ก (Bearing)

* Nominal Strength ($R_n$): {Rn_bearing_total:.2f} kN

**Design Strength (${str_Rn_bearing}$):**
$$ {str_Rn_bearing} = {str_calc_bearing} = \\mathbf{{{design_bearing:.2f} \\text{{ kN}}}} $$

---

#### 🏁 Summary
**Status: <span style='color:{status_color}'>{status}</span>**

| Check | Demand | Capacity | Ratio |
| :--- | :---: | :---: | :---: |
| **Governing** | **{V_load:.2f}** | **{capacity:.2f}** | **{ratio:.2f}** |

> **Note:** Capacity based on min({str_Rn_shear}, {str_Rn_bearing})
    """
    
    return report
