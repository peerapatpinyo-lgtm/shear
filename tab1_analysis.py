import streamlit as st
import plotly.graph_objects as go
import numpy as np
import math

def render(data):
    """
    Render Tab 1: Analysis & Graphs
    Smart Logic: Switches Calculation Sheet style based on 'Check Mode' vs 'Find Capacity'
    """
    # ==========================================
    # 0. UNPACK DATA
    # ==========================================
    is_check_mode = data['is_check_mode'] # True = Check, False = Find Capacity
    gov_ratio = data['gov_ratio']
    gov_cause = data['gov_cause']
    method_str = data['method_str']
    is_lrfd = data['is_lrfd']
    
    # Loads
    w_load = data['w_load'] # Input Load
    p_load = data['p_load']
    fact_w = data['fact_w']
    fact_p = data['fact_p']
    
    # Geometry & Material
    user_span = data['user_span']
    Lb = data['Lb']
    sec_name = data['sec_name']
    Aw = data['Aw']
    Fy = data['Fy']
    E = data['E']
    Ix = data['Ix']
    Sx = data['Sx']
    Zx = data.get('Zx', Sx)
    
    # Results
    v_act = data['v_act']
    V_cap = data['V_cap']
    m_act = data['m_act']
    M_cap = data['M_cap']
    d_act = data['d_act']
    d_allow = data['d_allow']
    
    # Ratios
    ratio_v = data['ratio_v']
    ratio_m = data['ratio_m']
    ratio_d = data['ratio_d']
    
    # LTB Parameters
    Mn = data['Mn']
    Mp = data['Mp']
    Lp_cm = data['Lp_cm']
    Lr_cm = data['Lr_cm']
    ltb_zone = data['ltb_zone']
    Cb = data.get('Cb', 1.0)
    
    # Constants
    factor_txt = "1.4" if is_lrfd else "1.0"
    load_comb_name = "1.4(DL+LL)" if is_lrfd else "DL+LL"
    defl_denom = data['defl_denom']
    factor_val = 1.4 if is_lrfd else 1.0

    st.subheader(f"ผลการวิเคราะห์หน้าตัด: {sec_name}")

    # ==========================================
    # PART 1: DASHBOARD (คงเดิม)
    # ==========================================
    if is_check_mode:
        # ... (Code Check Mode Dashboard แบบเดิม) ...
        status_color = "#10b981" if gov_ratio <= 1.0 else "#ef4444"
        status_icon = "✅ ผ่าน (PASS)" if gov_ratio <= 1.0 else "❌ ไม่ผ่าน (FAIL)"
        bg_color = "#ecfdf5" if gov_ratio <= 1.0 else "#fef2f2"
        st.markdown(f"""
        <div style="background:{bg_color}; border-left:5px solid {status_color}; padding:15px; border-radius:8px; margin-bottom:20px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h3 style="margin:0; color:{status_color};">{status_icon}</h3>
                    <div style="font-size:1.1em; color:#374151; margin-top:5px;">Ratio Max = <b>{gov_ratio:.2f}</b> ({gov_cause})</div>
                </div>
                <div style="text-align:right; font-size:0.9em; color:#6b7280;">Input Load: {w_load:,.0f} kg/m</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # ... (Code Find Capacity Dashboard แบบเดิม) ...
        safe_load_show = data['w_safe'] / factor_val
        st.markdown(f"""
        <div style="background:#f0f9ff; border-left:5px solid #0284c7; padding:15px; border-radius:8px; margin-bottom:20px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h3 style="margin:0; color:#0284c7;">Max Safe Load: {safe_load_show:,.0f} kg/m</h3>
                    <div style="font-size:1.0em; color:#374151;">(Service Load) Limited by: <b>{gov_cause}</b></div>
                </div>
                <div style="text-align:right; font-size:0.9em; color:#6b7280;">Span = {user_span} m</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Metrics Row
    c1, c2, c3 = st.columns(3)
    def get_metric_color(ratio):
        if not is_check_mode: return '#1f2937' # Black in Find Mode
        return '#ef4444' if ratio > 1 else '#1f2937'

    with c1:
        st.metric("Shear Capacity", f"{V_cap:,.0f} kg", delta_color="off")
    with c2:
        st.metric("Moment Capacity", f"{M_cap:,.0f} kg-m", delta_color="off")
    with c3:
        st.metric("Allowable Deflection", f"{d_allow:.2f} cm", delta_color="off")

    # ==========================================
    # PART 2: DETAILED CALCULATION (แก้ใหม่ แยก 2 ทาง)
    # ==========================================
    st.write("---")
    st.subheader("📝 รายการคำนวณละเอียด (Detailed Calculation)")
    
    with st.expander("แสดงวิธีทำอย่างละเอียด (Click to Expand)", expanded=True):
        st.markdown("""<style>.calc-head { font-weight: bold; font-size: 1.1em; color: #1e40af; margin-bottom: 10px; display:block; } .calc-step { border-bottom: 1px dashed #cbd5e1; padding-bottom: 15px; margin-bottom: 20px; }</style>""", unsafe_allow_html=True)

        # 1. Properties (เหมือนกันทั้ง 2 โหมด)
        st.markdown('<span class="calc-head">1. ข้อมูลหน้าตัด (Section Properties)</span>', unsafe_allow_html=True)
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1: st.latex(rf"S_x = {Sx} \; cm^3")
        with col_p2: st.latex(rf"Z_x = {Zx:.1f} \; cm^3")
        with col_p3: st.latex(rf"I_x = {Ix:,.0f} \; cm^4")
        st.markdown('<div class="calc-step"></div>', unsafe_allow_html=True)

        # ---------------------------------------------------------
        # CASE A: CHECK MODE (วิธีทำแบบเดินหน้า: Load -> Ratio)
        # ---------------------------------------------------------
        if is_check_mode:
            # 2. Load
            st.markdown('<span class="calc-head">2. วิเคราะห์น้ำหนักบรรทุก (Load Analysis)</span>', unsafe_allow_html=True)
            st.latex(rf"w_u = {factor_txt} \times {w_load:,.0f} = \mathbf{{{fact_w:,.0f}}} \; kg/m")
            st.latex(rf"P_u = {factor_txt} \times {p_load:,.0f} = \mathbf{{{fact_p:,.0f}}} \; kg")
            st.markdown('<div class="calc-step"></div>', unsafe_allow_html=True)
            
            # 3. Moment
            st.markdown('<span class="calc-head">3. ตรวจสอบโมเมนต์ (Moment Check)</span>', unsafe_allow_html=True)
            st.write("Demand ($M_u$):")
            st.latex(rf"M_u = \frac{{w_u L^2}}{{8}} + \frac{{P_u L}}{{4}} = \mathbf{{{m_act:,.0f}}} \; kg \cdot m")
            
            st.write("Capacity ($M_{n}$):")
            st.caption(f"LTB Zone: {ltb_zone} (Lb={Lb} m)")
            if is_lrfd: st.latex(rf"\phi M_n = \mathbf{{{M_cap:,.0f}}} \; kg \cdot m")
            else: st.latex(rf"M_n / \Omega = \mathbf{{{M_cap:,.0f}}} \; kg \cdot m")
            
            st.write(f"Ratio = {ratio_m:.3f} ({'OK' if ratio_m<=1 else 'FAIL'})")
            st.markdown('<div class="calc-step"></div>', unsafe_allow_html=True)
            
            # 4. Shear & Deflection (ย่อ)
            st.markdown('<span class="calc-head">4. ตรวจสอบแรงเฉือนและระยะแอ่น</span>', unsafe_allow_html=True)
            st.latex(rf"V_u = {v_act:,.0f} \; kg \quad \text{{vs}} \quad Capacity = {V_cap:,.0f} \; kg \quad \rightarrow \text{{Ratio}} = {ratio_v:.3f}")
            st.latex(rf"\Delta = {d_act:.2f} \; cm \quad \text{{vs}} \quad \Delta_{{allow}} = {d_allow:.2f} \; cm \quad \rightarrow \text{{Ratio}} = {ratio_d:.3f}")

        # ---------------------------------------------------------
        # CASE B: FIND CAPACITY MODE (วิธีทำแบบย้อนกลับ: Capacity -> w)
        # ---------------------------------------------------------
        else:
            st.info("💡 โหมดหาค่าน้ำหนัก: คำนวณย้อนกลับจากกำลังรับน้ำหนัก (Capacity) ไปหา Distributed Load ($w$)")
            
            # 2. Moment Capacity Base
            st.markdown('<span class="calc-head">2. หากำลังรับโมเมนต์ดัด ($M_{capacity}$ & $M_n$)</span>', unsafe_allow_html=True)
            st.write(f"พิจารณาการค้ำยันด้านข้าง $L_b = {Lb}$ m $\rightarrow$ **{ltb_zone}**")
            
            # Show Mn Formula briefly based on zone
            if "Zone 1" in ltb_zone: st.latex(r"M_n = M_p = F_y Z_x")
            elif "Zone 2" in ltb_zone: st.latex(r"M_n = C_b [M_p - (M_p - 0.7 F_y S_x)...]")
            else: st.latex(r"M_n = F_{cr} S_x")
            
            mn_kgm = Mn/100
            st.latex(rf"M_n = {mn_kgm:,.0f} \; kg \cdot m")
            
            if is_lrfd:
                st.latex(rf"\phi M_n = 0.90 \times {mn_kgm:,.0f} = \mathbf{{{M_cap:,.0f}}} \; kg \cdot m")
            else:
                st.latex(rf"M_n / \Omega = {mn_kgm:,.0f} / 1.67 = \mathbf{{{M_cap:,.0f}}} \; kg \cdot m")
            st.markdown('<div class="calc-step"></div>', unsafe_allow_html=True)
            
            # 3. Back-Calculate w
            st.markdown('<span class="calc-head">3. คำนวณน้ำหนักบรรทุกปลอดภัย ($w_{safe}$ Calculation)</span>', unsafe_allow_html=True)
            
            # 3.1 From Moment
            st.write("**กรณีที่ 1: ควบคุมโดยโมเมนต์ (Moment Control)**")
            st.latex(r"M_{cap} = \frac{w_u L^2}{8} \quad \Rightarrow \quad w_u = \frac{8 M_{cap}}{L^2}")
            w_m_val = (8 * M_cap) / (user_span**2)
            st.latex(rf"w_{{moment}} = \frac{{8 ({M_cap:,.0f})}}{{ {user_span}^2 }} = \mathbf{{{w_m_val:,.0f}}} \; kg/m")
            
            # 3.2 From Shear
            st.write("**กรณีที่ 2: ควบคุมโดยแรงเฉือน (Shear Control)**")
            st.latex(r"V_{cap} = \frac{w_u L}{2} \quad \Rightarrow \quad w_u = \frac{2 V_{cap}}{L}")
            w_v_val = (2 * V_cap) / user_span
            st.latex(rf"w_{{shear}} = \frac{{2 ({V_cap:,.0f})}}{{ {user_span} }} = \mathbf{{{w_v_val:,.0f}}} \; kg/m")
            
            # 3.3 From Deflection
            st.write("**กรณีที่ 3: ควบคุมโดยระยะแอ่น (Deflection Control)**")
            st.caption("Note: ใช้ Service Load สำหรับ Deflection")
            st.latex(r"\Delta_{allow} = \frac{5 w_{serv} L^4}{384 E I} \quad \Rightarrow \quad w_{serv} = \frac{384 E I \Delta_{allow}}{5 L^4}")
            
            # Calc values for display
            l_cm = user_span * 100
            w_d_val = (384 * E * Ix * d_allow) / (5 * l_cm**4) * 100 # *100 converts kg/cm to kg/m
            
            st.latex(rf"w_{{defl(service)}} = \frac{{384 ({E:.0f}) ({Ix:.0f}) ({d_allow:.2f})}}{{5 ({l_cm:.0f})^4}} \times 100 = \mathbf{{{w_d_val:,.0f}}} \; kg/m")
            
            # Convert Deflection w to Ultimate level for comparison (if LRFD)
            w_d_ult = w_d_val * factor_val
            st.write(f"เทียบเท่า Load Factor ({factor_txt}): $w_{{defl(u)}} = {w_d_val:,.0f} \\times {factor_txt} = {w_d_ult:,.0f}$ kg/m")
            
            st.markdown('<div class="calc-step"></div>', unsafe_allow_html=True)
            
            # 4. Conclusion
            st.markdown('<span class="calc-head">4. สรุปผล (Conclusion)</span>', unsafe_allow_html=True)
            min_w_u = min(w_m_val, w_v_val, w_d_ult)
            st.latex(rf"w_{{safe(u)}} = \min({w_m_val:,.0f}, {w_v_val:,.0f}, {w_d_ult:,.0f}) = \mathbf{{{min_w_u:,.0f}}} \; kg/m")
            
            st.write(f"แปลงกลับเป็น **Service Load** (หารด้วย {factor_txt}):")
            final_safe = min_w_u / factor_val
            st.markdown(f"### ✅ Max Safe Service Load = {final_safe:,.0f} kg/m")
            st.caption(f"Controlled by: {gov_cause}")

    # ==========================================
    # PART 3: GRAPHS (คงเดิม)
    # ==========================================
    st.markdown("---")
    st.subheader("📈 Force Diagrams & Capacity Curve")
    
    # 1. SFD/BMD
    x_plot = np.linspace(0, user_span, 100)
    ra = v_act # Note: In Find Capacity, these acts are based on the capacity load
    v_y, m_y = [], []
    for val in x_plot:
        shear = ra - (fact_w * val)
        if val > user_span/2: shear -= fact_p
        v_y.append(shear)
        moment = (ra * val) - (fact_w * val**2 / 2)
        if val > user_span/2: moment -= fact_p * (val - user_span/2)
        m_y.append(moment)

    c_g1, c_g2 = st.columns(2)
    with c_g1:
        fig_v = go.Figure(go.Scatter(x=x_plot, y=v_y, fill='tozeroy', line_color='#3b82f6', name='Shear'))
        fig_v.update_layout(title="Shear Force (SFD)", height=300, margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig_v, use_container_width=True)
    with c_g2:
        fig_m = go.Figure(go.Scatter(x=x_plot, y=m_y, fill='tozeroy', line_color='#ef4444', name='Moment'))
        fig_m.update_layout(title="Bending Moment (BMD)", height=300, margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig_m, use_container_width=True)

    # 2. Span Curve (Logic เดิม)
    st.subheader("📉 Safe Load vs Span")
    spans = np.linspace(1.0, 12.0, 50)
    w_cap_m, w_cap_v, w_cap_d = [], [], []
    
    r_ts_g = data.get('r_ts', 1.0)
    
    for s in spans:
        l_cm_g = s * 100
        # Shear
        w_v = (2 * V_cap) / s 
        # Moment
        if l_cm_g <= Lp_cm: mn_g = Mp
        elif l_cm_g <= Lr_cm:
            t = (Mp - 0.7*Fy*Sx) * ((l_cm_g - Lp_cm)/(Lr_cm - Lp_cm))
            mn_g = min(Mp, Cb*(Mp - t))
        else:
            sl = l_cm_g / r_ts_g
            fcr = (Cb * math.pi**2 * E) / (sl**2) 
            mn_g = min(fcr * Sx, Mp)
        m_des = (0.9*mn_g)/100 if is_lrfd else (mn_g/1.67)/100
        w_m = (8 * m_des) / (s**2)
        # Defl
        d_al = l_cm_g / defl_denom
        w_d = ((d_al * 384 * E * Ix)/(5 * l_cm_g**4) * 100) * factor_val
        
        w_cap_m.append(w_m/factor_val)
        w_cap_v.append(w_v/factor_val)
        w_cap_d.append(w_d/factor_val)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spans, y=w_cap_m, name='Moment', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=spans, y=w_cap_d, name='Deflection', line=dict(color='green', dash='dash')))
    fig.add_trace(go.Scatter(x=spans, y=w_cap_v, name='Shear', line=dict(color='orange', dash='dot')))
    
    if is_check_mode:
        fig.add_trace(go.Scatter(x=[user_span], y=[(fact_w+2*fact_p/user_span)/factor_val], mode='markers', name='Your Load', marker=dict(color='red', size=10, symbol='x')))
    else:
         fig.add_trace(go.Scatter(x=[user_span], y=[safe_load_show], mode='markers', name='Safe Load', marker=dict(color='purple', size=12, symbol='star')))

    fig.update_layout(height=400, xaxis_title="Span (m)", yaxis_title="Service Load (kg/m)")
    st.plotly_chart(fig, use_container_width=True)
