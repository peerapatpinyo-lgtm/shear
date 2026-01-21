# report_generator.py
# Version: 3.1 (Fixed: Added render_report_tab compatibility)
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
    Fy = 2500 # ksc
    Fu = 4100 # ksc
    E = 2.04e6 # ksc
    
    # 1. Beam Shear Capacity
    Aw = sec['d'] * sec['tw'] # cm2
    Vn_beam = 0.6 * Fy * Aw # kg
    V_target = Vn_beam * (load_pct / 100.0)
    
    # 2. Bolt Capacity (Single Shear)
    # A325 / 8.8 (Standard Approx)
    Fub = 8250 # ksc
    Ab = 3.1416 * (bolt_dia/10/2)**2 # cm2
    # phi Rn = 0.75 * 0.45 * Fub * Ab (Threads included)
    phiRn_bolt = 0.75 * 0.45 * Fub * Ab 
    
    # 3. Bolt Quantity
    if phiRn_bolt > 0:
        req_bolts = V_target / phiRn_bolt
        n_bolts = math.ceil(req_bolts)
        if n_bolts < 2: n_bolts = 2
    else:
        n_bolts = 0

    # 4. Connection Plate Sizing
    pitch = 3 * bolt_dia # mm
    edge = 1.5 * bolt_dia # mm
    plate_len_mm = (2 * edge) + ((n_bolts - 1) * pitch)
    plate_len_cm = plate_len_mm / 10.0
    
    # 5. Span Calculation
    Mn = sec['Zx'] * Fy # kg-cm
    if V_target > 0:
        L_crit_moment_cm = (4 * Mn) / V_target
        L_crit_moment_m = L_crit_moment_cm / 100.0
    else:
        L_crit_moment_m = 0
        
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
    ฟังก์ชันหลักสำหรับแสดงรายงาน (Core Function)
    """
    res = calculate_connection(section, load_pct, bolt_dia, factor, load_case)
    Fy = 2500
    Fu = 4100
    E = 2.04e6
    Fub = 8250 
    
    st.markdown(f"## 📝 รายการคำนวณ: จุดต่อคานเหล็ก {section['name']}")
    st.markdown("---")

    # Part 1: Parameters
    st.subheader("1. ข้อกำหนดการออกแบบ (Design Parameters)")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Properties of Beam:**")
        st.latex(f"Section: \\text{{{section['name']}}}")
        st.latex(f"d = {section['d']} \\, cm, \\; t_w = {section['tw']} \\, cm")
        st.latex(f"Z_x = {section['Zx']} \\, cm^3, \\; I_x = {section['Ix']} \\, cm^4")
    with c2:
        st.markdown("**Bolt Properties:**")
        st.latex(f"Dia (\\O) = {bolt_dia} \\, mm")
        st.latex(f"Load: {load_pct}\\% \\, of \\, V_n")

    st.markdown("---")

    # Part 2: Design Loads
    st.subheader("2. แรงเฉือนออกแบบ (Design Shear Force)")
    Ab = 3.1416 * (bolt_dia/10/2)**2
    st.latex(r"A_w = d \times t_w")
    st.latex(f"V_{{n(beam)}} = 0.60 \\times {Fy} \\times {section['d']*section['tw']:.2f} = {res['Vn_beam']:,.2f} \\, kg")
    st.latex(f"V_{{u(design)}} = V_{{n(beam)}} \\times {load_pct}\\% = \\mathbf{{{res['V_target']:,.0f} \\, kg}}")
    
    st.markdown("---")

    # Part 3: Bolt Design
    st.subheader("3. การออกแบบจุดต่อสลักเกลียว (Bolt Design)")
    st.latex(f"A_b = {Ab:.3f} \\, cm^2")
    st.latex(r"\phi R_n = 0.75 \times 0.45 \times F_{ub} \times A_b")
    st.latex(f"\\phi R_n = 0.75 \\times 0.45 \\times {Fub} \\times {Ab:.3f} = {res['phiRn_bolt']:,.2f} \\, kg/bolt")
    st.latex(f"N = \\frac{{{res['V_target']:,.0f}}}{{{res['phiRn_bolt']:,.0f}}} = {res['V_target']/res['phiRn_bolt']:.2f} \\rightarrow \\mathbf{{{res['Bolt Qty']} \\, pcs.}}")
    
    st.markdown("---")

    # Part 4: Safe Span
    st.subheader("4. การวิเคราะห์ระยะปลอดภัย (Safe Span Analysis)")
    st.latex(f"M_n = {section['Zx']} \\times {Fy} = {section['Zx']*Fy:,.0f} \\, kg\\cdot cm")
    st.latex(f"L_{{moment}} = \\frac{{4 \\times M_n}}{{V_u}} = \\mathbf{{{res['L_crit_moment']:.2f} \\, m}}")
    st.latex(f"L_{{defl}} = \\sqrt{{\\frac{{384 E I}}{{3600 V_u}}}} = \\mathbf{{{res['L_crit_defl']:.2f} \\, m}}")

    st.success(f"✅ **Safe Max Span: {res['L_safe']:.2f} m**")

# --- 🟢 ส่วนที่เพิ่มใหม่เพื่อแก้ Error (Compatibility Fix) ---
def render_report_tab(beam_data, conn_data):
    """
    Wrapper function to handle calls from app.py
    แปลงข้อมูลจาก Dictionary มาเป็น Argument ที่ถูกต้อง
    """
    # ดึงค่าจาก conn_data (ใช้ .get เพื่อกัน error กรณี key ไม่ตรง)
    load_pct = conn_data.get('load_pct', conn_data.get('load_percent', 50))
    bolt_dia = conn_data.get('bolt_dia', conn_data.get('bolt_diameter', 16))
    factor = conn_data.get('factor', conn_data.get('safety_factor', 1.0))
    load_case = conn_data.get('load_case', conn_data.get('load_case_name', 'Design Load'))

    # เรียกฟังก์ชันหลัก
    render_detailed_report(beam_data, load_pct, bolt_dia, factor, load_case)
