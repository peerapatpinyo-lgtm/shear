import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# --- IMPORT MODULES ---
try:
    import data_utils as db
    import connection_design as conn
    import calculation_report as rep
except ImportError as e:
    st.error(f"⚠️ Error importing modules: {e}")
    st.stop()

# =============================================================================
# 1. PAGE CONFIG & STYLING
# =============================================================================
st.set_page_config(page_title="Beam Insight V16 (Verified)", layout="wide", page_icon="🏗️")

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
# 2. SIDEBAR INPUTS
# =============================================================================
with st.sidebar:
    st.title("🏗️ Beam Insight V16")
    st.caption("AISC 360-16 Verified")
    st.divider()
    
    # --- 1. Global Settings ---
    method = st.radio("Design Method", ["ASD (Allowable Stress)", "LRFD (Limit State)"])
    is_lrfd = "LRFD" in method
    
    with st.expander("📋 Project Information"):
        proj_name = st.text_input("Project Name", "Factory Extension")
        eng_name = st.text_input("Engineer Name", "Eng. Somchai")

    st.subheader("🛠️ Material & Section")
    sec_name = st.selectbox("Select Section", list(db.STEEL_DB.keys()), index=11)
    p = db.STEEL_DB[sec_name] # Get properties from DB
    
    c_fy, c_e = st.columns(2)
    with c_fy: Fy = st.number_input("Fy (ksc)", value=2500, help="Yield Strength (kg/cm^2)")
    with c_e:  E_mod = st.number_input("E (ksc)", value=2.04e6, format="%e", help="Elastic Modulus")
    
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
# 3. CORE CALCULATIONS (Engine Verified)
# =============================================================================
# 3.1 Properties & Unit Conversion
# Database stores dimensions in mm. Convert to cm for calculations.
L_cm = user_span * 100
Ix, Zx = p['Ix'], p['Zx'] # Ix (cm^4), Zx (cm^3) - Ensure DB is in cm units

# Physical Dimensions (mm -> cm)
h_cm = p['h'] / 10.0  # Depth (d)
tw_cm = p['tw'] / 10.0 # Web Thickness
Aw = h_cm * tw_cm      # Web Area (cm^2) [AISC G2.1: Aw = d * tw]
w_self_kgm = p['w']    # Self Weight (kg/m)

# 3.2 Capacity Calculation (AISC 360-16) 
if is_lrfd:
    label_load = "Factored Load (Wu)"
    # Moment: phi*Mn (phi = 0.90 for Flexure)
    M_cap = 0.90 * Fy * Zx  
    # Shear: phi*Vn (phi = 1.00 for Shear in rolled I-shapes, Eq G2-1)
    V_cap = 1.00 * 0.60 * Fy * Aw 
else:
    label_load = "Safe Load (w)"
    # Moment: Mn/Omega (Omega = 1.67 for Flexure)
    M_cap = (Fy * Zx) / 1.67
    # Shear: Vn/Omega (Omega = 1.50 for Shear in rolled I-shapes, Eq G2-1)
    V_cap = (0.60 * Fy * Aw) / 1.50

# 3.3 Back-Calculation for "Allowable Uniform Load (w)"
def get_capacity(L_m_input):
    L_c = L_m_input * 100
    # 1. Shear Limit: V = wL/2  => w = 2V/L
    w_v = (2 * V_cap / L_c) * 100 # x100 to convert kg/cm -> kg/m
    
    # 2. Moment Limit: M = wL^2/8 => w = 8M/L^2
    w_m = (8 * M_cap / (L_c**2)) * 100 
    
    # 3. Deflection Limit: Delta = 5wL^4 / 384EI
    # => w = (384 E I Delta_allow) / (5 L^4)
    delta_allow = L_c / defl_lim_val
    w_d = (delta_allow * 384 * E_mod * Ix) / (5 * (L_c**4)) * 100
    
    w_gov = min(w_v, w_m, w_d)
    cause = "Shear" if w_gov == w_v else ("Moment" if w_gov == w_m else "Deflection")
    return w_v, w_m, w_d, w_gov, cause

w_max_shear, w_max_moment, w_max_defl, w_max_gov, user_cause = get_capacity(user_span)

# 3.4 Load Determination
if design_mode == "Auto (Max Capacity %)":
    # User Safe Load = (Capacity - SelfWeight) * SafetyFactor
    user_safe_load = (w_max_gov * (target_pct / 100)) - w_self_kgm
    if user_safe_load < 0: user_safe_load = 0
else:
    user_safe_load = user_load_input

# 3.5 Actual Forces Calculation (Include Self Weight)
w_external_kg_cm = user_safe_load / 100
w_self_kg_cm = w_self_kgm / 100
w_total_kg_cm = w_external_kg_cm + w_self_kg_cm 
w_total_kg_m = (w_total_kg_cm * 100) # Total load for display

# Force Calculation
v_act = w_total_kg_cm * L_cm / 2           # V = wL/2
m_act = w_total_kg_cm * L_cm**2 / 8        # M = wL^2/8
d_act = (5 * w_external_kg_cm * L_cm**4) / (384 * E_mod * Ix) # Deflection usually checks Live Load (Ext)
d_all = L_cm / defl_lim_val

# 3.6 Ratios
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
# 4. UI RENDERING (Step-by-Step with Logic Check)
# =============================================================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Beam Analysis", "🔩 Connection Detail", "💾 Load Table", "📝 Report"])

with tab1:
    st.subheader(f"Engineering Analysis: {sec_name}")
    cause_color = "#dc2626" if user_cause == "Shear" else ("#d97706" if user_cause == "Moment" else "#059669")

    # --- Highlight Card ---
    st.markdown(f"""
    <div class="highlight-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div><span class="sub-text">Total Design Load (Ext + Self)</span><br>
                <span class="big-num">{w_total_kg_m:,.0f}</span> <span style="font-size:20px; color:#4b5563;">kg/m</span></div>
            <div style="text-align: right;"><span class="sub-text">Governing Limit</span><br>
                <span style="font-size: 22px; font-weight:bold; color:{cause_color}; background-color:{cause_color}15; padding: 8px 20px; border-radius:15px; border: 1px solid {cause_color}30;">{user_cause.upper()}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Reusable Check Function ---
    def render_check_ratio_with_w(title, act, lim, ratio_label, eq_w, eq_act, eq_ratio):
        ratio = act / lim
        is_pass = ratio <= 1.01 
        status_class = "pass" if is_pass else "fail"
        border_color = "#10b981" if is_pass else "#ef4444"

        st.markdown(f"""
        <div class="detail-card" style="border-top-color: {border_color}">
            <span class="status-badge {status_class}">{'PASS' if is_pass else 'FAIL'}</span>
            <h4 style="margin:0; color:#374151;">{title}</h4>
            <div style="margin-top:10px;">
                <small style="color:#6b7280;">Usage Ratio ({ratio_label}):</small>
                <div style="font-size:24px; font-weight:700; color:{border_color};">{ratio:.3f}</div>
                <small style="color:#6b7280;">Act: {act:,.0f} / Cap: {lim:,.0f}</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
        # Expander with Logic Explanation
        with st.expander(f"View {title} Step-by-Step"):
            st.info(f"**Step 1: Calculate Max Allowable Load (w)** [AISC 360-16]")
            st.latex(eq_w)
            st.divider()
            st.info(f"**Step 2: Check Actual Force vs Capacity**")
            st.latex(eq_act)
            st.latex(eq_ratio)

    c1, c2, c3 = st.columns(3)
    
    # 1. SHEAR MATH
    shear_const = 1.0 if is_lrfd else 1.50
    shear_method = r"\phi = 1.0" if is_lrfd else r"\Omega = 1.50"
    with c1:
        render_check_ratio_with_w(
            "Shear Check (V)", v_act, V_cap, "V/V_cap",
            fr"w_{{lim}} = \frac{{2 (\frac{{0.6 F_y A_w}}{{{shear_method}}})}}{{L}} = \frac{{2 \cdot {V_cap:,.0f}}}{{{L_cm:,.0f}}} \times 100 = {w_max_shear:,.0f} \text{{ kg/m}}",
            fr"\begin{{aligned}} V_{{cap}} &= {V_cap:,.0f} \text{{ kg}} \quad (\text{{using }} A_w = {Aw:.2f} \text{{ cm}}^2) \\ V_{{act}} &= \frac{{w_{{total}} L}}{{2}} = \frac{{{w_total_kg_m:,.0f} \times {user_span}}}{{2}} = {v_act:,.0f} \text{{ kg}} \end{{aligned}}",
            fr"\text{{Ratio}} = \frac{{{v_act:,.0f}}}{{{V_cap:,.0f}}} = \mathbf{{{v_ratio:.3f}}}"
        )
    
    # 2. MOMENT MATH
    moment_const = 0.9 if is_lrfd else 1.67
    moment_method = r"\phi = 0.9" if is_lrfd else r"\Omega = 1.67"
    with c2:
        render_check_ratio_with_w(
            "Moment Check (M)", m_act/100, M_cap/100, "M/M_cap",
            fr"w_{{lim}} = \frac{{8 (\frac{{F_y Z_x}}{{{moment_method}}})}}{{L^2}} = \frac{{8 \cdot {M_cap:,.0f}}}{{{L_cm:,.0f}^2}} \times 100 = {w_max_moment:,.0f} \text{{ kg/m}}",
            fr"\begin{{aligned}} M_{{cap}} &= {M_cap/100:,.0f} \text{{ kg-m}} \quad (\text{{Plastic Moment }} Z_x) \\ M_{{act}} &= \frac{{w_{{total}} L^2}}{{8}} = \frac{{{w_total_kg_m:,.0f} \times {user_span}^2}}{{8}} = {m_act/100:,.0f} \text{{ kg-m}} \end{{aligned}}",
            fr"\text{{Ratio}} = \frac{{{m_act/100:,.0f}}}{{{M_cap/100:,.0f}}} = \mathbf{{{m_ratio:.3f}}}"
        )

    # 3. DEFLECTION MATH
    with c3:
        render_check_ratio_with_w(
            "Deflection Check (Δ)", d_act, d_all, "Δ/Δ_allow",
            fr"w_{{lim}} = \frac{{384 E I \Delta_{{all}}}}{{5 L^4}} = \frac{{384 \cdot {E_mod:.2e} \cdot {Ix} \cdot {d_all:.2f}}}{{5 \cdot {L_cm:,.0f}^4}} \times 100 = {w_max_defl:,.0f}",
            fr"\begin{{aligned}} \Delta_{{allow}} &= L/{defl_lim_val} = {d_all:.2f} \text{{ cm}} \\ \Delta_{{act}} &= \frac{{5 w_{{ext}} L^4}}{{384 E I}} = {d_act:.3f} \text{{ cm}} \end{{aligned}}",
            fr"\text{{Ratio}} = \frac{{{d_act:.3f}}}{{{d_all:.3f}}} = \mathbf{{{d_ratio:.3f}}}"
        )

    # --- Plotting ---
    st.markdown("### 📈 Capacity Envelope Curve")
    spans_plot = np.linspace(2, 12, 100)
    data_env = [get_capacity(s) for s in spans_plot]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spans_plot, y=[d[0] for d in data_env], name='Shear Limit', line=dict(color='#ef4444', dash='dash')))
    fig.add_trace(go.Scatter(x=spans_plot, y=[d[1] for d in data_env], name='Moment Limit', line=dict(color='#f59e0b', dash='dash')))
    fig.add_trace(go.Scatter(x=spans_plot, y=[d[2] for d in data_env], name='Deflection Limit', line=dict(color='#3b82f6', dash='dash')))
    fig.add_trace(go.Scatter(x=spans_plot, y=[d[3] for d in data_env], name='Safe Envelope', fill='tozeroy', fillcolor='rgba(37, 99, 235, 0.1)', line=dict(color='#1e40af', width=4)))
    fig.add_trace(go.Scatter(x=[user_span], y=[w_total_kg_m], mode='markers+text', name='Design Point', text=[f" ({user_span}m, {w_total_kg_m:,.0f})"], textposition="top right", marker=dict(color='red', size=12, symbol='diamond')))
    fig.update_layout(height=450, margin=dict(t=20, b=20, l=20, r=20), xaxis_title="Span Length (m)", yaxis_title="Load (kg/m)")
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption(f"Note: Moment Capacity assumes the beam is Compact and Fully Braced ($L_b = 0$). Calculation based on AISC 360-16.")

with tab2:
    conn_result = conn.render_connection_tab(V_design=v_act, method=method, is_lrfd=is_lrfd, section_data=p, conn_type=conn_type)

with tab3:
    st.markdown("### 🏗️ Span-Load Reference Table")
    df_tbl = pd.DataFrame([[s, get_capacity(s)[3], get_capacity(s)[4]] for s in np.arange(2.0, 12.5, 0.5)], columns=["Span (m)", "Max Load (kg/m)", "Control"])
    st.dataframe(df_tbl.style.format({"Span (m)": "{:.1f}", "Max Load (kg/m)": "{:,.0f}"}), use_container_width=True)

with tab4:
    if conn_result: rep.render_report_tab({'name': proj_name, 'eng': eng_name, 'sec': sec_name, 'method': method}, beam_res, conn_result)
    else: st.warning("⚠️ Please configure connection in Tab 2.")

st.divider(); st.caption("Beam Insight V16 (Verified) | Professional Engineering Software")
