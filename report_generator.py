# report_generator.py
# Version: 23.0 (Interactive & Visualization)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime
import math

# =========================================================
# 🏗️ 1. MOCK DATABASE
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
# 🎨 2. DRAWING FUNCTION (Matplotlib)
# =========================================================
def draw_connection_sketch(h_beam, n_bolts, bolt_dia, plate_len, le, spacing):
    """
    สร้างรูป Sketch 2D ของ Shear Plate
    """
    fig, ax = plt.subplots(figsize=(4, 6))
    
    # 1. Draw Beam Web (Background)
    # สมมติวาดแค่ส่วน web ที่เกี่ยวข้อง
    web_width = 150 # mm (width visible in plot)
    ax.add_patch(patches.Rectangle((0, -50), web_width, h_beam+100, linewidth=0, edgecolor='none', facecolor='#f0f2f6', label='Beam Web'))
    
    # 2. Draw Shear Plate
    plate_width = 100 # mm (Standard width for single row)
    plate_x = (web_width - plate_width) / 2
    plate_y_start = (h_beam - plate_len) / 2 + 50 # Center vertically relative to beam
    
    rect = patches.Rectangle((plate_x, plate_y_start), plate_width, plate_len, linewidth=2, edgecolor='#1f77b4', facecolor='#aec7e8', alpha=0.8, label='Shear Plate')
    ax.add_patch(rect)
    
    # 3. Draw Bolts
    hole_dia = bolt_dia + 2
    bolt_x = plate_x + (plate_width / 2) # Center of plate
    
    # Top bolt y position (relative to plate bottom)
    # y = plate_y_start + plate_len - Le
    current_y = plate_y_start + plate_len - (le*10) # Convert cm to mm
    
    for i in range(n_bolts):
        circle = patches.Circle((bolt_x, current_y), radius=hole_dia/2, edgecolor='black', facecolor='white', linewidth=1.5)
        ax.add_patch(circle)
        # Crosshair center
        ax.plot([bolt_x-5, bolt_x+5], [current_y, current_y], 'k-', linewidth=0.5)
        ax.plot([bolt_x, bolt_x], [current_y-5, current_y+5], 'k-', linewidth=0.5)
        
        current_y -= (spacing * 10) # Move down by spacing
        
    # 4. Annotation
    ax.text(bolt_x + 30, plate_y_start + plate_len/2, f"{n_bolts}-M{int(bolt_dia)}", fontsize=10, color='blue', verticalalignment='center')
    ax.text(plate_x - 10, plate_y_start + plate_len/2, f"PL-{int(plate_len)}mm", fontsize=10, rotation=90, verticalalignment='center', horizontalalignment='right')

    # Settings
    ax.set_xlim(0, web_width)
    ax.set_ylim(0, h_beam + 100)
    ax.set_aspect('equal')
    ax.axis('off') # Hide axis
    ax.set_title(f"Connection Sketch (N.T.S)", fontsize=10)
    
    return fig

# =========================================================
# 🧠 3. CALCULATION LOGIC (Updated with Parameters)
# =========================================================
def calculate_zx(h, b, tw, tf):
    h_cm, b_cm = h/10.0, b/10.0
    tw_cm, tf_cm = tw/10.0, tf/10.0
    return (b_cm * tf_cm * (h_cm - tf_cm)) + (tw_cm * (h_cm - 2*tf_cm)**2 / 4.0)

def calculate_connection(props, load_percent=75, selected_bolt_dia=20):
    # Unpack
    h, tw, fy, fu = props['h'], props['tw'], props['Fy'], props['Fu']
    b, tf = props.get('b', h/2.0), props.get('tf', tw*1.5)
    
    # User Parameters
    DB = float(selected_bolt_dia)
    load_ratio = load_percent / 100.0
    plate_t_mm = 10.0
    
    # Shear Cap
    Aw = (h/10.0) * (tw/10.0)
    V_cap_max = 1.00 * (0.60 * fy * Aw)
    V_u = load_ratio * V_cap_max
    
    # Moment Cap & Critical Span
    Zx = calculate_zx(h, b, tw, tf)
    phiMn = 0.90 * (fy * Zx)
    L_critical_m = ((4 * phiMn) / V_u) / 100.0 if V_u > 0 else 0
    
    # Bolt Design
    Ab = (math.pi * (DB/10.0)**2) / 4.0
    Rn_shear = 0.75 * 3300 * Ab
    
    Le = 3.5
    Lc = Le - ((DB+2)/10.0)/2.0
    t_pl, t_web = plate_t_mm/10.0, tw/10.0
    
    phiRn_pl = 0.75 * min(1.2*Lc*t_pl*4050, 2.4*(DB/10.0)*t_pl*4050)
    phiRn_web = 0.75 * min(1.2*Lc*t_web*fu, 2.4*(DB/10.0)*t_web*fu)
    
    cap_per_bolt = min(Rn_shear, phiRn_pl, phiRn_web)
    n_bolts = max(2, math.ceil(V_u / cap_per_bolt)) if cap_per_bolt > 0 else 99
    
    # Plate Geometry
    spacing = 7.0 # cm
    L_plate_cm = (2*Le) + ((n_bolts-1)*spacing)

    # Utilization % (เพื่อดูความคุ้มค่า)
    actual_capacity = n_bolts * cap_per_bolt
    utilization = (V_u / actual_capacity) * 100 if actual_capacity > 0 else 0

    return {
        "Steel Section": props['name'],
        "h": h,
        "Design Vu (Ton)": V_u/1000.0,
        "Max Span (m)": L_critical_m,
        "Bolt Qty": n_bolts,
        "Bolt Spec": f"M{int(DB)}",
        "Control By": "Web Bear" if phiRn_web < phiRn_pl else "Bolt/Plt",
        "Utilization": utilization,
        "Plate Len (cm)": L_plate_cm,
        "Spacing (cm)": spacing,
        "Le (cm)": Le
    }

# =========================================================
# 🖥️ 4. RENDER FUNCTION (Interactive UI)
# =========================================================
def render_report_tab(beam_data, conn_data):
    
    st.markdown("### 🖨️ Interactive Connection Design")

    # --- 🎛️ CONTROLS SECTION (NEW!) ---
    with st.container(border=True):
        st.markdown("**⚙️ Design Parameters (ปรับค่าการออกแบบ)**")
        col_param1, col_param2 = st.columns(2)
        
        with col_param1:
            load_percent = st.slider("Target Capacity (%)", min_value=10, max_value=100, value=75, step=5, help="ออกแบบที่กี่ % ของกำลังคาน")
        
        with col_param2:
            bolt_dia = st.selectbox("Bolt Size (mm)", [12, 16, 20, 22, 24], index=2, help="เลือกขนาดน๊อต A325")

    st.divider()

    # --- TAB A: SINGLE BEAM + VISUALIZATION ---
    with st.expander("📌 Single Beam Analysis & Sketch", expanded=True):
        if beam_data:
            try:
                # Calculate
                res = calculate_connection({
                    "name": beam_data.get('sec_name', 'Custom'),
                    "h": float(beam_data.get('h', 400)),
                    "b": float(beam_data.get('h', 400))/2,
                    "tw": float(beam_data.get('tw', 8)),
                    "tf": float(beam_data.get('tw', 8))*1.5,
                    "Fy": float(beam_data.get('Fy', 2500)),
                    "Fu": float(beam_data.get('Fu', 4100))
                }, load_percent, bolt_dia)
                
                # Layout: Left = Data, Right = Sketch
                col_left, col_right = st.columns([1.5, 1])
                
                with col_left:
                    st.subheader(f"Results: {res['Steel Section']}")
                    c1, c2 = st.columns(2)
                    c1.metric("Design Load", f"{res['Design Vu (Ton)']:.1f} Ton", f"@{load_percent}% Cap")
                    c2.metric("Bolts Required", f"{res['Bolt Qty']} pcs", f"{res['Bolt Spec']} (A325)")
                    
                    st.metric("Critical Span", f"{res['Max Span (m)']:.2f} m", "Max Length")
                    
                    # Utilization Bar (NEW!)
                    st.write("Efficiency (ความคุ้มค่า):")
                    st.progress(res['Utilization'] / 100.0, text=f"{res['Utilization']:.1f}% Utilized")
                    if res['Utilization'] < 50:
                        st.caption("⚠️ Low efficiency (Over designed). Try reducing bolt size.")
                
                with col_right:
                    # Draw Sketch (NEW!)
                    fig = draw_connection_sketch(
                        res['h'], res['Bolt Qty'], bolt_dia, res['Plate Len (cm)']*10, res['Le (cm)'], res['Spacing (cm)']
                    )
                    st.pyplot(fig)
                    
            except Exception as e:
                st.error(f"Error: {e}")
        else:
             st.warning("Please select a beam first.")

    # --- TAB B: BATCH ANALYSIS ---
    st.subheader("🚀 Batch Analysis Table")
    if st.button(f"⚡ Generate Table (Load={load_percent}%, Bolt=M{bolt_dia})", type="primary"):
        all_beams = get_standard_sections()
        results = []
        progress_bar = st.progress(0)
        
        for i, beam in enumerate(all_beams):
            progress_bar.progress((i + 1) / len(all_beams))
            results.append(calculate_connection(beam, load_percent, bolt_dia))
            
        df_res = pd.DataFrame(results)
        
        st.dataframe(
            df_res,
            use_container_width=True,
            column_config={
                "Steel Section": st.column_config.TextColumn("Section"),
                "Design Vu (Ton)": st.column_config.NumberColumn("Load (Ton)", format="%.2f"),
                "Bolt Qty": st.column_config.NumberColumn("Bolts", format="%d"),
                "Utilization": st.column_config.ProgressColumn("Efficiency", format="%.0f%%", min_value=0, max_value=100),
            },
            hide_index=True
        )
