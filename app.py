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
st.set_page_config(page_title="Beam Insight V12 (Modular)", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }

    /* Highlight Card */
    .highlight-card { 
        background: linear-gradient(135deg, #ebf5fb 0%, #ffffff 100%);
        padding: 25px; border-radius: 12px; border-left: 6px solid #2e86c1; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 25px; 
    }

    /* Metric Box */
    .metric-box { 
        text-align: center; padding: 15px; background: white; 
        border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); 
        border-top: 5px solid #ccc; height: 100%;
    }
    .metric-title { font-size: 16px; font-weight: 700; color: #555; margin-bottom: 5px; text-transform: uppercase; }
    .metric-value { font-size: 24px; font-weight: 800; color: #2c3e50; }
    .metric-sub { font-size: 13px; color: #7f8c8d; margin-top: 5px; font-family: 'Courier New', monospace; }
    .metric-badge { 
        display: inline-block; padding: 2px 8px; border-radius: 4px; 
        font-size: 12px; font-weight: bold; margin-top: 5px;
    }
    
    /* Math/Calc Box Style */
    .math-card {
        background-color: #fdfefe;
        border: 1px solid #e0e6e9;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    .math-header {
        font-weight: bold;
        color: #2e86c1;
        margin-bottom: 8px;
        border-bottom: 2px solid #f2f4f4;
        padding-bottom: 5px;
    }
    .math-desc {
        font-size: 0.9em;
        color: #666;
        margin-bottom: 5px;
    }

    /* Report & Connection Styles */
    .report-paper { background-color: #ffffff; padding: 40px; border: 1px solid #e5e7e9; box-shadow: 0 10px 30px rgba(0,0,0,0.08); border-radius: 2px; max-width: 900px; margin: auto; }
    .report-header { font-size: 20px; font-weight: 800; color: #1a5276; margin-top: 25px; border-bottom: 2px solid #a9cce3; padding-bottom: 8px; }
    .report-line { font-family: 'Courier New', monospace; font-size: 16px; margin-bottom: 8px; color: #2c3e50; border-bottom: 1px dotted #eee; }
    .conn-card { background-color: #fffbf0; padding: 20px; border-radius: 10px; border-left: 6px solid #f1c40f; box-shadow: 0 2px 5px rgba(0,0,0,0.02); }
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
    st.caption("Modular Edition")
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

    # --- 2. Logic Source (Detailed Math) ---
    with st.expander(f"🕵️‍♂️ ดูที่มาการคำนวณแบบละเอียด (Show Calculations)", expanded=False):
        st.caption("สมการหาค่าน้ำหนักบรรทุกปลอดภัย (w) ในหน่วย kg/m จากเงื่อนไขต่างๆ:")
        
        c_cal1, c_cal2, c_cal3 = st.columns(3)
        
        # Prepare Values for LaTeX
        L_cm_disp = user_span * 100
        
        with c_cal1:
            st.markdown(f'<div class="math-card"><div class="math-header">1. Shear Control ({label_cap_v})</div>', unsafe_allow_html=True)
            st.markdown(f"Cap = {V_cap:,.0f} kg")
            # Math Latex
            st.latex(r''' w = \frac{2 \times V_{cap}}{L} \times 100 ''')
            st.latex(fr''' w = \frac{{2 \times {V_cap:,.0f}}}{{{L_cm_disp:.0f}}} \times 100 ''')
            st.markdown(f"<div style='text-align:center; font-weight:bold; color:#e74c3c;'>= {w_shear:,.0f} kg/m</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with c_cal2:
            st.markdown(f'<div class="math-card"><div class="math-header">2. Moment Control ({label_cap_m})</div>', unsafe_allow_html=True)
            st.markdown(f"Cap = {M_cap:,.0f} kg.cm")
            # Math Latex
            st.latex(r''' w = \frac{8 \times M_{cap}}{L^2} \times 100 ''')
            st.latex(fr''' w = \frac{{8 \times {M_cap:,.0f}}}{{{L_cm_disp:.0f}^2}} \times 100 ''')
            st.markdown(f"<div style='text-align:center; font-weight:bold; color:#f39c12;'>= {w_moment:,.0f} kg/m</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with c_cal3:
            st.markdown(f'<div class="math-card"><div class="math-header">3. Deflection (L/{defl_lim_val})</div>', unsafe_allow_html=True)
            st.markdown(f"Allow = {delta_allow:.2f} cm (Ix={Ix})")
            # Math Latex
            st.latex(r''' w = \frac{384 E I \Delta}{5 L^4} \times 100 ''')
            st.latex(fr''' w = \frac{{384 \cdot {E_mod:.2e} \cdot {Ix} \cdot {delta_allow:.1f}}}{{5 \cdot {L_cm_disp:.0f}^4}} \times 100 ''')
            st.markdown(f"<div style='text-align:center; font-weight:bold; color:#27ae60;'>= {w_defl:,.0f} kg/m</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        st.info(f"💡 หมายเหตุ: การคูณ 100 ในสูตร คือการแปลงหน่วยจาก kg/cm ให้เป็น kg/m เพื่อให้ง่ายต่อการใช้งาน (L ใช้หน่วย cm ในการคำนวณ)")

    st.markdown("---")

    # --- 3. Metrics (Complete Data) ---
    cm1, cm2, cm3 = st.columns(3)
    
    # Shear Box
    v_pct = V_actual/V_cap*100
    v_bg = "#fadbd8" if v_pct > 100 else "#eafaf1"
    v_txt = "#943126" if v_pct > 100 else "#1e8449"
    with cm1: 
        st.markdown(f"""
        <div class="metric-box" style="border-top-color: #e74c3c; background-color: {v_bg};">
            <div class="metric-title">Shear (V)</div>
            <div class="metric-value" style="color:{v_txt}">{V_actual:,.0f} <small>kg</small></div>
            <div class="metric-sub">Limit: {V_cap:,.0f} kg</div>
            <div class="metric-badge" style="background-color:rgba(0,0,0,0.1); color:{v_txt};">Usage: {v_pct:.0f}%</div>
        </div>""", unsafe_allow_html=True)
    
    # Moment Box
    m_pct = M_actual*100/M_cap*100
    m_bg = "#fdebd0" if m_pct > 100 else "#eafaf1"
    m_txt = "#b9770e" if m_pct > 100 else "#1e8449"
    with cm2: 
        st.markdown(f"""
        <div class="metric-box" style="border-top-color: #f39c12; background-color: {m_bg};">
            <div class="metric-title">Moment (M)</div>
            <div class="metric-value" style="color:{m_txt}">{M_actual:,.0f} <small>kg.m</small></div>
            <div class="metric-sub">Limit: {M_cap/100:,.0f} kg.m</div>
            <div class="metric-badge" style="background-color:rgba(0,0,0,0.1); color:{m_txt};">Usage: {m_pct:.0f}%</div>
        </div>""", unsafe_allow_html=True)
    
    # Deflection Box
    d_pct = delta_actual/delta_allow*100
    d_bg = "#e8f8f5"
    d_txt = "#2e86c1"
    with cm3: 
        st.markdown(f"""
        <div class="metric-box" style="border-top-color: #27ae60; background-color: {d_bg};">
            <div class="metric-title">Deflection</div>
            <div class="metric-value" style="color:{d_txt}">{delta_actual:.2f} <small>cm</small></div>
            <div class="metric-sub">Allow (L/{defl_lim_val}): {delta_allow:.2f} cm</div>
            <div class="metric-badge" style="background-color:rgba(0,0,0,0.1); color:{d_txt};">Usage: {d_pct:.0f}%</div>
        </div>""", unsafe_allow_html=True)

    # --- 4. Graph ---
    st.markdown("<br>", unsafe_allow_html=True)
    g_spans = np.linspace(2, 15, 100)
    g_data = [get_capacity(l) for l in g_spans]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=g_spans, y=[x[1] for x in g_data], mode='lines', name=f'{label_cap_m} Limit', line=dict(color='#f39c12', dash='dot')))
    fig.add_trace(go.Scatter(x=g_spans, y=[x[0] for x in g_data], mode='lines', name=f'{label_cap_v} Limit', line=dict(color='#e74c3c', dash='dot')))
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
