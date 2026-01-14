import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- IMPORT MODULES ---
import connection_design as conn
import report_generator as rep

# ==========================================
# 1. SETUP & STYLE
# ==========================================
st.set_page_config(page_title="Beam Insight V12", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600&family=Roboto+Mono:wght@500&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Sarabun', sans-serif; 
    }

    /* --- 1. Metric Card --- */
    .metric-card-clean {
        background: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        border: 1px solid #e0e0e0;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .mc-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
    .mc-title { font-weight: 600; color: #555; font-size: 16px; display: flex; gap: 8px; }
    .mc-percent { font-family: 'Roboto Mono', monospace; font-size: 26px; font-weight: 700; }

    .mc-values { 
        display: flex; justify-content: space-between; align-items: flex-end; 
        font-family: 'Roboto Mono', monospace; color: #333; margin-bottom: 8px; font-size: 14px;
    }
    .mc-label { font-size: 12px; color: #999; font-family: 'Sarabun'; margin-bottom: 2px; }

    .mc-bar-bg { background-color: #f0f0f0; height: 8px; border-radius: 4px; overflow: hidden; margin-bottom: 12px; }
    .mc-bar-fill { height: 100%; border-radius: 4px; }

    /* Footer: สมการเช็คความถูกต้อง (แก้ไขใหม่) */
    .mc-footer { 
        background-color: #fafafa; border-top: 1px solid #eee; 
        padding-top: 8px; margin-top: 5px;
        font-size: 13px; color: #555; text-align: center; 
        font-family: 'Roboto Mono', monospace;
        letter-spacing: -0.5px;
    }

    /* --- 2. Calculation Box --- */
    .calc-box {
        background-color: #fff;
        border: 1px solid #ddd;
        border-left-width: 5px;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .calc-title {
        font-weight: 600; color: #333; margin-bottom: 10px;
        border-bottom: 1px dotted #ccc; padding-bottom: 5px;
    }

    /* --- 3. Highlight Card --- */
    .highlight-card { 
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        padding: 25px; border-radius: 12px; border: 1px solid #ddd; border-left: 6px solid #2c3e50;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03); margin-bottom: 20px; 
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. INPUTS
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

with st.sidebar:
    st.title("Beam Insight V12")
    st.caption("Standard Edition")
    st.divider()
    
    st.header("1. Design Method")
    method = st.radio("Standard", ["ASD (Allowable Stress)", "LRFD (Limit State)"])
    is_lrfd = "LRFD" in method
    
    st.divider()
    st.header("2. Beam Settings")
    sec_name = st.selectbox("Select Section", list(steel_db.keys()), index=5)
    user_span = st.number_input("Span Length (m)", min_value=1.0, value=6.0, step=0.5)
    fy = st.number_input("Fy (ksc)", 2400)
    defl_ratio = st.selectbox("Defl. Limit", ["L/300", "L/360", "L/400"], index=1)
    
    st.divider()
    st.header("3. Connection Settings")
    bolt_size = st.selectbox("Bolt Size", ["M16", "M20", "M22", "M24"], index=1)
    design_mode = st.radio("Connection Design:", ["Actual Load (from Span)", "Fixed % Capacity"])
    
    if design_mode == "Fixed % Capacity":
        target_pct = st.slider("Target % Usage", 50, 100, 75, 5)
    else:
        target_pct = None

    E_mod = 2.04e6 
    defl_lim_val = int(defl_ratio.split("/")[1])

# ==========================================
# 3. CORE CALCULATION
# ==========================================
p = steel_db[sec_name]
h_cm, tw_cm = p['h']/10, p['tw']/10
Aw = h_cm * tw_cm
Ix, Zx = p['Ix'], p['Zx']

if is_lrfd:
    phi_b, phi_v = 0.90, 1.00
    M_cap = phi_b * fy * Zx
    V_cap = phi_v * 0.6 * fy * Aw
    label_load = "Factored Load (Wu)"
    label_cap_m = "Phi Mn"
    label_cap_v = "Phi Vn"
else:
    M_cap = 0.6 * fy * Zx
    V_cap = 0.4 * fy * Aw
    label_load = "Safe Load (w)"
    label_cap_m = "M allow"
    label_cap_v = "V allow"

def get_capacity(L_m):
    L_cm = L_m * 100
    w_s = (2 * V_cap) / L_cm * 100
    w_m = (8 * M_cap) / (L_cm**2) * 100
    w_d = ((L_cm/defl_lim_val) * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100
    w_gov = min(w_s, w_m, w_d)
    cause = "Shear" if w_gov == w_s else ("Moment" if w_gov == w_m else "Deflection")
    return w_s, w_m, w_d, w_gov, cause

w_shear, w_moment, w_defl, user_safe_load, user_cause = get_capacity(user_span)
V_actual = user_safe_load * user_span / 2
M_actual = user_safe_load * user_span**2 / 8
delta_actual = (5 * (user_safe_load/100) * ((user_span*100)**4)) / (384 * E_mod * Ix)
delta_allow = (user_span*100) / defl_lim_val

if design_mode == "Actual Load (from Span)":
    V_design = V_actual
else:
    V_design = V_cap * (target_pct / 100)

# ==========================================
# 4. UI DISPLAY
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Beam Analysis", "🔩 Connection Detail", "💾 Load Table", "📝 Calculation Report"])

with tab1:
    st.subheader(f"Capacity Analysis: {sec_name}")
    
    # --- 1. Highlight Card ---
    cause_color = "#27ae60" # Default Green
    if user_cause == "Moment": cause_color = "#f39c12" # Orange
    if user_cause == "Shear": cause_color = "#c0392b" # Red

    st.markdown(f"""
    <div class="highlight-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="color:#555;">Max {label_load}</span><br>
                <span style="font-size:38px; font-weight:bold; color:#2c3e50;">{user_safe_load:,.0f}</span> <span style="font-size:20px; color:#777;">kg/m</span>
            </div>
            <div style="text-align: right;">
                <span style="color:#555;">Control Factor</span><br>
                <span style="font-size: 20px; font-weight:bold; color:{cause_color}; background-color:rgba(0,0,0,0.05); padding: 5px 15px; border-radius:20px;">{user_cause}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- 2. Calculation Details ---
    with st.expander(f"🕵️‍♂️ ดูรายการคำนวณ (Calculation Details)", expanded=True):
        c1, c2, c3 = st.columns(3)
        L_cm_disp = user_span * 100
        
        with c1:
            st.markdown(f'<div class="calc-box" style="border-left-color: #27ae60;"><div class="calc-title">1. Shear Control</div>', unsafe_allow_html=True)
            st.latex(r''' w = \frac{2 \times V_{cap}}{L} \times 100 ''')
            st.latex(fr''' w = \frac{{2 \times {V_cap:,.0f}}}{{{L_cm_disp:,.0f}}} \times 100 ''')
            st.latex(fr''' w = \mathbf{{{w_shear:,.0f}}} \; kg/m ''')
            st.markdown("</div>", unsafe_allow_html=True)

        with c2:
            st.markdown(f'<div class="calc-box" style="border-left-color: #f39c12;"><div class="calc-title">2. Moment Control</div>', unsafe_allow_html=True)
            st.latex(r''' w = \frac{8 \times M_{cap}}{L^2} \times 100 ''')
            st.latex(fr''' w = \frac{{8 \times {M_cap:,.0f}}}{{{L_cm_disp:,.0f}^2}} \times 100 ''')
            st.latex(fr''' w = \mathbf{{{w_moment:,.0f}}} \; kg/m ''')
            st.markdown("</div>", unsafe_allow_html=True)

        with c3:
            st.markdown(f'<div class="calc-box" style="border-left-color: #2980b9;"><div class="calc-title">3. Deflection Control</div>', unsafe_allow_html=True)
            st.latex(r''' w = \frac{384 E I \Delta}{5 L^4} \times 100 ''')
            st.latex(fr''' w = \frac{{384 \times {E_mod:.2e} \times {Ix} \times {delta_allow:.2f}}}{{5 \times {L_cm_disp:,.0f}^4}} \times 100 ''')
            st.latex(fr''' w = \mathbf{{{w_defl:,.0f}}} \; kg/m ''')
            st.markdown("</div>", unsafe_allow_html=True)
            
    st.markdown("---")

    # --- 3. METRIC CARDS ---
    cm1, cm2, cm3 = st.columns(3)
    
    def create_card(icon, title, actual, limit, unit, color, decimal=0):
        pct = (actual / limit) * 100
        width_css = f"{min(pct, 100):.1f}"
        fmt_val = f",.{decimal}f"
        
        # Color Logic
        bar_color = color
        if pct > 100: bar_color = "#c0392b" # Red warning

        # FIXED: Footer now shows explicit percentage calculation: (A / B) * 100 = %
        return f"""
        <div class="metric-card-clean" style="border-top: 4px solid {bar_color};">
            <div class="mc-header">
                <div class="mc-title"><span>{icon}</span> {title}</div>
                <div class="mc-percent" style="color:{bar_color};">{pct:.1f}%</div>
            </div>
            
            <div class="mc-values">
                <div style="text-align:left;">
                    <div class="mc-label">ACTUAL</div>
                    <div><b>{actual:{fmt_val}}</b></div>
                </div>
                <div style="text-align:right;">
                    <div class="mc-label">LIMIT</div>
                    <div style="color:#888;">{limit:{fmt_val}} <small>{unit}</small></div>
                </div>
            </div>
            
            <div class="mc-bar-bg">
                <div class="mc-bar-fill" style="width:{width_css}%; background-color:{bar_color};"></div>
            </div>
            
            <div class="mc-footer">
                ({actual:{fmt_val}} / {limit:{fmt_val}}) × 100 = <b>{pct:.1f}%</b>
            </div>
        </div>
        """
    
    with cm1:
        st.markdown(create_card("✂️", "Shear (V)", V_actual, V_cap, "kg", "#27ae60"), unsafe_allow_html=True)
    with cm2:
        st.markdown(create_card("🔄", "Moment (M)", M_actual, M_cap/100, "kg.m", "#f39c12"), unsafe_allow_html=True)
    with cm3:
        st.markdown(create_card("📏", "Deflection", delta_actual, delta_allow, "cm", "#2980b9", decimal=2), unsafe_allow_html=True)

    # --- 4. Chart ---
    st.markdown("<br>", unsafe_allow_html=True)
    g_spans = np.linspace(2, 15, 100)
    g_data = [get_capacity(l) for l in g_spans]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=g_spans, y=[x[1] for x in g_data], mode='lines', name=f'{label_cap_m} Limit', line=dict(color='#f39c12', dash='dot')))
    fig.add_trace(go.Scatter(x=g_spans, y=[x[0] for x in g_data], mode='lines', name=f'{label_cap_v} Limit', line=dict(color='#27ae60', dash='dot')))
    fig.add_trace(go.Scatter(x=g_spans, y=[x[3] for x in g_data], mode='lines', name=f'Max {label_load}', line=dict(color='#2c3e50', width=3), fill='tozeroy', fillcolor='rgba(44, 62, 80, 0.1)'))
    fig.add_trace(go.Scatter(x=[user_span], y=[user_safe_load], mode='markers', 
                             marker=dict(color='#c0392b', size=14, symbol='star', line=dict(width=2, color='white')), 
                             name='Current Design'))
    
    fig.update_layout(
        title="Span vs Capacity Chart",
        xaxis_title="Span Length (m)",
        yaxis_title=f"Load Capacity (kg/m)",
        height=450, 
        margin=dict(t=40, b=40, l=60, r=40),
        plot_bgcolor='white',
        xaxis=dict(showgrid=True, gridcolor='#eee'),
        yaxis=dict(showgrid=True, gridcolor='#eee'),
        hovermode="x unified",
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right")
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    req_bolt_result, v_bolt_result = conn.render_connection_tab(V_design, bolt_size, method, is_lrfd, p)

with tab3:
    st.subheader("Reference Load Table")
    t_spans = np.arange(2, 15.5, 0.5)
    t_data = [get_capacity(l) for l in t_spans]
    df_res = pd.DataFrame({"Span (m)": t_spans, f"Max {label_load}": [x[3] for x in t_data], "Control": [x[4] for x in t_data]})
    st.dataframe(df_res.style.format("{:,.0f}", subset=[f"Max {label_load}"]), use_container_width=True)

with tab4:
    caps = {'M_cap': M_cap, 'V_cap': V_cap}
    bolt_info = {'size': bolt_size, 'capacity': v_bolt_result}
    rep.render_report_tab(method, is_lrfd, sec_name, fy, p, caps, bolt_info)
