import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & STYLE
# ==========================================
st.set_page_config(page_title="Beam Capacity Insight", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .highlight-card { background-color: #e8f6f3; padding: 20px; border-radius: 10px; border: 1px solid #1abc9c; }
    .metric-box { text-align: center; padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-top: 3px solid #3498db; }
    .big-num { font-size: 24px; font-weight: bold; color: #17202a; }
    .sub-text { font-size: 14px; color: #7f8c8d; margin-top: 5px; }
    .limit-label { font-size: 12px; background-color: #f1c40f; padding: 2px 8px; border-radius: 10px; color: #7f8c8d; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE
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

# ==========================================
# 3. SIDEBAR INPUTS
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2666/2666505.png", width=60)
    st.title("Beam Capacity Insight")
    st.divider()
    
    st.header("⚙️ Design Parameters")
    sec_name = st.selectbox("Select Section", list(steel_db.keys()), index=5)
    
    # Span Input สำหรับคำนวณย้อนกลับ
    st.markdown("### 📏 Target Span")
    user_span = st.number_input("Length (m)", min_value=1.0, value=6.0, step=0.5, help="ระบุความยาวที่ต้องการตรวจสอบ Capacity")
    
    st.divider()
    col_fy, col_dl = st.columns(2)
    with col_fy:
        fy = st.number_input("Fy (ksc)", 2400)
    with col_dl:
        defl_ratio = st.selectbox("Defl. Limit", ["L/300", "L/360", "L/400"], index=1)
    
    E_mod = 2.04e6 # ksc
    defl_lim_val = int(defl_ratio.split("/")[1])
    
    # Bolt Info ย้ายลงมาข้างล่างเพราะเป็นเรื่องรอง
    st.divider()
    st.caption("🔩 Connection Assumption")
    bolt_size = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)


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

# 4.2 Capacities (Allowable Limits of Section)
M_cap = 0.6 * fy * Zx # kg.cm
V_cap = 0.4 * fy * Aw # kg

# Bolt Cap
dia_cm = int(bolt_size[1:])/10
b_area = 3.14 if bolt_size=="M20" else (2.01 if bolt_size=="M16" else 3.8)
v_bolt_shear = 1000 * b_area 
v_bolt_bear = 1.2 * 4000 * dia_cm * tw_cm
v_bolt = min(v_bolt_shear, v_bolt_bear)

# 4.3 Generate Load Curve (Capacity vs Span)
spans = np.linspace(2, 15, 100) # meters
w_shear = []
w_moment = []
w_defl = []
w_govern = []
govern_cause = []

for L in spans:
    L_cm = L * 100
    # Reverse Eq: w = ...
    ws = (2 * V_cap) / L_cm * 100 # kg/m
    wm = (8 * M_cap) / (L_cm**2) * 100 # kg/m
    delta_allow = L_cm / defl_lim_val
    wd = (delta_allow * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100 # kg/m
    
    w_shear.append(ws)
    w_moment.append(wm)
    w_defl.append(wd)
    
    min_w = min(ws, wm, wd)
    w_govern.append(min_w)
    
    if min_w == ws: govern_cause.append("Shear Control")
    elif min_w == wm: govern_cause.append("Moment Control")
    else: govern_cause.append("Deflection Control")

# 4.4 Calculate for SPECIFIC USER SPAN
# แทนที่จะ check ว่า user load ผ่านไหม เราคำนวณ max load ที่ span นี้เลย
L_target_cm = user_span * 100
w_cap_shear = (2 * V_cap) / L_target_cm * 100
w_cap_moment = (8 * M_cap) / (L_target_cm**2) * 100
delta_target = L_target_cm / defl_lim_val
w_cap_defl = (delta_target * 384 * E_mod * Ix) / (5 * (L_target_cm**4)) * 100

max_safe_load = min(w_cap_shear, w_cap_moment, w_cap_defl)

# Determine Cause
if max_safe_load == w_cap_shear: 
    cause_text = "Shear (แรงเฉือน)"
    cause_color = "#e74c3c" # Red
elif max_safe_load == w_cap_moment: 
    cause_text = "Moment (โมเมนต์ดัด)"
    cause_color = "#f39c12" # Orange
else: 
    cause_text = f"Deflection ({defl_ratio})"
    cause_color = "#27ae60" # Green

# Calculate Resulting Forces at Max Load
V_at_max = max_safe_load * user_span / 2
M_at_max = max_safe_load * (user_span**2) / 8 # kg.m
req_bolt = math.ceil(V_at_max / v_bolt)

# Optimal Range
d_m = p['h'] / 1000
opt_min_span = 15 * d_m
opt_max_span = 20 * d_m

# ==========================================
# 5. UI DISPLAY
# ==========================================

tab1, tab2, tab3 = st.tabs(["📊 Capacity Analysis", "📐 Section Properties", "💾 Load Table"])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.subheader(f"Capacity Analysis for: {sec_name} @ {user_span} m.")
    
    # 1.1 Result Card (The Big Answer)
    st.markdown(f"""
    <div class="highlight-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span class="sub-text">Maximum Uniform Load Capacity</span><br>
                <span class="big-num" style="font-size: 36px;">{max_safe_load:,.0f}</span> <span style="font-size:20px; color:#555;">kg/m</span>
            </div>
            <div style="text-align: right;">
                <span class="sub-text">Limited by</span><br>
                <span style="font-size: 18px; font-weight:bold; color:{cause_color};">{cause_text}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # 1.2 Breakdown Metrics (Compare Actual vs Cap)
    st.markdown("##### 📌 Resulting Forces at Max Capacity")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        # SHEAR
        shear_usage = (V_at_max / V_cap) * 100
        st.markdown(f"""
        <div class="metric-box" style="border-top-color: #e74c3c;">
            <div class="sub-text">End Reaction (V)</div>
            <div class="big-num">{V_at_max:,.0f} <small style="font-size:14px; color:#999;">kg</small></div>
            <div class="sub-text">Capacity: {V_cap:,.0f} kg</div>
            <div style="background:#eee; height:6px; width:100%; margin-top:5px; border-radius:3px;">
                <div style="background:#e74c3c; width:{shear_usage}%; height:100%; border-radius:3px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        # MOMENT
        moment_usage = ((M_at_max*100) / M_cap) * 100
        st.markdown(f"""
        <div class="metric-box" style="border-top-color: #f39c12;">
            <div class="sub-text">Max Moment (M)</div>
            <div class="big-num">{M_at_max:,.0f} <small style="font-size:14px; color:#999;">kg.m</small></div>
            <div class="sub-text">Capacity: {M_cap/100:,.0f} kg.m</div>
             <div style="background:#eee; height:6px; width:100%; margin-top:5px; border-radius:3px;">
                <div style="background:#f39c12; width:{moment_usage}%; height:100%; border-radius:3px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with c3:
        # CONNECTION
        st.markdown(f"""
        <div class="metric-box" style="border-top-color: #34495e;">
            <div class="sub-text">Connection Suggestion</div>
            <div class="big-num">{req_bolt} <small style="font-size:14px; color:#999;">Bolts</small></div>
            <div class="sub-text">Size: {bolt_size} (Shear Cap: {v_bolt:,.0f} kg)</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 1.3 Graph Visualization
    st.markdown("#### 📈 Capacity Curve")
    fig = go.Figure()
    
    # Limit lines
    fig.add_trace(go.Scatter(x=spans, y=w_moment, mode='lines', name='Moment Limit', line=dict(color='orange', dash='dot', width=1)))
    fig.add_trace(go.Scatter(x=spans, y=w_shear, mode='lines', name='Shear Limit', line=dict(color='red', dash='dot', width=1)))
    fig.add_trace(go.Scatter(x=spans, y=w_defl, mode='lines', name=f'Deflection Limit ({defl_ratio})', line=dict(color='green', dash='dot', width=1)))
    
    # Safe Load Area
    fig.add_trace(go.Scatter(x=spans, y=w_govern, mode='lines', name='Max Safe Load', line=dict(color='#2E86C1', width=3), fill='tozeroy', fillcolor='rgba(46, 134, 193, 0.1)'))
    
    # Target Marker
    fig.add_trace(go.Scatter(
        x=[user_span], y=[max_safe_load], 
        mode='markers+text', name='Current Selection',
        marker=dict(color='black', size=12, symbol='star'),
        text=[f"{max_safe_load:,.0f}"], textposition="top center"
    ))
    
    fig.update_layout(xaxis_title="Span Length (m)", yaxis_title="Uniform Load (kg/m)", height=450, hovermode="x unified", margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: SECTION PROPERTIES ---
with tab2:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Section Data")
        st.table(pd.DataFrame({
            "Property": ["Depth (d)", "Width (b)", "Web (tw)", "Flange (tf)", "Ix", "Zx", "Area (Aw)"],
            "Value": [p['h'], p['b'], p['tw'], p['tf'], p['Ix'], p['Zx'], f"{Aw:.2f}"],
            "Unit": ["mm", "mm", "mm", "mm", "cm4", "cm3", "cm2"]
        }))
    with c2:
        st.subheader("Capacity Constants")
        st.markdown(f"""
        - **Allowable Moment ($M_a = 0.6F_y Z_x$):** {M_cap/100:,.0f} kg.m
        - **Allowable Shear ($V_a = 0.4F_y A_w$):** {V_cap:,.0f} kg
        - **Modulus of Elasticity ($E$):** {E_mod:,.0e} ksc
        """)
        st.info("Section properties are based on standard JIS/TIS H-Beam tables.")

# --- TAB 3: LOAD TABLE ---
with tab3:
    st.subheader(f"Load Capacity Table for {sec_name}")
    df_res = pd.DataFrame({
        "Span (m)": spans,
        "Max Load (kg/m)": w_govern,
        "Limited By": govern_cause,
        "Reaction V (kg)": [w * l / 2 for w, l in zip(w_govern, spans)],
        "Max Moment (kg.m)": [w * l**2 / 8 for w, l in zip(w_govern, spans)]
    }).round(0)
    
    st.dataframe(df_res, use_container_width=True, height=500)
    
    csv = df_res.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Capacity Table (CSV)", data=csv, file_name=f'capacity_{sec_name}.csv', mime='text/csv')
