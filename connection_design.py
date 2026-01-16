# connection_design.py (V13 - Final Fix)
import math
import streamlit as st

# พยายาม Import drawing_utils และตรวจสอบ Error
try:
    import drawing_utils as drw
    DRAWING_AVAILABLE = True
except Exception as e:
    DRAWING_AVAILABLE = False
    DRAWING_ERROR = str(e)

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade):
    st.subheader(f"🔩 Connection Design: {conn_type}")
    
    # 1. จัดการข้อมูล Bolt Size (M16, M20 -> 16, 20)
    try:
        d = int(''.join(filter(str.isdigit, bolt_size)))
    except:
        d = 20

    # 2. รับ Input จากผู้ใช้ (จัดกลุ่มให้ตรงกับ Drawing Utils)
    col1, col2 = st.columns(2)
    with col1:
        t_plate = st.number_input("Plate Thickness (mm)", min_value=1, value=9)
        h_plate = st.number_input("Plate Height (mm)", min_value=50, value=200)
        weld_size = st.number_input("Weld Size (mm)", min_value=3, value=6)
        e1 = st.number_input("Edge distance from Col (e1) (mm)", min_value=10, value=40)
    
    with col2:
        bolt_rows = st.number_input("Number of Rows", min_value=1, value=3)
        bolt_cols = st.number_input("Number of Columns", min_value=1, value=1)
        s_v = st.number_input("Vertical Spacing (s_v) (mm)", min_value=10, value=75)
        s_h = st.number_input("Horizontal Spacing (s_h) (mm)", min_value=0, value=60)
        l_side = st.number_input("Edge distance to Beam end (mm)", min_value=10, value=40)

    # 3. เตรียม Material & Bolt Properties
    bolt_props = {"A325 (High Strength)": 372, "Grade 8.8 (Standard)": 320, "A490 (Premium)": 496}
    fnv = bolt_props.get(bolt_grade, 372)
    
    # คำนวณความกว้าง Plate อัตโนมัติ (สำคัญมากสำหรับการวาดรูป)
    w_plate = e1 + (max(0, bolt_cols - 1) * s_h) + l_side

    # 4. สร้าง Dictionary ให้ตรงกับ drawing_utils.py เป๊ะๆ
    plate_data = {
        't': t_plate, 'h': h_plate, 'w': w_plate,
        'lv': 40, 'e1': e1, 'l_side': l_side, 
        'weld_size': weld_size, 'Fy': 250, 'Fu': 400
    }
    
    bolts_data = {
        'd': d, 'rows': bolt_rows, 'cols': bolt_cols,
        's_v': s_v, 's_h': s_h, 'Fnv': fnv
    }

    # 5. ส่วนแสดงผล DRAWING (ต้องขึ้นก่อน Report)
    if DRAWING_AVAILABLE:
        st.divider()
        st.subheader("🎨 Engineering Drawing (3 Views)")
        
        # จัดเตรียมข้อมูล Beam
        beam_draw = {
            'h': section_data['h'], 'b': section_data['b'], 
            'tf': section_data['tf'], 'tw': section_data['tw']
        }
        
        # แสดงผล 3 มุม
        c_drw1, c_drw2 = st.columns(2)
        with c_drw1:
            st.plotly_chart(drw.create_plan_view(beam_draw, plate_data, bolts_data), use_container_width=True)
            st.plotly_chart(drw.create_side_view(beam_draw, plate_data, bolts_data), use_container_width=True)
        with c_drw2:
            st.plotly_chart(drw.create_front_view(beam_draw, plate_data, bolts_data), use_container_width=True)
    else:
        st.error(f"❌ Drawing Module Error: {DRAWING_ERROR}")

    # 6. ส่วนคำนวณและสร้าง Report
    V_load_kn = V_design / 100
    report_md = generate_report(V_load_kn, section_data, plate_data, bolts_data, is_lrfd)
    st.markdown(report_md, unsafe_allow_html=True)
    
    return (bolt_rows * bolt_cols), V_load_kn

def generate_report(V_load, beam, plate, bolts, is_lrfd=True):
    # --- AISC Calculation Logic ---
    d = bolts['d']
    h_hole = d + 2 
    n_rows = bolts['rows']
    n_cols = bolts['cols']
    n_total = n_rows * n_cols
    
    t_pl = plate['t']
    h_pl = plate['h']
    lv = plate['lv'] 
    l_side = plate['l_side'] 
    weld_size = plate['weld_size']
    Fy_pl, Fu_pl = plate['Fy'], plate['Fu']
    Fnv, Fexx = bolts['Fnv'], 480

    if is_lrfd:
        method_name, load_symbol = "LRFD", "V_u"
        phi_shear, phi_yield, phi_rupture, phi_weld = 0.75, 1.00, 0.75, 0.75
        def apply_f(Rn, phi): return phi * Rn, r"\phi R_n", f"{phi} \cdot {Rn:.2f}"
    else:
        method_name, load_symbol = "ASD", "V_a"
        om_shear, om_yield, om_rupture, om_weld = 2.00, 1.50, 2.00, 2.00
        def apply_f(Rn, omega): return Rn / omega, r"\frac{R_n}{\Omega}", f"\\frac{{{Rn:.2f}}}{{{omega}}}"

    # Calculations
    Ab = (math.pi * d**2) / 4
    Rn_bs = (Fnv * Ab * n_total) / 1000
    cap_bs, f_bs, c_bs = apply_f(Rn_bs, phi_shear if is_lrfd else om_shear)

    Rn_br = (2.4 * d * t_pl * Fu_pl * n_total) / 1000
    cap_br, f_br, c_br = apply_f(Rn_br, phi_shear if is_lrfd else om_shear)

    Rn_y = 0.60 * Fy_pl * (h_pl * t_pl) / 1000
    cap_y, f_y, c_y = apply_f(Rn_y, phi_yield if is_lrfd else om_yield)

    Rn_r = 0.60 * Fu_pl * ((h_pl - (n_rows * h_hole)) * t_pl) / 1000
    cap_r, f_r, c_r = apply_f(Rn_r, phi_rupture if is_lrfd else om_rupture)

    # Summary logic
    caps = {"Bolt Shear": cap_bs, "Bolt Bearing": cap_br, "Plate Yielding": cap_y, "Plate Rupture": cap_r}
    min_cap = min(caps.values())
    ratio = V_load / min_cap if min_cap > 0 else 999
    status_color = "green" if ratio <= 1.0 else "red"

    return f"""
<div style="border:1px solid #e5e7eb; padding:20px; border-radius:10px; background-color: #ffffff;">
<h3>📝 AISC Connection Report ({method_name})</h3>
<b>Design Shear ({load_symbol}): {V_load:.2f} kN</b><br>
<b>Status: <span style="color:{status_color}">{"✅ PASS" if ratio <= 1.0 else "❌ FAIL"}</span></b> (Ratio: {ratio:.2f})
<hr>
<b>1. Bolt Capacity:</b> {cap_bs:.2f} kN ({f_bs})<br>
<b>2. Plate Yielding:</b> {cap_y:.2f} kN ({f_y})<br>
<b>3. Plate Rupture:</b> {cap_r:.2f} kN ({f_r})
</div>
"""
