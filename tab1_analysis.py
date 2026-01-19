# tab1_analysis.py
import streamlit as st
import plotly.graph_objects as go
import numpy as np
import math

def render(data):
    """
    Render Tab 1: Analysis & Graphs
    Includes:
    1. Dashboard Summary
    2. Detailed Engineering Calculation Sheet (LaTeX)
    3. SFD & BMD Graphs
    4. Span vs Capacity Curve
    """
    # ==========================================
    # 0. UNPACK DATA (ดึงตัวแปรทั้งหมด)
    # ==========================================
    # Status & Method
    is_check_mode = data['is_check_mode']
    gov_ratio = data['gov_ratio']
    gov_cause = data['gov_cause']
    method_str = data['method_str']
    is_lrfd = data['is_lrfd']
    
    # Loads
    w_load = data['w_load']
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
    Zx = data.get('Zx', Sx) # Fallback
    
    # Results (Act vs Cap)
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
    
    # Factors
    factor_txt = "1.4" if is_lrfd else "1.0"
    load_comb_name = "1.4(DL+LL)" if is_lrfd else "DL+LL"
    defl_denom = data['defl_denom']

    st.subheader(f"ผลการวิเคราะห์หน้าตัด: {sec_name}")

    # ==========================================
    # PART 1: DASHBOARD SUMMARY (ของเดิม)
    # ==========================================
    if is_check_mode:
        status_color = "#10b981" if gov_ratio <= 1.0 else "#ef4444"
        status_icon = "✅ ผ่าน (PASS)" if gov_ratio <= 1.0 else "❌ ไม่ผ่าน (FAIL)"
        bg_color = "#ecfdf5" if gov_ratio <= 1.0 else "#fef2f2"
        
        st.markdown(f"""
        <div style="background:{bg_color}; border-left:5px solid {status_color}; padding:15px; border-radius:8px; margin-bottom:20px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h3 style="margin:0; color:{status_color};">{status_icon}</h3>
                    <div style="font-size:1.1em; color:#374151; margin-top:5px;">
                        Max Ratio = <b>{gov_ratio:.2f}</b> (Control: {gov_cause})
                    </div>
                </div>
                <div style="text-align:right; font-size:0.9em; color:#6b7280;">
                    <b>Design Method:</b> {method_str}<br>
                    Load: w={w_load:,.0f}, P={p_load:,.0f}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Find Capacity Mode
        w_safe_service = data['w_safe']/(1.4 if is_lrfd else 1.0)
        st.markdown(f"""
        <div style="background:#f0f9ff; border-left:5px solid #0284c7; padding:15px; border-radius:8px; margin-bottom:20px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h3 style="margin:0; color:#0284c7;">Safe Load: {w_safe_service:,.0f} kg/m</h3>
                    <div style="font-size:1.0em; color:#374151;">(Service Load) Control: {gov_cause}</div>
                </div>
                <div style="text-align:right; font-size:0.9em; color:#6b7280;">
                    Span = {user_span} m<br>Lb = {Lb} m
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Metrics Row
    c1, c2, c3 = st.columns(3)
    def get_metric_color(ratio):
        return '#ef4444' if is_check_mode and ratio > 1 else '#1f2937'

    with c1:
        st.markdown(f"""<div style="text-align:center; padding:10px; border:1px solid #e5e7eb; border-radius:8px; background:white;">
            <div style="color:#6b7280; font-size:0.9em; font-weight:bold;">SHEAR (V)</div>
            <div style="font-size:1.8em; font-weight:800; color:{get_metric_color(ratio_v)}">{ratio_v:.2f}</div>
            <div style="font-size:0.8em; color:#4b5563;">{v_act:,.0f} / {V_cap:,.0f} kg</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div style="text-align:center; padding:10px; border:1px solid #e5e7eb; border-radius:8px; background:white;">
            <div style="color:#6b7280; font-size:0.9em; font-weight:bold;">MOMENT (M)</div>
            <div style="font-size:1.8em; font-weight:800; color:{get_metric_color(ratio_m)}">{ratio_m:.2f}</div>
            <div style="font-size:0.8em; color:#4b5563;">{m_act:,.0f} / {M_cap:,.0f} kg-m</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div style="text-align:center; padding:10px; border:1px solid #e5e7eb; border-radius:8px; background:white;">
            <div style="color:#6b7280; font-size:0.9em; font-weight:bold;">DEFLECTION ($\Delta$)</div>
            <div style="font-size:1.8em; font-weight:800; color:{get_metric_color(ratio_d)}">{ratio_d:.2f}</div>
            <div style="font-size:0.8em; color:#4b5563;">{d_act:.2f} / {d_allow:.2f} cm</div>
        </div>""", unsafe_allow_html=True)

    # ==========================================
    # PART 2: DETAILED CALCULATION SHEET (ของใหม่)
    # ==========================================
    st.write("---")
    st.subheader("📝 รายการคำนวณละเอียด (Detailed Calculation Sheet)")
    
    with st.expander("แสดงวิธีทำอย่างละเอียด (Click to Expand)", expanded=True):
        
        # Style
        st.markdown("""
        <style>
        .calc-step { margin-bottom: 25px; border-bottom: 1px dashed #cbd5e1; padding-bottom: 15px; }
        .calc-head { font-weight: bold; font-size: 1.1em; color: #1e40af; margin-bottom: 10px; display:block; }
        </style>
        """, unsafe_allow_html=True)

        # ---------------------------------------------
        # 1. Properties
        # ---------------------------------------------
        st.markdown('<span class="calc-head">1. ข้อมูลออกแบบ (Design Parameters)</span>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.latex(rf"F_y = {Fy} \; ksc")
            st.latex(rf"A_w = {Aw:.2f} \; cm^2")
        with c2:
            st.latex(rf"E = {E:,.0f} \; ksc")
            st.latex(rf"Z_x = {Zx:.1f} \; cm^3")
        with c3:
            st.latex(rf"L = {user_span} \; m")
            st.latex(rf"I_x = {Ix:,.0f} \; cm^4")
        st.markdown('<div class="calc-step"></div>', unsafe_allow_html=True)

        # ---------------------------------------------
        # 2. Load Analysis
        # ---------------------------------------------
        st.markdown('<span class="calc-head">2. วิเคราะห์น้ำหนักบรรทุก (Load Analysis)</span>', unsafe_allow_html=True)
        st.write(f"**Load Combination:** {load_comb_name}")
        
        col_L1, col_L2 = st.columns(2)
        with col_L1:
            st.markdown("**Distributed Load ($w_u$):**")
            st.latex(rf"w_u = {factor_txt} \times {w_load:,.0f} = \mathbf{{{fact_w:,.0f}}} \; kg/m")
        with col_L2:
            st.markdown("**Point Load ($P_u$):**")
            st.latex(rf"P_u = {factor_txt} \times {p_load:,.0f} = \mathbf{{{fact_p:,.0f}}} \; kg")
        
        st.markdown("**Internal Forces Calculation (Max Demand):**")
        col_F1, col_F2 = st.columns(2)
        with col_F1:
            st.latex(r"V_{max} = \frac{w_u L}{2} + \frac{P_u}{2}")
            st.latex(rf"V_u = \frac{{{fact_w:,.0f}({user_span})}}{{2}} + \frac{{{fact_p:,.0f}}}{{2}} = \mathbf{{{v_act:,.0f}}} \; kg")
        with col_F2:
            st.latex(r"M_{max} = \frac{w_u L^2}{8} + \frac{P_u L}{4}")
            st.latex(rf"M_u = \frac{{{fact_w:,.0f}({user_span})^2}}{{8}} + \frac{{{fact_p:,.0f}({user_span})}}{{4}} = \mathbf{{{m_act:,.0f}}} \; kg \cdot m")
        st.markdown('<div class="calc-step"></div>', unsafe_allow_html=True)

        # ---------------------------------------------
        # 3. Shear Check
        # ---------------------------------------------
        st.markdown('<span class="calc-head">3. ตรวจสอบกำลังรับแรงเฉือน (Shear Capacity Check)</span>', unsafe_allow_html=True)
        col_S1, col_S2 = st.columns(2)
        
        with col_S1:
            st.write("**3.1 Nominal Shear Strength ($V_n$)**")
            st.latex(r"V_n = 0.6 F_y A_w")
            vn_val = 0.6 * Fy * Aw
            st.latex(rf"V_n = 0.6 ({Fy}) ({Aw:.2f}) = {vn_val:,.0f} \; kg")
            
        with col_S2:
            st.write(f"**3.2 Design Capacity ({method_str})**")
            if is_lrfd:
                st.latex(rf"\phi V_n = 1.00 \times {vn_val:,.0f} = \mathbf{{{V_cap:,.0f}}} \; kg")
            else:
                st.latex(rf"V_n / \Omega = {vn_val:,.0f} / 1.50 = \mathbf{{{V_cap:,.0f}}} \; kg")
            
            st.write("**3.3 Check Ratio**")
            check_mark = "OK" if ratio_v <= 1.0 else "FAIL"
            color_mark = "green" if ratio_v <= 1.0 else "red"
            st.markdown(f"Ratio = ${v_act:,.0f} / {V_cap:,.0f} = {ratio_v:.3f}$ ... <b style='color:{color_mark}'>{check_mark}</b>", unsafe_allow_html=True)
        st.markdown('<div class="calc-step"></div>', unsafe_allow_html=True)

        # ---------------------------------------------
        # 4. Moment Check (LTB)
        # ---------------------------------------------
        st.markdown('<span class="calc-head">4. ตรวจสอบกำลังรับโมเมนต์ดัด (Moment Capacity Check)</span>', unsafe_allow_html=True)
        
        # 4.1 LTB Parameters
        st.write("**4.1 ตรวจสอบระยะค้ำยันด้านข้าง (Lateral-Torsional Buckling Analysis)**")
        col_M1, col_M2 = st.columns(2)
        with col_M1:
            st.latex(rf"L_b = {Lb:.2f} \; m")
            st.latex(rf"L_p = {Lp_cm/100:.2f} \; m")
            st.latex(rf"L_r = {Lr_cm/100:.2f} \; m")
        with col_M2:
            st.info(f"Condition: $L_b$ falls in **{ltb_zone}**")
            st.latex(rf"C_b = {Cb}")

        # 4.2 Mn Calculation logic display
        st.write(f"**4.2 คำนวณกำลังระบุ ($M_n$) ตามโซน {ltb_zone}**")
        
        if "Zone 1" in ltb_zone:
            st.write("Case: Plastic Yielding ($L_b \le L_p$)")
            st.latex(r"M_n = M_p = F_y Z_x")
            st.latex(rf"M_n = {Fy} \times {Zx:.1f} = {Mn:,.0f} \; kg \cdot cm")
        elif "Zone 2" in ltb_zone:
            st.write("Case: Inelastic Buckling ($L_p < L_b \le L_r$)")
            st.latex(r"M_n = C_b [M_p - (M_p - 0.7 F_y S_x)(\frac{L_b - L_p}{L_r - L_p})] \le M_p")
            st.write("Substituting values:")
            term_mr = 0.7 * Fy * Sx
            term_frac = (Lb*100 - Lp_cm)/(Lr_cm - Lp_cm)
            st.latex(rf"M_n = {Cb} [{Mp:,.0f} - ({Mp:,.0f} - {term_mr:,.0f})({term_frac:.3f})]")
            st.latex(rf"M_n = {Mn:,.0f} \; kg \cdot cm")
        else: # Zone 3
            st.write("Case: Elastic Buckling ($L_b > L_r$)")
            st.latex(r"M_n = F_{cr} S_x \le M_p")
            st.latex(rf"F_{{cr}} = \frac{{C_b \pi^2 E}}{{(L_b/r_{{ts}})^2}} \sqrt{{1 + 0.078 \frac{{J c}}{{S_x h_o}} (L_b/r_{{ts}})^2}}")
            st.latex(rf"M_n = {Mn:,.0f} \; kg \cdot cm")
        
        # 4.3 Check
        st.write("**4.3 Design Capacity & Ratio**")
        c_res1, c_res2 = st.columns(2)
        mn_kgm = Mn / 100
        with c_res1:
            if is_lrfd:
                st.latex(rf"\phi M_n = 0.90 \times {mn_kgm:,.0f} = \mathbf{{{M_cap:,.0f}}} \; kg \cdot m")
            else:
                st.latex(rf"M_n / \Omega = {mn_kgm:,.0f} / 1.67 = \mathbf{{{M_cap:,.0f}}} \; kg \cdot m")
        with c_res2:
            check_mark_m = "OK" if ratio_m <= 1.0 else "FAIL"
            color_mark_m = "green" if ratio_m <= 1.0 else "red"
            st.markdown(f"Ratio = ${m_act:,.0f} / {M_cap:,.0f} = {ratio_m:.3f}$ ... <b style='color:{color_mark_m}'>{check_mark_m}</b>", unsafe_allow_html=True)
        st.markdown('<div class="calc-step"></div>', unsafe_allow_html=True)

        # ---------------------------------------------
        # 5. Deflection Check
        # ---------------------------------------------
        st.markdown('<span class="calc-head">5. ตรวจสอบระยะแอ่นตัว (Deflection Check)</span>', unsafe_allow_html=True)
        st.caption("*Note: Checked at Service Load (Unfactored)*")
        
        c_d1, c_d2 = st.columns(2)
        with c_d1:
            st.write("**Actual Deflection ($\Delta_{act}$)**")
            st.latex(r"\Delta = \frac{5 w L^4}{384 E I} + \frac{P L^3}{48 E I}")
            
            # Unit variables
            w_kg_cm = w_load / 100
            l_cm = user_span * 100
            st.write("Substituting (Units: kg, cm):")
            st.latex(rf"\Delta = \frac{{5({w_kg_cm:.2f})({l_cm:.0f})^4}}{{384({E:.0f})({Ix:.0f})}} + \frac{{{p_load:.0f}({l_cm:.0f})^3}}{{48({E:.0f})({Ix:.0f})}}")
            st.latex(rf"\Delta_{{actual}} = \mathbf{{{d_act:.2f}}} \; cm")
            
        with c_d2:
            st.write("**Allowable Limit ($\Delta_{allow}$)**")
            st.latex(rf"\Delta_{{limit}} = L / {defl_denom}")
            st.latex(rf"\Delta_{{limit}} = {l_cm:.0f} / {defl_denom} = \mathbf{{{d_allow:.2f}}} \; cm")
            
            check_mark_d = "OK" if ratio_d <= 1.0 else "FAIL"
            color_mark_d = "green" if ratio_d <= 1.0 else "red"
            st.markdown(f"Ratio = ${d_act:.2f} / {d_allow:.2f} = {ratio_d:.3f}$ ... <b style='color:{color_mark_d}'>{check_mark_d}</b>", unsafe_allow_html=True)

    # ==========================================
    # PART 3: GRAPHS (SFD, BMD, Span Curve) - ของเดิม
    # ==========================================
    st.markdown("---")
    st.subheader("📈 แผนภาพแรง (Force Diagrams)")
    
    # --- SFD & BMD Logic ---
    x_plot = np.linspace(0, user_span, 100)
    ra = v_act
    v_y, m_y = [], []
    for val in x_plot:
        shear = ra - (fact_w * val)
        if val > user_span/2: shear -= fact_p
        v_y.append(shear)
        moment = (ra * val) - (fact_w * val**2 / 2)
        if val > user_span/2: moment -= fact_p * (val - user_span/2)
        m_y.append(moment)

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig_v = go.Figure(go.Scatter(x=x_plot, y=v_y, fill='tozeroy', line_color='#3b82f6', name='Shear'))
        fig_v.update_layout(title="Shear Force Diagram (SFD)", xaxis_title="Length (m)", yaxis_title="Shear (kg)", height=300, margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig_v, use_container_width=True)
        
    with col_g2:
        fig_m = go.Figure(go.Scatter(x=x_plot, y=m_y, fill='tozeroy', line_color='#ef4444', name='Moment'))
        fig_m.update_layout(title="Bending Moment Diagram (BMD)", xaxis_title="Length (m)", yaxis_title="Moment (kg-m)", height=300, margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig_m, use_container_width=True)

    # --- SPAN VS CAPACITY CURVE Logic ---
    st.subheader("📉 กราฟน้ำหนักบรรทุกปลอดภัย vs ระยะพาด (Safe Load vs Span)")
    
    spans = np.linspace(1.0, 12.0, 50)
    w_cap_moment, w_cap_shear, w_cap_defl = [], [], []
    
    # Constants for graph loop (handling missing keys safely)
    r_ts_g = data.get('r_ts', 1.0)
    val_J_g = data.get('J', 1.0)
    ho_g = data.get('h0', 1.0)
    if ho_g == 0: ho_g = 1.0
    val_A_g = (val_J_g * 1.0) / (Sx * ho_g)
    
    phi_b = 0.90
    omg_b = 1.67
    factor_load = 1.4 if is_lrfd else 1.0 
    
    for s in spans:
        l_cm_g = s * 100
        lb_cm_g = l_cm_g # Assumption Lb=L
        
        # 1. Shear
        w_v = (2 * V_cap) / s 
        
        # 2. Moment (Full LTB)
        if lb_cm_g <= Lp_cm: 
            mn_g = Mp
        elif lb_cm_g <= Lr_cm:
            term_g = (Mp - 0.7*Fy*Sx) * ((lb_cm_g - Lp_cm)/(Lr_cm - Lp_cm))
            mn_g = min(Mp, Cb*(Mp - term_g))
        else:
            slend_g = lb_cm_g / r_ts_g
            if slend_g > 0:
                fcr_g = (Cb * math.pi**2 * E) / (slend_g**2) * math.sqrt(1 + 0.078 * val_A_g * slend_g**2)
            else:
                fcr_g = Fy
            mn_g = min(fcr_g * Sx, Mp)
            
        m_cap_g = (phi_b * mn_g)/100 if is_lrfd else (mn_g/omg_b)/100
        w_m = (8 * m_cap_g) / (s**2)
        
        # 3. Deflection
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
        equiv_w_act = (fact_w + (2*fact_p/user_span)) / factor_load 
        fig.add_trace(go.Scatter(x=[user_span], y=[equiv_w_act], mode='markers', name='Your Load', marker=dict(color='red', size=12, symbol='x')))
    
    fig.update_layout(xaxis_title="Span (m)", yaxis_title="Safe Service Load (kg/m)", height=450, margin=dict(l=20,r=20,t=40,b=20))
    st.plotly_chart(fig, use_container_width=True)
