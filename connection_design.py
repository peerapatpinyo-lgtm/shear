import streamlit as st
import math
import drawing_utils  # เรียกใช้ไฟล์ drawing_utils.py

def render_connection_tab(V_design_from_tab1, default_bolt_size, method, is_lrfd, section_data, conn_type, default_bolt_grade, default_mat_grade):
    
    # --- STYLE & LAYOUT ---
    st.markdown("""
    <style>
        .input-card { background-color: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 15px; }
        .control-label { font-weight: bold; font-size: 14px; color: #1e293b; margin-bottom: 5px; }
        .dim-display { background-color: #e0f2fe; color: #0369a1; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 13px; }
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

    col_input, col_result = st.columns([1, 1.4], gap="medium")

    # ==========================
    # 1. INPUT SECTION (FULL CONTROL)
    # ==========================
    with col_input:
        st.markdown("#### 🛠️ Connection Setup")
        
        # --- Group 1: Bolt & Material ---
        with st.expander("1. Bolt & Material Spec", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                size_map = {"M12": 1.2, "M16": 1.6, "M20": 2.0, "M22": 2.2, "M24": 2.4, "M27": 2.7}
                try: def_idx = list(size_map.keys()).index(default_bolt_size)
                except: def_idx = 2
                b_size_str = st.selectbox("Size", list(size_map.keys()), index=def_idx)
                d_bolt = size_map[b_size_str] # cm
            with c2:
                b_grade = st.selectbox("Grade", ["A325", "Gr. 8.8", "A490"])
            
            c3, c4 = st.columns(2)
            pl_thick = c3.select_slider("Plate T (mm)", options=[6, 9, 10, 12, 16, 19, 20, 25], value=10)
            weld_sz = c4.number_input("Weld (mm)", 3, 12, 6)

        # --- Group 2: Geometry Control (The Core Request) ---
        st.markdown('<div class="input-card">', unsafe_allow_html=True)
        st.markdown('<p class="control-label">📍 Bolt Layout & Plate Size</p>', unsafe_allow_html=True)
        
        # 2.1 Rows & Cols
        col_r1, col_r2 = st.columns(2)
        h_beam = section_data.get('h', 400)/10 # cm
        def_rows = max(2, int(h_beam / 8))
        n_rows = col_r1.number_input("Rows (Qty)", 1, 10, def_rows)
        n_cols = col_r2.number_input("Cols (Qty)", 1, 4, 1)

        st.markdown("---")
        
        # 2.2 Vertical Dimensions (Height Control)
        st.caption("↕️ Vertical (Control Height)")
        v1, v2 = st.columns(2)
        pitch_v = v1.number_input("Pitch V (cm)", 3.0, 15.0, 7.5, step=0.5, help="ระยะห่างน็อตแนวดิ่ง")
        edge_v = v2.number_input("Edge V (cm)", 2.0, 10.0, 4.0, step=0.5, help="ระยะขอบบน/ล่าง")
        
        # Calculate Height
        h_plate = (n_rows - 1) * pitch_v + (2 * edge_v)
        
        # 2.3 Horizontal Dimensions (Width Control)
        st.caption("↔️ Horizontal (Control Width)")
        h1, h2, h3 = st.columns(3)
        dist_weld = h1.number_input("To Weld", 3.0, 10.0, 5.0, step=0.5, help="Dist to Weld (e1)")
        
        pitch_h = 0.0
        if n_cols > 1:
            pitch_h = h2.number_input("Pitch H", 3.0, 10.0, 6.0, step=0.5, help="Horizontal Pitch")
        else:
            h2.text_input("Pitch H", "-", disabled=True)
            
        dist_edge = h3.number_input("To Edge", 2.0, 10.0, 4.0, step=0.5, help="Dist to Edge (e2)")

        # Calculate Width
        w_plate = dist_weld + (max(0, n_cols - 1) * pitch_h) + dist_edge
        
        # Show Resulting Dimensions
        st.markdown(f"""
        <div style="margin-top:10px; text-align:center;">
            <span class="dim-display">Plate Size: {w_plate:.1f} x {h_plate:.1f} cm</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Warnings
        if h_plate > h_beam:
            st.warning(f"⚠️ Plate H ({h_plate}cm) > Beam H ({h_beam}cm)")

        st.markdown('</div>', unsafe_allow_html=True)

        # --- Material Strength Setup ---
        fy_pl = 2500 if "A36" in default_mat_grade or "SS400" in default_mat_grade else 3500
        fu_pl = 4000 if fy_pl == 2500 else 4900

    # ==========================
    # 2. CALCULATION LOGIC
    # ==========================
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

    # ==========================
    # 3. RESULT & DRAWING
    # ==========================
    with col_result:
        # Status Bar
        status_color = "#22c55e" if is_pass else "#ef4444"
        st.markdown(f"""
        <div style="background:{status_color}; color:white; padding:10px 15px; border-radius:5px; margin-bottom:15px; display:flex; justify-content:space-between; align-items:center;">
            <span style="font-weight:bold; font-size:18px;">{'PASS ✅' if is_pass else 'FAIL ❌'}</span>
            <span>Ratio: <b>{ratio:.2f}</b> (Gov: {min(capacities, key=capacities.get)})</span>
        </div>
        """, unsafe_allow_html=True)

        # Drawing Tabs
        st.markdown("#### 📐 Interactive Detail")
        
        # --- PREPARE DATA FOR PLOTTING (LINKED TO INPUTS) ---
        beam_h_mm = section_data.get('h', 400)
        beam_b_mm = section_data.get('b', 200)
        
        beam_dict = {
            'h': beam_h_mm,
            'b': beam_b_mm,
            'tf': section_data.get('tf', 13),
            'tw': section_data.get('tw', 8)
        }
        
        # Direct Link: Inputs -> Plot Dictionary
        plate_dict = {
            'h': h_plate * 10,       # From (Rows x PitchV) + EdgeV
            'w': w_plate * 10,       # From WeldDist + PitchH + EdgeDist
            't': pl_thick,           # From Slider
            'e1': dist_weld * 10,    # From Input
            'lv': edge_v * 10,       # From Input
            'weld_size': weld_sz     # From Input
        }
        
        bolt_dict = {
            'd': d_bolt * 10,        # From Selectbox
            'rows': n_rows,          # From Input
            'cols': n_cols,          # From Input
            's_v': pitch_v * 10,     # From Input
            's_h': pitch_h * 10      # From Input
        }

        tab1, tab2, tab3 = st.tabs(["🖼️ Front", "🏗️ Top", "✂️ Side"])
        
        # View Helper
        def fit_view(fig, x_range, y_range, height=500):
            fig.update_layout(
                height=height,
                margin=dict(l=10, r=10, t=30, b=10),
                xaxis=dict(range=x_range, visible=False, scaleanchor="y", scaleratio=1),
                yaxis=dict(range=y_range, visible=False),
                dragmode="pan", showlegend=False
            )
            return fig

        pad = 50

        with tab1: # Elevation
            try:
                fig_front = drawing_utils.create_front_view(beam_dict, plate_dict, bolt_dict)
                # Center Y, Center X (mostly)
                st.plotly_chart(
                    fit_view(fig_front, [-pad, beam_b_mm + pad], [-(beam_h_mm/2)-pad, (beam_h_mm/2)+pad], 500), 
                    use_container_width=True
                )
            except Exception as e: st.error(e)

        with tab2: # Plan (Top)
            try:
                fig_plan = drawing_utils.create_plan_view(beam_dict, plate_dict, bolt_dict)
                # Shifted UP as requested
                st.plotly_chart(
                    fit_view(fig_plan, [-(beam_b_mm/2)-pad, (beam_b_mm/2)+pad], [-150, 250], 400),
                    use_container_width=True
                )
            except Exception as e: st.error(e)

        with tab3: # Section (Side)
            try:
                fig_side = drawing_utils.create_side_view(beam_dict, plate_dict, bolt_dict)
                # Zoomed OUT as requested
                zoom_pad = 100
                st.plotly_chart(
                    fit_view(fig_side, [-250, 250], [-(beam_h_mm/2)-zoom_pad, (beam_h_mm/2)+zoom_pad], 500),
                    use_container_width=True
                )
            except Exception as e: st.error(e)

        # Capacity Bars
        with st.expander("📊 Calculation Breakdown"):
            for name, cap in capacities.items():
                st.progress(min(V_design_from_tab1/cap, 1.0), f"{name}: {cap:,.0f} kg")
