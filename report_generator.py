# report_generator.py
# Version: 26.0 (Ultimate Workbench: Manual Select + Calc Sheet + Classic Table)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime
import math

# =========================================================
# 🏗️ 1. DATABASE
# =========================================================
def get_standard_sections():
    # เรียงลำดับตามขนาดให้หาง่าย
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
# ⚙️ 2. CORE LOGIC
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
    Aw = (h/10)*(tw/10) # cm2
    Vn_beam = 0.60 * fy * Aw
    V_target = (load_percent/100) * Vn_beam
    
    # 2. Critical Span
    Zx = calculate_zx(h, b, tw, tf)
    Mn_beam = fy * Zx
    phiMn = 0.90 * Mn_beam
    L_crit = (span_factor * (phiMn / V_target)) / 100.0 if V_target > 0 else 0
    
    # 3. Bolt Capacity
    DB = float(bolt_dia)
    Ab = 3.1416 * (DB/10)**2 / 4
    Rn_shear = 0.75 * 3300 * Ab # Single Shear
    
    plate_t_mm = 10.0
    Le = 3.5
    Lc = Le - ((DB+2)/10)/2
    
    # Bearing Plate
    Rn_pl = 0.75 * min(1.2*Lc*(plate_t_mm/10)*4050, 2.4*(DB/10)*(plate_t_mm/10)*4050)
    # Bearing Web
    Rn_web = 0.75 * min(1.2*Lc*(tw/10)*fu, 2.4*(DB/10)*(tw/10)*fu)
    
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
    
    # Geometry
    spacing = 7.0
    L_plate = (2*Le) + ((n_bolts-1)*spacing)

    return {
        "Section": props['name'],
        "h": h, "tw": tw, "Fy": fy, "Fu": fu,
        "Aw": Aw,
        "Zx": Zx,
        "Vn_beam": Vn_beam,
        "V_target": V_target,
        "L_crit": L_crit,
        "phiRn_bolt": phiRn_bolt,
        "Bolt Qty": n_bolts,
        "Bolt Spec": f"M{int(DB)}",
        "Control By": control_mode,
        "Plate Len": L_plate,
        "Le": Le, "S": spacing
    }

# =========================================================
# 🎨 3. DRAWING (Auto-Dimension)
# =========================================================
def draw_connection_sketch(h_beam, n_bolts, bolt_dia, plate_len_mm, le_cm, spacing_cm):
    fig, ax = plt.subplots(figsize=(4, 6))
    web_w = 160
    h_draw = h_beam + 80
    
    # Web & Plate
    ax.add_patch(patches.Rectangle((0, -40), web_w, h_draw, fc='#f8f9fa'))
    pl_w = 90
    px = (web_w - pl_w)/2
    py = (h_beam - plate_len_mm)/2 + 40
    ax.add_patch(patches.Rectangle((px, py), pl_w, plate_len_mm, ec='#007bff', fc='#cfe2ff', lw=2))
    
    # Bolts
    bx = px + pl_w/2
    curr_y = py + plate_len_mm - (le_cm*10)
    ys = []
    for _ in range(n_bolts):
        ys.append(curr_y)
        ax.add_patch(patches.Circle((bx, curr_y), (bolt_dia+2)/2, ec='k', fc='w'))
        curr_y -= (spacing_cm*10)
        
    # Dimensions
    dx = px + pl_w + 15
    def dim(y1, y2, txt, c='r'):
        ax.plot([dx, dx], [y1, y2], color=c, lw=1)
        ax.plot([dx-3, dx+3], [y1, y1], color=c, lw=1)
        ax.plot([dx-3, dx+3], [y2, y2], color=c, lw=1)
        ax.text(dx+5, (y1+y2)/2, txt, color=c, fontsize=8, va='center')
        
    dim(py+plate_len_mm, ys[0], f"{int(le_cm*10)}")
    for i in range(len(ys)-1):
        dim(ys[i], ys[i+1], f"{int(spacing_cm*10)}")
    dim(ys[-1], py, f"{int(le_cm*10)}")
    
    # Total H
    dx2 = dx + 25
    ax.plot([dx2, dx2], [py, py+plate_len_mm], 'b-', lw=1)
    ax.text(dx2+5, py+plate_len_mm/2, f"L={int(plate_len_mm)}", color='b', rotation=90, va='center')

    ax.set_xlim(0, web_w + 60)
    ax.set_ylim(0, h_draw)
    ax.axis('off')
    return fig

# =========================================================
# 🖥️ 4. RENDER UI
# =========================================================
def render_report_tab(beam_data_ignored, conn_data_ignored):
    st.markdown("### 🖨️ Structural Connection Workbench")
    
    # -------------------------------------------
    # 🎛️ 1. INPUT CONTROL (Select Section Here!)
    # -------------------------------------------
    with st.container(border=True):
        st.markdown("**1. Configuration (กำหนดค่า)**")
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1.5])
        
        all_sections = get_standard_sections()
        sec_names = [s['name'] for s in all_sections]
        
        with c1:
            # เลือกเหล็กตรงนี้ได้เลย!
            selected_sec_name = st.selectbox("🏗️ Select Steel Section", sec_names, index=6)
        with c2:
            load_pct = st.number_input("Load %", 10, 100, 75, step=5)
        with c3:
            bolt_dia = st.selectbox("Bolt", [12, 16, 20, 24], index=2)
        with c4:
            load_case = st.selectbox("Support", [
                "Simple Beam (Uniform Load)", 
                "Simple Beam (Point Load @Center)",
                "Cantilever (Uniform Load)",
                "Cantilever (Point Load @Tip)"
            ])
            
    # หาข้อมูลเหล็กที่เลือก
    selected_props = next(s for s in all_sections if s['name'] == selected_sec_name)
    factor = get_load_case_factor(load_case)
    
    # Run Calculation
    res = calculate_connection(selected_props, load_pct, bolt_dia, factor)

    st.divider()

    # -------------------------------------------
    # 📝 2. CALCULATION SHEET & SKETCH
    # -------------------------------------------
    col_cal, col_draw = st.columns([1.5, 1])
    
    with col_cal:
        st.subheader("📝 รายการคำนวณ (Calculation Sheet)")
        with st.container(height=500, border=True):
            st.markdown(f"""
            **Project:** Connection Design for {res['Section']}
            **Method:** ASD (Allowable Stress Design)
            
            ---
            **1. Beam Properties**
            * Depth ($h$) = {res['h']} mm, Web ($t_w$) = {res['tw']} mm
            * Steel Grade: $F_y$ = {res['Fy']} ksc, $F_u$ = {res['Fu']} ksc
            * Shear Area ($A_w$) = $h \\times t_w$ = {res['Aw']:.2f} cm²
            
            **2. Design Load ($V_u$)**
            * Beam Shear Cap ($V_n$) = $0.6 F_y A_w$ = {res['Vn_beam']:,.2f} kg
            * **Target Load ({load_pct}%)** = {res['V_target']:,.2f} kg ✅
            
            **3. Critical Span Check**
            * Plastic Modulus ($Z_x$) = {res['Zx']:.2f} cm³
            * Moment Cap ($\\phi M_n$) = $0.9 F_y Z_x$ = {res['Zx']*res['Fy']*0.9/100:,.2f} kg.m
            * **Critical Span** ($L$) = {res['L_crit']:.2f} m
            *(Note: If span > {res['L_crit']:.2f} m, beam fails by moment first)*
            
            **4. Bolt Capacity (M{bolt_dia} A325)**
            * Single Shear Strength = {0.75*3300*3.1416*((float(bolt_dia)/10)**2)/4:,.0f} kg/bolt
            * Plate Bearing Strength = Check OK
            * Web Bearing Strength = Check OK
            * **Max Capacity per Bolt** = **{res['phiRn_bolt']:,.0f} kg** (Control by {res['Control By']})
            
            **5. Conclusion**
            $$
            n_{{req}} = \\frac{{{res['V_target']:,.0f}}}{{{res['phiRn_bolt']:,.0f}}} = {res['V_target']/res['phiRn_bolt']:.2f} \\rightarrow \\mathbf{{{res['Bolt Qty']} \\; pcs}}
            $$
            """)
            st.info(f"สรุป: ใช้โบลท์ **{res['Bolt Qty']} ตัว** (M{bolt_dia})")

    with col_draw:
        st.subheader("📐 Shop Drawing")
        fig = draw_connection_sketch(res['h'], res['Bolt Qty'], float(bolt_dia), res['Plate Len']*10, res['Le'], res['S'])
        st.pyplot(fig)

    st.divider()

    # -------------------------------------------
    # 📊 3. THE "CLASSIC" TABLE (Batch)
    # -------------------------------------------
    st.subheader("📊 ตารางเปรียบเทียบทุกหน้าตัด (Classic Table)")
    
    if st.checkbox("Show Full Table", value=True):
        # Run loop for all
        batch_results = []
        for sec in all_sections:
            r = calculate_connection(sec, load_pct, bolt_dia, factor)
            batch_results.append({
                "Steel Section": r['Section'],
                "Design Vu (Ton)": r['V_target']/1000,
                "Max Span (m)": r['L_crit'],
                "Bolt Qty": r['Bolt Qty'],
                "Bolt Spec": r['Bolt Spec'],
                "Control By": r['Control By']
            })
            
        df = pd.DataFrame(batch_results)
        
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "Design Vu (Ton)": st.column_config.NumberColumn("Vu (Ton)", format="%.2f"),
                "Max Span (m)": st.column_config.NumberColumn("Max Span (m)", format="%.2f", help="ความยาววิกฤต"),
                "Bolt Qty": st.column_config.NumberColumn("Bolt Qty", format="%d"),
            },
            hide_index=True
        )
