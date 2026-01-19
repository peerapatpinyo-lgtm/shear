import streamlit as st
import plotly.graph_objects as go
import numpy as np

def render(data):
    """
    Render Tab 1: Analysis & Graphs
    Combines:
    1. Summary Dashboard (Quick View)
    2. Graphs (Visuals)
    3. Detailed Calculation Sheet (Deep Dive)
    """
    # --- 1. UNPACK DATA (ดึงข้อมูล) ---
    user_span = data['user_span']
    w_load = data['w_load']
    p_load = data['p_load']
    fact_w = data['fact_w']
    fact_p = data['fact_p']
    
    v_act = data['v_act']
    m_act = data['m_act']
    d_act = data['d_act']
    d_allow = data['d_allow']
    
    V_cap = data['V_cap']
    M_cap = data['M_cap']
    
    gov_ratio = data['gov_ratio']
    gov_cause = data['gov_cause']
    
    is_lrfd = data['is_lrfd']
    E = data['E']
    Ix = data['Ix']
    L_cm = user_span * 100

    # ==========================================
    # PART 1: SUMMARY DASHBOARD (ของเดิมที่ห้ามหาย)
    # ==========================================
    st.subheader("📊 Analysis Summary")
    
    # กำหนดสีและสถานะ
    if gov_ratio <= 1.0:
        status_color = "green"
        status_icon = "✅"
        status_text = "PASSED"
        bg_color = "#f0fdf4"
        border_color = "#22c55e"
    else:
        status_color = "red"
        status_icon = "❌"
        status_text = "FAILED"
        bg_color = "#fef2f2"
        border_color = "#ef4444"

    # แสดงผลแบบ Card (Custom HTML) เพื่อความสวยงามและชัดเจน
    col_sum1, col_sum2, col_sum3 = st.columns(3)
    
    with col_sum1:
        st.markdown(f"""
        <div style="background:{bg_color}; border:1px solid {border_color}; border-radius:10px; padding:15px; text-align:center;">
            <div style="color:{status_color}; font-size:14px; font-weight:bold;">DESIGN STATUS</div>
            <div style="color:{status_color}; font-size:28px; font-weight:800; margin:5px 0;">{status_icon} {status_text}</div>
            <div style="color:#64748b; font-size:12px;">Overall Check</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_sum2:
        st.markdown(f"""
        <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:15px; text-align:center;">
            <div style="color:#64748b; font-size:14px; font-weight:bold;">MAX RATIO</div>
            <div style="color:#1e293b; font-size:28px; font-weight:800; margin:5px 0;">{gov_ratio:.2f}</div>
            <div style="color:#ef4444; font-size:12px;">Limit ≤ 1.00</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_sum3:
        st.markdown(f"""
        <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:15px; text-align:center;">
            <div style="color:#64748b; font-size:14px; font-weight:bold;">CRITICAL CASE</div>
            <div style="color:#d97706; font-size:24px; font-weight:800; margin:5px 0;">{gov_cause}</div>
            <div style="color:#64748b; font-size:12px;">Governing Factor</div>
        </div>
        """, unsafe_allow_html=True)

    # ==========================================
    # PART 2: GRAPHS (กราฟแสดงผล)
    # ==========================================
    st.divider()
    st.subheader("📈 Shear & Moment Diagrams")
    
    # Graph Logic
    x = np.linspace(0, user_span, 100)
    ra = v_act 
    v_y = []
    m_y = []
    
    for val in x:
        # Shear V(x)
        shear = ra - (fact_w * val)
        if val > user_span/2: shear -= fact_p
        v_y.append(shear)
        
        # Moment M(x)
        moment = (ra * val) - (fact_w * val**2 / 2)
        if val > user_span/2: moment -= fact_p * (val - user_span/2)
        m_y.append(moment)

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig_v = go.Figure()
        fig_v.add_trace(go.Scatter(x=x, y=v_y, fill='tozeroy', line=dict(color='#3b82f6'), name='Shear'))
        fig_v.update_layout(title="Shear Force Diagram (SFD)", xaxis_title="Length (m)", yaxis_title="Shear (kg)", height=300, margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig_v, use_container_width=True)
        
    with col_g2:
        fig_m = go.Figure()
        fig_m.add_trace(go.Scatter(x=x, y=m_y, fill='tozeroy', line=dict(color='#ef4444'), name='Moment'))
        fig_m.update_layout(title="Bending Moment Diagram (BMD)", xaxis_title="Length (m)", yaxis_title="Moment (kg-m)", height=300, margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig_m, use_container_width=True)

    # ==========================================
    # PART 3: DETAILED CALCULATION (ส่วนที่เพิ่มใหม่)
    # ==========================================
    st.divider()
    st.subheader("📝 Detailed Calculation Sheet")
    st.caption("แสดงรายการคำนวณละเอียด (Click เพื่อดูแต่ละหัวข้อ)")
    
    # Style สำหรับกล่องคำนวณ
    st.markdown("""
    <style>
    .result-box { padding: 10px 15px; border-radius: 6px; margin-top: 10px; border-left: 5px solid; font-family: 'Roboto Mono', monospace; font-size: 0.95em; }
    .pass { background-color: #f0fdf4; border-color: #22c55e; color: #166534; }
    .fail { background-color: #fef2f2; border-color: #ef4444; color: #991b1b; }
    </style>
    """, unsafe_allow_html=True)

    # 3.1 Load Analysis
    with st.expander("1️⃣ Load Analysis (วิเคราะห์น้ำหนักบรรทุก)", expanded=False):
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            st.markdown(f"**Method: {data['method_str']}**")
            factor = 1.4 if is_lrfd else 1.0
            st.latex(rf"\text{{Load Factor}} = {factor}")
        with col_l2:
            st.write(f"Uniform Load ($w_u$):")
            st.latex(rf"{factor} \times {w_load:,.0f} = \mathbf{{{fact_w:,.0f}}} \; kg/m")
            st.write(f"Point Load ($P_u$):")
            st.latex(rf"{factor} \times {p_load:,.0f} = \mathbf{{{fact_p:,.0f}}} \; kg")

    # 3.2 Shear Check
    with st.expander("2️⃣ Shear Capacity Check (แรงเฉือน)", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Demand ($V_{u}$):**")
            st.latex(r"V_{max} = \frac{w_u L}{2} + \frac{P_u}{2}")
            st.latex(rf"= \mathbf{{{v_act:,.0f}}} \; kg")
        with c2:
            st.markdown("**Capacity ($V_{design}$):**")
            st.latex(rf"V_{{design}} = \mathbf{{{V_cap:,.0f}}} \; kg")
        
        ratio_v = v_act / V_cap if V_cap > 0 else 0
        v_css = "pass" if ratio_v <= 1.0 else "fail"
        st.markdown(f"""<div class="result-box {v_css}">Shear Ratio = {v_act:,.0f} / {V_cap:,.0f} = <strong>{ratio_v:.3f}</strong></div>""", unsafe_allow_html=True)

    # 3.3 Moment Check
    with st.expander("3️⃣ Moment Capacity Check (โมเมนต์ดัด)", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Demand ($M_{u}$):**")
            st.latex(r"M_{max} = \frac{w_u L^2}{8} + \frac{P_u L}{4}")
            st.latex(rf"= \mathbf{{{m_act:,.0f}}} \; kg\cdot m")
        with c2:
            st.markdown("**Capacity ($M_{design}$):**")
            st.caption(f"Calculated from LTB Analysis (Zone: {data['ltb_zone']})")
            st.latex(rf"M_{{design}} = \mathbf{{{M_cap:,.0f}}} \; kg\cdot m")
            
        ratio_m = m_act / M_cap if M_cap > 0 else 0
        m_css = "pass" if ratio_m <= 1.0 else "fail"
        st.markdown(f"""<div class="result-box {m_css}">Moment Ratio = {m_act:,.0f} / {M_cap:,.0f} = <strong>{ratio_m:.3f}</strong></div>""", unsafe_allow_html=True)

    # 3.4 Deflection Check
    with st.expander("4️⃣ Deflection Check (ระยะแอ่นตัว)", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Actual ($\Delta_{actual}$):**")
            st.latex(r"\Delta = \frac{5 w L^4}{384 EI} + \frac{P L^3}{48 EI}")
            st.latex(rf"= \mathbf{{{d_act:.2f}}} \; cm")
        with c2:
            st.markdown("**Allowable ($\Delta_{allow}$):**")
            st.latex(rf"L/{data['defl_denom']} = {L_cm:.0f}/{data['defl_denom']}")
            st.latex(rf"= \mathbf{{{d_allow:.2f}}} \; cm")
            
        ratio_d = d_act / d_allow
        d_css = "pass" if ratio_d <= 1.0 else "fail"
        st.markdown(f"""<div class="result-box {d_css}">Deflection Ratio = {d_act:.2f} / {d_allow:.2f} = <strong>{ratio_d:.3f}</strong></div>""", unsafe_allow_html=True)
