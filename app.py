import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & STYLE
# ==========================================
st.set_page_config(page_title="Beam Insight Pro V2", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .highlight-card { background-color: #e8f6f3; padding: 20px; border-radius: 10px; border: 1px solid #1abc9c; }
    .fail-card { background-color: #fdedec; padding: 20px; border-radius: 10px; border: 1px solid #e74c3c; }
    .metric-box { text-align: center; padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-top: 3px solid #3498db; }
    .big-num { font-size: 24px; font-weight: bold; color: #17202a; }
    .sub-text { font-size: 14px; color: #7f8c8d; margin-top: 5px; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f8f9f9; border-radius: 4px 4px 0 0; gap: 1px; padding-top: 10px; padding-bottom: 10px; }
    .stTabs [aria-selected="true"] { background-color: #ffffff; border-bottom: 2px solid #3498db; color: #3498db; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE (Expanded)
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
    st.title("Beam Insight Pro")
    st.caption("v2.0 | Engineered for Speed")
    st.divider()
    
    st.header("⚙️ Design Parameters")
    sec_name = st.selectbox("Select Section", list(steel_db.keys()), index=5)
    bolt_size = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)
    
    st.divider()
    col_fy, col_dl = st.columns(2)
    with col_fy:
        fy = st.number_input("Fy (ksc)", 2400)
    with col_dl:
        defl_ratio = st.selectbox("Defl. Limit", ["L/300", "L/360", "L/400"], index=1)
    
    E_mod = 2.04e6 # ksc
    defl_lim_val = int(defl_ratio.split("/")[1])
    
    st.divider()
    st.subheader("🎯 Check Specific Load")
    user_span = st.number_input("Design Span (m)", min_value=1.0, value=6.0, step=0.5)
    user_load = st.number_input("Design Load (kg/m)", min_value=0, value=1500, step=100)


# ==========================================
# 4. CALCULATION ENGINE
# ==========================================
p = steel_db[sec_name]

# 4.1 Properties
h_cm = p['h']/10
tw_cm = p['tw']/10
tf_cm = p['tf']/10
b_cm = p['b']/10
Aw = h_cm * tw_cm
Ix = p['Ix']
Zx = p['Zx']

# 4.2 Capacities
M_allow = 0.6 * fy * Zx # kg.cm
V_allow_web = 0.4 * fy * Aw # kg

# Bolt Cap
dia_cm = int(bolt_size[1:])/10
b_area = 3.14 if bolt_size=="M20" else (2.01 if bolt_size=="M16" else 3.8)
v_bolt_shear = 1000 * b_area # Approximate simple shear per bolt
v_bolt_bear = 1.2 * 4000 * dia_cm * tw_cm
v_bolt = min(v_bolt_shear, v_bolt_bear)

# 4.3 Generate Load Curve
spans = np.linspace(2, 15, 100) # meters
w_shear = []
w_moment = []
w_defl = []
w_govern = []
govern_cause = []

for L in spans:
    L_cm = L * 100
    ws = (2 * V_allow_web) / L_cm * 100 # kg/m
    wm = (8 * M_allow) / (L_cm**2) * 100 # kg/m
    delta_allow = L_cm / defl_lim_val
    wd = (delta_allow * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100 # kg/m
    
    w_shear.append(ws)
    w_moment.append(wm)
    w_defl.append(wd)
    
    min_w = min(ws, wm, wd)
    w_govern.append(min_w)
    
    if min_w == ws: govern_cause.append("Shear")
    elif min_w == wm: govern_cause.append("Moment")
    else: govern_cause.append("Deflection")

# 4.4 Optimal Range
d_m = p['h'] / 1000
opt_min_span = 15 * d_m
opt_max_span = 20 * d_m

# ==========================================
# 5. UI DISPLAY (TABS)
# ==========================================

tab1, tab2, tab3 = st.tabs(["📊 Dashboard Analysis", "📐 Section Details", "💾 Data Table"])

# --- TAB 1: DASHBOARD ---
with tab1:
    # 1.1 Header & Pass/Fail Check
    st.subheader(f"Analysis for: {sec_name}")
    
    # Calculate Capacity at User Span
    idx_check = (np.abs(spans - user_span)).argmin()
    cap_load = w_govern[idx_check]
    cap_cause = govern_cause[idx_check]
    dc_ratio = user_load / cap_load
    
    col_status, col_metrics = st.columns([1.5, 3])
    
    with col_status:
        if user_load <= cap_load:
            st.markdown(f"""
            <div class="highlight-card">
                <h2 style="color:#27ae60; margin:0;">✅ PASS</h2>
                <div class="sub-text">Load Efficiency (D/C): <b>{dc_ratio*100:.1f}%</b></div>
                <progress value="{dc_ratio}" max="1" style="width:100%; height:10px;"></progress>
                <hr>
                <small>Allows up to <b>{cap_load:,.0f} kg/m</b><br>Governed by: {cap_cause}</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="fail-card">
                <h2 style="color:#c0392b; margin:0;">❌ FAIL</h2>
                <div class="sub-text">Over Capacity: <b>{dc_ratio*100:.1f}%</b></div>
                <progress value="1" max="1" style="width:100%; height:10px; accent-color: red;"></progress>
                <hr>
                <small>Limit is <b>{cap_load:,.0f} kg/m</b><br>Failed by: {cap_cause}</small>
            </div>
            """, unsafe_allow_html=True)

    with col_metrics:
        m1, m2, m3 = st.columns(3)
        # Recalculate forces for user input
        user_V = user_load * user_span / 2
        user_M = user_load * (user_span**2) / 8 * 100 # kg.cm
        user_Defl = (5 * (user_load/100) * ((user_span*100)**4)) / (384 * E_mod * Ix)
        
        with m1: st.markdown(f"<div class='metric-box'><div class='sub-text'>Max Shear (V)</div><div class='big-num'>{user_V:,.0f}</div><div class='sub-text'>kg (Cap: {V_allow_web:,.0f})</div></div>", unsafe_allow_html=True)
        with m2: st.markdown(f"<div class='metric-box'><div class='sub-text'>Max Moment (M)</div><div class='big-num'>{user_M/100:,.0f}</div><div class='sub-text'>kg.m (Cap: {M_allow/100:,.0f})</div></div>", unsafe_allow_html=True)
        with m3: st.markdown(f"<div class='metric-box'><div class='sub-text'>Deflection</div><div class='big-num'>{user_Defl:.2f}</div><div class='sub-text'>cm (Limit: {user_span*100/defl_lim_val:.2f})</div></div>", unsafe_allow_html=True)

    st.markdown("---")
    
    # 1.2 The Chart
    st.markdown("#### 📈 Load Capacity Curve")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spans, y=w_moment, mode='lines', name='Moment Limit', line=dict(color='orange', dash='dot', width=1)))
    fig.add_trace(go.Scatter(x=spans, y=w_shear, mode='lines', name='Shear Limit', line=dict(color='red', dash='dot', width=1)))
    fig.add_trace(go.Scatter(x=spans, y=w_defl, mode='lines', name=f'Deflection Limit ({defl_ratio})', line=dict(color='green', dash='dot', width=1)))
    fig.add_trace(go.Scatter(x=spans, y=w_govern, mode='lines', name='Safe Load', line=dict(color='#2E86C1', width=3), fill='tozeroy', fillcolor='rgba(46, 134, 193, 0.1)'))
    
    # Add User Point
    fig.add_trace(go.Scatter(x=[user_span], y=[user_load], mode='markers', name='Your Design', marker=dict(color='black', size=12, symbol='x')))
    
    # Highlight Optimal
    fig.add_vrect(x0=opt_min_span, x1=opt_max_span, fillcolor="green", opacity=0.05, annotation_text="Optimal Span", annotation_position="top left")
    
    fig.update_layout(xaxis_title="Span Length (m)", yaxis_title="Uniform Load (kg/m)", height=500, hovermode="x unified", margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: SECTION DETAILS ---
with tab2:
    col_draw, col_prop = st.columns([1, 1])
    
    with col_draw:
        st.subheader("📐 Section Geometry")
        # Draw H-Beam Shape using Plotly Shapes
        # Dimensions in mm
        h_mm, b_mm, tw_mm, tf_mm = p['h'], p['b'], p['tw'], p['tf']
        
        # Coordinates for I-shape
        x_coords = [-b_mm/2, b_mm/2, b_mm/2, tw_mm/2, tw_mm/2, b_mm/2, b_mm/2, -b_mm/2, -b_mm/2, -tw_mm/2, -tw_mm/2, -b_mm/2, -b_mm/2]
        y_coords = [h_mm/2, h_mm/2, h_mm/2-tf_mm, h_mm/2-tf_mm, -h_mm/2+tf_mm, -h_mm/2+tf_mm, -h_mm/2, -h_mm/2, -h_mm/2+tf_mm, -h_mm/2+tf_mm, h_mm/2-tf_mm, h_mm/2-tf_mm, h_mm/2]
        
        fig_sec = go.Figure(go.Scatter(x=x_coords, y=y_coords, fill="toself", line=dict(color="#2c3e50"), name=sec_name))
        fig_sec.update_layout(
            showlegend=False, 
            plot_bgcolor='white',
            width=400, height=400,
            xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
            yaxis=dict(visible=False),
            annotations=[
                dict(x=0, y=0, text=sec_name, showarrow=False, font=dict(size=14, color='white'))
            ]
        )
        st.plotly_chart(fig_sec)

    with col_prop:
        st.subheader("📋 Properties & Constants")
        
        st.markdown(f"""
        | Property | Symbol | Value | Unit |
        | :--- | :---: | :---: | :---: |
        | Depth | $d$ | {p['h']} | mm |
        | Width | $b_f$ | {p['b']} | mm |
        | Web Thick | $t_w$ | {p['tw']} | mm |
        | Flange Thick | $t_f$ | {p['tf']} | mm |
        | Weight | $w$ | {p['w']} | kg/m |
        | Area (Web) | $A_w$ | {Aw:.2f} | cm² |
        | Moment of Inertia | $I_x$ | {Ix:,.0f} | cm⁴ |
        | Section Modulus | $Z_x$ | {Zx:,.0f} | cm³ |
        | Yield Strength | $F_y$ | {fy:,.0f} | ksc |
        """)
        
        st.info("💡 **Note:** Web area ($A_w$) calculation assumes simplified rectangular web ($d \\times t_w$) for shear capacity.")

# --- TAB 3: DATA TABLE ---
with tab3:
    st.subheader("💾 Data Table Export")
    
    # Create DataFrame
    df_res = pd.DataFrame({
        "Span (m)": spans,
        "Shear Limit (kg/m)": w_shear,
        "Moment Limit (kg/m)": w_moment,
        "Deflection Limit (kg/m)": w_defl,
        "Safe Load (kg/m)": w_govern,
        "Governing Case": govern_cause
    }).round(2)
    
    col_dl, col_blank = st.columns([1, 4])
    with col_dl:
        csv = df_res.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", data=csv, file_name=f'beam_capacity_{sec_name}.csv', mime='text/csv')
    
    st.dataframe(df_res, use_container_width=True, height=500)
