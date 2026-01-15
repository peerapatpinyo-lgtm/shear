import streamlit as st
import drawing_utils as du 

# ==========================================
# MAIN APP Logic
# ==========================================
def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    
    st.markdown(f"### 📐 Structural Detail: **{conn_type}**")
    st.caption("Designed by: Senior Structural Engineer (Auto-Generated)")

    # 1. INPUTS SECTION (Compact)
    with st.expander("⚙️ Connection Parameters (Click to Edit)", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        d_mm = int(bolt_size[1:])
        
        with c1:
            n_rows = st.number_input("Rows (V)", 2, 10, 3)
            n_cols = st.number_input("Cols (H)", 1, 3, 2)
        with c2:
            s_v = st.number_input("Pitch V", 0.0, 300.0, float(max(75, 3*d_mm)))
            s_h = st.number_input("Pitch H", 0.0, 150.0, float(max(60, 3*d_mm)))
        with c3:
            e1_mm = st.number_input("Gap (e1)", 10.0, 100.0, 50.0)
            t_plate = st.number_input("Plate Thk", 6.0, 25.0, 10.0)
        with c4:
            # Auto Calc
            min_h = (n_rows-1)*s_v + 80
            plate_h = st.number_input("Plate H", min_value=float(min_h), value=float(min_h))
            
    # Calculations
    plate_w = e1_mm + (n_cols-1)*s_h + 40
    real_lv = (plate_h - (n_rows-1)*s_v) / 2
    l_side = plate_w - (e1_mm + (n_cols-1)*s_h)

    # --- PACK DATA ---
    beam_data = {
        'h': float(section_data.get('h', 350)), 'b': float(section_data.get('b', 175)),
        'tf': float(section_data.get('tf', 11)), 'tw': float(section_data.get('tw', 7))
    }
    plate_data = {'h': plate_h, 'w': plate_w, 't': t_plate, 'e1': e1_mm, 'lv': real_lv, 'l_side': l_side}
    bolt_data = {'d': d_mm, 'rows': n_rows, 'cols': n_cols, 's_v': s_v, 's_h': s_h}

    # 2. DRAWING SECTION (3 VIEWS)
    st.divider()
    st.markdown("#### 🏗️ Construction Drawings")
    
    # Create 3 Columns for the drawings
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("Top View (Plan)")
        fig1 = du.create_plan_view(beam_data, plate_data, bolt_data)
        st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
        
    with col2:
        st.info("Front View (Elevation)")
        fig2 = du.create_front_view(beam_data, plate_data, bolt_data)
        st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
        
    with col3:
        st.info("Side View (Section)")
        fig3 = du.create_side_view(beam_data, plate_data, bolt_data)
        st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})

    # Summary Text
    st.success(f"**Summary:** Plate {plate_w:.0f}x{plate_h:.0f}x{t_plate:.0f} mm | {n_rows*n_cols} Bolts M{d_mm}")

    return n_rows*n_cols, 10000
