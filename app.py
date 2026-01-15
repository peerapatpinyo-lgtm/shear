import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# --- IMPORT MODULES ---
try:
    import data_utils as db
    import connection_design as conn
    import drawing_utils as dwg
    import calculation_report as rep
except ImportError as e:
    st.error(f"⚠️ Error importing modules: {e}")
    st.stop()

# =============================================================================
# 1. PAGE CONFIG & STYLING
# =============================================================================
st.set_page_config(page_title="Beam Insight V14", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=Roboto+Mono:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
    .detail-card { background: white; border-radius: 12px; padding: 20px; border: 1px solid #e5e7eb; border-top: 6px solid #2563eb; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .status-badge { padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 12px; float: right; text-transform: uppercase; }
    .pass { background-color: #dcfce7; color: #166534; }
    .fail { background-color: #fee2e2; color: #991b1b; }
    .highlight-card { background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%); padding: 25px; border-radius: 20px; border-left: 8px solid #2563eb; box-shadow: 0 10px 30px rgba(37, 99, 235, 0.08); margin-bottom: 25px; border: 1px solid #e5e7eb; }
    .big-num { color: #1e40af; font-size: 42px; font-weight: 800; font-family: 'Roboto Mono', monospace; }
    .sub-text { color: #6b7280; font-size: 14px; font-weight: 600; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. SIDEBAR INPUTS
# =============================================================================
with st.sidebar:
    st.title("🏗️ Beam Insight V14")
    st.caption("Professional Structural Analysis")
    
    method = st.radio("Design Method", ["ASD (Allowable Stress)", "LRFD (Limit State)"])
    is_lrfd = "LRFD" in method
    
    with st.expander("📋 Project Information"):
        proj_name = st.text_input("Project Name", "Warehouse Building A")
        eng_name = st.text_input("Engineer Name", "Eng. Somchai")
    
    st.divider()
    st.subheader("🛠️ Material & Section")
    sec_name = st.selectbox("Select Section", list(db.STEEL_DB.keys()), index=11)
    p = db.STEEL_DB[sec_name]
    
    c_fy, c_e = st.columns(2)
    with c_fy: Fy = st.number_input("Fy (ksc)", value=2500)
    with c_e:  E_mod = st.number_input("E (ksc)", value=2.04e6, format="%e")
    
    user_span = st.number_input("Span Length (m)", min_value=1.0, value=6.0, step=0.5)
    defl_ratio = st.selectbox("Deflection Limit", ["L/200", "L/240", "L/300", "L/360", "L/400"], index=3)
    defl_lim_val = int(defl_ratio.split("/")[1])
    
    st.divider()
    st.subheader("⚖️ Load Configuration")
    design_mode = st.radio("Load Input:", ["Auto (Max Capacity %)", "Manual (Input Load)"])
    
    if design_mode == "Auto (Max Capacity %)":
        target_pct = st.slider("Target Capacity (%)", 10, 100, 80)
    else:
        user_load_input = st.number_input("Uniform Load (kg/m)", value=1000)

    st.divider()
    st.subheader("🔗 Connection Logic")
    conn_type = st.selectbox("Connection Type", ["Fin Plate (Single Shear)", "End Plate (Single Shear)", "Double Angle (Double Shear)"])

# =============================================================================
# 3. CORE CALCULATIONS (Engine)
# =============================================================================
# 3.1 Constants & Section Properties
L_cm = user_span * 100
Ix, Zx = p['Ix'], p['Zx']

# ✅ Correct Unit Conversion (mm -> cm)
h = p['h'] / 10.0   
tw = p['tw'] / 10.0 
tf = p['tf'] / 10.0 

Aw = h * tw # cm^2
w_self_kgm = p['w'] # ✅ Defined correctly here as w_self_kgm

# 3.2 Capacity Setup
if is_lrfd:
    label_load = "Factored Load (Wu)"
    M_cap = 0.90 * Fy * Zx
    V_cap = 1.00 * 0.60 * Fy * Aw
else:
    label_load = "Safe Load (w)"
    M_cap = (Fy * Zx) / 1.67
    V_cap = (0.60 * Fy * Aw) / 1.50

# 3.3 Dynamic Capacity Function
def get_capacity(L_m_input):
    L_c = L_m_input * 100
    w_v = (2 * V_cap / L_c) * 100 
    w_m = (8 * M_cap / (L_c**2)) * 100
    D_all_temp = L_c / defl_lim_val
    w_d = (D_all_temp * 384 * E_mod * Ix) / (5 * (L_c**4)) * 100
    w_gov = min(w_v, w_m, w_d)
    cause = "Shear" if w_gov == w_v else ("Moment" if w_gov == w_m else "Deflection")
    return w_v, w_m, w_d, w_gov, cause

w_max_shear, w_max_moment, w_max_defl, w_max_gov, user_cause = get_capacity(user_span)

if design_mode == "Auto (Max Capacity %)":
    user_safe_load = w_max_gov * (target_pct / 100)
else:
    user_safe_load = user_load_input

# 3.4 Calculate Actual Forces
w_external_kg_cm = user_safe_load / 100
w_self_kg_cm = w_self_kgm / 100
w_total_kg_cm = w_external_kg_cm + w_self_kg_cm # ✅ Correctly uses variables

v_act = w_total_kg_cm * L_cm / 2
m_act = w_total_kg_cm * L_cm**2 / 8
d_act = (5 * w_external_kg_cm * L_cm**4) / (384 * E_mod * Ix) # Deflection typically checks Live Load
d_all = L_cm / defl_lim_val

# 3.5 Ratios
v_ratio = v_act / V_cap
m_ratio = m_act / M_cap
d_ratio = d_act / d_all
is_pass = (v_ratio <= 1.0) and (m_ratio <= 1.0) and (d_ratio <= 1.0)

beam_res = {
    'pass': is_pass, 'w_safe': user_safe_load,
    'v_act': v_act, 'v_cap': V_cap, 'v_ratio': v_ratio,
    'm_act': m_act/100, 'm_cap': M_cap/100, 'm_ratio': m_ratio,
    'd_act': d_act, 'd_all': d_all, 'd_ratio': d_ratio, 'span': user_span
}

# =============================================================================
# 4. UI RENDERING
# =============================================================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Beam Analysis", "🔩 Connection Detail", "💾 Load Table", "📝 Report"])

# --- TAB 1: BEAM ANALYSIS (Enhanced) ---
with tab1:
    st.subheader(f"Engineering Analysis: {sec_name}")
    
    # Highlight Card
    cause_color = "#dc2626" if user_cause == "Shear" else ("#d97706" if user_cause == "Moment" else "#059669")
    total_load_disp = user_safe_load + w_self_kgm # ✅ No more NameError
    
    st.markdown(f"""
    <div class="highlight-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div><span class="sub-text">Total Applied Load (Ext + Self)</span><br>
                <span class="big-num">{total_load_disp:,.0f}</span> <span style="font-size:20px; color:#4b5563;">kg/m</span></div>
            <div style="text-align: right;"><span class="sub-text">Governing Limit</span><br>
                <span style="font-size: 22px; font-weight:bold; color:{cause_color}; background-color:{cause_color}15; padding: 8px 20px; border-radius:15px; border: 1px solid {cause_color}30;">{user_cause.upper()}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    def render_check_ratio_with_w(title, act, lim, unit, ratio, eq_cap, eq_act):
        is_pass = ratio <= 1.0
        status_class = "pass" if is_pass else "fail"
        border_color = "#10b981" if is_pass else "#ef4444"
        st.markdown(f"""
        <div class="detail-card" style="border-top-color: {border_color}">
            <span class="status-badge {status_class}">{'PASS' if is_pass else 'FAIL'}</span>
            <h4 style="margin:0; color:#374151;">{title}</h4>
            <div style="margin-top:10px;">
                <small style="color:#6b7280;">Utilization Ratio:</small>
                <div style="font-size:24px; font-weight:700; color:{border_color};">{ratio:.3f}</div>
                <small style="color:#6b7280;">{act:,.2f} / {lim:,.2f} {unit}</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
        with st.expander(f"View {title} Step-by-Step"):
            st.markdown("**1. Capacity Calculation:**")
            st.latex(eq_cap)
            st.divider()
            st.markdown("**2. Actual Force & Ratio:**")
            st.latex(eq_act)

    c1, c2, c3 = st.columns(3)
    
    # --- LATEX STRINGS ---
    # 1. SHEAR
    Vn_raw = 0.6 * Fy * Aw
    if is_lrfd:
        shear_cap_tex = fr"""
        \begin{{aligned}}
        A_w &= d \times t_w = {h:.2f} \times {tw:.2f} = {Aw:.2f} \text{{ cm}}^2 \\
        V_n &= 0.6 F_y A_w = 0.6 \times {Fy} \times {Aw:.2f} = {Vn_raw:,.0f} \text{{ kg}} \\
        \phi V_n &= 1.00 \times {Vn_raw:,.0f} = \mathbf{{{V_cap:,.0f} \text{{ kg}}}}
        \end{{aligned}}
        """
    else:
        shear_cap_tex = fr"""
        \begin{{aligned}}
        A_w &= d \times t_w = {h:.2f} \times {tw:.2f} = {Aw:.2f} \text{{ cm}}^2 \\
        V_n &= 0.6 F_y A_w = 0.6 \times {Fy} \times {Aw:.2f} = {Vn_raw:,.0f} \text{{ kg}} \\
        V_{{cap}} &= \frac{{V_n}}{{\Omega}} = \frac{{{Vn_raw:,.0f}}}{{1.50}} = \mathbf{{{V_cap:,.0f} \text{{ kg}}}}
        \end{{aligned}}
        """
    shear_act_tex = fr"""
    \begin{{aligned}}
    w_{{total}} &= {total_load_disp:,.0f} \text{{ kg/m}} \\
    V_{{act}} &= \frac{{w_{{total}} L}}{{2}} = \frac{{{total_load_disp:,.0f} \times {user_span}}}{{2}} = \mathbf{{{v_act:,.0f} \text{{ kg}}}} \\
    \text{{Ratio}} &= \frac{{{v_act:,.0f}}}{{{V_cap:,.0f}}} = \mathbf{{{v_ratio:.3f}}}
    \end{{aligned}}
    """

    # 2. MOMENT
    Mn_raw = Fy * Zx
    if is_lrfd:
        moment_cap_tex = fr"""
        \begin{{aligned}}
        M_n &= F_y Z_x = {Fy} \times {Zx} = {Mn_raw:,.0f} \text{{ kg-cm}} \\
        \phi M_n &= 0.90 \times {Mn_raw:,.0f} = \mathbf{{{M_cap/100:,.0f} \text{{ kg-m}}}}
        \end{{aligned}}
        """
    else:
        moment_cap_tex = fr"""
        \begin{{aligned}}
        M_n &= F_y Z_x = {Fy} \times {Zx} = {Mn_raw:,.0f} \text{{ kg-cm}} \\
        M_{{cap}} &= \frac{{M_n}}{{\Omega}} = \frac{{{Mn_raw:,.0f}}}{{1.67}} = \mathbf{{{M_cap/100:,.0f} \text{{ kg-m}}}}
        \end{{aligned}}
        """
    moment_act_tex = fr"""
    \begin{{aligned}}
    M_{{act}} &= \frac{{w_{{total}} L^2}}{{8}} = \frac{{{total_load_disp:,.0f} \times {user_span}^2}}{{8}} \\
    &= \mathbf{{{m_act/100:,.0f} \text{{ kg-m}}}} \\
    \text{{Ratio}} &= \frac{{{m_act/100:,.0f}}}{{{M_cap/100:,.0f}}} = \mathbf{{{m_ratio:.3f}}}
    \end{{aligned}}
    """

    # 3. DEFLECTION
    defl_cap_tex = fr"""
    \Delta_{{allow}} = \frac{{L}}{{{defl_lim_val}}} = \frac{{{L_cm}}}{{{defl_lim_val}}} = \mathbf{{{d_all:.2f} \text{{ cm}}}}
    """
    defl_act_tex = fr"""
    \begin{{aligned}}
    I_x &= {Ix:,.0f} \text{{ cm}}^4, \quad E = {E_mod:,.2e} \text{{ ksc}} \\
    \Delta_{{act}} &= \frac{{5 (w_{{ext}}) L^4}}{{384 E I_x}} = \frac{{5 ({w_external_kg_cm:.2f}) ({L_cm})^{{4}}}}{{384 ({E_mod:.2e}) ({Ix})}} \\
    &= \mathbf{{{d_act:.3f} \text{{ cm}}}} \\
    \text{{Ratio}} &= \frac{{{d_act:.3f}}}{{{d_all:.2f}}} = \mathbf{{{d_ratio:.3f}}}
    \end{{aligned}}
    """

    with c1: render_check_ratio_with_w("Shear Check", v_act, V_cap, "kg", v_ratio, shear_cap_tex, shear_act_tex)
    with c2: render_check_ratio_with_w("Moment Check", m_act/100, M_cap/100, "kg-m", m_ratio, moment_cap_tex, moment_act_tex)
    with c3: render_check_ratio_with_w("Deflection Check", d_act, d_all, "cm", d_ratio, defl_cap_tex, defl_act_tex)

    # Plot
    st.markdown("### 📈 Capacity Envelope Curve")
    spans_plot = np.linspace(2, 12, 100)
    data_env = [get_capacity(s) for s in spans_plot]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spans_plot, y=[d[0] for d in data_env], name='Shear Limit', line=dict(color='#ef4444', dash='dash')))
    fig.add_trace(go.Scatter(x=spans_plot, y=[d[1] for d in data_env], name='Moment Limit', line=dict(color='#f59e0b', dash='dash')))
    fig.add_trace(go.Scatter(x=spans_plot, y=[d[2] for d in data_env], name='Deflection Limit', line=dict(color='#3b82f6', dash='dash')))
    fig.add_trace(go.Scatter(x=spans_plot, y=[d[3] for d in data_env], name='Safe Envelope', fill='tozeroy', fillcolor='rgba(37, 99, 235, 0.1)', line=dict(color='#1e40af', width=4)))
    fig.add_trace(go.Scatter(x=[user_span], y=[total_load_disp], mode='markers+text', name='Design Point', marker=dict(color='red', size=12, symbol='diamond')))
    fig.update_layout(height=450, margin=dict(t=20, b=20, l=20, r=20), xaxis_title="Span Length (m)", yaxis_title="Load (kg/m)")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    conn_result = conn.render_connection_tab(V_design=v_act, method=method, is_lrfd=is_lrfd, section_data=p, conn_type=conn_type)

with tab3:
    st.markdown("### 🏗️ Span-Load Reference Table")
    df_tbl = pd.DataFrame([[s, get_capacity(s)[3], get_capacity(s)[4]] for s in np.arange(2.0, 12.5, 0.5)], columns=["Span (m)", "Max Load (kg/m)", "Control"])
    st.dataframe(df_tbl.style.format({"Span (m)": "{:.1f}", "Max Load (kg/m)": "{:,.0f}"}), use_container_width=True)

with tab4:
    if conn_result: rep.render_report_tab({'name': proj_name, 'eng': eng_name, 'sec': sec_name, 'method': method}, beam_res, conn_result)
    else: st.warning("⚠️ Please configure connection in Tab 2.")

st.divider(); st.caption("Beam Insight V14.2 Final | Professional Engineering Software")
