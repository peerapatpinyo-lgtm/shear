import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & STYLE
# ==========================================
st.set_page_config(page_title="Beam Insight V2.3", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .highlight-card { background-color: #e8f6f3; padding: 20px; border-radius: 10px; border: 1px solid #1abc9c; }
    .metric-box { text-align: center; padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-top: 3px solid #3498db; }
    .big-num { font-size: 24px; font-weight: bold; color: #17202a; }
    .sub-text { font-size: 14px; color: #7f8c8d; margin-top: 5px; }
    .opt-tag { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; margin-left: 8px;}
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
    st.title("Beam Insight V2.3")
    st.divider()
    
    st.header("⚙️ Design Parameters")
    sec_name = st.selectbox("Select Section", list(steel_db.keys()), index=5)
    
    st.markdown("### 📏 Target Span")
    user_span = st.number_input("Length (m)", min_value=1.0, value=6.0, step=0.5)
    
    st.divider()
    col_fy, col_dl = st.columns(2)
    with col_fy:
        fy = st.number_input("Fy (ksc)", 2400)
    with col_dl:
        defl_ratio = st.selectbox("Defl. Limit", ["L/300", "L/360", "L/400"], index=1)
    
    E_mod = 2.04e6 
    defl_lim_val = int(defl_ratio.split("/")[1])
    
    st.divider()
    bolt_size = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)

# ==========================================
# 4. CALCULATION ENGINE
# ==========================================
p = steel_db[sec_name]

# Properties
h_cm = p['h']/10
tw_cm = p['tw']/10
Aw = h_cm * tw_cm
Ix = p['Ix']
Zx = p['Zx']

# Capacities
M_cap = 0.6 * fy * Zx # kg.cm
V_cap = 0.4 * fy * Aw # kg

# Bolt Cap
dia_cm = int(bolt_size[1:])/10
b_area = 3.14 if bolt_size=="M20" else (2.01 if bolt_size=="M16" else 3.8)
v_bolt = min(1000 * b_area, 1.2 * 4000 * dia_cm * tw_cm)

# Helper Function
def get_capacity(L_m):
    L_cm = L_m * 100
    w_s = (2 * V_cap) / L_cm * 100
    w_m = (8 * M_cap) / (L_cm**2) * 100
    delta_allow = L_cm / defl_lim_val
    w_d = (delta_allow * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100
    w_gov = min(w_s, w_m, w_d)
    
    cause = "Deflection"
    if w_gov == w_s: cause = "Shear"
    elif w_gov == w_m: cause = "Moment"
    
    return w_s, w_m, w_d, w_gov, cause

# --- CALCULATION FOR USER SPAN ---
_, _, _, user_safe_load, user_cause = get_capacity(user_span)

# Forces at Max Load
V_at_max = user_safe_load * user_span / 2
M_at_max = user_safe_load * (user_span**2) / 8 # kg.m

# ⚠️ Calculate Deflection at Max Load (Fix: คำนวณจริงตาม Load ที่รับได้)
L_cm = user_span * 100
delta_actual = (5 * (user_safe_load/100) * (L_cm**4)) / (384 * E_mod * Ix) # cm
delta_allow = L_cm / defl_lim_val # cm

# Percentages
shear_pct = (V_at_max / V_cap) * 100
moment_pct = ((M_at_max*100) / M_cap) * 100
defl_pct = (delta_actual / delta_allow) * 100

req_bolt = math.ceil(V_at_max / v_bolt)

# --- OPTIMAL SPAN LOGIC ---
# Rule of Thumb: L approx 15d - 20d
d_m = p['h'] / 1000
opt_min = 15 * d_m
opt_max = 20 * d_m

# Span Status Logic
if user_span < opt_min:
    span_status = "Deep (สั้นเกินไป/เปลือง)"
    span_color = "#f1c40f" # Yellow
    span_bg = "#fcf3cf"
elif user_span > opt_max:
    span_status = "Slender (ยาวเกินไป/เสี่ยงแอ่น)"
    span_color = "#e74c3c" # Red
    span_bg = "#fadbd8"
else:
    span_status = "Optimal (เหมาะสม)"
    span_color = "#27ae60" # Green
    span_bg = "#d5f5e3"

# ==========================================
# 5. UI DISPLAY
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 Capacity Analysis", "📐 Section Properties", "💾 Load Table"])

with tab1:
    st.subheader(f"Capacity Analysis for: {sec_name}")

    # --- PART 1: OPTIMAL CHECK ---
    st.markdown(f"""
    <div style="background-color: {span_bg}; padding: 10px 15px; border-radius: 8px; border-left: 5px solid {span_color}; margin-bottom: 20px;">
        <span style="color: {span_color}; font-weight: bold; font-size: 16px;">
            Span {user_span} m. is {span_status}
        </span>
        <br>
        <span style="font-size: 14px; color: #555;">
            💡 ช่วงความยาวที่ประหยัด (Optimal Range L/d ≈ 15-20) สำหรับหน้าตัดนี้คือ: <b>{opt_min:.1f} - {opt_max:.1f} m.</b>
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # --- PART 2: MAIN CARD ---
    cause_color = "#e74c3c" if user_cause == "Shear" else ("#f39c12" if user_cause == "Moment" else "#27ae60")
    st.markdown(f"""
    <div class="highlight-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span class="sub-text">Maximum Safe Uniform Load</span><br>
                <span class="big-num" style="font-size: 36px;">{user_safe_load:,.0f}</span> <span style="font-size:20px; color:#555;">kg/m</span>
            </div>
            <div style="text-align: right;">
                <span class="sub-text">Controlled by</span><br>
                <span style="font-size: 18px; font-weight:bold; color:{cause_color};">{user_cause}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # --- PART 3: DETAILED METRICS (WITH DEFLECTION %) ---
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(f"""
        <div class="metric-box" style="border-top-color: #e74c3c;">
            <div class="sub-text">Shear (V)</div>
            <div class="big-num">{V_at_max:,.0f} <small style="font-size:14px; color:#999;">kg</small></div>
            <div class="sub-text">Usage: <b>{shear_pct:.0f}%</b></div>
            <div style="background:#eee; height:6px; width:100%; margin-top:5px; border-radius:3px;">
                <div style="background:#e74c3c; width:{shear_pct}%; height:100%; border-radius:3px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown(f"""
        <div class="metric-box" style="border-top-color: #f39c12;">
            <div class="sub-text">Moment (M)</div>
            <div class="big-num">{M_at_max:,.0f} <small style="font-size:14px; color:#999;">kg.m</small></div>
            <div class="sub-text">Usage: <b>{moment_pct:.0f}%</b></div>
             <div style="background:#eee; height:6px; width:100%; margin-top:5px; border-radius:3px;">
                <div style="background:#f39c12; width:{moment_pct}%; height:100%; border-radius:3px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with c3:
        # DEFLECTION METRIC
        st.markdown(f"""
        <div class="metric-box" style="border-top-color: #27ae60;">
            <div class="sub-text">Deflection (Δ)</div>
            <div class="big-num">{delta_actual:.2f} <small style="font-size:14px; color:#999;">cm</small></div>
            <div class="sub-text">Usage: <b>{defl_pct:.0f}%</b> (Limit {delta_allow:.2f})</div>
             <div style="background:#eee; height:6px; width:100%; margin-top:5px; border-radius:3px;">
                <div style="background:#27ae60; width:{min(defl_pct, 100)}%; height:100%; border-radius:3px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.caption(f"Connection Requirement: {req_bolt} bolts of {bolt_size} (at Max Load)")

    # --- PART 4: GRAPH ---
    st.markdown("#### 📈 Capacity Curve & Optimal Zone")
    
    # Generate Data
    g_spans = np.linspace(2, 15, 100)
    g_data = [get_capacity(l) for l in g_spans]
    
    fig = go.Figure()
    
    # Highlight Optimal Zone
    fig.add_vrect(x0=opt_min, x1=opt_max, fillcolor="green", opacity=0.1, 
                  annotation_text="Optimal Range", annotation_position="top left")
    
    # Lines
    fig.add_trace(go.Scatter(x=g_spans, y=[x[1] for x in g_data], mode='lines', name='Moment Limit', line=dict(color='orange', dash='dot')))
    fig.add_trace(go.Scatter(x=g_spans, y=[x[0] for x in g_data], mode='lines', name='Shear Limit', line=dict(color='red', dash='dot')))
    fig.add_trace(go.Scatter(x=g_spans, y=[x[2] for x in g_data], mode='lines', name=f'Defl. Limit', line=dict(color='green', dash='dot')))
    fig.add_trace(go.Scatter(x=g_spans, y=[x[3] for x in g_data], mode='lines', name='Safe Load', line=dict(color='#2E86C1', width=3), fill='tozeroy', fillcolor='rgba(46, 134, 193, 0.1)'))
    
    # User Point
    fig.add_trace(go.Scatter(x=[user_span], y=[user_safe_load], mode='markers', marker=dict(color='black', size=12, symbol='star'), name='Current Span'))
    
    fig.update_layout(xaxis_title="Span (m)", yaxis_title="Load (kg/m)", height=450, hovermode="x unified", margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 2 & 3 (Same as before) ---
with tab2:
    st.table(pd.DataFrame({
        "Property": ["Depth", "Width", "Web", "Flange", "Ix", "Zx"],
        "Value": [p['h'], p['b'], p['tw'], p['tf'], p['Ix'], p['Zx']],
        "Unit": ["mm", "mm", "mm", "mm", "cm4", "cm3"]
    }))

with tab3:
    table_spans = np.arange(2, 15.5, 0.5) 
    table_data = [get_capacity(l) for l in table_spans]
    df_res = pd.DataFrame({
        "Span (m)": table_spans,
        "Max Load (kg/m)": [x[3] for x in table_data],
        "Limited By": [x[4] for x in table_data],
        "Deflection (cm)": [(5 * (x[3]/100) * ((l*100)**4)) / (384 * E_mod * Ix) for l, x in zip(table_spans, table_data)]
    })
    
    st.dataframe(df_res.style.format({"Span (m)": "{:.1f}", "Max Load (kg/m)": "{:,.0f}", "Deflection (cm)": "{:.2f}"}), use_container_width=True, height=500)
