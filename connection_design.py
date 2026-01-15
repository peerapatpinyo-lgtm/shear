import streamlit as st
import drawing_utils as du 

# ==========================================
# MAIN APP Logic
# ==========================================
def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    
    st.markdown(f"### 📐 Connection Detail Design: **{conn_type}**")
    
    # --- 1. FULL INPUT PARAMETERS ---
    st.info("📝 **Connection Parameters** (กรุณาระบุระยะอย่างละเอียด)")
    
    # สร้าง Tab ย่อยสำหรับการกรอกข้อมูลเพื่อให้เป็นระเบียบแต่ครบถ้วน
    in_col1, in_col2, in_col3 = st.columns(3)
    
    d_mm = int(bolt_size[1:])
    
    with in_col1:
        st.markdown("##### 🔩 Bolt Configuration")
        n_rows = st.number_input("จำนวนแถวแนวดิ่ง (Rows)", min_value=2, max_value=20, value=3)
        n_cols = st.number_input("จำนวนแถวแนวราบ (Columns)", min_value=1, max_value=4, value=2)
        bolt_gr = st.selectbox("เกรดน็อต (Grade)", ["A325", "A490", "Gr.8.8"], index=0)
    
    with in_col2:
        st.markdown("##### 📏 Spacing & Pitch")
        # Default logic
        min_sv = 3 * d_mm
        min_sh = 3 * d_mm
        s_v = st.number_input(f"ระยะห่างแนวดิ่ง (sv) [Min {min_sv}]", min_value=0.0, value=float(max(75, min_sv)), step=5.0)
        s_h = st.number_input(f"ระยะห่างแนวราบ (sh) [Min {min_sh}]", min_value=0.0, value=float(max(60, min_sh)), step=5.0)
        
    with in_col3:
        st.markdown("##### 🧱 Plate Geometry")
        e1_mm = st.number_input("ระยะขอบถึงน็อต (e1/Gap)", min_value=10.0, value=50.0, step=5.0)
        t_plate = st.number_input("ความหนาเพลท (Thickness)", min_value=6.0, value=10.0, step=1.0)
        
        # Auto-calculate suggestion for Height
        min_req_h = (n_rows - 1) * s_v + 2.5 * d_mm * 2 # Approximate edge
        plate_h_input = st.number_input("ความสูงเพลท (Plate H)", min_value=float(min_req_h), value=float(min_req_h + 40))

    # --- Calculations ---
    # Width calculation based on inputs
    plate_w = e1_mm + (n_cols - 1) * s_h + 40 # Default edge 40mm at end
    # Actual vertical edge distance
    real_lv = (plate_h_input - (n_rows - 1) * s_v) / 2
    l_side = plate_w - (e1_mm + (n_cols - 1) * s_h)

    # Display Check
    st.markdown("---")
    res_c1, res_c2, res_c3 = st.columns(3)
    res_c1.metric("Plate Size (HxWxT)", f"{plate_h_input:.0f} x {plate_w:.0f} x {t_plate:.0f} mm")
    res_c2.metric("Total Bolts", f"{n_rows * n_cols} Nos.", f"M{d_mm}")
    res_c3.metric("Vertical Edge (Lv)", f"{real_lv:.1f} mm", help="Distance from plate edge to first bolt center")

    # --- PACK DATA ---
    beam_data = {
        'h': float(section_data.get('h', 350)), 'b': float(section_data.get('b', 175)),
        'tf': float(section_data.get('tf', 11)), 'tw': float(section_data.get('tw', 7))
    }
    plate_data = {'h': plate_h_input, 'w': plate_w, 't': t_plate, 'e1': e1_mm, 'lv': real_lv, 'l_side': l_side}
    bolt_data = {'d': d_mm, 'rows': n_rows, 'cols': n_cols, 's_v': s_v, 's_h': s_h}

    # --- 2. DRAWING SECTION ---
    st.markdown("#### 🏗️ Construction Shop Drawings")
    
    tab_draw1, tab_draw2 = st.tabs(["📐 2D Layout (All Views)", "🔍 Detailed View"])
    
    with tab_draw1:
        col_d1, col_d2, col_d3 = st.columns(3)
        with col_d1:
            fig1 = du.create_plan_view(beam_data, plate_data, bolt_data)
            st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
        with col_d2:
            fig2 = du.create_front_view(beam_data, plate_data, bolt_data)
            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
        with col_d3:
            fig3 = du.create_side_view(beam_data, plate_data, bolt_data)
            st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})

    with tab_draw2:
        st.info("ขยายดูรายละเอียดเฉพาะจุด (Zoomed View)")
        c_z1, c_z2 = st.columns(2)
        with c_z1:
            st.plotly_chart(fig2, use_container_width=True) # Front Large
        with c_z2:
            st.plotly_chart(fig1, use_container_width=True) # Plan Large

    return n_rows * n_cols, 10000
