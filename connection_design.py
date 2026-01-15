import streamlit as st
# 👇 Import ไฟล์ที่เราเพิ่งสร้าง
import drawing_utils as du 

# ==========================================
# MAIN APP Logic
# ==========================================
def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    
    st.markdown(f"### 📐 Connection Design: **{conn_type}**")

    # 1. INPUTS SECTION
    tab1, tab2 = st.tabs(["📝 Design Inputs", "🏗️ Shop Drawing (CAD Mode)"])
    
    with tab1:
        # --- Bolt & Plate Inputs ---
        d_mm = int(bolt_size[1:])
        c1, c2, c3 = st.columns(3)
        with c1:
            st.info(f"**🔩 Bolt: {bolt_size}**")
            n_rows = st.number_input("Rows (V)", 2, 12, 3)
            n_cols = st.number_input("Cols (H)", 1, 3, 2)
            s_v = st.number_input("Pitch V (sv)", 0.0, 300.0, float(max(75, 3*d_mm)))
            s_h = st.number_input("Pitch H (sh)", 0.0, 150.0, float(max(60, 3*d_mm))) if n_cols > 1 else 0
        
        with c2:
            st.warning("**📏 Geometry**")
            e1_mm = st.number_input("Gap (e1)", 10.0, 100.0, 50.0)
            t_plate = st.number_input("Plate Thk", 6.0, 25.0, 10.0)
            
            # Auto Calc Height/Width
            min_h = (n_rows-1)*s_v + 80
            plate_h = st.number_input("Plate H", min_value=float(min_h), value=float(min_h))
            
            # Calculate Derived Values
            plate_w = e1_mm + (n_cols-1)*s_h + 40 # Default edge 40
            real_lv = (plate_h - (n_rows-1)*s_v) / 2
            l_side = plate_w - (e1_mm + (n_cols-1)*s_h)

        with c3:
            st.success("**📊 Check**")
            st.write(f"Plate W: **{plate_w:.0f} mm**")
            st.write(f"Vert Edge: **{real_lv:.1f} mm**")
            n_total = n_rows * n_cols
            st.metric("Total Bolts", n_total)

    # 2. DRAWING SECTION
    with tab2:
        st.divider()
        col_view1, col_view2 = st.columns([1.2, 1])
        
        # --- PACK DATA (ห่อข้อมูลเป็นก้อน เพื่อส่งให้ไฟล์ drawing_utils) ---
        # ข้อมูลคาน
        beam_data = {
            'h': float(section_data.get('h', 300)),
            'b': float(section_data.get('b', 150)),
            'tf': float(section_data.get('tf', 10)),
            'tw': float(section_data.get('tw', 8))
        }
        # ข้อมูลเพลท
        plate_data = {
            'h': plate_h,
            'w': plate_w,
            't': t_plate,
            'e1': e1_mm,
            'lv': real_lv,
            'l_side': l_side
        }
        # ข้อมูลน็อต
        bolt_data = {
            'd': d_mm,
            'rows': n_rows,
            'cols': n_cols,
            's_v': s_v,
            's_h': s_h
        }

        # --- CALL FUNCTIONS FROM drawing_utils.py ---
        with col_view1:
            # เรียกใช้ฟังก์ชันสร้างรูป Section
            fig_sec = du.create_section_view(beam_data, plate_data, bolt_data)
            st.plotly_chart(fig_sec, use_container_width=True)

        with col_view2:
            # เรียกใช้ฟังก์ชันสร้างรูป Elevation
            fig_elev = du.create_elevation_view(beam_data, plate_data, bolt_data)
            st.plotly_chart(fig_elev, use_container_width=True)

    return n_total, 10000 # Return dummy design values
