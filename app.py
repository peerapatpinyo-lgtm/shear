import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. STYLE: CLEAN & MINIMAL
# ==========================================
st.set_page_config(page_title="Smart Beam Analyst", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .main-metric { font-size: 32px; font-weight: bold; color: #2e86c1; }
    .sub-metric { font-size: 14px; color: #566573; }
    .card { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); border-top: 4px solid #AED6F1; }
    .status-box { padding: 10px; border-radius: 5px; margin-top: 5px; font-weight: bold; font-size: 14px; }
    .ok { background-color: #D4EFDF; color: #196F3D; border: 1px solid #A9DFBF; }
    .warning { background-color: #FADBD8; color: #943126; border: 1px solid #F5B7B1; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA & LOGIC
# ==========================================
steel_db = {
    "H 300x150x6.5x9": {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481,   "w": 36.7},
    "H 350x175x7x11":  {"h": 350, "b": 175, "tw": 7,   "tf": 11,  "Ix": 13600,  "Zx": 775,   "w": 49.6},
    "H 400x200x8x13":  {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190,  "w": 66.0},
    "H 450x200x9x14":  {"h": 450, "b": 200, "tw": 9,   "tf": 14,  "Ix": 33500,  "Zx": 1490,  "w": 76.0},
    "H 500x200x10x16": {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910,  "w": 89.6},
}

def calc_block_shear(n_bolts, dia_bolt, t_web, Fu=4000, Fy=2400):
    if n_bolts < 2: return 999999 # Needs >1 bolt
    d_hole = dia_bolt + 0.2
    # Standard Layout Estimate
    pitch, edge_v, edge_h = 3*dia_bolt, 1.5*dia_bolt, 1.5*dia_bolt
    
    L_gv = edge_v + (n_bolts-1)*pitch
    L_nv = L_gv - (n_bolts-0.5)*d_hole
    A_nv = L_nv * t_web
    A_nt = (edge_h - 0.5*d_hole) * t_web
    
    # Simple AISC Block Shear
    return (0.6 * Fu * A_nv) + (1.0 * Fu * A_nt)

# ==========================================
# 3. UI SIDEBAR
# ==========================================
with st.sidebar:
    st.header("🎛️ Settings")
    sec_name = st.selectbox("Section", list(steel_db.keys()), index=2)
    p = steel_db[sec_name]
    bolt_size = st.selectbox("Bolt", ["M20", "M22", "M24"], index=0)
    fy = 2400

# ==========================================
# 4. CALCULATION CORE
# ==========================================
# Constant Props
h_cm, tw_cm = p['h']/10, p['tw']/10
dia_cm = int(bolt_size[1:])/10
bolt_cap = min(1000 * 3.14*(dia_cm/2)**2, 1.2*4000*dia_cm*tw_cm) # Min(Shear, Bearing)
V_web_max = 0.4 * fy * (h_cm * tw_cm)
M_allow = 0.6 * fy * p['Zx']

# Generate Curve Data
spans = np.linspace(2, 16, 100)
shear_design = []
shear_limit_web = []

for L in spans:
    L_cm = L * 100
    # The smooth curve formula
    v_mom = (4 * M_allow) / L_cm 
    # The cut-off
    shear_design.append(min(v_mom, V_web_max))
    shear_limit_web.append(V_web_max)

# ==========================================
# 5. MAIN DISPLAY
# ==========================================
st.title("🏗️ Beam Connection Insight (Clean View)")

# --- PART 1: INTERACTIVE SLIDER ---
st.markdown("### 1️⃣ เลือกความยาวคาน (Span)")
sel_span = st.slider("เลื่อนเพื่อตรวจสอบค่าที่จุดต่างๆ (เมตร)", 2.0, 16.0, 6.0, 0.5)

# --- PART 2: REAL-TIME CHECKER ---
# Calc specific values for selected span
idx = (np.abs(spans - sel_span)).argmin()
V_active = shear_design[idx]
req_bolts = math.ceil(V_active / bolt_cap)

# Hidden Complex Check (Block Shear)
bs_cap = calc_block_shear(req_bolts, dia_cm, tw_cm)
is_bs_fail = bs_cap < V_active

col_res1, col_res2, col_res3 = st.columns(3)

with col_res1:
    st.markdown(f"""
    <div class="card">
        <div class="sub-metric">Design Shear Force (V)</div>
        <div class="main-metric">{V_active/1000:,.1f} <span style="font-size:18px">Ton</span></div>
        <div class="sub-metric">แรงเฉือนที่เกิดขึ้นจริง</div>
    </div>
    """, unsafe_allow_html=True)

with col_res2:
    st.markdown(f"""
    <div class="card" style="border-top-color: #F39C12;">
        <div class="sub-metric">Bolts Required ({bolt_size})</div>
        <div class="main-metric">{req_bolts} <span style="font-size:18px">ตัว</span></div>
        <div class="sub-metric">Capacity: {bolt_cap/1000:.1f} T/ตัว</div>
    </div>
    """, unsafe_allow_html=True)

with col_res3:
    # Traffic Light System
    status_html = ""
    if not is_bs_fail:
        status_html = f"""
        <div class="status-box ok">✅ Web Shear: OK ({(V_active/V_web_max)*100:.0f}%)</div>
        <div class="status-box ok">✅ Block Shear: OK</div>
        """
        main_text = "PASSED"
        color = "#27AE60"
    else:
        status_html = f"""
        <div class="status-box ok">✅ Web Shear: OK</div>
        <div class="status-box warning">❌ Block Shear: FAIL ({bs_cap/1000:.1f} T)</div>
        """
        main_text = "CHECK!"
        color = "#C0392B"
        
    st.markdown(f"""
    <div class="card" style="border-top-color: {color};">
        <div class="sub-metric">Safety Inspector</div>
        <div class="main-metric" style="color:{color}">{main_text}</div>
        {status_html}
    </div>
    """, unsafe_allow_html=True)

# --- PART 3: THE CLEAN GRAPH ---
st.markdown("### 2️⃣ กราฟแสดงแนวโน้ม (Efficiency Curve)")
fig = go.Figure()

# Zone Filling
fig.add_trace(go.Scatter(
    x=spans, y=[v/1000 for v in shear_design],
    mode='lines', name='Design Shear',
    line=dict(color='#3498DB', width=3),
    fill='tozeroy', fillcolor='rgba(52, 152, 219, 0.1)'
))

# Max Limit Line (Reference only)
fig.add_trace(go.Scatter(
    x=[spans[0], spans[-1]], y=[V_web_max/1000, V_web_max/1000],
    mode='lines', name='Max Web Capacity',
    line=dict(color='#E74C3C', dash='dash')
))

# User Point
fig.add_trace(go.Scatter(
    x=[sel_span], y=[V_active/1000],
    mode='markers', marker=dict(size=15, color='#E67E22', line=dict(width=2, color='white')),
    name='จุดที่คุณเลือก'
))

fig.update_layout(
    xaxis_title="ความยาวคาน (m)",
    yaxis_title="แรงเฉือนออกแบบ (Ton)",
    height=400,
    margin=dict(t=20, b=20, l=20, r=20),
    hovermode="x unified"
)
st.plotly_chart(fig, use_container_width=True)

# --- PART 4: EXPLANATION ---
if is_bs_fail:
    st.error(f"""
    **⚠️ ตรวจพบปัญหา: Block Shear Failure**
    
    ที่ความยาว {sel_span} เมตร แรงเฉือนยังสูงอยู่ ({V_active/1000:.1f} T) ทำให้ต้องใช้น็อต {req_bolts} ตัว 
    แต่หน้าตัดเหล็กบางเกินไป ({p['tw']} mm) ทำให้เหล็กมีโอกาส **"ฉีกขาดเป็นก้อน"** (Block Shear Cap = {bs_cap/1000:.1f} T) ก่อนที่น็อตจะขาด
    
    **คำแนะนำ:** 1. เพิ่มความหนา Plate เหล็กฉาก
    2. หรือเปลี่ยนขนาดน็อตให้ใหญ่ขึ้น (เพื่อลดจำนวนรูเจาะ)
    """)
