# report_generator.py
# Version: 33.0 (Uniform Formatting & Consistency)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime
import math

# =========================================================
# 🏗️ 1. FULL DATABASE (TIS Standard - ครบทุกตัว)
# =========================================================
def get_standard_sections():
    return [
        # Series 100
        {"name": "H-100x50x5x7",    "h": 100, "b": 50,  "tw": 5,  "tf": 7,  "Fy": 2500, "Fu": 4100},
        {"name": "H-100x100x6x8",   "h": 100, "b": 100, "tw": 6,  "tf": 8,  "Fy": 2500, "Fu": 4100},
        # Series 125
        {"name": "H-125x60x6x8",    "h": 125, "b": 60,  "tw": 6,  "tf": 8,  "Fy": 2500, "Fu": 4100},
        {"name": "H-125x125x6.5x9", "h": 125, "b": 125, "tw": 6.5,"tf": 9,  "Fy": 2500, "Fu": 4100},
        # Series 150
        {"name": "H-148x100x6x9",   "h": 148, "b": 100, "tw": 6,  "tf": 9,  "Fy": 2500, "Fu": 4100},
        {"name": "H-150x75x5x7",    "h": 150, "b": 75,  "tw": 5,  "tf": 7,  "Fy": 2500, "Fu": 4100},
        {"name": "H-150x150x7x10",  "h": 150, "b": 150, "tw": 7,  "tf": 10, "Fy": 2500, "Fu": 4100},
        # Series 175
        {"name": "H-175x90x5x8",    "h": 175, "b": 90,  "tw": 5,  "tf": 8,  "Fy": 2500, "Fu": 4100},
        {"name": "H-175x175x7.5x11","h": 175, "b": 175, "tw": 7.5,"tf": 11, "Fy": 2500, "Fu": 4100},
        # Series 200
        {"name": "H-194x150x6x9",   "h": 194, "b": 150, "tw": 6,  "tf": 9,  "Fy": 2500, "Fu": 4100},
        {"name": "H-200x100x5.5x8", "h": 200, "b": 100, "tw": 5.5,"tf": 8,  "Fy": 2500, "Fu": 4100},
        {"name": "H-200x200x8x12",  "h": 200, "b": 200, "tw": 8,  "tf": 12, "Fy": 2500, "Fu": 4100},
        # Series 250
        {"name": "H-244x175x7x11",  "h": 244, "b": 175, "tw": 7,  "tf": 11, "Fy": 2500, "Fu": 4100},
        {"name": "H-250x125x6x9",   "h": 250, "b": 125, "tw": 6,  "tf": 9,  "Fy": 2500, "Fu": 4100},
        {"name": "H-250x250x9x14",  "h": 250, "b": 250, "tw": 9,  "tf": 14, "Fy": 2500, "Fu": 4100},
        # Series 300
        {"name": "H-294x200x8x12",  "h": 294, "b": 200, "tw": 8,  "tf": 12, "Fy": 2500, "Fu": 4100},
        {"name": "H-300x150x6.5x9", "h": 300, "b": 150, "tw": 6.5,"tf": 9,  "Fy": 2500, "Fu": 4100},
        {"name": "H-300x300x10x15", "h": 300, "b": 300, "tw": 10, "tf": 15, "Fy": 2500, "Fu": 4100},
        # Series 350
        {"name": "H-340x250x9x14",  "h": 340, "b": 250, "tw": 9,  "tf": 14, "Fy": 2500, "Fu": 4100},
        {"name": "H-350x175x7x11",  "h": 350, "b": 175, "tw": 7,  "tf": 11, "Fy": 2500, "Fu": 4100},
        {"name": "H-350x350x12x19", "h": 350, "b": 350, "tw": 12, "tf": 19, "Fy": 2500, "Fu": 4100},
        # Series 400
        {"name": "H-390x300x10x16", "h": 390, "b": 300, "tw": 10, "tf": 16, "Fy": 2500, "Fu": 4100},
        {"name": "H-400x200x8x13",  "h": 400, "b": 200, "tw": 8,  "tf": 13, "Fy": 2500, "Fu": 4100},
        {"name": "H-400x400x13x21", "h": 400, "b": 400, "tw": 13, "tf": 21, "Fy": 2500, "Fu": 4100},
        # Series 450
        {"name": "H-440x300x11x18", "h": 440, "b": 300, "tw": 11, "tf": 18, "Fy": 2500, "Fu": 4100},
        {"name": "H-450x200x9x14",  "h": 450, "b": 200, "tw": 9,  "tf": 14, "Fy": 2500, "Fu": 4100},
        # Series 500
        {"name": "H-482x300x11x15", "h": 482, "b": 300, "tw": 11, "tf": 15, "Fy": 2500, "Fu": 4100},
        {"name": "H-488x300x11x18", "h": 488, "b": 300, "tw": 11, "tf": 18, "Fy": 2500, "Fu": 4100},
        {"name": "H-500x200x10x16", "h": 500, "b": 200, "tw": 10, "tf": 16, "Fy": 2500, "Fu": 4100},
        # Series 600
        {"name": "H-582x300x12x17", "h": 582, "b": 300, "tw": 12, "tf": 17, "Fy": 2500, "Fu": 4100},
        {"name": "H-588x300x12x20", "h": 588, "b": 300, "tw": 12, "tf": 20, "Fy": 2500, "Fu": 4100},
        {"name": "H-600x200x11x17", "h": 600, "b": 200, "tw": 11, "tf": 17, "Fy": 2500, "Fu": 4100},
        # Series 700-900 (Large)
        {"name": "H-700x300x13x24", "h": 700, "b": 300, "tw": 13, "tf": 24, "Fy": 2500, "Fu": 4100},
        {"name": "H-800x300x14x26", "h": 800, "b": 300, "tw": 14, "tf": 26, "Fy": 2500, "Fu": 4100},
        {"name": "H-900x300x16x28", "h": 900, "b": 300, "tw": 16, "tf": 28, "Fy": 2500, "Fu": 4100},
    ]

# =========================================================
# ⚙️ 2. CORE LOGIC (Detailed Calc)
# =========================================================
def get_load_case_factor(case_name):
    cases = {
        "Simple Beam (Uniform Load)": 4.0,
        "Simple Beam (Point Load @Center)": 2.0,
        "Cantilever (Uniform Load)": 2.0,
        "Cantilever (Point Load @Tip)": 1.0
    }
    return cases.get(case_name, 4.0)

# 🆕 Proof Text Generator (Formatted for consistency)
def get_derivation_text(case_name):
    if case_name == "Simple Beam (Uniform Load)":
        return r"""
        * **Support:** Simple Support
        * **Load:** Uniform Distributed Load
        * **Proof:** $V = wL/2 \rightarrow M = wL^2/8 \rightarrow \mathbf{M = VL/4}$
        * **Factor:** $\mathbf{4.0}$
        """
    elif case_name == "Simple Beam (Point Load @Center)":
        return r"""
        * **Support:** Simple Support
        * **Load:** Point Load at Center
        * **Proof:** $V = P/2 \rightarrow M = PL/4 \rightarrow \mathbf{M = VL/2}$
        * **Factor:** $\mathbf{2.0}$
        """
    elif case_name == "Cantilever (Uniform Load)":
        return r"""
        * **Support:** Cantilever (Fixed)
        * **Load:** Uniform Distributed Load
        * **Proof:** $V = wL \rightarrow M = wL^2/2 \rightarrow \mathbf{M = VL/2}$
        * **Factor:** $\mathbf{2.0}$
        """
    elif case_name == "Cantilever (Point Load @Tip)":
        return r"""
        * **Support:** Cantilever (Fixed)
        * **Load:** Point Load at Tip
        * **Proof:** $V = P \rightarrow M = PL \rightarrow \mathbf{M = VL}$
        * **Factor:** $\mathbf{1.0}$
        """
    return ""

def calculate_zx(h, b, tw, tf):
    h, b, tw, tf = h/10, b/10, tw/10, tf/10 
    return (b*tf*(h-tf)) + (tw*(h-2*tf)**2/4)

def calculate_connection(props, load_percent, bolt_dia, span_factor):
    # Unpack
    h, tw, fy, fu = props['h'], props['tw'], props['Fy'], props['Fu']
    b, tf = props.get('b', h/2), props.get('tf', tw*1.5)
    
    # 1. Shear Capacity
    Aw_cm2 = (h/10)*(tw/10) 
    Vn_beam = 0.60 * fy * Aw_cm2
    V_target = (load_percent/100) * Vn_beam
    
    # 2. Critical Span
    Zx = calculate_zx(h, b, tw, tf)
    Mn_beam = fy * Zx
    phiMn = 0.90 * Mn_beam
    L_crit = (span_factor * (phiMn / V_target)) / 100.0 if V_target > 0 else 0
    
    # 3. Bolt Capacity
    DB_mm = float(bolt_dia)
    Ab_cm2 = 3.1416 * (DB_mm/10)**2 / 4
    Fnv = 3300
    Rn_shear = 0.75 * Fnv * Ab_cm2 
    
    # Bearing
    plate_t_mm = 10.0
    Le_cm = 3.5
    hole_dia_mm = DB_mm + 2
    Lc_cm = Le_cm - (hole_dia_mm/10)/2
    
    Rn_pl_1 = 1.2 * Lc_cm * (plate_t_mm/10) * 4050
    Rn_pl_2 = 2.4 * (DB_mm/10) * (plate_t_mm/10) * 4050
    Rn_pl = 0.75 * min(Rn_pl_1, Rn_pl_2)
    
    Rn_web_1 = 1.2 * Lc_cm * (tw/10) * fu
    Rn_web_2 = 2.4 * (DB_mm/10) * (tw/10) * fu
    Rn_web = 0.75 * min(Rn_web_1, Rn_web_2)
    
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
        "DB": DB_mm, "Ab": Ab_cm2, "Rn_shear": Rn_shear,
        "Lc": Lc_cm, "Rn_pl": Rn_pl, "Rn_web": Rn_web,
        "Rn_pl_1": Rn_pl_1, "Rn_pl_2": Rn_pl_2,
        "Rn_web_1": Rn_web_1, "Rn_web_2": Rn_web_2,
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
# 🖥️ 4. RENDER UI
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
    proof_text = get_derivation_text(load_case)

    st.divider()

    # 2. Detailed Report Layout
    col_cal, col_draw = st.columns([1.6, 1])
    
    with col_cal:
        st.subheader("📝 รายการคำนวณ (Detailed Calculation)")
        with st.container(height=650, border=True):
            st.markdown(f"""
            #### 1. Design Parameters
            * **Section:** {res['Section']}
            * **Method:** ASD (Allowable Stress Design)
            * **Bolt:** M{int(res['DB'])} (A325), Hole $\\phi = {int(res['DB']+2)}$ mm
            
            ---
            #### 2. Load Calculation
            $$ V_n = 0.60 F_y A_w = 0.60({res['Fy']:,})({res['Aw']:.2f}) = {res['Vn_beam']:,.2f} \\; kg $$
            $$ V_u = {load_pct/100:.2f} \\times V_n = \\mathbf{{{res['V_target']:,.2f} \\; kg}} $$

            ---
            #### 3. Bolt Capacity Check
            **3.1 Shear Capacity:**
            $$ \\phi R_n = 0.75(3300)({res['Ab']:.2f}) = \\mathbf{{{res['Rn_shear']:,.0f} \\; kg/bolt}} $$

            **3.2 Bearing (Plate t=10mm):**
            $$ R_{{pl}} = 0.75 \\times \\min({res['Rn_pl_1']:,.0f}, {res['Rn_pl_2']:,.0f}) = {res['Rn_pl']:,.0f} \\; kg $$

            **3.3 Bearing (Web t={res['tw']}mm):**
            $$ R_{{web}} = 0.75 \\times \\min({res['Rn_web_1']:,.0f}, {res['Rn_web_2']:,.0f}) = {res['Rn_web']:,.0f} \\; kg $$
            
            **Controlling Capacity:**
            $$ \\phi R_{{bolt}} = \\min({res['Rn_shear']:,.0f}, {res['Rn_pl']:,.0f}, {res['Rn_web']:,.0f}) = \\mathbf{{{res['phiRn_bolt']:,.0f} \\; kg}} $$
            *(Control by: {res['Control By']})*
            
            $$ n = {res['V_target']:,.0f} / {res['phiRn_bolt']:,.0f} = {res['V_target']/res['phiRn_bolt']:.2f} \\rightarrow \\mathbf{{{res['Bolt Qty']} \\; pcs}} $$

            ---
            #### 4. Critical Span Check ($L_{{crit}}$)
            **4.1 Theory & Factor:**
            {proof_text}
            
            **4.2 Section Properties:**
            $$ Z_x = {res['Zx']:.2f} \\; cm^3 $$
            $$ \\phi M_n = 0.90 F_y Z_x = 0.90({res['Fy']})({res['Zx']:.2f}) = {res['Mn_beam']*0.9/100:,.0f} \\; kg.m $$
            
            **4.3 Limit Calculation:**
            $$ L_{{crit}} = {factor} \\times \\frac{{\\phi M_n}}{{V_u}} = {factor} \\times \\frac{{{res['Mn_beam']*0.9:,.0f}}}{{{res['V_target']:,.0f}}} = \\mathbf{{{res['L_crit']:.2f} \\; m}} $$
            
            *(Note: If span > {res['L_crit']:.2f} m, beam fails by moment before shear)*
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
                "L_crit (m)": r['L_crit'],
                "Bolt Qty": r['Bolt Qty'],
                "Plate Size": f"100x{int(r['Plate Len']*10)}x10",
                "Utilization": util,
                "Control By": r['Control By']
            })
            
        df = pd.DataFrame(batch_results)
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "Design Vu (Ton)": st.column_config.NumberColumn("Vu (Ton)", format="%.2f"),
                "L_crit (m)": st.column_config.NumberColumn("Max Span (m)", format="%.2f"),
                "Bolt Qty": st.column_config.NumberColumn("Bolt Qty", format="%d"),
                "Utilization": st.column_config.ProgressColumn("Eff.", format="%.0f%%", min_value=0, max_value=100),
                "Plate Size": st.column_config.TextColumn("Plate Size (mm)"),
            },
            hide_index=True, height=500
        )
