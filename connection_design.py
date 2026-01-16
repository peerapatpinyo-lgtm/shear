import streamlit as st
import math
import plotly.graph_objects as go
import drawing_utils        
import calculation_report   
import steel_db             # <--- Import Database

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
        st.markdown(f"### 🔩 {conn_type} Design (Phase 2: DB Integrated)")
        st.caption(f"Method: **{method}**")
    with col_head2:
        st.info(f"⚡ Design Load ($V_u$): **{V_design_from_tab1:,.0f} kg**")
    st.divider()

    col_input, col_result = st.columns([1, 1.4], gap="medium")

    # ==========================
    # 1. INPUT SECTION (LEFT)
    # ==========================
    with col_input:
        st.markdown("#### 🛠️ Configuration")
        
        # --- 1.1 Beam Section Selection (PHASE 2 UPDATE) ---
        with st.expander("1. Beam Section (Database)", expanded=True):
            beam_source = st.radio("Source", ["Standard (SYS/TIS)", "Custom Input"], horizontal=True, label_visibility="collapsed")
            
            # Initial values from previous tab
            init_h = section_data.get('h', 400)
            init_b = section_data.get('b', 200)
            init_tw = section_data.get('tw', 8.0)
            init_tf = section_data.get('tf', 13.0)
            
            if "Standard" in beam_source:
                # Attempt to find closest match or default to index 13 (H400)
                sec_list = steel_db.get_section_list()
                try: 
                    def_idx = sec_list.index(section_data.get('name', ''))
                except: 
                    def_idx = 13 # Default to H-400x200
                
                selected_sec = st.selectbox("Select Section", sec_list, index=def_idx)
                props = steel_db.get_properties(selected_sec)
                
                # Auto-fill variables
                beam_h_mm = props['h']
                beam_b_mm = props['b']
                beam_tw = props['tw']
                beam_tf = props['tf']
                
                st.info(f"ℹ️ {selected_sec}: H={beam_h_mm}, Web={beam_tw}mm")
            else:
                # Custom Input
                c_cust1, c_cust2 = st.columns(2)
                beam_h_mm = c_cust1.number_input("Depth (d)", 100, 2000, int(init_h))
                beam_b_mm = c_cust2.number_input("Width (bf)", 50, 600, int(init_b))
                
                c_cust3, c_cust4 = st.columns(2)
                beam_tw = c_cust3.number_input("Web t (tw)", 3.0, 50.0, float(init_tw), step=0.5)
                beam_tf = c_cust4.number_input("Flange t (tf)", 3.0, 50.0, float(init_tf), step=0.5)

        # --- 1.2 Bolt & Plate Specs ---
        with st.expander("2. Connection Details", expanded=True):
            # Bolt
            c1, c2 = st.columns(2)
            size_map = {"M12": 1.2, "M16": 1.6, "M20": 2.0, "M22": 2.2, "M24": 2.4, "M27": 2.7}
            try: def_idx = list(size_map.keys()).index(default_bolt_size)
            except: def_idx = 2
            b_size_str = c1.selectbox("Bolt Size", list(size_map.keys()), index=def_idx)
            d_bolt = size_map[b_size_str] # cm
            
            b_grade = c2.selectbox("Bolt Grade", ["A325", "Gr. 8.8", "A490"])
            
            # Plate
            c3, c4 = st.columns(2)
            pl_thick = c3.select_slider("Plate T (mm)", options=[6, 9, 10, 12, 16, 19, 20, 25], value=10)
            weld_sz = c4.number_input("Weld Size (mm)", 3, 12, 6)

        # --- 1.3 Geometry Control ---
        st.markdown('<div class="input-card">', unsafe_allow_html=True)
        st.markdown("**3. Geometry & Layout**")
        
        c_w, c_h = st.columns(2)
        w_plate_input = c_w.number_input("Plate Width", 50, 500, 150, step=10)
        h_plate_input = c_h.number_input("Plate Height", 50, 1000, 300, step=10)
        
        # Check Plate Height vs Beam Depth (T-distance check approx)
        T_dist = beam_h_mm - (2 * beam_tf) - 70 # Rough T-dist
        if h_plate_input > T_dist:
            st.warning(f"⚠️ Plate height ({h_plate_input}) might exceed Beam T-distance (~{T_dist}mm)")
        
        st.markdown("---")
        
        col_r, col_c = st.columns(2)
        n_rows = col_r.number_input("Rows", 1, 10, 3)
        n_cols = col_c.number_input("Cols", 1, 4, 1)
        
        st.caption("📍 Spacing & Edge Distance (mm)")
        v1, v2 = st.columns(2)
        pitch_v_mm = v1.number_input("Pitch V (s)", 30, 200, 75, step=5)
        edge_v_mm = v2.number_input("Edge V (lv)", 20, 100, 40, step=5)
        
        h1, h2 = st.columns(2)
        dist_weld_mm = h1.number_input("To Weld (e1)", 20, 100, 50, step=5)
        pitch_h_mm = 0
        if n_cols > 1:
            pitch_h_mm = h2.number_input("Pitch H", 30, 200, 60, step=5)
        else:
            h2.text_input("Pitch H", "-", disabled=True)

        # Validation Calculations
        req_h = (n_rows - 1) * (pitch_v_mm/10) + (2 * (edge_v_mm/10))
        check_h = (h_plate_input/10) >= req_h
        req_w_bolts = (dist_weld_mm/10) + (max(0, n_cols - 1) * (pitch_h_mm/10))
        rem_edge_mm = w_plate_input - (req_w_bolts * 10)
        
        st.markdown(f"""
        <div style="font-size:13px; margin-top:5px;">
            <div>↕️ Height: <span class="dim-check {'dim-ok' if check_h else 'dim-err'}">{'OK' if check_h else 'Too Short'}</span></div>
            <div style="margin-top:4px;">↔️ Side Edge: <span class="dim-check {'dim-ok' if rem_edge_mm >= 20 else 'dim-err'}">{rem_edge_mm:.1f} mm</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ==========================================
        # 3. PRE-CALCULATION (PHASE 1 LOGIC)
        # ==========================================
        conversion_factor = 101.97
        V_kN = V_design_from_tab1 / conversion_factor
        
        fy_ksc = 2500 if "A36" in default_mat_grade or "SS400" in default_mat_grade else 3500
        Fy = 250 if fy_ksc == 2500 else 345 
        Fu = 400 if fy_ksc == 2500 else 490 
        Fnv = 372 if "A325" in b_grade else 457 
        Fexx = 480 
        
        if is_lrfd:
            phi_v, phi_y, phi_r, phi_w = 0.75, 1.00, 0.75, 0.75
            def get_cap(Rn, type_f): return Rn * type_f
        else:
            om_v, om_y, om_r, om_w = 2.00, 1.50, 2.00, 2.00
            def get_cap(Rn, type_f): return Rn / type_f

        # --- Bolt Analysis (Eccentricity) ---
        d = d_bolt * 10 
        Ab = math.pi * d**2 / 4
        n_total = n_rows * n_cols
        
        x_bar = ((n_cols - 1) * pitch_h_mm) / 2 if n_cols > 1 else 0
        eccentricity = dist_weld_mm + x_bar
        Moment = V_kN * eccentricity 
        
        sum_r2 = 0
        row_start = -((n_rows - 1) * pitch_v_mm) / 2
        col_start = -x_bar
        for c in range(n_cols):
            for r in range(n_rows):
                dx = col_start + (c * pitch_h_mm)
                dy = row_start + (r * pitch_v_mm)
                sum_r2 += (dx**2 + dy**2)
        
        # Forces on Critical Bolt
        Rv_direct = V_kN / n_total
        crit_x = x_bar 
        crit_y = ((n_rows - 1) * pitch_v_mm) / 2 
        
        if sum_r2 > 0:
            Rv_moment = (Moment * crit_x) / sum_r2 
            Rh_moment = (Moment * crit_y) / sum_r2 
        else:
            Rv_moment, Rh_moment = 0, 0
            
        V_resultant = math.sqrt((Rv_direct + Rv_moment)**2 + Rh_moment**2)
        
        # --- CAPACITIES ---
        # 1. Bolt Shear
        Rn_shear = (Fnv * Ab) / 1000
        cap_bolt_single = get_cap(Rn_shear, phi_v if is_lrfd else om_v)
        
        # 2. Bearing (Auto-selected Beam Web vs Plate)
        Rn_br_pl = (2.4 * d * pl_thick * Fu) / 1000
        cap_br_pl = get_cap(Rn_br_pl, phi_v if is_lrfd else om_v)
        
        # Check against BEAM WEB (Updated Logic from Phase 1)
        Rn_br_wb = (2.4 * d * beam_tw * Fu) / 1000 
        cap_br_wb = get_cap(Rn_br_wb, phi_v if is_lrfd else om_v)
        
        cap_br_gov = min(cap_br_pl, cap_br_wb)
        
        # 3. Plate & Block Shear
        Ag = h_plate_input * pl_thick
        Rn_y = (0.60 * Fy * Ag) / 1000
        cap_yld = get_cap(Rn_y, phi_y if is_lrfd else om_y)
        
        h_hole = d + 2
        An = (h_plate_input - (n_rows * h_hole)) * pl_thick
        Rn_r = (0.60 * Fu * An) / 1000
        cap_rup = get_cap(Rn_r, phi_r if is_lrfd else om_r)
        
        l_gv = (n_rows - 1) * pitch_v_mm + edge_v_mm
        agv = l_gv * pl_thick
        anv = (l_gv - (n_rows - 0.5) * h_hole) * pl_thick
        ant = (rem_edge_mm - 0.5 * h_hole) * pl_thick
        rn_blk = min(0.6*Fu*anv + 1.0*Fu*ant, 0.6*Fy*agv + 1.0*Fu*ant) / 1000
        cap_blk = get_cap(rn_blk, phi_r if is_lrfd else om_r)
        
        # 4. Weld
        l_weld = h_plate_input * 2
        rn_weld = (0.6 * Fexx * 0.707 * weld_sz * l_weld) / 1000
        cap_weld = get_cap(rn_weld, phi_w if is_lrfd else om_w)

        # Ratios
        ratio_bolt = V_resultant / cap_bolt_single
        ratio_bear = V_resultant / cap_br_gov
        ratio_yld = V_kN / cap_yld
        ratio_rup = V_kN / cap_rup
        ratio_blk = V_kN / cap_blk
        ratio_weld = V_kN / cap_weld
        
        max_ratio = max(ratio_bolt, ratio_bear, ratio_yld, ratio_rup, ratio_blk, ratio_weld)
        is_pass = max_ratio <= 1.0

        # ==========================================
        # 4. SHOW SUMMARY TABLE (LEFT)
        # ==========================================
        st.markdown("#### 🏁 Final Summary")
        status_bg = "#dcfce7" if is_pass else "#fee2e2"
        status_txt = "#166534" if is_pass else "#991b1b"
        st.markdown(f"<div style='background:{status_bg}; color:{status_txt}; padding:10px; border-radius:6px; margin-bottom:10px; text-align:center; font-weight:bold;'>{'PASS ✅' if is_pass else 'FAIL ❌'} (Max Ratio: {max_ratio:.2f})</div>", unsafe_allow_html=True)
        
        checks = [
            ("Bolt Shear", V_resultant, cap_bolt_single, ratio_bolt),
            ("Bearing (Web/Pl)", V_resultant, cap_br_gov, ratio_bear),
            ("Plate Yield", V_kN, cap_yld, ratio_yld),
            ("Plate Rupture", V_kN, cap_rup, ratio_rup),
            ("Block Shear", V_kN, cap_blk, ratio_blk),
            ("Weld Strength", V_kN, cap_weld, ratio_weld)
        ]
        
        rows_html = ""
        for name, load_val, cap_val, ratio in checks:
            row_class = "hl-row" if ratio == max_ratio else ""
            text_class = "pass-text" if ratio <= 1.0 else "fail-text"
            rows_html += f"<tr class='{row_class}'><td>{name}</td><td align='center'>{load_val:.2f}</td><td align='center'>{cap_val:.2f}</td><td align='center' class='{text_class}'>{ratio:.2f}</td></tr>"

        st.markdown(f"<table class='summary-table'><thead><tr><th>Check</th><th>Load</th><th>Cap</th><th>Ratio</th></tr></thead><tbody>{rows_html}</tbody></table>", unsafe_allow_html=True)
        st.markdown(f"<div class='load-source'>* Using Beam: <b>{selected_sec if 'Standard' in beam_source else 'Custom'}</b> (tw={beam_tw}mm)</div>", unsafe_allow_html=True)

    # ==========================
    # 5. RIGHT SECTION (TABS)
    # ==========================
    with col_result:
        tab_draw, tab_calc = st.tabs(["📐 Drawing", "📝 Full Report"])
        
        with tab_draw:
            # Drawing Logic (Pass updated beam dimensions)
            beam_dict = {'h': beam_h_mm, 'b': beam_b_mm, 'tf': beam_tf, 'tw': beam_tw}
            plate_dict = {'h': h_plate_input, 'w': w_plate_input, 't': pl_thick, 'e1': dist_weld_mm, 'lv': edge_v_mm, 'weld_size': weld_sz}
            bolt_dict = {'d': d, 'rows': n_rows, 'cols': n_cols, 's_v': pitch_v_mm, 's_h': pitch_h_mm}

            def fit_view(fig, x_range, y_range, height=450):
                fig.update_layout(height=height, margin=dict(l=10,r=10,t=30,b=10), xaxis=dict(range=x_range, visible=False, scaleanchor="y"), yaxis=dict(range=y_range, visible=False), showlegend=False)
                return fig
            
            sub_t1, sub_t2 = st.tabs(["Front View", "Side View"])
            with sub_t1:
                try:
                    fig = drawing_utils.create_front_view(beam_dict, plate_dict, bolt_dict)
                    st.plotly_chart(fit_view(fig, [-50, beam_b_mm+50], [-(beam_h_mm/2)-50, (beam_h_mm/2)+50], 500), use_container_width=True)
                except: st.error("Drawing Error")
            with sub_t2:
                try:
                    fig = drawing_utils.create_side_view(beam_dict, plate_dict, bolt_dict)
                    st.plotly_chart(fit_view(fig, [-200, 200], [-(beam_h_mm/2)-100, (beam_h_mm/2)+100], 500), use_container_width=True)
                except: pass

        with tab_calc:
            # Report Logic
            beam_data_rpt = {'tw': beam_tw, 'Fu': Fu, 'name': selected_sec if 'Standard' in beam_source else 'Custom Beam'}
            plate_data_rpt = {'t': pl_thick, 'h': h_plate_input, 'w': w_plate_input, 'e1': dist_weld_mm, 'lv': edge_v_mm, 'l_side': rem_edge_mm, 'weld_size': weld_sz, 'Fy': Fy, 'Fu': Fu}
            bolt_data_rpt = {'d': d, 'rows': n_rows, 'cols': n_cols, 'Fnv': Fnv, 's_v': pitch_v_mm, 's_h': pitch_h_mm}
            
            try:
                full_report = calculation_report.generate_report(V_kN, beam_data_rpt, plate_data_rpt, bolt_data_rpt, is_lrfd, default_mat_grade, b_grade)
                if "#### 🏁 Summary" in full_report:
                    st.markdown(full_report.split("#### 🏁 Summary")[0] + "\n\n*(Check summary dashboard on the left)*", unsafe_allow_html=True)
                else:
                    st.markdown(full_report, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Report Error: {e}")
