# report_generator.py
# Version: 46.0 (Pure Engineering Logic - No Shear Shading)
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

    # Simplified Dimensions
    ax.set_xlim(0, web_w_draw + 50)
    ax.set_ylim(0, h_draw_area)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("SHOP DRAWING (N.T.S)", fontsize=12, fontweight='bold', color=COLOR_OBJ, pad=10)
    return fig

# =========================================================
# 🖥️ 4. RENDER UI & APP LOGIC
# =========================================================
def render_report_tab(beam_data=None, conn_data=None):
    st.markdown("### 🖨️ Structural Calculation Workbench (Final Logic)")
    
    # 1. Controls
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1.5])
        all_sections = get_standard_sections()
        with c1:
            selected_sec_name = st.selectbox("Select Section", [s['name'] for s in all_sections], index=10)
        with c2:
            load_pct = st.number_input("Load % (of Vn)", 10, 100, 75, step=5)
        with c3:
            bolt_dia = st.selectbox("Bolt", [12, 16, 20, 24], index=2)
        with c4:
            load_case = st.selectbox("Support", ["Simple Beam (Uniform Load)", "Simple Beam (Point Load @Center)", "Cantilever (Uniform Load)", "Cantilever (Point Load @Tip)"])
            
    # Calculate
    selected_props = next(s for s in all_sections if s['name'] == selected_sec_name)
    factor = get_load_case_factor(load_case)
    res = calculate_connection(selected_props, load_pct, bolt_dia, factor, load_case)
    
    st.divider()

    col_cal, col_draw = st.columns([1.5, 1.2]) 
    with col_cal:
        st.subheader("📝 รายการคำนวณ")
        with st.container(height=400, border=True):
            st.markdown(f"""
            **Section:** {res['Section']}
            
            **1. Safe Span:** `{res['L_safe']:.2f} m` 
            *(Controlled by {res['Control By'] if res['Control By'] in ['Shear','Bolt'] else 'Moment/Deflection'})*
            
            **2. Span Limits (Geometric Constraints):**
            * Moment Limit: `{res['L_crit_moment']:.2f} m`
            * Deflection Limit: `{res['L_crit_defl']:.2f} m`
            
            **3. Shear Check (Capacity Constraints):**
            * Shear Capacity ($V_n$): `{res['Vn_beam']:,.0f} kg`
            * Current Load ($V_u$): `{res['V_target']:,.0f} kg`
            * Status: {"✅ OK" if res['V_target'] < res['Vn_beam'] else "❌ FAIL"}
            """)

    with col_draw:
        fig = draw_connection_sketch(res['h'], res['Bolt Qty'], float(bolt_dia), res['Plate Len']*10, res['Le'], res['S'])
        st.pyplot(fig)

    st.divider()

    # =====================================================
    # 📊 GRAPH UPDATE (Corrected Logic)
    # =====================================================
    st.subheader("📊 Structural Limit States Diagram")
    
    names = []
    moments = []
    defls = []
    shears = [] 
    
    for sec in all_sections:
        r = calculate_connection(sec, load_pct, bolt_dia, factor, load_case)
        names.append(sec['name'].replace("H-", "")) 
        moments.append(r['L_crit_moment'])
        defls.append(r['L_crit_defl'])
        shears.append(r['Vn_beam']) 

    fig2, ax1 = plt.subplots(figsize=(12, 6))
    x_indices = range(len(names))
    
    # --- Left Axis (Span) ---
    ax1.set_xlabel('Section Size')
    ax1.set_ylabel('Span Length (m)', color='#2C3E50', fontweight='bold')
    
    l1 = ax1.plot(x_indices, moments, color='#E74C3C', linestyle='--', marker='o', markersize=4, label='Moment Limit', alpha=0.9)
    l2 = ax1.plot(x_indices, defls, color='#3498DB', linestyle='-', label='Deflection Limit', alpha=0.8)
    
    # 🔥 GREEN AREA: Only under Moment & Deflection
    # ไม่มีการระบายสีเขียวที่เกี่ยวข้องกับ Shear เลย
    min_vals = np.minimum(moments, defls)
    ax1.fill_between(x_indices, 0, min_vals, color='#2ECC71', alpha=0.3, label='Safe Span Zone')
    
    # --- Right Axis (Shear Force) ---
    ax2 = ax1.twinx()
    ax2.set_ylabel('Shear Capacity (kg)', color='#8E44AD', fontweight='bold')
    
    # Shear Plot as Reference (Dashed / Dotted)
    # แสดงเป็นเส้นอ้างอิงเท่านั้น ไม่มีการ Fill
    l3 = ax2.plot(x_indices, shears, color='#8E44AD', linestyle=':', linewidth=1.5, label='Shear Capacity Check', alpha=0.5)

    # Highlight Current
    try:
        current_idx = [s['name'] for s in all_sections].index(selected_sec_name)
        ax1.axvline(x=current_idx, color='#F1C40F', linestyle='-', linewidth=2, alpha=0.6)
        
        safe_val = res['L_safe']
        ax1.plot(current_idx, safe_val, 'g*', markersize=15, zorder=10)
        ax1.text(current_idx, safe_val + 0.5, f" {safe_val:.2f}m", color='green', fontweight='bold')
    except:
        pass

    # Legends
    lns = l1 + l2 + [patches.Patch(color='#2ECC71', alpha=0.3, label='Safe Span Zone')] + l3
    labs = [l.get_label() for l in lns]
    ax1.legend(lns, labs, loc='upper left')

    ax1.set_xticks(x_indices)
    ax1.set_xticklabels(names, rotation=90, fontsize=8)
    ax1.grid(True, linestyle=':', alpha=0.5)
    ax1.set_title(f"Design Envelope (Defined by Moment & Deflection Only)", fontweight='bold')
    
    st.pyplot(fig2)
    
    st.info("💡 **Note:** พื้นที่สีเขียว (Safe Span Zone) ถูกกำหนดโดย Moment และ Deflection เท่านั้น ส่วน **Shear Capacity** แสดงไว้ในแกนขวาเพื่อใช้ตรวจสอบ (Check) แต่ไม่ได้เป็นตัวกำหนดพื้นที่ปลอดภัยในการใช้งานปกติครับ")

if __name__ == "__main__":
    st.set_page_config(page_title="Structural Workbench", layout="wide")
    render_report_tab()
