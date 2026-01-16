import streamlit as st
import math
import drawing_utils  # เรียกใช้ไฟล์ drawing_utils.py

def render_connection_tab(V_design_from_tab1, default_bolt_size, method, is_lrfd, section_data, conn_type, default_bolt_grade, default_mat_grade):
    
    # --- STYLE & LAYOUT ---
    st.markdown("""
    <style>
        .input-card { background-color: #f8fafc; padding: 20px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 20px; }
        .result-card { background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 5px solid #3b82f6; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 15px; }
        .metric-label { font-size: 14px; color: #64748b; font-weight: 600; text-transform: uppercase; }
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

    # --- MAIN COLUMNS ---
    col_input, col_result = st.columns([1, 1.5], gap="large")

    # ==========================
    # 1. INPUT SECTION
    # ==========================
    with col_input:
        st.markdown("#### ⚙️ Configuration")
        with st.container():
            st.markdown('<div class="input-card">', unsafe_allow_html=True)
            
            # --- 1. Bolt Settings ---
            st.markdown("**1. Bolt Settings**")
            c1, c2 = st.columns(2)
            with c1:
                size_map = {"M12": 1.2, "M16": 1.6, "M20": 2.0, "M22": 2.2, "M24": 2.4, "M27": 2.7}
                try:
                    def_idx = list(size_map.keys()).index(default_bolt_size)
                except ValueError:
                    def_idx = 2
                b_size_str = st.selectbox("Bolt Size", list(size_map.keys()), index=def_idx)
                d_bolt = size_map[b_size_str] # cm
            with c2:
                grades = ["A325 (High Strength)", "Grade 8.8", "A490"]
                b_grade = st.selectbox("Bolt Grade", grades)

            st.markdown("---")
            
            # --- 2. Plate Geometry (Detailed) ---
            st.markdown("**2. Geometry (Plate)**")
            h_beam = section_data.get('h', 400)/10 # cm
            
            # Row 2.1: Quantity
            c_qty1, c_qty2 = st.columns(2)
            default_rows = max(2, int(h_beam / 8))
            n_rows = c_qty1.number_input("Rows", min_value=1, value=default_rows)
            n_cols = c_qty2.number_input("Columns", min_value=1, value=1)
            
            # Row 2.2: Vertical Dimensions
            st.caption("↕️ Vertical Dimensions (cm)")
            c_v1, c_v2 = st.columns(2)
            pitch_v = c_v1.number_input("Pitch (V)", min_value=3.0, value=7.5, step=0.5, help="ระยะห่างระหว่างแถวแนวดิ่ง")
            edge_v = c_v2.number_input("Edge (V)", min_value=2.0, value=4.0, step=0.5, help="ระยะขอบบน-ล่าง")
            
            # Row 2.3: Horizontal Dimensions
            st.caption("↔️ Horizontal Dimensions (cm)")
            c_h1, c_h2, c_h3 = st.columns(3)
            dist_weld = c_h1.number_input("To Weld", min_value=3.0, value=5.0, step=0.5, help="ระยะจากแนวเชื่อมถึงน็อตแถวแรก (e1)")
            dist_edge = c_h2.number_input("To Edge", min_value=3.0, value=4.0, step=0.5, help="ระยะจากน็อตแถวสุดท้ายถึงขอบแผ่น (e2)")
            pitch_h = c_h3.number_input("Pitch (H)", min_value=3.0, value=6.0, step=0.5, disabled=(n_cols<=1), help="ระยะห่างระหว่างคอลัมน์")

            st.markdown("---")
            
            # --- 3. Plate & Weld Spec ---
            st.markdown("**3. Plate & Weld**")
            pl_thick = st.selectbox("Plate Thick (mm)", [6, 9, 10, 12, 16, 20, 25], index=2)
            weld_sz = st.number_input("Weld Size (mm)", min_value=3, value=6)
            
            # Material
            fy_pl = 2500 if "A36" in default_mat_grade or "SS400" in default_mat_grade else 3500
            fu_pl = 4000 if fy_pl == 2500 else 4900
            
            st.markdown('</div>', unsafe_allow_html=True)

            # --- Validation & Calculations ---
            h_plate = (n_rows - 1) * pitch_v + (2 * edge_v) # cm
            w_plate = dist_weld + ((n_cols - 1) * pitch_h) + dist_edge # cm (Auto Calculate Width)
            
            # Display Calculated Dimensions
            st.info(f"📏 Plate Size: **{w_plate:.1f} x {h_plate:.1f} cm**")
            
            if h_plate > h_beam:
                st.error(f"⚠️ Plate height ({h_plate}cm) > Beam depth ({h_beam}cm)")

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
    # 3. RESULT & DRAWING DASHBOARD
    # ==========================
    with col_result:
        status_color = "#22c55e" if is_pass else "#ef4444"
        status_text = "PASS" if is_pass else "FAIL"
        
        # Summary Card
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

        for name, cap in capacities.items():
            r = V_design_from_tab1 / cap if cap > 0 else 1.5
            st.progress(min(r, 1.0), text=f"{name}: {cap:,.0f} kg (Ratio: {r:.2f})")

        st.markdown("---")
        
        # ==========================
        # 4. PLOTLY DRAWING SECTION
        # ==========================
        st.markdown("#### 📐 Construction Details")
        
        # Data Prep (mm)
        beam_h_mm = section_data.get('h', 400)
        beam_b_mm = section_data.get('b', 200)
        
        beam_dict = {
            'h': beam_h_mm,
            'b': beam_b_mm,
            'tf': section_data.get('tf', 13),
            'tw': section_data.get('tw', 8)
        }
        
        # Update Plate Data with calculated WIDTH and Inputs
        plate_dict = {
            'h': h_plate * 10,       
            'w': w_plate * 10,       # Use calculated width
            't': pl_thick,           
            'e1': dist_weld * 10,    # Horizontal dist to first bolt
            'lv': edge_v * 10,       # Vertical edge
            'weld_size': weld_sz     
        }
        
        bolt_dict = {
            'd': d_bolt * 10,        
            'rows': n_rows,
            'cols': n_cols,
            's_v': pitch_v * 10,      # Vertical pitch
            's_h': pitch_h * 10       # Horizontal pitch
        }

        tab1, tab2, tab3 = st.tabs(["🖼️ Elevation (Front)", "🏗️ Plan (Top)", "✂️ Section (Side)"])
        
        def fit_view(fig, x_range, y_range, height=500):
            fig.update_layout(
                height=height,
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis=dict(range=x_range, visible=False, scaleanchor="y", scaleratio=1),
                yaxis=dict(range=y_range, visible=False),
                dragmode="pan",
                showlegend=False
            )
            return fig

        pad = 50 

        with tab1:
            try:
                fig_front = drawing_utils.create_front_view(beam_dict, plate_dict, bolt_dict)
                
                # Elevation Range
                y_max = (beam_h_mm / 2) + pad
                y_min = -(beam_h_mm / 2) - pad
                x_max = beam_b_mm + pad
                x_min = -pad 
                
                st.plotly_chart(
                    fit_view(fig_front, [x_min, x_max], [y_min, y_max], height=550), 
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error: {e}")

        with tab2:
            try:
                fig_plan = drawing_utils.create_plan_view(beam_dict, plate_dict, bolt_dict)
                
                # Plan Range
                x_half = (beam_b_mm / 2) + pad
                y_range_shifted = [-150, 250] 
                
                st.plotly_chart(
                    fit_view(fig_plan, [-x_half, x_half], y_range_shifted, height=400),
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error: {e}")

        with tab3:
            try:
                fig_side = drawing_utils.create_side_view(beam_dict, plate_dict, bolt_dict)
                
                # Section Range
                pad_zoom = 100 
                y_max = (beam_h_mm / 2) + pad_zoom
                y_min = -(beam_h_mm / 2) - pad_zoom
                x_limit_zoomed = 250 
                
                st.plotly_chart(
                    fit_view(fig_side, [-x_limit_zoomed, x_limit_zoomed], [y_min, y_max], height=550),
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error: {e}")

        st.caption("Interactive Drawing powered by Plotly")
