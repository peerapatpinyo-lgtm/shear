import streamlit as st
import pandas as pd
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_engineering_views(section_data, plate_dims, bolt_dims, weld_sz):
    """
    สร้างรูป Drawing 3 มุมมอง (Front, Top, Side) โดยใช้ Matplotlib
    """
    # Unpack Data
    h_beam = section_data.get('h', 400) / 10  # cm
    bf_beam = section_data.get('b', 200) / 10 # cm
    tw_beam = section_data.get('tw', 8) / 10  # cm
    tf_beam = section_data.get('tf', 13) / 10 # cm
    
    h_plate = plate_dims['h']
    w_plate = plate_dims['w'] # สมมติความกว้างแผ่น (ระยะยื่น)
    t_plate = plate_dims['t'] / 10 # cm
    
    rows = bolt_dims['rows']
    cols = bolt_dims['cols']
    pitch = bolt_dims['pitch']
    edge = bolt_dims['edge']
    d_bolt = bolt_dims['dia']
    
    # Setup Figure (3 Subplots)
    fig = plt.figure(figsize=(10, 8))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.5, 1], height_ratios=[1.5, 1], wspace=0.3, hspace=0.3)
    
    # -----------------------------------------------
    # 1. FRONT VIEW (Elevation) - Main View
    # -----------------------------------------------
    ax_front = fig.add_subplot(gs[0, 0])
    ax_front.set_title("1. Front View (Elevation)", fontsize=10, fontweight='bold', pad=10)
    
    # Column Face (Line)
    ax_front.axvline(x=0, color='black', linewidth=3)
    
    # Beam Outline (Hidden lines mostly, but showing web)
    ax_front.plot([0.5, 30], [h_beam/2, h_beam/2], 'k--', linewidth=0.8) # Top Flange
    ax_front.plot([0.5, 30], [-h_beam/2, -h_beam/2], 'k--', linewidth=0.8) # Bot Flange
    
    # Fin Plate
    rect_plate = patches.Rectangle((0, (h_beam/2) - (h_beam - h_plate)/2 - h_plate), 
                                   w_plate, h_plate, 
                                   linewidth=1.5, edgecolor='#2563eb', facecolor='#bfdbfe', alpha=0.5)
    ax_front.add_patch(rect_plate)
    
    # Weld Symbol (Triangle)
    weld_poly = patches.Polygon([[0, (h_beam/2) - (h_beam - h_plate)/2], 
                                 [0.8, (h_beam/2) - (h_beam - h_plate)/2 - 0.8], 
                                 [0, (h_beam/2) - (h_beam - h_plate)/2 - 1.6]], 
                                closed=True, color='black')
    # ax_front.add_patch(weld_poly) # Optional visual
    ax_front.text(-2, 0, f"Weld {weld_sz}mm", rotation=90, va='center', ha='center', fontsize=8)

    # Bolts
    start_y = ((h_beam/2) - (h_beam - h_plate)/2) - edge
    start_x = 5.0 # Distance from col face
    
    for c in range(cols):
        for r in range(rows):
            bx = start_x + (c * 5.0) # Assume horizontal pitch 50mm fixed for simple fin
            by = start_y - (r * pitch)
            circle = patches.Circle((bx, by), radius=d_bolt/2, edgecolor='black', facecolor='white')
            ax_front.add_patch(circle)
            # Crosshair
            ax_front.plot([bx-0.5, bx+0.5], [by, by], 'k-', linewidth=0.5)
            ax_front.plot([bx, bx], [by-0.5, by+0.5], 'k-', linewidth=0.5)

    ax_front.set_xlim(-5, 25)
    ax_front.set_ylim(-h_beam/2 - 5, h_beam/2 + 5)
    ax_front.set_aspect('equal')
    ax_front.axis('off')

    # -----------------------------------------------
    # 2. TOP VIEW (Plan)
    # -----------------------------------------------
    ax_top = fig.add_subplot(gs[1, 0])
    ax_top.set_title("2. Top View (Plan)", fontsize=10, fontweight='bold', pad=10)
    
    # Column Flange
    ax_top.plot([0, 0], [-10, 10], 'k-', linewidth=3)
    
    # Beam Web
    ax_top.plot([0.5, 30], [0, 0], 'k-', linewidth=tw_beam*5) # Exaggerate thickness for visual
    
    # Fin Plate (Offset from web)
    # Assume plate is on one side of web
    ax_top.plot([0, w_plate], [tw_beam/2 + t_plate/2, tw_beam/2 + t_plate/2], 
                color='#2563eb', linewidth=t_plate*5) 
    
    # Bolts (Line representation)
    for c in range(cols):
        bx = start_x + (c * 5.0)
        ax_top.plot([bx, bx], [-2, 2], 'k-.', linewidth=0.5)

    ax_top.set_xlim(-5, 25)
    ax_top.set_ylim(-5, 5)
    # ax_top.set_aspect('equal')
    ax_top.axis('off')
    
    # -----------------------------------------------
    # 3. SIDE VIEW (Profile) - Seeing Beam Section
    # -----------------------------------------------
    ax_side = fig.add_subplot(gs[0, 1])
    ax_side.set_title("3. Side View (Section)", fontsize=10, fontweight='bold', pad=10)
    
    # I-Shape Drawing
    # Web
    ax_side.add_patch(patches.Rectangle((-tw_beam/2, -h_beam/2), tw_beam, h_beam, color='gray', alpha=0.3))
    # Top Flange
    ax_side.add_patch(patches.Rectangle((-bf_beam/2, h_beam/2 - tf_beam), bf_beam, tf_beam, color='gray', alpha=0.3))
    # Bot Flange
    ax_side.add_patch(patches.Rectangle((-bf_beam/2, -h_beam/2), bf_beam, tf_beam, color='gray', alpha=0.3))
    
    # Fin Plate (Side View)
    plate_y_top = ((h_beam/2) - (h_beam - h_plate)/2)
    ax_side.add_patch(patches.Rectangle((tw_beam/2, plate_y_top - h_plate), t_plate, h_plate, 
                                        edgecolor='#2563eb', facecolor='#bfdbfe'))
    
    # Bolts
    for r in range(rows):
        by = start_y - (r * pitch)
        # Bolt head
        ax_side.add_patch(patches.Rectangle((tw_beam/2 + t_plate, by - d_bolt/2), 1.5, d_bolt, color='black'))
        # Nut
        ax_side.add_patch(patches.Rectangle((-tw_beam/2 - 1.5, by - d_bolt/2), 1.5, d_bolt, color='black'))
        # Shank
        ax_side.plot([-tw_beam/2, tw_beam/2 + t_plate], [by, by], 'k-', linewidth=1)

    ax_side.set_xlim(-bf_beam/2 - 5, bf_beam/2 + 5)
    ax_side.set_ylim(-h_beam/2 - 5, h_beam/2 + 5)
    ax_side.set_aspect('equal')
    ax_side.axis('off')

    return fig

# ==========================================
# MAIN RENDER FUNCTION
# ==========================================
def render_connection_tab(V_design_from_tab1, default_bolt_size, method, is_lrfd, section_data, conn_type, default_bolt_grade, default_mat_grade):
    
    # --- STYLE ---
    st.markdown("""
    <style>
        .input-card { background-color: #f8fafc; padding: 20px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 20px; }
        .result-card { background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 5px solid #3b82f6; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 15px; }
        .pass-card { border-left-color: #22c55e !important; }
        .fail-card { border-left-color: #ef4444 !important; }
        .metric-label { font-size: 14px; color: #64748b; font-weight: 600; text-transform: uppercase; }
        .metric-value { font-size: 24px; font-weight: 800; color: #1e293b; }
    </style>
    """, unsafe_allow_html=True)

    # --- HEADER ---
    col_head1, col_head2 = st.columns([2, 1])
    with col_head1:
        st.markdown(f"### 🔩 {conn_type} Design")
        st.caption(f"Beam: **{section_data.get('name', 'Custom Section')}** | Method: **{method}**")
    with col_head2:
        st.info(f"⚡ Design Load ($V_u$): **{V_design_from_tab1:,.0f} kg**")

    st.divider()

    # --- INPUT & RESULT COLUMNS ---
    col_input, col_result = st.columns([1, 1.5], gap="large")

    with col_input:
        st.markdown("#### ⚙️ Configuration")
        with st.container():
            st.markdown('<div class="input-card">', unsafe_allow_html=True)
            
            # 1. Bolt Settings
            st.markdown("**1. Bolt Settings**")
            c1, c2 = st.columns(2)
            with c1:
                size_map = {"M12": 1.2, "M16": 1.6, "M20": 2.0, "M22": 2.2, "M24": 2.4, "M27": 2.7}
                b_size_str = st.selectbox("Bolt Size", list(size_map.keys()), index=list(size_map.keys()).index(default_bolt_size) if default_bolt_size in size_map else 2)
                d_bolt = size_map[b_size_str]
            with c2:
                grades = ["A325 (High Strength)", "Grade 8.8", "A490"]
                b_grade = st.selectbox("Bolt Grade", grades)

            st.markdown("---")
            
            # 2. Geometry
            st.markdown("**2. Geometry (Plate)**")
            h_beam = section_data.get('h', 400)/10
            default_rows = max(2, int(h_beam / 8))
            
            row_c1, row_c2 = st.columns(2)
            n_rows = row_c1.number_input("Rows", min_value=1, value=default_rows)
            n_cols = row_c2.number_input("Columns", min_value=1, value=1)
            
            geo_c1, geo_c2 = st.columns(2)
            pitch = geo_c1.number_input("Pitch (cm)", min_value=3.0, value=7.5, step=0.5)
            edge_dist = geo_c2.number_input("Edge Dist (cm)", min_value=2.0, value=4.0, step=0.5)
            
            st.markdown("---")
            
            # 3. Plate & Weld
            st.markdown("**3. Plate & Weld**")
            pl_thick = st.selectbox("Plate Thick (mm)", [6, 9, 10, 12, 16, 20, 25], index=2)
            weld_sz = st.number_input("Weld Size (mm)", min_value=3, value=6)
            
            # Material
            fy_pl = 2500 if "A36" in default_mat_grade or "SS400" in default_mat_grade else 3500
            fu_pl = 4000 if fy_pl == 2500 else 4900
            
            st.markdown('</div>', unsafe_allow_html=True)

            h_plate = (n_rows - 1) * pitch + (2 * edge_dist)
            st.caption(f"ℹ️ Plate Height: **{h_plate:.1f} cm**")
            if h_plate > h_beam:
                st.error("⚠️ Plate height exceeds beam depth!")

    # --- CALCULATION ENGINE ---
    Ab = math.pi * (d_bolt**2) / 4
    Fnv = 3720 if "A325" in b_grade else (4690 if "A490" in b_grade else 2800)
    if not is_lrfd: Fnv = Fnv / 1.5
    cap_bolt_shear = (n_rows * n_cols) * (Fnv * Ab)
    
    Rn_bearing_unit = 2.4 * d_bolt * (pl_thick/10) * fu_pl
    if not is_lrfd: Rn_bearing_unit = Rn_bearing_unit / 2.0
    cap_bolt_bearing = (n_rows * n_cols) * Rn_bearing_unit
    
    Ag_plate = h_plate * (pl_thick/10)
    Rn_y = 0.60 * fy_pl * Ag_plate
    if not is_lrfd: Rn_y = Rn_y / 1.50
    cap_plate_yield = Rn_y

    An_plate = Ag_plate - (n_rows * (d_bolt + 0.2) * (pl_thick/10))
    Rn_r = 0.60 * fu_pl * An_plate
    if not is_lrfd: Rn_r = Rn_r / 2.00
    cap_plate_rupture = Rn_r
    
    Fn_weld = 0.60 * 4900 # E70XX
    Aw_weld = 0.707 * (weld_sz/10) * h_plate * 2
    Rn_w = Fn_weld * Aw_weld
    if not is_lrfd: Rn_w = Rn_w / 2.00
    cap_weld = Rn_w

    capacities = {
        "Bolt Shear": cap_bolt_shear, "Bolt Bearing": cap_bolt_bearing,
        "Plate Yield": cap_plate_yield, "Plate Rupture": cap_plate_rupture,
        "Weld Shear": cap_weld
    }
    min_cap = min(capacities.values())
    ratio = V_design_from_tab1 / min_cap if min_cap > 0 else 999
    is_pass = ratio <= 1.0

    # --- RESULT DASHBOARD ---
    with col_result:
        status_color = "#22c55e" if is_pass else "#ef4444"
        status_text = "PASS" if is_pass else "FAIL"
        
        st.markdown(f"""
        <div class="result-card" style="border-left-color: {status_color}">
            <div style="display:flex; justify-content:space-between;">
                <div>
                    <span class="metric-label">Status</span><br>
                    <span style="font-size:32px; font-weight:900; color:{status_color}">{status_text}</span>
                </div>
                <div style="text-align:right;">
                    <span class="metric-label">Efficiency</span><br>
                    <span style="font-size:32px; font-weight:900;">{ratio:.2f}</span>
                </div>
            </div>
            <div style="margin-top:10px; font-size:14px; color:#64748b;">
                Governing: <b>{min(capacities, key=capacities.get)}</b> ({min_cap:,.0f} kg)
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**Check Breakdown**")
        for name, cap in capacities.items():
            r = V_design_from_tab1 / cap if cap > 0 else 1.5
            st.progress(min(r, 1.0), text=f"{name}: {cap:,.0f} kg (Ratio: {r:.2f})")

        st.markdown("---")
        
        # --- [NEW] 3-VIEW DRAWING ---
        st.markdown("#### 📐 Engineering Drawing (3 Views)")
        
        with st.spinner("Generating CAD Drawings..."):
            plate_dims = {'h': h_plate, 'w': 15.0, 't': pl_thick} # w=15 assume
            bolt_dims = {'rows': n_rows, 'cols': n_cols, 'pitch': pitch, 'edge': edge_dist, 'dia': d_bolt}
            
            fig_cad = draw_engineering_views(section_data, plate_dims, bolt_dims, weld_sz)
            st.pyplot(fig_cad)
        
        st.caption("Note: Drawings are schematic representation. Dimensions in cm/mm.")
