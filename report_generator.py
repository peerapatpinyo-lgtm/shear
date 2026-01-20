# report_generator.py
# Version: 25.0 (Multi-Load Case Support)
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
        {"name": "H-150x75x5x7",    "h": 150, "b": 75,  "tw": 5,  "tf": 7,  "Fy": 2500, "Fu": 4100},
        {"name": "H-200x100x5.5x8", "h": 200, "b": 100, "tw": 5.5,"tf": 8,  "Fy": 2500, "Fu": 4100},
        {"name": "H-250x125x6x9",    "h": 250, "b": 125, "tw": 6,  "tf": 9,  "Fy": 2500, "Fu": 4100},
        {"name": "H-300x150x6.5x9",  "h": 300, "b": 150, "tw": 6.5,"tf": 9,  "Fy": 2500, "Fu": 4100},
        {"name": "H-350x175x7x11",   "h": 350, "b": 175, "tw": 7,  "tf": 11, "Fy": 2500, "Fu": 4100},
        {"name": "H-400x200x8x13",   "h": 400, "b": 200, "tw": 8,  "tf": 13, "Fy": 2500, "Fu": 4100},
        {"name": "H-500x200x10x16",  "h": 500, "b": 200, "tw": 10, "tf": 16, "Fy": 2500, "Fu": 4100},
        {"name": "H-600x200x11x17",  "h": 600, "b": 200, "tw": 11, "tf": 17, "Fy": 2500, "Fu": 4100},
        {"name": "H-800x300x14x26",  "h": 800, "b": 300, "tw": 14, "tf": 26, "Fy": 2500, "Fu": 4100},
    ]

# =========================================================
# ⚙️ 2. LOAD CASE LOGIC (NEW!)
# =========================================================
def get_load_case_factor(case_name):
    """
    Return factor 'k' where L_critical = k * (M_cap / V_cap)
    """
    cases = {
        "Simple Beam (Uniform Load)": 4.0,   # M=VL/4
        "Simple Beam (Point Load @Center)": 2.0, # M=VL/2
        "Cantilever (Uniform Load)": 2.0,    # M=VL/2
        "Cantilever (Point Load @Tip)": 1.0  # M=VL
    }
    return cases.get(case_name, 4.0)

# =========================================================
# 🎨 3. DRAWING FUNCTION (With Dimensions)
# =========================================================
def draw_connection_sketch(h_beam, n_bolts, bolt_dia, plate_len_mm, le_cm, spacing_cm):
    fig, ax = plt.subplots(figsize=(4.5, 6.5))
    
    web_width = 160 
    h_draw = h_beam + 80
    
    # Beam
    ax.add_patch(patches.Rectangle((0, -40), web_width, h_draw, color='#f0f2f6'))
    
    # Plate
    plate_w = 90
    px = (web_width - plate_w)/2
    py = (h_beam - plate_len_mm)/2 + 40
    ax.add_patch(patches.Rectangle((px, py), plate_w, plate_len_mm, ec='#1f77b4', fc='#aec7e8', lw=2))
    
    # Bolts
    bx = px + plate_w/2
    by_top = py + plate_len_mm - (le_cm*10)
    
    curr_y = by_top
    bolt_ys = []
    for _ in range(n_bolts):
        bolt_ys.append(curr_y)
        ax.add_patch(patches.Circle((bx, curr_y), (bolt_dia+2)/2, ec='k', fc='w'))
        curr_y -= (spacing_cm*10)
        
    # --- Dimensions (Red) ---
    dx = px + plate_w + 15
    def dim(y1, y2, txt):
        ax.plot([dx, dx], [y1, y2], 'r-', lw=1)
        ax.plot([dx-3, dx+3], [y1, y1], 'r-', lw=1)
        ax.plot([dx-3, dx+3], [y2, y2], 'r-', lw=1)
        ax.text(dx+5, (y1+y2)/2, txt, color='r', fontsize=8, va='center')

    dim(py+plate_len_mm, bolt_ys[0], f"{int(le_cm*10)}") # Top Le
    for i in range(len(bolt_ys)-1):
        dim(bolt_ys[i], bolt_ys[i+1], f"{int(spacing_cm*10)}") # Spacing
    dim(bolt_ys[-1], py, f"{int(le_cm*10)}") # Bot Le
    
    # Total H (Blue)
    dx2 = dx + 25
    ax.plot([dx2, dx2], [py, py+plate_len_mm], 'b-', lw=1)
    ax.text(dx2+5, py+plate_len_mm/2, f"L={int(plate_len_mm)}", color='b', rotation=90, va='center')

    ax.set_xlim(0, web_width + 60)
    ax.set_ylim(0, h_draw)
    ax.axis('off')
    ax.set_title(f"Shop Drawing: {n_bolts}-M{int(bolt_dia)}", fontsize=10, fontweight='bold')
    return fig

# =========================================================
# 🧠 4. CALCULATION CORE
# =========================================================
def calculate_zx(h, b, tw, tf):
    h, b, tw, tf = h/10, b/10, tw/10, tf/10
    return (b*tf*(h-tf)) + (tw*(h-2*tf)**2/4)

def calculate_connection(props, load_percent, bolt_dia, span_factor):
    h, tw, fy, fu = props['h'], props['tw'], props['Fy'], props['Fu']
    b, tf = props.get('b', h/2), props.get('tf', tw*1.5)
    
    # Load
    Aw = (h/10)*(tw/10)
    V_cap = 1.0 * (0.6 * fy * Aw)
    V_u = (load_percent/100) * V_cap
    
    # Critical Span (Physics Engine) ⚛️
    Zx = calculate_zx(h, b, tw, tf)
    phiMn = 0.90 * (fy * Zx)
    # Formula: L = Factor * (M / V)
    L_crit = (span_factor * (phiMn / V_u)) / 100.0 if V_u > 0 else 0
    
    # Bolts
    DB = float(bolt_dia)
    Ab = 3.1416 * (DB/10)**2 / 4
    Rn_shear = 0.75 * 3300 * Ab
    
    Le = 3.5
    Lc = Le - ((DB+2)/10)/2
    t_pl, t_web = 1.0, tw/10
    
    br_pl = 0.75 * min(1.2*Lc*t_pl*4050, 2.4*(DB/10)*t_pl*4050)
    br_web = 0.75 * min(1.2*Lc*t_web*fu, 2.4*(DB/10)*t_web*fu)
    
    cap = min(Rn_shear, br_pl, br_web)
    n = max(2, math.ceil(V_u / cap)) if cap > 0 else 99
    
    L_pl = (2*Le) + ((n-1)*7.0)
    util = (V_u / (n*cap)) * 100

    return {
        "Steel Section": props['name'],
        "h": h,
        "Design Vu": V_u/1000,
        "Span": L_crit,
        "Bolt Qty": n,
        "Bolt Spec": f"M{int(DB)}",
        "Plt Len": L_pl,
        "Util": util,
        "Le": Le, "S": 7.0
    }

# =========================================================
# 🖥️ 5. UI RENDERER
# =========================================================
def render_report_tab(beam_data, conn_data):
    st.markdown("### 🖨️ Advanced Connection Engine")

    # --- 🎛️ CONTROLS ---
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            load_pct = st.slider("Target Load (%)", 10, 100, 75, 5)
        with c2:
            bolt = st.selectbox("Bolt Size", [12, 16, 20, 24], index=2)
        with c3:
            # NEW: Support Selector
            case_options = [
                "Simple Beam (Uniform Load)", 
                "Simple Beam (Point Load @Center)",
                "Cantilever (Uniform Load)",
                "Cantilever (Point Load @Tip)"
            ]
            load_case = st.selectbox("Support Condition", case_options)
            
    # Get Factor
    factor = get_load_case_factor(load_case)

    st.divider()

    # --- SINGLE BEAM ---
    with st.expander("📌 Detail Analysis", expanded=True):
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
                }, load_pct, bolt, factor)
                
                c_left, c_right = st.columns([1, 1])
                
                with c_left:
                    st.subheader(res['Steel Section'])
                    st.metric("Design Shear (Vu)", f"{res['Design Vu']:.2f} Ton", f"@{load_pct}% Cap")
                    
                    # Dynamic Metric Label
                    st.metric("Critical Span Limit", f"{res['Span']:.2f} m", f"Case: {load_case}")
                    st.caption("ถ้าคานจริงยาวกว่านี้ -> จะพังด้วย Moment ก่อน (Shear ไม่ถึงเป้า)")
                    
                    st.write("---")
                    st.write(f"**Bolts:** {res['Bolt Qty']} - {res['Bolt Spec']}")
                    st.progress(res['Util']/100, f"Efficiency: {res['Util']:.0f}%")
                
                with c_right:
                    fig = draw_connection_sketch(res['h'], res['Bolt Qty'], float(bolt), res['Plt Len']*10, res['Le'], res['S'])
                    st.pyplot(fig)
            except Exception as e:
                st.error(f"Err: {e}")
        else:
             st.warning("Select beam first")

    # --- BATCH TABLE ---
    st.subheader("🚀 Batch Comparison Table")
    if st.button("⚡ Run Batch Analysis"):
        data = [calculate_connection(b, load_pct, bolt, factor) for b in get_standard_sections()]
        df = pd.DataFrame(data)
        st.dataframe(
            df[['Steel Section', 'Design Vu', 'Span', 'Bolt Qty', 'Util']], 
            column_config={
                "Design Vu": st.column_config.NumberColumn("Vu (Ton)", format="%.2f"),
                "Span": st.column_config.NumberColumn("Crit. Span (m)", format="%.2f"),
                "Util": st.column_config.ProgressColumn("Eff.", format="%.0f%%"),
            },
            use_container_width=True, hide_index=True
        )
