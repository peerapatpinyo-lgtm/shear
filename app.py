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
    .metric-box { text-align: center; padding: 10px; background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .big-num { font-size: 28px; font-weight: bold; color: #17202a; }
    .sub-text { font-size: 14px; color: #7f8c8d; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE
# ==========================================
steel_db = {
    "H 150x75x5x7":     {"h": 150, "b": 75,  "tw": 5,   "tf": 7,   "Ix": 666,    "Zx": 88.8,  "w": 14.0},
    "H 200x100x5.5x8": {"h": 200, "b": 100, "tw": 5.5, "tf": 8,   "Ix": 1840,   "Zx": 184,   "w": 21.3},
    "H 250x125x6x9":    {"h": 250, "b": 125, "tw": 6,   "tf": 9,   "Ix": 3690,   "Zx": 295,   "w": 29.6},
    "H 300x150x6.5x9": {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481,   "w": 36.7},
    "H 350x175x7x11":  {"h": 350, "b": 175, "tw": 7,   "tf": 11,  "Ix": 13600,  "Zx": 775,   "w": 49.6},
    "H 400x200x8x13":  {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190,  "w": 66.0},
    "H 450x200x9x14":  {"h": 450, "b": 200, "tw": 9,   "tf": 14,  "Ix": 33500,  "Zx": 1490,  "w": 76.0},
    "H 500x200x10x16": {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910,  "w": 89.6},
    "H 600x200x11x17": {"h": 600, "b": 200, "tw": 11,  "tf": 17,  "Ix": 77600,  "Zx": 2590,  "w": 106},
}

# ==========================================
# 3. SIDEBAR INPUTS
# ==========================================
with st.sidebar:
    st.header("⚙️ Parameter Setup")
    sec_name = st.selectbox("Select Section", list(steel_db.keys()), index=5)
    bolt_size = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)
    
    st.divider()
    fy = st.number_input("Fy (ksc)", 2400)
    E_mod = 2.04e6 # ksc
    defl_ratio = st.selectbox("Deflection Limit", ["L/300", "L/360", "L/400"], index=1)
    defl_lim_val = int(defl_ratio.split("/")[1])

# ==========================================
# 4. CALCULATION ENGINE
# ==========================================
p = steel_db[sec_name]

# 4.1 Properties
h_cm = p['h']/10
tw_cm = p['tw']/10
Aw = h_cm * tw_cm
Ix = p['Ix']
Zx = p['Zx']

# 4.2 Capacities
# Moment Cap (Allowable)
M_allow = 0.6 * fy * Zx # kg.cm
# Shear Cap (Web Yield)
V_allow_web = 0.4 * fy * Aw # kg

# Bolt Cap
dia_cm = int(bolt_size[1:])/10
b_area = 3.14 if bolt_size=="M20" else (2.01 if bolt_size=="M16" else 3.8)
v_bolt_shear = 1000 * b_area
v_bolt_bear = 1.2 * 4000 * dia_cm * tw_cm
v_bolt = min(v_bolt_shear, v_bolt_bear)

# 4.3 Generate Load Curve
# Loop spans from 2m to 15m
spans = np.linspace(2, 15, 100) # meters
w_shear = []
w_moment = []
w_defl = []
w_govern = []
govern_cause = []

for L in spans:
    L_cm = L * 100
    
    # 1. Load limit by Shear: V = wL/2 => w = 2V/L
    ws = (2 * V_allow_web) / L_cm * 100 # kg/m
    
    # 2. Load limit by Moment: M = wL^2/8 => w = 8M/L^2
    wm = (8 * M_allow) / (L_cm**2) * 100 # kg/m
    
    # 3. Load limit by Deflection: delta = 5wL^4 / 384EI
    # delta_allow = L/360
    delta_allow = L_cm / defl_lim_val
    # w = (delta * 384 * E * I) / (5 * L^4)
    wd = (delta_allow * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100 # kg/m
    
    w_shear.append(ws)
    w_moment.append(wm)
    w_defl.append(wd)
    
    # Min governs
    min_w = min(ws, wm, wd)
    w_govern.append(min_w)
    
    if min_w == ws: govern_cause.append("Shear")
    elif min_w == wm: govern_cause.append("Moment")
    else: govern_cause.append("Deflection")

# 4.4 Optimal Range Logic
# Optimal is usually L/d between 15 and 20 (Rule of Thumb)
d_m = p['h'] / 1000
opt_min_span = 15 * d_m
opt_max_span = 20 * d_m

# ==========================================
# 5. UI DISPLAY
# ==========================================
st.title(f"📊 Beam Insight: {sec_name}")

# --- SECTION 1: THE ANSWER (Optimal Range) ---
col_opt, col_cap = st.columns([1, 2])

with col_opt:
    st.markdown(f"""
    <div class="highlight-card">
        <h3 style="margin-top:0; color:#1abc9c;">✅ Optimal Span</h3>
        <div class="big-num">{opt_min_span:.1f} - {opt_max_span:.1f} m.</div>
        <div class="sub-text">ช่วงความยาวที่เหมาะสมที่สุด (L/d = 15~20)</div>
        <hr>
        <b>Why?</b><br>
        <small>
        • สั้นกว่านี้ = Shear สูง (เปลืองเหล็ก)<br>
        • ยาวกว่านี้ = Deflection ตกท้องช้าง
        </small>
    </div>
    """, unsafe_allow_html=True)

with col_cap:
    # Interactive Slider to check specific span
    check_span = st.slider("🔍 เลื่อนเพื่อดูความสามารถรับน้ำหนักที่ Span ต่างๆ (m)", 2.0, 15.0, (opt_min_span+opt_max_span)/2, 0.5)
    
    # Find closest index
    idx = (np.abs(spans - check_span)).argmin()
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='metric-box'><div class='sub-text'>Safe Uniform Load</div><div class='big-num' style='color:#2e86c1'>{w_govern[idx]:,.0f}</div><div class='sub-text'>kg/m</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='metric-box'><div class='sub-text'>End Reaction (V)</div><div class='big-num' style='color:#d35400'>{w_govern[idx]*check_span/2:,.0f}</div><div class='sub-text'>kg</div></div>", unsafe_allow_html=True)
    with c3:
        req_b = math.ceil((w_govern[idx]*check_span/2) / v_bolt)
        st.markdown(f"<div class='metric-box'><div class='sub-text'>Bolts Required</div><div class='big-num' style='color:#27ae60'>{req_b}</div><div class='sub-text'>x {bolt_size}</div></div>", unsafe_allow_html=True)
        
    st.caption(f"*Note: Limitation at {check_span}m is **{govern_cause[idx]}**")

# --- SECTION 2: THE GRAPH (Governing Curve) ---
st.subheader("📈 Load Capacity Chart (Safe Load Table)")
st.markdown("กราฟแสดงน้ำหนักบรรทุกปลอดภัย (Safe Load) ที่ความยาวช่วงต่างๆ")

fig = go.Figure()

# Plot Limit Lines
fig.add_trace(go.Scatter(x=spans, y=w_moment, mode='lines', name='Moment Limit', line=dict(color='orange', dash='dot', width=1)))
fig.add_trace(go.Scatter(x=spans, y=w_shear, mode='lines', name='Shear Limit', line=dict(color='red', dash='dot', width=1)))
fig.add_trace(go.Scatter(x=spans, y=w_defl, mode='lines', name=f'Deflection Limit ({defl_ratio})', line=dict(color='green', dash='dot', width=1)))

# Plot Governing Area
fig.add_trace(go.Scatter(
    x=spans, y=w_govern, mode='lines', name='✅ Safe Load Capacity',
    line=dict(color='#2E86C1', width=4),
    fill='tozeroy', fillcolor='rgba(46, 134, 193, 0.1)'
))

# Highlight Optimal Zone
fig.add_vrect(x0=opt_min_span, x1=opt_max_span, fillcolor="green", opacity=0.1, 
              annotation_text="Optimal Span", annotation_position="top")

# Layout
fig.update_layout(
    xaxis_title="Span Length (m)",
    yaxis_title="Safe Uniform Load (kg/m)",
    hovermode="x unified",
    yaxis=dict(range=[0, max(w_govern)*1.2]),
    height=450,
    margin=dict(t=30, b=20, l=20, r=20),
    legend=dict(orientation="h", y=1.1)
)
st.plotly_chart(fig, use_container_width=True)

# --- SECTION 3: CONNECTION MATRIX ---
st.subheader("🔩 Connection Recommendation Matrix")
col_tbl, col_note = st.columns([2, 1])

with col_tbl:
    # Generate Table Data for Standard Spans
    std_spans = [4, 6, 8, 10, 12]
    table_data = []
    
    for s in std_spans:
        if s < 2 or s > 15: continue
        # Find Val
        i = (np.abs(spans - s)).argmin()
        load = w_govern[i]
        react = load * s / 2
        nb = math.ceil(react / v_bolt)
        
        # Check suitability text
        suit = "✅ Good"
        if s < opt_min_span: suit = "⚠️ Deep Beam"
        elif s > opt_max_span: suit = "⚠️ Deflection Prone"
        
        table_data.append({
            "Span (m)": f"{s:.1f}",
            "Safe Load (kg/m)": f"{load:,.0f}",
            "Reaction (kg)": f"{react:,.0f}",
            "Bolts Req": f"{nb}",
            "Suitability": suit
        })
        
    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

with col_note:
    st.info(f"""
    **📌 วิธีใช้งาน:**
    
    1. **เลือก Span ที่ต้องการใช้งาน** จากตารางซ้ายมือ
    2. ดูค่า **Safe Load** ว่าเพียงพอกับงานหรือไม่
    3. ดูจำนวน **Bolts** เพื่อนำไปทำแบบ Standard Detail
    
    **Bolt Info ({bolt_size}):**
    * Shear Cap: {v_bolt_shear:,.0f} kg
    * Bearing Cap: {v_bolt_bear:,.0f} kg
    """)
