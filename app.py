import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & STYLE
# ==========================================
st.set_page_config(page_title="Beam Capacity Insight V2.2", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .highlight-card { background-color: #e8f6f3; padding: 20px; border-radius: 10px; border: 1px solid #1abc9c; }
    .metric-box { text-align: center; padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-top: 3px solid #3498db; }
    .big-num { font-size: 24px; font-weight: bold; color: #17202a; }
    .sub-text { font-size: 14px; color: #7f8c8d; margin-top: 5px; }
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
    
    st.markdown("### 📏 Target Span")
    user_span = st.number_input("Length (m)", min_value=1.0, value=6.0, step=0.5)
    
    st.divider()
    col_fy, col_dl = st.columns(2)
    with col_fy:
        fy = st.number_input("Fy (ksc)", 2400)
    with col_dl:
        defl_ratio = st.selectbox("Defl. Limit", ["L/300", "L/360", "L/400"], index=1)
    
    E_mod = 2.04e6 # ksc
    defl_lim_val = int(defl_ratio.split("/")[1])
    
    st.divider()
    st.caption("🔩 Connection Assumption")
    bolt_size = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)

# ==========================================
# 4. CALCULATION ENGINE (HELPER FUNCTION)
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

def get_capacity(L_m):
    """Calculate capacity for a given span L (meters)"""
    L_cm = L_m * 100
    
    # Allowable Loads based on criteria
    w_s = (2 * V_cap) / L_cm * 100  # Shear Control
    w_m = (8 * M_cap) / (L_cm**2) * 100 # Moment Control
    delta_allow = L_cm / defl_lim_val
    w_d = (delta_allow * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100 # Deflection Control
    
    w_gov = min(w_s, w_m, w_d)
    
    cause = "Deflection"
    if w_gov == w_s: cause = "Shear"
    elif w_gov == w_m: cause = "Moment"
    
    return w_s, w_m, w_d, w_gov, cause

# ==========================================
# 5. DATA GENERATION
# ==========================================

# 5.1 For Graph (High Resolution)
graph_spans = np.linspace(2, 15, 100)
graph_data = [get_capacity(l) for l in graph_spans]
w_shear_g = [x[0] for x in graph_data]
w_moment_g = [x[1] for x in graph_data]
w_defl_g = [x[2] for x in graph_data]
w_gov_g = [x[3] for x in graph_data]

# 5.2 For Table (Clean Steps: 0.5m) -> แก้ปัญหาเลขซ้ำ
table_spans = np.arange(2, 15.5, 0.5) 
table_data = [get_capacity(l) for l in table_spans]
w_gov_t = [x[3] for x in table_data]
cause_t = [x[4] for x in table_data]

# 5.3 For User Specific Span
_, _, _, user_safe_load, user_cause = get_capacity(user_span)
V_at_max = user_safe_load * user_span / 2
M_at_max = user_safe_load * (user_span**2) / 8
req_bolt = math.ceil(V_at_max / v_bolt)

# ==========================================
# 6. UI DISPLAY
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 Capacity Analysis", "📐 Section Properties", "💾 Load Table"])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.subheader(f"Capacity Analysis for: {sec_name} @ {user_span} m.")
    
    # Card
    cause_color = "#e74c3c" if user_cause == "Shear" else ("#f39c12" if user_cause == "Moment" else "#27ae60")
    st.markdown(f"""
    <div class="highlight-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span class="sub-text">Maximum Uniform Load Capacity</span><br>
                <span class="big-num" style="font-size: 36px;">{user_safe_load:,.0f}</span> <span style="font-size:20px; color:#555;">kg/m</span>
            </div>
            <div style="text-align: right;">
                <span class="sub-text">Limited by</span><br>
                <span style="font-size: 18px; font-weight:bold; color:{cause_color};">{user_cause}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Metrics
    c1, c2, c3 = st.columns(3)
    with c1:
        shear_pct = (V_at_max / V_cap) * 100
        st.markdown(f"<div class='metric-box'><div class='sub-text'>Reaction (V)</div><div class='big-num'>{V_at_max:,.0f}</div><div class='sub-text'>Cap: {V_cap:,.0f} kg ({shear_pct:.0f}%)</div></div>", unsafe_allow_html=True)
    with c2:
        moment_pct = ((M_at_max*100) / M_cap) * 100
        st.markdown(f"<div class='metric-box'><div class='sub-text'>Moment (M)</div><div class='big-num'>{M_at_max:,.0f}</div><div class='sub-text'>Cap: {M_cap/100:,.0f} kg.m ({moment_pct:.0f}%)</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='metric-box'><div class='sub-text'>Connection</div><div class='big-num'>{req_bolt}</div><div class='sub-text'>Bolts ({bolt_size})</div></div>", unsafe_allow_html=True)

    # Graph
    st.markdown("#### 📈 Capacity Curve")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=graph_spans, y=w_moment_g, mode='lines', name='Moment Limit', line=dict(color='orange', dash='dot')))
    fig.add_trace(go.Scatter(x=graph_spans, y=w_shear_g, mode='lines', name='Shear Limit', line=dict(color='red', dash='dot')))
    fig.add_trace(go.Scatter(x=graph_spans, y=w_defl_g, mode='lines', name=f'Defl. Limit', line=dict(color='green', dash='dot')))
    fig.add_trace(go.Scatter(x=graph_spans, y=w_gov_g, mode='lines', name='Safe Load', line=dict(color='#2E86C1', width=3), fill='tozeroy', fillcolor='rgba(46, 134, 193, 0.1)'))
    fig.add_trace(go.Scatter(x=[user_span], y=[user_safe_load], mode='markers', marker=dict(color='black', size=12, symbol='star'), name='Selected'))
    
    fig.update_layout(xaxis_title="Span (m)", yaxis_title="Load (kg/m)", height=450, hovermode="x unified", margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: SECTION ---
with tab2:
    st.table(pd.DataFrame({
        "Property": ["Depth", "Width", "Web", "Flange", "Ix", "Zx"],
        "Value": [p['h'], p['b'], p['tw'], p['tf'], p['Ix'], p['Zx']],
        "Unit": ["mm", "mm", "mm", "mm", "cm4", "cm3"]
    }))

# --- TAB 3: TABLE ---
with tab3:
    st.subheader(f"Load Capacity Table: {sec_name}")
    
    # สร้าง DataFrame ใหม่จาก table_data (ที่ Span สะอาดๆ)
    df_res = pd.DataFrame({
        "Span (m)": table_spans,
        "Max Load (kg/m)": w_gov_t,
        "Limited By": cause_t,
        "Reaction V (kg)": [w * l / 2 for w, l in zip(w_gov_t, table_spans)],
        "Max Moment (kg.m)": [w * l**2 / 8 for w, l in zip(w_gov_t, table_spans)]
    })
    
    # Formatting display
    st.dataframe(
        df_res.style.format({
            "Span (m)": "{:.1f}", 
            "Max Load (kg/m)": "{:,.0f}",
            "Reaction V (kg)": "{:,.0f}",
            "Max Moment (kg.m)": "{:,.0f}"
        }), 
        use_container_width=True, 
        height=500
    )
    
    csv = df_res.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download CSV", data=csv, file_name=f'capacity_{sec_name}.csv', mime='text/csv')
