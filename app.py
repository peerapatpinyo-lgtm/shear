import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ==========================================
# 1. SETUP & STYLE
# ==========================================
st.set_page_config(page_title="Engineering Calc Sheet", layout="wide", page_icon="📐")

st.markdown("""
<style>
    .math-box { 
        background-color: white; 
        padding: 20px; 
        border-radius: 10px; 
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .optimal-box {
        background-color: #e8f8f5;
        border-left: 5px solid #27ae60;
        padding: 15px;
        border-radius: 5px;
    }
    .header-sub { color: #2c3e50; font-weight: bold; font-size: 18px; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE & INPUTS
# ==========================================
steel_db = {
    "H 300x150x6.5x9": {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481,   "w": 36.7},
    "H 350x175x7x11":  {"h": 350, "b": 175, "tw": 7,   "tf": 11,  "Ix": 13600,  "Zx": 775,   "w": 49.6},
    "H 400x200x8x13":  {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190,  "w": 66.0},
    "H 450x200x9x14":  {"h": 450, "b": 200, "tw": 9,   "tf": 14,  "Ix": 33500,  "Zx": 1490,  "w": 76.0},
    "H 500x200x10x16": {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910,  "w": 89.6},
}

with st.sidebar:
    st.header("⚙️ Design Parameters")
    sec_name = st.selectbox("Section Size", list(steel_db.keys()), index=2)
    p = steel_db[sec_name]
    
    fy = st.number_input("Yield Strength ($F_y$)", value=2400)
    E_mod = 2.04e6 # ksc

# ==========================================
# 3. CALCULATION LOGIC
# ==========================================
# Constants
h_cm = p['h']/10
tw_cm = p['tw']/10
Aw = h_cm * tw_cm
Ix, Zx = p['Ix'], p['Zx']

# 1. Optimal Span Logic (Rule of Thumb: L/d = 15 to 20)
d_meter = p['h'] / 1000
opt_min = 15 * d_meter
opt_max = 20 * d_meter

# 2. Capacity Constants
V_allow = 0.4 * fy * Aw      # kg
M_allow = 0.6 * fy * Zx      # kg.cm

# ==========================================
# 4. MAIN DISPLAY
# ==========================================
st.title("📐 Beam Analysis: Optimal Span & Detailed Calcs")

col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.markdown("### 1️⃣ เลือกความยาวคาน (Span Selection)")
    
    # --- OPTIMAL SPAN EXPLANATION ---
    st.markdown(f"""
    <div class="optimal-box">
        <div class="header-sub">🎯 ช่วงความยาวที่เหมาะสม (Optimal Span)</div>
        <p>สำหรับคานเหล็ก (Floor Beam) โดยทั่วไปเราใช้เกณฑ์อัตราส่วนความลึกต่อความยาว (Depth Ratio) เพื่อประหยัดและควบคุมการแอ่นตัว:</p>
        <ul>
            <li><b>Rule of Thumb:</b> $L/d \\approx 15 - 20$</li>
            <li><b>Section Depth (d):</b> {d_meter:.2f} m</li>
            <li><b>แนะนำช่วง:</b> <b>{opt_min:.1f} - {opt_max:.1f} เมตร</b></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Slider
    sel_span = st.slider("ความยาวคานที่ต้องการออกแบบ (เมตร)", 2.0, 16.0, (opt_min+opt_max)/2, 0.5)
    
    # Status Check relative to Optimal
    if sel_span < opt_min:
        st.warning(f"⚠️ **Short Span:** คานสั้นกว่าช่วงแนะนำ (อาจจะ Overdesign หรือเปลืองเหล็กโดยใช่เหตุ เพราะ Shear จะสูง)")
    elif sel_span > opt_max:
        st.warning(f"⚠️ **Long Span:** คานยาวกว่าช่วงแนะนำ (ระวังเรื่องการแอ่นตัว Deflection จะเป็นตัวควบคุม)")
    else:
        st.success(f"✅ **Optimal:** ความยาวอยู่ในช่วงที่เหมาะสม")

with col_right:
    st.markdown("### 2️⃣ รายการคำนวณละเอียด (Detailed Calculation)")
    
    # Calc values for display
    L_cm = sel_span * 100
    
    # --- FORMULA RENDERING ---
    st.markdown('<div class="math-box">', unsafe_allow_html=True)
    
    # 1. SHEAR CALCULATION
    st.markdown("**A. ตรวจสอบแรงเฉือน (Shear Control)**")
    st.markdown("แรงเฉือนสูงสุดที่หน้าตัดรับได้ (Web Yielding):")
    st.latex(r'''
        V_{allow} = 0.4 \cdot F_y \cdot A_w
    ''')
    st.latex(f'''
        V_{{allow}} = 0.4 \\cdot {fy} \\cdot ({h_cm} \\times {tw_cm}) = \\mathbf{{{V_allow:,.0f}}} \\; kg
    ''')
    
    st.markdown(f"แปลงเป็น Uniform Load ($w_v$) ที่ความยาว $L = {sel_span} m$:")
    val_s = (2 * V_allow) / L_cm * 100 # kg/m
    st.latex(r'''
        w_v = \frac{2 \cdot V_{allow}}{L}
    ''')
    st.latex(f'''
        w_v = \\frac{{2 \\cdot {V_allow:,.0f}}}{{{sel_span}}} = \\mathbf{{{val_s:,.0f}}} \\; kg/m
    ''')

    st.markdown("---")

    # 2. MOMENT CALCULATION
    st.markdown("**B. ตรวจสอบโมเมนต์ (Moment Control)**")
    st.markdown("โมเมนต์สูงสุดที่หน้าตัดรับได้ (Allowable Bending):")
    st.latex(r'''
        M_{allow} = 0.6 \cdot F_y \cdot Z_x
    ''')
    st.latex(f'''
        M_{{allow}} = 0.6 \\cdot {fy} \\cdot {Zx} = \\mathbf{{{M_allow:,.0f}}} \\; kg \cdot cm
    ''')
    
    st.markdown(f"แปลงเป็น Uniform Load ($w_m$) ที่ความยาว $L = {sel_span} m$:")
    val_m = (8 * M_allow) / (L_cm**2) * 100
    st.latex(r'''
        w_m = \frac{8 \cdot M_{allow}}{L^2}
    ''')
    st.latex(f'''
        w_m = \\frac{{8 \\cdot {M_allow:,.0f}}}{{ ({sel_span} \\cdot 100)^2 }} \\times 100 = \\mathbf{{{val_m:,.0f}}} \\; kg/m
    ''')
    
    st.markdown("---")

    # 3. DEFLECTION CALCULATION
    st.markdown("**C. ตรวจสอบการแอ่นตัว (Deflection Control)**")
    st.markdown(f"ระยะแอ่นตัวที่ยอมให้ ($L/360$):")
    delta_allow = L_cm / 360
    st.latex(f'''
        \Delta_{{allow}} = \\frac{{L}}{{360}} = \\frac{{{sel_span} \\cdot 100}}{{360}} = {delta_allow:.2f} \\; cm
    ''')
    
    st.markdown("คำนวณ Load ที่ทำให้แอ่นตัวถึงพิกัด:")
    val_d = (delta_allow * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100
    st.latex(r'''
        w_{\delta} = \frac{384 \cdot E \cdot I \cdot \Delta_{allow}}{5 \cdot L^4}
    ''')
    st.latex(f'''
        w_{{\delta}} = \\frac{{384 \\cdot {E_mod:.2e} \\cdot {Ix} \\cdot {delta_allow:.2f}}}{{5 \cdot ({sel_span} \\cdot 100)^4}} \\times 100 = \\mathbf{{{val_d:,.0f}}} \\; kg/m
    ''')

    st.markdown('</div>', unsafe_allow_html=True) # Close box

    # --- SUMMARY ---
    final_w = min(val_s, val_m, val_d)
    cause = "Shear" if final_w==val_s else ("Moment" if final_w==val_m else "Deflection")
    
    st.info(f"""
    🏆 **สรุป:** คานยาว {sel_span} เมตร รับน้ำหนักแผ่ได้ปลอดภัยสูงสุด
    ### {final_w:,.0f} kg/m
    (ควบคุมโดย: **{cause}**)
    """)
