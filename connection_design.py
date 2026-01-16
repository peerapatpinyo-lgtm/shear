import streamlit as st
import math
import plotly.graph_objects as go
import drawing_utils        # ต้องมีไฟล์ drawing_utils.py
import calculation_report   # ต้องมีไฟล์ calculation_report.py (ที่แก้เป็น Phase 1 แล้ว)

def render_connection_tab(V_design_from_tab1, default_bolt_size, method, is_lrfd, section_data, conn_type, default_bolt_grade, default_mat_grade):
    
    # --- STYLE & CSS ---
    st.markdown("""
    <style>
        .input-card { background-color: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 15px; }
        .dim-check { font-weight: bold; padding: 4px 8px; border-radius: 4px; font-size: 13px; display: inline-block; margin-top: 5px;}
        .dim-ok { background-color: #dcfce7; color: #166534; }
        .dim-err { background-color: #fee2e2; color: #991b1b; }
        
        /* Summary Table Style */
        .summary-table { font-size: 13px; width: 100%; border-collapse: collapse; margin-top: 5px; }
        .summary-table th { background-color: #f1f5f9; padding: 6px; border-bottom: 2px solid #cbd5e1; font-weight: bold; color: #334155; }
        .summary-table td { padding: 6px; border-bottom: 1px solid #e2e8f0; vertical-align: middle; }
        .pass-text { color: #166534; font-weight: bold; }
        .fail-text { color: #991b1b; font-weight: bold; }
        .hl-row { background-color: #fff7ed; } /* Warning highlight for governing case */
        .load-source { font-size: 11px; color: #64748b; font-style: italic; margin-top: 4px; display: block; }
    </style>
    """, unsafe_allow_html=True)

    # --- HEADER ---
    col_head1, col_head2 = st.columns([2, 1])
    with col_head1:
        st.markdown(f"### 🔩 {conn_type} Design (Phase 1: Advanced)")
        st.caption(f"Beam: **{section_data.get('name', 'Custom Section')}** | Method: **{method}**")
    with col_head2:
        st.info(f"⚡ Design Load ($V_u$): **{V_design_from_tab1:,.0f} kg**")
    st.divider()

    col_input, col_result = st.columns([1, 1.4], gap="medium")

    # ==========================
    # 1. INPUT SECTION (LEFT)
    # ==========================
    with col_input:
        st.markdown("#### 🛠️ Configuration")
        
        # --- 1.1 Bolt, Material & Beam Web ---
        with st.expander("1. Material & Specs", expanded=True):
            # Bolt Size
            c1, c2 = st.columns(2)
            size_map = {"M12": 1.2, "M16": 1.6, "M20": 2.0, "M22": 2.2, "M24": 2.4, "M27": 2.7}
            try: def_idx = list(size_map.keys()).index(default_bolt_size)
            except: def_idx = 2
            b_size_str = c1.selectbox("Bolt Size", list(size_map.keys()), index=def_idx)
            d_bolt = size_map[b_size_str] # cm
            
            # Bolt Grade
            b_grade = c2.selectbox("Bolt Grade", ["A325", "Gr. 8.8", "A490"])
            
            # Plate & Beam Web
            c3, c4 = st.columns(2)
            pl_thick = c3.select_slider("Plate T (mm)", options=[6, 9, 10, 12, 16, 19, 20, 25], value=10)
            
            # New: Beam Web Input for Check
            def_tw = section_data.get('tw', 8)
            beam_tw = c4.number_input("Beam Web t (mm)", 3.0, 30.0, float(def_tw), step=0.5, help="Crucial for Bearing Check on Beam Side")
            
            weld_sz = st.number_input("Weld Size (mm)", 3, 12, 6)

        # --- 1.2 Geometry Control ---
        st.markdown('<div class="input-card">', unsafe_allow_html=True)
        st.markdown("**2. Geometry & Layout**")
        
        c_w, c_h = st.columns(2)
        w_plate_input = c_w.number_input("Plate Width (mm)", 50, 500, 150, step=10)
        h_plate_input = c_h.number_input("Plate Height (mm)", 50, 1000, 300, step=10)
        
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
        pitch_v = pitch_v_mm / 10
        edge_v = edge_v_mm / 10
        dist_weld = dist_weld_mm / 10
        pitch_h = pitch_h_mm / 10
        
        req_h = (n_rows - 1) * pitch_v + (2 * edge_v)
        check_h = (h_plate_input/10) >= req_h
        req_w_bolts = dist_weld + (max(0, n_cols - 1) * pitch_h)
        rem_edge_mm = w_plate_input - (req_w_bolts * 10)
        
        st.markdown(f"""
        <div style="font-size:13px; margin-top:5px;">
            <div>↕️ Height: <span class="dim-check {'dim-ok' if check_h else 'dim-err'}">{'OK' if check_h else 'Too Short (Min '+str(req_h*10)+'mm)'}</span></div>
            <div style="margin-top:4px;">↔️ Side Edge: <span class="dim-check {'dim-ok' if rem_edge_mm >= 20 else 'dim-err'}">{rem_edge_mm:.1f} mm</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ==========================================
        # 3. PRE-CALCULATION (ADVANCED: ELASTIC METHOD)
        # ==========================================
        # 3.1 Unit & Material Setup
        conversion_factor = 101.97
        V_kN = V_design_from_tab1 / conversion_factor
        
        # Standard Properties
        fy_ksc = 2500 if "A36" in default_mat_grade or "SS400" in default_mat_grade else 3500
        Fy = 250 if fy_ksc == 2500 else 345 # MPa
        Fu = 400 if fy_ksc == 2500 else 490 # MPa
        Fnv = 372 if "A325" in b_grade else 457 # MPa
        Fexx = 480 # MPa
        
        # Factors (ASD/LRFD)
        if is_lrfd:
            phi_v, phi_y, phi_r, phi_w = 0.75, 1.00, 0.75, 0.75
            def get_cap(Rn, type_f): return Rn * type_f
        else:
            om_v, om_y, om_r, om_w = 2.00, 1.50, 2.00, 2.00
            def get_cap(Rn, type_f): return Rn / type_f

        # --- 3.2 Advanced Bolt Analysis (Eccentricity) ---
        d = d_bolt * 10 # mm
        Ab = math.pi * d**2 / 4
        n_total = n_rows * n_cols
        
        # 1. Centroid & Eccentricity
        x_bar = ((n_cols - 1) * pitch_h_mm) / 2 if n_cols > 1 else 0
        eccentricity = dist_weld_mm + x_bar
        Moment = V_kN * eccentricity # kN-mm
        
        # 2. Polar Moment of Inertia (Sum r^2)
        sum_r2 = 0
        # Assume centroid at (0,0) locally
        row_start = -((n_rows - 1) * pitch_v_mm) / 2
        col_start = -x_bar
        for c in range(n_cols):
            for r in range(n_rows):
                dx = col_start + (c * pitch_h_mm)
                dy = row_start + (r * pitch_v_mm)
                sum_r2 += (dx**2 + dy**2)
        
        # 3. Forces on Critical Bolt
        # Direct Shear
        Rv_direct = V_kN / n_total
        # Moment Shear (Elastic)
        crit_x = x_bar # Max distance X
        crit_y = ((n_rows - 1) * pitch_v_mm) / 2 # Max distance Y
        
        if sum_r2 > 0:
            Rv_moment = (Moment * crit_x) / sum_r2 # Vertical comp
            Rh_moment = (Moment * crit_y) / sum_r2 # Horizontal comp
        else:
            Rv_moment, Rh_moment = 0, 0
            
        # Resultant Force
        V_resultant = math.sqrt((Rv_direct + Rv_moment)**2 + Rh_moment**2)
        
        # --- 3.3 CAPACITIES ---
        
        # 1. Bolt Shear Check (Compare V_resultant vs Cap)
        Rn_shear = (Fnv * Ab) / 1000 # kN per bolt
        cap_bolt_single = get_cap(Rn_shear, phi_v if is_lrfd else om_v)
        
        # 2. Bearing Check (Check BOTH Plate and Beam Web)
        # Plate
        Rn_br_pl = (2.4 * d * pl_thick * Fu) / 1000
        cap_br_pl = get_cap(Rn_br_pl, phi_v if is_lrfd else om_v)
        # Beam Web (New Phase 1)
        Rn_br_wb = (2.4 * d * beam_tw * Fu) / 1000 
        cap_br_wb = get_cap(Rn_br_wb, phi_v if is_lrfd else om_v)
        
        cap_br_gov = min(cap_br_pl, cap_br_wb)
        
        # 3. Plate Checks (Yield/Rupture) - Use Total V_kN
        Ag = h_plate_input * pl_thick
        Rn_y = (0.60 * Fy * Ag) / 1000
        cap_yld = get_cap(Rn_y, phi_y if is_lrfd else om_y)
        
        h_hole = d + 2
        An = (h_plate_input - (n_rows * h_hole)) * pl_thick
        Rn_r = (0.60 * Fu * An) / 1000
        cap_rup = get_cap(Rn_r, phi_r if is_lrfd else om_r)
        
        # 4. Block Shear
        l_gv = (n_rows - 1) * pitch_v_mm + edge_v_mm
        agv = l_gv * pl_thick
        anv = (l_gv - (n_rows - 0.5) * h_hole) * pl_thick
        ant = (rem_edge_mm - 0.5 * h_hole) * pl_thick
        rn_blk = min(0.6*Fu*anv + 1.0*Fu*ant, 0.6*Fy*agv + 1.0*Fu*ant) / 1000
        cap_blk = get_cap(rn_blk, phi_r if is_lrfd else om_r)
        
        # 5. Weld
        l_weld = h_plate_input * 2
        rn_weld = (0.6 * Fexx * 0.707 * weld_sz * l_weld) / 1000
        cap_weld = get_cap(rn_weld, phi_w if is_lrfd else om_w)

        # 3.4 Summary Logic (Ratios)
        # For Bolt & Bearing, we use V_resultant per bolt
        ratio_bolt = V_resultant / cap_bolt_single
        ratio_bear = V_resultant / cap_br_gov
        
        # For Plate/Weld, we use Total V_kN
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
        status_msg = "PASS ✅" if is_pass else "FAIL ❌"
        
        st.markdown(f"""
        <div style="background:{status_bg}; color:{status_txt}; padding:10px; border-radius:6px; margin-bottom:10px; text-align:center; font-weight:bold;">
            {status_msg} (Max Ratio: {max_ratio:.2f})
        </div>
        """, unsafe_allow_html=True)
        
        # List of checks for display
        # Name, Load to Show, Capacity, Ratio
        checks = [
            ("Bolt Shear (Elastic)", V_resultant, cap_bolt_single, ratio_bolt),
            ("Bearing (Web/Plate)", V_resultant, cap_br_gov, ratio_bear),
            ("Plate Yield", V_kN, cap_yld, ratio_yld),
            ("Plate Rupture", V_kN, cap_rup, ratio_rup),
            ("Block Shear", V_kN, cap_blk, ratio_blk),
            ("Weld Strength", V_kN, cap_weld, ratio_weld)
        ]
        
        rows_html = ""
        for name, load_val, cap_val, ratio in checks:
            is_governing = (ratio == max_ratio)
            row_class = "hl-row" if is_governing else ""
            text_class = "pass-text" if ratio <= 1.0 else "fail-text"
            icon = "⚠️" if ratio > 1.0 else ""
            
            rows_html += f"""<tr class='{row_class}'>
                <td>{name} {icon}</td>
                <td style='text-align:center;'>{load_val:.2f}</td>
                <td style='text-align:center;'>{cap_val:.2f}</td>
                <td style='text-align:center;' class='{text_class}'>{ratio:.2f}</td>
            </tr>"""

        st.markdown(f"""
        <table class="summary-table">
            <thead>
                <tr>
                    <th style='text-align:left'>Check List</th>
                    <th style='text-align:center'>Load ($V_u$/$R_u$)</th>
                    <th style='text-align:center'>Cap. (kN)</th>
                    <th style='text-align:center'>Ratio</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
        <div class="load-source">
            * <b>Note:</b> Bolt & Bearing loads ($R_u$) include moment effects (Elastic Method).
        </div>
        """, unsafe_allow_html=True)

    # ==========================
    # 5. RIGHT SECTION (TABS)
    # ==========================
    with col_result:
        tab_draw, tab_calc = st.tabs(["📐 Drawing", "📝 Full Report"])
        
        with tab_draw:
            # --- DRAWING LOGIC ---
            beam_h_mm = section_data.get('h', 400)
            beam_b_mm = section_data.get('b', 200)
            # Pass beam_tw to drawing (if needed)
            beam_dict = {'h': beam_h_mm, 'b': beam_b_mm, 'tf': section_data.get('tf', 13), 'tw': beam_tw}
            plate_dict = {'h': h_plate_input, 'w': w_plate_input, 't': pl_thick, 'e1': dist_weld_mm, 'lv': edge_v_mm, 'weld_size': weld_sz}
            bolt_dict = {'d': d, 'rows': n_rows, 'cols': n_cols, 's_v': pitch_v_mm, 's_h': pitch_h_mm}

            # Helper for Dims
            def add_manual_dims(fig, view_type, p_data, b_data):
                annot_color = "#0369a1"
                def draw_dim_line(x0, y0, x1, y1, text, offset_x=0, offset_y=0):
                    fig.add_shape(type="line", x0=x0, y0=y0, x1=x1, y1=y1, line=dict(color=annot_color, width=1))
                    tick_len = 5
                    if x0 == x1: # Vert
                        fig.add_shape(type="line", x0=x0-tick_len, y0=y0, x1=x0+tick_len, y1=y0, line=dict(color=annot_color, width=1))
                        fig.add_shape(type="line", x0=x1-tick_len, y0=y1, x1=x1+tick_len, y1=y1, line=dict(color=annot_color, width=1))
                        text_angle = -90
                    else: # Horiz
                        fig.add_shape(type="line", x0=x0, y0=y0-tick_len, x1=x0, y1=y0+tick_len, line=dict(color=annot_color, width=1))
                        fig.add_shape(type="line", x0=x1, y0=y1-tick_len, x1=x1, y1=y1+tick_len, line=dict(color=annot_color, width=1))
                        text_angle = 0
                    mid_x, mid_y = (x0+x1)/2, (y0+y1)/2
                    fig.add_annotation(x=mid_x + offset_x, y=mid_y + offset_y, text=f"<b>{text}</b>", showarrow=False,
                                       font=dict(size=10, color=annot_color), bgcolor="rgba(255,255,255,0.8)", textangle=text_angle)

                if view_type == "front":
                    y_ref = (p_data['h']/2) + 20
                    x_start = 0
                    x_bolt1 = p_data['e1']
                    draw_dim_line(x_start, y_ref, x_bolt1, y_ref, f"{p_data['e1']}", 0, 10)
                    curr_x = x_bolt1
                    if b_data['cols'] > 1:
                        total_pitch = (b_data['cols']-1) * b_data['s_h']
                        draw_dim_line(curr_x, y_ref, curr_x + total_pitch, y_ref, f"{b_data['cols']-1}@{b_data['s_h']}", 0, 10)
                        curr_x += total_pitch
                    x_end = p_data['w']
                    draw_dim_line(curr_x, y_ref, x_end, y_ref, f"{x_end-curr_x:.0f}", 0, 10)
                return fig
            
            def fit_view(fig, x_range, y_range, height=450):
                fig.update_layout(height=height, margin=dict(l=10,r=10,t=30,b=10),
                                  xaxis=dict(range=x_range, visible=False, scaleanchor="y", scaleratio=1),
                                  yaxis=dict(range=y_range, visible=False), dragmode="pan", showlegend=False)
                return fig
            
            sub_t1, sub_t2, sub_t3 = st.tabs(["Front", "Top", "Side"])
            pad = 50
            with sub_t1:
                try:
                    fig = drawing_utils.create_front_view(beam_dict, plate_dict, bolt_dict)
                    fig = add_manual_dims(fig, "front", plate_dict, bolt_dict)
                    st.plotly_chart(fit_view(fig, [-pad, beam_b_mm+pad], [-(beam_h_mm/2)-pad, (beam_h_mm/2)+pad+40], 500), use_container_width=True)
                except: st.error("Drawing Error: Please check inputs")
            with sub_t2:
                try:
                    fig = drawing_utils.create_plan_view(beam_dict, plate_dict, bolt_dict)
                    st.plotly_chart(fit_view(fig, [-(beam_b_mm/2)-pad, (beam_b_mm/2)+pad], [-150, 250], 400), use_container_width=True)
                except: pass
            with sub_t3:
                try:
                    fig = drawing_utils.create_side_view(beam_dict, plate_dict, bolt_dict)
                    st.plotly_chart(fit_view(fig, [-250, 250], [-(beam_h_mm/2)-100, (beam_h_mm/2)+100], 500), use_container_width=True)
                except: pass

        with tab_calc:
            # Prepare Data for Report (Ensure Beam Web 'tw' is included)
            beam_data_rpt = {
                'tw': beam_tw,  # <--- Important Phase 1 Update
                'Fu': Fu
            }
            plate_data_rpt = {
                't': pl_thick, 'h': h_plate_input, 'w': w_plate_input,
                'e1': dist_weld_mm, # Need for eccentricity calc
                'lv': edge_v_mm, 'l_side': rem_edge_mm, 'weld_size': weld_sz,
                'Fy': Fy, 'Fu': Fu
            }
            bolt_data_rpt = {
                'd': d, 'rows': n_rows, 'cols': n_cols,
                'Fnv': Fnv, 's_v': pitch_v_mm, 's_h': pitch_h_mm
            }
            
            try:
                # Generate Report
                full_report = calculation_report.generate_report(
                    V_load=V_kN, 
                    beam=beam_data_rpt, 
                    plate=plate_data_rpt, 
                    bolts=bolt_data_rpt,
                    is_lrfd=is_lrfd, 
                    material_grade=default_mat_grade, 
                    bolt_grade=b_grade
                )
                
                # Render Report
                # Cut duplicate summary if present in text, otherwise show all
                if "#### 🏁 Summary" in full_report:
                    report_body = full_report.split("#### 🏁 Summary")[0]
                    report_body += "\n\n*(Please refer to the dashboard summary on the left)*"
                    st.markdown(report_body, unsafe_allow_html=True)
                else:
                    st.markdown(full_report, unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"Report Generation Error: {e}")
