# tab1_analysis.py
import streamlit as st
import plotly.graph_objects as go
import numpy as np
import math

def render(data):
    """
    Render Tab 1: Analysis & Graphs
    data: Dictionary containing all calculation results and inputs
    """
    # Unpack necessary data for cleaner code
    is_check_mode = data['is_check_mode']
    gov_ratio = data['gov_ratio']
    method_str = data['method_str']
    w_load = data['w_load']
    p_load = data['p_load']
    gov_cause = data['gov_cause']
    w_safe = data['w_safe']
    is_lrfd = data['is_lrfd']
    user_span = data['user_span']
    Lb = data['Lb']
    sec_name = data['sec_name']
    
    # Ratios and Forces
    ratio_v = data['ratio_v']
    v_act = data['v_act']
    V_cap = data['V_cap']
    
    ratio_m = data['ratio_m']
    m_act = data['m_act']
    M_cap = data['M_cap']
    
    ratio_d = data['ratio_d']
    d_act = data['d_act']
    d_allow = data['d_allow']
    
    # Calculation details
    Aw = data['Aw']
    Fy = data['Fy']
    Ix = data['Ix']
    defl_denom = data['defl_denom']
    Lp_cm = data['Lp_cm']
    Lr_cm = data['Lr_cm']
    ltb_zone = data['ltb_zone']
    Mn = data['Mn']
    
    st.subheader(f"Results for: {sec_name}")

    # --- TOP CARD ---
    if is_check_mode:
        status_color = "#10b981" if gov_ratio <= 1.0 else "#ef4444"
        status_icon = "✅ PASS" if gov_ratio <= 1.0 else "❌ FAIL"
        st.markdown(f"""
        <div class="highlight-card" style="border-left-color: {status_color};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span class="sub-text">Check Result ({method_str})</span><br>
                    <span class="big-num" style="color:{status_color}">{gov_ratio:.2f}</span> 
                    <span style="font-size:20px; font-weight:bold; color:{status_color}">{status_icon}</span>
                </div>
                <div style="text-align: right;">
                    <small><b>Load Case:</b> {w_load:,.0f} kg/m, {p_load:,.0f} kg</small><br>
                    <small><b>Control:</b> {gov_cause}</small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        safe_val_show = w_safe / 1.4 if is_lrfd else w_safe
        st.markdown(f"""
        <div class="highlight-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span class="sub-text">Max Safe Service Load ({method_str})</span><br>
                    <span class="big-num">{safe_val_show:,.0f}</span> <span style="font-size:24px; color:#6b7280;">kg/m</span>
                </div>
                <div style="text-align: right;">
                    <span class="sub-text" style="color:#2563eb;">Limit: {gov_cause}</span><br>
                    <small>L={user_span}m | Lb={Lb}m</small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- METRICS ROW ---
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="detail-card">
            <h4 style="margin:0;">Shear (V)</h4>
            <div style="font-size:24px; font-weight:700; color:{'#ef4444' if is_check_mode and ratio_v>1 else '#1f2937'}">
                {ratio_v:.2f} <small style="font-size:14px; color:#9ca3af;">(Ratio)</small>
            </div>
            <div style="margin-top:8px; font-size:14px;">
                <div>Act*: <b>{v_act:,.0f}</b> kg</div>
                <div>Cap: <b>{V_cap:,.0f}</b> kg</div>
            </div>
        </div>""", unsafe_allow_html=True)
    
    with c2:
        st.markdown(f"""<div class="detail-card">
            <h4 style="margin:0;">Moment (M)</h4>
            <div style="font-size:24px; font-weight:700; color:{'#ef4444' if is_check_mode and ratio_m>1 else '#1f2937'}">
                {ratio_m:.2f} <small style="font-size:14px; color:#9ca3af;">(Ratio)</small>
            </div>
            <div style="margin-top:8px; font-size:14px;">
                <div>Act*: <b>{m_act:,.0f}</b> kg-m</div>
                <div>Cap: <b>{M_cap:,.0f}</b> kg-m</div>
            </div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""<div class="detail-card">
            <h4 style="margin:0;">Deflection ($\Delta$)</h4>
            <div style="font-size:24px; font-weight:700; color:{'#ef4444' if is_check_mode and ratio_d>1 else '#1f2937'}">
                {ratio_d:.2f} <small style="font-size:14px; color:#9ca3af;">(Ratio)</small>
            </div>
            <div style="margin-top:8px; font-size:14px;">
                <div>Act*: <b>{d_act:.2f}</b> cm</div>
                <div>All: <b>{d_allow:.2f}</b> cm</div>
            </div>
        </div>""", unsafe_allow_html=True)
    
    if not is_check_mode:
        st.caption("*Act values in 'Find Capacity' mode represent the forces at the calculated Max Load.")

    # --- CALCULATION SHEET ---
    st.subheader("🧮 Calculation Sheet")
    with st.expander("📄 View Detailed Engineering Calculations", expanded=True):
        
        v_label_calc = "\phi V_n" if is_lrfd else "V_n / \Omega"
        m_label_calc = "\phi M_n" if is_lrfd else "M_n / \Omega"
        
        c_calc1, c_calc2 = st.columns(2)
        
        with c_calc1:
            st.markdown(f"""
            <div class="calc-sheet">
                <div class="calc-header">1. Shear Capacity ({method_str})</div>
                <div class="calc-row">
                    <span class="calc-label">Area Web ($A_w = h \cdot t_w$)</span>
                    <span class="calc-val">{Aw:.2f} cm²</span>
                </div>
                <div class="calc-row">
                    <span class="calc-label">Nominal Shear ($V_n = 0.6 F_y A_w$)</span>
                    <span class="calc-val">{0.6*Fy*Aw:,.0f} kg</span>
                </div>
                <div class="calc-row">
                    <span class="calc-label">Design Capacity ({v_label_calc})</span>
                    <span class="calc-val" style="color:#166534; font-weight:bold;">{V_cap:,.0f} kg</span>
                </div>
                <div class="calc-row">
                    <span class="calc-label">Actual Shear ($V_u$)</span>
                    <span class="calc-val" style="color:#1e40af;">{v_act:,.0f} kg</span>
                </div>
                <div class="calc-formula">
                    Ratio = {v_act:,.0f} / {V_cap:,.0f} = <b>{ratio_v:.3f}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="calc-sheet">
                <div class="calc-header">3. Serviceability (Deflection)</div>
                <div class="calc-row">
                    <span class="calc-label">Moment of Inertia ($I_x$)</span>
                    <span class="calc-val">{Ix:,.0f} cm⁴</span>
                </div>
                <div class="calc-row">
                    <span class="calc-label">Limit (L/{defl_denom})</span>
                    <span class="calc-val" style="color:#166534;">{d_allow:.2f} cm</span>
                </div>
                <div class="calc-row">
                    <span class="calc-label">Actual Deflection ($\Delta$)</span>
                    <span class="calc-val" style="color:#1e40af;">{d_act:.2f} cm</span>
                </div>
                <div class="calc-formula">
                    Ratio = {d_act:.2f} / {d_allow:.2f} = <b>{ratio_d:.3f}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with c_calc2:
            st.markdown(f"""
            <div class="calc-sheet">
                <div class="calc-header">2. Flexural Capacity ({method_str})</div>
                <div class="calc-row">
                    <span class="calc-label">Unbraced Length ($L_b$)</span>
                    <span class="calc-val">{Lb:.2f} m</span>
                </div>
                <div class="calc-row">
                    <span class="calc-label">LTB Limits ($L_p$, $L_r$)</span>
                    <span class="calc-val">{Lp_cm/100:.2f} m, {Lr_cm/100:.2f} m</span>
                </div>
                <div class="calc-row">
                    <span class="calc-label">State</span>
                    <span class="calc-val" style="color:#b45309;">{ltb_zone}</span>
                </div>
                <div class="calc-row">
                    <span class="calc-label">Nominal Moment ($M_n$)</span>
                    <span class="calc-val">{Mn/100:,.0f} kg-m</span>
                </div>
                <div class="calc-row">
                    <span class="calc-label">Design Capacity ({m_label_calc})</span>
                    <span class="calc-val" style="color:#166534; font-weight:bold;">{M_cap:,.0f} kg-m</span>
                </div>
                <div class="calc-row">
                    <span class="calc-label">Actual Moment ($M_u$)</span>
                    <span class="calc-val" style="color:#1e40af;">{m_act:,.0f} kg-m</span>
                </div>
                <div class="calc-formula">
                    Ratio = {m_act:,.0f} / {M_cap:,.0f} = <b>{ratio_m:.3f}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # --- GRAPH GENERATION (Local Logic) ---
    st.markdown("### 📉 Span vs. Load Capacity Curve")
    spans = np.linspace(1.0, 12.0, 50)
    w_cap_moment, w_cap_shear, w_cap_defl = [], [], []
    factor_load = 1.4 if is_lrfd else 1.0 
    
    # Graph Constants from data
    Mp = data['Mp']
    Sx = data['Sx']
    E = data['E']
    Cb = data['Cb']
    val_A = data['val_A']
    r_ts = data['r_ts']
    phi_b = 0.90
    omg_b = 1.67
    
    for s in spans:
        l_cm_g = s * 100
        lb_cm_g = l_cm_g # Assuming Lb = Span for the graph
        
        w_v = (2 * V_cap) / s
        
        if lb_cm_g <= Lp_cm: mn_g = Mp
        elif lb_cm_g <= Lr_cm:
            term_g = (Mp - 0.7*Fy*Sx) * ((lb_cm_g - Lp_cm)/(Lr_cm - Lp_cm))
            mn_g = min(Mp, Cb*(Mp - term_g))
        else:
            slend_g = lb_cm_g / r_ts
            fcr_g = (Cb * math.pi**2 * E) / (slend_g**2) * math.sqrt(1 + 0.078 * val_A * slend_g**2)
            mn_g = min(fcr_g * Sx, Mp)
            
        m_cap_g = (phi_b * mn_g)/100 if is_lrfd else (mn_g/omg_b)/100
        w_m = (8 * m_cap_g) / (s**2)
        
        d_all_g = l_cm_g / defl_denom
        w_d_serv = (d_all_g * 384 * E * Ix) / (5 * l_cm_g**4) * 100
        w_d = w_d_serv * factor_load 
        
        w_cap_moment.append(w_m / factor_load)
        w_cap_shear.append(w_v / factor_load)
        w_cap_defl.append(w_d / factor_load)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spans, y=w_cap_moment, name='Moment Limit', line=dict(color='#3b82f6', width=3)))
    fig.add_trace(go.Scatter(x=spans, y=w_cap_defl, name='Deflection Limit', line=dict(color='#10b981', dash='dash')))
    fig.add_trace(go.Scatter(x=spans, y=w_cap_shear, name='Shear Limit', line=dict(color='#f59e0b', dash='dot')))
    
    if is_check_mode:
        fact_w = data.get('fact_w', 0)
        fact_p = data.get('fact_p', 0)
        equiv_w_act = (fact_w + (2*fact_p/user_span)) / factor_load 
        fig.add_trace(go.Scatter(x=[user_span], y=[equiv_w_act], mode='markers', name='Your Load', marker=dict(color='red', size=12, symbol='x')))
    
    fig.update_layout(title="Safe Service Load vs. Span", xaxis_title="Span (m)", yaxis_title="Load (kg/m)", height=450)
    st.plotly_chart(fig, use_container_width=True)
