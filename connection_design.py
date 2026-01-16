# connection_design.py (V13 - Full Clean Version)
import math
import streamlit as st
try:
    import drawing_utils as drw
except ImportError:
    st.warning("Warning: drawing_utils.py not found. Drawings will not be displayed.")

def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade):
    """
    ฟังก์ชันสำหรับแสดงผลหน้า Tab Connection ใน Streamlit
    และคำนวณจำนวนโบลท์เบื้องต้นเพื่อส่งค่ากลับไปยัง App หลัก
    """
    st.subheader(f"🔩 Connection Design: {conn_type}")
    
    # ดึงค่าขนาดโบลท์ (เช่น "M20" -> 20)
    d = int(bolt_size.replace("M", ""))
    
    # ส่วนรับ Input เพิ่มเติมสำหรับแผ่นเหล็ก
    col1, col2 = st.columns(2)
    with col1:
        t_plate = st.number_input("Plate Thickness (mm)", min_value=1, value=9)
        h_plate = st.number_input("Plate Height (mm)", min_value=50, value=200)
        weld_size = st.number_input("Weld Size (mm)", min_value=3, value=6)
    
    with col2:
        bolt_rows = st.number_input("Number of Rows", min_value=1, value=3)
        bolt_cols = st.number_input("Number of Columns", min_value=1, value=1)
        s_v = st.number_input("Vertical Spacing (mm)", min_value=1, value=75)
        l_side = st.number_input("Edge Distance (mm)", min_value=1, value=40)

    # กำหนดค่า Material Properties เบื้องต้น
    Fy_pl = 250  # MPa (A36/SS400)
    Fu_pl = 400  # MPa
    
    # กำหนด Fnv ตามเกรดโบลท์ (MPa)
    bolt_props = {
        "A325 (High Strength)": 372,
        "Grade 8.8 (Standard)": 320,
        "A490 (Premium)": 496
    }
    fnv = bolt_props.get(bolt_grade, 372)

    # เตรียม Dictionary ข้อมูลสำหรับคำนวณ
    plate = {
        't': t_plate, 'h': h_plate, 'w': section_data['b'],
        'lv': 40, 'l_side': l_side, 'weld_size': weld_size,
        'Fy': Fy_pl, 'Fu': Fu_pl
    }
    
    bolts = {
        'd': d, 'rows': bolt_rows, 'cols': bolt_cols,
        's_v': s_v, 'Fnv': fnv, 's_h': 60 # ระยะห่างแนวนอนสมมติเพื่อวาดรูป
    }

    # แปลง V_design จาก kg เป็น kN
    V_load_kn = V_design / 100

    # แสดงผล Drawing (เพิ่มส่วนนี้เพื่อให้รูปปรากฏใน Tab 2)
    if 'drw' in globals():
        st.divider()
        st.subheader("🎨 Engineering Drawing (3 Views)")
        
        # จัดเตรียมข้อมูลสำหรับโมดูลวาดภาพ
        beam_draw_data = {
            'h': section_data['h'], 
            'b': section_data['b'], 
            'tf': section_data['tf'], 
            'tw': section_data['tw']
        }
        
        # แสดงผลรูปภาพ 3 มุม
        col_draw_a, col_draw_b = st.columns(2)
        with col_draw_a:
            fig_plan = drw.create_plan_view(beam_draw_data, plate, bolts)
            st.plotly_chart(fig_plan, use_container_width=True)
            
            fig_side = drw.create_side_view(beam_draw_data, plate, bolts)
            st.plotly_chart(fig_side, use_container_width=True)

        with col_draw_b:
            fig_front = drw.create_front_view(beam_draw_data, plate, bolts)
            st.plotly_chart(fig_front, use_container_width=True)

    # เรียกใช้ฟังก์ชันคำนวณเพื่อสร้าง Report
    report_md = generate_report(V_load_kn, section_data, plate, bolts, is_lrfd)
    
    st.markdown(report_md, unsafe_allow_html=True)
    
    # ส่งค่ากลับไปยัง app.py (จำนวนโบลท์ทั้งหมด และแรงที่ออกแบบ)
    return (bolt_rows * bolt_cols), V_load_kn

def generate_report(V_load, beam, plate, bolts, is_lrfd=True):
    # --- 1. Setup Parameters ---
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
    
    Fy_pl = plate['Fy'] 
    Fu_pl = plate['Fu'] 
    Fnv = bolts['Fnv']   
    Fexx = 480  # E70xx

    # --- 2. Setup Factors (ASD vs LRFD) ---
    if is_lrfd:
        method_name = "LRFD"
        load_symbol = "V_u"
        phi_shear = 0.75
        phi_yield = 1.00
        phi_rupture = 0.75
        phi_weld = 0.75
        
        def apply_factor(Rn, phi):
            return phi * Rn, r"\phi R_n", f"{phi} \cdot {Rn:.2f}"
            
    else: # ASD
        method_name = "ASD"
        load_symbol = "V_a"
        om_shear = 2.00
        om_yield = 1.50
        om_rupture = 2.00
        om_weld = 2.00
        
        def apply_factor(Rn, omega):
            return Rn / omega, r"\frac{R_n}{\Omega}", f"\\frac{{{Rn:.2f}}}{{{omega}}}"

    # --- 3. CALCULATIONS ---
    # 3.1 Bolt Shear
    Ab = (math.pi * d**2) / 4
    Rn_shear_total = (Fnv * Ab * n_total) / 1000
    cap_bolt_shear, str_f_bs, str_c_bs = apply_factor(Rn_shear_total, phi_shear if is_lrfd else om_shear)

    # 3.2 Bolt Bearing
    Rn_bearing_total = (2.4 * d * t_pl * Fu_pl * n_total) / 1000
    cap_bearing, str_f_br, str_c_br = apply_factor(Rn_bearing_total, phi_shear if is_lrfd else om_shear)

    # 3.3 Plate Shear Yielding
    Ag_shear = h_pl * t_pl
    Rn_y = 0.60 * Fy_pl * Ag_shear / 1000
    cap_yield, str_f_y, str_c_y = apply_factor(Rn_y, phi_yield if is_lrfd else om_yield)

    # 3.4 Plate Shear Rupture
    An_shear = (h_pl - (n_rows * h_hole)) * t_pl
    Rn_r = 0.60 * Fu_pl * An_shear / 1000
    cap_rupture, str_f_r, str_c_r = apply_factor(Rn_r, phi_rupture if is_lrfd else om_rupture)

    # 3.5 Block Shear Rupture
    L_gv = (n_rows - 1) * bolts['s_v'] + lv 
    Agv = L_gv * t_pl
    Anv = (L_gv - (n_rows - 0.5) * h_hole) * t_pl
    Ant = (l_side - 0.5 * h_hole) * t_pl
    Ubs = 1.0 
    
    term1 = 0.6 * Fu_pl * Anv + Ubs * Fu_pl * Ant
    term2 = 0.6 * Fy_pl * Agv + Ubs * Fu_pl * Ant
    Rn_block = min(term1, term2) / 1000
    cap_block, str_f_bl, str_c_bl = apply_factor(Rn_block, phi_rupture if is_lrfd else om_rupture)

    # 3.6 Weld Strength
    L_weld = h_pl * 2 
    Rn_weld = (0.6 * Fexx * 0.707 * weld_size * L_weld) / 1000
    cap_weld, str_f_wd, str_c_wd = apply_factor(Rn_weld, phi_weld if is_lrfd else om_weld)

    # --- 4. SUMMARY ---
    capacities = {
        "Bolt Shear": cap_bolt_shear,
        "Bolt Bearing": cap_bearing,
        "Plate Yielding": cap_yield,
        "Plate Rupture": cap_rupture,
        "Block Shear": cap_block,
        "Weld Strength": cap_weld
    }
    
    min_cap_val = min(capacities.values())
    governing_mode = min(capacities, key=capacities.get)
    ratio = V_load / min_cap_val if min_cap_val > 0 else 999
    
    status = "✅ PASS" if ratio <= 1.0 else "❌ FAIL"
    color = "green" if ratio <= 1.0 else "red"

    # --- 5. REPORT ---
    report = f"""
<div style="border:1px solid #e5e7eb; padding:20px; border-radius:10px; background-color: #ffffff;">

### 📝 AISC Connection Report ({method_name})

**Parameters:**
- Design Shear (${load_symbol}$): **{V_load:.2f} kN**
- Plate: {h_pl:.0f}x{t_pl:.0f} mm
- Bolts: {n_total} x M{d}

---

#### 1. Bolt Capacity
**1.1 Bolt Shear ({str_f_bs})**
$$ {str_f_bs} = {str_c_bs} = \\mathbf{{{cap_bolt_shear:.2f} \\text{{ kN}}}} $$

**1.2 Bolt Bearing ({str_f_br})**
$$ {str_f_br} = {str_c_br} = \\mathbf{{{cap_bearing:.2f} \\text{{ kN}}}} $$

---

#### 2. Plate Capacity
**2.1 Shear Yielding ({str_f_y})**
$$ {str_f_y} = {str_c_y} = \\mathbf{{{cap_yield:.2f} \\text{{ kN}}}} $$

**2.2 Shear Rupture ({str_f_r})**
$$ {str_f_r} = {str_c_r} = \\mathbf{{{cap_rupture:.2f} \\text{{ kN}}}} $$

**2.3 Block Shear ({str_f_bl})**
$$ {str_f_bl} = {str_c_bl} = \\mathbf{{{cap_block:.2f} \\text{{ kN}}}} $$

---

#### 3. Weld Capacity
**3.1 Fillet Weld ({str_f_wd})**
$$ {str_f_wd} = {str_c_wd} = \\mathbf{{{cap_weld:.2f} \\text{{ kN}}}} $$

---

#### 🏁 Summary
**Status: <span style='color:{color}'>{status}</span>**
- Utilization Ratio: **{ratio:.2f}**
- Governing Mode: **{governing_mode}**

</div>
    """
    return report
