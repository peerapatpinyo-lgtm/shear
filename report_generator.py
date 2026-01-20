# report_generator.py
# Version: 24.0 (Auto-Dimensioning Shop Drawing)
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
# 🎨 2. DRAWING FUNCTION (With Dimensions!)
# =========================================================
def draw_connection_sketch(h_beam, n_bolts, bolt_dia, plate_len_mm, le_cm, spacing_cm):
    """
    สร้างรูป Sketch 2D พร้อมเส้นบอกระยะ (Dimension Lines)
    """
    fig, ax = plt.subplots(figsize=(5, 7)) # ขยายความกว้างนิดนึงเผื่อ dimension
    
    # --- 1. Geometry Setup ---
    web_width = 180 
    h_draw_area = h_beam + 100
    
    plate_width = 100
    plate_x = (web_width - plate_width) / 2
    plate_y_start = (h_beam - plate_len_mm) / 2 + 50
    
    # Draw Beam Web
    ax.add_patch(patches.Rectangle((0, -50), web_width, h_draw_area, linewidth=0, facecolor='#f0f2f6', label='Beam Web'))
    
    # Draw Plate
    rect = patches.Rectangle((plate_x, plate_y_start), plate_width, plate_len_mm, linewidth=2, edgecolor='#1f77b4', facecolor='#aec7e8', alpha=0.9)
    ax.add_patch(rect)
    
    # --- 2. Bolts & Centers ---
    hole_dia = bolt_dia + 2
    bolt_x = plate_x + (plate_width / 2)
    
    # Calculate positions
    le_mm = le_cm * 10
    spacing_mm = spacing_cm * 10
    
    # Top bolt Y position
    top_bolt_y = plate_y_start + plate_len_mm - le_mm
    bolt_positions_y = []
    
    current_y = top_bolt_y
    for i in range(n_bolts):
        bolt_positions_y.append(current_y)
        # Bolt Circle
        circle = patches.Circle((bolt_x, current_y), radius=hole_dia/2, edgecolor='black', facecolor='white', linewidth=1.5)
        ax.add_patch(circle)
        # Crosshair
        ax.plot([bolt_x-5, bolt_x+5], [current_y, current_y], 'k-', linewidth=0.5)
        ax.plot([bolt_x, bolt_x], [current_y-5, current_y+5], 'k-', linewidth=0.5)
        
        current_y -= spacing_mm

    # --- 3. DIMENSION LINES (The Logic) 📏 ---
    dim_x_offset = plate_x + plate_width + 15 # ระยะห่างเส้น Dimension จากขอบเพลท
    
    def draw_dim_line(y1, y2, x_pos, text):
        # เส้นตั้ง
        ax.plot([x_pos, x_pos], [y1, y2], color='red', linewidth=1)
        # ขีดบน-ล่าง (Tick marks)
        tick_w = 3
        ax.plot([x_pos-tick_w, x_pos+tick_w], [y1, y1], color='red', linewidth=1)
        ax.plot([x_pos-tick_w, x_pos+tick_w], [y2, y2], color='red', linewidth=1)
        # เส้นโยงจากชิ้นงาน (Extension lines) - optional
        ax.plot([plate_x + plate_width, x_pos], [y1, y1], color='red', linestyle=':', linewidth=0.5)
        ax.plot([plate_x + plate_width, x_pos], [y2, y2], color='red', linestyle=':', linewidth=0.5)
        
        # ตัวหนังสือ (Text)
        mid_y = (y1 + y2) / 2
        ax.text(x_pos + 5, mid_y, text, color='red', fontsize=9, va='center')

    # 3.1 Top Edge Distance
    y_plate_top = plate_y_start + plate_len_mm
    draw_dim_line(y_plate_top, bolt_positions_y[0], dim_x_offset, f"{int(le_mm)}")
    
    # 3.2 Spacing (Loop)
    for i in range(len(bolt_positions_y)-1):
        y_curr = bolt_positions_y[i]
        y_next = bolt_positions_y[i+1]
        draw_dim_line(y_curr, y_next, dim_x_offset, f"{int(spacing_mm)}")
        
    # 3.3 Bottom Edge Distance
    y_plate_bot = plate_y_start
    draw_dim_line(bolt_positions_y[-1], y_plate_bot, dim_x_offset, f"{int(le_mm)}")
    
    # 3.4 Total Plate Height (Outer Line)
    outer_dim_x = dim_x_offset + 30
    ax.plot([outer_dim_x, outer_dim_x], [y_plate_bot, y_plate_top], color='blue', linewidth=1)
    # Ticks
    ax.plot([outer_dim_x-3, outer_dim_x+3], [y_plate_bot, y_plate_bot], color='blue', linewidth=1)
    ax.plot([outer_dim_x-3, outer_dim_x+3], [y_plate_top, y_plate_top], color='blue', linewidth=1)
    # Text
    ax.text(outer_dim_x + 5, (y_plate_bot + y_plate_top)/2, f"Total: {int(plate_len_mm)}", color='blue', fontsize=9, rotation=90, va='center')

    # --- 4. Settings ---
    ax.set_xlim(0, web_width + 80) # เผื่อที่ด้านขวาให้ Dimension
    ax.set_ylim(0, h_draw_area)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(f"Shop Drawing: {n_bolts}-M{int(bolt_dia)}", fontsize=11, fontweight='bold')
    
    return fig

# =========================================================
# 🧠 3. CALCULATION LOGIC
# =========================================================
def calculate_zx(h, b, tw, tf):
    h_cm, b_cm = h/10.0, b/10.0
    tw_cm, tf_cm = tw/10.0, tf/10.0
    return (b_cm * tf_cm * (h_cm - tf_cm)) + (tw_cm * (h_cm - 2*tf_cm)**2 / 4.0)

def calculate_connection(props, load_percent=75, selected_bolt_dia=20):
    # Unpack
    h, tw, fy, fu = props['h'], props['tw'], props['Fy'], props['Fu']
    b, tf = props.get('b', h/2.0), props.get('tf', tw*1.5)
    
    # Params
    DB = float(selected_bolt_dia)
    load_ratio = load_percent / 100.0
    plate_t_mm = 10.0
    
    # Shear Cap
    Aw = (h/10.0) * (tw/10.0)
    V_cap_max = 1.00 * (0.60 * fy * Aw)
    V_u = load_ratio * V_cap_max
    
    # Moment Cap
    Zx = calculate_zx(h, b, tw, tf)
    phiMn = 0.90 * (fy * Zx)
    L_critical_m = ((4 * phiMn) / V_u) / 100.0 if V_u > 0 else 0
    
    # Bolts
    Ab = (math.pi * (DB/10.0)**2) / 4.0
    Rn_shear = 0.75 * 3300 * Ab
    
    Le = 3.5 # cm
    Lc = Le - ((DB+2)/10.0)/2.0
    t_pl, t_web = plate_t_mm/10.0, tw/10.0
    
    phiRn_pl = 0.75 * min(1.2*Lc*t_pl*4050, 2.4*(DB/10.0)*t_pl*4050)
    phiRn_web = 0.75 * min(1.2*Lc*t_web*fu, 2.4*(DB/10.0)*t_web*fu)
    
    cap_per_bolt = min(Rn_shear, phiRn_pl, phiRn_web)
    n_bolts = max(2, math.ceil(V_u / cap_per_bolt)) if cap_per_bolt > 0 else 99
    
    # Plate Geometry
    spacing = 7.0 # cm
    L_plate_cm = (2*Le) + ((n_bolts-1)*spacing)
    
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
# 🖥️ 4. RENDER FUNCTION
# =========================================================
def render_report_tab(beam_data, conn_data):
    
    st.markdown("### 🖨️ Interactive Shop Drawing")

    # Controls
    with st.container(border=True):
        col_param1, col_param2 = st.columns(2)
        with col_param1:
            load_percent = st.slider("Target Capacity (%)", 10, 100, 75, 5)
        with col_param2:
            bolt_dia = st.selectbox("Bolt Size (mm)", [12, 16, 20, 22, 24], index=2)

    st.divider()

    # --- TAB A: SINGLE BEAM + DRAWING ---
    with st.expander("📌 Connection Details & Drawing", expanded=True):
        if beam_data:
            try:
                res = calculate_connection({
                    "name": beam_data.get('sec_name', 'Custom'),
                    "h": float(beam_data.get('h', 400)),
                    "b": float(beam_data.get('h', 400))/2,
                    "tw": float(beam_data.get('tw', 8)),
                    "tf": float(beam_data.get('tw', 8))*1.5,
                    "Fy": float(beam_data.get('Fy', 2500)),
                    "Fu": float(beam_data.get('Fu', 4100))
                }, load_percent, bolt_dia)
                
                # Layout
                col_left, col_right = st.columns([1.2, 1.5]) # ขยาย col_right ให้กว้างขึ้นเพื่อรูป
                
                with col_left:
                    st.subheader("Design Data")
                    st.write(f"**Section:** {res['Steel Section']}")
                    st.write(f"**Load:** {res['Design Vu (Ton)']:.2f} Ton")
                    st.write(f"**Bolts:** {res['Bolt Qty']} - {res['Bolt Spec']}")
                    st.write(f"**Plate:** 100x{int(res['Plate Len (cm)']*10)}x10 mm")
                    
                    st.metric("Critical Span", f"{res['Max Span (m)']:.2f} m")
                    
                    st.caption("Utilization:")
                    st.progress(res['Utilization'] / 100.0)
                
                with col_right:
                    # Draw with Dimensions!
                    fig = draw_connection_sketch(
                        res['h'], 
                        res['Bolt Qty'], 
                        bolt_dia, 
                        res['Plate Len (cm)']*10, # mm
                        res['Le (cm)'], 
                        res['Spacing (cm)']
                    )
                    st.pyplot(fig)
                    
            except Exception as e:
                st.error(f"Error: {e}")
        else:
             st.warning("Please select a beam first.")

    # --- TAB B: TABLE ---
    st.subheader("🚀 Batch Table")
    if st.button(f"⚡ Generate Table"):
        all_beams = get_standard_sections()
        results = [calculate_connection(b, load_percent, bolt_dia) for b in all_beams]
        df_res = pd.DataFrame(results)
        st.dataframe(df_res, use_container_width=True, hide_index=True)
