import streamlit as st
import math
import plotly.graph_objects as go

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type="Beam-to-Column (Flange)", support_data=None):
    """
    ฟังก์ชันคำนวณจุดต่อแบบมืออาชีพ รองรับ Beam-to-Beam และ Beam-to-Column
    """
    p = section_data
    h_cm, tw_cm = p['h']/10, p['tw']/10
    
    # 1. ตั้งค่าพื้นฐาน Bolt
    bolt_factor = 1.5 if is_lrfd else 1.0 
    dia_mm = int(bolt_size[1:])
    dia_cm = dia_mm/10
    
    # Area (cm2)
    b_areas = {"M16": 2.01, "M20": 3.14, "M22": 3.80, "M24": 4.52}
    b_area = b_areas.get(bolt_size, 3.14)
    
    # 2. Capacity Calculation
    # Shear Strength
    F_v = 1000 * bolt_factor # ksc (Base simulation)
    v_shear = F_v * b_area 
    
    # Bearing Strength (1.2 * Fu * d * t)
    F_u = 4000 # ksc
    v_bearing = 1.2 * F_u * dia_cm * tw_cm
    
    # Governing Bolt Capacity
    v_bolt_cap = min(v_shear, v_bearing)
    
    # 3. Connection Type Logic (สมจริงขึ้น)
    # ถ้าเป็น Beam-to-Beam มักต้องบากคาน (Cope) ทำให้กำลังรับแรงเฉือนลดลง
    reduction_factor = 1.0
    if conn_type == "Beam-to-Beam":
        reduction_factor = 0.85 # สมมติลดทอนกำลังจากการบากคาน (Coping)
        st.caption("⚠️ Note: Capacity reduced by 15% due to beam coping.")

    # 4. จำนวนน็อต
    req_bolt_calc = V_design / (v_bolt_cap * reduction_factor)
    n_bolts = math.ceil(req_bolt_calc)
    if n_bolts < 2: n_bolts = 2
    if n_bolts % 2 != 0: n_bolts += 1 # ปรับให้เป็นเลขคู่เพื่อความสวยงามในงานติดตั้ง
    
    # 5. Layout Check (AISC Standard)
    n_rows = int(n_bolts / 2)
    pitch = 3.0 * dia_mm # ระยะห่างระหว่างแถว
    edge = 1.5 * dia_mm  # ระยะขอบ
    h_req = (n_rows - 1) * pitch + (2 * edge)
    
    # ความสูงที่ใช้งานได้ (Available Height)
    h_avail = p['h'] - (2 * p['tf']) - 20 # หักปีกและระยะมน
    if conn_type == "Beam-to-Beam":
        h_avail -= 40 # หักส่วนที่บากปีกออก (Top Cope)

    is_ok = h_req <= h_avail

    # --- UI Rendering ---
    st.markdown(f"### 🔩 {conn_type} Details")
    
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.info(f"**Target Force:** {V_design:,.0f} kg")
        st.write(f"**Bolt Capacity:** {v_bolt_cap:,.0f} kg/bolt")
        st.metric("Required Bolts", f"{n_bolts} Nos", delta=f"{n_bolts-req_bolt_calc:.2f} extra", delta_color="normal")
        
        # แสดงสถานะความสูง
        status = "✅ Space OK" if is_ok else "❌ Insufficient Space"
        st.markdown(f"**Geom Check:** {status}")
        st.progress(min(h_req/h_avail, 1.0))
        st.caption(f"Req: {h_req:.0f}mm / Avail: {h_avail:.0f}mm")

    with col2:
        # Drawing Logic
        fig = go.Figure()
        
        # 1. Draw Support (Column or Main Beam)
        if "Column" in conn_type:
            # วาดหน้าตัดเสาเป็นสีเทาเข้ม
            fig.add_shape(type="rect", x0=-120, y0=-20, x1=-100, y1=p['h']+20, fillcolor="#475569")
        else:
            # คานตัวหลัก (Main Beam)
            fig.add_shape(type="rect", x0=-150, y0=-20, x1=-110, y1=p['h']+20, fillcolor="#94a3b8")

        # 2. Draw Beam Web
        fig.add_shape(type="rect", x0=-100, y0=0, x1=150, y1=p['h'], line_color="RoyalBlue", fillcolor="rgba(65, 105, 225, 0.1)")
        
        # 3. Draw Bolts
        start_y = (p['h']/2) - ((n_rows-1)*pitch)/2
        for r in range(n_rows):
            y = start_y + r*pitch
            for x in [-30, 30]: # Gage 60mm
                fig.add_trace(go.Scatter(x=[x], y=[y], mode='markers', marker=dict(size=12, color='#ef4444', line=dict(width=1, color='white'))))

        fig.update_layout(showlegend=False, height=350, margin=dict(l=0,r=0,t=0,b=0), xaxis_visible=False, yaxis_visible=False, plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)

    return n_bolts, v_bolt_cap
