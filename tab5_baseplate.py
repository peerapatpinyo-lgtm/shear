import streamlit as st
import streamlit.components.v1 as components
import steel_db
import baseplate_drawer  # Import ไฟล์วาดรูปที่เราสร้างขึ้น

def render(res_ctx, v_design):
    # --- 1. CONFIGURATION & INPUTS ---
    with st.container(border=True):
        st.markdown("##### 📐 Ultimate Shop Drawing Control")
        c_m1, c_m2, c_m3 = st.columns([1, 1, 1])
        with c_m1:
            sec_list = steel_db.get_section_list()
            col_name = st.selectbox("Column Size", sec_list, index=sec_list.index(res_ctx['sec_name']) if res_ctx['sec_name'] in sec_list else 13)
            p = steel_db.get_properties(col_name)
            ch, cb, ctw, ctf = float(p['h']), float(p['b']), float(p['tw']), float(p['tf'])
        with c_m2:
            clr_x = st.number_input("Clearance X (mm)", value=50.0)
            clr_y = st.number_input("Clearance Y (mm)", value=60.0)
            tp = st.number_input("Plate Thk. (mm)", value=25.0)
        with c_m3:
            edge_x = st.number_input("Edge X (mm)", value=50.0)
            edge_y = st.number_input("Edge Y (mm)", value=50.0)
            bolt_d = st.selectbox("Bolt Dia.", [20, 24, 30], index=0)

    # --- 2. GEOMETRY CALC ---
    sx, sy = cb + (2 * clr_x), ch - (2 * ctf) + (2 * clr_y)
    B, N = sx + (2 * edge_x), sy + (2 * edge_y)
    grout_h = 50.0
    
    # --- 3. PREPARE PARAMETERS & DRAW ---
    # รวบรวมข้อมูลทั้งหมดใส่ Dictionary เพื่อส่งให้ Drawer
    drawing_params = {
        'B': B, 'N': N, 'cb': cb, 'ch': ch, 'ctw': ctw, 'ctf': ctf,
        'sx': sx, 'sy': sy, 'tp': tp, 'grout_h': grout_h,
        'edge_x': edge_x, 'edge_y': edge_y, 'clr_x': clr_x, 'clr_y': clr_y,
        'col_name': col_name, 'bolt_d': bolt_d
    }
    
    # เรียกฟังก์ชันจากไฟล์ baseplate_drawer
    svg_code = baseplate_drawer.get_svg_drawing(drawing_params)
    
    # แสดงผล
    components.html(svg_code, height=1300, scrolling=True)
