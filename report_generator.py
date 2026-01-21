# report_generator.py
# Version: 48.0 (Fixed Error + Added Section Properties Table)
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
    # ข้อมูลหน้าตัดมาตรฐาน
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

def calculate_properties(props):
    # คำนวณ Properties พื้นฐานเพื่อแสดงในตาราง
    h, b, tw, tf = props['h']/10, props['b']/10, props['tw']/10, props['tf']/10 # cm
    
    # Area (cm2)
    A = (2 * b * tf) + ((h - 2*tf) * tw)
    
    # Inertia Ix (cm4)
    outer_I = (b * h**3) / 12
    inner_w = b - tw
    inner_h = h - (2*tf)
    inner_I = (inner_w * inner_h**3) / 12
    Ix = outer_I - inner_I
    
    # Modulus Zx (cm3)
    Zx = Ix / (h/2) # Elastic Modulus (Sx) actually, but often used loosely
    
    # Plastic Modulus (approx) for strength calc
    Zx_plastic = (b*tf*(h-tf)) + (tw*(h-2*tf)**2/4)

    return {
        "h (mm)": props['h'],
        "b (mm)": props['b'],
        "tw (mm)": props['tw'],
        "tf (mm)": props['tf'],
        "Area (cm2)": round(A, 2),
        "Ix (cm4)": round(Ix, 0),
        "Zx (cm3)": round(Zx_plastic, 0), # Use Plastic Zx for Capacity
        "Sx (cm3)": round(Zx, 0) # Elastic Sx
    }

def calculate_connection(props, load_percent, bolt_dia, span_factor, case_name):
    # ดึงค่า Properties มาใช้คำนวณ
    calc_props = calculate_properties(props)
    h, tw, fy, fu = props['h'], props['tw'], props['Fy'], props['Fu']
    
    Aw_cm2 = (h/10)*(tw/10) 
    Vn_beam = 0.60 * fy * Aw_cm2
    V_target = (load_percent/100) * Vn_beam
    
    # Moment
    Zx = calc_props['Zx (cm3)']
    Mn_beam = fy * Zx
    phiMn = 0.90 * Mn_beam
    L_crit_moment = (span_factor * (phiMn / V_target)) / 100.0 if V_target > 0 else 0
    
    # Deflection
    Ix = calc_props['Ix (cm4)']
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
        L_sq = (coeff * E * Ix) / Reaction
        L_crit_defl = math.sqrt(L_sq) / 100.0 
    
    L_safe = min(L_crit_moment, L_crit_defl) if L_crit_defl > 0 else L_crit_moment
    
    # Bolt Calc
    DB_mm = float(bolt_dia)
    Ab_cm2 = 3.1416 * (DB_mm/10)**2 / 4
    Fnv = 3300
    Rn_shear = 0.75 * Fnv * Ab_cm2 
    
    plate_t_mm = 10.0
    Le_cm = 3.5
    hole_dia_mm = DB_mm + 2
    Lc_cm = Le_cm - (hole_dia_mm/10)/2
    Rn_pl = 0.75 * min(1.2 * Lc_cm * (plate_t_mm/10) * 4050, 2.4 * (DB_mm/10) * (plate_t_mm/10) * 4050)
    Rn_web = 0.75 * min(1.2 * Lc_cm * (tw/10) * fu, 2.4 * (DB_mm/10) * (tw/10) * fu)
    
    phiRn_bolt = min(Rn_shear, Rn_pl, Rn_web)
    
    control_mode = "Bolt Shear"
    if Rn_pl < Rn_shear and Rn_pl < Rn_web: control_mode = "Plate Bearing"
    if Rn_web < Rn_shear and Rn_web < Rn_pl: control_mode = "Web Bearing"
    
    if phiRn_bolt > 0:
        n_req = V_target / phiRn_bolt
        n_bolts = max(2, math.ceil(n_req))
    else:
        n_bolts = 99
        
    spacing = 7.0
    L_plate = (2*Le_cm) + ((n_bolts-1)*spacing)
    
    return {
        "Section": props['name'], "h": h, "Vn_beam": Vn_beam, "V_target": V_target, 
        "L_crit_moment": L_crit_moment, "L_crit_defl": L_crit_defl, "L_safe": L_safe,
        "DB": DB_mm, "Rn_shear": Rn_shear, "Rn_pl": Rn_pl, "Rn_web": Rn_web,
        "phiRn_bolt": phiRn_bolt, "Bolt Qty": n_bolts, "Control By": control_mode,
        "Plate Len": L_plate, "Le": Le_cm, "S": spacing,
        "Props": calc_props # ส่ง Properties กลับไปด้วย
    }

# =========================================================
# 🎨 3. DRAWING LOGIC
# =========================================================
def draw_connection_sketch(h_beam, n_bolts, bolt_dia, plate_len_mm, le_cm, spacing_cm):
    fig, ax = plt.subplots(figsize=(4, 6)) # ปรับขนาดรูปให้พอดี
    COLOR_OBJ = '#2C3E50' 
    
    web_w_draw = 200 
    h_draw_area = h_beam + 120
    plate_w = 100
    plate_x = (web_w_draw - plate_w) / 2
    plate_y_start = (h_beam - plate_len_mm) / 2 + 60
    
    ax.add_patch(patches.Rectangle((0, 0), web_w_draw, h_draw_area, facecolor='#ECF0F1', zorder=1))
    ax.add_patch(patches.Rectangle((plate_x, plate_y_start), plate_w, plate_len_mm, linewidth=2, edgecolor=COLOR_OBJ, facecolor='#D6EAF8', zorder=2))
    
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
    return fig

# =========================================================
# 🖥️ 4. APP UI (FIXED ERROR & ADDED TABLE)
# =========================================================
# แก้ไขบรรทัดนี้: รับ argument *args, **kwargs เพื่อป้องกัน Error เวลาถูกเรียกจาก app.py
def render_report_tab(beam_data=None, conn_data=None, *args, **kwargs):
    st.markdown("### 🖨️ Structural Calculation Workbench")
    
    # 1. Controls
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1.5])
        all_sections = get_standard_sections()
        with c1: selected_sec_name = st.selectbox("Section", [s['name'] for s in all_sections], index=10)
        with c2: load_pct = st.number_input("Load % (of Vn)", 10, 100, 75)
        with c3: bolt_dia = st.selectbox("Bolt M", [12, 16, 20, 24], index=2)
        with c4: load_case = st.selectbox("Case", ["Simple Beam (Uniform Load)", "Simple Beam (Point Load @Center)", "Cantilever (Uniform Load)", "Cantilever (Point Load @Tip)"])
            
    # Calculate
    selected_props = next(s for s in all_sections if s['name'] == selected_sec_name)
    factor = get_load_case_factor(load_case)
    res = calculate_connection(selected_props, load_pct, bolt_dia, factor, load_case)
    
    st.divider()

    # =================================================
    # 🆕 TABLE SECTION: ตารางคุณสมบัติหน้าตัด (Requested)
    # =================================================
    st.markdown("#### 📐 Section Properties (คุณสมบัติหน้าตัด)")
    
    # สร้าง DataFrame สำหรับแสดงผลตาราง
    prop_data = res['Props']
    df_prop = pd.DataFrame([prop_data])
    
    # จัดรูปแบบตารางให้สวยงาม
    st.dataframe(
        df_prop,
        column_config={
            "h (mm)": st.column_config.NumberColumn("Depth (h)", format="%d mm"),
            "b (mm)": st.column_config.NumberColumn("Width (b)", format="%d mm"),
            "tw (mm)": st.column_config.NumberColumn("Web (tw)", format="%.1f mm"),
            "tf (mm)": st.column_config.NumberColumn("Flange (tf)", format="%.1f mm"),
            "Area (cm2)": st.column_config.NumberColumn("Area", format="%.2f cm²"),
            "Ix (cm4)": st.column_config.NumberColumn("Inertia (Ix)", format="%.0f cm⁴"),
            "Zx (cm3)": st.column_config.NumberColumn("Plastic Modulus (Zx)", format="%.0f cm³"),
            "Sx (cm3)": st.column_config.NumberColumn("Elastic Modulus (Sx)", format="%.0f cm³"),
        },
        hide_index=True,
        use_container_width=True
    )
    
    st.divider()

    # --- CALCULATION RESULTS ---
    col_cal, col_draw = st.columns([1.5, 1]) 
    with col_cal:
        st.subheader("📝 Engineering Report")
        with st.container(height=400, border=True):
            
            # Safe Span Result
            st.markdown(f"**1. Recommended Span (Safe Zone)**")
            st.info(f"👉 **Max Safe Length: {res['L_safe']:.2f} m**")
            st.caption(f"Controlled by: {'Moment' if res['L_crit_moment'] < res['L_crit_defl'] else 'Deflection'}")
            
            st.markdown("---")
            
            # Connection Check
            st.markdown(f"**2. Connection Check (Shear Only)**")
            
            # Mini Table for Connection
            conn_df = pd.DataFrame({
                "Parameter": ["Beam Shear Capacity (Vn)", f"Load Target ({load_pct}%)", "Bolt Capacity (per bolt)", "Bolts Required"],
                "Value": [f"{res['Vn_beam']:,.0f} kg", f"{res['V_target']:,.0f} kg", f"{res['phiRn_bolt']:,.0f} kg", f"{res['Bolt Qty']} pcs"]
            })
            st.table(conn_df)

    with col_draw:
        st.markdown("**Shop Drawing**")
        fig = draw_connection_sketch(res['h'], res['Bolt Qty'], float(bolt_dia), res['Plate Len']*10, res['Le'], res['S'])
        st.pyplot(fig)

    st.divider()

    # --- GRAPH ---
    st.subheader("📊 Structural Limit States Diagram")
    
    names, moments, defls, shears = [], [], [], []
    
    for sec in all_sections:
        r = calculate_connection(sec, load_pct, bolt_dia, factor, load_case)
        names.append(sec['name'].replace("H-", "")) 
        moments.append(r['L_crit_moment'])
        defls.append(r['L_crit_defl'])
        shears.append(r['Vn_beam']) 

    fig2, ax1 = plt.subplots(figsize=(10, 5))
    x = range(len(names))
    
    # Left Axis: Span
    ax1.set_ylabel('Span (m)', color='#27AE60', fontweight='bold')
    l1 = ax1.plot(x, moments, 'r--o', markersize=3, label='Moment Limit')
    l2 = ax1.plot(x, defls, 'b-', label='Deflection Limit')
    
    # Green Zone (Moment & Defl Only)
    min_vals = np.minimum(moments, defls)
    ax1.fill_between(x, 0, min_vals, color='#2ECC71', alpha=0.3, label='Safe Zone')
    
    # Right Axis: Shear
    ax2 = ax1.twinx()
    ax2.set_ylabel('Shear Capacity (kg)', color='purple', fontweight='bold')
    l3 = ax2.plot(x, shears, color='purple', linestyle=':', label='Shear Capacity Check')

    # Highlight
    idx = [s['name'] for s in all_sections].index(selected_sec_name)
    ax1.axvline(x=idx, color='orange', linewidth=2)
    ax1.plot(idx, res['L_safe'], 'g*', markersize=15)

    lns = l1 + l2 + [patches.Patch(color='#2ECC71', alpha=0.3, label='Safe Zone')] + l3
    ax1.legend(lns, [l.get_label() for l in lns], loc='upper left')

    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=90, fontsize=8)
    ax1.grid(True, linestyle=':', alpha=0.5)
    
    st.pyplot(fig2)

if __name__ == "__main__":
    st.set_page_config(page_title="Structural Workbench", layout="wide")
    render_report_tab()
