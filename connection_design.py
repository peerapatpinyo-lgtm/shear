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
        min_pitch = 3 * d_mm
        s_v = st.number_input("Pitch V", float(min_pitch), 300.0, float(max(75, min_pitch)))
        s_h = st.number_input("Pitch H", float(min_pitch), 150.0, float(max(60, min_pitch)))
        
    with c3:
        st.caption("🧱 Plate Config (mm)")
        e1_mm = st.number_input("Gap to Bolt (e1)", 10.0, 100.0, 50.0)
        t_plate = st.number_input("Thickness", 6.0, 40.0, 10.0)

    st.divider()
    
    # --- Custom Plate Dimensions ---
    st.markdown("##### 📏 Plate Dimensions (Customizable)")
    c4, c5 = st.columns(2)
    req_h = (n_rows - 1) * s_v + 80 
    req_w = e1_mm + (n_cols - 1) * s_h + 40
    
    with c4:
        plate_h = st.number_input(f"Plate Height (Min {req_h:.0f})", min_value=float(req_h), value=float(req_h), step=10.0)
    with c5:
        plate_w = st.number_input(f"Plate Width (Min {req_w:.0f})", min_value=float(req_w), value=float(req_w), step=5.0)

    # --- Calculations & Data ---
    real_lv = (plate_h - (n_rows - 1) * s_v) / 2
    l_side = plate_w - (e1_mm + (n_cols - 1) * s_h)

    beam_data = {'h': float(section_data.get('h', 350)), 'b': float(section_data.get('b', 175)), 'tf': float(section_data.get('tf', 11)), 'tw': float(section_data.get('tw', 7))}
    plate_data = {'h': plate_h, 'w': plate_w, 't': t_plate, 'e1': e1_mm, 'lv': real_lv, 'l_side': l_side}
    bolt_data = {'d': d_mm, 'rows': n_rows, 'cols': n_cols, 's_v': s_v, 's_h': s_h}

    # --- Drawings (พร้อม Config สำหรับ Download) ---
    
    # ++ ตั้งค่า Plotly Config ให้โหลดรูปได้ ++
    plotly_config = {
        'displayModeBar': True, # แสดงแถบเครื่องมือ
        'displaylogo': False,   # ซ่อนโลโก้ Plotly
        'modeBarButtonsToRemove': ['zoom', 'pan', 'select', 'lasso2d', 'autoScale', 'resetScale'], # เอาปุ่มที่ไม่จำเป็นออก เหลือแค่ save as image
        'toImageButtonOptions': {
            'format': 'png', # หรือ 'svg', 'jpeg'
            'filename': f'connection_{conn_type}_{n_rows}x{n_cols}',
            'height': 800, # ความละเอียดรูปที่จะโหลด
            'width': 800,
            'scale': 2 # เพิ่มความคมชัด (Retina)
        }
    }

    col1, col2, col3 = st.columns(3)
    
    with col1:
        fig1 = du.create_plan_view(beam_data, plate_data, bolt_data)
        st.plotly_chart(fig1, use_container_width=True, config=plotly_config)
        
    with col2:
        fig2 = du.create_front_view(beam_data, plate_data, bolt_data)
        st.plotly_chart(fig2, use_container_width=True, config=plotly_config)
        
    with col3:
        fig3 = du.create_side_view(beam_data, plate_data, bolt_data)
        st.plotly_chart(fig3, use_container_width=True, config=plotly_config)

    # Summary Info
    st.info(f"""
    **Specification:**
    - **Plate Size:** {plate_w:.0f} (W) x {plate_h:.0f} (H) x {t_plate:.0f} (T) mm
    - **Bolt Layout:** {n_rows*n_cols} Bolts (M{d_mm})
    """)

    return n_rows*n_cols, 10000
