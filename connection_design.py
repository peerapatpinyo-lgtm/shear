# connection_design.py
import streamlit as st
import math
import drawing_utils        # Import ไฟล์ที่คุณให้มา
import calculation_report   # (สมมติว่ามีไฟล์นี้อยู่แล้วสำหรับการทำ Report text)
import steel_db             # (สมมติว่ามีไฟล์นี้สำหรับ Database เหล็ก)

def render_connection_tab(V_design_from_tab1, default_bolt_size, method, is_lrfd, section_data, conn_type, default_bolt_grade, default_mat_grade):
    
    # --- STYLE & CSS ---
    st.markdown("""
    <style>
        .input-card { background-color: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 15px; }
        .dim-check { font-weight: bold; padding: 4px 8px; border-radius: 4px; font-size: 13px; display: inline-block; margin-top: 5px;}
        .dim-ok { background-color: #dcfce7; color: #166534; }
        .dim-err { background-color: #fee2e2; color: #991b1b; }
        .summary-table { font-size: 13px; width: 100%; border-collapse: collapse; margin-top: 5px; }
        .summary-table th { background-color: #f1f5f9; padding: 6px; border-bottom: 2px solid #cbd5e1; font-weight: bold; color: #334155; }
        .summary-table td { padding: 6px; border-bottom: 1px solid #e2e8f0; vertical-align: middle; }
        .pass-text { color: #166534; font-weight: bold; }
        .fail-text { color: #991b1b; font-weight: bold; }
        .hl-row { background-color: #fff7ed; }
        .load-source { font-size: 11px; color: #64748b; font-style: italic; margin-top: 4px; display: block; }
    </style>
    """, unsafe_allow_html=True)

    # --- HEADER ---
    col_head1, col_head2 = st.columns([2, 1])
    with col_head1:
        st.markdown(f"### 🔩 Connection Design: {conn_type}")
        st.caption(f"Code: AISC 360-16 ({method}) | Grade: {default_mat_grade}")
    with col_head2:
        st.info(f"⚡ Design Load ($V_u$): **{V_design_from_tab1:,.0f} kg**")
    st.divider()

    col_input, col_result = st.columns([1, 1.4], gap="medium")

    # ==========================
    # 1. INPUT SECTION (LEFT)
    # ==========================
    with col_input:
        st.markdown("#### 🛠️ Configuration")
        
        # --- 1.1 Beam Section (Inherited) ---
        current_beam_name = section_data.get('name', 'Custom Section')
        with st.expander(f"🔹 Beam: {current_beam_name}", expanded=False):
            # Read-only display primarily, allows override if needed
            beam_h_mm = float(section_data.get('h', 400))
            beam_b_mm = float(section_data.get('b', 200))
            beam_tw = float(section_data.get('tw', 8.0))
            beam_tf = float(section_data.get('tf', 13.0))
            
            c_ov1, c_ov2 = st.columns(2)
            if c_ov1.checkbox("Override Beam Data"):
                beam_tw = c_ov2.number_input("Web t (tw)", 1.0, 50.0, beam_tw, step=0.5)
                beam_h_mm = st.number_input("Depth (d)", 100, 2000, int(beam_h_mm))
            
            st.caption(f"Designing for Web t = {beam_tw} mm")

        # --- 1.2 Connection Parameters ---
        with st.expander("2. Plate & Bolt Details", expanded=True):
            # Bolts
            c1, c2 = st.columns(2)
            size_map = {"M12": 1.2, "M16": 1.6, "M20": 2.0, "M22": 2.2, "M24": 2.4, "M27": 2.7}
            b_size_str = c1.selectbox("Bolt Size", list(size_map.keys()), index=list(size_map.keys()).index(default_bolt_size) if default_bolt_size in size_map else 2)
            d_bolt = size_map[b_size_str]
            b_grade = c2.selectbox("Bolt Grade", ["A325", "Gr. 8.8", "A490"], index=0 if "A325" in default_bolt_grade else 1)
            
            # Plate
            c3, c4 = st.columns(2)
            pl_thick = c3.select_slider("Plate T (mm)", options=[6, 9, 10, 12, 16, 19, 20, 25], value=10)
            weld_sz = c4.number_input("Weld Size (mm)", 3, 12, 6)
            
            if "Double Angle" in conn_type:
                st.caption("ℹ️ For Double Angle, 'Plate T' represents Angle Thickness")

        # --- 1.3 Geometry Layout ---
        st.markdown('<div class="input-card">', unsafe_allow_html=True)
        st.markdown("**3. Geometry & Layout**")
        
        c_w, c_h = st.columns(2)
        w_plate_input = c_w.number_input("Plate/Angle Width", 50, 500, 100 if "Double" in conn_type else 150, step=10)
        h_plate_input = c_h.number_input("Plate/Angle Length", 50, 1000, 300, step=10)
        
        col_r, col_c = st.columns(2)
        n_rows = col_r.number_input("Rows", 1, 10, 3)
        n_cols = col_c.number_input("Cols", 1, 4, 1)
        
        st.caption("📍 Spacing (mm)")
        v1, v2 = st.columns(2)
        pitch_v_mm = v1.number_input("Pitch V", 30, 200, 75, step=5)
        edge_v_mm = v2.number_input("Edge V", 20, 100, 40, step=5)
        
        h1, h2 = st.columns(2)
        dist_weld_mm = h1.number_input("To Weld/Back", 20, 100, 50, step=5) # e1
        pitch_h_mm = h2.number_input("Pitch H", 30, 200, 60, step=5) if n_cols > 1 else 0

        # --- Quick Geometry Validation ---
        req_h = (n_rows - 1) * pitch_v_mm + (2 * edge_v_mm)
        check_h = h_plate_input >= req_h
        
        req_w = dist_weld_mm + (max(0, n_cols - 1) * pitch_h_mm) + 30 # +30 approx min edge
        rem_edge = w_plate_input - (dist_weld_mm + (max(0, n_cols - 1) * pitch_h_mm))
        
        st.markdown(f"""
        <div style="font-size:13px; margin-top:5px;">
            Height Check: <span class="dim-check {'dim-ok' if check_h else 'dim-err'}">{'OK' if check_h else f'Need {req_h}mm'}</span> | 
            Edge Rem: <span class="dim-check {'dim-ok' if rem_edge >= d_bolt*10*1.5 else 'dim-err'}">{rem_edge:.1f} mm</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ==========================================
        # 3. CALCULATION CORE (Multi-Type Support)
        # ==========================================
        
        # --- Common Constants ---
        V_kN = V_design_from_tab1 / 101.97
        fy_ksc = 2500 if "A36" in default_mat_grade or "SS400" in default_mat_grade else 3500
        Fy, Fu = (250, 400) if fy_ksc == 2500 else (345, 490)
        Fnv = 372 if "A325" in b_grade else 457 
        Fexx = 480 
        
        # Factors
        if is_lrfd:
            phi_v, phi_y, phi_r, phi_w, phi_bb = 0.75, 1.00, 0.75, 0.75, 0.75
            def get_cap(Rn, fac): return Rn * fac
        else:
            om_v, om_y, om_r, om_w, om_bb = 2.00, 1.50, 2.00, 2.00, 2.00
            def get_cap(Rn, fac): return Rn / fac
            
        # --- Bolt Basic ---
        d = d_bolt * 10 
        Ab = math.pi * d**2 / 4
        n_total = n_rows * n_cols
        
        results = [] # Store tuple (Label, Load, Cap, Ratio)
        
        # --- LOGIC SWITCH BASED ON TYPE ---
        
        # 1. BOLT SHEAR
        Rn_shear_unit = (Fnv * Ab) / 1000
        is_double_shear = "Double Angle" in conn_type
        shear_planes = 2 if is_double_shear else 1
        Rn_shear_total = Rn_shear_unit * n_total * shear_planes
        
        # Eccentricity Logic (Simplified Loop Analysis for Fin Plate)
        eccentricity = dist_weld_mm + ((n_cols-1)*pitch_h_mm)/2 if "Fin" in conn_type else 0
        C_coeff = 1.0 # Coefficient for ecc shear
        if eccentricity > 0 and "Fin" in conn_type:
            # Simplified Elastic Method (Vector Analysis) approximation
            # (In real app, full vector loop is needed, here we use conservative reduction)
            pass # We calculate actual resultant below
            
        # -- Vector Analysis for Fin Plate --
        if "Fin" in conn_type and eccentricity > 0:
            Moment = V_kN * eccentricity
            # Calculate sum r^2 ... (Standard elastic vector method)
            sum_r2 = 0
            cx, cy = ((n_cols-1)*pitch_h_mm)/2, ((n_rows-1)*pitch_v_mm)/2
            for c in range(n_cols):
                for r in range(n_rows):
                    dx = (c*pitch_h_mm) - cx
                    dy = (r*pitch_v_mm) - cy
                    sum_r2 += (dx**2 + dy**2)
            
            if sum_r2 > 0:
                Rv_direct = V_kN / n_total
                Rv_moment = (Moment * cx) / sum_r2
                Rh_moment = (Moment * cy) / sum_r2
                V_bolt_max = math.sqrt((Rv_direct + Rv_moment)**2 + Rh_moment**2)
            else:
                V_bolt_max = V_kN / n_total
        else:
            V_bolt_max = V_kN / n_total # Pure shear for others (Simplified)
            
        cap_bolt = get_cap(Rn_shear_unit * shear_planes, phi_v if is_lrfd else om_v)
        results.append(("Bolt Shear", V_bolt_max, cap_bolt, V_bolt_max/cap_bolt))

        # 2. BEARING
        # Plate Bearing
        Rn_br_pl = (2.4 * d * pl_thick * Fu) / 1000
        cap_br_pl = get_cap(Rn_br_pl, phi_bb if is_lrfd else om_bb)
        
        # Beam Web Bearing
        Rn_br_wb = (2.4 * d * beam_tw * Fu) / 1000
        cap_br_wb = get_cap(Rn_br_wb, phi_bb if is_lrfd else om_bb)
        
        # Double Angle Bearing (Sum of 2 angles)
        if "Double" in conn_type:
             Rn_br_pl = (2.4 * d * (2 * pl_thick) * Fu) / 1000 # 2 angles
             cap_br_pl = get_cap(Rn_br_pl, phi_bb if is_lrfd else om_bb)
        
        cap_br_gov = min(cap_br_pl, cap_br_wb)
        results.append(("Bearing (Gov)", V_bolt_max, cap_br_gov, V_bolt_max/cap_br_gov))

        # 3. SHEAR YIELD (Gross)
        Ag = h_plate_input * pl_thick * (2 if "Double" in conn_type else 1)
        Rn_y = (0.60 * Fy * Ag) / 1000
        cap_yld = get_cap(Rn_y, phi_y if is_lrfd else om_y)
        results.append(("Plate/Angle Yield", V_kN, cap_yld, V_kN/cap_yld))

        # 4. SHEAR RUPTURE (Net)
        h_hole = d + 2
        An = (h_plate_input - (n_rows * h_hole)) * pl_thick * (2 if "Double" in conn_type else 1)
        Rn_r = (0.60 * Fu * An) / 1000
        cap_rup = get_cap(Rn_r, phi_r if is_lrfd else om_r)
        results.append(("Plate/Angle Rupture", V_kN, cap_rup, V_kN/cap_rup))

        # 5. BLOCK SHEAR
        # Applicable mostly to Fin Plate and Angles
        l_gv = (n_rows - 1) * pitch_v_mm + edge_v_mm
        agv = l_gv * pl_thick * (2 if "Double" in conn_type else 1)
        anv = (l_gv - (n_rows - 0.5) * h_hole) * pl_thick * (2 if "Double" in conn_type else 1)
        ant = (rem_edge - 0.5 * h_hole) * pl_thick * (2 if "Double" in conn_type else 1)
        rn_blk = min(0.6*Fu*anv + 1.0*Fu*ant, 0.6*Fy*agv + 1.0*Fu*ant) / 1000
        cap_blk = get_cap(rn_blk, phi_r if is_lrfd else om_r)
        
        if "End Plate" not in conn_type:
            results.append(("Block Shear", V_kN, cap_blk, V_kN/cap_blk))

        # 6. WELD
        l_weld = h_plate_input * 2 # 2 lines
        if "Double" in conn_type: l_weld *= 2 # 2 angles = 4 lines usually, or 2 lines per angle
        
        rn_weld = (0.6 * Fexx * 0.707 * weld_sz * l_weld) / 1000
        cap_weld = get_cap(rn_weld, phi_w if is_lrfd else om_w)
        results.append(("Weld Strength", V_kN, cap_weld, V_kN/cap_weld))

        # --- MAX RATIO ---
        max_ratio = max([r[3] for r in results])
        is_pass = max_ratio <= 1.0

        # ==========================================
        # 4. SHOW SUMMARY TABLE
        # ==========================================
        st.markdown("#### 🏁 Final Summary")
        status_bg = "#dcfce7" if is_pass else "#fee2e2"
        status_txt = "#166534" if is_pass else "#991b1b"
        st.markdown(f"<div style='background:{status_bg}; color:{status_txt}; padding:10px; border-radius:6px; margin-bottom:10px; text-align:center; font-weight:bold;'>{'PASS ✅' if is_pass else 'FAIL ❌'} (Max Ratio: {max_ratio:.2f})</div>", unsafe_allow_html=True)
        
        rows_html = ""
        for name, load_val, cap_val, ratio in results:
            row_class = "hl-row" if ratio == max_ratio else ""
            text_class = "pass-text" if ratio <= 1.0 else "fail-text"
            rows_html += f"<tr class='{row_class}'><td>{name}</td><td align='center'>{load_val:.2f}</td><td align='center'>{cap_val:.2f}</td><td align='center' class='{text_class}'>{ratio:.2f}</td></tr>"

        st.markdown(f"<table class='summary-table'><thead><tr><th>Check</th><th>Load (kN)</th><th>Cap (kN)</th><th>Ratio</th></tr></thead><tbody>{rows_html}</tbody></table>", unsafe_allow_html=True)
        st.markdown(f"<div class='load-source'>* Geometry check for: <b>{conn_type}</b></div>", unsafe_allow_html=True)

    # ==========================
    # 5. RIGHT SECTION (TABS)
    # ==========================
    with col_result:
        tab_draw, tab_calc = st.tabs(["📐 Drawing", "📝 Full Report"])
        
        with tab_draw:
            # Prepare Data for Drawing Utils
            # NOTE: Drawing utils provided is optimized for Fin Plate / Shear Tab. 
            # We map inputs to "best fit" for others, or warn.
            
            beam_dict = {'h': beam_h_mm, 'b': beam_b_mm, 'tf': beam_tf, 'tw': beam_tw}
            plate_dict = {
                'h': h_plate_input, 
                'w': w_plate_input, 
                't': pl_thick, 
                'e1': dist_weld_mm, 
                'lv': edge_v_mm, 
                'weld_size': weld_sz,
                'type': conn_type
            }
            bolt_dict = {'d': d, 'rows': n_rows, 'cols': n_cols, 's_v': pitch_v_mm, 's_h': pitch_h_mm}

            def fit_view(fig, height=450):
                fig.update_layout(height=height, margin=dict(l=10,r=10,t=40,b=10))
                return fig
            
            if "Fin" in conn_type or "Shear Tab" in conn_type:
                sub_t1, sub_t2, sub_t3 = st.tabs(["Front", "Side (Sec A-A)", "Plan"])
                with sub_t1:
                    try:
                        fig = drawing_utils.create_front_view(beam_dict, plate_dict, bolt_dict)
                        st.plotly_chart(fit_view(fig, 500), use_container_width=True)
                    except Exception as e: st.error(f"Draw Error: {e}")
                with sub_t2:
                    try:
                        fig = drawing_utils.create_side_view(beam_dict, plate_dict, bolt_dict)
                        st.plotly_chart(fit_view(fig, 500), use_container_width=True)
                    except: pass
                with sub_t3:
                    try:
                        fig = drawing_utils.create_plan_view(beam_dict, plate_dict, bolt_dict)
                        st.plotly_chart(fit_view(fig, 450), use_container_width=True)
                    except: pass
            else:
                st.warning(f"⚠️ Detailed shop drawings in `drawing_utils` are optimized for Shear Tab (Fin Plate).")
                st.info("Showing schematic Front View for geometry verification:")
                try:
                    fig = drawing_utils.create_front_view(beam_dict, plate_dict, bolt_dict)
                    st.plotly_chart(fit_view(fig, 500), use_container_width=True)
                except: st.error("Could not render schematic.")

        with tab_calc:
            # Reuse your existing report generator or simple text dump
            st.markdown("### 📋 Design Calculation Trace")
            st.markdown(f"**Connection Type:** {conn_type}")
            st.markdown(f"**Method:** {'LRFD (phi)' if is_lrfd else 'ASD (Omega)'}")
            
            st.markdown("---")
            for name, load, cap, ratio in results:
                icon = "✅" if ratio <= 1.0 else "❌"
                st.markdown(f"**{icon} {name}**")
                st.latex(f"Ratio = \\frac{{{load:.2f}}}{{{cap:.2f}}} = \\mathbf{{{ratio:.2f}}}")
