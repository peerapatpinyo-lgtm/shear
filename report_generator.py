# report_generator.py
# Version: 52.1 (Fix Argument Error + Auto-Link Analytics)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math

# =========================================================
# 🏗️ 1. DATABASE & PROPERTIES
# =========================================================
def get_standard_sections():
    return [
        {"name": "H-100x50x5x7",    "h": 100, "b": 50,  "tw": 5,  "tf": 7,  "Fy": 2500, "Fu": 4100},
        {"name": "H-100x100x6x8",   "h": 100, "b": 100, "tw": 6,  "tf": 8,  "Fy": 2500, "Fu": 4100},
        {"name": "H-125x60x6x8",    "h": 125, "b": 60,  "tw": 6,  "tf": 8,  "Fy": 2500, "Fu": 4100},
        {"name": "H-125x125x6.5x9", "h": 125, "b": 125, "tw": 6.5,"tf": 9,  "Fy": 2500, "Fu": 4100},
        {"name": "H-150x75x5x7",    "h": 150, "b": 75,  "tw": 5,  "tf": 7,  "Fy": 2500, "Fu": 4100},
        {"name": "H-150x150x7x10",  "h": 150, "b": 150, "tw": 7,  "tf": 10, "Fy": 2500, "Fu": 4100},
        {"name": "H-175x90x5x8",    "h": 175, "b": 90,  "tw": 5,  "tf": 8,  "Fy": 2500, "Fu": 4100},
        {"name": "H-175x175x7.5x11","h": 175, "b": 175, "tw": 7.5,"tf": 11, "Fy": 2500, "Fu": 4100},
        {"name": "H-200x100x5.5x8", "h": 200, "b": 100, "tw": 5.5,"tf": 8,  "Fy": 2500, "Fu": 4100},
        {"name": "H-200x200x8x12",  "h": 200, "b": 200, "tw": 8,  "tf": 12, "Fy": 2500, "Fu": 4100},
        {"name": "H-250x125x6x9",   "h": 250, "b": 125, "tw": 6,  "tf": 9,  "Fy": 2500, "Fu": 4100},
        {"name": "H-250x250x9x14",  "h": 250, "b": 250, "tw": 9,  "tf": 14, "Fy": 2500, "Fu": 4100},
        {"name": "H-300x150x6.5x9", "h": 300, "b": 150, "tw": 6.5,"tf": 9,  "Fy": 2500, "Fu": 4100},
        {"name": "H-300x300x10x15", "h": 300, "b": 300, "tw": 10, "tf": 15, "Fy": 2500, "Fu": 4100},
        {"name": "H-350x175x7x11",  "h": 350, "b": 175, "tw": 7,  "tf": 11, "Fy": 2500, "Fu": 4100},
        {"name": "H-350x350x12x19", "h": 350, "b": 350, "tw": 12, "tf": 19, "Fy": 2500, "Fu": 4100},
        {"name": "H-400x200x8x13",  "h": 400, "b": 200, "tw": 8,  "tf": 13, "Fy": 2500, "Fu": 4100},
        {"name": "H-400x400x13x21", "h": 400, "b": 400, "tw": 13, "tf": 21, "Fy": 2500, "Fu": 4100},
        {"name": "H-450x200x9x14",  "h": 450, "b": 200, "tw": 9,  "tf": 14, "Fy": 2500, "Fu": 4100},
        {"name": "H-500x200x10x16", "h": 500, "b": 200, "tw": 10, "tf": 16, "Fy": 2500, "Fu": 4100},
        {"name": "H-600x200x11x17", "h": 600, "b": 200, "tw": 11, "tf": 17, "Fy": 2500, "Fu": 4100},
        {"name": "H-700x300x13x24", "h": 700, "b": 300, "tw": 13, "tf": 24, "Fy": 2500, "Fu": 4100},
        {"name": "H-800x300x14x26", "h": 800, "b": 300, "tw": 14, "tf": 26, "Fy": 2500, "Fu": 4100},
        {"name": "H-900x300x16x28", "h": 900, "b": 300, "tw": 16, "tf": 28, "Fy": 2500, "Fu": 4100},
    ]

def calculate_full_properties(props):
    h, b, tw, tf = props['h']/10, props['b']/10, props['tw']/10, props['tf']/10 # cm
    A = (2 * b * tf) + ((h - 2*tf) * tw)
    outer_I = (b * h**3) / 12
    inner_w = b - tw
    inner_h = h - (2*tf)
    inner_I = (inner_w * inner_h**3) / 12
    Ix = outer_I - inner_I
    Sx = Ix / (h/2) 
    Zx = (b*tf*(h-tf)) + (tw*(h-2*tf)**2/4) 
    return {
        "Name": props['name'],
        "h": props['h'], "b": props['b'], "tw": props['tw'], "tf": props['tf'],
        "Area (cm2)": round(A, 2), "Ix (cm4)": round(Ix, 0), "Zx (cm3)": round(Zx, 0)
    }

def get_full_database_df():
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
    full_props = calculate_full_properties(props) 
    h, tw, fy, fu = props['h'], props['tw'], props['Fy'], props['Fu']
    
    # 1. Shear
    Vn_beam = 0.60 * fy * (h/10)*(tw/10)
    V_target = (load_percent/100) * Vn_beam
    
    # 2. Moment Limit
    Mn_beam = fy * full_props['Zx (cm3)']
    phiMn = 0.90 * Mn_beam
    L_crit_moment = (span_factor * (phiMn / V_target)) / 100.0 if V_target > 0 else 0
    
    # 3. Deflection Limit
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
    
    # 4. Bolt Capacity
    DB_mm = float(bolt_dia)
    Ab_cm2 = 3.1416 * (DB_mm/10)**2 / 4
    Rn_shear = 0.75 * 3300 * Ab_cm2 
    plate_t_mm = 10.0; Le_cm = 3.5; Lc_cm = Le_cm - ((DB_mm+2)/10)/2
    Rn_pl = 0.75 * min(1.2 * Lc_cm * (plate_t_mm/10) * 4050, 2.4 * (DB_mm/10) * (plate_t_mm/10) * 4050)
    Rn_web = 0.75 * min(1.2 * Lc_cm * (tw/10) * fu, 2.4 * (DB_mm/10) * (tw/10) * fu)
    phiRn_bolt = min(Rn_shear, Rn_pl, Rn_web)
    
    n_bolts = max(2, math.ceil(V_target / phiRn_bolt)) if phiRn_bolt > 0 else 99
    spacing = 7.0
    L_plate = (2*Le_cm) + ((n_bolts-1)*spacing)
    
    return {
        "Section": props['name'], "h": h, "b": props['b'], "tw": tw, "tf": props['tf'], 
        "Vn_beam": Vn_beam, "V_target": V_target, 
        "L_crit_moment": L_crit_moment, "L_crit_defl": L_crit_defl, "L_safe": L_safe,
        "DB": DB_mm, "phiRn_bolt": phiRn_bolt, "Bolt Qty": n_bolts,
        "Plate Len": L_plate, "Le": Le_cm, "S": spacing
    }

# =========================================================
# 🎨 3. DRAWING LOGIC (Single Beam)
# =========================================================
def draw_professional_shop_drawing(res):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 7), gridspec_kw={'width_ratios': [2, 1]})
    
    # Styles
    COLOR_OBJ = '#2C3E50'; COLOR_DIM = '#E74C3C'; COLOR_CENTER = '#95A5A6'
    LW_OBJ = 1.5; LW_DIM = 0.8
    
    # --- VIEW 1: ELEVATION ---
    h, tw, L_plate_mm = res['h'], res['tw'], res['Plate Len']*10
    web_w_draw = 220; h_draw_area = h + 150
    plate_w = 100; plate_x = (web_w_draw - plate_w) / 2
    plate_y_start = (h - L_plate_mm) / 2 + 75
    
    ax1.add_patch(patches.Rectangle((0, 0), web_w_draw, h_draw_area, facecolor='#ECF0F1', zorder=0))
    ax1.add_patch(patches.Rectangle((plate_x, plate_y_start), plate_w, L_plate_mm, linewidth=LW_OBJ, edgecolor=COLOR_OBJ, facecolor='#D6EAF8', zorder=2))
    
    bolt_x = plate_x + plate_w/2
    bolt_y_top = plate_y_start + L_plate_mm - (res['Le']*10)
    bolt_ys = []
    curr_y = bolt_y_top
    for i in range(res['Bolt Qty']):
        bolt_ys.append(curr_y)
        ax1.add_patch(patches.Circle((bolt_x, curr_y), (res['DB']+2)/2, edgecolor=COLOR_OBJ, facecolor='white', linewidth=1.2, zorder=3))
        ax1.hlines(curr_y, bolt_x-10, bolt_x+10, colors=COLOR_CENTER, linestyles='-.', linewidth=0.5)
        curr_y -= (res['S']*10)
    ax1.vlines(bolt_x, plate_y_start-20, plate_y_start+L_plate_mm+20, colors=COLOR_CENTER, linestyles='-.', linewidth=0.5)

    def draw_dim_arrow(ax, y_start, y_end, x_pos, text_val, label_prefix="", orient='v'):
        if orient == 'v':
            ax.annotate(text='', xy=(x_pos, y_start), xytext=(x_pos, y_end), arrowprops=dict(arrowstyle='<|-|>', color=COLOR_DIM, lw=LW_DIM))
            mid_y = (y_start + y_end) / 2
            txt = f"{label_prefix} {int(text_val)}" if label_prefix else f"{int(text_val)}"
            ax.text(x_pos + 5, mid_y, txt, color=COLOR_DIM, fontsize=8, va='center')
            ax.plot([plate_x+plate_w, x_pos], [y_start, y_start], color=COLOR_DIM, lw=0.5, ls=':')
            ax.plot([plate_x+plate_w, x_pos], [y_end, y_end], color=COLOR_DIM, lw=0.5, ls=':')
        else:
            ax.annotate(text='', xy=(y_start, x_pos), xytext=(y_end, x_pos), arrowprops=dict(arrowstyle='<|-|>', color=COLOR_DIM, lw=LW_DIM))
            mid_x = (y_start + y_end) / 2
            txt = f"{int(text_val)}"
            ax.text(mid_x, x_pos - 8, txt, color=COLOR_DIM, fontsize=8, ha='center', va='top')
            ax.plot([y_start, y_start], [plate_y_start, x_pos], color=COLOR_DIM, lw=0.5, ls=':')
            ax.plot([y_end, y_end], [plate_y_start, x_pos], color=COLOR_DIM, lw=0.5, ls=':')

    dim_x_offset = plate_x + plate_w + 15
    draw_dim_arrow(ax1, plate_y_start + L_plate_mm, bolt_ys[0], dim_x_offset, res['Le']*10, "Le", 'v')
    for i in range(len(bolt_ys)-1):
        draw_dim_arrow(ax1, bolt_ys[i], bolt_ys[i+1], dim_x_offset, res['S']*10, "S", 'v')
    draw_dim_arrow(ax1, bolt_ys[-1], plate_y_start, dim_x_offset, res['Le']*10, "Le", 'v')
    
    dim_y_horz = plate_y_start - 30
    draw_dim_arrow(ax1, plate_x, bolt_x, dim_y_horz, plate_w/2, "", 'h')
    draw_dim_arrow(ax1, bolt_x, plate_x+plate_w, dim_y_horz, plate_w/2, "", 'h')

    ax1.set_xlim(0, web_w_draw + 60); ax1.set_ylim(0, h_draw_area); ax1.axis('off')
    ax1.set_title("ELEVATION", fontweight='bold', color=COLOR_OBJ)

    # --- VIEW 2: SECTION ---
    b, tf = res['b'], res['tf']; cx = 100 
    ax2.add_patch(patches.Rectangle((cx - b/2, h_draw_area/2 + h/2 - tf), b, tf, facecolor='#7F8C8D', edgecolor='black')) 
    ax2.add_patch(patches.Rectangle((cx - b/2, h_draw_area/2 - h/2), b, tf, facecolor='#7F8C8D', edgecolor='black')) 
    ax2.add_patch(patches.Rectangle((cx - tw/2, h_draw_area/2 - h/2 + tf), tw, h - 2*tf, facecolor='#95A5A6', edgecolor='black'))
    pl_thk = 10
    ax2.add_patch(patches.Rectangle((cx + tw/2, h_draw_area/2 - L_plate_mm/2), pl_thk, L_plate_mm, facecolor='#3498DB', edgecolor='black'))
    ax2.plot([cx-20, cx+50], [h_draw_area/2, h_draw_area/2], 'k-.', linewidth=0.5)
    ax2.set_xlim(0, 200); ax2.set_ylim(0, h_draw_area); ax2.axis('off')
    ax2.set_title("SECTION", fontweight='bold', color=COLOR_OBJ)

    plt.suptitle(f"SHOP DRAWING: {res['Section']} (PL-100x{int(L_plate_mm)}x10mm)", fontsize=12, fontweight='bold', color=COLOR_OBJ)
    return fig

# =========================================================
# 🖥️ 4. APP RENDERER
# =========================================================
def render_report_tab(beam_data=None, conn_data=None):
    """
    ฟังก์ชันหลักที่ App.py เรียกใช้
    รับ args: beam_data, conn_data (เพื่อ Compatibility ไม่ให้ Error แต่ไม่ได้ใช้ค่าข้างใน)
    """
    st.markdown("### 🏗️ Structural Calculation Workbench (Split Modules)")
    
    with st.expander("📂 ดูตารางเหล็กทั้งหมด", expanded=False):
        st.dataframe(get_full_database_df(), use_container_width=True, hide_index=True)

    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1.5])
        all_sections = get_standard_sections()
        with c1: selected_sec_name = st.selectbox("เลือกหน้าตัด", [s['name'] for s in all_sections], index=10)
        with c2: load_pct = st.number_input("Load %", 10, 100, 75)
        with c3: bolt_dia = st.selectbox("Bolt Size", [12, 16, 20, 24], index=2)
        with c4: load_case = st.selectbox("Case", ["Simple Beam (Uniform Load)", "Simple Beam (Point Load @Center)", "Cantilever (Uniform Load)", "Cantilever (Point Load @Tip)"])
            
    selected_props = next(s for s in all_sections if s['name'] == selected_sec_name)
    factor = get_load_case_factor(load_case)
    res = calculate_connection(selected_props, load_pct, bolt_dia, factor, load_case)
    
    st.divider()
    c_left, c_right = st.columns([1, 1.5])
    with c_left:
        st.subheader("📝 Summary Result")
        st.success(f"✅ **Safe Span Limit: {res['L_safe']:.2f} m**")
        st.caption(f"Controlled by: {'Moment' if res['L_crit_moment'] < res['L_crit_defl'] else 'Deflection'}")
        st.markdown(f"- Shear Load: `{res['V_target']:,.0f} kg`")
        st.markdown(f"- Bolts Req: `{res['Bolt Qty']} pcs` (M{int(res['DB'])})")
    with c_right:
        st.pyplot(draw_professional_shop_drawing(res))
    
    # 🔗 AUTO LINK: เรียก Analytics ให้ทำงานต่อเลย
    st.divider()
    try:
        import report_analytics
        report_analytics.render_analytics_section(load_pct, bolt_dia, load_case, factor)
    except ImportError:
        st.warning("⚠️ ไม่พบไฟล์ report_analytics.py กรุณาสร้างไฟล์เพื่อดู Analytics")
