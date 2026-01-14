import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. ตั้งค่าหน้าเว็บ (STYLE)
# ==========================================
st.set_page_config(page_title="Beam Insight V10 (Human Friendly)", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    /* สไตล์การ์ดแสดงผล */
    .highlight-card { background-color: #e8f6f3; padding: 20px; border-radius: 15px; border: 1px solid #1abc9c; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    
    /* กล่อง 3 ช่องด้านล่าง */
    .metric-box { 
        text-align: center; 
        padding: 20px; 
        background: white; 
        border-radius: 12px; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); 
        border-top: 5px solid #bdc3c7;
        margin-bottom: 10px;
    }
    
    /* ตัวเลขและตัวหนังสือ */
    .big-num { font-size: 28px; font-weight: 800; color: #2c3e50; }
    .sub-text { font-size: 14px; color: #7f8c8d; margin-bottom: 8px; }
    
    /* แถบ Progress Bar พื้นหลัง */
    .progress-bg { background-color: #f0f3f4; height: 10px; width: 100%; border-radius: 5px; margin-top: 10px; overflow: hidden; }
    
    /* ส่วนแสดงที่มา (Audit) */
    .audit-box { background-color: #fdfefe; padding: 15px; border: 1px solid #d5dbdb; border-radius: 8px; font-family: 'Sarabun', sans-serif; margin-top: 10px; font-size: 14px; }
    .formula-row { display: flex; justify-content: space-between; margin-bottom: 8px; border-bottom: 1px dashed #eee; padding-bottom: 4px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ฐานข้อมูล (DATABASE)
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
# 3. เมนูตั้งค่า (SIDEBAR)
# ==========================================
with st.sidebar:
    st.title("Beam Insight V10")
    st.caption("ใช้ง่าย + มีที่มาที่ไป")
    st.divider()
    
    st.header("1. ตั้งค่าคาน (Beam)")
    sec_name = st.selectbox("เลือกขนาดหน้าตัด", list(steel_db.keys()), index=4)
    mat_name = st.selectbox("เกรดเหล็ก", list(material_db.keys()))
    user_span = st.number_input("ความยาวช่วงคาน (เมตร)", min_value=1.0, value=6.0, step=0.5)
    
    st.divider()
    st.header("2. ตั้งค่าน็อต (Connection)")
    bolt_size = st.selectbox("ขนาดน็อต", ["M16", "M20", "M22", "M24"], index=1)
    
    # ดึงค่า
    p = steel_db[sec_name]
    mat = material_db[mat_name]
    fy, fu = mat["Fy"], mat["Fu"]
    E_mod = 2.04e6
    defl_lim_val = 360 # L/360

# ==========================================
# 4. ส่วนคำนวณ (CALCULATION)
# ==========================================
# 4.1 แปลงหน่วยและหา Properties
h_cm, tw_cm = p['h']/10, p['tw']/10
Aw = h_cm * tw_cm      # พื้นที่รับแรงเฉือน
Zx = p['Zx']           # โมดูลัสหน้าตัด
Ix = p['Ix']           # โมเมนต์ความเฉื่อย

# 4.2 ขีดจำกัดการรับแรง (Capacity)
V_cap = 0.4 * fy * Aw  # รับแรงเฉือนได้สูงสุด (kg)
M_cap = 0.6 * fy * Zx  # รับโมเมนต์ได้สูงสุด (kg.cm)

# 4.3 หา "น้ำหนักปลอดภัยสูงสุด" (Max Safe Load)
L_cm = user_span * 100
delta_allow = L_cm / defl_lim_val

# คำนวณ Load (w) ย้อนกลับจากทั้ง 3 กรณี
w_shear = (2 * V_cap) / L_cm * 100          # จากสูตร V = wL/2
w_moment = (8 * M_cap) / (L_cm**2) * 100    # จากสูตร M = wL^2/8
w_defl = (delta_allow * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100 # จากสูตร Deflection

# เลือกค่าน้อยที่สุดเป็นตัวคุม (Governing)
user_safe_load = min(w_shear, w_moment, w_defl)

# หาว่าตัวไหนเป็นตัวคุม
if user_safe_load == w_shear: cause = "Shear (แรงเฉือน)"
elif user_safe_load == w_moment: cause = "Moment (แรงดัด)"
else: cause = "Deflection (การแอ่นตัว)"

# 4.4 คำนวณค่าจริงที่เกิดขึ้น (Actual Forces) เพื่อโชว์ในกล่อง
V_actual = user_safe_load * user_span / 2
M_actual = user_safe_load * user_span**2 / 8
# Deflection จริง (ต้องแปลง w เป็น kg/cm ก่อนคำนวณ)
delta_actual = (5 * (user_safe_load/100) * (L_cm**4)) / (384 * E_mod * Ix)

# ==========================================
# 5. แสดงผล (DISPLAY)
# ==========================================
tab1, tab2 = st.tabs(["📊 วิเคราะห์คาน (Beam)", "🔩 จุดต่อ (Connection)"])

with tab1:
    st.subheader(f"ผลวิเคราะห์: {sec_name} ยาว {user_span} เมตร")
    
    # --- การ์ดสรุปผลหลัก ---
    color_map = {"Shear": "#e74c3c", "Moment": "#f39c12", "Deflection": "#27ae60"}
    cause_key = cause.split(" ")[0] # เอาแค่คำแรกไปเทียบสี
    
    st.markdown(f"""
    <div class="highlight-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span class="sub-text">น้ำหนักแผ่ปลอดภัยสูงสุด (Safe Load)</span><br>
                <span class="big-num" style="font-size: 36px;">{user_safe_load:,.0f}</span> <span style="font-size:20px; color:#555;">kg/m</span>
            </div>
            <div style="text-align: right;">
                <span class="sub-text">ถูกควบคุมโดย</span><br>
                <span style="font-size: 20px; font-weight:bold; color:{color_map.get(cause_key, 'black')};">{cause}</span>
            </div>
        </div>
    </div>
    <br>
    """, unsafe_allow_html=True)

    # --- กล่อง 3 ช่อง (มี Bar Graph กลับมาแล้ว!) ---
    c1, c2, c3 = st.columns(3)
    
    # คำนวณ %
    pct_v = (V_actual / V_cap) * 100
    pct_m = ((M_actual*100) / M_cap) * 100
    pct_d = (delta_actual / delta_allow) * 100
    
    def metric_html(title, val, unit, cap, pct, color):
        # ฟังก์ชันสร้าง HTML กล่องพร้อม Bar Graph
        bar_width = min(pct, 100)
        return f"""
        <div class="metric-box" style="border-top-color: {color};">
            <div class="sub-text">{title}</div>
            <div class="big-num">{val:,.0f} <span style="font-size:16px;">{unit}</span></div>
            <div style="font-size:12px; color:#999; margin-top:5px;">Max: {cap:,.0f} {unit}</div>
            
            <div class="progress-bg">
                <div style="background:{color}; width:{bar_width}%; height:100%;"></div>
            </div>
            <div style="text-align:right; font-size:12px; font-weight:bold; color:{color}; margin-top:3px;">{pct:.0f}%</div>
        </div>
        """

    with c1: st.markdown(metric_html("แรงเฉือน (Shear)", V_actual, "kg", V_cap, pct_v, "#e74c3c"), unsafe_allow_html=True)
    with c2: st.markdown(metric_html("โมเมนต์ (Moment)", M_actual, "kg.m", M_cap/100, pct_m, "#f39c12"), unsafe_allow_html=True)
    with c3: st.markdown(metric_html("การแอ่น (Deflection)", delta_actual, "cm", delta_allow, pct_d, "#27ae60").replace(",.0f cm", ".2f cm").replace(f"{delta_allow:,.0f}", f"{delta_allow:.2f}"), unsafe_allow_html=True)

    # --- ส่วนเจาะลึกที่มา (Audit Section) ---
    st.markdown("---")
    with st.expander("🕵️‍♂️ ดูที่มาของตัวเลข (กดเพื่อขยาย)", expanded=True):
        st.markdown(f"""
        <div class="audit-box">
            <b>1. พื้นฐาน (Basic Info)</b>
            <div class="formula-row"><span>หน้าตัด ({sec_name})</span> <span>Aw={Aw:.2f} cm², Zx={Zx} cm³, Ix={Ix} cm⁴</span></div>
            <div class="formula-row"><span>วัสดุ ({mat_name})</span> <span>Fy={fy}, Fu={fu}, E=2.04x10⁶ ksc</span></div>
            <br>
            
            <b>2. ที่มาของเลขในกล่อง (คำนวณย้อนกลับจาก Load {user_safe_load:,.0f} kg/m)</b>
            <div class="formula-row">
                <span><b>กล่อง 1: แรงเฉือน (V)</b> <br><small>สูตร: Load × ยาว ÷ 2</small></span>
                <span>{user_safe_load:,.0f} × {user_span} ÷ 2 = <b>{V_actual:,.0f}</b> kg</span>
            </div>
            <div class="formula-row">
                <span><b>กล่อง 2: โมเมนต์ (M)</b> <br><small>สูตร: Load × ยาว² ÷ 8</small></span>
                <span>{user_safe_load:,.0f} × {user_span}² ÷ 8 = <b>{M_actual:,.0f}</b> kg.m</span>
            </div>
            <div class="formula-row">
                <span><b>กล่อง 3: การแอ่นตัว (Δ)</b> <br><small>สูตร: 5wL⁴ / 384EI</small></span>
                <span>คำนวณละเอียดได้ = <b>{delta_actual:.2f}</b> cm</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.subheader(f"ออกแบบจุดต่อด้วยน็อต {bolt_size}")
    
    # คำนวณน็อต
    dia = int(bolt_size[1:])/10 # cm
    # รับแรงเฉือน (สมมติเกรด 8.8)
    fv_bolt = 1000 # ksc
    bolt_area = 3.14 if bolt_size=="M20" else (2.01 if bolt_size=="M16" else 3.8)
    cap_shear = fv_bolt * bolt_area
    
    # รับแรงแบกทาน (Bearing)
    cap_bear = 1.2 * fu * dia * tw_cm
    
    bolt_cap = min(cap_shear, cap_bear)
    req_bolt = math.ceil(V_actual / bolt_cap)
    if req_bolt < 2: req_bolt = 2
    if req_bolt % 2 != 0: req_bolt += 1
    
    c_info, c_draw = st.columns([1,1])
    
    with c_info:
        st.info(f"""
        **แรงเฉือนที่เกิดขึ้น:** {V_actual:,.0f} kg
        
        **ความสามารถน็อต 1 ตัว:**
        - ตัดขาด (Shear): {cap_shear:,.0f} kg
        - รูฉีก (Bearing): {cap_bear:,.0f} kg
        - **ใช้ค่าต่ำสุด:** {bolt_cap:,.0f} kg/ตัว
        
        **สรุปจำนวน:**
        {V_actual:,.0f} ÷ {bolt_cap:,.0f} = {V_actual/bolt_cap:.2f} 
        👉 **ต้องใช้ {req_bolt} ตัว**
        """)
        
    with c_draw:
        # วาดรูปง่ายๆ
        fig = go.Figure()
        # ขอบคาน
        fig.add_shape(type="rect", x0=0, y0=0, x1=100, y1=p['h'], line=dict(color="blue"))
        # น็อต
        rows = req_bolt // 2
        spacing = 3 * (dia*10)
        start_y = (p['h'] - (rows-1)*spacing)/2
        
        x_pos = [30, 70] * rows
        y_pos = []
        for r in range(rows):
            y = start_y + r*spacing
            y_pos.extend([y, y])
            
        fig.add_trace(go.Scatter(x=x_pos, y=y_pos, mode='markers', marker=dict(size=15, color='red'), name='Bolt'))
        fig.update_layout(title="ภาพจำลองการจัดเรียงน็อต", xaxis=dict(visible=False), yaxis=dict(visible=False, range=[0, p['h']]), height=300)
        st.plotly_chart(fig, use_container_width=True)
