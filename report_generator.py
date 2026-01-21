# report_generator.py
# Version: 49.0 (Full Database Table + Section View Drawing)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np 
import math

# =========================================================
# 🏗️ 1. DATABASE & PROPERTIES
# =========================================================
def get_standard_sections():
    # ข้อมูลดิบ (Raw Data)
    return [
        {"name": "H-100x50x5x7",    "h": 100, "b": 50,  "tw": 5,  "tf": 7,  "Fy": 2500, "Fu": 4100},
        {"name": "H-100x100x6x8",   "h": 100, "b": 100, "tw": 6,  "tf": 8,  "Fy": 2500, "Fu": 4100},
        {"name": "H-125x60x6x8",    "h": 125, "b": 60,  "tw": 6,  "tf": 8,  "Fy": 2500, "Fu": 4100},
        {"name": "H-125x125x6.5x9", "h": 125, "b": 125, "tw": 6.5,"tf": 9,  "Fy": 2500, "Fu": 4100},
        {"name": "H-150x75x5x7",    "h": 150, "b": 75,  "tw": 5,  "tf": 7,  "Fy": 2500, "Fu": 4100},
        {"name": "H-150x150x7x10",  "h": 150, "b": 150, "tw": 7,  "tf": 10, "Fy": 2500, "Fu": 4100},
        {"name": "H-175x90x5x8",    "h": 175, "b": 90,  "tw": 5,  "tf": 8,  "Fy": 2500, "Fu": 4100},
        {"name": "H-175x175x7.5x11","h": 175, "b": 175, "tw": 7.5,"tf": 11, "Fy": 2500, "Fu": 4100},
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
        {"name": "H-700x300x13x24", "h": 700, "b": 300, "tw": 13, "tf": 24, "Fy": 2500, "Fu": 4100},
        {"name": "H-800x300x14x26", "h": 800, "b": 300, "tw": 14, "tf": 26, "Fy": 2500, "Fu": 4100},
        {"name": "H-900x300x16x28", "h": 900, "b": 300, "tw": 16, "tf": 28, "Fy": 2500, "Fu": 4100},
    ]

def calculate_full_properties(props):
    # ฟังก์ชันคำนวณ Properties (ใช้สำหรับสร้างตารางรวม)
    h, b, tw, tf = props['h']/10, props['b']/10, props['tw']/10, props['tf']/10 # cm
    
    # Area
    A = (2 * b * tf) + ((h - 2*tf) * tw)
    
    # Inertia Ix
    outer_I = (b * h**3) / 12
    inner_w = b - tw
    inner_h = h - (2*tf)
    inner_I = (inner_w * inner_h**3) / 12
    Ix = outer_I - inner_I
    
    # Modulus
    Sx = Ix / (h/2) # Elastic
    Zx = (b*tf*(h-tf)) + (tw*(h-2*tf)**2/4) # Plastic
    
    return {
        "Name": props['name'],
        "h": props['h'], "b": props['b'], "tw": props['tw'], "tf": props['tf'],
        "Area (cm2)": round(A, 2),
        "Ix (cm4)": round(Ix, 0),
        "Zx (cm3)": round(Zx, 0),
        "Sx (cm3)": round(Sx, 0)
    }

def get_full_database_df():
    # สร้าง DataFrame รวมเหล็กทุกตัว
    sections = get_standard_sections()
    data = [calculate_full_properties(s) for s in sections]
    return pd.DataFrame(data)

# =========================================================
# ⚙️ 2. CALCULATION ENGINE
# =========================================================
def get_load_case_factor(case_name):
    cases = {"Simple Beam (Uniform Load)": 4.0, "Simple Beam (Point Load @Center)": 2.0, "Cantilever (Uniform Load)": 2.0, "Cantilever (Point Load @Tip)": 1.0}
    return cases.get(case_name, 4.0)

def calculate_connection(props, load_percent, bolt_dia, span_factor, case_name):
    # Logic เดิมที่ถูกต้อง (Green Zone = Moment/Deflection)
    full_props = calculate_full_properties(props) # Reuse calculation
    h, tw, fy, fu = props['h'], props['tw'], props['Fy'], props['Fu']
    
    Vn_beam = 0.60 * fy * (h/10)*(tw/10)
    V_target = (load_percent/100) * Vn_beam
    
    # Moment
    Mn_beam = fy * full_props['Zx (cm3)']
    phiMn = 0.90 * Mn_beam
    L_crit_moment = (span_factor * (phiMn / V_target)) / 100.0 if V_target > 0 else 0
    
    # Deflection
    E = 2040000 
    Reaction = V_target 
    Limit_Factor = 360 
    coeff = 0
    if case_name == "Simple Beam (Uniform Load)": coeff = 192 / (5 * Limit_Factor)
    elif case_name == "Simple Beam (Point Load @Center)": coeff = 24 / Limit_Factor
    elif case_name == "Cantilever (Uniform Load)": coeff = 8 / Limit_Factor
    elif case_name == "Cantilever (Point Load @Tip)": coeff = 3 / Limit_Factor
    
    L_crit_defl = 0
    if Reaction > 0 and coeff > 0:
        L_sq = (coeff * E * full_props['Ix (cm4)']) / Reaction
        L_crit_defl = math.sqrt(L_sq) / 100.0 
    
    L_safe = min(L_crit_moment, L_crit_defl) if L_crit_defl > 0 else L_crit_moment
    
    # Bolt
    DB_mm = float(bolt_dia)
    Ab_cm2 = 3.1416 * (DB_mm/10)**2 / 4
    Rn_shear = 0.75 * 3300 * Ab_cm2 
    
    plate_t_mm = 10.0; Le_cm = 3.5; Lc_cm = Le_cm - ((DB_mm+2)/10)/2
    Rn_pl = 0.75 * min(1.2 * Lc_cm * (plate_t_mm/10) * 4050, 2.4 * (DB_mm/10) * (plate_t_mm/10) * 4050)
    Rn_web = 0.75 * min(1.2 * Lc_cm * (tw/10) * fu, 2.4 * (DB_mm/10) * (tw/10) * fu)
    phiRn_bolt = min(Rn_shear, Rn_pl, Rn_web)
    
    control_mode = "Bolt Shear"
    if Rn_pl < Rn_shear and Rn_pl < Rn_web: control_mode = "Plate Bear"
    if Rn_web < Rn_shear and Rn_web < Rn_pl: control_mode = "Web Bear"
    
    n_bolts = max(2, math.ceil(V_target / phiRn_bolt)) if phiRn_bolt > 0 else 99
    spacing = 7.0
    L_plate = (2*Le_cm) + ((n_bolts-1)*spacing)
    
    return {
        "Section": props['name'], "h": h, "b": props['b'], "tw": tw, "tf": props['tf'], 
        "Vn_beam": Vn_beam, "V_target": V_target, 
        "L_crit_moment": L_crit_moment, "L_crit_defl": L_crit_defl, "L_safe": L_safe,
        "DB": DB_mm, "phiRn_bolt": phiRn_bolt, "Bolt Qty": n_bolts, "Control By": control_mode,
        "Plate Len": L_plate, "Le": Le_cm, "S": spacing
    }

# =========================================================
# 🎨 3. DRAWING LOGIC (FULL SHOP DRAWING)
# =========================================================
def draw_full_shop_drawing(res):
    # สร้างรูป 2 View: Elevation + Section
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 6), gridspec_kw={'width_ratios': [1.5, 1]})
    
    # --- View 1: Elevation (ด้านข้าง) ---
    h, tw, L_plate = res['h'], res['tw'], res['Plate Len']*10
    web_w = 250
    h_draw = h + 150
    
    # Web
    ax1.add_patch(patches.Rectangle((0, 0), web_w, h_draw, facecolor='#ECF0F1'))
    # Plate
    pl_w = 100
    pl_x = (web_w - pl_w)/2
    pl_y = (h - L_plate)/2 + 75
    ax1.add_patch(patches.Rectangle((pl_x, pl_y), pl_w, L_plate, linewidth=2, edgecolor='#2C3E50', facecolor='#D6EAF8'))
    
    # Bolts
    bx = pl_x + pl_w/2
    by_start = pl_y + L_plate - (res['Le']*10)
    for i in range(res['Bolt Qty']):
        ax1.add_patch(patches.Circle((bx, by_start), (res['DB']+2)/2, edgecolor='black', facecolor='white'))
        ax1.text(bx+15, by_start, f"#{i+1}", fontsize=8, color='gray')
        by_start -= (res['S']*10)
        
    ax1.set_xlim(0, web_w); ax1.set_ylim(0, h_draw)
    ax1.set_title("ELEVATION", fontweight='bold')
    ax1.axis('off')

    # --- View 2: Section (หน้าตัด) ---
    b, tf = res['b'], res['tf']
    cx = 100 # Center X of section view
    
    # Flanges (Top & Bottom)
    ax2.add_patch(patches.Rectangle((cx - b/2, h_draw/2 + h/2 - tf), b, tf, facecolor='#7F8C8D', edgecolor='black')) # Top
    ax2.add_patch(patches.Rectangle((cx - b/2, h_draw/2 - h/2), b, tf, facecolor='#7F8C8D', edgecolor='black')) # Bottom
    
    # Web (Center)
    ax2.add_patch(patches.Rectangle((cx - tw/2, h_draw/2 - h/2 + tf), tw, h - 2*tf, facecolor='#95A5A6', edgecolor='black'))
    
    # Plate (Side of Web) - สมมติ Plate หนา 10mm
    pl_thk = 10
    ax2.add_patch(patches.Rectangle((cx + tw/2, h_draw/2 - L_plate/2), pl_thk, L_plate, facecolor='#3498DB', edgecolor='black'))
    
    # Bolt Line
    ax2.plot([cx-20, cx+40], [h_draw/2, h_draw/2], 'k-.', linewidth=0.5)
    
    ax2.set_xlim(0, 200); ax2.set_ylim(0, h_draw)
    ax2.set_title("SECTION", fontweight='bold')
    ax2.axis('off')

    plt.suptitle(f"SHOP DRAWING: {res['Section']} (N.T.S)", fontsize=14, fontweight='bold', color='#2C3E50')
    return fig

# =========================================================
# 🖥️ 4. APP UI
# =========================================================
def render_report_tab(beam_data=None, conn_data=None, *args, **kwargs):
    st.markdown("### 🖨️ Structural Calculation Workbench (Pro Version)")
    
    # --- 1. Database Table (NEW!) ---
    with st.expander("📂 ดูตารางเหล็กทั้งหมด (Standard Sections Database)", expanded=False):
        df_full = get_full_database_df()
        st.dataframe(df_full, use_container_width=True, hide_index=True)

    # --- 2. Controls ---
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1.5])
        all_sections = get_standard_sections()
        with c1: selected_sec_name = st.selectbox("เลือกหน้าตัด (Select Section)", [s['name'] for s in all_sections], index=10)
        with c2: load_pct = st.number_input("Load %", 10, 100, 75)
        with c3: bolt_dia = st.selectbox("Bolt Size", [12, 16, 20, 24], index=2)
        with c4: load_case = st.selectbox("Support Case", ["Simple Beam (Uniform Load)", "Simple Beam (Point Load @Center)", "Cantilever (Uniform Load)", "Cantilever (Point Load @Tip)"])
            
    # Calculate
    selected_props = next(s for s in all_sections if s['name'] == selected_sec_name)
    factor = get_load_case_factor(load_case)
    res = calculate_connection(selected_props, load_pct, bolt_dia, factor, load_case)
    
    st.divider()

    # --- 3. Results & Shop Drawing ---
    c_left, c_right = st.columns([1, 1.5])
    
    with c_left:
        st.subheader("📝 Summary Result")
        st.info(f"✅ **Safe Span Limit: {res['L_safe']:.2f} m**")
        
        st.markdown("**Check List:**")
        st.markdown(f"- Moment Span: `{res['L_crit_moment']:.2f} m`")
        st.markdown(f"- Deflection Span: `{res['L_crit_defl']:.2f} m`")
        st.markdown(f"- Shear Load: `{res['V_target']:,.0f} kg` (Capacity: `{res['Vn_beam']:,.0f}`) fit `{res['Bolt Qty']}-M{int(res['DB'])}`")
        
    with c_right:
        # Drawing Logic (New)
        fig = draw_full_shop_drawing(res)
        st.pyplot(fig)

    st.divider()

    # --- 4. The Graph (Safe Zone Logic) ---
    st.subheader("📊 Design Envelope (Safe Zone)")
    
    names, moments, defls, shears = [], [], [], []
    for sec in all_sections:
        r = calculate_connection(sec, load_pct, bolt_dia, factor, load_case)
        names.append(sec['name'].replace("H-", "")) 
        moments.append(r['L_crit_moment'])
        defls.append(r['L_crit_defl'])
        shears.append(r['Vn_beam']) 

    fig2, ax1 = plt.subplots(figsize=(12, 5))
    x = range(len(names))
    
    # Span Axis
    ax1.set_ylabel('Span (m)', color='#27AE60', fontweight='bold')
    ax1.plot(x, moments, 'r--', label='Moment Limit', alpha=0.5)
    ax1.plot(x, defls, 'b-', label='Deflection Limit', alpha=0.5)
    ax1.fill_between(x, 0, np.minimum(moments, defls), color='#2ECC71', alpha=0.3, label='Safe Zone')
    
    # Shear Axis
    ax2 = ax1.twinx()
    ax2.set_ylabel('Shear Capacity (kg)', color='purple', fontweight='bold')
    ax2.plot(x, shears, color='purple', linestyle=':', label='Shear Check (Ref)')

    # Highlight
    idx = [s['name'] for s in all_sections].index(selected_sec_name)
    ax1.plot(idx, res['L_safe'], 'g*', markersize=15)
    ax1.axvline(x=idx, color='orange', alpha=0.5)

    ax1.legend(loc='upper left')
    ax1.set_xticks(x); ax1.set_xticklabels(names, rotation=90, fontsize=8)
    ax1.grid(True, linestyle=':', alpha=0.5)
    
    st.pyplot(fig2)

if __name__ == "__main__":
    st.set_page_config(page_title="Structural Workbench", layout="wide")
    render_report_tab()
