import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. ตั้งค่าหน้าเว็บ
# ==========================================
st.set_page_config(page_title="Beam Insight V11 (Fixed)", layout="wide", page_icon="🏗️")

# CSS ตกแต่งเล็กน้อย (เอาเฉพาะที่จำเป็นเพื่อให้ดูง่าย)
st.markdown("""
<style>
    .highlight-card { 
        background-color: #f0f8ff; 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 5px solid #3498db;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .metric-container {
        text-align: center;
        padding: 15px;
        background: white;
        border: 1px solid #ddd;
        border-radius: 8px;
    }
    .big-font { font-size: 24px; font-weight: bold; color: #333; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ฐานข้อมูลเหล็ก (เหมือนเดิม)
# ==========================================
steel_db = {
    "H 150x75x5x7":     {"h": 150, "b": 75,  "tw": 5,   "tf": 7,   "Ix": 666,    "Zx": 88.8},
    "H 200x100x5.5x8":  {"h": 200, "b": 100, "tw": 5.5, "tf": 8,   "Ix": 1840,   "Zx": 184},
    "H 250x125x6x9":    {"h": 250, "b": 125, "tw": 6,   "tf": 9,   "Ix": 3690,   "Zx": 295},
    "H 300x150x6.5x9":  {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481},
    "H 350x175x7x11":   {"h": 350, "b": 175, "tw": 7,   "tf": 11,  "Ix": 13600,  "Zx": 775},
    "H 400x200x8x13":   {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190},
    "H 500x200x10x16":  {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910},
}

material_db = {
    "SS400 (เหล็กทั่วไป)": {"Fy": 2400, "Fu": 4100},
    "SM520 (เหล็กกำลังสูง)": {"Fy": 3600, "Fu": 5300}
}

# ==========================================
# 3. ส่วนรับค่า (Sidebar)
# ==========================================
with st.sidebar:
    st.header("⚙️ ตั้งค่าโครงสร้าง")
    sec_name = st.selectbox("เลือกขนาดหน้าตัด", list(steel_db.keys()), index=4)
    mat_name = st.selectbox("เกรดเหล็ก", list(material_db.keys()))
    user_span = st.number_input("ความยาวคาน (เมตร)", min_value=1.0, value=6.0, step=0.5)
    
    st.divider()
    st.header("🔩 ตั้งค่าน็อต")
    bolt_size = st.selectbox("ขนาดน็อต", ["M16", "M20", "M22", "M24"], index=1)

# ==========================================
# 4. คำนวณ (Engine)
# ==========================================
# ดึงค่า
p = steel_db[sec_name]
mat = material_db[mat_name]
fy, fu = mat["Fy"], mat["Fu"]
E_mod = 2.04e6
defl_lim = 360 # L/360

# แปลงหน่วย
h_cm, tw_cm = p['h']/10, p['tw']/10
Aw = h_cm * tw_cm
Zx = p['Zx']
Ix = p['Ix']

# ขีดจำกัด (Capacity)
V_cap = 0.4 * fy * Aw
M_cap = 0.6 * fy * Zx

# หา Load Safe สูงสุด (คำนวณย้อนกลับ)
L_cm = user_span * 100
delta_allow = L_cm / defl_lim

w_shear = (2 * V_cap) / L_cm * 100         # kg/m
w_moment = (8 * M_cap) / (L_cm**2) * 100   # kg/m
w_defl = (delta_allow * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100 # kg/m

# สรุป Load ที่ปลอดภัยที่สุด
safe_load = min(w_shear, w_moment, w_defl)

# หาตัวควบคุม
if safe_load == w_shear: cause = "Shear (แรงเฉือน)"
elif safe_load == w_moment: cause = "Moment (แรงดัด)"
else: cause = "Deflection (การแอ่นตัว)"

# หาแรงจริงที่เกิดขึ้น (Actual Force) เมื่อใส่ Safe Load
V_act = safe_load * user_span / 2
M_act = safe_load * user_span**2 / 8
delta_act = (5 * (safe_load/100) * L_cm**4) / (384 * E_mod * Ix)

# ==========================================
# 5. แสดงผล (Display) - แก้ใหม่ให้ไม่งง
# ==========================================
st.title(f"ผลวิเคราะห์: {sec_name} ยาว {user_span} เมตร")

# --- การ์ดสรุปผล ---
st.markdown(f"""
<div class="highlight-card">
    <h3 style="margin:0; color:#2c3e50;">น้ำหนักปลอดภัยสูงสุด (Safe Load)</h3>
    <p style="font-size: 36px; font-weight: bold; color: #2980b9; margin: 10px 0;">
        {safe_load:,.0f} <span style="font-size:20px; color:black;">kg/m</span>
    </p>
    <p style="color: #7f8c8d;">
        ⚠️ ถูกจำกัดโดย: <b>{cause}</b> <br>
        (แปลว่าถ้าใส่น้ำหนักเกินนี้ คานจะพังด้วยอาการนี้ก่อนเพื่อน)
    </p>
</div>
<br>
""", unsafe_allow_html=True)

# --- กราฟแท่ง 3 ช่อง (ใช้ st.progress ปกติ ไม่ใช้ HTML ซับซ้อน) ---
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### ✂️ แรงเฉือน (Shear)")
    st.markdown(f"**{V_act:,.0f}** / {V_cap:,.0f} kg")
    pct_v = V_act / V_cap
    st.progress(min(pct_v, 1.0))
    st.caption(f"ใช้งาน {pct_v*100:.1f}%")

with col2:
    st.markdown("### 🪵 แรงดัด (Moment)")
    st.markdown(f"**{M_act:,.0f}** / {M_cap/100:,.0f} kg.m")
    pct_m = (M_act*100) / M_cap
    st.progress(min(pct_m, 1.0))
    st.caption(f"ใช้งาน {pct_m*100:.1f}%")

with col3:
    st.markdown("### 〰️ การแอ่น (Deflection)")
    st.markdown(f"**{delta_act:.2f}** / {delta_allow:.2f} cm")
    pct_d = delta_act / delta_allow
    st.progress(min(pct_d, 1.0))
    st.caption(f"ใช้งาน {pct_d*100:.1f}%")

st.divider()

# --- ส่วนอธิบายที่มา (แก้ใหม่! ไม่ใช้ HTML ยึกยือแล้ว) ---
with st.expander("🕵️‍♂️ ดูวิธีคำนวณ (ที่มาของตัวเลข)", expanded=True):
    st.write("#### 1. ข้อมูลเบื้องต้น")
    st.write(f"- หน้าตัด: **{sec_name}**, เกรด: **{mat_name}**")
    st.write(f"- ค่า Ix (ความแข็ง): {Ix:,.0f} cm⁴, Zx (ต้านโมเมนต์): {Zx:,.0f} cm³")
    
    st.write("---")
    
    st.write("#### 2. ตรวจสอบทีละเงื่อนไข (เพื่อหาน้ำหนักปลอดภัย)")
    
    # แสดงผลแบบสะอาดๆ ด้วย st.success/warning
    st.markdown("**กรณี A: แรงเฉือน (Shear)**")
    st.latex(r"V_{max} = 0.4 \times F_y \times A_w")
    st.write(f"รับได้สูงสุด = {V_cap:,.0f} kg → แปลงเป็น load ได้ = **{w_shear:,.0f} kg/m**")
    
    st.markdown("**กรณี B: แรงดัด (Moment)**")
    st.latex(r"M_{max} = 0.6 \times F_y \times Z_x")
    st.write(f"รับได้สูงสุด = {M_cap:,.0f} kg.cm → แปลงเป็น load ได้ = **{w_moment:,.0f} kg/m**")
    
    st.markdown("**กรณี C: การแอ่นตัว (Deflection)**")
    st.latex(r"\Delta_{allow} = L/360")
    st.write(f"ยอมให้แอ่นได้ {delta_allow:.2f} cm → แปลงเป็น load ได้ = **{w_defl:,.0f} kg/m**")
    
    st.info(f"👉 **สรุป:** ค่าน้อยที่สุดคือ **{safe_load:,.0f} kg/m** (มาจากกรณี {cause})")

# --- Tab 2: จุดต่อ (แถมให้เหมือนเดิม) ---
st.divider()
st.subheader("🔩 ตรวจสอบจุดต่อ (Connection)")
dia = int(bolt_size[1:])/10
cap_bolt = min(1000 * 3.14, 1.2 * fu * dia * tw_cm) # คิดคร่าวๆ
req_bolt = math.ceil(V_act / cap_bolt)
if req_bolt < 2: req_bolt = 2

c_img, c_txt = st.columns([1,2])
with c_txt:
    st.success(f"แรงเฉือนที่เกิดขึ้น: **{V_act:,.0f} kg**")
    st.write(f"ใช้น็อต **{bolt_size}** (รับได้ {cap_bolt:,.0f} kg/ตัว)")
    st.write(f"ต้องใช้จำนวน: **{req_bolt} ตัว**")

with c_img:
    # วาดออกแบบง่ายๆ
    fig = go.Figure()
    fig.add_shape(type="rect", x0=0, y0=0, x1=50, y1=p['h'], line=dict(color="blue"))
    y_pos = np.linspace(p['h']*0.2, p['h']*0.8, req_bolt)
    fig.add_trace(go.Scatter(x=[25]*req_bolt, y=y_pos, mode='markers', marker=dict(size=15, color='red'), name='Bolt'))
    fig.update_layout(height=200, margin=dict(l=0,r=0,t=0,b=0), xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, use_container_width=True)
