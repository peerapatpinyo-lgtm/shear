import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. DATABASE
# ==========================================
steel_db = {
    "H 150x75x5x7":     {"h": 150, "b": 75,  "tw": 5,   "tf": 7,   "Ix": 666,    "Zx": 88.8,  "w": 14.0},
    "H 175x90x5x8":     {"h": 175, "b": 90,  "tw": 5,   "tf": 8,   "Ix": 1210,   "Zx": 138,   "w": 18.1},
    "H 200x100x5.5x8": {"h": 200, "b": 100, "tw": 5.5, "tf": 8,   "Ix": 1840,   "Zx": 184,   "w": 21.3},
    "H 250x125x6x9":    {"h": 250, "b": 125, "tw": 6,   "tf": 9,   "Ix": 3690,   "Zx": 295,   "w": 29.6},
    "H 300x150x6.5x9": {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481,   "w": 36.7},
    "H 350x175x7x11":  {"h": 350, "b": 175, "tw": 7,   "tf": 11,  "Ix": 13600,  "Zx": 775,   "w": 49.6},
    "H 400x200x8x13":  {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190,  "w": 66.0},
    "H 450x200x9x14":  {"h": 450, "b": 200, "tw": 9,   "tf": 14,  "Ix": 33500,  "Zx": 1490,  "w": 76.0},
    "H 500x200x10x16": {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910,  "w": 89.6},
    "H 600x200x11x17": {"h": 600, "b": 200, "tw": 11,  "tf": 17,  "Ix": 77600,  "Zx": 2590,  "w": 106},
}

st.set_page_config(page_title="Standard Connection Finder", layout="centered", page_icon="🔩")

# ==========================================
# 2. FUNCTIONS
# ==========================================
def draw_bolt_layout(n_bolts, bolt_size):
    if n_bolts == 0: return go.Figure()
    
    # Layout Logic
    cols = 2 if n_bolts > 3 else 1
    rows = math.ceil(n_bolts / cols)
    
    s_x, s_y = 80, 70
    x_coords, y_coords = [], []
    
    start_x = -s_x/2 if cols == 2 else 0
    start_y = (rows - 1) * s_y / 2
    
    count = 0
    for r in range(rows):
        current_y = start_y - (r * s_y)
        for c in range(cols):
            if count >= n_bolts: break
            current_x = start_x + (c * s_x)
            x_coords.append(current_x)
            y_coords.append(current_y)
            count += 1
            
    fig = go.Figure()
    # Plate
    p_w = (cols-1)*s_x + 100
    p_h = (rows-1)*s_y + 80
    fig.add_shape(type="rect", x0=-p_w/2, y0=-p_h/2, x1=p_w/2, y1=p_h/2, line=dict(color="Gray"), fillcolor="#E5E7EB", opacity=0.5)
    
    # Bolts
    dia = int(bolt_size[1:])
    fig.add_trace(go.Scatter(
        x=x_coords, y=y_coords, mode='markers', 
        marker=dict(size=dia*1.2, color='#1F2937', symbol='circle', line=dict(width=2, color='white')),
        name='Bolt'
    ))
    
    fig.update_layout(
        title=dict(text=f"Standard Detail: {n_bolts}-{bolt_size}", y=0.9),
        xaxis=dict(visible=False, range=[-200, 200]),
        yaxis=dict(visible=False, range=[-250, 250]),
        height=350, width=350, margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="white"
    )
    return fig

# ==========================================
# 3. UI & LOGIC
# ==========================================
st.title("🔩 Standard Connection Finder")
st.markdown("ระบุ **หน้าตัด** เพื่อหาค่าแรงเฉือนที่ **เหมาะสม (Typical)** และจำนวน Bolt ที่แนะนำ")

# --- Inputs ---
col1, col2 = st.columns([1.5, 1])
with col1:
    section_name = st.selectbox("เลือกขนาดเหล็ก (Section)", list(steel_db.keys()), index=4)
with col2:
    bolt_size = st.selectbox("ขนาด Bolt", ["M12", "M16", "M20", "M22", "M24"], index=2)

# --- Constants ---
fy = 2400
props = steel_db[section_name]

# --- CALCULATIONS ---

# 1. Max Shear Capacity (Web Yielding) - ค่าสูงสุดทางทฤษฎี
# V_max = 0.4 * Fy * Aw
Aw = (props['h']/10) * (props['tw']/10) # cm2
V_max_web = 0.4 * fy * Aw # kg

# 2. Typical / Balanced Shear (The "Appropriate" Value)
# Logic: สมมติคานยาว 10 เท่าของความลึก (Span 10D) ซึ่งเป็นจุดที่คานรับโมเมนต์เต็มที่
# V_typical = (4 * M_allow) / L_10d
M_allow = 0.6 * fy * props['Zx'] # kg.cm
L_typical = 10 * (props['h']/10) # cm (10 times depth)
V_typical = (4 * M_allow) / L_typical # kg

# 3. Bolt Calculation
# Bolt Shear Strength (Single Shear Assumption for simple tab)
b_areas = {"M12": 1.13, "M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}
bolt_area = b_areas[bolt_size]
phi_bolt_shear = 1000 * bolt_area # Approx 1.0 ton/cm2 shear strength

# Bearing Strength Check (Web thickness)
d_bolt = int(bolt_size[1:])/10 # cm
t_web = props['tw']/10 # cm
phi_bearing = 1.2 * 4000 * d_bolt * t_web # SS400 Plate (Fu=4000)

bolt_cap_per_one = min(phi_bolt_shear, phi_bearing)
gov_mode = "Shear Cut" if phi_bolt_shear < phi_bearing else "Bearing (Web ฉีก)"

# Calculate Number of Bolts based on Typical Load
n_req = math.ceil(V_typical / bolt_cap_per_one)

# --- DISPLAY RESULTS ---
st.divider()

# Header Result
st.subheader(f"ผลลัพธ์สำหรับ: {section_name}")

# Metrics Row
m1, m2, m3 = st.columns(3)
m1.metric("1. Web Capacity (Max)", f"{V_max_web:,.0f} kg", help="ความสามารถรับแรงเฉือนสูงสุดของเอวคาน (ห้ามเกินนี้)")
m2.metric("2. Typical Load (แนะนำ)", f"{V_typical:,.0f} kg", help="แรงเฉือนที่เหมาะสมสำหรับ Span ประมาณ 10 เท่าของความลึก (ใช้ค่านี้ออกแบบจุดต่อ)")
m3.metric("3. จำนวน Bolt ที่เหมาะสม", f"{n_req} x {bolt_size}", help=f"คำนวณจากแรง Typical Load หารด้วยกำลังน็อต ({bolt_cap_per_one:,.0f} kg/ตัว)")

# Details & Layout
c_info, c_plot = st.columns([1.2, 1])

with c_info:
    st.info(f"""
    **💡 หลักการคำนวณความคุ้มค่า (Typical Logic):**
    
    เราคำนวณหาแรงเฉือน ($V$) ที่เกิดขึ้นเมื่อคานรับโมเมนต์ได้เต็มที่ ($M_{{max}}$) 
    ที่ความยาวช่วงพาดมาตรฐาน ($L = 10 \\times Depth$)
    
    * **Max Web Capacity:** {V_max_web:,.0f} kg (ค่าทฤษฎีสูงสุด)
    * **Design Load (10D):** {V_typical:,.0f} kg (ค่าที่ใช้จริงส่วนใหญ่)
    * **Ratio:** Typical คิดเป็น **{(V_typical/V_max_web)*100:.0f}%** ของ Web Cap
    
    ---------------------------
    **การตรวจสอบ Bolt ({bolt_size}):**
    * Bolt Shear Cap: {phi_bolt_shear:,.0f} kg/ตัว
    * Web Bearing Cap: {phi_bearing:,.0f} kg/ตัว (เช็คความหนาเอวคาน {props['tw']} mm)
    * **Control Capacity:** {bolt_cap_per_one:,.0f} kg/ตัว ({gov_mode})
    """)

with c_plot:
    st.plotly_chart(draw_bolt_layout(n_req, bolt_size), use_container_width=True)
