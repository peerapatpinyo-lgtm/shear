import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & STYLE (ตกแต่งหน้าตา)
# ==========================================
st.set_page_config(page_title="Beam Insight V12 (Full Detail)", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    /* กล่องสรุปผลหลัก */
    .summary-box {
        background-color: #e8f8f5;
        padding: 20px;
        border-radius: 10px;
        border-left: 6px solid #1abc9c;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    /* กล่องแสดงที่มาการคำนวณ (Audit) */
    .audit-box {
        background-color: #fdfefe;
        border: 1px solid #d0d3d4;
        border-radius: 8px;
        padding: 15px;
        margin-top: 10px;
        font-family: 'Sarabun', sans-serif;
    }
    .audit-step {
        margin-bottom: 8px;
        padding-bottom: 8px;
        border-bottom: 1px dashed #eee;
        font-size: 15px;
    }
    .big-number {
        font-size: 24px; 
        font-weight: bold; 
        color: #2c3e50;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ฐานข้อมูล (DATABASE)
# ==========================================
steel_db = {
    "H 150x75x5x7":     {"h": 150, "b": 75,  "tw": 5,   "tf": 7,   "Ix": 666,    "Zx": 88.8,  "A": 17.85},
    "H 200x100x5.5x8":  {"h": 200, "b": 100, "tw": 5.5, "tf": 8,   "Ix": 1840,   "Zx": 184,   "A": 26.67},
    "H 250x125x6x9":    {"h": 250, "b": 125, "tw": 6,   "tf": 9,   "Ix": 3690,   "Zx": 295,   "A": 36.97},
    "H 300x150x6.5x9":  {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481,   "A": 46.78},
    "H 350x175x7x11":   {"h": 350, "b": 175, "tw": 7,   "tf": 11,  "Ix": 13600,  "Zx": 775,   "A": 63.14},
    "H 400x200x8x13":   {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190,  "A": 84.12},
    "H 500x200x10x16":  {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910,  "A": 114.2},
}

material_db = {
    "SS400 (เหล็กทั่วไป)":   {"Fy": 2400, "Fu": 4100},
    "SM520 (เหล็กกำลังสูง)": {"Fy": 3600, "Fu": 5300}
}

# ==========================================
# 3. INPUT (Sidebar)
# ==========================================
with st.sidebar:
    st.title("🏗️ Beam Insight V12")
    st.caption("ละเอียด | มีกราฟ | แทนค่าตัวเลขครบ")
    st.divider()
    
    st.header("1. ตั้งค่าคาน (Beam)")
    sec_name = st.selectbox("ขนาดหน้าตัด", list(steel_db.keys()), index=4)
    mat_name = st.selectbox("เกรดเหล็ก", list(material_db.keys()))
    user_span = st.number_input("ความยาวคาน (เมตร)", min_value=2.0, max_value=15.0, value=6.0, step=0.5)
    
    st.header("2. ตั้งค่าน็อต (Bolt)")
    bolt_size = st.selectbox("ขนาดน็อต", ["M16", "M20", "M22", "M24"], index=1)

# ==========================================
# 4. CALCULATION ENGINE
# ==========================================
# 4.1 ดึงค่าตัวแปร
p = steel_db[sec_name]
mat = material_db[mat_name]

# ค่าทางเรขาคณิต (Geometry)
h = p['h'] / 10  # cm
tw = p['tw'] / 10 # cm
Aw = h * tw      # cm2 (คิดพื้นที่รับแรงเฉือนแบบง่าย h*tw)
Zx = p['Zx']     # cm3
Ix = p['Ix']     # cm4

# ค่าวัสดุ (Material)
Fy = mat['Fy']
Fu = mat['Fu']
E = 2.04e6       # ksc

# 4.2 คำนวณขีดจำกัด (Capacity) ของหน้าตัดเหล็ก
V_capacity = 0.4 * Fy * Aw
M_capacity = 0.6 * Fy * Zx
Defl_limit_cm = (user_span * 100) / 360  # L/360

# 4.3 ฟังก์ชันคำนวณ Safe Load (ใช้สำหรับวาดกราฟด้วย)
def calculate_safe_load(span_m):
    L_cm = span_m * 100
    
    # กรณี 1: Shear Control (w = 2V/L) -> หน่วย kg/cm
    w_shear_cm = (2 * V_capacity) / L_cm
    
    # กรณี 2: Moment Control (w = 8M/L^2) -> หน่วย kg/cm
    w_moment_cm = (8 * M_capacity) / (L_cm**2)
    
    # กรณี 3: Deflection Control (w = delta * 384EI / 5L^4) -> หน่วย kg/cm
    delta_lim = L_cm / 360
    w_defl_cm = (delta_lim * 384 * E * Ix) / (5 * (L_cm**4))
    
    # หาค่าน้อยสุด
    w_safe_cm = min(w_shear_cm, w_moment_cm, w_defl_cm)
    
    # ระบุสาเหตุ
    if w_safe_cm == w_shear_cm: cause = "Shear"
    elif w_safe_cm == w_moment_cm: cause = "Moment"
    else: cause = "Deflection"
    
    return {
        "safe_load_kgm": w_safe_cm * 100, # แปลงเป็น kg/m
        "w_shear": w_shear_cm * 100,
        "w_moment": w_moment_cm * 100,
        "w_defl": w_defl_cm * 100,
        "cause": cause
    }

# 4.4 คำนวณที่จุดปัจจุบัน (Current State)
current_res = calculate_safe_load(user_span)
safe_load = current_res["safe_load_kgm"]
cause = current_res["cause"]

# คำนวณแรงภายในที่เกิดขึ้นจริง (Actual Forces) จาก Safe Load
w_use = safe_load / 100 # kg/cm
L_cm = user_span * 100
V_actual = w_use * L_cm / 2
M_actual = w_use * (L_cm**2) / 8
Delta_actual = (5 * w_use * (L_cm**4)) / (384 * E * Ix)

# ==========================================
# 5. DISPLAY (แสดงผล)
# ==========================================
st.title(f"📊 ผลวิเคราะห์: {sec_name} @ {user_span} เมตร")

# --- 5.1 สรุปผลหลัก (Summary Card) ---
st.markdown(f"""
<div class="summary-box">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <h3 style="margin:0; color:#145a32;">น้ำหนักบรรทุกปลอดภัย (Safe Load)</h3>
            <div style="font-size:40px; font-weight:800; color:#1e8449;">
                {safe_load:,.0f} <span style="font-size:20px; color:#555;">kg/m</span>
            </div>
            <div style="color:#7f8c8d;">(รวมน้ำหนักตัวเองแล้ว)</div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:16px; color:#555;">จุดวิกฤตที่ควบคุมการออกแบบ</div>
            <div style="font-size:24px; font-weight:bold; color:#e74c3c; border: 2px solid #e74c3c; padding: 5px 15px; border-radius:5px; display:inline-block; margin-top:5px;">
                {cause}
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# --- 5.2 กราฟเส้น (Capacity Chart) ที่ขอกลับมา ---
# สร้างข้อมูลสำหรับกราฟ
x_range = np.linspace(2, 15, 100) # กราฟช่วง 2-15 เมตร
y_shear = []
y_moment = []
y_defl = []
y_safe = []

for x in x_range:
    res = calculate_safe_load(x)
    y_shear.append(res["w_shear"])
    y_moment.append(res["w_moment"])
    y_defl.append(res["w_defl"])
    y_safe.append(res["safe_load_kgm"])

# วาดกราฟ Plotly
fig = go.Figure()
# เส้น Limit ต่างๆ
fig.add_trace(go.Scatter(x=x_range, y=y_shear, name="ขีดจำกัดแรงเฉือน (Shear)", line=dict(color='#e74c3c', width=2, dash='dot')))
fig.add_trace(go.Scatter(x=x_range, y=y_moment, name="ขีดจำกัดแรงดัด (Moment)", line=dict(color='#f39c12', width=2, dash='dot')))
fig.add_trace(go.Scatter(x=x_range, y=y_defl, name="ขีดจำกัดการแอ่น (Deflection)", line=dict(color='#27ae60', width=2, dash='dot')))
# พื้นที่ปลอดภัย (Filled Area)
fig.add_trace(go.Scatter(x=x_range, y=y_safe, name="พื้นที่ปลอดภัย (Safe Zone)", fill='tozeroy', line=dict(color='#2980b9', width=4)))
# จุดปัจจุบัน
fig.add_trace(go.Scatter(x=[user_span], y=[safe_load], mode='markers+text', name='จุดที่คุณเลือก', 
                         marker=dict(size=15, color='black', symbol='x'),
                         text=[f"{safe_load:,.0f}"], textposition="top right"))

fig.update_layout(
    title="กราฟความสามารถในการรับน้ำหนัก vs ความยาวคาน",
    xaxis_title="ความยาวคาน (เมตร)",
    yaxis_title="น้ำหนักบรรทุกปลอดภัย (kg/m)",
    height=450,
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig, use_container_width=True)

# --- 5.3 รายละเอียดเจาะลึก 3 ด้าน (Detail Columns) ---
c1, c2, c3 = st.columns(3)

# 1. แรงเฉือน
with c1:
    st.info("✂️ 1. แรงเฉือน (Shear)")
    pct_v = V_actual / V_capacity
    st.write(f"**เกิดจริง:** {V_actual:,.0f} kg")
    st.write(f"**รับได้:** {V_capacity:,.0f} kg")
    st.progress(pct_v)
    st.caption(f"ใช้งาน {pct_v*100:.1f}%")

# 2. แรงดัด
with c2:
    st.warning("🪵 2. แรงดัด (Moment)")
    pct_m = (M_actual) / (M_capacity/100) # ปรับหน่วย
    st.write(f"**เกิดจริง:** {M_actual:,.0f} kg.m")
    st.write(f"**รับได้:** {M_capacity/100:,.0f} kg.m")
    st.progress(pct_m)
    st.caption(f"ใช้งาน {pct_m*100:.1f}%")

# 3. การแอ่น
with c3:
    st.success("〰️ 3. การแอ่น (Deflection)")
    pct_d = Delta_actual / Defl_limit_cm
    st.write(f"**เกิดจริง:** {Delta_actual:.2f} cm")
    st.write(f"**ยอมให้:** {Defl_limit_cm:.2f} cm")
    st.progress(pct_d)
    st.caption(f"ใช้งาน {pct_d*100:.1f}%")

st.markdown("---")

# ==========================================
# 6. AUDIT REPORT (โชว์การแทนค่าแบบละเอียด)
# ==========================================
st.subheader("📝 รายการคำนวณแบบละเอียด (Calculation Audit)")
st.write("ส่วนนี้แสดงการ **แทนค่าตัวเลขจริง** ลงในสูตร เพื่อให้ตรวจสอบที่มาของผลลัพธ์ได้")

with st.expander("คลิกเพื่อดูการแทนค่าทีละบรรทัด (Step-by-Step)", expanded=True):
    
    # 6.1 ข้อมูลเบื้องต้น
    st.markdown("#### 1. ค่าคงที่ของหน้าตัดและวัสดุ")
    st.markdown(f"""
    <div class="audit-box">
        <div class="audit-step"><b>หน้าตัด (Section):</b> {sec_name}</div>
        <div class="audit-step">
            $A_w$ (พื้นที่รับแรงเฉือน) = $h \\times t_w$ = {h} × {tw} = <b>{Aw:.2f}</b> cm²
        </div>
        <div class="audit-step">
            $Z_x$ (โมดูลัสหน้าตัด) = <b>{Zx}</b> cm³ &nbsp;|&nbsp; $I_x$ (โมเมนต์ความเฉื่อย) = <b>{Ix}</b> cm⁴
        </div>
        <div class="audit-step">
            <b>วัสดุ (Material):</b> {mat_name} ($F_y$ = {Fy} ksc)
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 6.2 คำนวณความสามารถ (Capacity)
    st.markdown("#### 2. คำนวณขีดจำกัดการรับแรง (Capacity)")
    st.markdown(f"""
    <div class="audit-box">
        <div class="audit-step">
            <b>ก. แรงเฉือนสูงสุดที่รับได้ ($V_{{max}}$):</b><br>
            สูตร: $0.4 \\times F_y \\times A_w$<br>
            แทนค่า: $0.4 \\times {Fy} \\times {Aw:.2f}$<br>
            ผลลัพธ์: <b>{V_capacity:,.0f}</b> kg
        </div>
        <div class="audit-step">
            <b>ข. โมเมนต์สูงสุดที่รับได้ ($M_{{max}}$):</b><br>
            สูตร: $0.6 \\times F_y \\times Z_x$<br>
            แทนค่า: $0.6 \\times {Fy} \\times {Zx}$<br>
            ผลลัพธ์: <b>{M_capacity:,.0f}</b> kg.cm (หรือ {M_capacity/100:,.0f} kg.m)
        </div>
        <div class="audit-step">
            <b>ค. การแอ่นตัวที่ยอมให้ ($\Delta_{{allow}}$):</b><br>
            สูตร: $L / 360$<br>
            แทนค่า: ${user_span*100} / 360$<br>
            ผลลัพธ์: <b>{Defl_limit_cm:.2f}</b> cm
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 6.3 คำนวณ Load
    st.markdown("#### 3. คำนวณน้ำหนักปลอดภัย ($w$) จากขีดจำกัดทั้ง 3")
    w_shear_load = res["w_shear"]
    w_moment_load = res["w_moment"]
    w_defl_load = res["w_defl"]
    
    st.markdown(f"""
    <div class="audit-box">
        <div class="audit-step">
            <b>กรณี A: คิดจากแรงเฉือน ($w = 2V/L$)</b><br>
            แทนค่า: $(2 \\times {V_capacity:,.0f}) \div {user_span*100} $<br>
            = {w_shear_load/100:,.1f} kg/cm $\\rightarrow$ <b>{w_shear_load:,.0f} kg/m</b>
        </div>
        <div class="audit-step">
            <b>กรณี B: คิดจากโมเมนต์ ($w = 8M/L^2$)</b><br>
            แทนค่า: $(8 \\times {M_capacity:,.0f}) \div ({user_span*100})^2 $<br>
            = {w_moment_load/100:,.1f} kg/cm $\\rightarrow$ <b>{w_moment_load:,.0f} kg/m</b>
        </div>
        <div class="audit-step">
            <b>กรณี C: คิดจากการแอ่นตัว ($w = \\Delta \\cdot 384EI / 5L^4$)</b><br>
            แทนค่า: $({Defl_limit_cm:.2f} \\times 384 \\times {2.04e6:,.0f} \\times {Ix}) \div (5 \\times {user_span*100}^4)$<br>
            = {w_defl_load/100:,.1f} kg/cm $\\rightarrow$ <b>{w_defl_load:,.0f} kg/m</b>
        </div>
        <div style="margin-top:10px; padding:10px; background:#eaf2f8; border-radius:5px;">
            <b>สรุป:</b> เลือกค่าที่น้อยที่สุด = <b>{safe_load:,.0f} kg/m</b> (ควบคุมโดย {cause})
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 7. CONNECTION CHECK (จุดต่อ)
# ==========================================
st.markdown("---")
st.subheader(f"🔩 ตรวจสอบจุดต่อ (Connection Audit) : น็อต {bolt_size}")

# คำนวณจุดต่อ
dia = int(bolt_size[1:]) / 10 # cm
bolt_area = 3.14 if bolt_size == "M20" else (2.01 if bolt_size == "M16" else (3.80 if bolt_size == "M22" else 4.52))

# 1. แรงเฉือนน็อต
fv_bolt = 1000 # ksc (สมมติเกรดทั่วไป)
cap_shear = fv_bolt * bolt_area

# 2. แรงแบกทาน
cap_bearing = 1.2 * Fu * dia * tw

# เลือกค่าน้อยสุด
bolt_cap_final = min(cap_shear, cap_bearing)

# จำนวนที่ต้องใช้
req_bolt = math.ceil(V_actual / bolt_cap_final)
if req_bolt < 2: req_bolt = 2

col_bolt1, col_bolt2 = st.columns([1, 1])

with col_bolt1:
    st.markdown(f"""
    <div class="audit-box">
        <b>1. ความสามารถน็อต 1 ตัว (Per Bolt Capacity)</b>
        <ul>
            <li>
                แรงเฉือน (Shear): $F_v \\times A_b$<br>
                = {fv_bolt} × {bolt_area} = <b>{cap_shear:,.0f}</b> kg
            </li>
            <li>
                แรงแบกทาน (Bearing): $1.2 F_u d t_w$<br>
                = 1.2 × {Fu} × {dia} × {tw} = <b>{cap_bearing:,.0f}</b> kg
            </li>
            <li><b>ใช้ค่าต่ำสุด: {bolt_cap_final:,.0f} kg/ตัว</b></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col_bolt2:
    st.markdown(f"""
    <div class="audit-box" style="background-color: #fef9e7; border-color: #f1c40f;">
        <b>2. ตรวจสอบจำนวน (Quantity Check)</b>
        <br><br>
        แรงเฉือนที่เกิดขึ้นจริง ($V_{{act}}$) = <b>{V_actual:,.0f}</b> kg
        <br>
        ความสามารถน็อต ($R_{{bolt}}$) = <b>{bolt_cap_final:,.0f}</b> kg
        <br><hr>
        จำนวนที่ต้องใช้ = {V_actual:,.0f} ÷ {bolt_cap_final:,.0f} = {V_actual/bolt_cap_final:.2f}
        <br>
        <h1>👉 ต้องใช้ {req_bolt} ตัว</h1>
    </div>
    """, unsafe_allow_html=True)
