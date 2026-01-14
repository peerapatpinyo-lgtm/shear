import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- IMPORT MODULES ---
try:
    import connection_design as conn
    import report_generator as rep
except ImportError:
    pass # ข้ามถ้ายังไม่ได้ต่อไฟล์ภายนอก

# ==========================================
# 1. SETUP & STYLE
# ==========================================
st.set_page_config(page_title="Beam Insight V12", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=Roboto+Mono:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
    
    .metric-card-final {
        background: white; border-radius: 16px; padding: 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05); border: 1px solid #f0f2f6;
        height: 100%; display: flex; flex-direction: column; justify-content: space-between;
    }
    .m-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
    .m-percent { font-family: 'Roboto Mono', monospace; font-size: 28px; font-weight: 700; }
    .m-bar-bg { background-color: #f3f4f6; height: 10px; border-radius: 5px; overflow: hidden; margin-bottom: 16px; }
    .m-bar-fill { height: 100%; border-radius: 5px; transition: width 0.8s ease; }
    .m-check { background-color: #f9fafb; border-radius: 8px; padding: 8px; font-size: 13px; color: #4b5563; text-align: center; border: 1px solid #f3f4f6; font-family: 'Roboto Mono', monospace; }
    
    .highlight-card { 
        background: linear-gradient(135deg, #ffffff 0%, #f8faff 100%);
        padding: 30px; border-radius: 20px; border-left: 8px solid #2563eb; 
        box-shadow: 0 10px 30px rgba(37, 99, 235, 0.08); margin-bottom: 30px; border: 1px solid #e5e7eb;
    }
    .calc-box {
        background-color: #fcfcfc; border: 1px solid #e5e7eb; border-top: 4px solid #374151;
        padding: 20px; margin-bottom: 15px; border-radius: 12px; min-height: 220px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA
# ==========================================
steel_db = {
    "H 150x75x5x7":     {"h": 150, "b": 75,  "tw": 5,   "tf": 7,   "Ix": 666,    "Zx": 88.8},
    "H 200x100x5.5x8":  {"h": 200, "b": 100, "tw": 5.5, "tf": 8,   "Ix": 1840,   "Zx": 184},
    "H 250x125x6x9":    {"h": 250, "b": 125, "tw": 6,   "tf": 9,   "Ix": 3690,   "Zx": 295},
    "H 300x150x6.5x9":  {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481},
    "H 350x175x7x11":   {"h": 350, "b": 175, "tw": 7,   "tf": 11,  "Ix": 13600,  "Zx": 775},
    "H 400x200x8x13":   {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190},
    "H 450x200x9x14":   {"h": 450, "b": 200, "tw": 9,   "tf": 14,  "Ix": 33500,  "Zx": 1490},
    "H 500x200x10x16":  {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910},
    "H 600x200x11x17":  {"h": 600, "b": 200, "tw": 11,  "tf": 17,  "Ix": 77600,  "Zx": 2590},
}

with st.sidebar:
    st.header("1. Input Parameters")
    method = st.radio("Method", ["ASD", "LRFD"])
    is_lrfd = method == "LRFD"
    sec_name = st.selectbox("Steel Section", list(steel_db.keys()), index=5)
    user_span = st.number_input("Span (m)", 1.0, 20.0, 6.0)
    fy = st.number_input("Fy (ksc)", 2400)
    defl_limit = st.selectbox("Deflection Limit", ["L/300", "L/360", "L/400"], index=1)
    defl_div = int(defl_limit.split("/")[1])
    
    st.divider()
    bolt_size = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)

# ==========================================
# 3. CORE LOGIC
# ==========================================
p = steel_db[sec_name]
Ix, Zx = p['Ix'], p['Zx']
Aw = (p['h']/10) * (p['tw']/10)
E = 2.04e6

if is_lrfd:
    M_cap, V_cap = 0.9 * fy * Zx, 1.0 * 0.6 * fy * Aw
    label_load = "Factored Load (Wu)"
else:
    M_cap, V_cap = 0.6 * fy * Zx, 0.4 * fy * Aw
    label_load = "Safe Load (w)"

def get_capacity(L_m):
    L_c = L_m * 100
    ws = (2 * V_cap / L_c) * 100
    wm = (8 * M_cap / (L_c**2)) * 100
    wd = ((L_c/defl_div) * 384 * E * Ix) / (5 * (L_c**4)) * 100
    w_gov = min(ws, wm, wd)
    cause = "Shear" if w_gov == ws else ("Moment" if w_gov == wm else "Deflection")
    return ws, wm, wd, w_gov, cause

w_s, w_m, w_d, w_final, gov = get_capacity(user_span)

# ==========================================
# 4. TAB 1 DISPLAY
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Beam Analysis", "🔩 Connection", "💾 Data", "📝 Report"])

with tab1:
    # 1. Highlight Card
    st.markdown(f"""<div class="highlight-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div><small>Maximum {label_load}</small><h2>{w_final:,.0f} kg/m</h2></div>
            <div style="text-align:right;"><small>Controlled By</small><h3 style="color:#2563eb;">{gov}</h3></div>
        </div>
    </div>""", unsafe_allow_html=True)

    # 2. รายการคำนวณ (Calculation Details)
    with st.expander("📝 Calculation Steps (Demand / Capacity Check)", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown('<div class="calc-box"><b>1. Shear Limit</b>', unsafe_allow_html=True)
            st.latex(fr"w_v = \frac{{2 \cdot {V_cap:,.0f}}}{{{user_span*100:,.0f}}} \cdot 100 = {w_s:,.0f}")
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="calc-box"><b>2. Moment Limit</b>', unsafe_allow_html=True)
            st.latex(fr"w_m = \frac{{8 \cdot {M_cap:,.0f}}}{{{user_span*100:,.0f}^2}} \cdot 100 = {w_m:,.0f}")
            st.markdown('</div>', unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="calc-box"><b>3. Deflection Limit</b>', unsafe_allow_html=True)
            st.latex(fr"w_d = \frac{{384 \cdot E \cdot I \cdot \Delta}}{{5 \cdot L^4}} = {w_d:,.0f}")
            st.markdown('</div>', unsafe_allow_html=True)

    # 3. THE GRAPH (FULL RESTORE)
    st.markdown("### Load Capacity Chart")
    x_range = np.linspace(2, 12, 100)
    y_data = [get_capacity(x) for x in x_range]
    
    fig = go.Figure()
    # เส้นขีดจำกัดแต่ละด้าน
    fig.add_trace(go.Scatter(x=x_range, y=[y[0] for y in y_data], name='Shear Limit', line=dict(color='#10b981', dash='dash')))
    fig.add_trace(go.Scatter(x=x_range, y=[y[1] for y in y_data], name='Moment Limit', line=dict(color='#f59e0b', dash='dash')))
    fig.add_trace(go.Scatter(x=x_range, y=[y[2] for y in y_data], name='Deflection Limit', line=dict(color='#3b82f6', dash='dash')))
    # เส้น Capacity รวม (พื้นที่ระบายสี)
    fig.add_trace(go.Scatter(x=x_range, y=[y[3] for y in y_data], name='Overall Capacity', 
                             fill='tozeroy', fillcolor='rgba(37, 99, 235, 0.1)',
                             line=dict(color='#1e293b', width=4)))
    # จุดปัจจุบัน
    fig.add_trace(go.Scatter(x=[user_span], y=[w_final], mode='markers+text', 
                             text=[f"  {w_final:,.0f} kg/m"], textposition="top right",
                             marker=dict(size=12, color='red', symbol='diamond'), name='Current Span'))

    fig.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(title="Span Length (m)", showgrid=True, gridcolor='#f0f0f0'),
        yaxis=dict(title="Load Capacity (kg/m)", showgrid=True, gridcolor='#f0f0f0'),
        plot_bgcolor='white', height=500
    )
    st.plotly_chart(fig, use_container_width=True)

    # 4. Metrics
    m1, m2, m3 = st.columns(3)
    # ... (ส่วน Metric Card เดิมของคุณ) ...
