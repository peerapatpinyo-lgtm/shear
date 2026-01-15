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
    st.error(f"⚠️ Error importing modules: {e}. Please ensure data_utils.py, connection_design.py, drawing_utils.py, and calculation_report.py are in the same directory.")
    st.stop()

# =============================================================================
# 1. PAGE CONFIG & PROFESSIONAL STYLE (V13.2 Style)
# =============================================================================
st.set_page_config(page_title="Beam Insight V14 Ultimate", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=Roboto+Mono:wght@400;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }

    /* --- Metric Card --- */
    .detail-card {
        background: white; border-radius: 12px; padding: 20px;
        border: 1px solid #e5e7eb; border-top: 6px solid #2563eb;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 20px;
    }
    .status-badge {
        padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 12px;
        float: right; text-transform: uppercase;
    }
    .pass { background-color: #dcfce7; color: #166534; }
    .fail { background-color: #fee2e2; color: #991b1b; }

    /* --- Highlight Card --- */
    .highlight-card { 
        background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%);
        padding: 25px; border-radius: 20px; border-left: 8px solid #2563eb; 
        box-shadow: 0 10px 30px rgba(37, 99, 235, 0.08); margin-bottom: 25px; border: 1px solid #e5e7eb;
    }
    .big-num { color: #1e40af; font-size: 42px; font-weight: 800; font-family: 'Roboto Mono', monospace; }
    .sub-text { color: #6b7280; font-size: 14px; font-weight: 600; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. SIDEBAR INPUTS (V14 Structure)
# =============================================================================
with st.sidebar:
    st.title("🏗️ Beam Insight V14")
    st.caption("Professional Structural Analysis")
    
    # 2.1 Global Settings
    method = st.radio("Design Method", ["ASD (Allowable Stress)", "LRFD (Limit State)"])
    is_lrfd = "LRFD" in method
    
    # 2.2 Project Info
    with st.expander("📋 Project Information"):
        proj_name = st.text_input("Project Name", "Warehouse Building A")
        eng_name = st.text_input("Engineer Name", "Eng. Somchai")
    
    st.divider()

    # 2.3 Beam & Material
    st.subheader("🛠️ Material & Section")
    sec_name = st.selectbox("Select Section", list(db.STEEL_DB.keys()), index=11)
    p = db.STEEL_DB[sec_name]
    
    # Material Props
    c_fy, c_e = st.columns(2)
    with c_fy: Fy = st.number_input("Fy (ksc)", value=2500)
    with c_e:  E_mod = st.number_input("E (ksc)", value=2.04e6, format="%e")
    
    # Geometry
    user_span = st.number_input("Span Length (m)", min_value=1.0, value=6.0, step=0.5)
    defl_ratio = st.selectbox("Deflection Limit", ["L/200", "L/240", "L/300", "L/360", "L/400"], index=3)
    defl_lim_val = int(defl_ratio.split("/")[1])
    
    st.divider()

    # 2.4 Load Logic
    st.subheader("⚖️ Load Configuration")
    design_mode = st.radio("Load Input:", ["Auto (Max Capacity %)", "Manual (Input Load)"])
    
    if design_mode == "Auto (Max Capacity %)":
        target_pct = st.slider("Target Capacity (%)", 10, 100, 80)
    else:
        user_load_input = st.number_input("Uniform Load (kg/m)", value=1000)

    st.divider()
    
    # 2.5 Connection Logic
    st.subheader("🔗 Connection Logic")
    conn_type = st.selectbox("Connection Type", [
        "Fin Plate (Single Shear)", 
        "End Plate (Single Shear)", 
        "Double Angle (Double Shear)"
    ])

# =============================================================================
# 3. CORE CALCULATIONS (Engine)
# =============================================================================
# 3.1 Constants & Section Properties
L_cm = user_span * 100
Ix, Zx = p['Ix'], p['Zx']
h, tw, tf = p['h'], p['tw'], p['tf']
Aw = h * tw # Simplified web area
w_self = p['w']

# 3.2 Capacity Setup (ASD vs LRFD)
if is_lrfd:
    label_load = "Factored Load (Wu)"
    M_cap = 0.90 * Fy * Zx
    V_cap = 1.00 * 0.60 * Fy * Aw
else:
    label_load = "Safe Load (w)"
    M_cap = (Fy * Zx) / 1.67
    V_cap = (0.60 * Fy * Aw) / 1.50

# 3.3 Dynamic Capacity Function (For Envelope Curve)
def get_capacity(L_m_input):
    """Calculate max load w (kg/m) for a given span"""
    L_c = L_m_input * 100
    
    # Shear Governs: V = wL/2 -> w = 2V/L
    w_v = (2 * V_cap / L_c) * 100 
    
    # Moment Governs: M = wL^2/8 -> w = 8M/L^2
    w_m = (8 * M_cap / (L_c**2)) * 100
    
    # Deflection Governs: D = 5wL^4/384EI -> w = 384EI*D / 5L^4
    # D_allow = L_c / defl_lim_val
    D_all_temp = L_c / defl_lim_val
    w_d = (D_all_temp * 384 * E_mod * Ix) / (5 * (L_c**4)) * 100
    
    w_gov = min(w_v, w_m, w_d)
    cause = "Shear" if w_gov == w_v else ("Moment" if w_gov == w_m else "Deflection")
    return w_v, w_m, w_d, w_gov, cause

# 3.4 Calculate Main Design Point
w_max_shear, w_max_moment, w_max_defl, w_max_gov, user_cause = get_capacity(user_span)

if design_mode == "Auto (Max Capacity %)":
    user_safe_load = w_max_gov * (target_pct / 100)
else:
    user_safe_load = user_load_input

# 3.5 Calculate Actual Forces
w_kg_cm = user_safe_load / 100
v_act = w_kg_cm * L_cm / 2
m_act = w_kg_cm * L_cm**2 / 8
d_act = (5 * w_kg_cm * L_cm**4) / (384 * E_mod * Ix)
d_all = L_cm / defl_lim_val

# 3.6 Ratios & Status
v_ratio = v_act / V_cap
m_ratio = m_act / M_cap
d_ratio = d_act / d_all
is_pass = (v_ratio <= 1.0) and (m_ratio <= 1.0) and (d_ratio <= 1.0)

# Pack Beam Results for Report
beam_res = {
    'pass': is_pass,
    'w_safe': user_safe_load,
    'v_act': v_act, 'v_cap': V_cap, 'v_ratio': v_ratio,
    'm_act': m_act/100, 'm_cap': M_cap/100, 'm_ratio': m_ratio,
    'd_act': d_act, 'd_all': d_all, 'd_ratio': d_ratio,
    'span': user_span
}

# =============================================================================
# 4. UI RENDERING
# =============================================================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Beam Analysis", "🔩 Connection Detail", "💾 Load Table", "📝 Report"])

# --- TAB 1: BEAM ANALYSIS (Restored V13.2 Glory) ---
with tab1:
    st.subheader(f"Engineering Analysis: {sec_name}")
    
    # 1. Highlight Card (Governing Check)
    cause_color = "#dc2626" if user_cause == "Shear" else ("#d97706" if user_cause == "Moment" else "#059669")
    st.markdown(f"""
    <div class="highlight-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div><span class="sub-text">Applied Load ({label_load})</span><br>
                <span class="big-num">{user_safe_load:,.0f}</span> <span style="font-size:20px; color:#4b5563;">kg/m</span></div>
            <div style="text-align: right;"><span class="sub-text">Governing Limit</span><br>
                <span style="font-size: 22px; font-weight:bold; color:{cause_color}; background-color:{cause_color}15; padding: 8px 20px; border-radius:15px; border: 1px solid {cause_color}30;">{user_cause.upper()}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Detailed Cards with Steps (Function Helper)
    def render_check_ratio_with_w(title, act, lim, unit, ratio, eq_w, eq_act):
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
            st.info(f"**Step 1: Limit Calculation**")
            st.latex(eq_w)
            st.divider()
            st.info(f"**Step 2: Actual Force & Ratio**")
            st.latex(eq_act)

    c1, c2, c3 = st.columns(3)
    L_disp = user_span * 100
    
    with c1:
        render_check_ratio_with_w(
            "Shear Check", v_act, V_cap, "kg", v_ratio,
            fr"V_{{cap}} = \dots = {V_cap:,.0f} \text{{ kg}} \rightarrow w_{{lim}} = {w_max_shear:,.0f} \text{{ kg/m}}",
            fr"V_{{act}} = \frac{{wL}}{{2}} = {v_act:,.0f} \text{{ kg}} \rightarrow \text{{Ratio}} = {v_ratio:.3f}"
        )
    with c2:
        render_check_ratio_with_w(
            "Moment Check", m_act/100, M_cap/100, "kg-m", m_ratio,
            fr"M_{{cap}} = \dots = {M_cap/100:,.0f} \text{{ kg-m}} \rightarrow w_{{lim}} = {w_max_moment:,.0f} \text{{ kg/m}}",
            fr"M_{{act}} = \frac{{wL^2}}{{8}} = {m_act/100:,.0f} \text{{ kg-m}} \rightarrow \text{{Ratio}} = {m_ratio:.3f}"
        )
    with c3:
        render_check_ratio_with_w(
            "Deflection Check", d_act, d_all, "cm", d_ratio,
            fr"\Delta_{{all}} = L/{defl_lim_val} = {d_all:.2f} \text{{ cm}} \rightarrow w_{{lim}} = {w_max_defl:,.0f} \text{{ kg/m}}",
            fr"\Delta_{{act}} = \frac{{5wL^4}}{{384EI}} = {d_act:.3f} \text{{ cm}} \rightarrow \text{{Ratio}} = {d_ratio:.3f}"
        )

    # 3. Envelope Curve (Restored)
    st.markdown("### 📈 Capacity Envelope Curve")
    spans_plot = np.linspace(2, 12, 100)
    data_env = [get_capacity(s) for s in spans_plot]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spans_plot, y=[d[0] for d in data_env], name='Shear Limit', line=dict(color='#ef4444', dash='dash')))
    fig.add_trace(go.Scatter(x=spans_plot, y=[d[1] for d in data_env], name='Moment Limit', line=dict(color='#f59e0b', dash='dash')))
    fig.add_trace(go.Scatter(x=spans_plot, y=[d[2] for d in data_env], name='Deflection Limit', line=dict(color='#3b82f6', dash='dash')))
    fig.add_trace(go.Scatter(x=spans_plot, y=[d[3] for d in data_env], name='Safe Envelope', fill='tozeroy', fillcolor='rgba(37, 99, 235, 0.1)', line=dict(color='#1e40af', width=4)))
    fig.add_trace(go.Scatter(x=[user_span], y=[user_safe_load], mode='markers+text', name='Design Point', text=[f" ({user_span}m, {user_safe_load:,.0f})"], textposition="top right", marker=dict(color='red', size=12, symbol='diamond', line=dict(width=2, color='white'))))
    fig.update_layout(hovermode="x unified", height=450, margin=dict(t=20, b=20, l=20, r=20), plot_bgcolor='white', xaxis_title="Span Length (m)", yaxis_title="Load (kg/m)")
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: CONNECTION DETAIL (V14 Integration + Clean UI) ---
with tab2:
    # เรียกใช้ conn.render_connection_tab (V14 Fixed Logic)
    conn_result = conn.render_connection_tab(
        V_design=v_act, 
        method=method, 
        is_lrfd=is_lrfd, 
        section_data=p, 
        conn_type=conn_type
    )

# --- TAB 3: LOAD TABLE ---
with tab3:
    st.markdown("### 🏗️ Span-Load Reference Table")
    tbl_spans = np.arange(2.0, 12.5, 0.5)
    tbl_data = []
    for s in tbl_spans:
        res = get_capacity(s)
        tbl_data.append([s, res[3], res[4]])
    
    df_tbl = pd.DataFrame(tbl_data, columns=["Span (m)", "Max Load (kg/m)", "Control"])
    st.dataframe(df_tbl.style.format({"Span (m)": "{:.1f}", "Max Load (kg/m)": "{:,.0f}"}), use_container_width=True)

# --- TAB 4: REPORT ---
with tab4:
    if conn_result:
        project_info = {'name': proj_name, 'eng': eng_name, 'sec': sec_name, 'method': method}
        rep.render_report_tab(project_info, beam_res, conn_result)
    else:
        st.warning("⚠️ Please configure connection in Tab 2.")

# Footer
st.divider()
st.caption("Beam Insight V14 Ultimate | Professional Engineering Software")
