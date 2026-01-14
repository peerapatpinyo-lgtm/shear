import streamlit as st
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & STYLE (แต่งสวย)
# ==========================================
st.set_page_config(page_title="Beam Insight V13", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9f9;
        border: 1px solid #e5e8e8;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .big-percent {
        font-size: 32px;
        font-weight: bold;
        color: #2c3e50;
    }
    .math-row {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #3498db;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA & INPUT
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
    "SS400":   {"Fy": 2400, "Fu": 4100},
    "SM520":   {"Fy": 3600, "Fu": 5300}
}

with st.sidebar:
    st.header("⚙️ ตั้งค่าโครงสร้าง")
    sec_name = st.selectbox("ขนาดหน้าตัด", list(steel_db.keys()), index=4)
    mat_name = st.selectbox("เกรดเหล็ก", list(material_db.keys()))
    user_span = st.number_input("ความยาวคาน (m)", 2.0, 15.0, 6.0, 0.5)
    bolt_size = st.selectbox("ขนาดน็อต", ["M16", "M20", "M22", "M24"], index=1)

# ==========================================
# 3. CALCULATION
# ==========================================
p = steel_db[sec_name]
mat = material_db[mat_name]
h, tw = p['h']/10, p['tw']/10
Aw = h * tw
Zx, Ix = p['Zx'], p['Ix']
Fy, Fu = mat['Fy'], mat['Fu']
E = 2.04e6

# Capacity
V_cap = 0.4 * Fy * Aw
M_cap = 0.6 * Fy * Zx
Defl_allow = (user_span * 100) / 360

# Safe Load Logic
L_cm = user_span * 100
w_shear = (2 * V_cap) / L_cm * 100
w_moment = (8 * M_cap) / (L_cm**2) * 100
w_defl = (Defl_allow * 384 * E * Ix) / (5 * (L_cm**4)) * 100
safe_load = min(w_shear, w_moment, w_defl)

# Actual Force (ใช้ Safe Load คำนวณกลับ)
w_act = safe_load / 100 # kg/cm
V_act = w_act * L_cm / 2
M_act = w_act * (L_cm**2) / 8 # kg.cm
Defl_act = (5 * w_act * (L_cm**4)) / (384 * E * Ix)

# Percentages (เอาไว้โชว์ 75% ที่คุณต้องการ)
pct_v = (V_act / V_cap) * 100
pct_m = (M_act / M_cap) * 100
pct_d = (Defl_act / Defl_allow) * 100

# ==========================================
# 4. MAIN DISPLAY
# ==========================================
st.title(f"📊 ผลวิเคราะห์: {sec_name} @ {user_span}m")

# --- 4.1 The "Percentage Cards" (เอาแบบเก่ากลับมาตามขอ) ---
c1, c2, c3 = st.columns(3)

def show_card(col, title, act, limit, unit, pct, color):
    with col:
        st.markdown(f"""
        <div class="metric-card" style="border-top: 5px solid {color};">
            <h4 style="margin:0;">{title}</h4>
            <div class="big-percent" style="color:{color};">{pct:.1f}%</div>
            <p style="font-size:14px; color:#555;">
                ใช้จริง: <b>{act:,.0f}</b> {unit}<br>
                รับได้: {limit:,.0f} {unit}
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.progress(min(pct/100, 1.0))

show_card(c1, "✂️ แรงเฉือน (Shear)", V_act, V_cap, "kg", pct_v, "#e74c3c")
show_card(c2, "🪵 แรงดัด (Moment)", M_act/100, M_cap/100, "kg.m", pct_m, "#f39c12") # หาร 100 เป็น kg.m
show_card(c3, "〰️ การแอ่น (Deflection)", Defl_act, Defl_allow, "cm", pct_d, "#27ae60")

st.markdown(f"""
<div style="text-align:center; margin-top:20px; padding:15px; background:#eafaf1; border-radius:10px;">
    <h3>🚀 น้ำหนักบรรทุกปลอดภัยสูงสุด: <span style="color:#27ae60; font-size:36px;">{safe_load:,.0f}</span> kg/m</h3>
</div>
""", unsafe_allow_html=True)

# --- 4.2 Graph (กราฟเอาไว้เหมือนเดิม) ---
st.markdown("---")
x_range = np.linspace(2, 15, 100)
y_s, y_m, y_d, y_safe = [], [], [], []
for x in x_range:
    Lx = x * 100
    ws = (2 * V_cap) / Lx * 100
    wm = (8 * M_cap) / (Lx**2) * 100
    wd = ((Lx/360) * 384 * E * Ix) / (5 * (Lx**4)) * 100
    y_s.append(ws); y_m.append(wm); y_d.append(wd); y_safe.append(min(ws,wm,wd))

fig = go.Figure()
fig.add_trace(go.Scatter(x=x_range, y=y_s, name="Shear Limit", line=dict(dash='dot', color='#e74c3c')))
fig.add_trace(go.Scatter(x=x_range, y=y_m, name="Moment Limit", line=dict(dash='dot', color='#f39c12')))
fig.add_trace(go.Scatter(x=x_range, y=y_d, name="Deflection Limit", line=dict(dash='dot', color='#27ae60')))
fig.add_trace(go.Scatter(x=x_range, y=y_safe, name="Safe Zone", fill='tozeroy', line=dict(color='#2980b9')))
fig.add_trace(go.Scatter(x=[user_span], y=[safe_load], mode='markers', marker=dict(size=15, color='black'), name="Current"))
fig.update_layout(height=400, margin=dict(t=30,b=0), title="Capacity Chart", xaxis_title="Length (m)", yaxis_title="Load (kg/m)")
st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 5. AUDIT (แก้การแสดงผลตัวเลขให้สวยตามสั่ง)
# ==========================================
st.markdown("---")
st.subheader("📝 ตรวจสอบการคำนวณ (Calculation Audit)")

with st.expander("ดูวิธีการแทนค่า (Step-by-Step)", expanded=True):
    
    st.write("##### 1. คุณสมบัติหน้าตัด (Section Properties)")
    # ใช้ LaTeX จัดเรียงสวยๆ
    st.latex(r"""
    \begin{aligned}
    A_w &= h \times t_w \\
        &= """ + f"{h:.1f} \\times {tw:.1f} \\\\" + r"""
        &= \mathbf{""" + f"{Aw:.2f}" + r"""} \text{ cm}^2
    \end{aligned}
    """)
    st.caption("👆 นี่ครับ แปลงเป็นสมการคณิตศาสตร์ให้ดูง่ายขึ้นแล้วครับ")
    
    st.write("##### 2. ขีดจำกัดการรับแรง (Allowable Limits)")
    c_a, c_b = st.columns(2)
    with c_a:
        st.info("**Allowable Shear ($V_a$)**")
        st.latex(r"""
        \begin{aligned}
        V_a &= 0.4 \times F_y \times A_w \\
            &= 0.4 \times """ + f"{Fy} \\times {Aw:.2f} \\\\" + r"""
            &= \mathbf{""" + f"{V_cap:,.0f}" + r"""} \text{ kg}
        \end{aligned}
        """)
    with c_b:
        st.info("**Allowable Moment ($M_a$)**")
        st.latex(r"""
        \begin{aligned}
        M_a &= 0.6 \times F_y \times Z_x \\
            &= 0.6 \times """ + f"{Fy} \\times {Zx} \\\\" + r"""
            &= \mathbf{""" + f"{M_cap:,.0f}" + r"""} \text{ kg.cm}
        \end{aligned}
        """)

    st.write("##### 3. ตรวจสอบจุดต่อ (Connection Check)")
    dia = int(bolt_size[1:])/10
    # คำนวณ Bolt แบบเดิม
    bolt_shear_cap = 1000 * (3.1416 * (dia/2)**2) # Shear Area
    bolt_bear_cap = 1.2 * Fu * dia * tw
    one_bolt_cap = min(bolt_shear_cap, bolt_bear_cap)
    req_n = math.ceil(V_act / one_bolt_cap)
    if req_n < 2: req_n = 2
    
    st.latex(r"""
    \text{Bolt Capacity } (\phi P_n) = \min(\text{Shear}, \text{Bearing}) = \mathbf{""" + f"{one_bolt_cap:,.0f}" + r"""} \text{ kg/bolt}
    """)
    st.latex(r"""
    \text{Required Bolts} = \frac{V_{act}}{P_{bolt}} = \frac{""" + f"{V_act:,.0f}" + r"""}{""" + f"{one_bolt_cap:,.0f}" + r"""} = """ + f"{V_act/one_bolt_cap:.2f}" + r""" \rightarrow \mathbf{""" + f"{req_n}" + r"""} \text{ pcs}
    """)
