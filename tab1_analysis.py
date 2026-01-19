import streamlit as st
import plotly.graph_objects as go
import numpy as np

def render(data):
    """
    Render Tab 1: Analysis & Graphs + Detailed Calculation Sheet
    """
    # --- UNPACK DATA ---
    # ดึงค่าที่จำเป็นออกมาเพื่อความสะดวกในการเรียกใช้
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
    
    is_lrfd = data['is_lrfd']
    is_check = data['is_check_mode']
    
    E = data['E']
    Ix = data['Ix']
    Fy = data['Fy']
    L_cm = user_span * 100
    
    # ==========================================
    # 1. VISUALIZATION (GRAPHS) - ส่วนกราฟแสดงผล
    # ==========================================
    st.subheader("📈 Shear & Moment Diagrams")
    
    # สร้างข้อมูลกราฟ
    x = np.linspace(0, user_span, 100)
    
    # Shear Diagram Equation (V)
    # V(x) = RA - w*x - (P if x > L/2)
    ra = v_act # Reaction (Simple span सि mmerty)
    v_y = []
    for val in x:
        shear = ra - (fact_w * val)
        if val > user_span/2:
            shear -= fact_p
        v_y.append(shear)
        
    # Moment Diagram Equation (M)
    # M(x) = RA*x - (w*x^2)/2 - (P*(x-L/2) if x > L/2)
    m_y = []
    for val in x:
        moment = (ra * val) - (fact_w * val**2 / 2)
        if val > user_span/2:
            moment -= fact_p * (val - user_span/2)
        m_y.append(moment)

    # Plotting
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        fig_v = go.Figure()
        fig_v.add_trace(go.Scatter(x=x, y=v_y, fill='tozeroy', line=dict(color='#3b82f6'), name='Shear'))
        fig_v.update_layout(title="Shear Force Diagram (SFD)", xaxis_title="Length (m)", yaxis_title="Shear (kg)", height=300)
        st.plotly_chart(fig_v, use_container_width=True)
        
    with col_g2:
        fig_m = go.Figure()
        fig_m.add_trace(go.Scatter(x=x, y=m_y, fill='tozeroy', line=dict(color='#ef4444'), name='Moment'))
        fig_m.update_layout(title="Bending Moment Diagram (BMD)", xaxis_title="Length (m)", yaxis_title="Moment (kg-m)", height=300)
        st.plotly_chart(fig_m, use_container_width=True)

    # ==========================================
    # 2. DETAILED CALCULATION SHEET - ส่วนคำนวณละเอียด
    # ==========================================
    st.markdown("---")
    st.subheader("📝 Detailed Calculation Sheet")
    st.caption("แสดงรายการคำนวณอย่างละเอียดตามมาตรฐานวิศวกรรม")

    # CSS สำหรับกล่องผลลัพธ์
    st.markdown("""
    <style>
    .result-box { padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 5px solid; }
    .pass { background-color: #f0fdf4; border-color: #22c55e; color: #166534; }
    .fail { background-color: #fef2f2; border-color: #ef4444; color: #991b1b; }
    .calc-step { margin-left: 20px; font-family: 'Sarabun', sans-serif; color: #334155; }
    </style>
    """, unsafe_allow_html=True)

    # --- SECTION A: LOAD ANALYSIS ---
    with st.expander("1️⃣ Load Analysis (วิเคราะห์น้ำหนักบรรทุก)", expanded=True):
        col_load1, col_load2 = st.columns([1, 1])
        
        with col_load1:
            st.markdown("##### **Load Factors**")
            if is_lrfd:
                st.latex(r"\text{Method: LRFD (Limit State)}")
                st.write("Factor Load Combination:")
                st.latex(r"U = 1.4(DL + LL)")
                factor = 1.4
            else:
                st.latex(r"\text{Method: ASD (Allowable Stress)}")
                st.write("Factor Load:")
                st.latex(r"U = 1.0(DL + LL)")
                factor = 1.0
        
        with col_load2:
            st.markdown("##### **Factored Loads**")
            # Uniform Load
            st.write("**1. Uniform Load ($w_u$):**")
            st.latex(rf"w_u = {factor} \times {w_load:,.0f} = \mathbf{{{fact_w:,.0f}}} \; kg/m")
            
            # Point Load
            st.write("**2. Point Load ($P_u$):**")
            st.latex(rf"P_u = {factor} \times {p_load:,.0f} = \mathbf{{{fact_p:,.0f}}} \; kg")

    # --- SECTION B: SHEAR CHECK ---
    with st.expander("2️⃣ Shear Check (ตรวจสอบแรงเฉือน)", expanded=True):
        c_s1, c_s2 = st.columns(2)
        
        with c_s1:
            st.markdown("**Demand ($V_{max}$)**")
            st.write("สูตรคำนวณแรงเฉือนสูงสุด (Simple Beam):")
            st.latex(r"V_{max} = \frac{w_u L}{2} + \frac{P_u}{2}")
            st.markdown("**Substituting values:**")
            st.latex(rf"V_{{max}} = \frac{{{fact_w:,.0f} \cdot {user_span}}}{{2}} + \frac{{{fact_p:,.0f}}}{{2}}")
            st.latex(rf"V_{{max}} = \mathbf{{{v_act:,.0f}}} \; kg")
            
        with c_s2:
            st.markdown(f"**Capacity ($V_{{design}}$)**")
            if is_lrfd:
                st.latex(r"\phi V_n = \phi (0.6 F_y A_w)")
                st.write(f"(Using $\phi = 1.00$)")
            else:
                st.latex(r"V_n/\Omega = \frac{0.6 F_y A_w}{\Omega}")
                st.write(f"(Using $\Omega = 1.50$)")
            
            st.latex(rf"V_{{design}} = \mathbf{{{V_cap:,.0f}}} \; kg")

        # Result Logic
        ratio_v = v_act / V_cap if V_cap > 0 else 0
        v_status = "PASSED" if ratio_v <= 1.0 else "FAILED"
        v_class = "pass" if ratio_v <= 1.0 else "fail"
        v_icon = "✅" if ratio_v <= 1.0 else "❌"
        
        st.markdown(f"""
        <div class="result-box {v_class}">
            <strong>{v_icon} Shear Result: {v_status}</strong><br>
            Ratio = {v_act:,.0f} / {V_cap:,.0f} = <strong>{ratio_v:.3f}</strong>
        </div>
        """, unsafe_allow_html=True)

    # --- SECTION C: MOMENT CHECK ---
    with st.expander("3️⃣ Moment Check (ตรวจสอบโมเมนต์ดัด)", expanded=True):
        c_m1, c_m2 = st.columns(2)
        
        with c_m1:
            st.markdown("**Demand ($M_{max}$)**")
            st.write("สูตรคำนวณโมเมนต์สูงสุด (Simple Beam):")
            st.latex(r"M_{max} = \frac{w_u L^2}{8} + \frac{P_u L}{4}")
            st.markdown("**Substituting values:**")
            st.latex(rf"M_{{max}} = \frac{{{fact_w:,.0f} \cdot {user_span}^2}}{{8}} + \frac{{{fact_p:,.0f} \cdot {user_span}}}{{4}}")
            st.latex(rf"M_{{max}} = \mathbf{{{m_act:,.0f}}} \; kg \cdot m")
            
        with c_m2:
            st.markdown(f"**Capacity ($M_{{design}}$)**")
            st.caption("ดึงค่าจาก Tab 3 (LTB Analysis)")
            
            if is_lrfd:
                st.latex(r"M_{design} = \phi M_n")
                st.write("(Using $\phi = 0.90$)")
            else:
                st.latex(r"M_{design} = M_n / \Omega")
                st.write("(Using $\Omega = 1.67$)")
                
            st.latex(rf"M_{{design}} = \mathbf{{{M_cap:,.0f}}} \; kg \cdot m")
            
        # Result Logic
        ratio_m = m_act / M_cap if M_cap > 0 else 0
        m_status = "PASSED" if ratio_m <= 1.0 else "FAILED"
        m_class = "pass" if ratio_m <= 1.0 else "fail"
        m_icon = "✅" if ratio_m <= 1.0 else "❌"

        st.markdown(f"""
        <div class="result-box {m_class}">
            <strong>{m_icon} Moment Result: {m_status}</strong><br>
            Ratio = {m_act:,.0f} / {M_cap:,.0f} = <strong>{ratio_m:.3f}</strong>
        </div>
        """, unsafe_allow_html=True)

    # --- SECTION D: DEFLECTION CHECK ---
    with st.expander("4️⃣ Deflection Check (ตรวจสอบระยะแอ่นตัว)", expanded=True):
        st.info("💡 การตรวจสอบระยะแอ่นตัวใช้ Service Load (ไม่มี Factor)")
        
        c_d1, c_d2 = st.columns(2)
        
        with c_d1:
            st.markdown("**Actual Deflection ($\Delta_{actual}$)**")
            st.write("ผลรวมระยะแอ่นตัว (Uniform + Point):")
            st.latex(r"\Delta = \frac{5 w L^4}{384 E I_x} + \frac{P L^3}{48 E I_x}")
            
            # แปลงหน่วยเพื่อแสดงผลการแทนค่า (ใช้ cm)
            # w (kg/m) -> w/100 (kg/cm)
            w_cm = w_load / 100
            
            st.markdown("**Substituting (units in kg, cm):**")
            st.latex(rf"\Delta = \frac{{5({w_cm:.2f})({L_cm:.0f})^4}}{{384({E:,.0f})({Ix:,.0f})}} + \frac{{({p_load:.0f})({L_cm:.0f})^3}}{{48({E:,.0f})({Ix:,.0f})}}")
            st.latex(rf"\Delta_{{actual}} = \mathbf{{{d_act:.2f}}} \; cm")

        with c_d2:
            st.markdown("**Allowable Limit ($\Delta_{allow}$)**")
            st.write(f"Based on criteria L/{data['defl_denom']}:")
            st.latex(rf"\Delta_{{allow}} = \frac{{L}}{{{data['defl_denom']}}} = \frac{{{L_cm:.0f}}}{{{data['defl_denom']}}}")
            st.latex(rf"\Delta_{{allow}} = \mathbf{{{d_allow:.2f}}} \; cm")
            
        # Result Logic
        ratio_d = d_act / d_allow
        d_status = "PASSED" if ratio_d <= 1.0 else "FAILED"
        d_class = "pass" if ratio_d <= 1.0 else "fail"
        d_icon = "✅" if ratio_d <= 1.0 else "❌"

        st.markdown(f"""
        <div class="result-box {d_class}">
            <strong>{d_icon} Deflection Result: {d_status}</strong><br>
            Actual ({d_act:.2f} cm) vs Allowable ({d_allow:.2f} cm) <br>
            Ratio = <strong>{ratio_d:.3f}</strong>
        </div>
        """, unsafe_allow_html=True)
