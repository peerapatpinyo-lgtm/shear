# report_generator.py
# Version: 42.0 (Added 75% Shear Line)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np 
import math

# =========================================================
# 🏗️ 1. DATABASE
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
    h, b, tw, tf = h/10, b/10, tw/10, tf/10 
    return (b*tf*(h-tf)) + (tw*(h-2*tf)**2/4)

def calculate_ix(h, b, tw, tf):
    h, b, tw, tf = h/10, b/10, tw/10, tf/10
    outer_I = (b * h**3) / 12
    inner_w = b - tw
    inner_h = h - (2*tf)
    inner_I = (inner_w * inner_h**3) / 12
    return outer_I - inner_I

def calculate_deflection_limit(Ix, V_target, case_name):
    E = 2040000 
    Reaction = V_target # kg
    Limit_Factor = 360 # L/360
    
    coeff = 0
    if case_name == "Simple Beam (Uniform Load)":
        coeff = 192 / (5 * Limit_Factor)
    elif case_name == "Simple Beam (Point Load @Center)":
        coeff = 24 / Limit_Factor
    elif case_name == "Cantilever (Uniform Load)":
        coeff = 8 / Limit_Factor
    elif case_name == "Cantilever (Point Load @Tip)":
        coeff = 3 / Limit_Factor
        
    if Reaction > 0 and coeff > 0:
        L_sq = (coeff * E * Ix) / Reaction
        return math.sqrt(L_sq) / 100.0 
    return 0

def calculate_connection(props, load_percent, bolt_dia, span_factor, case_name):
    h, tw, fy, fu = props['h'], props['tw'], props['Fy'], props['Fu']
    b, tf = props.get('b', h/2), props.get('tf', tw*1.5)
    
    Aw_cm2 = (h/10)*(tw/10) 
    Vn_beam = 0.60 * fy * Aw_cm2
    V_target = (load_percent/100) * Vn_beam
    
    # Moment
    Zx = calculate_zx(h, b, tw, tf)
    Mn_beam = fy * Zx
    phiMn = 0.90 * Mn_beam
    L_crit_moment = (span_factor * (phiMn / V_target)) / 100.0 if V_target > 0 else 0
    
    # Deflection
    Ix = calculate_ix(h, b, tw, tf)
    L_crit_defl = calculate_deflection_limit(Ix, V_target, case_name)
    
    # Safe Span
    L_safe = min(L_crit_moment, L_crit_defl) if L_crit_defl > 0 else L_crit_moment
    
    # Bolt
    DB_mm = float(bolt_dia)
    Ab_cm2 = 3.1416 * (DB_mm/10)**2 / 4
    Fnv = 3300
    Rn_shear = 0.75 * Fnv * Ab_cm2 
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
        "Section": props['name'], "h": h, "tw": tw, "Fy": fy, "Fu": fu, "Aw": Aw_cm2, 
        "Zx": Zx, "Ix": Ix,
        "Vn_beam": Vn_beam, "V_target": V_target, 
        "L_crit_moment": L_crit_moment, "L_crit_defl": L_crit_defl, "L_safe": L_safe,
        "Mn_beam": Mn_beam,
        "DB": DB_mm, "Ab": Ab_cm2, "Rn_shear": Rn_shear, "Lc": Lc_cm, "Rn_pl": Rn_pl, "Rn_web": Rn_web,
        "phiRn_bolt": phiRn_bolt, "Bolt Qty": n_bolts, "Control By": control_mode,
        "Plate Len": L_plate, "Le": Le_cm, "S": spacing
    }

# =========================================================
# 🎨 3. DRAWING LOGIC (Matplotlib)
# =========================================================
def draw_connection_sketch(h_beam, n_bolts, bolt_dia, plate_len_mm, le_cm, spacing_cm):
    fig, ax = plt.subplots(figsize=(5, 7.5))
    COLOR_OBJ = '#2C3E50' 
    COLOR_DIM = '#E74C3C' 
    COLOR_CENTER = '#95A5A6'
    LW_OBJ = 2.0
    LW_DIM = 1.0
    
    web_w_draw = 200 
    h_draw_area = h_beam + 120
    plate_w = 100
    plate_x = (web_w_draw - plate_w) / 2
    plate_y_start = (h_beam - plate_len_mm) / 2 + 60
    
    web_rect = patches.Rectangle((0, 0), web_w_draw, h_draw_area, linewidth=0, facecolor='#ECF0F1', zorder=1)
    ax.add_patch(web_rect)
    ax.text(10, h_draw_area - 20, "BEAM WEB (ELEVATION)", fontsize=9, color=COLOR_OBJ, fontweight='bold')
    
    plate_rect = patches.Rectangle((plate_x, plate_y_start), plate_w, plate_len_mm, linewidth=LW_OBJ, edgecolor=COLOR_OBJ, facecolor='#D6EAF8', zorder=2)
    ax.add_patch(plate_rect)
    
    bolt_x_center = plate_x + (plate_w / 2)
    bolt_y_top = plate_y_start + plate_len_mm - (le_cm*10)
    
    ax.vlines(web_w_draw/2, 0, h_draw_area, colors=COLOR_CENTER, linestyles='-.', linewidth=0.8, zorder=1.5) 
    ax.vlines(bolt_x_center, plate_y_start-30, plate_y_start+plate_len_mm+10, colors=COLOR_CENTER, linestyles='-.', linewidth=0.8, zorder=1.5) 

    bolt_ys = []
    curr_y = bolt_y_top
    for i in range(n_bolts):
        bolt_ys.append(curr_y)
        circle = patches.Circle((bolt_x_center, curr_y), radius=(bolt_dia+2)/2, edgecolor=COLOR_OBJ, facecolor='white', linewidth=1.5, zorder=3)
        ax.add_patch(circle)
        ax.hlines(curr_y, bolt_x_center-15, bolt_x_center+15, colors=COLOR_CENTER, linestyles='-.', linewidth=0.5, zorder=3)
        curr_y -= (spacing_cm*10)

    def draw_dim_arrow(y_start, y_end, x_pos, text_val, label_prefix="", orient='v'):
        if orient == 'v':
            ax.annotate(text='', xy=(x_pos, y_start), xytext=(x_pos, y_end), arrowprops=dict(arrowstyle='<|-|>', color=COLOR_DIM, lw=LW_DIM))
            mid_y = (y_start + y_end) / 2
            txt = f"{label_prefix} {int(text_val)}" if label_prefix else f"{int(text_val)}"
            ax.text(x_pos + 8, mid_y, txt, color=COLOR_DIM, fontsize=9, va='center')
            ax.plot([plate_x+plate_w, x_pos+2], [y_start, y_start], color=COLOR_DIM, lw=0.5, ls=':')
            ax.plot([plate_x+plate_w, x_pos+2], [y_end, y_end], color=COLOR_DIM, lw=0.5, ls=':')
        else:
            ax.annotate(text='', xy=(y_start, x_pos), xytext=(y_end, x_pos), arrowprops=dict(arrowstyle='<|-|>', color=COLOR_DIM, lw=LW_DIM))
            mid_x = (y_start + y_end) / 2
            txt = f"{int(text_val)}"
            ax.text(mid_x, x_pos - 8, txt, color=COLOR_DIM, fontsize=9, ha='center', va='top')
            
    dim_x_offset = plate_x + plate_w + 25
    draw_dim_arrow(plate_y_start + plate_len_mm, bolt_ys[0], dim_x_offset, le_cm*10, "Le", 'v')
    for i in range(len(bolt_ys)-1):
        draw_dim_arrow(bolt_ys[i], bolt_ys[i+1], dim_x_offset, spacing_cm*10, "S", 'v')
    draw_dim_arrow(bolt_ys[-1], plate_y_start, dim_x_offset, le_cm*10, "Le", 'v')
    
    dim_y_horz = plate_y_start - 20
    draw_dim_arrow(plate_x, bolt_x_center, dim_y_horz, plate_w/2, "", 'h')
    draw_dim_arrow(bolt_x_center, plate_x+plate_w, dim_y_horz, plate_w/2, "", 'h')
    
    ax.plot([plate_x, plate_x], [plate_y_start, dim_y_horz-2], color=COLOR_DIM, lw=0.5, ls=':')
    ax.plot([bolt_x_center, bolt_x_center], [plate_y_start, dim_y_horz-2], color=COLOR_DIM, lw=0.5, ls=':')
    ax.plot([plate_x + plate_w, plate_x + plate_w], [plate_y_start, dim_y_horz-2], color=COLOR_DIM, lw=0.5, ls=':')

    outer_dim_x = dim_x_offset + 40
    ax.annotate(text='', xy=(outer_dim_x, plate_y_start), xytext=(outer_dim_x, plate_y_start + plate_len_mm), arrowprops=dict(arrowstyle='<|-|>', color=COLOR_OBJ, lw=LW_DIM))
    ax.text(outer_dim_x + 10, plate_y_start + plate_len_mm/2, f"TOTAL PL = {int(plate_len_mm)}", color=COLOR_OBJ, fontsize=10, fontweight='bold', rotation=90, va='center')

    ax.text(plate_x + plate_w/2, plate_y_start - 50, f"PL-100x{int(plate_len_mm)}x10mm", fontsize=10, color=COLOR_OBJ, ha='center', fontweight='bold')
    ax.text(plate_x + plate_w/2, plate_y_start - 65, f"({n_bolts}-M{int(bolt_dia)} A325 Bolts)", fontsize=9, color=COLOR_OBJ, ha='center')

    ax.set_xlim(0, web_w_draw + 100)
    ax.set_ylim(0, h_draw_area)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("CONNECTION SHOP DRAWING (N.T.S)", fontsize=12, fontweight='bold', color=COLOR_OBJ, pad=20)
    return fig

# =========================================================
# 🖥️ 4. RENDER UI & APP LOGIC
# =========================================================
def render_report_tab(beam_data=None, conn_data=None):
    st.markdown("### 🖨️ Structural Calculation Workbench (v42.0)")
    
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
            
    # Calculate Single Case
    selected_props = next(s for s in all_sections if s['name'] == selected_sec_name)
    factor = get_load_case_factor(load_case)
    res = calculate_connection(selected_props, load_pct, bolt_dia, factor, load_case)
    
    st.divider()

    # 2. Detailed Report & Drawing
    col_cal, col_draw = st.columns([1.5, 1.2]) 
    
    with col_cal:
        st.subheader("📝 รายการคำนวณ (Analysis Report)")
        with st.container(height=600, border=True):
            st.markdown(f"""
#### Results: {res['Section']}
* **Safe Span:** {res['L_safe']:.2f} m
* **Control By:** {res['Control By']} (Bolt) / {'Moment' if res['L_crit_moment'] < res['L_crit_defl'] else 'Deflection'} (Span)

**Span Limits (Strength vs Stiffness):**
* Strength (Moment): **{res['L_crit_moment']:.2f} m**
* Stiffness (Deflection): **{res['L_crit_defl']:.2f} m**

**Shear & Bolt Check:**
* Beam Shear Capacity ($V_n$): {res['Vn_beam']:,.0f} kg
* Load Target ($V_u$): {res['V_target']:,.0f} kg
* Bolt Capacity per Unit: {res['phiRn_bolt']:,.0f} kg
* Required Bolts: **{res['Bolt Qty']} pcs**
""")

    with col_draw:
        st.subheader("📐 Shop Drawing")
        fig = draw_connection_sketch(res['h'], res['Bolt Qty'], float(bolt_dia), res['Plate Len']*10, res['Le'], res['S'])
        st.pyplot(fig)

    st.divider()

    # =====================================================
    # 📊 NEW! DUAL AXIS CHART (Includes 75% Shear)
    # =====================================================
    st.subheader("📊 แนวโน้มพฤติกรรมหน้าตัด (Strength vs Stiffness vs Shear)")
    
    # 1. Prepare Batch Data
    names = []
    moments = []
    defls = []
    shears = [] 
    shears_75 = [] # 🔥 New 75% List
    
    batch_results = [] # For Table

    for sec in all_sections:
        r = calculate_connection(sec, load_pct, bolt_dia, factor, load_case)
        names.append(sec['name'].replace("H-", "")) 
        moments.append(r['L_crit_moment'])
        defls.append(r['L_crit_defl'])
        
        shears.append(r['Vn_beam']) 
        shears_75.append(r['Vn_beam'] * 0.75) # 🔥 Calculate 75%
        
        # Data for Table
        ctrl = "Moment" if r['L_crit_moment'] < r['L_crit_defl'] else "Deflection"
        batch_results.append({
            "Section": r['Section'],
            "Safe Span (m)": r['L_safe'],
            "Shear Cap (kg)": r['Vn_beam'],
            "Control": ctrl,
            "Bolts": r['Bolt Qty']
        })
        
    # 2. Create Dual Axis Plot
    fig2, ax1 = plt.subplots(figsize=(12, 6))
    
    x_indices = range(len(names))
    
    # --- Left Axis (Span - meters) ---
    ax1.set_xlabel('Section Size')
    ax1.set_ylabel('Safe Span Length (m)', color='#2C3E50', fontweight='bold')
    
    l1 = ax1.plot(x_indices, moments, color='#E74C3C', linestyle='--', marker='o', markersize=4, label='Moment Limit (m)', alpha=0.8)
    l2 = ax1.plot(x_indices, defls, color='#3498DB', linestyle='-', marker='s', markersize=4, label='Deflection Limit (m)', alpha=0.8)
    
    # Fill Safe Area
    min_vals = np.minimum(moments, defls)
    ax1.fill_between(x_indices, 0, min_vals, color='#2ECC71', alpha=0.2, label='Safe Span Zone')

    # --- Right Axis (Shear - kg) ---
    ax2 = ax1.twinx()
    ax2.set_ylabel('Shear Capacity (kg)', color='#8E44AD', fontweight='bold')
    
    # 100% Shear Line
    l3 = ax2.plot(x_indices, shears, color='#8E44AD', linestyle=':', linewidth=2, label='Shear Cap. (100%)', alpha=0.6)
    
    # 🔥 75% Shear Line
    l4 = ax2.plot(x_indices, shears_75, color='#D2B4DE', linestyle='-.', linewidth=1.5, label='Shear Cap. (75%)', alpha=0.8)

    # Highlight Selected
    try:
        current_idx = [s['name'] for s in all_sections].index(selected_sec_name)
        ax1.axvline(x=current_idx, color='#F1C40F', linestyle='-', linewidth=2, alpha=0.5)
    except:
        pass

    # Combine Legends
    lns = l1 + l2 + l3 + l4
    labs = [l.get_label() for l in lns]
    ax1.legend(lns, labs, loc='upper left')

    # Styling
    ax1.set_xticks(x_indices)
    ax1.set_xticklabels(names, rotation=90, fontsize=8)
    ax1.grid(True, linestyle=':', alpha=0.5)
    
    st.pyplot(fig2)
    
    st.info("""
    **คำอธิบายกราฟ (2 แกน):**
    * 🔴🔵 **เส้นแดง/ฟ้า (แกนซ้าย - เมตร):** ดูความยาวที่รับได้
    * 🟣 **เส้นม่วงเข้ม (แกนขวา - kg):** ความสามารถรับแรงเฉือนสูงสุด ($V_n$)
    * 🟣 **เส้นม่วงอ่อน (แกนขวา - kg):** เส้น 75% ของแรงเฉือนสูงสุด (เอาไว้ดูระยะปลอดภัยหรือจุดใช้งานจริง)
    """)

    # =====================================================
    # 📋 DATA TABLE
    # =====================================================
    st.markdown("##### 📋 ตารางสรุปผล (Summary Table)")
    
    df = pd.DataFrame(batch_results)
    
    def get_icon(val):
        return "🛑 Strength" if val == "Moment" else "〰️ Stiffness"
    
    df["Status"] = df["Control"].apply(get_icon)

    st.dataframe(
        df[["Section", "Safe Span (m)", "Status", "Shear Cap (kg)", "Bolts"]],
        use_container_width=True,
        column_config={
            "Section": st.column_config.TextColumn("Section", width="medium"),
            "Safe Span (m)": st.column_config.NumberColumn("Safe Span (m)", format="%.2f"),
            "Shear Cap (kg)": st.column_config.NumberColumn("Shear Cap ($V_n$)", format="%.0f"),
            "Bolts": st.column_config.NumberColumn("Bolts Req.", format="%d"),
            "Status": st.column_config.TextColumn("Limitation"),
        },
        hide_index=True,
        height=400
    )

if __name__ == "__main__":
    st.set_page_config(page_title="Structural Workbench", layout="wide")
    render_report_tab()
