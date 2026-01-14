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
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600&family=Roboto+Mono:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Sarabun', sans-serif; 
        color: #333;
    }

    /* --- Metric Card CSS --- */
    .metric-card-clean {
        background: white;
        border-radius: 8px;
        padding: 15px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .mc-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .mc-title { font-weight: 600; color: #555; font-size: 16px; }
    .mc-percent { font-family: 'Roboto Mono', monospace; font-size: 22px; font-weight: 700; }

    .mc-values { 
        display: flex; justify-content: space-between; align-items: flex-end; 
        font-family: 'Roboto Mono', monospace; color: #333; margin-bottom: 8px; font-size: 14px;
    }
    .mc-label { font-size: 11px; color: #888; font-family: 'Sarabun'; text-transform: uppercase; }
    .mc-val-text { font-weight: 600; font-size: 15px; }

    .mc-bar-bg { background-color: #f1f1f1; height: 6px; border-radius: 3px; overflow: hidden; margin-bottom: 10px; }
    .mc-bar-fill { height: 100%; border-radius: 3px; }

    /* Footer equation text */
    .mc-footer { 
        background-color: #f8f9fa; 
        border-top: 1px solid #eee; 
        padding: 6px; 
        text-align: center; 
        font-family: 'Roboto Mono', monospace;
        font-size: 12px;
        color: #555;
        border-radius: 4px;
    }

    /* --- Calculation Box --- */
    .calc-box {
        background-color: #fff;
        border: 1px solid #ddd;
        border-left-width: 5px;
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 10px;
    }
    .calc-header {
        font-weight: bold; font-size: 14px; margin-bottom: 8px; 
        border-bottom: 1px dashed #ccc; padding-bottom: 4px;
    }

    /* --- Highlight Card --- */
    .highlight-card { 
        background: white;
        padding: 20px; 
        border-radius: 10px; 
        border: 1px solid #ddd; 
        border-left: 6px solid #2c3e50;
        margin-bottom: 20px; 
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
    st.caption("Professional Edition")
    st.divider()
    
    st.markdown("#### 1. Design Method")
    method = st.radio("Method", ["ASD (Allowable Stress)", "LRFD (Limit State)"], label_visibility="collapsed")
    is_lrfd = "LRFD" in method
    
    st.divider()
    st.markdown("#### 2. Beam Selection")
    sec_name = st.selectbox("Section Size", list(steel_db.keys()), index=5)
    user_span = st.number_input("Span Length (m)", min_value=1.0, value=6.0, step=0.5)
    fy = st.number_input("Yield Strength (ksc)", 2400)
    defl_ratio = st.selectbox("Deflection Limit", ["L/300", "L/360", "L/400"], index=1)
    
    st.divider()
    st.markdown("#### 3. Connection")
    bolt_size = st.selectbox("Bolt Diameter", ["M16", "M20", "M22", "M24"], index=1)
    design_mode = st.radio("Load Basis", ["Actual Load (from Span)", "Fixed % Capacity"])
    
    if design_mode == "Fixed % Capacity":
        target_pct = st.slider("Target %", 50, 100, 75, 5)
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

# 1. Determine Capacity (Limit)
if is_lrfd:
    phi_b, phi_v = 0.90, 1.00
    M_cap_kgcm = phi_b * fy * Zx       
    V_cap_kg = phi_v * 0.6 * fy * Aw 
    label_load = "Factored Load (Wu)"
    label_cap_m = "Phi Mn"
    label_cap_v = "Phi Vn"
else:
    M_cap_kgcm = 0.6 * fy * Zx         
    V_cap_kg = 0.4 * fy * Aw         
    label_load = "Safe Load (w)"
    label_cap_m = "M allow"
    label_cap_v = "V allow"

# 2. Determine Safe Load (Reverse Calc) for the Highlight Card & Chart
L_cm = user_span * 100
w_shear = (2 * V_cap_kg) / L_cm * 100
w_moment = (8 * M_cap_kgcm) / (L_cm**2) * 100
w_defl = ((L_cm/defl_lim_val) * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100
w_gov = min(w_shear, w_moment, w_defl)
user_safe_load = w_gov # Max allowable uniform load

if w_gov == w_shear: user_cause = "Shear"
elif w_gov == w_moment: user_cause = "Moment"
else: user_cause = "Deflection"

# 3. Determine ACTUAL Forces based on the Safe Load (Forward Calc)
# These are the values we use for the "Check"
V_actual = user_safe_load * user_span / 2
M_actual_kgm = (user_safe_load * user_span**2) / 8
delta_actual = (5 * (user_safe_load/100) * (L_cm**4)) / (384 * E_mod * Ix)
delta_limit = L_cm / defl_lim_val

if design_mode == "Actual Load (from Span)":
    V_design = V_actual
else:
    V_design = V_cap_kg * (target_pct / 100)

# ==========================================
# 4. DISPLAY
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Analysis Dashboard", "🔩 Connection", "💾 Data Table", "📝 Report"])

with tab1:
    st.subheader(f"Capacity Analysis: {sec_name}")
    
    # --- 1. Highlight Card ---
    if user_cause == "Moment": c_stat = "#f39c12"; 
    elif user_cause == "Shear": c_stat = "#27ae60"; 
    else: c_stat = "#2980b9";
    
    st.markdown(f"""
    <div class="highlight-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="color:#666; font-size:14px; text-transform:uppercase;">MAX {label_load}</span><br>
                <span style="font-family:'Roboto Mono'; font-size:42px; font-weight:700; color:#333;">{user_safe_load:,.0f}</span> 
                <span style="font-size:18px; color:#777;">kg/m</span>
            </div>
            <div style="text-align: right;">
                <span style="color:#666; font-size:14px; text-transform:uppercase;">Controlled By</span><br>
                <span style="font-size: 18px; font-weight:bold; color:{c_stat}; background:{c_stat}20; padding: 5px 15px; border-radius:20px;">
                    {user_cause}
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- 2. Calculation Details (THE FIX: Plain & Simple Check) ---
    with st.expander(f"Show Design Check (Demand / Capacity)", expanded=True):
        c1, c2, c3 = st.columns(3)
        
        # Helper for formatting
        def fmt(n): return f"{n:,.0f}"

        with c1:
            shear_ratio = (V_actual / V_cap_kg) * 100
            st.markdown(f'<div class="calc-box" style="border-left-color: #27ae60;"><div class="calc-header">1. Shear Check</div>', unsafe_allow_html=True)
            st.latex(r''' \% = \frac{V_{actual}}{V_{capacity}} \times 100 ''')
            st.latex(fr''' \% = \frac{{{fmt(V_actual)}}}{{{fmt(V_cap_kg)}}} \times 100 ''')
            st.latex(fr''' \% = \mathbf{{{shear_ratio:.1f}\%}} ''')
            st.markdown("</div>", unsafe_allow_html=True)

        with c2:
            moment_ratio = (M_actual_kgm / (M_cap_kgcm/100)) * 100
            st.markdown(f'<div class="calc-box" style="border-left-color: #f39c12;"><div class="calc-header">2. Moment Check</div>', unsafe_allow_html=True)
            st.latex(r''' \% = \frac{M_{actual}}{M_{capacity}} \times 100 ''')
            # Note: Displaying M in kg-m for consistency
            st.latex(fr''' \% = \frac{{{fmt(M_actual_kgm)}}}{{{fmt(M_cap_kgcm/100)}}} \times 100 ''')
            st.latex(fr''' \% = \mathbf{{{moment_ratio:.1f}\%}} ''')
            st.markdown("</div>", unsafe_allow_html=True)

        with c3:
            defl_ratio_val = (delta_actual / delta_limit) * 100
            st.markdown(f'<div class="calc-box" style="border-left-color: #2980b9;"><div class="calc-header">3. Deflection Check</div>', unsafe_allow_html=True)
            st.latex(r''' \% = \frac{\Delta_{actual}}{\Delta_{limit}} \times 100 ''')
            st.latex(fr''' \% = \frac{{{delta_actual:.2f}}}{{{delta_limit:.2f}}} \times 100 ''')
            st.latex(fr''' \% = \mathbf{{{defl_ratio_val:.1f}\%}} ''')
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 3. METRIC CARDS (FIXED HTML) ---
    cm1, cm2, cm3 = st.columns(3)
    
    def render_metric_card(icon, title, actual_val, limit_val, unit, color):
        # Calculate percent
        pct = (actual_val / limit_val) * 100 if limit_val > 0 else 0
        width_css = f"{min(pct, 100):.1f}"
        
        # Format strings
        s_act = f"{actual_val:,.2f}" if unit == "cm" else f"{actual_val:,.0f}"
        s_lim = f"{limit_val:,.2f}" if unit == "cm" else f"{limit_val:,.0f}"
        
        # Color warning
        final_color = "#c0392b" if pct > 100 else color

        # Construct HTML
        html_code = f"""
        <div class="metric-card-clean" style="border-top: 4px solid {final_color};">
            <div class="mc-header">
                <div class="mc-title"><span>{icon}</span> {title}</div>
                <div class="mc-percent" style="color:{final_color};">{pct:.1f}%</div>
            </div>
            
            <div class="mc-values">
                <div style="text-align:left;">
                    <div class="mc-label">ACTUAL</div>
                    <div class="mc-val-text">{s_act}</div>
                </div>
                <div style="text-align:right;">
                    <div class="mc-label">LIMIT ({unit})</div>
                    <div class="mc-val-text" style="color:#999;">{s_lim}</div>
                </div>
            </div>
            
            <div class="mc-bar-bg">
                <div class="mc-bar-fill" style="width:{width_css}%; background-color:{final_color};"></div>
            </div>
            
            <div class="mc-footer">
                {s_act} ÷ {s_lim} = <b>{pct:.1f}%</b>
            </div>
        </div>
        """
        return html_code
    
    # !!! CRITICAL: unsafe_allow_html=True is REQUIRED here !!!
    with cm1:
        st.markdown(render_metric_card("✂️", "Shear (V)", V_actual, V_cap_kg, "kg", "#27ae60"), unsafe_allow_html=True)
    with cm2:
        st.markdown(render_metric_card("🔄", "Moment (M)", M_actual_kgm, M_cap_kgcm/100, "kg.m", "#f39c12"), unsafe_allow_html=True)
    with cm3:
        st.markdown(render_metric_card("📏", "Deflection", delta_actual, delta_limit, "cm", "#2980b9"), unsafe_allow_html=True)

    # --- 4. Chart ---
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Helper to re-calc for chart
    def get_caps(L):
        L_c = L * 100
        w1 = (2 * V_cap_kg) / L_c * 100
        w2 = (8 * M_cap_kgcm) / (L_c**2) * 100
        return w1, w2, min(w1, w2)

    g_spans = np.linspace(2, 15, 50)
    g_shear = []
    g_moment = []
    g_max = []
    
    # Calculate chart data loop
    for l_val in g_spans:
        s, m, _ = get_caps(l_val)
        g_shear.append(s)
        g_moment.append(m)
        # We also need deflection for the "Real" capacity, but to keep chart simple, let's plot S vs M
        # Or better, just plot what we had before correctly
        
    # Re-using the simple function for chart consistency
    def get_all_caps(L_m):
        L_c = L_m * 100
        ws = (2 * V_cap_kg) / L_c * 100
        wm = (8 * M_cap_kgcm) / (L_c**2) * 100
        wd = ((L_c/defl_lim_val) * 384 * E_mod * Ix) / (5 * (L_c**4)) * 100
        return ws, wm, wd, min(ws, wm, wd)

    c_data = [get_all_caps(l) for l in g_spans]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=g_spans, y=[x[1] for x in c_data], mode='lines', name='Moment Limit', line=dict(color='#f39c12', dash='dot')))
    fig.add_trace(go.Scatter(x=g_spans, y=[x[0] for x in c_data], mode='lines', name='Shear Limit', line=dict(color='#27ae60', dash='dot')))
    fig.add_trace(go.Scatter(x=g_spans, y=[x[3] for x in c_data], mode='lines', name='Safe Load Capacity', line=dict(color='#2c3e50', width=3), fill='tozeroy', fillcolor='rgba(44, 62, 80, 0.1)'))
    fig.add_trace(go.Scatter(x=[user_span], y=[user_safe_load], mode='markers', 
                             marker=dict(color='#c0392b', size=14, symbol='x', line=dict(width=2, color='white')), 
                             name='Current Point'))
    
    fig.update_layout(
        title="Load Capacity Curve",
        xaxis_title="Span Length (m)",
        yaxis_title="Load (kg/m)",
        height=400,
        margin=dict(t=40, b=40, l=60, r=40),
        hovermode="x unified",
        legend=dict(orientation="h", y=1.05, x=1, xanchor="right")
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    req_bolt_result, v_bolt_result = conn.render_connection_tab(V_design, bolt_size, method, is_lrfd, p)

with tab3:
    st.markdown("### Load Table")
    t_spans = np.arange(2, 12.5, 0.5)
    t_rows = []
    for l in t_spans:
        ws, wm, wd, wgov = get_all_caps(l)
        ctrl = "Shear" if wgov == ws else ("Moment" if wgov == wm else "Deflection")
        t_rows.append({"Span (m)": l, "Max Load (kg/m)": wgov, "Control": ctrl})
    
    st.dataframe(pd.DataFrame(t_rows).style.format("{:,.0f}", subset=["Max Load (kg/m)"]), use_container_width=True)

with tab4:
    caps = {'M_cap': M_cap_kgcm, 'V_cap': V_cap_kg} # Pass units correctly
    bolt_info = {'size': bolt_size, 'capacity': v_bolt_result}
    rep.render_report_tab(method, is_lrfd, sec_name, fy, p, caps, bolt_info)
