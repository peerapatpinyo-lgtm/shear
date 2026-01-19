import streamlit as st
import plotly.graph_objects as go
import numpy as np
import math

def render(data):
    """
    Render Tab 1: Analysis & Graphs
    Features:
    - Detailed Calculation for BOTH 'Check Mode' and 'Find Capacity Mode'
    - Smart Dashboard
    - Synchronized Graphs
    - Engineering Notes & Reaction Force Summary (New!)
    """
    # ==========================================
    # 0. UNPACK DATA
    # ==========================================
    is_check_mode = data['is_check_mode']
    gov_ratio = data['gov_ratio']
    gov_cause = data['gov_cause']
    method_str = data['method_str']
    is_lrfd = data['is_lrfd']
    
    # Loads
    w_input = data['w_load']
    p_input = data['p_load']
    
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
    
    # Capacities & Results
    V_cap = data['V_cap']
    M_cap = data['M_cap']
    d_allow = data['d_allow']
    
    # LTB Parameters
    Mn = data['Mn']
    Mp = data['Mp']
    Lp_cm = data['Lp_cm']
    Lr_cm = data['Lr_cm']
    ltb_zone = data['ltb_zone']
    Cb = data.get('Cb', 1.0)
    
    # Constants
    factor_txt = "1.4" if is_lrfd else "1.0"
    factor_val = 1.4 if is_lrfd else 1.0
    defl_denom = data['defl_denom']

    # ==========================================
    # PREPARE DATA FOR DISPLAY
    # ==========================================
    if not is_check_mode:
        # --- Find Capacity Mode ---
        # ใช้ Safe Load ที่คำนวณมาได้ในการพล็อตกราฟ
        w_safe_service = data['w_safe'] / factor_val
        w_plot_service = w_safe_service
        p_plot_service = 0 # Assume UDL only for capacity finding visualization
        
        # Factored Load for Graph
        fact_w_plot = w_plot_service * factor_val
        fact_p_plot = 0
        
        # Recalculate Ratios (Should be ~1.00 for governing)
        v_act_sim = (fact_w_plot * user_span) / 2
        ratio_v_show = v_act_sim / V_cap
        
        m_act_sim = (fact_w_plot * user_span**2) / 8
        ratio_m_show = m_act_sim / M_cap
        
        # Deflection Ratio
        w_kg_cm = w_plot_service / 100
        l_cm = user_span * 100
        d_act_sim = (5 * w_kg_cm * l_cm**4) / (384 * E * Ix)
        ratio_d_show = d_act_sim / d_allow
        
        header_title = f"Max Safe Load: {w_safe_service:,.0f} kg/m"
        header_subtitle = f"Control by: {gov_cause} (Ratio = 1.00)"
        header_color = "#0284c7"
        header_bg = "#f0f9ff"
        
    else:
        # --- Check Mode ---
        w_plot_service = w_input
        p_plot_service = p_input
        fact_w_plot = data['fact_w']
        fact_p_plot = data['fact_p']
        
        v_act_sim = data['v_act']
        m_act_sim = data['m_act']
        d_act_sim = data['d_act']
        
        ratio_v_show = data['ratio_v']
        ratio_m_show = data['ratio_m']
        ratio_d_show = data['ratio_d']
        
        pass_status = gov_ratio <= 1.0
        header_title = f"Check Result: {'PASS ✅' if pass_status else 'FAIL ❌'}"
        header_subtitle = f"Max Ratio: {gov_ratio:.2f} ({gov_cause})"
        header_color = "#10b981" if pass_status else "#ef4444"
        header_bg = "#ecfdf5" if pass_status else "#fef2f2"

    st.subheader(f"ผลการวิเคราะห์หน้าตัด: {sec_name}")

    # ==========================================
    # PART 1: DASHBOARD
    # ==========================================
    st.markdown(f"""
    <div style="background:{header_bg}; border-left:5px solid {header_color}; padding:15px; border-radius:8px; margin-bottom:20px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <h3 style="margin:0; color:{header_color};">{header_title}</h3>
                <div style="font-size:1.0em; color:#374151; margin-top:5px;">{header_subtitle}</div>
            </div>
            <div style="text-align:right; font-size:0.9em; color:#6b7280;">
                <b>Method:</b> {method_str}<br>
                Span: {user_span} m | Lb: {Lb} m
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Metrics
    c1, c2, c3 = st.columns(3)
    def metric_card(title, act, cap, ratio, unit):
        # Color logic
        if ratio > 1.001: color = "#ef4444"
        elif 0.99 <= ratio <= 1.001 and not is_check_mode: color = "#2563eb" # Highlight limiting factor
        else: color = "#374151"
        
        st.markdown(f"""<div style="text-align:center; padding:10px; border:1px solid #e5e7eb; border-radius:8px; background:white;">
            <div style="color:#6b7280; font-size:0.85em; font-weight:bold; text-transform:uppercase;">{title}</div>
            <div style="font-size:1.8em; font-weight:800; color:{color}">{ratio:.2f}</div>
            <div style="font-size:0.8em; color:#4b5563;">{act:,.0f} / {cap:,.0f} {unit}</div>
        </div>""", unsafe_allow_html=True)

    with c1: metric_card("Shear (V)", v_act_sim, V_cap, ratio_v_show, "kg")
    with c2: metric_card("Moment (M)", m_act_sim, M_cap, ratio_m_show, "kg-m")
    with c3: metric_card("Deflection", d_act_sim, d_allow, ratio_d_show, "cm")

    # ==========================================
    # PART 2: DETAILED CALCULATION SHEET
    # ==========================================
    st.write("---")
    st.subheader("📝 รายการคำนวณ (Calculation Sheet)")
    
    with st.expander("แสดงรายละเอียดการคำนวณ (Click to Expand)", expanded=True):
        st.markdown("""<style>.calc-head { font-weight: bold; font-size: 1.1em; color: #1e40af; margin-bottom: 10px; display:block; } .calc-step { border-bottom: 1px dashed #cbd5e1; padding-bottom: 15px; margin-bottom: 20px; }</style>""", unsafe_allow_html=True)

        # ----------------------------------------
        # SECTION 1: PROPERTIES (Shared)
        # ----------------------------------------
        st.markdown('<span class="calc-head">1. ข้อมูลออกแบบ (Design Parameters)</span>', unsafe_allow_html=True)
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1: 
            st.latex(rf"F_y = {Fy} \; ksc")
            st.latex(rf"S_x = {Sx} \; cm^3")
        with col_p2: 
            st.latex(rf"E = {E:,.0f} \; ksc")
            st.latex(rf"Z_x = {Zx:.1f} \; cm^3")
        with col_p3: 
            st.latex(rf"L = {user_span} \; m")
            st.latex(rf"I_x = {Ix:,.0f} \; cm^4")
        st.markdown('<div class="calc-step"></div>', unsafe_allow_html=True)

        if is_check_mode:
            # ========================================
            # MODE A: CHECK DESIGN (เดินหน้า)
            # ========================================
            st.info("📌 **Mode: Check Design** (ตรวจสอบหน้าตัดจาก Load ที่กำหนด)")
            
            # 2. Load
            st.markdown('<span class="calc-head">2. Load Analysis (วิเคราะห์น้ำหนัก)</span>', unsafe_allow_html=True)
            st.latex(rf"w_u = {factor_txt} \times {w_input:,.0f} = {fact_w_plot:,.0f} \; kg/m")
            st.latex(rf"P_u = {factor_txt} \times {p_input:,.0f} = {fact_p_plot:,.0f} \; kg")
            st.latex(rf"M_u = \frac{{w_u L^2}}{{8}} + \frac{{P_u L}}{{4}} = {m_act_sim:,.0f} \; kg \cdot m")
            st.markdown('<div class="calc-step"></div>', unsafe_allow_html=True)
            
            # 3. Capacity Check
            st.markdown('<span class="calc-head">3. Capacity Check (ตรวจสอบกำลัง)</span>', unsafe_allow_html=True)
            
            # 3.1 Shear
            st.write("**3.1 Shear Capacity**")
            st.latex(rf"V_n = 0.6 F_y A_w = 0.6({Fy})({Aw}) = {0.6*Fy*Aw:,.0f} \; kg")
            st.latex(rf"\text{{Capacity }} V_{{cap}} = {V_cap:,.0f} \; kg \quad \text{{(Ratio = {ratio_v_show:.2f})}}")
            
            # 3.2 Moment (LTB)
            st.write("**3.2 Moment Capacity (LTB)**")
            st.latex(rf"L_b = {Lb} m, \quad L_p = {Lp_cm/100:.2f} m, \quad L_r = {Lr_cm/100:.2f} m")
            st.write(f"Condition: **{ltb_zone}**")
            
            # Show LTB Formula based on zone
            if "Zone 1" in ltb_zone: st.latex(r"M_n = M_p = F_y Z_x")
            elif "Zone 2" in ltb_zone: st.latex(r"M_n = C_b [M_p - (M_p - 0.7 F_y S_x)(\frac{L_b - L_p}{L_r - L_p})]")
            else: st.latex(r"M_n = F_{cr} S_x")
            
            st.latex(rf"M_n = {Mn/100:,.0f} \; kg \cdot m")
            st.latex(rf"\text{{Capacity }} M_{{cap}} = {M_cap:,.0f} \; kg \cdot m \quad \text{{(Ratio = {ratio_m_show:.2f})}}")
            st.markdown('<div class="calc-step"></div>', unsafe_allow_html=True)
            
            # 4. Deflection
            st.markdown('<span class="calc-head">4. Deflection Check</span>', unsafe_allow_html=True)
            st.latex(rf"\Delta_{{act}} = {d_act_sim:.2f} \; cm")
            st.latex(rf"\Delta_{{limit}} = L/{defl_denom} = {d_allow:.2f} \; cm \quad \text{{(Ratio = {ratio_d_show:.2f})}}")

        else:
            # ========================================
            # MODE B: FIND CAPACITY (ย้อนกลับ)
            # ========================================
            st.info("📌 **Mode: Find Capacity** (คำนวณหากำลังรับน้ำหนักสูงสุด)")
            
            # 2. Section Capacity (ละเอียดเหมือนเดิม)
            st.markdown('<span class="calc-head">2. คำนวณกำลังของหน้าตัด (Determine Section Capacity)</span>', unsafe_allow_html=True)
            
            # 2.1 Shear Capacity
            st.write("**2.1 กำลังรับแรงเฉือน ($V_n$)**")
            st.latex(r"V_n = 0.6 F_y A_w")
            vn_val = 0.6 * Fy * Aw
            st.latex(rf"V_n = 0.6 ({Fy}) ({Aw:.2f}) = {vn_val:,.0f} \; kg")
            if is_lrfd:
                st.latex(rf"V_{{design}} = \phi V_n = 1.0 \times {vn_val:,.0f} = \mathbf{{{V_cap:,.0f}}} \; kg")
            else:
                st.latex(rf"V_{{design}} = V_n / \Omega = {vn_val:,.0f} / 1.5 = \mathbf{{{V_cap:,.0f}}} \; kg")
            
            # 2.2 Moment Capacity (Full Steps)
            st.write("**2.2 กำลังรับโมเมนต์ดัด ($M_n$)**")
            st.write("ตรวจสอบระยะค้ำยันด้านข้าง (LTB):")
            col_z1, col_z2 = st.columns(2)
            with col_z1:
                st.latex(rf"L_b = {Lb} \; m")
            with col_z2:
                st.latex(rf"L_p = {Lp_cm/100:.2f} m, \; L_r = {Lr_cm/100:.2f} m")
            
            st.write(f"$\therefore$ Condition falls in **{ltb_zone}**")
            
            # แสดงสูตร LTB เต็มๆ
            if "Zone 1" in ltb_zone:
                st.latex(r"M_n = M_p = F_y Z_x")
                st.latex(rf"M_n = {Fy} \times {Zx:.1f} = {Mn:,.0f} \; kg \cdot cm")
            elif "Zone 2" in ltb_zone:
                st.latex(r"M_n = C_b [M_p - (M_p - 0.7 F_y S_x)(\frac{L_b - L_p}{L_r - L_p})]")
                st.write("Substituting:")
                term_mp = Mp
                term_mr = 0.7 * Fy * Sx
                frac = (Lb*100 - Lp_cm)/(Lr_cm - Lp_cm)
                st.latex(rf"M_n = {Cb} [{term_mp:,.0f} - ({term_mp:,.0f} - {term_mr:,.0f})({frac:.3f})]")
                st.latex(rf"M_n = {Mn:,.0f} \; kg \cdot cm")
            else:
                st.latex(r"M_n = F_{cr} S_x")
                st.latex(rf"F_{{cr}} = \frac{{C_b \pi^2 E}}{{(L_b/r_{{ts}})^2}} \sqrt{{1 + 0.078 \frac{{J c}}{{S_x h_o}} (L_b/r_{{ts}})^2}}")
                st.latex(rf"M_n = {Mn:,.0f} \; kg \cdot cm")

            # แปลงเป็น Design Moment
            mn_kgm = Mn/100
            if is_lrfd:
                st.latex(rf"M_{{design}} = \phi M_n = 0.90 \times {mn_kgm:,.0f} = \mathbf{{{M_cap:,.0f}}} \; kg \cdot m")
            else:
                st.latex(rf"M_{{design}} = M_n / \Omega = {mn_kgm:,.0f} / 1.67 = \mathbf{{{M_cap:,.0f}}} \; kg \cdot m")
            
            # 2.3 Deflection Limit
            st.write("**2.3 ระยะแอ่นที่ยอมให้ ($\Delta_{allow}$)**")
            st.latex(rf"\Delta_{{allow}} = L / {defl_denom} = {user_span*100:.0f} / {defl_denom} = \mathbf{{{d_allow:.2f}}} \; cm")
            st.markdown('<div class="calc-step"></div>', unsafe_allow_html=True)
            
            # 3. Reverse Calculation
            st.markdown('<span class="calc-head">3. คำนวณน้ำหนักบรรทุกปลอดภัย (Calculate Safe Load)</span>', unsafe_allow_html=True)
            st.write("ย้ายข้างสมการเพื่อหา $w$ (Uniform Load) จากค่า Capacity:")
            
            col_rev1, col_rev2 = st.columns(2)
            with col_rev1:
                st.markdown("**Case A: Moment Control**")
                st.latex(r"M_{des} = \frac{w L^2}{8} \Rightarrow w = \frac{8 M_{des}}{L^2}")
                w_m_val = (8 * M_cap) / (user_span**2)
                st.latex(rf"w_1 = \frac{{8 ({M_cap:,.0f})}}{{ {user_span}^2 }} = {w_m_val:,.0f} \; kg/m")
                
            with col_rev2:
                st.markdown("**Case B: Shear Control**")
                st.latex(r"V_{des} = \frac{w L}{2} \Rightarrow w = \frac{2 V_{des}}{L}")
                w_v_val = (2 * V_cap) / user_span
                st.latex(rf"w_2 = \frac{{2 ({V_cap:,.0f})}}{{ {user_span} }} = {w_v_val:,.0f} \; kg/m")
            
            st.markdown("**Case C: Deflection Control (Service Limit)**")
            st.latex(r"\Delta_{all} = \frac{5 w_{serv} L^4}{384 E I} \Rightarrow w_{serv} = \frac{384 E I \Delta_{all}}{5 L^4}")
            
            l_cm = user_span * 100
            w_d_serv = (384 * E * Ix * d_allow) / (5 * l_cm**4) * 100
            w_d_ult = w_d_serv * factor_val
            
            st.latex(rf"w_{{serv}} = \frac{{384 ({E:.0f}) ({Ix:.0f}) ({d_allow:.2f})}}{{5 ({l_cm:.0f})^4}} \times 100 = {w_d_serv:,.0f} \; kg/m")
            st.write(f"Convert to Strength Level for comparison (x {factor_txt}):")
            st.latex(rf"w_3 = {w_d_serv:,.0f} \times {factor_txt} = {w_d_ult:,.0f} \; kg/m")
            
            st.markdown('<div class="calc-step"></div>', unsafe_allow_html=True)
            st.markdown('<span class="calc-head">4. สรุปผล (Conclusion)</span>', unsafe_allow_html=True)
            min_w = min(w_m_val, w_v_val, w_d_ult)
            st.latex(rf"w_{{safe(u)}} = \min({w_m_val:,.0f}, {w_v_val:,.0f}, {w_d_ult:,.0f}) = \mathbf{{{min_w:,.0f}}} \; kg/m")
            st.write(f"แปลงกลับเป็น Service Load (หารด้วย {factor_txt}):")
            st.markdown(f"### ✅ Max Safe Load = {min_w/factor_val:,.0f} kg/m")


    # ==========================================
    # PART 3: GRAPHS (Synchronized)
    # ==========================================
    st.write("---")
    st.subheader("📈 Force & Deflection Diagrams")
    if not is_check_mode:
        st.caption(f"💡 กราฟแสดงพฤติกรรมภายใต้ **Safe Load: {w_plot_service:,.0f} kg/m**")

    # Data Gen
    x_plot = np.linspace(0, user_span, 100)
    ra = (fact_w_plot * user_span / 2) + (fact_p_plot / 2)
    v_y, m_y, d_y = [], [], []
    
    # Const for Deflection
    w_line_kcm = (w_plot_service / 100)
    p_point_k = p_plot_service
    L_cm = user_span * 100
    
    for x_m in x_plot:
        # V, M
        shear = ra - (fact_w_plot * x_m)
        if x_m > user_span/2: shear -= fact_p_plot
        v_y.append(shear)
        moment = (ra * x_m) - (fact_w_plot * x_m**2 / 2)
        if x_m > user_span/2: moment -= fact_p_plot * (x_m - user_span/2)
        m_y.append(moment)
        # Deflection (Simplified Center Point Load + UDL)
        x_cm = x_m * 100
        y_udl = (w_line_kcm * x_cm) / (24 * E * Ix) * (L_cm**3 - 2*L_cm*x_cm**2 + x_cm**3)
        if x_cm <= L_cm/2:
            y_pl = (p_point_k * x_cm) / (48 * E * Ix) * (3*L_cm**2 - 4*x_cm**2)
        else:
            y_pl = (p_point_k * (L_cm - x_cm)) / (48 * E * Ix) * (3*L_cm**2 - 4*(L_cm-x_cm)**2)
        d_y.append(y_udl + y_pl)

    # Plot
    c_g1, c_g2, c_g3 = st.columns(3)
    with c_g1:
        fig_v = go.Figure(go.Scatter(x=x_plot, y=v_y, fill='tozeroy', line_color='#3b82f6', name='Shear'))
        fig_v.add_hline(y=V_cap, line_dash="dot", line_color="gray")
        fig_v.add_hline(y=-V_cap, line_dash="dot", line_color="gray")
        fig_v.update_layout(title="Shear Force (SFD)", height=250, margin=dict(l=10,r=10,t=30,b=10))
        st.plotly_chart(fig_v, use_container_width=True)
    with c_g2:
        fig_m = go.Figure(go.Scatter(x=x_plot, y=m_y, fill='tozeroy', line_color='#ef4444', name='Moment'))
        fig_m.add_hline(y=M_cap, line_dash="dot", line_color="gray")
        fig_m.update_layout(title="Bending Moment (BMD)", height=250, margin=dict(l=10,r=10,t=30,b=10))
        st.plotly_chart(fig_m, use_container_width=True)
    with c_g3:
        fig_d = go.Figure(go.Scatter(x=x_plot, y=d_y, line_color='#10b981', name='Deflection'))
        fig_d.add_hline(y=d_allow, line_dash="dash", line_color="red")
        fig_d.update_yaxes(autorange="reversed")
        fig_d.update_layout(title="Deflection", height=250, margin=dict(l=10,r=10,t=30,b=10))
        st.plotly_chart(fig_d, use_container_width=True)

    # ==========================================
    # PART 4: SPAN CURVE (Original Logic)
    # ==========================================
    st.subheader("📉 Safe Load vs Span")
    spans = np.linspace(1.0, 12.0, 50)
    w_c_m, w_c_v, w_c_d = [], [], []
    r_ts_g = data.get('r_ts', 1.0)
    
    for s in spans:
        l_g = s * 100
        # Shear
        wv = (2 * V_cap) / s 
        # Moment
        if l_g <= Lp_cm: mn_g = Mp
        elif l_g <= Lr_cm:
            t = (Mp - 0.7*Fy*Sx) * ((l_g - Lp_cm)/(Lr_cm - Lp_cm))
            mn_g = min(Mp, Cb*(Mp - t))
        else:
            sl = l_g / r_ts_g
            fcr = (Cb * math.pi**2 * E) / (sl**2) 
            mn_g = min(fcr * Sx, Mp)
        m_d = (0.9*mn_g)/100 if is_lrfd else (mn_g/1.67)/100
        wm = (8 * m_d) / (s**2)
        # Defl
        da = l_g / defl_denom
        wd = ((da * 384 * E * Ix)/(5 * l_g**4) * 100) * factor_val
        
        w_c_m.append(wm/factor_val)
        w_c_v.append(wv/factor_val)
        w_c_d.append(wd/factor_val)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spans, y=w_c_m, name='Moment', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=spans, y=w_c_d, name='Deflection', line=dict(color='green', dash='dash')))
    fig.add_trace(go.Scatter(x=spans, y=w_c_v, name='Shear', line=dict(color='orange', dash='dot')))
    
    # Marker
    if is_check_mode:
        fig.add_trace(go.Scatter(x=[user_span], y=[(fact_w_plot + 2*fact_p_plot/user_span)/factor_val], 
                                 mode='markers', name='Your Load', marker=dict(color='red', size=12, symbol='x')))
    else:
         fig.add_trace(go.Scatter(x=[user_span], y=[w_plot_service], 
                                  mode='markers', name='Safe Load', marker=dict(color='purple', size=14, symbol='star')))

    fig.update_layout(height=400, xaxis_title="Span (m)", yaxis_title="Safe Service Load (kg/m)")
    st.plotly_chart(fig, use_container_width=True)

    # ==========================================
    # PART 5: ENGINEERING SUMMARY & NOTES (NEW!)
    # ==========================================
    st.write("---")
    st.subheader("🏗️ สรุปข้อมูลสำหรับออกแบบจุดต่อ (Connection Data)")
    
    # Calculate Reaction
    # Reaction = Max Shear at Support
    R_design = (fact_w_plot * user_span / 2) + (fact_p_plot / 2)
    
    ec1, ec2 = st.columns([1, 2])
    with ec1:
        st.info(f"**Max Reaction ($R_u$):**\n\n# {R_design:,.0f} kg")
    with ec2:
        st.markdown(f"""
        **Engineering Notes:**
        * **Reaction Force:** ใช้ค่า {R_design:,.0f} kg ในการออกแบบจุดต่อ (Bolt/Weld) หรือถ่ายแรงลงเสา
        * **Self-Weight:** โปรดตรวจสอบว่าน้ำหนักบรรทุก ($w$) ได้รวมน้ำหนักตัวเองของคาน (Beam Self-weight) แล้วหรือไม่
        * **Compactness:** รายการคำนวณนี้สมมติหน้าตัดเป็น **Compact Section** (ไม่เกิด Local Buckling)
        * **Deflection:** ตรวจสอบที่สภาวะ Total Service Load (Limit $L/{defl_denom}$)
        """)
