import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- IMPORT MODULES ---
import connection_design as conn
import report_generator as rep

# ==========================================
# 1. SETUP & STYLE (The Design System)
# ==========================================
st.set_page_config(page_title="Beam Insight V12", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    /* Import Fonts: Sarabun (TH/EN) & Roboto Mono (Numbers/Code) */
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;700&family=Roboto+Mono:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Sarabun', sans-serif; 
        color: #2c3e50;
    }
    
    /* --- COLOR PALETTE VARIABLES --- */
    :root {
        --primary: #2c3e50;
        --accent: #3498db;
        --success: #10b981; /* Soft Emerald */
        --warning: #f59e0b; /* Amber */
        --info: #3b82f6;    /* Blue */
        --bg-light: #f8fafc;
        --border-color: #e2e8f0;
    }

    /* --- 1. METRIC CARD (Professional) --- */
    .metric-card-final {
        background: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border: 1px solid var(--border-color);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: transform 0.2s ease;
    }
    .metric-card-final:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }

    .m-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }
    .m-title { 
        font-weight: 600; color: #64748b; font-size: 15px; 
        text-transform: uppercase; letter-spacing: 0.5px;
        display: flex; align-items: center; gap: 8px; 
    }
    .m-percent { font-family: 'Roboto Mono', monospace; font-size: 28px; font-weight: 700; line-height: 1; }

    /* Values Row */
    .m-values { 
        display: flex; justify-content: space-between; align-items: flex-end; 
        margin-bottom: 12px; font-family: 'Roboto Mono', monospace;
    }
    .val-group { display: flex; flex-direction: column; }
    .val-label { font-size: 11px; color: #94a3b8; font-weight: 600; text-transform: uppercase; margin-bottom: 4px; font-family: 'Sarabun', sans-serif;}
    .val-num { font-size: 18px; font-weight: 600; color: #334155; }
    .val-limit { font-size: 18px; color: #cbd5e1; }

    /* Progress Bar */
    .m-bar-bg { background-color: #f1f5f9; height: 8px; border-radius: 4px; overflow: hidden; margin-bottom: 16px; }
    .m-bar-fill { height: 100%; border-radius: 4px; }

    /* Footer / Check Equation */
    .m-check { 
        background-color: #f8fafc; border-radius: 6px; padding: 8px 12px; 
        font-size: 12px; color: #64748b; text-align: center; 
        border: 1px solid #e2e8f0; font-family: 'Roboto Mono', monospace;
        display: flex; justify-content: center; align-items: center; gap: 8px;
    }
    .m-check span { color: #94a3b8; }

    /* --- 2. CALCULATION BOX (Paper Style) --- */
    .calc-box {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid var(--accent);
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        height: 100%;
    }
    .calc-title {
        font-weight: 700; color: #1e293b; margin-bottom: 15px;
        font-size: 16px; border-bottom: 2px solid #f1f5f9; padding-bottom: 8px;
    }

    /* --- 3. MAIN HIGHLIGHT CARD --- */
    .highlight-card { 
        background: linear-gradient(to right, #ffffff, #f8fafc);
        padding: 30px; border-radius: 16px; 
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); 
        margin-bottom: 30px; 
    }
    .big-num { font-family: 'Roboto Mono', monospace; font-weight: 700; }
    
    /* Global Adjustments */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { border-radius: 4px; padding-top: 8px; padding-bottom: 8px; }
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
    st.caption("Engineered for Precision")
    st.divider()
    
    st.markdown("### 1. Method")
    method = st.radio("Design Code", ["ASD (Allowable Stress)", "LRFD (Limit State)"], label_visibility="collapsed")
    is_lrfd = "LRFD" in method
    
    st.divider()
    st.markdown("### 2. Beam")
    sec_name = st.selectbox("Section Size", list(steel_db.keys()), index=5)
    user_span = st.number_input("Span Length (m)", min_value=1.0, value=6.0, step=0.5)
    fy = st.number_input("Yield Strength (ksc)", 2400)
    defl_ratio = st.selectbox("Deflection Limit", ["L/300", "L/360", "L/400"], index=1)
    
    st.divider()
    st.markdown("### 3. Connection")
    bolt_size = st.selectbox("Bolt Diameter", ["M16", "M20", "M22", "M24"], index=1)
    design_mode = st.radio("Load Basis:", ["Actual Load (from Span)", "Fixed % Capacity"])
    
    if design_mode == "Fixed % Capacity":
        target_pct = st.slider("Target Usage %", 50, 100, 75, 5)
    else:
        target_pct = None

    E_mod = 2.04e6 
    defl_lim_val = int(defl_ratio.split("/")[1])

# ==========================================
# 3. CORE LOGIC
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
# 4. DISPLAY
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Analysis Dashboard", "🔩 Connection", "💾 Data Table", "📝 Report"])

with tab1:
    st.markdown(f"### Capacity Analysis: **{sec_name}**")
    
    # Colors for Status
    if user_cause == "Shear": c_stat = "#10b981"; 
    elif user_cause == "Moment": c_stat = "#f59e0b"; 
    else: c_stat = "#3b82f6";
    
    # --- 1. Highlight Card ---
    st.markdown(f"""
    <div class="highlight-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="color:#64748b; font-size:14px; text-transform:uppercase; letter-spacing:1px;">Maximum {label_load}</span><br>
                <span class="big-num" style="color:#1e293b; font-size:42px;">{user_safe_load:,.0f}</span> 
                <span style="font-size:18px; color:#94a3b8; font-weight:500;">kg/m</span>
            </div>
            <div style="text-align: right;">
                <span style="color:#64748b; font-size:14px; text-transform:uppercase;">Control Factor</span><br>
                <span style="font-size: 18px; font-weight:700; color:{c_stat}; background:{c_stat}15; padding: 6px 16px; border-radius:30px;">
                    {user_cause}
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- 2. Calculation Details (Standardized Math) ---
    with st.expander(f"Show Calculation Steps (Standardized)", expanded=True):
        c1, c2, c3 = st.columns(3)
        L_cm_disp = user_span * 100
        
        # Helper for consistent latex color/bold
        def latex_result(val, unit): return fr"\mathbf{{{val:,.0f}}} \; \text{{{unit}}}"

        with c1:
            st.markdown(f'<div class="calc-box" style="border-left-color: #10b981;"><div class="calc-title">1. Shear Check</div>', unsafe_allow_html=True)
            st.latex(r''' w = \frac{2 \times V_{cap}}{L} \times 100 ''')
            st.latex(fr''' w = \frac{{2 \times {V_cap:,.0f}}}{{{L_cm_disp:,.0f}}} \times 100 ''')
            st.latex(fr''' w = {latex_result(w_shear, 'kg/m')} ''')
            st.markdown("</div>", unsafe_allow_html=True)

        with c2:
            st.markdown(f'<div class="calc-box" style="border-left-color: #f59e0b;"><div class="calc-title">2. Moment Check</div>', unsafe_allow_html=True)
            st.latex(r''' w = \frac{8 \times M_{cap}}{L^2} \times 100 ''')
            st.latex(fr''' w = \frac{{8 \times {M_cap:,.0f}}}{{{L_cm_disp:,.0f}^2}} \times 100 ''')
            st.latex(fr''' w = {latex_result(w_moment, 'kg/m')} ''')
            st.markdown("</div>", unsafe_allow_html=True)

        with c3:
            st.markdown(f'<div class="calc-box" style="border-left-color: #3b82f6;"><div class="calc-title">3. Deflection Check</div>', unsafe_allow_html=True)
            st.latex(r''' w = \frac{384 E I \Delta_{allow}}{5 L^4} \times 100 ''')
            st.latex(fr''' w = \frac{{384 \times {E_mod:.2e} \times {Ix} \times {delta_allow:.2f}}}{{5 \times {L_cm_disp:,.0f}^4}} \times 100 ''')
            st.latex(fr''' w = {latex_result(w_defl, 'kg/m')} ''')
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 3. METRIC CARDS (Refined) ---
    cm1, cm2, cm3 = st.columns(3)
    
    def create_card_polished(icon, title, actual, limit, unit, color_hex, decimal=0):
        pct = (actual / limit) * 100
        width_css = f"{min(pct, 100):.1f}"
        
        # Color Logic
        c_final = "#ef4444" if pct > 100 else color_hex
        fmt = f",.{decimal}f"
        
        return f"""
        <div class="metric-card-final">
            <div>
                <div class="m-header">
                    <div class="m-title"><span style="font-size:18px;">{icon}</span> {title}</div>
                    <div class="m-percent" style="color:{c_final};">{pct:.1f}%</div>
                </div>
                
                <div class="m-values">
                    <div class="val-group">
                        <span class="val-label">Actual Load</span>
                        <span class="val-num">{actual:{fmt}}</span>
                    </div>
                    <div class="val-group" style="text-align:right;">
                        <span class="val-label">Capacity</span>
                        <span class="val-limit">{limit:{fmt}} <small style="font-size:12px;">{unit}</small></span>
                    </div>
                </div>
                
                <div class="m-bar-bg">
                    <div class="m-bar-fill" style="width:{width_css}%; background-color:{c_final};"></div>
                </div>
            </div>
            
            <div class="m-check">
                <span style="font-family:'Sarabun';">Check:</span> 
                {actual:{fmt}} ÷ {limit:{fmt}} = <b>{pct:.1f}%</b>
            </div>
        </div>
        """
    
    with cm1:
        st.markdown(create_card_polished("✂️", "Shear (V)", V_actual, V_cap, "kg", "#10b981"), unsafe_allow_html=True) # Green
    with cm2:
        st.markdown(create_card_polished("🔄", "Moment (M)", M_actual, M_cap/100, "kg.m", "#f59e0b"), unsafe_allow_html=True) # Amber
    with cm3:
        st.markdown(create_card_polished("📏", "Deflection", delta_actual, delta_allow, "cm", "#3b82f6", decimal=2), unsafe_allow_html=True) # Blue

    # --- 4. Chart (Minimalist) ---
    st.markdown("<br>", unsafe_allow_html=True)
    g_spans = np.linspace(2, 15, 100)
    g_data = [get_capacity(l) for l in g_spans]
    
    fig = go.Figure()
    # Colors updated to match palette
    fig.add_trace(go.Scatter(x=g_spans, y=[x[1] for x in g_data], mode='lines', name=f'{label_cap_m}', line=dict(color='#f59e0b', dash='dash')))
    fig.add_trace(go.Scatter(x=g_spans, y=[x[0] for x in g_data], mode='lines', name=f'{label_cap_v}', line=dict(color='#10b981', dash='dash')))
    fig.add_trace(go.Scatter(x=g_spans, y=[x[3] for x in g_data], mode='lines', name=f'Capacity Envelope', line=dict(color='#3b82f6', width=3), fill='tozeroy', fillcolor='rgba(59, 130, 246, 0.05)'))
    fig.add_trace(go.Scatter(x=[user_span], y=[user_safe_load], mode='markers', 
                             marker=dict(color='#1e293b', size=15, symbol='circle', line=dict(width=3, color='white')), 
                             name='Selected Span'))
    
    fig.update_layout(
        title=dict(text="Load Capacity Curves", font=dict(size=18, color='#64748b')),
        height=400, 
        margin=dict(t=50, b=40, l=60, r=40),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(showgrid=True, gridcolor='#f1f5f9', title="Span (m)"),
        yaxis=dict(showgrid=True, gridcolor='#f1f5f9', title="Load (kg/m)"),
        hovermode="x unified",
        legend=dict(orientation="h", y=1.05, x=1, xanchor="right")
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    req_bolt_result, v_bolt_result = conn.render_connection_tab(V_design, bolt_size, method, is_lrfd, p)

with tab3:
    st.markdown("### Reference Load Table")
    t_spans = np.arange(2, 15.5, 0.5)
    t_data = [get_capacity(l) for l in t_spans]
    df_res = pd.DataFrame({"Span (m)": t_spans, f"Max {label_load}": [x[3] for x in t_data], "Control": [x[4] for x in t_data]})
    st.dataframe(df_res.style.format("{:,.0f}", subset=[f"Max {label_load}"]), use_container_width=True)

with tab4:
    caps = {'M_cap': M_cap, 'V_cap': V_cap}
    bolt_info = {'size': bolt_size, 'capacity': v_bolt_result}
    rep.render_report_tab(method, is_lrfd, sec_name, fy, p, caps, bolt_info)
