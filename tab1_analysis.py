import streamlit as st
import plotly.graph_objects as go
import numpy as np
import math

def render(data):
    """
    Render Tab 1: Analysis & Graphs
    Features:
    - Smart Dashboard (Check vs Find Capacity)
    - Detailed Calculation (Forward vs Reverse)
    - Interactive Graphs (SFD, BMD, Deflection) that sync with the calculated load
    - Span vs Capacity Curve
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
    
    # Capacities
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
    load_comb_name = "1.4(DL+LL)" if is_lrfd else "DL+LL"

    # ==========================================
    # LOGIC PREPARATION FOR DISPLAY
    # ==========================================
    # ถ้าเป็นโหมด "หาค่ารับน้ำหนัก" (Find Capacity) เราต้องจำลอง Load ขึ้นมาเพื่อพล็อตกราฟ
    if not is_check_mode:
        # ดึงค่า Safe Load ที่คำนวณมาได้ (Service Load)
        w_safe_service = data['w_safe'] / factor_val
        
        # สมมติว่า P = 0 ในโหมดหา Uniform Load Capacity เพื่อให้กราฟ Clean
        p_plot_service = 0 
        w_plot_service = w_safe_service
        
        # Factored Load สำหรับกราฟ SFD/BMD
        fact_w_plot = w_plot_service * factor_val
        fact_p_plot = 0
        
        # Recalculate Ratios based on Safe Load (เพื่อให้เห็นว่า Ratio = 1.00 ที่จุดวิกฤต)
        # 1. Shear Ratio
        v_act_sim = (fact_w_plot * user_span) / 2
        ratio_v_show = v_act_sim / V_cap
        
        # 2. Moment Ratio
        m_act_sim = (fact_w_plot * user_span**2) / 8
        ratio_m_show = m_act_sim / M_cap
        
        # 3. Deflection Ratio
        # Delta = 5wL^4 / 384EI
        w_kg_cm = w_plot_service / 100
        l_cm = user_span * 100
        d_act_sim = (5 * w_kg_cm * l_cm**4) / (384 * E * Ix)
        ratio_d_show = d_act_sim / d_allow
        
        # Variables for Display
        header_title = f"Max Safe Load: {w_safe_service:,.0f} kg/m"
        header_subtitle = f"Limited by: {gov_cause} (Ratio reaches 1.00)"
        header_color = "#0284c7" # Blue
        header_bg = "#f0f9ff"
        
    else:
        # โหมด Check: ใช้ค่าจริงจากการคำนวณ
        w_plot_service = w_input
        p_plot_service = p_input
        fact_w_plot = data['fact_w']
        fact_p_plot = data['fact_p']
        
        ratio_v_show = data['ratio_v']
        ratio_m_show = data['ratio_m']
        ratio_d_show = data['ratio_d']
        
        v_act_sim = data['v_act']
        m_act_sim = data['m_act']
        d_act_sim = data['d_act']
        
        pass_status = gov_ratio <= 1.0
        header_title = f"Check Result: {'PASS ✅' if pass_status else 'FAIL ❌'}"
        header_subtitle = f"Max Ratio: {gov_ratio:.2f} (Control: {gov_cause})"
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
                <b>Design Method:</b> {method_str}<br>
                Span: {user_span} m | Lb: {Lb} m
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Metrics (แสดงค่า Actual vs Capacity)
    c1, c2, c3 = st.columns(3)
    
    def metric_card(title, act, cap, ratio, unit):
        # Color logic: Red if ratio > 1, Blue if ratio ~ 1 (Governing in find mode), Gray otherwise
        if ratio > 1.001: color = "#ef4444" # Fail
        elif 0.99 <= ratio <= 1.001: color = "#2563eb" # Governing Limit
        else: color = "#374151" # OK
        
        st.markdown(f"""<div style="text-align:center; padding:10px; border:1px solid #e5e7eb; border-radius:8px; background:white;">
            <div style="color:#6b7280; font-size:0.85em; font-weight:bold; text-transform:uppercase;">{title}</div>
            <div style="font-size:1.8em; font-weight:800; color:{color}">{ratio:.2f}</div>
            <div style="font-size:0.8em; color:#4b5563;">{act:,.0f} / {cap:,.0f} {unit}</div>
        </div>""", unsafe_allow_html=True)

    with c1: metric_card("Shear (V)", v_act_sim, V_cap, ratio_v_show, "kg")
    with c2: metric_card("Moment (M)", m_act_sim, M_cap, ratio_m_show, "kg-m")
    with c3: metric_card("Deflection", d_act_sim, d_allow, ratio_d_show, "cm")

    # ==========================================
    # PART 2: CALCULATION SHEET
    # ==========================================
    st.write("---")
    st.subheader("📝 รายการคำนวณ (Calculation Sheet)")
    
    with st.expander("แสดงรายละเอียดการคำนวณ (Click to Expand)", expanded=True):
        st.markdown("""<style>.calc-head { font-weight: bold; font-size: 1.1em; color: #1e40af; margin-bottom: 10px; display:block; } .calc-step { border-bottom: 1px dashed #cbd5e1; padding-bottom: 15px; margin-bottom: 20px; }</style>""", unsafe_allow_html=True)

        # 1. Properties
        st.markdown('<span class="calc-head">1. ข้อมูลหน้าตัด (Properties)</span>', unsafe_allow_html=True)
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1: st.latex(rf"S_x = {Sx} \; cm^3")
        with col_p2: st.latex(rf"Z_x = {Zx:.1f} \; cm^3")
        with col_p3: st.latex(rf"I_x = {Ix:,.0f} \; cm^4")
        st.markdown('<div class="calc-step"></div>', unsafe_allow_html=True)

        if is_check_mode:
            # --- CHECK MODE DISPLAY ---
            st.info("Mode: Check Design (ตรวจสอบหน้าตัด)")
            # 2. Load
            st.markdown('<span class="calc-head">2. Load Analysis</span>', unsafe_allow_html=True)
            st.latex(rf"w_u = {factor_txt} \times {w_input:,.0f} = {fact_w_plot:,.0f} \; kg/m")
            st.markdown('<div class="calc-step"></div>', unsafe_allow_html=True)
            
            # 3. Moment
            st.markdown('<span class="calc-head">3. Moment Check</span>', unsafe_allow_html=True)
            st.latex(rf"M_u = {m_act_sim:,.0f} \; kg \cdot m")
            if is_lrfd: st.latex(rf"\phi M_n = {M_cap:,.0f} \; kg \cdot m")
            else: st.latex(rf"M_n / \Omega = {M_cap:,.0f} \; kg \cdot m")
            st.write(f"Ratio = {ratio_m_show:.3f}")
        else:
            # --- FIND CAPACITY MODE DISPLAY ---
            st.info("Mode: Find Capacity (หาค่ารับน้ำหนัก)")
            # 2. Capacity
            st.markdown('<span class="calc-head">2. คำนวณกำลังรับน้ำหนัก (Capacity)</span>', unsafe_allow_html=True)
            st.latex(rf"V_{{cap}} = {V_cap:,.0f} \; kg")
            st.latex(rf"M_{{cap}} = {M_cap:,.0f} \; kg \cdot m \quad (\text{{Zone: }} {ltb_zone})")
            st.latex(rf"\Delta_{{allow}} = L/{defl_denom} = {d_allow:.2f} \; cm")
            st.markdown('<div class="calc-step"></div>', unsafe_allow_html=True)
            
            # 3. Reverse Calc
            st.markdown('<span class="calc-head">3. คำนวณน้ำหนักบรรทุกปลอดภัย (Safe Load)</span>', unsafe_allow_html=True)
            st.write(f"คำนวณหา $w$ จากสมการย้ายข้าง (Uniform Load Only):")
            
            w_m_val = (8 * M_cap) / (user_span**2)
            w_v_val = (2 * V_cap) / user_span
            
            # Deflection w (service)
            l_cm = user_span * 100
            w_d_serv = (384 * E * Ix * d_allow) / (5 * l_cm**4) * 100
            w_d_ult = w_d_serv * factor_val
            
            st.latex(rf"w_{{moment(u)}} = \frac{{8 M_{{cap}}}}{{L^2}} = \mathbf{{{w_m_val:,.0f}}} \; kg/m")
            st.latex(rf"w_{{shear(u)}} = \frac{{2 V_{{cap}}}}{{L}} = \mathbf{{{w_v_val:,.0f}}} \; kg/m")
            st.latex(rf"w_{{defl(u)}} = w_{{serv}} \times {factor_txt} = {w_d_serv:,.0f} \times {factor_txt} = \mathbf{{{w_d_ult:,.0f}}} \; kg/m")
            
            st.markdown(f"**Conclusion:** เลือกค่าน้อยที่สุดเป็นคำตอบ")
            st.latex(rf"w_{{safe(u)}} = \min({w_m_val:,.0f}, {w_v_val:,.0f}, {w_d_ult:,.0f}) = \mathbf{{{w_plot_service*factor_val:,.0f}}} \; kg/m")
            st.write(f"Safe Service Load = {w_plot_service:,.0f} kg/m")

    # ==========================================
    # PART 3: GRAPHS (UPDATED WITH DEFLECTION)
    # ==========================================
    st.write("---")
    st.subheader("📈 Force & Deflection Diagrams")
    if not is_check_mode:
        st.caption(f"💡 กราฟแสดงพฤติกรรมภายใต้ **Safe Load: {w_plot_service:,.0f} kg/m** (เพื่อให้เห็นว่าหน้าตัดรับแรงเต็มพิกัดอย่างไร)")
    else:
        st.caption(f"💡 กราฟแสดงพฤติกรรมภายใต้ **Input Load** ของคุณ")

    # --- Generate Data Points ---
    x_plot = np.linspace(0, user_span, 100)
    ra = (fact_w_plot * user_span / 2) + (fact_p_plot / 2) # Reaction
    
    v_y = []
    m_y = []
    d_y = [] # Deflection
    
    # Unit conversions for Deflection calc
    w_line_kcm = (w_plot_service / 100) # kg/cm (Service load for defl)
    p_point_k = p_plot_service # kg
    L_cm = user_span * 100
    E_val = E
    I_val = Ix

    for x_m in x_plot:
        # 1. Shear & Moment (Using Factored Load)
        shear = ra - (fact_w_plot * x_m)
        if x_m > user_span/2: shear -= fact_p_plot
        v_y.append(shear)
        
        moment = (ra * x_m) - (fact_w_plot * x_m**2 / 2)
        if x_m > user_span/2: moment -= fact_p_plot * (x_m - user_span/2)
        m_y.append(moment)
        
        # 2. Deflection (Using Service Load, Simplified for Display)
        # Superposition: UDL + Point Load at center
        x_cm = x_m * 100
        
        # Deflection due to UDL
        y_udl = (w_line_kcm * x_cm) / (24 * E_val * I_val) * (L_cm**3 - 2*L_cm*x_cm**2 + x_cm**3)
        
        # Deflection due to Point Load (approx at center for graph smoothness)
        if x_cm <= L_cm/2:
            y_pl = (p_point_k * x_cm) / (48 * E_val * I_val) * (3*L_cm**2 - 4*x_cm**2)
        else:
            y_pl = (p_point_k * (L_cm - x_cm)) / (48 * E_val * I_val) * (3*L_cm**2 - 4*(L_cm-x_cm)**2)
            
        d_y.append(y_udl + y_pl)

    # --- Plotting 3 Columns ---
    col_g1, col_g2, col_g3 = st.columns(3)
    
    with col_g1:
        fig_v = go.Figure(go.Scatter(x=x_plot, y=v_y, fill='tozeroy', line_color='#3b82f6', name='Shear'))
        fig_v.add_hline(y=V_cap, line_dash="dot", line_color="gray", annotation_text="Capacity")
        fig_v.add_hline(y=-V_cap, line_dash="dot", line_color="gray")
        fig_v.update_layout(title="Shear Force (SFD)", yaxis_title="Shear (kg)", height=250, margin=dict(l=10,r=10,t=30,b=10))
        st.plotly_chart(fig_v, use_container_width=True)
        
    with col_g2:
        fig_m = go.Figure(go.Scatter(x=x_plot, y=m_y, fill='tozeroy', line_color='#ef4444', name='Moment'))
        fig_m.add_hline(y=M_cap, line_dash="dot", line_color="gray", annotation_text="Capacity")
        fig_m.update_layout(title="Bending Moment (BMD)", yaxis_title="Moment (kg-m)", height=250, margin=dict(l=10,r=10,t=30,b=10))
        st.plotly_chart(fig_m, use_container_width=True)
        
    with col_g3:
        # Deflection (Invert y-axis to look like beam sagging)
        fig_d = go.Figure(go.Scatter(x=x_plot, y=d_y, line_color='#10b981', name='Deflection'))
        fig_d.add_hline(y=d_allow, line_dash="dash", line_color="red", annotation_text="Limit")
        fig_d.update_yaxes(autorange="reversed") # กลับหัวกราฟ
        fig_d.update_layout(title="Deflection Profile", yaxis_title="Deflection (cm)", height=250, margin=dict(l=10,r=10,t=30,b=10))
        st.plotly_chart(fig_d, use_container_width=True)

    # ==========================================
    # PART 4: CAPACITY CURVE (Logic เดิม คงไว้ตามขอ)
    # ==========================================
    st.subheader("📉 Safe Load vs Span Curve")
    
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
    fig.add_trace(go.Scatter(x=spans, y=w_cap_m, name='Moment Limit', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=spans, y=w_cap_d, name='Deflection Limit', line=dict(color='green', dash='dash')))
    fig.add_trace(go.Scatter(x=spans, y=w_cap_v, name='Shear Limit', line=dict(color='orange', dash='dot')))
    
    # Marker จุดที่เราสนใจ
    if is_check_mode:
        fig.add_trace(go.Scatter(x=[user_span], y=[(fact_w_plot + 2*fact_p_plot/user_span)/factor_val], 
                                 mode='markers', name='Your Load', marker=dict(color='red', size=12, symbol='x')))
    else:
         fig.add_trace(go.Scatter(x=[user_span], y=[w_plot_service], 
                                  mode='markers', name='Calculated Safe Load', marker=dict(color='purple', size=14, symbol='star')))

    fig.update_layout(height=400, xaxis_title="Span (m)", yaxis_title="Safe Service Load (kg/m)")
    st.plotly_chart(fig, use_container_width=True)
