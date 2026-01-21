# report_generator.py
# Version: 47.0 (Full Data Restoration + Correct Logic)
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
    # ข้อมูลหน้าตัดมาตรฐาน (Standard Sections)
    return [
        {"name": "H-100x50x5x7",    "h": 100, "b": 50,  "tw": 5,  "tf": 7,  "Fy": 2500, "Fu": 4100},
        {"name": "H-100x100x6x8",   "h": 100, "b": 100, "tw": 6,  "tf": 8,  "Fy": 2500, "Fu": 4100},
        {"name": "H-125x60x6x8",    "h": 125, "b": 60,  "tw": 6,  "tf": 8,  "Fy": 2500, "Fu": 4100},
        {"name": "H-125x125x6.5x9", "h": 125, "b": 125, "tw": 6.5,"tf": 9,  "Fy": 2500, "Fu": 4100},
        {"name": "H-150x75x5x7",    "h": 150, "b": 75,  "tw": 5,  "tf": 7,  "Fy": 2500, "Fu": 4100},
        {"name": "H-150x150x7x10",  "h": 150, "b": 150, "tw": 7,  "tf": 10, "Fy": 2500, "Fu": 4100},
        {"name": "H-175x90x5x8",    "h": 175, "b": 90,  "tw": 5,  "tf": 8,  "Fy": 2500, "Fu": 4100},
        {"name": "H-200x100x5.5x8", "h": 200, "b": 100, "tw": 5.5,"tf": 8,  "Fy": 2500, "Fu": 4100},
        {"name": "H-200x200x8x12",  "h": 200, "b": 200, "tw": 8,  "tf": 12, "Fy": 2500, "Fu": 4100},
        {"name": "H-250x125x6x9",   "h": 250, "b": 125, "tw": 6,  "tf": 9,  "Fy": 2500, "Fu": 4100},
        {"name": "H-250x250x9x14",  "h": 250, "b": 250, "tw": 9,  "tf": 14, "Fy": 2500, "Fu": 4100},
        {"name": "H-300x150x6.5x9", "h": 300, "b": 150, "tw": 6.5,"tf": 9,  "Fy": 2500, "Fu": 4100},
        {"name": "H-300x300x10x15", "h": 300, "b": 300, "tw": 10, "tf": 15, "Fy": 2500, "Fu": 4100},
        {"name": "H-350x175x7x11",  "h": 350, "b": 175, "tw": 7,  "tf": 11, "Fy": 2500, "Fu": 4100},
        {"name": "H-350x350x12x19", "h": 350, "b": 350, "tw": 12, "tf": 19, "Fy": 2500, "Fu": 4100},
        {"name": "H-400x200x8x13",  "h": 400, "b": 200, "tw": 8,  "tf": 13, "Fy": 2500, "Fu": 4100},
        {"name": "H-400x400x13x21", "h": 400, "b": 400, "tw": 13, "tf": 21, "Fy": 2500, "Fu": 4100},
        {"name": "H-450x200x9x14",  "h": 450, "b": 200, "tw": 9,  "tf": 14, "Fy": 2500, "Fu": 4100},
        {"name": "H-500x200x10x16", "h": 500, "b": 200, "tw": 10, "tf": 16, "Fy": 2500, "Fu": 4100},
        {"name": "H-600x200x11x17", "h": 600, "b": 200, "tw": 11, "tf": 17, "Fy": 2500, "Fu": 4100},
        {"name": "H-800x300x14x26", "h": 800, "b": 300, "tw": 14, "tf": 26, "Fy": 2500, "Fu": 4100},
    ]

# =========================================================
# ⚙️ 2. CORE LOGIC (ENGINE)
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
    
    # 1. Beam Shear Capacity
    Aw_cm2 = (h/10)*(tw/10) 
    Vn_beam = 0.60 * fy * Aw_cm2
    V_target = (load_percent/100) * Vn_beam
    
    # 2. Moment Capacity & Span
    Zx = calculate_zx(h, b, tw, tf)
    Mn_beam = fy * Zx
    phiMn = 0.90 * Mn_beam
    L_crit_moment = (span_factor * (phiMn / V_target)) / 100.0 if V_target > 0 else 0
    
    # 3. Deflection Span
    Ix = calculate_ix(h, b, tw, tf)
    L_crit_defl = calculate_deflection_limit(Ix, V_target, case_name)
    
    # Safe Span (Envelope)
    L_safe = min(L_crit_moment, L_crit_defl) if L_crit_defl > 0 else L_crit_moment
    
    # 4. Connection Details (The Missing Data!)
    DB_mm = float(bolt_dia)
    Ab_cm2 = 3.1416 * (DB_mm/10)**2 / 4
    Fnv = 3300 # A325
    
    # 4.1 Bolt Shear Strength
    Rn_shear = 0.75 * Fnv * Ab_cm2 
    
    # 4.2 Plate Bearing
    plate_t_mm = 10.0
    Le_cm = 3.5
    hole_dia_mm = DB_mm + 2
    Lc_cm = Le_cm - (hole_dia_mm/10)/2
    Rn_pl_1 = 1.2 * Lc_cm * (plate_t_mm/10) * 4050 # Fu plate (assuming A36/SS400)
    Rn_pl_2 = 2.4 * (DB_mm/10) * (plate_t_mm/10) * 4050
    Rn_pl = 0.75 * min(Rn_pl_1, Rn_pl_2)
    
    # 4.3 Web Bearing
    Rn_web_1 = 1.2 * Lc_cm * (tw/10) * fu # Fu Beam
    Rn_web_2 = 2.4 * (DB_mm/10) * (tw/10) * fu
    Rn_web = 0.75 * min(Rn_web_1, Rn_web_2)
    
    # Governing Bolt Capacity
    phiRn_bolt = min(Rn_shear, Rn_pl, Rn_web)
    
    # Determine Control Mode
    control_mode = "Bolt Shear"
    if Rn_pl < Rn_shear and Rn_pl < Rn_web: control_mode = "Plate Bearing"
    if Rn_web < Rn_shear and Rn_web < Rn_pl: control_mode = "Web Bearing"
    
    # Bolt Quantity
    if phiRn_bolt > 0:
        n_req = V_target / phiRn_bolt
        n_bolts = max(2, math.ceil(n_req))
    else:
        n_bolts = 99
        
    spacing = 7.0
    L_plate = (2*Le_cm) + ((n_bolts-1)*spacing)
    
    return {
        "Section": props['name'], "h": h, "tw": tw, "Fy": fy, "Fu": fu, "Aw": Aw_cm2, 
        "Zx": Zx, "Ix": Ix,
        "Vn_beam": Vn_beam, "V_target": V_target, 
        "L_crit_moment": L_crit_moment, "L_crit_defl": L_crit_defl, "L_safe": L_safe,
        "Mn_beam": Mn_beam,
        "DB": DB_mm, "Ab": Ab_cm2, 
        # Detailed Data Returned
        "Rn_shear": Rn_shear, "Rn_pl": Rn_pl, "Rn_web": Rn_web,
        "phiRn_bolt": phiRn_bolt, "Bolt Qty": n_bolts, "Control By": control_mode,
        "Plate Len": L_plate, "Le": Le_cm, "S": spacing
    }

# =========================================================
# 🎨 3. DRAWING LOGIC
# =========================================================
def draw_connection_sketch(h_beam, n_bolts, bolt_dia, plate_len_mm, le_cm, spacing_cm):
    fig, ax = plt.subplots(figsize=(5, 7.5))
    COLOR_OBJ = '#2C3E50' 
    COLOR_DIM = '#E74C3C' 
    
    web_w_draw = 200 
    h_draw_area = h_beam + 120
    plate_w = 100
    plate_x = (web_w_draw - plate_w) / 2
    plate_y_start = (h_beam - plate_len_mm) / 2 + 60
    
    # Web
    ax.add_patch(patches.Rectangle((0, 0), web_w_draw, h_draw_area, facecolor='#ECF0F1', zorder=1))
    
    # Plate
    ax.add_patch(patches.Rectangle((plate_x, plate_y_start), plate_w, plate_len_mm, linewidth=2, edgecolor=COLOR_OBJ, facecolor='#D6EAF8', zorder=2))
    
    # Bolts
    bolt_x_center = plate_x + (plate_w / 2)
    bolt_y_top = plate_y_start + plate_len_mm - (le_cm*10)
    curr_y = bolt_y_top
    
    for i in range(n_bolts):
        circle = patches.Circle((bolt_x_center, curr_y), radius=(bolt_dia+2)/2, edgecolor=COLOR_OBJ, facecolor='white', linewidth=1.5, zorder=3)
        ax.add_patch(circle)
        curr_y -= (spacing_cm*10)

    ax.set_xlim(0, web_w_draw + 50)
    ax.set_ylim(0, h_draw_area)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("SHOP DRAWING", fontsize=12, fontweight='bold', color=COLOR_OBJ)
    return fig

# =========================================================
# 🖥️ 4. APP UI
# =========================================================
def render_report_tab():
    st.markdown("### 🖨️ Structural Calculation Workbench (Full Data)")
    
    # --- Controls ---
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1.5])
        all_sections = get_standard_sections()
        with c1: selected_sec_name = st.selectbox("Section", [s['name'] for s in all_sections], index=10)
        with c2: load_pct = st.number_input("Load % (of Vn)", 10, 100, 75)
        with c3: bolt_dia = st.selectbox("Bolt M", [12, 16, 20, 24], index=2)
        with c4: load_case = st.selectbox("Case", ["Simple Beam (Uniform Load)", "Simple Beam (Point Load @Center)", "Cantilever (Uniform Load)", "Cantilever (Point Load @Tip)"])
            
    # --- Calculation ---
    selected_props = next(s for s in all_sections if s['name'] == selected_sec_name)
    factor = get_load_case_factor(load_case)
    res = calculate_connection(selected_props, load_pct, bolt_dia, factor, load_case)
    
    st.divider()

    # --- RESULTS DISPLAY (The Data is Back!) ---
    col_cal, col_draw = st.columns([1.5, 1.2]) 
    with col_cal:
        st.subheader("📝 รายการคำนวณละเอียด")
        with st.container(height=450, border=True):
            
            # 1. Main Checks
            st.markdown(f"**1. Geometric Check (Design Envelope)**")
            st.markdown(f"- Moment Limit Span: `{res['L_crit_moment']:.2f} m`")
            st.markdown(f"- Deflection Limit Span: `{res['L_crit_defl']:.2f} m`")
            st.success(f"👉 **Safe Span (Recommend): {res['L_safe']:.2f} m**")
            
            st.divider()
            
            # 2. Shear Capacity
            st.markdown(f"**2. Beam Shear Capacity ($V_n$)**")
            st.markdown(f"- $V_n$ (Capacity): `{res['Vn_beam']:,.0f} kg`")
            st.markdown(f"- $V_u$ (Target Load {load_pct}%): `{res['V_target']:,.0f} kg`")
            
            st.divider()
            
            # 3. Connection Detail (FULL DATA)
            st.markdown(f"**3. Connection Design (M{int(res['DB'])})**")
            st.markdown(f"Fail Mode Control: **{res['Control By']}**")
            
            # Create a mini dataframe for clean comparison
            conn_df = pd.DataFrame({
                "Check Mode": ["Bolt Shear", "Plate Bearing", "Web Bearing"],
                "Capacity (kg/bolt)": [res['Rn_shear'], res['Rn_pl'], res['Rn_web']]
            })
            st.dataframe(conn_df, hide_index=True)
            
            st.markdown(f"- **Capacity per Bolt ($\phi R_n$):** `{res['phiRn_bolt']:,.0f} kg`")
            st.markdown(f"- **Bolts Required:** `{res['Bolt Qty']} pcs`")

    with col_draw:
        fig = draw_connection_sketch(res['h'], res['Bolt Qty'], float(bolt_dia), res['Plate Len']*10, res['Le'], res['S'])
        st.pyplot(fig)

    st.divider()

    # --- GRAPH (Correct Logic Only) ---
    st.subheader("📊 Structural Limit States Diagram")
    
    names = []
    moments = []
    defls = []
    shears = [] 
    targets = []
    
    for sec in all_sections:
        r = calculate_connection(sec, load_pct, bolt_dia, factor, load_case)
        names.append(sec['name'].replace("H-", "")) 
        moments.append(r['L_crit_moment'])
        defls.append(r['L_crit_defl'])
        shears.append(r['Vn_beam']) 
        targets.append(r['V_target'])

    fig2, ax1 = plt.subplots(figsize=(12, 6))
    x = range(len(names))
    
    # Plot Span (Left Axis)
    ax1.set_ylabel('Safe Span Length (m)', color='#27AE60', fontweight='bold')
    l1 = ax1.plot(x, moments, color='#E74C3C', linestyle='--', marker='o', markersize=3, label='Moment Limit')
    l2 = ax1.plot(x, defls, color='#3498DB', linestyle='-', label='Deflection Limit')
    
    # GREEN ZONE (Corrected: Under Moment & Defl Only)
    min_vals = np.minimum(moments, defls)
    ax1.fill_between(x, 0, min_vals, color='#2ECC71', alpha=0.3, label='Safe Span Zone')
    
    # Plot Shear (Right Axis)
    ax2 = ax1.twinx()
    ax2.set_ylabel('Shear Load (kg)', color='#8E44AD', fontweight='bold')
    l3 = ax2.plot(x, shears, color='#8E44AD', linestyle=':', label='Shear Capacity (Vn)')
    l4 = ax2.plot(x, targets, color='gray', linestyle='-.', alpha=0.5, label=f'Current Load ({load_pct}%)')

    # Highlight
    idx = [s['name'] for s in all_sections].index(selected_sec_name)
    ax1.axvline(x=idx, color='#F1C40F', linewidth=2)
    ax1.plot(idx, res['L_safe'], 'g*', markersize=15)

    # Legend
    lns = l1 + l2 + [patches.Patch(color='#2ECC71', alpha=0.3, label='Safe Span Zone')] + l3 + l4
    ax1.legend(lns, [l.get_label() for l in lns], loc='upper left')

    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=90, fontsize=8)
    ax1.grid(True, linestyle=':', alpha=0.5)
    
    st.pyplot(fig2)

if __name__ == "__main__":
    st.set_page_config(page_title="Structural Workbench", layout="wide")
    render_report_tab()
