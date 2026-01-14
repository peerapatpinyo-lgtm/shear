import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- IMPORT MODULES ---
try:
    import connection_design as conn
    import report_generator as rep
except ImportError:
    st.warning("Warning: connection_design.py or report_generator.py not found. Some tabs may not work.")

# ==========================================
# 1. SETUP & STYLE (Engineering Professional)
# ==========================================
st.set_page_config(page_title="Beam Insight V12", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=Roboto+Mono:wght@400;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }

    /* --- Metric Card --- */
    .metric-card-final {
        background: white; border-radius: 16px; padding: 22px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05); border: 1px solid #f0f2f6;
        height: 100%; display: flex; flex-direction: column; justify-content: space-between;
    }
    .m-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
    .m-title { font-weight: 700; color: #4b5563; font-size: 15px; display: flex; align-items: center; gap: 8px; }
    .m-percent { font-family: 'Roboto Mono', monospace; font-size: 26px; font-weight: 700; }
    .m-bar-bg { background-color: #f3f4f6; height: 10px; border-radius: 5px; overflow: hidden; margin-bottom: 12px; }
    .m-bar-fill { height: 100%; border-radius: 5px; transition: width 0.8s ease; }
    .m-values { display: flex; justify-content: space-between; align-items: flex-end; font-family: 'Roboto Mono', monospace; font-size: 14px; color: #1f2937; margin-bottom: 8px; }
    .val-label { font-size: 11px; color: #9ca3af; font-weight: 600; text-transform: uppercase; }
    .m-check { background-color: #f9fafb; border-radius: 8px; padding: 8px; font-size: 12px; color: #4b5563; text-align: center; border: 1px solid #f3f4f6; font-family: 'Roboto Mono', monospace; }

    /* --- Highlight Card --- */
    .highlight-card { 
        background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%);
        padding: 25px; border-radius: 20px; border-left: 8px solid #2563eb; 
        box-shadow: 0 10px 30px rgba(37, 99, 235, 0.08); margin-bottom: 25px; border: 1px solid #e5e7eb;
    }
    .big-num { color: #1e40af; font-size: 42px; font-weight: 800; font-family: 'Roboto Mono', monospace; }
    .sub-text { color: #6b7280; font-size: 14px; font-weight: 600; text-transform: uppercase; }

    /* --- Calculation Box --- */
    .calc-box {
        background-color: #fcfcfc; border: 1px solid #e5e7eb; border-top: 4px solid #374151;
        padding: 18px; margin-bottom: 10px; border-radius: 12px; min-height: 200px;
    }
    .calc-title { font-weight: 700; color: #111827; margin-bottom: 10px; font-size: 16px; border-bottom: 1px solid #eee; padding-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. FULL DATA (ตารางเหล็กครบถ้วน)
# ==========================================
steel_db = {
    "H 100x100x6x8":    {"h": 100, "b": 100, "tw": 6,   "tf": 8,   "Ix": 383,    "Zx": 76.5,  "w": 17.2},
    "H 125x125x6.5x9":  {"h": 125, "b": 125, "tw": 6.5, "tf": 9,   "Ix": 847,    "Zx": 136,   "w": 23.8},
    "H 150x75x5x7":     {"h": 150, "b": 75,  "tw": 5,   "tf": 7,   "Ix": 666,    "Zx": 88.8,  "w": 14.0},
    "H 150x150x7x10":   {"h": 150, "b": 150, "tw": 7,   "tf": 10,  "Ix": 1640,   "Zx": 219,   "w": 31.5},
    "H 200x100x5.5x8":  {"h": 200, "b": 100, "tw": 5.5, "tf": 8,   "Ix": 1840,   "Zx": 184,   "w": 21.3},
    "H 200x200x8x12":   {"h": 200, "b": 200, "tw": 8,   "tf": 12,  "Ix": 4720,   "Zx": 472,   "w": 49.9},
    "H 250x125x6x9":    {"h": 250, "b": 125, "tw": 6,   "tf": 9,   "Ix": 3690,   "Zx": 295,   "w": 29.6},
    "H 250x250x9x14":   {"h": 250, "b": 250, "tw": 9,   "tf": 14,  "Ix": 10800,  "Zx": 867,   "w": 72.4},
    "H 300x150x6.5x9":  {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481,   "w": 36.7},
    "H 300x300x10x15":  {"h": 300, "b": 300, "tw": 10,  "tf": 15,  "Ix": 20400,  "Zx": 1360,  "w": 94.0},
    "H 350x175x7x11":   {"h": 350, "b": 175, "tw": 7,   "tf": 11,  "Ix": 13600,  "Zx": 775,   "w": 49.6},
    "H 400x200x8x13":   {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190,  "w": 66.0},
    "H 450x200x9x14":   {"h": 450, "b": 200, "tw": 9,   "tf": 14,  "Ix": 33500,  "Zx": 1490,  "w": 76.0},
    "H 500x200x10x16":  {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910,  "w": 89.6},
    "H 600x200x11x17":  {"h": 600, "b": 200, "tw": 11,  "tf": 17,  "Ix": 77600,  "Zx": 2590,  "w": 106},
}

with st.sidebar:
    st.title("🏗️ Beam Insight V12")
    st.divider()
    
    st.header("1. Design Standard")
    method = st.radio("Method", ["ASD (Allowable Stress)", "LRFD (Limit State)"])
    is_lrfd = method == "LRFD"
    
    st.divider()
    st.header("2. Geometry & Material")
    sec_name = st.selectbox("Steel Section", list(steel_db.keys()), index=11)
    user_span = st.number_input("Span Length (m)", min_value=1.0, value=6.0, step=0.5)
    fy = st.number_input("Fy (kg/cm²)", 2400)
    defl_ratio = st.selectbox("Deflection Limit", ["L/300", "L/360", "L/400"], index=1)
    defl_lim_val = int(defl_ratio.split("/")[1])
    
    st.divider()
    st.header("3. Connection Settings")
    bolt_size = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)
    design_mode = st.radio("Load for Connection:", ["Actual Load", "Fixed % Capacity"])
    target_pct = st.slider("Target Usage %", 50, 100, 75) if design_mode == "Fixed % Capacity" else None

    E_mod = 2.04e6 

# ==========================================
# 3. CORE CALCULATIONS
# ==========================================
p = steel_db[sec_name]
Aw = (p['h']/10) * (p['tw']/10) # cm²
Ix, Zx = p['Ix'], p['Zx']

if is_lrfd:
    M_cap = 0.9 * fy * Zx
    V_cap = 1.0 * 0.6 * fy * Aw
    label_load = "Factored Load (Wu)"
else:
    M_cap = 0.6 * fy * Zx
    V_cap = 0.4 * fy * Aw
    label_load = "Safe Load (w)"

def get_capacity(L_m):
    L_cm = L_m * 100
    w_v = (2 * V_cap / L_cm) * 100 # kg/m
    w_m = (8 * M_cap / (L_cm**2)) * 100 # kg/m
    w_d = ((L_cm/defl_lim_val) * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100 # kg/m
    w_gov = min(w_v, w_m, w_d)
    cause = "Shear" if w_gov == w_v else ("Moment" if w_gov == w_m else "Deflection")
    return w_v, w_m, w_d, w_gov, cause

w_shear, w_moment, w_defl, user_safe_load, user_cause = get_capacity(user_span)

# Actual values based on the safe load found
V_actual = user_safe_load * user_span / 2
M_actual = user_safe_load * user_span**2 / 8
delta_actual = (5 * (user_safe_load/100) * ((user_span*100)**4)) / (384 * E_mod * Ix)
delta_allow = (user_span*100) / defl_lim_val

V_design = V_actual if design_mode == "Actual Load" else V_cap * (target_pct / 100)

# ==========================================
# 4. UI RENDERING
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Beam Analysis", "🔩 Connection Detail", "💾 Load Table", "📝 Report"])

with tab1:
    st.subheader(f"Engineering Analysis: {sec_name}")
    cause_color = "#dc2626" if user_cause == "Shear" else ("#d97706" if user_cause == "Moment" else "#059669")

    # --- 1. Main Highlight Card ---
    st.markdown(f"""
    <div class="highlight-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span class="sub-text">Maximum {label_load}</span><br>
                <span class="big-num">{user_safe_load:,.0f}</span> <span style="font-size:20px; color:#4b5563;">kg/m</span>
            </div>
            <div style="text-align: right;">
                <span class="sub-text">Governing Limit</span><br>
                <span style="font-size: 22px; font-weight:bold; color:{cause_color}; background-color:{cause_color}15; padding: 8px 20px; border-radius:15px; border: 1px solid {cause_color}30;">
                    {user_cause.upper()}
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- 2. Calculation Steps ---
    with st.expander("🕵️‍♂️ View Calculation Steps (Detailed Verification)", expanded=True):
        c1, c2, c3 = st.columns(3)
        L_cm_disp = user_span * 100
        
        with c1:
            st.markdown(f'<div class="calc-box"><div class="calc-title">1. Shear Limit</div>', unsafe_allow_html=True)
            st.latex(r"w = \frac{2 \cdot V_{cap}}{L} \cdot 100")
            st.latex(fr"w = \frac{{2 \cdot {V_cap:,.0f}}}{{{L_cm_disp:,.0f}}} \cdot 100")
            st.latex(fr"= \mathbf{{{w_shear:,.0f}}} \; kg/m")
            st.markdown("</div>", unsafe_allow_html=True)

        with c2:
            st.markdown(f'<div class="calc-box" style="border-top-color:#f59e0b;"><div class="calc-title">2. Moment Limit</div>', unsafe_allow_html=True)
            st.latex(r"w = \frac{8 \cdot M_{cap}}{L^2} \cdot 100")
            st.latex(fr"w = \frac{{8 \cdot {M_cap:,.0f}}}{{{L_cm_disp:,.0f}^2}} \cdot 100")
            st.latex(fr"= \mathbf{{{w_moment:,.0f}}} \; kg/m")
            st.markdown("</div>", unsafe_allow_html=True)

        with c3:
            st.markdown(f'<div class="calc-box" style="border-top-color:#10b981;"><div class="calc-title">3. Deflection Limit</div>', unsafe_allow_html=True)
            st.latex(r"w = \frac{384 E I \Delta}{5 L^4} \cdot 100")
            st.latex(fr"w = \frac{{384 \cdot 2.04e6 \cdot {Ix} \cdot {delta_allow:.2f}}}{{5 \cdot {L_cm_disp:,.0f}^4}} \cdot 100")
            st.latex(fr"= \mathbf{{{w_defl:,.0f}}} \; kg/m")
            st.markdown("</div>", unsafe_allow_html=True)

    # --- 3. Capacity Graphic Graph ---
    st.markdown("### Capacity vs Span Curve")
    spans = np.linspace(2, 12, 100)
    data = [get_capacity(s) for s in spans]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spans, y=[d[0] for d in data], name='Shear Limit', line=dict(color='#ef4444', dash='dash')))
    fig.add_trace(go.Scatter(x=spans, y=[d[1] for d in data], name='Moment Limit', line=dict(color='#f59e0b', dash='dash')))
    fig.add_trace(go.Scatter(x=spans, y=[d[2] for d in data], name='Deflection Limit', line=dict(color='#3b82f6', dash='dash')))
    fig.add_trace(go.Scatter(x=spans, y=[d[3] for d in data], name='Safe Envelope', fill='tozeroy', fillcolor='rgba(37, 99, 235, 0.1)', line=dict(color='#1e40af', width=4)))
    fig.add_trace(go.Scatter(x=[user_span], y=[user_safe_load], mode='markers+text', text=[f"  Current: {user_safe_load:,.0f} kg/m"], textposition="top right", marker=dict(size=12, color='black', symbol='diamond'), name='Design Point'))
    
    fig.update_layout(hovermode="x unified", height=450, margin=dict(t=20, b=20, l=20, r=20), plot_bgcolor='white', xaxis=dict(showgrid=True, gridcolor='#f3f4f6'), yaxis=dict(showgrid=True, gridcolor='#f3f4f6'))
    st.plotly_chart(fig, use_container_width=True)

    # --- 4. Metric Cards ---
    st.markdown("### Check Ratio Summary")
    cm1, cm2, cm3 = st.columns(3)
    
    def draw_card(icon, title, act, lim, unit, color, dec=0):
        pct = (act/lim)*100
        return f"""
        <div class="metric-card-final" style="border-top: 5px solid {color};">
            <div class="m-header"><div class="m-title">{icon} {title}</div><div class="m-percent" style="color:{color};">{pct:.1f}%</div></div>
            <div class="m-values">
                <div><div class="val-label">ACTUAL</div><b>{act:,.{dec}f}</b></div>
                <div style="text-align:right;"><div class="val-label">LIMIT ({unit})</div><b>{lim:,.{dec}f}</b></div>
            </div>
            <div class="m-bar-bg"><div class="m-bar-fill" style="width:{min(pct, 100):.1f}%; background:{color};"></div></div>
            <div class="m-check">{act:,.{dec}f} ÷ {lim:,.{dec}f} = {pct:.1f}%</div>
        </div>"""
    
    with cm1: st.markdown(draw_card("🛡️", "Shear (V)", V_actual, V_cap, "kg", "#10b981"), unsafe_allow_html=True)
    with cm2: st.markdown(draw_card("🔄", "Moment (M)", M_actual, M_cap/100, "kg.m", "#f59e0b"), unsafe_allow_html=True)
    with cm3: st.markdown(draw_card("📏", "Deflection", delta_actual, delta_allow, "cm", "#3b82f6", 2), unsafe_allow_html=True)

with tab2:
    try:
        conn.render_connection_tab(V_design, bolt_size, method, is_lrfd, p)
    except:
        st.info("Connection module is being updated...")

with tab3:
    st.subheader("Span-Load Reference Table")
    tbl_spans = np.arange(2.0, 12.5, 0.5)
    tbl_data = [get_capacity(s) for s in tbl_spans]
    df = pd.DataFrame({
        "Span (m)": tbl_spans,
        f"Max {label_load} (kg/m)": [d[3] for d in tbl_data],
        "Control Factor": [d[4] for d in tbl_data]
    })
    st.dataframe(df.style.format("{:,.0f}", subset=[f"Max {label_load} (kg/m)"]), use_container_width=True)

with tab4:
    try:
        caps = {'M_cap': M_cap, 'V_cap': V_cap}
        rep.render_report_tab(method, is_lrfd, sec_name, fy, p, caps, {'size': bolt_size, 'capacity': 0})
    except:
        st.info("Report generator is being updated...")
