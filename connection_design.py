import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data):
    """
    ฟังก์ชันสำหรับคำนวณและแสดงผล Tab Connection Design
    """
    # 1. ดึงค่า Section
    p = section_data
    h_cm, tw_cm = p['h']/10, p['tw']/10
    
    # 2. ตั้งค่าตัวแปร Bolt
    # LRFD Bolt Cap approx 1.5x of ASD for visualization logic consistency
    bolt_factor = 1.5 if is_lrfd else 1.0 
    
    dia_mm = int(bolt_size[1:])
    dia_cm = dia_mm/10
    # พื้นที่หน้าตัด Bolt
    b_area = 3.14 if bolt_size=="M20" else (2.01 if bolt_size=="M16" else 3.8)
    
    # 3. คำนวณกำลังรับแรง (Capacity)
    # Shear Strength
    v_bolt_shear_base = 1000 * b_area 
    # Bearing Strength
    v_bolt_bear_base = 1.2 * 4000 * dia_cm * tw_cm
    
    # Min Capacity per bolt
    v_bolt = min(v_bolt_shear_base, v_bolt_bear_base) * bolt_factor

    # 4. คำนวณจำนวน Bolt ที่ต้องการ
    if v_bolt > 0:
        req_bolt = math.ceil(V_design / v_bolt)
    else:
        req_bolt = 99
        
    if req_bolt % 2 != 0: req_bolt += 1 
    if req_bolt < 2: req_bolt = 2

    # 5. ตรวจสอบระยะ (Layout Check)
    n_rows = int(req_bolt / 2)
    pitch = 3 * dia_mm
    edge_dist = 1.5 * dia_mm
    req_height = (n_rows - 1) * pitch + 2 * edge_dist
    avail_height = p['h'] - 2*p['tf'] - 20 # ลบปีกและเผื่อระยะนิดหน่อย
    layout_ok = req_height <= avail_height

    # --- ส่วนแสดงผล (UI) ---
    st.subheader(f"🔩 Connection Design ({'LRFD' if is_lrfd else 'ASD'})")
    c_info, c_draw = st.columns([1, 1.5])
    
    with c_info:
        # Card ข้อมูล
        st.markdown(f"""
        <div class="conn-card">
            <h4 style="margin:0; color:#b7950b;">📋 Design Criteria</h4>
            <div style="margin-top:10px;"><b>Method:</b> {method}</div>
            <div style="margin-top:5px;"><b>Load (Vu):</b> <span style="font-size:22px; font-weight:bold; color:#d35400;">{V_design:,.0f} kg</span></div>
            <hr>
            <div><b>Bolt Cap ({bolt_size}):</b> {v_bolt:,.0f} kg/bolt</div>
            <div><b>Required:</b> {V_design/v_bolt:.2f} → <b style="color:#2980b9; font-size:18px;">{req_bolt} pcs</b></div>
        </div>
        """, unsafe_allow_html=True)
        
        # กล่องตรวจสอบ Layout
        status_color = "#27ae60" if layout_ok else "#c0392b"
        status_text = "PASSED" if layout_ok else "FAILED"
        st.markdown(f"""
        <div style="margin-top:20px; padding:15px; border-left:6px solid {status_color}; background:#f9f9f9;">
            <b>Layout Check:</b> <span style="color:{status_color}; font-weight:bold;">{status_text}</span>
            <br><small>Space req: {req_height:.0f} mm / Avail: {avail_height:.0f} mm</small>
        </div>
        """, unsafe_allow_html=True)

    with c_draw:
        # วาดรูป
        fig_c = go.Figure()
        # Web (โปร่งแสง)
        fig_c.add_shape(type="rect", x0=-p['b']/2, y0=0, x1=p['b']/2, y1=p['h'], 
                        line=dict(color="RoyalBlue", width=1), fillcolor="rgba(65, 105, 225, 0.1)")
        # Flanges (สีเข้ม)
        fig_c.add_shape(type="rect", x0=-p['b']/2, y0=0, x1=p['b']/2, y1=p['tf'], fillcolor="#1f618d", line_width=0)
        fig_c.add_shape(type="rect", x0=-p['b']/2, y0=p['h']-p['tf'], x1=p['b']/2, y1=p['h'], fillcolor="#1f618d", line_width=0)
        
        # Bolts positions
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
            width=400, height=500, margin=dict(l=20, r=20, t=20, b=20), 
            plot_bgcolor='white'
        )
        st.plotly_chart(fig_c)
        
    # Return ค่าที่อาจต้องใช้ต่อ (ถ้ามี)
    return req_bolt, v_bolt
