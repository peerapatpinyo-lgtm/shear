import math

def generate_report(V_load, beam, plate, bolts, material_grade="A36", bolt_grade="A325"):
    """
    ฟังก์ชันสำหรับสร้างรายการคำนวณ (Calculation Report)
    Return: ข้อความในรูปแบบ Markdown String
    """
    
    # --- 1. Unpack Variables ---
    d = bolts['d']
    n_rows = bolts['rows']
    n_cols = bolts['cols']
    n_total = n_rows * n_cols
    t_pl = plate['t']
    tw_beam = beam['tw']
    
    # Material Properties (สมมติค่าเบื้องต้น ถ้าจะให้ละเอียดต้องรับ Input เพิ่ม)
    Fy_pl = 250  # MPa (A36)
    Fu_pl = 400  # MPa
    Fnv = 372    # MPa (A325N Shear Strength)
    phi = 0.75   # Resistance Factor for Rupture/Shear

    # --- 2. Calculation Logic ---

    # 2.1 Bolt Shear Capacity
    # Area of bolt
    Ab = (math.pi * d**2) / 4
    # Nominal Strength per bolt (Single Shear)
    Rn_shear_bolt = Fnv * Ab / 1000 # convert to kN
    # Design Strength (Total)
    phi_Rn_shear_total = phi * Rn_shear_bolt * n_total

    # 2.2 Bolt Bearing on Plate
    # สูตรอย่างง่าย: Rn = 2.4 * d * t * Fu (กรณีระยะขอบเพียงพอ)
    # จริงๆ ต้องเช็คระยะ Lc ด้วย แต่ในที่นี้ขอใช้สูตร 2.4dtFu เป็นตัวอย่าง
    Rn_bearing_per_bolt = 2.4 * d * t_pl * Fu_pl / 1000 # kN
    phi_Rn_bearing_total = phi * Rn_bearing_per_bolt * n_total

    # 2.3 Check Result
    status = "✅ PASS" if phi_Rn_shear_total >= V_load else "❌ FAIL"
    util_ratio = V_load / phi_Rn_shear_total

    # --- 3. Generate Markdown Text ---
    report = f"""
### 📝 Detailed Calculation Report

**Design Parameters:**
- Load ($V_u$): **{V_load:.2f} kN**
- Connection Type: Shear Fin Plate
- Material: Plate {material_grade}, Bolt {bolt_grade}

---

#### 1. Bolt Shear Capacity ($\phi R_n$)
ตรวจสอบกำลังรับแรงเฉือนของน็อต (Single Shear)

* Bolt Diameter ($d$): {d} mm
* Number of Bolts ($n$): {n_total}
* Shear Strength ($F_{{nv}}$): {Fnv} MPa
* Bolt Area ($A_b$): $$\\frac{{\pi \cdot {d}^2}}{{4}} = {Ab:.2f} \\text{{ mm}}^2$$

**Nominal Strength per Bolt:**
$$ R_n = F_{{nv}} A_b = {Fnv} \cdot {Ab:.2f} / 1000 = {Rn_shear_bolt:.2f} \\text{{ kN}} $$

**Total Design Strength:**
$$ \\phi R_n = 0.75 \cdot {Rn_shear_bolt:.2f} \cdot {n_total} = \\mathbf{{{phi_Rn_shear_total:.2f} \\text{{ kN}}}} $$

---

#### 2. Bolt Bearing on Plate
ตรวจสอบแรงแบกทานบนแผ่นเหล็ก (Bearing)

* Plate Thickness ($t_{{pl}}$): {t_pl} mm
* Ultimate Strength ($F_u$): {Fu_pl} MPa

**Nominal Bearing Strength:**
$$ R_n = 2.4 d t F_u = 2.4 \cdot {d} \cdot {t_pl} \cdot {Fu_pl} / 1000 = {Rn_bearing_per_bolt:.2f} \\text{{ kN/bolt}} $$

**Total Bearing Capacity:**
$$ \\phi R_n = 0.75 \cdot {Rn_bearing_per_bolt:.2f} \cdot {n_total} = \\mathbf{{{phi_Rn_bearing_total:.2f} \\text{{ kN}}}} $$

---

#### 🏁 Summary
**Capacity vs Demand:**
- Demand ($V_u$): {V_load:.2f} kN
- Capacity (Governing): {min(phi_Rn_shear_total, phi_Rn_bearing_total):.2f} kN
- **Utilization Ratio:** {util_ratio:.2f} ({status})
    """
    
    return report
