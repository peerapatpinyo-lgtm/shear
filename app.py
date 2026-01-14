import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- IMPORT MODULES ---
import connection_design as conn
import report_generator as rep

# ==========================================
# 1. SETUP & STYLE (New CSS for Pro Dashboard)
# ==========================================
st.set_page_config(page_title="Beam Insight V12 (Modular)", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;800&family=Roboto+Mono:wght@500&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }

    /* --- Pro Card Style --- */
    .metric-card-pro {
        background: white;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        border: 1px solid #f0f2f5;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: transform 0.2s;
    }
    .metric-card-pro:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }

    /* Header */
    .pro-header {
        display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px;
    }
    .pro-title {
        font-size: 16px; font-weight: 700; color: #636e72; text-transform: uppercase; letter-spacing: 0.5px;
        display: flex; align-items: center; gap: 8px;
    }
    .pro-percent {
        font-size: 36px; font-weight: 800; line-height: 1;
    }

    /* Grid Layout for Values */
    .stat-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 15px;
        margin-bottom: 15px;
        padding: 12px;
        background: #f8f9fa;
        border-radius: 10px;
    }
    .stat-item { display: flex; flex-direction: column; }
    .stat-label { font-size: 12px; color: #999; margin-bottom: 2px; }
    .stat-value { font-size: 18px; font-weight: 700; color: #2d3436; }
    
    /* Progress Bar Styled */
    .bar-container {
        height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden; margin-bottom: 12px;
    }
    .bar-fill { height: 100%; border-radius: 4px; transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1); }

    /* Math Pill (Subtle Footer) */
    .math-pill {
        font-family: 'Roboto Mono', monospace;
        font-size: 11px;
        color: #b2bec3;
        text-align: right;
        background: #fff;
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 6px;
    }
    .math-pill span { background: #f1f2f6; padding: 2px 6px; border-radius: 4px; }

    /* --- Global Utils --- */
    .highlight-card { 
        background: linear-gradient(135deg, #ebf5fb 0%, #ffffff 100%);
        padding: 25px; border-radius: 12px; border-left: 6px solid #2e86c1; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 25px; 
    }
    .math-card {
        background-color: #fdfefe; border: 1px solid #e0e6e9; border-radius: 8px;
        padding: 15px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); height: 100%;
    }
    .math-header { font-weight: bold; color: #2e86c1; margin-bottom: 8px; border-bottom: 2px solid #f2f4f4; padding-bottom: 5px; }
    
    .report-paper { background-color: #ffffff; padding: 40px; border: 1px solid #e5e7e9; box-shadow: 0 10px 30px rgba(0,0,0,0.08); border-radius: 2px; max-width: 900px; margin: auto; }
    .report-header { font-size: 20px; font-weight: 800; color: #1a5276; margin-top: 25px; border-bottom: 2px solid #a9cce3; padding-bottom: 8px; }
    .report-line { font-family: 'Courier New', monospace; font-size: 16px; margin-bottom: 8px; color: #2c3e50; border-bottom: 1px dotted #eee; }
    .conn-card { background-color: #fffbf0; padding: 20px; border-radius: 10px; border-left: 6px solid #f1c40f; box-shadow: 0 2px 5px rgba(0,0,0,0.02); }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. INPUTS (Logic เดิม)
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
    st.caption("Modular Edition (Pro UI)")
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
    cause_color = "#e74c3c" if user_cause == "Shear" else ("#f39c12" if user_cause == "Moment" else "#27ae60")
    
    # --- 1. Main Card ---
    st.markdown(f"""
    <div class="highlight-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span class="sub-text" style="color:#2874a6;">Max {label_load}</span><br>
                <span class="big-num" style="color:#2874a6; font-size:38px;">{user_safe_load:,.0f}</span> <span style="font-size:20px; color:#555;">kg/m</span>
            </div>
            <div style="text-align: right;">
                <span class="sub-text">Control Factor</span><br>
                <span style="font-size: 22px; font-weight:bold; color:{cause_color}; background-color:rgba(0,0,0,0.05); padding: 5px 15px; border-radius:20px;">{user_cause}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- 2. Logic Source (Math Card Style) ---
    with st.expander(f"🕵️‍♂️ ดูที่มาการคำนวณแบบละเอียด (Calculations)", expanded=False):
        c_cal1, c_cal2, c_cal3 = st.columns(3)
        L_cm_disp = user_span * 100
        
        with c_cal1:
            st.markdown(f'<div class="math-card"><div class="math-header">1. Shear Control</div>', unsafe_allow_html=True)
            st.latex(fr''' w = \frac{{2 \times {V_cap:,.0f}}}{{{L_cm_disp:.0f}}} \times 100 = \mathbf{{{w_shear:,.0f}}} ''')
            st.markdown("</div>", unsafe_allow_html=True)

        with c_cal2:
            st.markdown(f'<div class="math-card"><div class="math-header">2. Moment Control</div>', unsafe_allow_html=True)
            st.latex(fr''' w = \frac{{8 \times {M_cap:,.0f}}}{{{L_cm_disp:.0f}^2}} \times 100 = \mathbf{{{w_moment:,.0f}}} ''')
            st.markdown("</div>", unsafe_allow_html=True)

        with c_cal3:
            st.markdown(f'<div class="math-card"><div class="math-header">3. Deflection</div>', unsafe_allow_html=True)
            st.latex(fr''' w = \frac{{384 \cdot {E_mod:.2e} \cdot {Ix} \cdot {delta_allow:.1f}}}{{5 \cdot {L_cm_disp:.0f}^4}} \times 100 = \mathbf{{{w_defl:,.0f}}} ''')
            st.markdown("</div>", unsafe_allow_html=True)
            
    st.markdown("---")

    # --- 3. PRO METRICS (The Fix) ---
    cm1, cm2, cm3 = st.columns(3)
    
    def create_pro_card(icon, title, actual, limit, unit, color_base, decimal=0):
        # 1. Logic
        pct = (actual / limit) * 100
        bar_width = min(pct, 100)
        # Gradient effect for bar
        bar_gradient = f"linear-gradient(90deg, {color_base} 0%, {color_base}dd 100%)"
        if pct > 100:
             bar_gradient = "linear-gradient(90deg, #e74c3c 0%, #c0392b 100%)"
             color_text = "#e74c3c"
        else:
             color_text = color_base
             
        fmt = f",.{decimal}f"
        
        return f"""
        <div class="metric-card-pro" style="border-top: 5px solid {color_text};">
            <div class="pro-header">
                <div class="pro-title">
                    <span>{icon}</span> {title}
                </div>
                <div class="pro-percent" style="color:{color_text};">
                    {pct:.1f}<small style="font-size:18px;">%</small>
                </div>
            </div>
            
            <div class="stat-grid">
                <div class="stat-item">
                    <span class="stat-label">Actual Load</span>
                    <span class="stat-value">{actual:{fmt}}</span>
                </div>
                <div class="stat-item" style="align-items: flex-end;">
                    <span class="stat-label">Capacity (Limit)</span>
                    <span class="stat-value" style="color:#aaa;">{limit:{fmt}}</span>
                </div>
            </div>
            
            <div class="bar-container">
                <div class="bar-fill" style="width:{bar_width}%; background:{bar_gradient};"></div>
            </div>
            
            <div class="math-pill">
                <span>Check:</span> {actual:{fmt}} / {limit:{fmt}} <small>{unit}</small>
            </div>
        </div>
        """
    
    # 3.1 Shear
    with cm1:
        st.markdown(create_pro_card("✂️", "Shear (V)", V_actual, V_cap, "kg", "#2ecc71"), unsafe_allow_html=True)
        
    # 3.2 Moment
    with cm2:
        st.markdown(create_pro_card("🔄", "Moment (M)", M_actual, M_cap/100, "kg.m", "#f1c40f"), unsafe_allow_html=True)
        
    # 3.3 Deflection
    with cm3:
        st.markdown(create_pro_card("📏", "Deflection", delta_actual, delta_allow, "cm", "#3498db", decimal=2), unsafe_allow_html=True)

    # --- 4. Graph ---
    st.markdown("<br>", unsafe_allow_html=True)
    g_spans = np.linspace(2, 15, 100)
    g_data = [get_capacity(l) for l in g_spans]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=g_spans, y=[x[1] for x in g_data], mode='lines', name=f'{label_cap_m} Limit', line=dict(color='#f39c12', dash='dot')))
    fig.add_trace(go.Scatter(x=g_spans, y=[x[0] for x in g_data], mode='lines', name=f'{label_cap_v} Limit', line=dict(color='#27ae60', dash='dot')))
    fig.add_trace(go.Scatter(x=g_spans, y=[x[3] for x in g_data], mode='lines', name=f'Max {label_load}', line=dict(color='#2E86C1', width=3), fill='tozeroy', fillcolor='rgba(46, 134, 193, 0.1)'))
    fig.add_trace(go.Scatter(x=[user_span], y=[user_safe_load], mode='markers', 
                             marker=dict(color='#17202a', size=14, symbol='star', line=dict(width=2, color='white')), 
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
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
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
