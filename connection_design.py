import streamlit as st
import math
import plotly.graph_objects as go
import drawing_utils  # เรียกใช้ไฟล์ drawing_utils.py

def render_connection_tab(V_design_from_tab1, default_bolt_size, method, is_lrfd, section_data, conn_type, default_bolt_grade, default_mat_grade):
    
    # --- STYLE ---
    st.markdown("""
    <style>
        .input-card { background-color: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 15px; }
        .dim-check { font-weight: bold; padding: 4px 8px; border-radius: 4px; font-size: 13px; display: inline-block; margin-top: 5px;}
        .dim-ok { background-color: #dcfce7; color: #166534; }
        .dim-err { background-color: #fee2e2; color: #991b1b; }
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
    # 1. INPUT SECTION (MANUAL GEOMETRY)
    # ==========================
    with col_input:
        st.markdown("#### 🛠️ Connection Setup")
        
        # --- 1.1 Bolt Spec ---
        with st.expander("1. Bolt & Material", expanded=False):
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

        # --- 1.2 Geometry Control (Manual Size) ---
        st.markdown('<div class="input-card">', unsafe_allow_html=True)
        st.markdown("**2. Plate Geometry & Layout**")
        
        # Plate Size Inputs
        c_w, c_h = st.columns(2)
        w_plate_input = c_w.number_input("Plate Width (mm)", 50, 500, 150, step=10, help="ความกว้างแผ่นเหล็ก")
        h_plate_input = c_h.number_input("Plate Height (mm)", 50, 1000, 300, step=10, help="ความสูงแผ่นเหล็ก")
        
        st.markdown("---")
        
        # Bolt Layout
        col_r, col_c = st.columns(2)
        n_rows = col_r.number_input("Rows (Qty)", 1, 10, 3)
        n_cols = col_c.number_input("Cols (Qty)", 1, 4, 1)
        
        # Spacing Control
        st.caption("📍 Spacing & Edge Distance (mm)")
        
        # Vertical
        v1, v2 = st.columns(2)
        pitch_v_mm = v1.number_input("Pitch V (mm)", 30, 200, 75, step=5)
        edge_v_mm = v2.number_input("Edge V (mm)", 20, 100, 40, step=5)
        
        # Horizontal
        h1, h2 = st.columns(2)
        dist_weld_mm = h1.number_input("To Weld (e1)", 20, 100, 50, step=5, help="ระยะจากแนวเชื่อมถึงน็อตแถวแรก")
        pitch_h_mm = 0
        if n_cols > 1:
            pitch_h_mm = h2.number_input("Pitch H (mm)", 30, 200, 60, step=5)
        else:
            h2.text_input("Pitch H", "-", disabled=True)

        # --- Validation Check ---
        # Convert inputs to cm for calculation
        w_plate = w_plate_input / 10
        h_plate = h_plate_input / 10
        pitch_v = pitch_v_mm / 10
        edge_v = edge_v_mm / 10
        dist_weld = dist_weld_mm / 10
        pitch_h = pitch_h_mm / 10
        
        # Check Vertical Fit
        req_h = (n_rows - 1) * pitch_v + (2 * edge_v)
        check_h = h_plate >= req_h
        
        # Check Horizontal Fit
        req_w_bolts = dist_weld + (max(0, n_cols - 1) * pitch_h)
        rem_edge_mm = w_plate_input - (req_w_bolts * 10) # mm
        
        # Display Checks
        st.markdown(f"""
        <div style="font-size:13px; margin-top:5px;">
            <div>↕️ Height Check: <span class="dim-check {'dim-ok' if check_h else 'dim-err'}">
                {'OK' if check_h else f'Too Short (Req {req_h*10:.0f}mm)'}</span>
            </div>
            <div style="margin-top:4px;">↔️ Edge Distance (e2): <span class="dim-check {'dim-ok' if rem_edge_mm >= 20 else 'dim-err'}">
                {rem_edge_mm:.1f} mm</span> (Calc)
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Material Strength
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
    # 3. DRAWING & RESULT
    # ==========================
    with col_result:
        status_color = "#22c55e" if is_pass else "#ef4444"
        st.markdown(f"""
        <div style="background:{status_color}; color:white; padding:10px 15px; border-radius:5px; margin-bottom:15px; display:flex; justify-content:space-between; align-items:center;">
            <span style="font-weight:bold; font-size:18px;">{'PASS ✅' if is_pass else 'FAIL ❌'}</span>
            <span>Ratio: <b>{ratio:.2f}</b></span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 📐 Connection Detail")
        
        # Data Prep (mm)
        beam_h_mm = section_data.get('h', 400)
        beam_b_mm = section_data.get('b', 200)
        
        beam_dict = {
            'h': beam_h_mm, 'b': beam_b_mm,
            'tf': section_data.get('tf', 13), 'tw': section_data.get('tw', 8)
        }
        
        # Use Manual Inputs directly
        plate_dict = {
            'h': h_plate_input,      
            'w': w_plate_input,      
            't': pl_thick,           
            'e1': dist_weld_mm,    
            'lv': edge_v_mm,       
            'weld_size': weld_sz     
        }
        
        bolt_dict = {
            'd': d_bolt * 10,        
            'rows': n_rows, 'cols': n_cols,
            's_v': pitch_v_mm, 's_h': pitch_h_mm
        }

        # --- Helper Function: Inject Dimensions ---
        def add_manual_dims(fig, view_type, p_data, b_data):
            """
            ฟังก์ชันเสริมสำหรับเพิ่มเส้นบอกระยะ (Dimension) ลงในกราฟ Plotly
            โดยไม่ต้องแก้ไขไฟล์ drawing_utils.py
            """
            annot_color = "#0369a1" # Blue color for dims
            
            # Helper: Add Dim Line
            def draw_dim_line(x0, y0, x1, y1, text, offset_x=0, offset_y=0):
                # Main Line
                fig.add_shape(type="line", x0=x0, y0=y0, x1=x1, y1=y1, line=dict(color=annot_color, width=1))
                # Ends (Ticks)
                tick_len = 5
                if x0 == x1: # Vertical Dim
                    fig.add_shape(type="line", x0=x0-tick_len, y0=y0, x1=x0+tick_len, y1=y0, line=dict(color=annot_color, width=1))
                    fig.add_shape(type="line", x0=x1-tick_len, y0=y1, x1=x1+tick_len, y1=y1, line=dict(color=annot_color, width=1))
                    text_angle = -90
                else: # Horizontal Dim
                    fig.add_shape(type="line", x0=x0, y0=y0-tick_len, x1=x0, y0=y0+tick_len, line=dict(color=annot_color, width=1))
                    fig.add_shape(type="line", x0=x1, y0=y1-tick_len, x1=x1, y1=y1+tick_len, line=dict(color=annot_color, width=1))
                    text_angle = 0
                
                # Text
                mid_x, mid_y = (x0+x1)/2, (y0+y1)/2
                fig.add_annotation(
                    x=mid_x + offset_x, y=mid_y + offset_y,
                    text=f"<b>{text}</b>", showarrow=False,
                    font=dict(size=10, color=annot_color),
                    bgcolor="rgba(255,255,255,0.8)",
                    textangle=text_angle
                )

            if view_type == "front":
                # Add Horizontal Dimensions (Top of Plate)
                y_ref = (p_data['h']/2) + 20
                x_start = 0
                
                # 1. To Weld (e1)
                x_bolt1 = p_data['e1']
                draw_dim_line(x_start, y_ref, x_bolt1, y_ref, f"{p_data['e1']}", 0, 10)
                
                # 2. Pitch H (if any)
                curr_x = x_bolt1
                if b_data['cols'] > 1:
                    total_pitch = (b_data['cols']-1) * b_data['s_h']
                    draw_dim_line(curr_x, y_ref, curr_x + total_pitch, y_ref, f"{b_data['cols']-1}@{b_data['s_h']}", 0, 10)
                    curr_x += total_pitch
                
                # 3. To Edge (e2)
                x_end = p_data['w']
                e2_val = x_end - curr_x
                draw_dim_line(curr_x, y_ref, x_end, y_ref, f"{e2_val:.0f}", 0, 10)

            return fig

        # --- Plotting ---
        tab1, tab2, tab3 = st.tabs(["🖼️ Front", "🏗️ Top", "✂️ Side"])
        
        def fit_view(fig, x_range, y_range, height=500):
            fig.update_layout(
                height=height, margin=dict(l=10, r=10, t=30, b=10),
                xaxis=dict(range=x_range, visible=False, scaleanchor="y", scaleratio=1),
                yaxis=dict(range=y_range, visible=False),
                dragmode="pan", showlegend=False
            )
            return fig

        pad = 50

        with tab1: # Front
            try:
                fig_front = drawing_utils.create_front_view(beam_dict, plate_dict, bolt_dict)
                # Inject Dims!
                fig_front = add_manual_dims(fig_front, "front", plate_dict, bolt_dict)
                
                st.plotly_chart(
                    fit_view(fig_front, [-pad, beam_b_mm + pad], [-(beam_h_mm/2)-pad, (beam_h_mm/2)+pad+40], 500), 
                    use_container_width=True
                )
            except Exception as e: st.error(e)

        with tab2: # Top
            try:
                fig_plan = drawing_utils.create_plan_view(beam_dict, plate_dict, bolt_dict)
                st.plotly_chart(
                    fit_view(fig_plan, [-(beam_b_mm/2)-pad, (beam_b_mm/2)+pad], [-150, 250], 400),
                    use_container_width=True
                )
            except Exception as e: st.error(e)

        with tab3: # Side
            try:
                fig_side = drawing_utils.create_side_view(beam_dict, plate_dict, bolt_dict)
                zoom_pad = 100
                st.plotly_chart(
                    fit_view(fig_side, [-250, 250], [-(beam_h_mm/2)-zoom_pad, (beam_h_mm/2)+zoom_pad], 500),
                    use_container_width=True
                )
            except Exception as e: st.error(e)

        # Capacity Check Bars
        with st.expander("📊 Check Details", expanded=True):
            for name, cap in capacities.items():
                st.progress(min(V_design_from_tab1/cap, 1.0), f"{name}: {cap:,.0f} kg")
