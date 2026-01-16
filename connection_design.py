import streamlit as st
import math
import drawing_utils # <--- เรียกใช้ไฟล์ drawing_utils.py ที่คุณมีอยู่แล้ว

def render_connection_tab(V_design_from_tab1, default_bolt_size, method, is_lrfd, section_data, conn_type, default_bolt_grade, default_mat_grade):
    
    # --- STYLE & LAYOUT ---
    st.markdown("""
    <style>
        .input-card { background-color: #f8fafc; padding: 20px; border-radius: 10px; border: 1px solid #e2e8f0; margin-bottom: 20px; }
        .result-card { background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 5px solid #3b82f6; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 15px; }
        .metric-label { font-size: 14px; color: #64748b; font-weight: 600; text-transform: uppercase; }
        .pass-text { color: #22c55e; font-weight: 900; }
        .fail-text { color: #ef4444; font-weight: 900; }
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

    # --- SPLIT LAYOUT ---
    col_input, col_result = st.columns([1, 1.5], gap="large")

    # ==========================================
    # 1. INPUT PANEL (LEFT)
    # ==========================================
    with col_input:
        st.markdown("#### ⚙️ Connection Config")
        with st.container():
            st.markdown('<div class="input-card">', unsafe_allow_html=True)
            
            # --- Bolt Settings ---
            st.markdown("**1. Bolt Specification**")
            c1, c2 = st.columns(2)
            with c1:
                # Map bolt size strings to diameter (cm)
                size_map = {"M12": 1.2, "M16": 1.6, "M20": 2.0, "M22": 2.2, "M24": 2.4, "M27": 2.7}
                # Set default index safely
                try:
                    def_idx = list(size_map.keys()).index(default_bolt_size)
                except ValueError:
                    def_idx = 2 # Default to M20 if not found
                
                b_size_str = st.selectbox("Bolt Size", list(size_map.keys()), index=def_idx)
                d_bolt = size_map[b_size_str]
            with c2:
                grades = ["A325 (High Strength)", "Grade 8.8", "A490"]
                b_grade = st.selectbox("Bolt Grade", grades)

            st.markdown("---")
            
            # --- Plate Geometry ---
            st.markdown("**2. Plate Geometry**")
            h_beam = section_data.get('h', 400)/10 # Convert mm to cm
            default_rows = max(2, int(h_beam / 8))
            
            row_c1, row_c2 = st.columns(2)
            n_rows = row_c1.number_input("Rows", min_value=1, value=default_rows)
            n_cols = row_c2.number_input("Columns", min_value=1, value=1)
            
            geo_c1, geo_c2 = st.columns(2)
            pitch = geo_c1.number_input("Pitch (cm)", min_value=3.0, value=7.5, step=0.5)
            edge_dist = geo_c2.number_input("Edge (cm)", min_value=2.0, value=4.0, step=0.5)
            
            st.markdown("---")
            
            # --- Thickness & Weld ---
            st.markdown("**3. Detail & Weld**")
            pl_thick = st.selectbox("Plate Thick (mm)", [6, 9, 10, 12, 16, 20, 25], index=2)
            weld_sz = st.number_input("Weld Size (mm)", min_value=3, value=6)
            
            # Set Material Properties based on Sidebar selection passed via default_mat_grade
            fy_pl = 2500 if "A36" in default_mat_grade or "SS400" in default_mat_grade else 3500
            fu_pl = 4000 if fy_pl == 2500 else 4900
            
            st.markdown('</div>', unsafe_allow_html=True)

            # --- Validation Info ---
            h_plate = (n_rows - 1) * pitch + (2 * edge_dist)
            st.caption(f"ℹ️ Calculated Plate Height: **{h_plate:.1f} cm**")
            if h_plate > h_beam:
                st.error(f"⚠️ Plate ({h_plate}cm) exceeds Beam Depth ({h_beam}cm)!")

    # ==========================================
    # 2. CALCULATION ENGINE
    # ==========================================
    # 2.1 Bolt Shear
    Ab = math.pi * (d_bolt**2) / 4
    Fnv = 3720 if "A325" in b_grade else (4690 if "A490" in b_grade else 2800)
    if not is_lrfd: Fnv = Fnv / 1.5
    cap_bolt_shear = (n_rows * n_cols) * (Fnv * Ab)
    
    # 2.2 Bolt Bearing
    Rn_bearing_unit = 2.4 * d_bolt * (pl_thick/10) * fu_pl
    if not is_lrfd: Rn_bearing_unit = Rn_bearing_unit / 2.0
    cap_bolt_bearing = (n_rows * n_cols) * Rn_bearing_unit
    
    # 2.3 Plate Yield
    Ag_plate = h_plate * (pl_thick/10)
    Rn_y = 0.60 * fy_pl * Ag_plate
    if not is_lrfd: Rn_y = Rn_y / 1.50
    cap_plate_yield = Rn_y

    # 2.4 Plate Rupture
    An_plate = Ag_plate - (n_rows * (d_bolt + 0.2) * (pl_thick/10))
    Rn_r = 0.60 * fu_pl * An_plate
    if not is_lrfd: Rn_r = Rn_r / 2.00
    cap_plate_rupture = Rn_r
    
    # 2.5 Weld Shear
    Fn_weld = 0.60 * 4900 # E70XX
    Aw_weld = 0.707 * (weld_sz/10) * h_plate * 2
    Rn_w = Fn_weld * Aw_weld
    if not is_lrfd: Rn_w = Rn_w / 2.00
    cap_weld = Rn_w

    # Summary
    capacities = {
        "Bolt Shear": cap_bolt_shear, 
        "Bolt Bearing": cap_bolt_bearing,
        "Plate Yield": cap_plate_yield, 
        "Plate Rupture": cap_plate_rupture,
        "Weld Shear": cap_weld
    }
    min_cap = min(capacities.values())
    gov_mode = min(capacities, key=capacities.get)
    ratio = V_design_from_tab1 / min_cap if min_cap > 0 else 999
    is_pass = ratio <= 1.0

    # ==========================================
    # 3. RESULT DASHBOARD (RIGHT)
    # ==========================================
    with col_result:
        status_color = "#22c55e" if is_pass else "#ef4444"
        status_text = "PASS" if is_pass else "FAIL"
        
        # --- Summary Card ---
        st.markdown(f"""
        <div class="result-card" style="border-left-color: {status_color}">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span class="metric-label">Status</span><br>
                    <span style="font-size:32px; font-weight:900; color:{status_color}">{status_text}</span>
                </div>
                <div style="text-align:right;">
                    <span class="metric-label">Efficiency</span><br>
                    <span style="font-size:32px; font-weight:900;">{ratio:.2f}</span>
                </div>
            </div>
            <hr style="margin:10px 0;">
            <div style="font-size:14px; color:#475569;">
                Governing Limit: <b>{gov_mode}</b><br>
                Capacity: <b>{min_cap:,.0f} kg</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # --- Detailed Check (Progress Bars) ---
        st.markdown("#### ✅ Check Breakdown")
        for name, cap in capacities.items():
            r = V_design_from_tab1 / cap if cap > 0 else 1.5
            bar_color = "green" if r <= 1.0 else "red"
            st.progress(min(r, 1.0), text=f"{name}: {cap:,.0f} kg (Ratio: {r:.2f})")

        st.markdown("---")
        
        # --- DRAWING SECTION ---
        # ตรงนี้คือส่วนที่เรียกใช้ drawing_utils.py ที่คุณทำไว้แล้ว
        st.markdown("#### 📐 Engineering Drawing (3 Views)")
        
        with st.spinner("Generating CAD Drawings..."):
            # Prepare Dictionary Data Structure required by drawing_utils
            plate_dims = {
                'h': h_plate, 
                'w': 15.0,     # Fixed visual width or calculate based on bolt spacing
                't': pl_thick
            }
            bolt_dims = {
                'rows': n_rows, 
                'cols': n_cols, 
                'pitch': pitch, 
                'edge': edge_dist, 
                'dia': d_bolt
            }
            
            # เรียกฟังก์ชันจากไฟล์ drawing_utils.py
            try:
                fig_cad = drawing_utils.draw_fin_plate_3views(section_data, plate_dims, bolt_dims, weld_sz)
                st.pyplot(fig_cad)
            except Exception as e:
                st.error(f"Error calling drawing_utils: {e}")
                st.info("Please ensuring 'drawing_utils.py' is in the same folder and has the 'draw_fin_plate_3views' function.")
