# report_generator.py
# Version: 3.0 (Added Detailed Calculation Report)
import streamlit as st
import math
import pandas as pd

def get_standard_sections():
    """
    Database หน้าตัดเหล็ก Wide Flange (H-Beam) มาตรฐาน
    หน่วย: cm
    """
    return [
        {"name": "H-100x100x6x8", "d": 10, "b": 10, "tw": 0.6, "tf": 0.8, "Zx": 76.5, "Ix": 378, "Area": 21.9},
        {"name": "H-150x75x5x7", "d": 15, "b": 7.5, "tw": 0.5, "tf": 0.7, "Zx": 88.8, "Ix": 666, "Area": 17.85},
        {"name": "H-150x150x7x10", "d": 15, "b": 15, "tw": 0.7, "tf": 1.0, "Zx": 232, "Ix": 1620, "Area": 39.65},
        {"name": "H-200x100x5.5x8", "d": 20, "b": 10, "tw": 0.55, "tf": 0.8, "Zx": 184, "Ix": 1840, "Area": 27.16},
        {"name": "H-200x200x8x12", "d": 20, "b": 20, "tw": 0.8, "tf": 1.2, "Zx": 472, "Ix": 4720, "Area": 63.53},
        {"name": "H-250x125x6x9", "d": 25, "b": 12.5, "tw": 0.6, "tf": 0.9, "Zx": 324, "Ix": 4050, "Area": 37.66},
        {"name": "H-300x150x6.5x9", "d": 30, "b": 15, "tw": 0.65, "tf": 0.9, "Zx": 481, "Ix": 7210, "Area": 46.78},
        {"name": "H-350x175x7x11", "d": 35, "b": 17.5, "tw": 0.7, "tf": 1.1, "Zx": 775, "Ix": 13600, "Area": 63.14},
        {"name": "H-400x200x8x13", "d": 40, "b": 20, "tw": 0.8, "tf": 1.3, "Zx": 1190, "Ix": 23700, "Area": 84.12},
        {"name": "H-400x400x13x21", "d": 40, "b": 40, "tw": 1.3, "tf": 2.1, "Zx": 3330, "Ix": 66600, "Area": 218.7},
        {"name": "H-450x200x9x14", "d": 45, "b": 20, "tw": 0.9, "tf": 1.4, "Zx": 1490, "Ix": 33500, "Area": 96.76},
        {"name": "H-500x200x10x16", "d": 50, "b": 20, "tw": 1.0, "tf": 1.6, "Zx": 1910, "Ix": 47800, "Area": 114.2},
    ]

def calculate_full_properties(sec):
    """
    Helper function to normalize property names for display
    """
    return {
        "Name": sec['name'],
        "Depth (mm)": sec['d']*10,
        "Width (mm)": sec['b']*10,
        "Web t (mm)": sec['tw']*10,
        "Flange t (mm)": sec['tf']*10,
        "Zx (cm3)": sec['Zx'],
        "Ix (cm4)": sec['Ix'],
        "Area (cm2)": sec['Area']
    }

def calculate_connection(sec, load_pct, bolt_dia, factor, load_case):
    """
    Core Calculation Logic
    """
    # Material Constants
    Fy = 2500 # ksc
    Fu = 4100 # ksc
    E = 2.04e6 # ksc
    
    # 1. Beam Shear Capacity (Vn)
    # Vn = 0.6 * Fy * Aw (Yielding)
    Aw = sec['d'] * sec['tw'] # cm2
    Vn_beam = 0.6 * Fy * Aw # kg
    
    # 2. Design Load (Vu)
    V_target = Vn_beam * (load_pct / 100.0)
    
    # 3. Bolt Capacity (Single Shear)
    # A325 / 8.8 (Approx shear strength ~ 0.6 * Fub * Ab)
    # phi = 0.75
    Fub = 8250 # ksc (Grade A325/8.8 Ultimate) - Assumed for calc
    Ab = 3.1416 * (bolt_dia/10/2)**2 # cm2
    phi_bolt = 0.75
    # Nominal Shear Strength per bolt (assume threads excluded for conservative)
    # Rn = 0.5 * Fub * Ab (Conservative approx standard) or 0.6
    # Let's use EIT/AISC standard: phi * 0.45 * Fub * Ab (Threads included)
    # Or simplified: Shear Stress Allowable ~ 1200-1500 ksc * Area.
    # Let's use a standard value calculation:
    rn_nominal = 0.6 * Fu * Ab # Use Beam Fu for simple bearing or Bolt Fub? 
    # Let's use specific capacity for M-bolt
    bolt_shear_strength = 3000 # ksc (Allowable/Design shear stress approx)
    phiRn_bolt = bolt_shear_strength * Ab * 0.8 # approx factor
    
    # Re-cal for standard exactness (AISC LRFD style simplified)
    # phi rn = 0.75 * 0.45 * Fub * Ab
    phiRn_bolt = 0.75 * 0.45 * 8250 * Ab 
    
    # 4. Bolt Quantity
    if phiRn_bolt > 0:
        req_bolts = V_target / phiRn_bolt
        n_bolts = math.ceil(req_bolts)
        if n_bolts < 2: n_bolts = 2 # Minimum 2 bolts
    else:
        n_bolts = 0

    # 5. Connection Plate Sizing
    # Spacing 3d, Edge 1.5d
    pitch = 3 * bolt_dia # mm
    edge = 1.5 * bolt_dia # mm
    # Plate Height
    plate_len_mm = (2 * edge) + ((n_bolts - 1) * pitch)
    plate_len_cm = plate_len_mm / 10.0
    
    # 6. Span Calculation
    # 6.1 Limit by Moment (L_moment)
    # Mn = Zx * Fy
    Mn = sec['Zx'] * Fy # kg-cm
    # Load w (kg/m) from Beam Capacity or Target?
    # Usually we find Lmax such that Moment = Mn under uniform load w
    # Let's assume w is derived from V_target being the Reaction (R = wL/2)
    # V_target = wL/2  => w = 2*V_target / L
    # Moment = wL^2/8 = (2*V/L) * L^2 / 8 = V*L / 4
    # Mn = V_target * L / 4  => L = 4 * Mn / V_target
    if V_target > 0:
        L_crit_moment_cm = (4 * Mn) / V_target
        L_crit_moment_m = L_crit_moment_cm / 100.0
    else:
        L_crit_moment_m = 0
        
    # 6.2 Limit by Deflection (L_defl)
    # Delta_allow = L/360
    # Delta_max = 5wL^4 / 384EI
    # Subst w = 2V/L => Delta = 5(2V/L)L^4 / 384EI = 10 V L^3 / 384 EI
    # L/360 = 10 V L^3 / 384 EI
    # 1/360 = 10 V L^2 / 384 EI
    # L^2 = (384 * EI) / (3600 * V)
    if V_target > 0:
        val = (384 * E * sec['Ix']) / (3600 * V_target)
        L_crit_defl_cm = math.sqrt(val)
        L_crit_defl_m = L_crit_defl_cm / 100.0
    else:
        L_crit_defl_m = 0
        
    L_safe = min(L_crit_moment_m, L_crit_defl_m)

    return {
        "Section": sec['name'],
        "Vn_beam": Vn_beam,
        "V_target": V_target,
        "phiRn_bolt": phiRn_bolt,
        "Bolt Qty": n_bolts,
        "Plate Len": plate_len_cm,
        "L_crit_moment": L_crit_moment_m,
        "L_crit_defl": L_crit_defl_m,
        "L_safe": L_safe,
        "Zx": sec['Zx'],
        "Ix": sec['Ix'],
        "Area": sec['Area'],
        "Depth": sec['d'],
        "Web": sec['tw']
    }

def render_detailed_report(section, load_pct, bolt_dia, factor, load_case):
    """
    ฟังก์ชันสร้างรายการคำนวณโดยละเอียด (Step-by-Step Calculation)
    แสดงผลเป็น Markdown/LaTeX
    """
    # 1. Recalculate to get all variables
    res = calculate_connection(section, load_pct, bolt_dia, factor, load_case)
    
    # Constants
    Fy = 2500
    Fu = 4100
    E = 2.04e6
    Fub = 8250 # Bolt Ultimate
    
    st.markdown(f"## 📝 รายการคำนวณ: จุดต่อคานเหล็ก {section['name']}")
    st.markdown("---")

    # --- PART 1: Design Parameters ---
    st.subheader("1. ข้อกำหนดการออกแบบ (Design Parameters)")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Properties of Beam:**")
        st.latex(f"Section: \\text{{{section['name']}}}")
        st.latex(f"d = {section['d']} \\, cm, \\; t_w = {section['tw']} \\, cm")
        st.latex(f"Z_x = {section['Zx']} \\, cm^3, \\; I_x = {section['Ix']} \\, cm^4")
        st.latex(f"F_y = {Fy} \\, ksc, \\; E = 2.04 \\times 10^6 \\, ksc")
    with c2:
        st.markdown("**Bolt Properties:**")
        st.latex(f"Dia (\\O) = {bolt_dia} \\, mm")
        st.latex(f"Grade: \\text{{A325 / 8.8}}")
        st.latex(f"F_{{ub}} = {Fub} \\, ksc")
        st.latex(f"Load \\, Condition: {load_case} \\, ({load_pct}\\% \\, of \\, V_n)")

    st.markdown("---")

    # --- PART 2: Design Loads ---
    st.subheader("2. แรงเฉือนออกแบบ (Design Shear Force)")
    st.markdown(f"คำนวณกำลังรับแรงเฉือนของคาน ({section['name']}) และปรับลดตาม Load Factor ที่ต้องการ")
    
    st.latex(r"A_w = d \times t_w")
    st.latex(f"A_w = {section['d']} \\times {section['tw']} = {section['d']*section['tw']:.2f} \\, cm^2")
    
    st.latex(r"V_{n(beam)} = 0.60 \times F_y \times A_w")
    st.latex(f"V_{{n(beam)}} = 0.60 \\times {Fy} \\times {section['d']*section['tw']:.2f} = {res['Vn_beam']:,.2f} \\, kg")
    
    st.latex(f"V_{{u(design)}} = V_{{n(beam)}} \\times {load_pct}\\%")
    st.markdown(f"👉 **Design Shear ($V_u$):** `{res['V_target']:,.2f} kg`")
    
    st.markdown("---")

    # --- PART 3: Bolt Design ---
    st.subheader("3. การออกแบบจุดต่อสลักเกลียว (Bolt Design)")
    
    # 3.1 Bolt Area
    Ab = 3.1416 * (bolt_dia/10/2)**2
    st.markdown("**3.1 พื้นที่หน้าตัดสลักเกลียว ($A_b$):**")
    st.latex(r"A_b = \frac{\pi \times d^2}{4}")
    st.latex(f"A_b = \\frac{{3.1416 \\times ({bolt_dia/10})^2}}{{4}} = {Ab:.3f} \\, cm^2")
    
    # 3.2 Shear Capacity
    st.markdown("**3.2 กำลังรับแรงเฉือนของสลักเกลียว ($\phi R_n$):**")
    st.caption("อ้างอิงมาตรฐาน AISC LRFD/EIT สำหรับ Bolt Grade A325 (Threads included in shear plane)")
    st.latex(r"\phi R_n = \phi \times 0.45 \times F_{ub} \times A_b")
    st.latex(f"\\phi R_n = 0.75 \\times 0.45 \\times {Fub} \\times {Ab:.3f} = {res['phiRn_bolt']:,.2f} \\, kg/bolt")
    
    # 3.3 Quantity
    st.markdown("**3.3 จำนวนสลักเกลียวที่ต้องการ ($N$):**")
    st.latex(r"N = \frac{V_{u(design)}}{\phi R_n}")
    st.latex(f"N = \\frac{{{res['V_target']:,.2f}}}{{{res['phiRn_bolt']:,.2f}}} = {res['V_target']/res['phiRn_bolt']:.2f} \\rightarrow \\text{{Use }} {res['Bolt Qty']} \\text{{ pcs.}}")
    
    # 3.4 Plate Dimension
    st.markdown("**3.4 ขนาดแผ่นเหล็กเดือย (End Plate):**")
    st.write(f"- Spacing (3d): {3*bolt_dia} mm")
    st.write(f"- Edge Distance (1.5d): {1.5*bolt_dia} mm")
    st.write(f"- **Total Plate Height:** `{res['Plate Len']:.2f} cm`")

    st.markdown("---")

    # --- PART 4: Safe Span Analysis ---
    st.subheader("4. การวิเคราะห์ระยะปลอดภัย (Safe Span Analysis)")
    st.markdown("สมมติให้แรงเฉือน $V_u$ เกิดจากแรงกระทำแผ่กระจายสม่ำเสมอ ($w$) บนคานช่วงเดียว")
    st.info("Assumption: $V_u = wL/2$ (Reaction Force)")

    # 4.1 Moment Limit
    st.markdown("#### 4.1 ตรวจสอบโมเมนต์ดัด ($L_{moment}$)")
    st.latex(r"M_n = Z_x \times F_y")
    st.latex(f"M_n = {section['Zx']} \\times {Fy} = {section['Zx']*Fy:,.0f} \\, kg\\cdot cm")
    
    st.markdown("จากความสัมพันธ์ $M = V_u \cdot L / 4$ (ที่กลางคาน):")
    st.latex(r"L_{max} = \frac{4 \times M_n}{V_u}")
    st.latex(f"L_{{moment}} = \\frac{{4 \\times {section['Zx']*Fy:,.0f}}}{{{res['V_target']:,.2f}}} = {res['L_crit_moment']*100:,.2f} \\, cm")
    st.success(f"📌 Limit by Moment: **{res['L_crit_moment']:.2f} m**")

    # 4.2 Deflection Limit
    st.markdown("#### 4.2 ตรวจสอบการแอ่นตัว ($L_{defl}$)")
    st.markdown("กำหนดให้การแอ่นตัวสูงสุดไม่เกิน $L/360$")
    st.latex(r"L^2 = \frac{384 \times E \times I_x}{3600 \times V_u}")
    
    numerator = 384 * E * section['Ix']
    denominator = 3600 * res['V_target']
    l_sq = numerator/denominator if denominator > 0 else 0
    
    st.latex(f"L^2 = \\frac{{384 \\times {E:.2e} \\times {section['Ix']}}}{{3600 \\times {res['V_target']:,.2f}}} = {l_sq:,.2f}")
    st.success(f"📌 Limit by Deflection: **{res['L_crit_defl']:.2f} m**")

    st.markdown("---")
    
    # --- PART 5: Conclusion ---
    st.subheader("✅ สรุปผลการคำนวณ (Conclusion)")
    
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.metric("Bolt Quantity", f"{res['Bolt Qty']} pcs", f"Dia M{bolt_dia}")
        st.metric("Shear Capacity (Beam)", f"{res['Vn_beam']:,.0f} kg")
    with res_col2:
        st.metric("Safe Max Span", f"{res['L_safe']:.2f} m", "Controls Design")
        st.metric("Governing Limit", "Moment" if res['L_crit_moment'] < res['L_crit_defl'] else "Deflection")

    st.warning("**หมายเหตุ:** การคำนวณนี้เป็นรายการคำนวณเบื้องต้นสำหรับจุดต่อรับแรงเฉือน (Shear Connection) เท่านั้น วิศวกรควรตรวจสอบรายละเอียดรอยเชื่อม (Weld) และการวิบัติแบบ Block Shear เพิ่มเติมตามมาตรฐาน")
