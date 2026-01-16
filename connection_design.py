# connection_design.py (V13 - Fixed Keys for Drawing)
import math
import streamlit as st
try:
    import drawing_utils as drw
except ImportError:
    st.warning("Warning: drawing_utils.py not found. Drawings will not be displayed.")

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade):
    """
    ฟังก์ชันสำหรับแสดงผลหน้า Tab Connection ใน Streamlit
    """
    st.subheader(f"🔩 Connection Design: {conn_type}")
    
    # ดึงค่าขนาดโบลท์ (เช่น "M20" -> 20)
    d = int(bolt_size.replace("M", ""))
    
    # ส่วนรับ Input
    col1, col2 = st.columns(2)
    with col1:
        t_plate = st.number_input("Plate Thickness (mm)", min_value=1, value=9)
        h_plate = st.number_input("Plate Height (mm)", min_value=50, value=200)
        weld_size = st.number_input("Weld Size (mm)", min_value=3, value=6)
        e1_dist = st.number_input("Horizontal Edge Dist (e1) (mm)", min_value=1, value=40)
    
    with col2:
        bolt_rows = st.number_input("Number of Rows", min_value=1, value=3)
        bolt_cols = st.number_input("Number of Columns", min_value=1, value=1)
        s_v = st.number_input("Vertical Spacing (s_v) (mm)", min_value=1, value=75)
        s_h = st.number_input("Horizontal Spacing (s_h) (mm)", min_value=0, value=60)
        l_side = st.number_input("Final Edge Distance (mm)", min_value=1, value=40)

    # คำนวณความกว้างแผ่นเหล็ก (W_pl) อัตโนมัติเพื่อให้ Drawing วาดถูก
    w_plate_calc = e1_dist + ((bolt_cols - 1) * s_h) + l_side

    # เตรียม Data สำหรับคำนวณและวาดรูป (Fix Keys ให้ตรงกับ drawing_utils)
    plate = {
        't': t_plate, 
        'h': h_plate, 
        'w': w_plate_calc,
        'lv': 40, 
        'e1': e1_dist,    # เพิ่ม Key นี้
        'l_side': l_side, 
        'weld_size': weld_size,
        'Fy': 250, 
        'Fu': 400
    }
    
    bolts = {
        'd': d, 
        'rows': bolt_rows, 
        'cols': bolt_cols,
        's_v': s_v, 
        's_h': s_h,       # เพิ่ม Key นี้
        'Fnv': 372
    }

    V_load_kn = V_design / 100

    # --- ส่วนการแสดงผล DRAWING 3 มุม ---
    if 'drw' in globals():
        st.divider()
        st.subheader("🎨 Engineering Drawing (3 Views)")
        
        beam_draw_data = {
            'h': section_data['h'], 
            'b': section_data['b'], 
            'tf': section_data['tf'], 
            'tw': section_data['tw']
        }
        
        # แสดงผล Plotly Chart
        col_draw_a, col_draw_b = st.columns(2)
        with col_draw_a:
            st.plotly_chart(drw.create_plan_view(beam_draw_data, plate, bolts), use_container_width=True)
            st.plotly_chart(drw.create_side_view(beam_draw_data, plate, bolts), use_container_width=True)
        with col_draw_b:
            st.plotly_chart(drw.create_front_view(beam_draw_data, plate, bolts), use_container_width=True)

    # ส่วนสร้างรายงานคำนวณ
    report_md = generate_report(V_load_kn, section_data, plate, bolts, is_lrfd)
    st.markdown(report_md, unsafe_allow_html=True)
    
    return (bolt_rows * bolt_cols), V_load_kn

def generate_report(V_load, beam, plate, bolts, is_lrfd=True):
    # (โค้ดส่วนนี้เหมือนเดิมทุุกประการตามที่คุณส่งมา)
    # ผมละไว้ในฐานที่เข้าใจเพื่อความกระชับ แต่ในไฟล์จริงต้องมีครบครับ
    # ... (Copy ส่วน generate_report จากของเดิมมาใส่ได้เลยครับ) ...
    return "Report Content" # Placeholder
