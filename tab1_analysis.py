import streamlit as st
import plotly.graph_objects as go
import numpy as np
import math

def render(data):
    """
    Render Tab 1: Analysis & Graphs (Thai Engineering Standard Language)
    """
    # --- UNPACK DATA ---
    is_check_mode = data['is_check_mode']
    gov_ratio = data['gov_ratio']
    method_str = data['method_str'] # LRFD or ASD
    w_load = data['w_load']
    p_load = data['p_load']
    gov_cause = data['gov_cause']
    w_safe = data['w_safe']
    is_lrfd = data['is_lrfd']
    user_span = data['user_span']
    Lb = data['Lb']
    sec_name = data['sec_name']
    
    # Forces
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

    # Detail vars
    Aw = data['Aw']
    Fy = data['Fy']
    Ix = data['Ix']
    defl_denom = data['defl_denom']
    Lp_cm = data['Lp_cm']
    Lr_cm = data['Lr_cm']
    ltb_zone = data['ltb_zone']
    Mn = data['Mn']
    fact_w = data['fact_w']
    fact_p = data['fact_p']

    # Header
    st.subheader(f"ผลการวิเคราะห์หน้าตัด: {sec_name}")

    # ==========================================
    # 1. DASHBOARD (สรุปผล)
    # ==========================================
    if is_check_mode:
        status_color = "#10b981" if gov_ratio <= 1.0 else "#ef4444" # Green / Red
        status_text = "ผ่าน (PASS)" if gov_ratio <= 1.0 else "ไม่ผ่าน (FAIL)"
        status_icon = "✅" if gov_ratio <= 1.0 else "❌"
        
        st.markdown(f"""
        <div class="highlight-card" style="border-left-color: {status_color};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span class="sub-text">ผลการตรวจสอบ ({method_str})</span><br>
                    <span style="font-size:20px; font-weight:bold; color:{status_color}">{status_icon} {status_text}</span>
                    <div style="font-size:12px; color:#6b7280; margin-top:5px;">Max Ratio = {gov_ratio:.2f}</div>
                </div>
                <div style="text-align: right;">
                    <small><b>Load Case:</b> {w_load:,.0f} kg/m, {p_load:,.0f} kg</small><br>
                    <small style="color:{status_color};"><b>จุดวิกฤต:</b> {gov_cause}</small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Mode Find Capacity
        safe_val_show = w_safe / 1.4 if is_lrfd else w_safe
        st.markdown(f"""
        <div class="highlight-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span class="sub-text">น้ำหนักบรรทุกใช้งานปลอดภัย (Safe Service Load)</span><br>
                    <span class="big-num">{safe_val_show:,.0f}</span> <span style="font-size:24px; color:#6b7280;">kg/m</span>
                </div>
                <div style="text-align: right;">
                    <span class="sub-text" style="color:#2563eb;">ตัวควบคุม: {gov_cause}</span><br>
                    <small>Span={user_span}m | Lb={Lb}m</small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- 3 KEY CHECKS ---
    c1, c2, c3 = st.columns(3)
    
    # Helper styles
    def get_style(ratio):
        color = '#ef4444' if is_check_mode and ratio > 1 else '#1f2937'
        return color

    with c1:
        st.markdown(f"""<div class="detail-card">
            <h4 style="margin:0;">1. แรงเฉือน (Shear)</h4>
            <div style="font-size:24px; font-weight:700; color:{get_style(ratio_v)}">
                {ratio_v:.2f} <small style="font-size:14px; color:#9ca3af;">(Ratio)</small>
            </div>
            <div style="font-size:13px; margin-top:5px;">
                Demand: <b>{v_act:,.0f}</b> kg<br>
                Capacity: <b>{V_cap:,.0f}</b> kg
            </div>
        </div>""", unsafe_allow_html=True)
    
    with c2:
        st.markdown(f"""<div class="detail-card">
            <h4 style="margin:0;">2. โมเมนต์ (Moment)</h4>
            <div style="font-size:24px; font-weight:700; color:{get_style(ratio_m)}">
                {ratio_m:.2f} <small style="font-size:14px; color:#9ca3af;">(Ratio)</small>
            </div>
            <div style="font-size:13px; margin-top:5px;">
                Demand: <b>{m_act:,.0f}</b> kg-m<br>
                Capacity: <b>{M_cap:,.0f}</b> kg-m
            </div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""<div class="detail-card">
            <h4 style="margin:0;">3. ระยะแอ่น (Defl.)</h4>
            <div style="font-size:24px; font-weight:700; color:{get_style(ratio_d)}">
                {ratio_d:.2f} <small style="font-size:14px; color:#9ca3af;">(Ratio)</small>
            </div>
            <div style="font-size:13px; margin-top:5px;">
                Actual: <b>{d_act:.2f}</b> cm<br>
                Limit: <b>{d_allow:.2f}</b> cm
            </div>
        </div>""", unsafe_allow_html=True)

    # ==========================================
    # 2. CALCULATION SHEET (รายการคำนวณละเอียด)
    # ==========================================
    st.write("---")
    st.subheader("📝 รายการคำนวณ (Calculation Sheet)")
    
    with st.expander("คลิกเพื่อดูรายการคำนวณโดยละเอียด", expanded=True):
        
        # STYLE CSS LOCAL
        st.markdown("""
        <style>
        .calc-header-th { 
            background-color: #f1f5f9; padding: 8px; border-radius: 5px; 
            font-weight: bold; margin-bottom: 10px; color: #334155; 
            border-left: 4px solid #3b82f6;
        }
        .calc-line {
            display: flex; justify-content: space-between; margin-bottom: 6px;
            font-family: 'Sarabun', sans-serif; font-size: 0.95rem;
        }
        .calc-label { color: #475569; }
        .calc-val { font-weight: 500; color: #0f172a; }
        .calc-result { 
            background-color: #eff6ff; padding: 8px; border-radius: 4px;
            text-align: center; margin-top: 5px; font-weight: bold; color: #1e40af;
        }
        </style>
        """, unsafe_allow_html=True)

        # PART 1: LOAD ANALYSIS
        st.markdown('<div class="calc-header-th">1. วิเคราะห์น้ำหนักบรรทุก (Load Analysis)</div>', unsafe_allow_html=True)
        col_la1, col_la2 = st.columns(2)
        
        factor_txt = "1.4(DL+LL)" if is_lrfd else "1.0(DL+LL)"
        factor_val = 1.4 if is_lrfd else 1.0
        
        with col_la1:
            st.write(f"**วิธีออกแบบ:** {method_str}")
            st.write(f"**Load Combination:** {factor_txt}")
        with col_la2:
            st.markdown(f"""
            <div class="calc-line"><span class="calc-label">น้ำหนักแผ่ (w)</span> <span class="calc-val">{w_load:,.0f} kg/m</span></div>
            <div class="calc-line"><span class="calc-label">น้ำหนักจุด (P)</span> <span class="calc-val">{p_load:,.0f} kg</span></div>
            <div style="border-top: 1px dashed #ccc; margin: 5px 0;"></div>
            <div class="calc-line"><span class="calc-label"><b>น้ำหนักแผ่ประลัย ($w_u$)</b></span> <span class="calc-val"><b>{fact_w:,.0f}</b> kg/m</span></div>
            <div class="calc-line"><span class="calc-label"><b>น้ำหนักจุดประลัย ($P_u$)</b></span> <span class="calc-val"><b>{fact_p:,.0f}</b> kg</span></div>
            """, unsafe_allow_html=True)

        # PART 2 & 3: SHEAR & MOMENT
        c_cal1, c_cal2 = st.columns(2)

        # --- SHEAR ---
        with c_cal1:
            st.markdown('<div class="calc-header-th">2. ตรวจสอบแรงเฉือน (Shear Check)</div>', unsafe_allow_html=True)
            
            # Text Variables
            safety_factor = "\phi = 1.00" if is_lrfd else "\Omega = 1.50"
            design_eq = "\phi V_n" if is_lrfd else "V_n / \Omega"
            
            st.markdown(f"""
            <div class="calc-line">
                <span class="calc-label">พื้นที่รับแรงเฉือน ($A_w$)</span>
                <span class="calc-val">{Aw:.2f} cm²</span>
            </div>
            <div class="calc-line">
                <span class="calc-label">กำลังรับแรงเฉือนระบุ ($V_n = 0.6F_yA_w$)</span>
                <span class="calc-val">{0.6*Fy*Aw:,.0f} kg</span>
            </div>
            <div class="calc-line">
                <span class="calc-label">ตัวคูณความปลอดภัย</span>
                <span class="calc-val">{safety_factor}</span>
            </div>
            <div class="calc-result">
                กำลังที่ยอมให้ ({design_eq}) = {V_cap:,.0f} kg
            </div>
            <div style="margin-top:10px; text-align:center;">
                <small>แรงเฉือนที่เกิดขึ้น ($V_u$) = {v_act:,.0f} kg</small><br>
                <b>Ratio = {ratio_v:.3f}</b>
            </div>
            """, unsafe_allow_html=True)

        # --- MOMENT (LTB) ---
        with c_cal2:
            st.markdown('<div class="calc-header-th">3. ตรวจสอบโมเมนต์ดัด (Moment Check)</div>', unsafe_allow_html=True)
            
            safety_factor_m = "\phi = 0.90" if is_lrfd else "\Omega = 1.67"
            design_eq_m = "\phi M_n" if is_lrfd else "M_n / \Omega"
            
            # แปลง Zone เป็นภาษาไทยที่เข้าใจง่าย
            zone_desc = ""
            if "Zone 1" in ltb_zone: zone_desc = "เหล็กครากเต็มหน้าตัด (Plastic Yielding)"
            elif "Zone 2" in ltb_zone: zone_desc = "การโก่งตัวเดาะแบบ Inelastic"
            else: zone_desc = "การโก่งตัวเดาะแบบ Elastic (อันตราย)"

            st.markdown(f"""
            <div class="calc-line">
                <span class="calc-label">ระยะค้ำยันด้านข้าง ($L_b$)</span>
                <span class="calc-val" style="color:#d97706; font-weight:bold;">{Lb:.2f} m</span>
            </div>
            <div class="calc-line">
                <span class="calc-label">พิกัดความยาว ($L_p, L_r$)</span>
                <span class="calc-val">{Lp_cm/100:.2f} m, {Lr_cm/100:.2f} m</span>
            </div>
            <div style="background:#fff7ed; padding:5px; border-radius:4px; font-size:0.85rem; margin:5px 0; border:1px solid #fed7aa;">
                <b>Zone Analysis:</b> {ltb_zone}<br>
                <span style="color:#7c2d12;">{zone_desc}</span>
            </div>
            <div class="calc-line">
                <span class="calc-label">กำลังระบุ ($M_n$)</span>
                <span class="calc-val">{Mn/100:,.0f} kg-m</span>
            </div>
            <div class="calc-result">
                กำลังที่ยอมให้ ({design_eq_m}) = {M_cap:,.0f} kg-m
            </div>
            <div style="margin-top:10px; text-align:center;">
                <small>โมเมนต์ที่เกิดขึ้น ($M_u$) = {m_act:,.0f} kg-m</small><br>
                <b>Ratio = {ratio_m:.3f}</b>
            </div>
            """, unsafe_allow_html=True)

        # PART 4: DEFLECTION
        st.markdown('<div class="calc-header-th">4. ตรวจสอบระยะแอ่นตัว (Deflection Check)</div>', unsafe_allow_html=True)
        c_def1, c_def2 = st.columns([1, 1])
        with c_def1:
            st.info("💡 คำนวณที่ Service Load (ไม่มี Load Factor)")
        with c_def2:
            st.markdown(f"""
            <div class="calc-line">
                <span class="calc-label">ระยะแอ่นที่ยอมให้ ($L/{defl_denom}$)</span>
                <span class="calc-val" style="color:green;">{d_allow:.2f} cm</span>
            </div>
            <div class="calc-line">
                <span class="calc-label">ระยะแอ่นจริง ($\Delta_{{actual}}$)</span>
                <span class="calc-val" style="color:blue;">{d_act:.2f} cm</span>
            </div>
            <div style="text-align:right; font-weight:bold; margin-top:5px;">
                Ratio = {ratio_d:.3f}
            </div>
            """, unsafe_allow_html=True)

    # ==========================================
    # 3. GRAPH (Span vs Capacity)
    # ==========================================
    st.write("---")
    st.markdown("### 📉 กราฟความสัมพันธ์ระยะพาด vs น้ำหนักบรรทุก")
    
    # ... (ส่วนสร้างกราฟเหมือนเดิม แต่เปลี่ยน Label เป็นภาษาไทยถ้าต้องการ) ...
    spans = np.linspace(1.0, 12.0, 50)
    w_cap_moment, w_cap_shear, w_cap_defl = [], [], []
    factor_load = 1.4 if is_lrfd else 1.0 
    
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
        lb_cm_g = l_cm_g 
        
        # Shear
        w_v = (2 * V_cap) / s
        
        # Moment
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
        
        # Deflection
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
    
    fig.update_layout(
        title="Safe Service Load vs. Span (น้ำหนักบรรทุกปลอดภัย ตามระยะพาด)",
        xaxis_title="ระยะพาด Span (m)",
        yaxis_title="น้ำหนักบรรทุกปลอดภัย (kg/m)",
        height=450
    )
    st.plotly_chart(fig, use_container_width=True)
