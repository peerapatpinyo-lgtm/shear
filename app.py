import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & STYLE
# ==========================================
st.set_page_config(page_title="Beam Insight Pro", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .highlight-card { background-color: #e8f6f3; padding: 20px; border-radius: 10px; border: 1px solid #1abc9c; }
    .theory-card { background-color: #fdfefe; padding: 20px; border-radius: 10px; border-left: 5px solid #2e86c1; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .metric-box { text-align: center; padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-top: 3px solid #3498db; }
    .big-num { font-size: 24px; font-weight: bold; color: #17202a; }
    .sub-text { font-size: 13px; color: #7f8c8d; margin-top: 5px;}
    h3 { color: #2c3e50; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE & FUNCTIONS
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

def draw_section_profile(name, props):
    h, b, tw, tf = props['h'], props['b'], props['tw'], props['tf']
    
    fig = go.Figure()
    # Draw I-Shape
    x = [-b/2, b/2, b/2, tw/2, tw/2, b/2, b/2, -b/2, -b/2, -tw/2, -tw/2, -b/2, -b/2]
    y = [h/2, h/2, h/2-tf, h/2-tf, -h/2+tf, -h/2+tf, -h/2, -h/2, -h/2+tf, -h/2+tf, h/2-tf, h/2-tf, h/2]
    
    fig.add_trace(go.Scatter(x=x, y=y, fill="toself", line=dict(color="#2c3e50"), name="Section"))
    
    fig.update_layout(
        title=f"Cross Section: {name}",
        xaxis=dict(visible=False, scaleanchor="y"),
        yaxis=dict(visible=False),
        margin=dict(l=10, r=10, t=30, b=10),
        height=200,
        plot_bgcolor='white'
    )
    return fig

# ==========================================
# 3. SIDEBAR
# ==========================================
with st.sidebar:
    st.title("🎛️ Parameters")
    
    # Section Input
    sec_name = st.selectbox("Section Size", list(steel_db.keys()), index=5)
    p = steel_db[sec_name]
    
    # Section Visualizer (New!)
    st.plotly_chart(draw_section_profile(sec_name, p), use_container_width=True)
    
    st.caption(f"Weight: {p['w']} kg/m | Ix: {p['Ix']:,} cm⁴")
    
    st.divider()
    
    # Design Input
    bolt_size = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)
    defl_ratio_str = st.selectbox("Deflection Limit", ["L/300", "L/360", "L/400"], index=1)
    defl_lim_val = int(defl_ratio_str.split("/")[1])
    fy = 2400 # ksc

# ==========================================
# 4. CALCULATION
# ==========================================
# Unit Conversions & Props
h_cm, tw_cm = p['h']/10, p['tw']/10
Aw = h_cm * tw_cm
Ix, Zx = p['Ix'], p['Zx']

# 1. Capacities
M_allow = 0.6 * fy * Zx # kg.cm
V_allow_web = 0.4 * fy * Aw # kg

# 2. Bolt Capacity
dia_cm = int(bolt_size[1:])/10
b_areas = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}
v_shear = 1000 * b_areas[bolt_size]
v_bear = 1.2 * 4000 * dia_cm * tw_cm # SS400 Fu=4000
v_bolt = min(v_shear, v_bear)

# 3. Curve Generation
spans = np.linspace(2, 16, 100) # m
w_s, w_m, w_d, w_gov, limit_cause = [], [], [], [], []

E_mod = 2.04e6
for L in spans:
    L_cm = L * 100
    # Safe Loads (kg/m)
    ws = (2 * V_allow_web) / L_cm * 100
    wm = (8 * M_allow) / (L_cm**2) * 100
    wd = ((L_cm / defl_lim_val) * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100
    
    min_val = min(ws, wm, wd)
    w_gov.append(min_val)
    
    if min_val == ws: limit_cause.append("Shear")
    elif min_val == wm: limit_cause.append("Moment")
    else: limit_cause.append("Deflection")
    
    w_s.append(ws); w_m.append(wm); w_d.append(wd)

# Optimal Range (15d - 20d)
opt_min = 15 * (p['h']/1000)
opt_max = 20 * (p['h']/1000)

# ==========================================
# 5. MAIN UI
# ==========================================
st.title("🏗️ Beam Insight & Safe Load Dashboard")

tab1, tab2 = st.tabs(["📊 Dashboard & Analysis", "📚 Engineering Logic (Theory)"])

# --- TAB 1: DASHBOARD ---
with tab1:
    # 1. Optimal Card
    col_res1, col_res2 = st.columns([1, 2])
    with col_res1:
        st.markdown(f"""
        <div class="highlight-card">
            <h3 style="margin:0; color:#16a085;">✅ Optimal Span</h3>
            <div class="big-num">{opt_min:.1f} - {opt_max:.1f} m</div>
            <div class="sub-text">ช่วงความยาวที่ "คุ้มค่า" ที่สุด<br>(L/d Ratio = 15-20)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_res2:
        check_L = st.slider("🔍 Slide to Check Span (m)", 2.0, 16.0, (opt_min+opt_max)/2, 0.5)
        # Find values
        idx = (np.abs(spans - check_L)).argmin()
        gov_load = w_gov[idx]
        reaction = gov_load * check_L / 2
        req_bolts = math.ceil(reaction / v_bolt)
        cause = limit_cause[idx]
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='metric-box'><div class='sub-text'>Safe Uniform Load</div><div class='big-num' style='color:#2980b9'>{gov_load:,.0f}</div><div class='sub-text'>kg/m ({cause} Gov.)</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-box'><div class='sub-text'>End Reaction (V)</div><div class='big-num' style='color:#d35400'>{reaction:,.0f}</div><div class='sub-text'>kg</div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-box'><div class='sub-text'>Bolts ({bolt_size})</div><div class='big-num' style='color:#27ae60'>{req_bolts}</div><div class='sub-text'>Based on V</div></div>", unsafe_allow_html=True)

    # 2. The Chart
    st.subheader("📈 Safe Load Capacity Chart")
    fig = go.Figure()
    
    # Limits
    fig.add_trace(go.Scatter(x=spans, y=w_m, name="Moment Limit", line=dict(color='orange', dash='dot')))
    fig.add_trace(go.Scatter(x=spans, y=w_s, name="Shear Limit", line=dict(color='red', dash='dot')))
    fig.add_trace(go.Scatter(x=spans, y=w_d, name="Deflection Limit", line=dict(color='green', dash='dot')))
    
    # Safe Zone
    fig.add_trace(go.Scatter(x=spans, y=w_gov, name="Safe Load (Design)", fill='tozeroy', line=dict(color='#2980b9', width=4)))
    
    # Optimal Zone Highlight
    fig.add_vrect(x0=opt_min, x1=opt_max, fillcolor="green", opacity=0.1, annotation_text="Optimal Zone", annotation_position="top")
    
    # User Selection Point
    fig.add_trace(go.Scatter(x=[check_L], y=[gov_load], mode='markers', marker=dict(size=12, color='black'), name='Selected Span'))

    fig.update_layout(xaxis_title="Span (m)", yaxis_title="Safe Load (kg/m)", height=450, hovermode="x unified", yaxis=dict(range=[0, max(w_gov)*1.3]))
    st.plotly_chart(fig, use_container_width=True)

    # 3. Connection Matrix
    with st.expander("📋 View Connection Matrix Table", expanded=True):
        std_spans = [4, 5, 6, 8, 10, 12]
        data = []
        for s in std_spans:
            if s > 15: continue
            i = (np.abs(spans - s)).argmin()
            l = w_gov[i]
            r = l * s / 2
            nb = math.ceil(r / v_bolt)
            rem = "✅ Optimal" if opt_min <= s <= opt_max else ("⚠️ Short" if s < opt_min else "⚠️ Long")
            data.append({"Span (m)": s, "Safe Load (kg/m)": f"{l:,.0f}", "Reaction (kg)": f"{r:,.0f}", "Bolts Req": nb, "Note": rem})
        st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True)

# --- TAB 2: THEORY ---
with tab2:
    st.header("📚 Engineering Methodology (ที่มาของการคำนวณ)")
    st.markdown("เราใช้วิธี **Allowable Stress Design (ASD)** ตามมาตรฐานวิศวกรรมสากล โดยพิจารณา 3 ปัจจัยหลักที่จำกัดความสามารถของคาน:")
    
    # 1. Moment Logic
    st.markdown("""
    <div class="theory-card">
    <h3>1. การรับโมเมนต์ดัด (Bending Moment Capacity)</h3>
    <p>เมื่อคานยาวขึ้น โมเมนต์ดัดจะเป็นตัวควบคุมหลัก สูตรหาน้ำหนักบรรทุกปลอดภัยจากโมเมนต์คือ:</p>
    """, unsafe_allow_html=True)
    st.latex(r"w_{allow} = \frac{8 \cdot M_{allow}}{L^2}")
    st.markdown(f"""
    *โดยที่:*
    * $M_{{allow}} = 0.60 \cdot F_y \cdot Z_x$ (โมเมนต์ต้านทานที่ยอมให้)
    * สำหรับ {sec_name}: $M_{{allow}} = 0.6 \\times {fy} \\times {p['Zx']:,} = {M_allow:,.0f}$ kg.cm
    * *กราฟจะเป็นเส้นโค้งพาราโบลาสีส้ม (ยิ่งยาว ยิ่งรับน้ำหนักได้น้อยลงอย่างรวดเร็ว)*
    </div>
    """, unsafe_allow_html=True)

    # 2. Shear Logic
    st.markdown("""
    <div class="theory-card">
    <h3>2. การรับแรงเฉือน (Shear Capacity)</h3>
    <p>สำหรับคานช่วงสั้น (Short Span) แรงเฉือนมักจะเป็นตัวกำหนด (เหล็กขาดก่อนคานงอ) คำนวณจากพื้นที่หน้าตัดเอวคาน (Web):</p>
    """, unsafe_allow_html=True)
    st.latex(r"w_{allow} = \frac{2 \cdot V_{allow}}{L}")
    st.markdown(f"""
    *โดยที่:*
    * $V_{{allow}} = 0.40 \cdot F_y \cdot A_w$ (แรงเฉือนที่ยอมให้)
    * $A_w = h \cdot t_w$ (พื้นที่หน้าตัดเอวคาน)
    * สำหรับ {sec_name}: $V_{{allow}} = {V_allow_web:,.0f}$ kg
    * *กราฟจะเป็นเส้นชันสีแดงในช่วงต้น (คานสั้น)*
    </div>
    """, unsafe_allow_html=True)

    # 3. Deflection Logic
    st.markdown("""
    <div class="theory-card">
    <h3>3. การแอ่นตัว (Deflection Limit)</h3>
    <p>สำหรับคานยาวมากๆ แม้คานจะไม่พัง แต่การแอ่นตัวอาจเกินพิกัดที่ใช้งานได้ (Serviceability Limit State):</p>
    """, unsafe_allow_html=True)
    st.latex(r"w_{allow} = \frac{\Delta_{allow} \cdot 384 \cdot E \cdot I_x}{5 \cdot L^4}")
    st.markdown(f"""
    *โดยที่:*
    * $\Delta_{{allow}} = L / {defl_lim_val}$ (พิกัดการแอ่นตัวที่กำหนด)
    * $E = 2.04 \\times 10^6$ ksc (Modulus of Elasticity)
    * $I_x = {p['Ix']:,}$ cm⁴ (Moment of Inertia)
    * *กราฟสีเขียวจะตกลงอย่างรวดเร็วเมื่อคานยาวขึ้นมากๆ*
    </div>
    """, unsafe_allow_html=True)

    # 4. Connection Logic
    st.markdown("""
    <div class="theory-card">
    <h3>4. การออกแบบจุดต่อ (Connection Design)</h3>
    <p>จำนวน Bolt คำนวณจากแรงปฏิกิริยาที่ปลายคาน ($R = wL/2$) หารด้วยกำลังรับแรงต่ำสุดของ Bolt:</p>
    """, unsafe_allow_html=True)
    
    st.latex(r"N_{bolts} = \frac{V_{reaction}}{\min(\phi_{shear}, \phi_{bearing})}")
    st.markdown(f"""
    *การตรวจสอบ:*
    1. **Bolt Shear:** แรงเฉือนขาดของน็อต ({bolt_size} $\\approx {v_shear:,.0f}$ kg)
    2. **Plate Bearing:** แรงแบกทานของเอวคาน ({p['tw']} mm $\\approx {v_bear:,.0f}$ kg)
    * *ตัวที่ควบคุมการออกแบบคือ:* **{("Shear" if v_shear < v_bear else "Bearing")}**
    </div>
    """, unsafe_allow_html=True)
