import streamlit as st
import drawing_utils as du 

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    
    st.markdown(f"### 📐 Design Detail: **{conn_type}**")
    
    # --- Inputs ---
    c1, c2, c3 = st.columns(3)
    d_mm = int(bolt_size[1:])
    
    with c1:
        st.caption("🔩 Bolt Layout")
        n_rows = st.number_input("Rows", 2, 20, 3)
        n_cols = st.number_input("Cols", 1, 4, 2)
    
    with c2:
        st.caption("📏 Spacing (mm)")
        # แนะนำระยะ Pitch ขั้นต่ำ (3d)
        min_pitch = 3 * d_mm
        s_v = st.number_input("Pitch V", float(min_pitch), 300.0, float(max(75, min_pitch)))
        s_h = st.number_input("Pitch H", float(min_pitch), 150.0, float(max(60, min_pitch)))
        
    with c3:
        st.caption("🧱 Plate Config (mm)")
        e1_mm = st.number_input("Gap to Bolt (e1)", 10.0, 100.0, 50.0)
        t_plate = st.number_input("Thickness", 6.0, 40.0, 10.0)

    st.divider()
    
    # --- Custom Plate Dimensions (กำหนดขนาดเอง) ---
    st.markdown("##### 📏 Plate Dimensions (Customizable)")
    c4, c5 = st.columns(2)
    
    # คำนวณขนาดขั้นต่ำที่ต้องการ (Minimum Required Dimensions)
    # Height: (จำนวนช่องว่างแนวตั้ง * ระยะ) + (ระยะขอบบนล่าง 40mm x 2)
    req_h = (n_rows - 1) * s_v + 80 
    
    # Width: (Gap e1) + (จำนวนช่องว่างแนวนอน * ระยะ) + (ระยะขอบท้าย 40mm)
    req_w = e1_mm + (n_cols - 1) * s_h + 40
    
    with c4:
        # ให้ User กรอกเองได้ แต่ห้ามต่ำกว่า req_h
        plate_h = st.number_input(f"Plate Height (Min {req_h:.0f})", min_value=float(req_h), value=float(req_h), step=10.0)
        
    with c5:
        # ให้ User กรอกเองได้ แต่ห้ามต่ำกว่า req_w
        plate_w = st.number_input(f"Plate Width (Min {req_w:.0f})", min_value=float(req_w), value=float(req_w), step=5.0)

    # --- Calculations ---
    # คำนวณระยะขอบจริง (Actual Edge Distances) จากขนาดเพลทที่ User กรอก
    real_lv = (plate_h - (n_rows - 1) * s_v) / 2  # ระยะขอบบน/ล่างจริง
    l_side = plate_w - (e1_mm + (n_cols - 1) * s_h) # ระยะขอบท้ายจริง (e2)

    # Pack Data for Drawing
    beam_data = {
        'h': float(section_data.get('h', 350)), 
        'b': float(section_data.get('b', 175)), 
        'tf': float(section_data.get('tf', 11)), 
        'tw': float(section_data.get('tw', 7))
    }
    plate_data = {
        'h': plate_h, 
        'w': plate_w, 
        't': t_plate, 
        'e1': e1_mm, 
        'lv': real_lv, 
        'l_side': l_side
    }
    bolt_data = {
        'd': d_mm, 
        'rows': n_rows, 
        'cols': n_cols, 
        's_v': s_v, 
        's_h': s_h
    }

    # --- Drawings ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fig1 = du.create_plan_view(beam_data, plate_data, bolt_data)
        st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
        
    with col2:
        fig2 = du.create_front_view(beam_data, plate_data, bolt_data)
        st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
        
    with col3:
        fig3 = du.create_side_view(beam_data, plate_data, bolt_data)
        st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})

    # Summary Info
    st.info(f"""
    **Specification:**
    - **Plate Size:** {plate_w:.0f} (W) x {plate_h:.0f} (H) x {t_plate:.0f} (T) mm
    - **Bolt Layout:** {n_rows*n_cols} Bolts (M{d_mm}), Grade {bolt_grade}
    - **Edge Distances:** Top/Bot = {real_lv:.1f} mm, Side = {l_side:.1f} mm
    """)

    # Return calculation dummy (สามารถใส่ Logic คำนวณจริงตรงนี้ได้)
    return n_rows*n_cols, 10000
