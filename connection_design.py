import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data):
    """
    ฟังก์ชันสำหรับคำนวณและแสดงผล Tab Connection Design (Enhanced Math UI)
    """
    # 1. ดึงค่า Section และแปลงหน่วย
    p = section_data
    h_cm, tw_cm = p['h']/10, p['tw']/10
    
    # 2. ตั้งค่าตัวแปร Bolt
    # Factor: LRFD ใช้ค่าเต็ม (1.5 เท่าของ ASD โดยประมาณในโค้ดนี้เพื่อ Simulation)
    bolt_factor = 1.5 if is_lrfd else 1.0 
    
    dia_mm = int(bolt_size[1:])
    dia_cm = dia_mm/10
    
    # กำหนดพื้นที่หน้าตัด (Area) ตามขนาด
    if bolt_size == "M16": b_area = 2.01
    elif bolt_size == "M20": b_area = 3.14
    elif bolt_size == "M22": b_area = 3.80
    else: b_area = 4.52 # M24 approx
    
    # 3. คำนวณกำลังรับแรง (Capacity)
    # -- Shear Strength (สมมติค่า Stress หน่วย kg/cm2 เพื่อการคำนวณ) --
    # ASD ~ 1000 ksc, LRFD ~ 1500 ksc (Simulation)
    F_v_base = 1000 
    v_bolt_shear_base = F_v_base * b_area 
    v_bolt_shear = v_bolt_shear_base * bolt_factor
    
    # -- Bearing Strength --
    # Formula: 1.2 * Fu * d * t (สมมติ Fu Plate = 4000 ksc)
    F_u_plate = 4000
    v_bolt_bear_base = 1.2 * F_u_plate * dia_cm * tw_cm
    v_bolt_bear = v_bolt_bear_base * (1.0 if not is_lrfd else 1.0) # Bearing usually similar or checked differently, keep simple here
    
    # Governing Capacity
    v_bolt = min(v_bolt_shear, v_bolt_bear)
    cap_type = "Shear" if v_bolt_shear < v_bolt_bear else "Bearing"

    # 4. คำนวณจำนวน Bolt ที่ต้องการ
    if v_bolt > 0:
        req_bolt_calc = V_design / v_bolt
        req_bolt = math.ceil(req_bolt_calc)
    else:
        req_bolt = 99
        
    if req_bolt % 2 != 0: req_bolt += 1 
    if req_bolt < 2: req_bolt = 2

    # 5. ตรวจสอบระยะ (Layout Check)
    n_rows = int(req_bolt / 2)
    pitch = 3 * dia_mm
    edge_dist = 1.5 * dia_mm
    req_height = (n_rows - 1) * pitch + 2 * edge_dist
    avail_height = p['h'] - 2*p['tf'] - 20 
    layout_ok = req_height <= avail_height

    # --- ส่วนแสดงผล (UI) ---
    st.subheader(f"🔩 Connection Design ({'LRFD' if is_lrfd else 'ASD'})")
    
    # Layout 2 Columns
    c_info, c_draw = st.columns([1, 1.2])
    
    with c_info:
        # Card ข้อมูลสรุป
        st.markdown(f"""
        <div class="conn-card">
            <h4 style="margin:0; color:#b7950b;">📋 Design Summary</h4>
            <div style="margin-top:10px; font-size:14px;"><b>Load ({'Vu' if is_lrfd else 'V'}):</b> <span style="font-size:18px; font-weight:bold;">{V_design:,.0f} kg</span></div>
            <div style="margin-top:5px; font-size:14px;"><b>Bolt:</b> {bolt_size} (A325/8.8)</div>
            <hr style="margin:10px 0;">
            <div style="display:flex; justify-content:space-between;">
                <span>Capacity:</span>
                <b>{v_bolt:,.0f} kg/bolt</b>
            </div>
            <div style="display:flex; justify-content:space-between;">
                <span>Required:</span>
                <b>{req_bolt} bolts</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # กล่องตรวจสอบ Layout
        status_color = "#27ae60" if layout_ok else "#c0392b"
        status_text = "PASSED" if layout_ok else "FAILED"
        st.markdown(f"""
        <div style="margin-top:15px; padding:12px; border-left:6px solid {status_color}; background:#f9f9f9; border-radius:6px;">
            <b>Geom Check:</b> <span style="color:{status_color}; font-weight:bold;">{status_text}</span>
            <div style="font-size:12px; color:#555; margin-top:4px;">H_req: {req_height:.0f} mm / H_avail: {avail_height:.0f} mm</div>
        </div>
        """, unsafe_allow_html=True)

    with c_draw:
        # วาดรูป (คงเดิม)
        fig_c = go.Figure()
        # Web
        fig_c.add_shape(type="rect", x0=-p['b']/2, y0=0, x1=p['b']/2, y1=p['h'], 
                        line=dict(color="RoyalBlue", width=1), fillcolor="rgba(65, 105, 225, 0.1)")
        # Flanges
        fig_c.add_shape(type="rect", x0=-p['b']/2, y0=0, x1=p['b']/2, y1=p['tf'], fillcolor="#1f618d", line_width=0)
        fig_c.add_shape(type="rect", x0=-p['b']/2, y0=p['h']-p['tf'], x1=p['b']/2, y1=p['h'], fillcolor="#1f618d", line_width=0)
        
        # Bolts
        cy = p['h'] / 2
        start_y = cy - ((n_rows-1)*pitch)/2
        gage = 60 if p['h'] < 200 else (100 if p['h'] > 400 else 80)
        
        bx, by = [], []
        for r in range(n_rows):
            y_pos = start_y + r*pitch
            bx.extend([-gage/2, gage/2])
            by.extend([y_pos, y_pos])
            
        fig_c.add_trace(go.Scatter(x=bx, y=by, mode='markers', 
                                   marker=dict(size=14, color='#c0392b', line=dict(width=2, color='white')), 
                                   name='Bolts'))
        
        fig_c.update_layout(
            xaxis=dict(visible=False, range=[-p['b'], p['b']]), 
            yaxis=dict(visible=False, scaleanchor="x"), 
            width=350, height=400, margin=dict(l=10, r=10, t=10, b=10), 
            plot_bgcolor='white'
        )
        st.plotly_chart(fig_c, use_container_width=True)

    # --- ส่วน Math Card (New!) ---
    st.markdown("---")
    with st.expander("🧮 ดูการคำนวณจุดต่อ (Connection Calculation)", expanded=True):
        st.caption(f"รายละเอียดการคำนวณ Bolt ({method})")
        
        mc1, mc2, mc3 = st.columns(3)
        
        with mc1:
            st.markdown(f'<div class="math-card"><div class="math-header">1. Bolt Shear ({bolt_size})</div>', unsafe_allow_html=True)
            st.markdown(f"Area ($A_b$) = {b_area} cm²")
            
            # Logic การแสดงสูตร
            if is_lrfd:
                # LRFD Display
                st.latex(r''' \phi R_n = \phi F_v A_b ''')
                st.latex(fr''' = 1.0 \times {F_v_base*1.5:.0f} \times {b_area} ''')
            else:
                # ASD Display
                st.latex(r''' R_n = F_v A_b ''')
                st.latex(fr''' = {F_v_base} \times {b_area} ''')
                
            st.markdown(f"<div style='text-align:center; font-weight:bold; color:#2980b9;'>= {v_bolt_shear:,.0f} kg</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with mc2:
            st.markdown(f'<div class="math-card"><div class="math-header">2. Bearing on Web</div>', unsafe_allow_html=True)
            st.markdown(f"Web ($t_w$) = {tw_cm} cm, Dia = {dia_cm} cm")
            
            # Formula Bearing
            st.latex(r''' R_n = 1.2 F_u d t_w ''')
            st.latex(fr''' = 1.2 \times {F_u_plate} \times {dia_cm} \times {tw_cm} ''')
            
            st.markdown(f"<div style='text-align:center; font-weight:bold; color:#2980b9;'>= {v_bolt_bear:,.0f} kg</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with mc3:
            st.markdown(f'<div class="math-card"><div class="math-header">3. Bolt Quantity</div>', unsafe_allow_html=True)
            st.markdown(f"Load V = {V_design:,.0f} kg")
            st.markdown(f"Control Cap = {v_bolt:,.0f} ({cap_type})")
            
            # Formula Quantity
            st.latex(r''' N = \frac{V_{load}}{Capacity} ''')
            st.latex(fr''' = \frac{{ {V_design:,.0f} }}{{ {v_bolt:,.0f} }} = {req_bolt_calc:.2f} ''')
            
            st.markdown(f"<div style='text-align:center; font-weight:bold; color:#c0392b; font-size:18px;'>Use {req_bolt} Bolts</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    return req_bolt, v_bolt
