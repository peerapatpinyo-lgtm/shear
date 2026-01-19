import streamlit as st
import plotly.graph_objects as go
import numpy as np
import math

def render(data):
    """
    Render Tab 1: Analysis & Graphs
    Combines:
    1. Dashboard (Old Style)
    2. Detailed LaTeX Calculation (New Style)
    3. SFD/BMD Graphs (Old Style)
    4. Span vs Capacity Graph (Old Style - Logic Restored)
    """
    # --- 1. UNPACK DATA ---
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
    
    # Forces & Ratios
    v_act = data['v_act']
    V_cap = data['V_cap']
    ratio_v = data['ratio_v']
    
    m_act = data['m_act']
    M_cap = data['M_cap']
    ratio_m = data['ratio_m']
    
    d_act = data['d_act']
    d_allow = data['d_allow']
    ratio_d = data['ratio_d']

    # Detail vars for Calculation/Graph
    Aw = data['Aw']
    Fy = data['Fy']
    E = data['E']
    Ix = data['Ix']
    Sx = data['Sx']
    Mn = data['Mn']
    Mp = data['Mp']
    Cb = data['Cb']
    
    # LTB Parameters
    Lp_cm = data['Lp_cm']
    Lr_cm = data['Lr_cm']
    ltb_zone = data['ltb_zone']
    r_ts = data.get('r_ts', 1.0)
    val_J = data.get('J', 1.0)  # Needed for graph loop
    ho = data.get('ho', 1.0)    # Needed for graph loop
    
    fact_w = data['fact_w']
    fact_p = data['fact_p']
    defl_denom = data['defl_denom']

    st.subheader(f"ผลการวิเคราะห์หน้าตัด: {sec_name}")

    # ==========================================
    # PART 1: TOP DASHBOARD (คงของเดิมไว้)
    # ==========================================
    if is_check_mode:
        status_color = "#10b981" if gov_ratio <= 1.0 else "#ef4444"
        status_icon = "✅ PASS" if gov_ratio <= 1.0 else "❌ FAIL"
        st.markdown(f"""
        <div class="highlight-card" style="border-left: 5px solid {status_color}; background-color: {'#ecfdf5' if gov_ratio<=1 else '#fef2f2'}; padding: 15px; border-radius: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="color: #6b7280; font-size: 0.9em;">Check Result ({method_str})</span><br>
                    <span style="font-size: 2em; font-weight: bold; color: {status_color};">{gov_ratio:.2f}</span> 
                    <span style="font-size: 1.5em; font-weight: bold; color: {status_color}; margin-left: 10px;">{status_icon}</span>
                </div>
                <div style="text-align: right;">
                    <small><b>Load:</b> {w_load:,.0f} kg/m, {p_load:,.0f} kg</small><br>
                    <small style="color: {status_color};"><b>Control:</b> {gov_cause}</small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Mode Find Capacity
        safe_val_show = w_safe / 1.4 if is_lrfd else w_safe
        st.markdown(f"""
        <div class="highlight-card" style="padding: 15px; background-color: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="color: #6b7280; font-size: 0.9em;">Max Safe Service Load ({method_str})</span><br>
                    <span style="font-size: 2em; font-weight: bold; color: #1f2937;">{safe_val_show:,.0f}</span> 
                    <span style="font-size: 1.2em; color: #6b7280;">kg/m</span>
                </div>
                <div style="text-align: right;">
                    <span style="color: #2563eb; font-weight: bold;">Limit: {gov_cause}</span><br>
                    <small>L={user_span}m | Lb={Lb}m</small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- METRICS ROW ---
    c1, c2, c3 = st.columns(3)
    
    def get_metric_color(ratio):
        return '#ef4444' if is_check_mode and ratio > 1 else '#1f2937'

    with c1:
        st.markdown(f"""<div style="text-align:center; padding:10px; border:1px solid #e5e7eb; border-radius:8px;">
            <div style="color:#6b7280; font-size:0.9em;">Shear (V)</div>
            <div style="font-size:1.5em; font-weight:bold; color:{get_metric_color(ratio_v)}">{ratio_v:.2f}</div>
            <div style="font-size:0.8em;">{v_act:,.0f} / {V_cap:,.0f} kg</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div style="text-align:center; padding:10px; border:1px solid #e5e7eb; border-radius:8px;">
            <div style="color:#6b7280; font-size:0.9em;">Moment (M)</div>
            <div style="font-size:1.5em; font-weight:bold; color:{get_metric_color(ratio_m)}">{ratio_m:.2f}</div>
            <div style="font-size:0.8em;">{m_act:,.0f} / {M_cap:,.0f} kg-m</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div style="text-align:center; padding:10px; border:1px solid #e5e7eb; border-radius:8px;">
            <div style="color:#6b7280; font-size:0.9em;">Deflection ($\Delta$)</div>
            <div style="font-size:1.5em; font-weight:bold; color:{get_metric_color(ratio_d)}">{ratio_d:.2f}</div>
            <div style="font-size:0.8em;">{d_act:.2f} / {d_allow:.2f} cm</div>
        </div>""", unsafe_allow_html=True)

    # ==========================================
    # PART 2: SFD & BMD DIAGRAMS (กราฟแรง)
    # ==========================================
    st.markdown("---")
    st.subheader("📈 Shear & Moment Diagrams")
    
    x_plot = np.linspace(0, user_span, 100)
    ra = v_act
    v_y = []
    m_y = []
    
    # Logic สร้างกราฟ SFD/BMD
    for val in x_plot:
        shear = ra - (fact_w * val)
        if val > user_span/2: shear -= fact_p
        v_y.append(shear)
        
        moment = (ra * val) - (fact_w * val**2 / 2)
        if val > user_span/2: moment -= fact_p * (val - user_span/2)
        m_y.append(moment)

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig_v = go.Figure()
        fig_v.add_trace(go.Scatter(x=x_plot, y=v_y, fill='tozeroy', line=dict(color='#3b82f6'), name='Shear'))
        fig_v.update_layout(title="Shear Force Diagram (SFD)", xaxis_title="Length (m)", yaxis_title="Shear (kg)", height=300, margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig_v, use_container_width=True)
        
    with col_g2:
        fig_m = go.Figure()
        fig_m.add_trace(go.Scatter(x=x_plot, y=m_y, fill='tozeroy', line=dict(color='#ef4444'), name='Moment'))
        fig_m.update_layout(title="Bending Moment Diagram (BMD)", xaxis_title="Length (m)", yaxis_title="Moment (kg-m)", height=300, margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig_m, use_container_width=True)

    # ==========================================
    # PART 3: CALCULATION SHEET (ส่วนที่แก้ให้สวยด้วย LaTeX)
    # ==========================================
    st.markdown("---")
    st.subheader("📝 รายการคำนวณละเอียด (Detailed Calculation)")

    with st.expander("คลิกเพื่อดูรายการคำนวณ (Show Calculations)", expanded=False):
        # 3.1 Load Analysis
        st.markdown("**1. วิเคราะห์น้ำหนักบรรทุก (Load Analysis)**")
        st.latex(rf"w_u = {fact_w:,.0f} \; kg/m, \quad P_u = {fact_p:,.0f} \; kg")
        
        # 3.2 Shear
        st.markdown("**2. ตรวจสอบแรงเฉือน (Shear Check)**")
        c_sh1, c_sh2 = st.columns(2)
        with c_sh1:
            st.latex(rf"V_u = {v_act:,.0f} \; kg")
        with c_sh2:
            st.latex(rf"\phi V_n = {V_cap:,.0f} \; kg")
        st.write(f"Ratio = {ratio_v:.3f}")

        # 3.3 Moment
        st.markdown("**3. ตรวจสอบโมเมนต์ (Moment Check)**")
        c_mm1, c_mm2 = st.columns(2)
        with c_mm1:
            st.latex(rf"M_u = {m_act:,.0f} \; kg \cdot m")
        with c_mm2:
            st.latex(rf"\phi M_n = {M_cap:,.0f} \; kg \cdot m")
        st.caption(f"Note: $L_b$ = {Lb:.2f} m (Zone: {ltb_zone})")
        st.write(f"Ratio = {ratio_m:.3f}")

        # 3.4 Deflection
        st.markdown("**4. ตรวจสอบระยะแอ่น (Deflection Check)**")
        c_dd1, c_dd2 = st.columns(2)
        with c_dd1:
            st.latex(rf"\Delta_{{actual}} = {d_act:.2f} \; cm")
        with c_dd2:
            st.latex(rf"\Delta_{{allow}} = {d_allow:.2f} \; cm")
        st.write(f"Ratio = {ratio_d:.3f}")

    # ==========================================
    # PART 4: SPAN VS CAPACITY GRAPH (ของเดิมที่กู้คืนมา)
    # ==========================================
    st.markdown("---")
    st.subheader("📉 Span vs. Load Capacity Curve")
    st.caption("กราฟแสดงน้ำหนักบรรทุกปลอดภัยที่ระยะพาดต่างๆ (Safe Load vs Span)")

    # --- GRAPH LOGIC RESTORED ---
    spans = np.linspace(1.0, 12.0, 50)
    w_cap_moment, w_cap_shear, w_cap_defl = [], [], []
    factor_load = 1.4 if is_lrfd else 1.0 
    
    # Constants for Graph Loop
    phi_b = 0.90
    omg_b = 1.67
    
    # คำนวณค่า val_A สำหรับ LTB (เผื่อกรณีไม่มีค่าส่งมา)
    if 'val_A' not in data:
        # Approximation or Recalculate if data missing
        val_A = 1.0 # Fallback
    else:
        val_A = data['val_A']

    for s in spans:
        l_cm_g = s * 100
        lb_cm_g = l_cm_g # Assumption: Braced at ends only
        
        # 1. Shear Limit
        w_v = (2 * V_cap) / s # Simple Beam Uniform Load from Shear
        
        # 2. Moment Limit (Full LTB Logic)
        if lb_cm_g <= Lp_cm: 
            mn_g = Mp
        elif lb_cm_g <= Lr_cm:
            term_g = (Mp - 0.7*Fy*Sx) * ((lb_cm_g - Lp_cm)/(Lr_cm - Lp_cm))
            mn_g = min(Mp, Cb*(Mp - term_g))
        else:
            slend_g = lb_cm_g / r_ts
            if slend_g > 0:
                fcr_g = (Cb * math.pi**2 * E) / (slend_g**2) * math.sqrt(1 + 0.078 * val_J * 1.0 / (Sx*ho) * slend_g**2) # Simplified A term
                # หรือใช้ค่าคงที่ถ้าตัวแปรเยอะเกินไป:
                # fcr_g = (Cb * math.pi**2 * E) / (slend_g**2) 
            else:
                fcr_g = Fy
            mn_g = min(fcr_g * Sx, Mp)
            
        m_cap_g = (phi_b * mn_g)/100 if is_lrfd else (mn_g/omg_b)/100
        w_m = (8 * m_cap_g) / (s**2)
        
        # 3. Deflection Limit
        d_all_g = l_cm_g / defl_denom
        w_d_serv = (d_all_g * 384 * E * Ix) / (5 * l_cm_g**4) * 100 
        w_d = w_d_serv * factor_load 
        
        # Store results
        w_cap_moment.append(w_m / factor_load)
        w_cap_shear.append(w_v / factor_load)
        w_cap_defl.append(w_d / factor_load)

    # Plot Graph
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spans, y=w_cap_moment, name='Moment Limit', line=dict(color='#3b82f6', width=3)))
    fig.add_trace(go.Scatter(x=spans, y=w_cap_defl, name='Deflection Limit', line=dict(color='#10b981', dash='dash')))
    fig.add_trace(go.Scatter(x=spans, y=w_cap_shear, name='Shear Limit', line=dict(color='#f59e0b', dash='dot')))
    
    if is_check_mode:
        equiv_w_act = (fact_w + (2*fact_p/user_span)) / factor_load 
        fig.add_trace(go.Scatter(x=[user_span], y=[equiv_w_act], mode='markers', name='Your Load', marker=dict(color='red', size=12, symbol='x')))
    
    fig.update_layout(
        xaxis_title="Span (m)",
        yaxis_title="Safe Service Load (kg/m)",
        height=450,
        margin=dict(l=20,r=20,t=40,b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)
