import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math
from scipy.interpolate import interp1d

# ==========================================
# 1. SETUP & STYLE
# ==========================================
st.set_page_config(page_title="Smart Beam Solver V4", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .highlight-card { background-color: #e8f6f3; padding: 20px; border-radius: 10px; border: 1px solid #1abc9c; }
    .solver-box { background-color: #fcf3cf; padding: 15px; border-radius: 8px; border-left: 5px solid #f1c40f; margin-bottom: 15px; }
    .metric-box { text-align: center; padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-top: 3px solid #3498db; }
    .big-num { font-size: 24px; font-weight: bold; color: #17202a; }
    .sub-text { font-size: 14px; color: #7f8c8d; margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE & INPUTS
# ==========================================
steel_db = {
    "H 150x75x5x7":     {"h": 150, "b": 75,  "tw": 5,   "tf": 7,   "Ix": 666,    "Zx": 88.8,  "w": 14.0},
    "H 200x100x5.5x8":  {"h": 200, "b": 100, "tw": 5.5, "tf": 8,   "Ix": 1840,   "Zx": 184,   "w": 21.3},
    "H 250x125x6x9":    {"h": 250, "b": 125, "tw": 6,   "tf": 9,   "Ix": 3690,   "Zx": 295,   "w": 29.6},
    "H 300x150x6.5x9":  {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481,   "w": 36.7},
    "H 350x175x7x11":   {"h": 350, "b": 175, "tw": 7,   "tf": 11,  "Ix": 13600,  "Zx": 775,   "w": 49.6},
    "H 400x200x8x13":   {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190,  "w": 66.0},
    "H 450x200x9x14":   {"h": 450, "b": 200, "tw": 9,   "tf": 14,  "Ix": 33500,  "Zx": 1490,  "w": 76.0},
    "H 500x200x10x16":  {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910,  "w": 89.6},
    "H 600x200x11x17":  {"h": 600, "b": 200, "tw": 11,  "tf": 17,  "Ix": 77600,  "Zx": 2590,  "w": 106},
}

with st.sidebar:
    st.title("Smart Beam Solver V4")
    st.divider()
    sec_name = st.selectbox("Select Section", list(steel_db.keys()), index=3)
    
    st.header("🎯 Solver Target")
    target_usage = st.slider("Target Shear Usage (%)", 50, 100, 75, 5)
    
    st.header("🔩 Connection")
    bolt_size = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)
    
    # Constants
    fy = 2400
    E_mod = 2.04e6 
    defl_lim_val = 360

# ==========================================
# 3. LOGIC & SOLVER
# ==========================================
p = steel_db[sec_name]
h_cm = p['h']/10
tw_cm = p['tw']/10
Aw = h_cm * tw_cm
Ix = p['Ix']
Zx = p['Zx']

# Capacities
M_cap = 0.6 * fy * Zx
V_cap = 0.4 * fy * Aw 

# 3.1 Loop Calculation (0.5m to 20m)
spans = np.linspace(0.5, 20, 200) # ละเอียดเพื่อหาจุดตัด
v_usages = []
gov_loads = []
gov_causes = []

for L in spans:
    L_cm = L * 100
    
    # Calculate Max Allowable Load for each criteria
    w_s = (2 * V_cap) / L_cm * 100
    w_m = (8 * M_cap) / (L_cm**2) * 100
    w_d = ((L_cm/defl_lim_val) * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100
    
    # Governing Load
    w_gov = min(w_s, w_m, w_d)
    
    # Calculate Resulting Shear at this Max Load
    V_act = w_gov * L / 2
    usage = (V_act / V_cap) * 100
    
    v_usages.append(usage)
    gov_loads.append(w_gov)
    
    if w_gov == w_s: gov_causes.append("Shear")
    elif w_gov == w_m: gov_causes.append("Moment")
    else: gov_causes.append("Deflection")

# 3.2 SOLVER: Find span where usage crosses Target
# ใช้ Interpolation เพื่อหาค่า Span ที่แม่นยำที่สุดที่ทำให้ Usage = Target
try:
    # เราต้อง reverse list เพราะฟังก์ชัน interp1d ชอบค่า x ที่เรียงจากน้อยไปมาก
    # แต่กราฟ Shear usage มันลดลงเรื่อยๆ (Monotonic decreasing usually)
    # ตัดช่วงที่ usage นิ่งๆ (100%) ออกไปก่อนเพื่อให้ interpolate แม่น
    
    # สร้างฟังก์ชัน f(usage) = span
    solver_func = interp1d(v_usages, spans, kind='linear', fill_value="extrapolate")
    
    solved_span = float(solver_func(target_usage))
    
    # Clamp value
    if solved_span < 0.5: solved_span = 0.5
    if solved_span > 20: solved_span = 20
    
    # Recalculate exact values at solved span
    L_sol = solved_span
    L_sol_cm = L_sol * 100
    w_s = (2 * V_cap) / L_sol_cm * 100
    w_m = (8 * M_cap) / (L_sol_cm**2) * 100
    w_d = ((L_sol_cm/defl_lim_val) * 384 * E_mod * Ix) / (5 * (L_sol_cm**4)) * 100
    w_sol = min(w_s, w_m, w_d)
    
    V_sol = w_sol * L_sol / 2
    M_sol = w_sol * L_sol**2 / 8
    
    found_solution = True
    
except:
    found_solution = False
    solved_span = 0
    V_sol = 0

# 3.3 Connection Calculation
dia_mm = int(bolt_size[1:])
dia_cm = dia_mm/10
b_area = 3.14 if bolt_size=="M20" else (2.01 if bolt_size=="M16" else 3.8)
v_bolt = min(1000 * b_area, 1.2 * 4000 * dia_cm * tw_cm)
req_bolt = math.ceil(V_sol / v_bolt) if found_solution else 0

# ==========================================
# 4. UI DISPLAY
# ==========================================
st.subheader(f"🔍 Logic: Find Span where Shear Usage = {target_usage}%")

if found_solution and 0.5 < solved_span < 20:
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.markdown(f"""
        <div class="solver-box">
            <h3 style="margin:0; color:#b7950b;">🎯 Solved!</h3>
            <div class="sub-text">To reach <b>{target_usage}%</b> Shear Usage, the beam span is:</div>
            <div class="big-num" style="font-size:32px;">{solved_span:.2f} m.</div>
            <hr style="border-top: 1px solid #f7dc6f;">
            <div class="sub-text">Max Safe Load at this span:</div>
            <div style="font-weight:bold; font-size:18px;">{w_sol:,.0f} kg/m</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="highlight-card">
            <h4 style="margin:0;">⚙️ Connection Design</h4>
            <div class="sub-text">Design Shear (V at {target_usage}% Cap)</div>
            <div class="big-num" style="color:#e74c3c;">{V_sol:,.0f} kg</div>
            <div class="sub-text">Shear Capacity: {V_cap:,.0f} kg</div>
            <hr>
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:16px;">Required:</span>
                <span style="font-size:24px; font-weight:bold; color:#2980b9;">{req_bolt} x {bolt_size}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        # PLOT
        fig = go.Figure()
        
        # 1. Shear Usage Curve
        fig.add_trace(go.Scatter(x=spans, y=v_usages, mode='lines', name='Shear Usage (%)', line=dict(color='#3498db', width=3)))
        
        # 2. Target Line
        fig.add_hline(y=target_usage, line_dash="dash", line_color="red", annotation_text=f"Target {target_usage}%")
        
        # 3. Intersection Point
        fig.add_trace(go.Scatter(
            x=[solved_span], y=[target_usage],
            mode='markers+text',
            marker=dict(size=14, color='red', symbol='x'),
            text=[f"Span {solved_span:.2f}m"],
            textposition="top right",
            name='Design Point'
        ))
        
        # 4. Limit Zones (Optional background)
        # หาจุดเปลี่ยนจาก Shear Control เป็น Moment Control
        # เพื่อแสดงว่าช่วงไหน Shear Usage = 100%
        
        fig.update_layout(
            title=f"Shear Usage vs Span Length ({sec_name})",
            xaxis_title="Span Length (m)",
            yaxis_title="Shear Capacity Usage (%)",
            yaxis_range=[0, 110],
            height=450,
            hovermode="x unified"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.info(f"💡 **คำอธิบาย:** ที่ช่วงความยาวสั้นมากๆ คานจะพังด้วย Shear (Usage 100%) แต่เมื่อคานยาวขึ้นถึง **{solved_span:.2f} ม.** โมเมนต์ดัดจะเริ่มคุมการออกแบบ ทำให้เราใส่ Load ได้น้อยลง ส่งผลให้แรงเฉือนจริงลดลงเหลือ **{target_usage}%** ของความสามารถหน้าตัด")

else:
    st.error("ไม่สามารถหาค่า Span ที่ตรงกับเงื่อนไขได้ (ค่า Shear อาจจะต่ำกว่า Target ตลอดช่วง หรือ สูงกว่าตลอดช่วง)")
    st.dataframe(pd.DataFrame({"Span": spans, "Usage": v_usages}))
