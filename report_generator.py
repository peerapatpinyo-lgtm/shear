# report_generator.py
# Version: 29.0 (Submission Grade Calculation - ละเอียดระดับส่งงาน)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime
import math

# =========================================================
# 🏗️ 1. FULL DATABASE (TIS Standard)
# =========================================================
def get_standard_sections():
    return [
        {"name": "H-100x50x5x7",    "h": 100, "b": 50,  "tw": 5,  "tf": 7,  "Fy": 2500, "Fu": 4100},
        {"name": "H-125x60x6x8",    "h": 125, "b": 60,  "tw": 6,  "tf": 8,  "Fy": 2500, "Fu": 4100},
        {"name": "H-150x75x5x7",    "h": 150, "b": 75,  "tw": 5,  "tf": 7,  "Fy": 2500, "Fu": 4100},
        {"name": "H-175x90x5x8",    "h": 175, "b": 90,  "tw": 5,  "tf": 8,  "Fy": 2500, "Fu": 4100},
        {"name": "H-200x100x5.5x8", "h": 200, "b": 100, "tw": 5.5,"tf": 8,  "Fy": 2500, "Fu": 4100},
        {"name": "H-250x125x6x9",    "h": 250, "b": 125, "tw": 6,  "tf": 9,  "Fy": 2500, "Fu": 4100},
        {"name": "H-300x150x6.5x9",  "h": 300, "b": 150, "tw": 6.5,"tf": 9,  "Fy": 2500, "Fu": 4100},
        {"name": "H-350x175x7x11",   "h": 350, "b": 175, "tw": 7,  "tf": 11, "Fy": 2500, "Fu": 4100},
        {"name": "H-400x200x8x13",   "h": 400, "b": 200, "tw": 8,  "tf": 13, "Fy": 2500, "Fu": 4100},
        {"name": "H-450x200x9x14",   "h": 450, "b": 200, "tw": 9,  "tf": 14, "Fy": 2500, "Fu": 4100},
        {"name": "H-500x200x10x16",  "h": 500, "b": 200, "tw": 10, "tf": 16, "Fy": 2500, "Fu": 4100},
        {"name": "H-600x200x11x17",  "h": 600, "b": 200, "tw": 11, "tf": 17, "Fy": 2500, "Fu": 4100},
        {"name": "H-700x300x13x24",  "h": 700, "b": 300, "tw": 13, "tf": 24, "Fy": 2500, "Fu": 4100},
        {"name": "H-800x300x14x26",  "h": 800, "b": 300, "tw": 14, "tf": 26, "Fy": 2500, "Fu": 4100},
        {"name": "H-900x300x16x28",  "h": 900, "b": 300, "tw": 16, "tf": 28, "Fy": 2500, "Fu": 4100},
    ]

# =========================================================
# ⚙️ 2. CORE LOGIC (Enhanced for Detail)
# =========================================================
def get_load_case_factor(case_name):
    cases = {
        "Simple Beam (Uniform Load)": 4.0,
        "Simple Beam (Point Load @Center)": 2.0,
        "Cantilever (Uniform Load)": 2.0,
        "Cantilever (Point Load @Tip)": 1.0
    }
    return cases.get(case_name, 4.0)

def calculate_zx(h, b, tw, tf):
    h, b, tw, tf = h/10, b/10, tw/10, tf/10 # to cm
    return (b*tf*(h-tf)) + (tw*(h-2*tf)**2/4)

def calculate_connection(props, load_percent, bolt_dia, span_factor):
    # Unpack
    h, tw, fy, fu = props['h'], props['tw'], props['Fy'], props['Fu']
    b, tf = props.get('b', h/2), props.get('tf', tw*1.5)
    
    # 1. Shear Capacity (Beam)
    Aw_cm2 = (h/10)*(tw/10) 
    Vn_beam = 0.60 * fy * Aw_cm2
    V_target = (load_percent/100) * Vn_beam
    
    # 2. Critical Span
    Zx = calculate_zx(h, b, tw, tf)
    Mn_beam = fy * Zx
    phiMn = 0.90 * Mn_beam
    L_crit = (span_factor * (phiMn / V_target)) / 100.0 if V_target > 0 else 0
    
    # 3. Bolt Capacity Details
    DB_mm = float(bolt_dia)
    Ab_cm2 = 3.1416 * (DB_mm/10)**2 / 4
    Fnv = 3300 # ksc (A325)
    Rn_shear = 0.75 * Fnv * Ab_cm2 
    
    # Bearing Details
    plate_t_mm = 10.0
    Le_cm = 3.5
    hole_dia_mm = DB_mm + 2
    Lc_cm = Le_cm - (hole_dia_mm/10)/2
    
    # Bearing Plate
    Rn_pl_formula1 = 1.2 * Lc_cm * (plate_t_mm/10) * 4050 # Fu Plate (Assume SS400)
    Rn_pl_formula2 = 2.4 * (DB_mm/10) * (plate_t_mm/10) * 4050
    Rn_pl = 0.75 * min(Rn_pl_formula1, Rn_pl_formula2)
    
    # Bearing Web
    Rn_web_formula1 = 1.2 * Lc_cm * (tw/10) * fu
    Rn_web_formula2 = 2.4 * (DB_mm/10) * (tw/10) * fu
    Rn_web = 0.75 * min(Rn_web_formula1, Rn_web_formula2)
    
    phiRn_bolt = min(Rn_shear, Rn_pl, Rn_web)
    
    # 4. Result
    if phiRn_bolt > 0:
        n_req = V_target / phiRn_bolt
        n_bolts = max(2, math.ceil(n_req))
    else:
        n_bolts = 99
        
    control_mode = "Shear"
    if Rn_pl < Rn_shear and Rn_pl < Rn_web: control_mode = "Plate Bear"
    if Rn_web < Rn_shear and Rn_web < Rn_pl: control_mode = "Web Bear"
    
    spacing = 7.0
    L_plate = (2*Le_cm) + ((n_bolts-1)*spacing)

    return {
        "Section": props['name'],
        "h": h, "tw": tw, "Fy": fy, "Fu": fu,
        "Aw": Aw_cm2, "Zx": Zx,
        "Vn_beam": Vn_beam, "V_target": V_target,
        "L_crit": L_crit, "Mn_beam": Mn_beam,
        # Bolt Details
        "DB": DB_mm, "Ab": Ab_cm2, "Fnv": Fnv, "Rn_shear": Rn_shear,
        "Lc": Lc_cm, "Rn_pl": Rn_pl, "Rn_web": Rn_web,
        "Rn_pl_1": Rn_pl_formula1, "Rn_pl_2": Rn_pl_formula2,
        "Rn_web_1": Rn_web_formula1, "Rn_web_2": Rn_web_formula2,
        "phiRn_bolt": phiRn_bolt,
        "Bolt Qty": n_bolts,
        "Control By": control_mode,
        "Plate Len": L_plate,
        "Le": Le_cm, "S": spacing
    }

# =========================================================
# 🎨 3. DRAWING
# =========================================================
def draw_connection_sketch(h_beam, n_bolts, bolt_dia, plate_len_mm, le_cm, spacing_cm):
    fig, ax = plt.subplots(figsize=(4, 6))
    web_w = 160
    h_draw = h_beam + 80
    
    ax.add_patch(patches.Rectangle((0, -40), web_w, h_draw, fc='#f8f9fa'))
    pl_w = 90
    px = (web_w - pl_w)/2
    py = (h_beam - plate_len_mm)/2 + 40
    ax.add_patch(patches.Rectangle((px, py), pl_w, plate_len_mm, ec='#007bff', fc='#cfe2ff', lw=2))
    
    bx = px + pl_w/2
    curr_y = py + plate_len_mm - (le_cm*10)
    ys = []
    for _ in range(n_bolts):
        ys.append(curr_y)
        ax.add_patch(patches.Circle((bx, curr_y), (bolt_dia+2)/2, ec='k', fc='w'))
        curr_y -= (spacing_cm*10)
        
    dx = px + pl_w + 15
    def dim(y1, y2, txt):
        ax.plot([dx, dx], [y1, y2], 'r-', lw=1)
        ax.plot([dx-3, dx+3], [y1, y1], 'r-', lw=1)
        ax.plot([dx-3, dx+3], [y2, y2], 'r-', lw=1)
        ax.text(dx+5, (y1+y2)/2, txt, color='r', fontsize=8, va='center')
        
    dim(py+plate_len_mm, ys[0], f"{int(le_cm*10)}")
    for i in range(len(ys)-1):
        dim(ys[i], ys[i+1], f"{int(spacing_cm*10)}")
    dim(ys[-1], py, f"{int(le_cm*10)}")
    
    dx2 = dx + 25
    ax.plot([dx2, dx2], [py, py+plate_len_mm], 'b-', lw=1)
    ax.text(dx2+5, py+plate_len_mm/2, f"L={int(plate_len_mm)}", color='b', rotation=90, va='center')

    ax.set_xlim(0, web_w + 60)
    ax.set_ylim(0, h_draw)
    ax.axis('off')
    return fig

# =========================================================
# 🖥️ 4. RENDER UI (DETAILED REPORT)
# =========================================================
def render_report_tab(beam_data_ignored, conn_data_ignored):
    st.markdown("### 🖨️ Structural Calculation Workbench")
    
    # 1. Controls
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1.5])
        all_sections = get_standard_sections()
        with c1:
            selected_sec_name = st.selectbox("Select Section", [s['name'] for s in all_sections], index=10)
        with c2:
            load_pct = st.number_input("Load %", 10, 100, 75, step=5)
        with c3:
            bolt_dia = st.selectbox("Bolt", [12, 16, 20, 24], index=2)
        with c4:
            load_case = st.selectbox("Support", ["Simple Beam (Uniform Load)", "Simple Beam (Point Load @Center)", "Cantilever (Uniform Load)", "Cantilever (Point Load @Tip)"])
            
    # Calculate
    selected_props = next(s for s in all_sections if s['name'] == selected_sec_name)
    factor = get_load_case_factor(load_case)
    res = calculate_connection(selected_props, load_pct, bolt_dia, factor)

    st.divider()

    # 2. Detailed Report Layout
    col_cal, col_draw = st.columns([1.6, 1])
    
    with col_cal:
        st.subheader("📝 รายการคำนวณ (Detailed Calculation)")
        
        # ใช้ container แบบ scroll ได้ เพื่อรองรับเนื้อหายาวๆ
        with st.container(height=650, border=True):
            st.markdown(f"""
            #### 1. Design Parameters (ข้อกำหนดการออกแบบ)
            * **Method:** Allowable Stress Design (ASD)
            * **Steel Section:** {res['Section']}
            * **Properties:** $h={res['h']}$ mm, $t_w={res['tw']}$ mm
            * **Material:** $F_y = {res['Fy']:,}$ ksc, $F_u = {res['Fu']:,}$ ksc
            * **Bolt:** M{int(res['DB'])} (A325), Hole $\\phi = {int(res['DB']+2)}$ mm
            
            ---
            #### 2. Load Calculation (แรงกระทำ)
            คำนวณกำลังรับแรงเฉือนของหน้าตัดคาน ($V_n$)
            $$
            A_w = h \\times t_w = {res['h']/10} \\times {res['tw']/10} = {res['Aw']:.2f} \\; cm^2
            $$
            $$
            V_n = 0.60 F_y A_w = 0.60 \\times {res['Fy']:,} \\times {res['Aw']:.2f} = {res['Vn_beam']:,.2f} \\; kg
            $$
            **Design Load ($V_u$) at {load_pct}% Capacity:**
            $$
            V_u = {load_pct/100:.2f} \\times {res['Vn_beam']:,.2f} = \\mathbf{{{res['V_target']:,.2f} \\; kg}}
            $$

            ---
            #### 3. Bolt Capacity Check (กำลังรับแรงของสลักเกลียว)
            **3.1 Shear Capacity ($R_v$)**
            $$
            A_b = \\frac{{\\pi d^2}}{{4}} = \\frac{{3.14 \\times {res['DB']/10}^2}}{{4}} = {res['Ab']:.2f} \\; cm^2
            $$
            $$
            \\phi R_n = 0.75 \\times F_{{nv}} A_b = 0.75 \\times 3300 \\times {res['Ab']:.2f} = \\mathbf{{{res['Rn_shear']:,.2f} \\; kg/bolt}}
            $$

            **3.2 Bearing Capacity ($R_b$)**
            Clear distance ($L_c$) = $L_e - d_h/2$ = ${res['Le']} - {(res['DB']+2)/20:.2f} = {res['Lc']:.2f}$ cm
            
            *Check Plate (t=10mm):*
            $$
            R_n = 1.2 L_c t F_u = 1.2({res['Lc']:.2f})(1.0)(4050) = {res['Rn_pl_1']:,.0f} \\; kg
            $$
            $$
            Max = 2.4 d t F_u = 2.4({res['DB']/10})(1.0)(4050) = {res['Rn_pl_2']:,.0f} \\; kg
            $$
            $$
            \\phi R_{{pl}} = 0.75 \\times \\min({res['Rn_pl_1']:,.0f}, {res['Rn_pl_2']:,.0f}) = {res['Rn_pl']:,.0f} \\; kg/bolt
            $$

            *Check Web (t={res['tw']}mm):*
            $$
            R_n = 1.2 L_c t_w F_u = 1.2({res['Lc']:.2f})({res['tw']/10})({res['Fu']}) = {res['Rn_web_1']:,.0f} \\; kg
            $$
            $$
            Max = 2.4 d t_w F_u = 2.4({res['DB']/10})({res['tw']/10})({res['Fu']}) = {res['Rn_web_2']:,.0f} \\; kg
            $$
            $$
            \\phi R_{{web}} = 0.75 \\times \\min({res['Rn_web_1']:,.0f}, {res['Rn_web_2']:,.0f}) = {res['Rn_web']:,.0f} \\; kg/bolt
            $$
            
            **Controlling Capacity:**
            $$
            \\phi R_{{bolt}} = \\min({res['Rn_shear']:,.0f}, {res['Rn_pl']:,.0f}, {res['Rn_web']:,.0f}) = \\mathbf{{{res['phiRn_bolt']:,.0f} \\; kg/bolt}}
            $$
            *(Control by: {res['Control By']})*

            ---
            #### 4. Design Summary (สรุปผลการออกแบบ)
            จำนวนโบลท์ที่ต้องการ ($n$):
            $$
            n = \\frac{{V_u}}{{\\phi R_{{bolt}}}} = \\frac{{{res['V_target']:,.0f}}}{{{res['phiRn_bolt']:,.0f}}} = {res['V_target']/res['phiRn_bolt']:.2f} \\rightarrow \\mathbf{{{res['Bolt Qty']} \\; pcs}}
            $$
            
            * **Plate Size:** $100 \\times {int(res['Plate Len']*10)} \\times 10$ mm
            * **Min. Spacing:** $2.66d = {2.66*res['DB']:.1f}$ mm $\\rightarrow$ Use 70 mm (OK)
            * **Edge Distance:** {int(res['Le']*10)} mm (OK)

            ---
            #### 5. Critical Span Limit (ตรวจสอบความยาวคาน)
            $$
            \\phi M_n = 0.9 F_y Z_x = 0.9 \\times {res['Fy']} \\times {res['Zx']:.2f} = {res['Mn_beam']*0.9/100:,.0f} \\; kg.m
            $$
            $$
            L_{{crit}} = \\text{{Factor}} \\times \\frac{{\\phi M_n}}{{V_u}} = {factor} \\times \\frac{{{res['Mn_beam']*0.9:,.0f}}}{{{res['V_target']:,.0f}}} = \\mathbf{{{res['L_crit']:.2f} \\; m}}
            $$
            """)

    with col_draw:
        st.subheader("📐 Drawing")
        fig = draw_connection_sketch(res['h'], res['Bolt Qty'], float(bolt_dia), res['Plate Len']*10, res['Le'], res['S'])
        st.pyplot(fig)

    st.divider()

    # 3. Full Table
    st.subheader("📊 ตารางเปรียบเทียบ (Full Comparison)")
    if st.checkbox("Show Table", value=True):
        batch_results = []
        for sec in all_sections:
            r = calculate_connection(sec, load_pct, bolt_dia, factor)
            actual_cap = r['Bolt Qty'] * r['phiRn_bolt']
            util = (r['V_target'] / actual_cap) * 100 if actual_cap > 0 else 0
            
            batch_results.append({
                "Steel Section": r['Section'],
                "Design Vu (Ton)": r['V_target']/1000,
                "Bolt Qty": r['Bolt Qty'],
                "Plate Size (mm)": f"100x{int(r['Plate Len']*10)}x10",
                "Utilization": util,
                "Control By": r['Control By']
            })
            
        df = pd.DataFrame(batch_results)
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "Design Vu (Ton)": st.column_config.NumberColumn("Vu (Ton)", format="%.2f"),
                "Bolt Qty": st.column_config.NumberColumn("Bolt Qty", format="%d"),
                "Utilization": st.column_config.ProgressColumn("Eff.", format="%.0f%%"),
            },
            hide_index=True, height=400
        )
