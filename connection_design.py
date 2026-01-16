import streamlit as st
import math
import plotly.graph_objects as go
import drawing_utils        # Drawing Logic
import calculation_report   # The V13 Report File you provided

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
    # 1. INPUT SECTION
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

        # --- 1.2 Geometry Control ---
        st.markdown('<div class="input-card">', unsafe_allow_html=True)
        st.markdown("**2. Plate Geometry & Layout**")
        
        c_w, c_h = st.columns(2)
        w_plate_input = c_w.number_input("Plate Width (mm)", 50, 500, 150, step=10)
        h_plate_input = c_h.number_input("Plate Height (mm)", 50, 1000, 300, step=10)
        
        st.markdown("---")
        
        col_r, col_c = st.columns(2)
        n_rows = col_r.number_input("Rows", 1, 10, 3)
        n_cols = col_c.number_input("Cols", 1, 4, 1)
        
        st.caption("📍 Spacing & Edge Distance (mm)")
        v1, v2 = st.columns(2)
        pitch_v_mm = v1.number_input("Pitch V", 30, 200, 75, step=5)
        edge_v_mm = v2.number_input("Edge V", 20, 100, 40, step=5)
        
        h1, h2 = st.columns(2)
        dist_weld_mm = h1.number_input("To Weld (e1)", 20, 100, 50, step=5)
        pitch_h_mm = 0
        if n_cols > 1:
            pitch_h_mm = h2.number_input("Pitch H", 30, 200, 60, step=5)
        else:
            h2.text_input("Pitch H", "-", disabled=True)

        # Validation (Calculations in mm/cm for internal check)
        w_plate = w_plate_input / 10
        h_plate = h_plate_input / 10
        pitch_v = pitch_v_mm / 10
        edge_v = edge_v_mm / 10
        dist_weld = dist_weld_mm / 10
        pitch_h = pitch_h_mm / 10
        
        req_h = (n_rows - 1) * pitch_v + (2 * edge_v)
        check_h = h_plate >= req_h
        req_w_bolts = dist_weld + (max(0, n_cols - 1) * pitch_h)
        rem_edge_mm = w_plate_input - (req_w_bolts * 10) # This is 'l_side'
        
        st.markdown(f"""
        <div style="font-size:13px; margin-top:5px;">
            <div>↕️ Height: <span class="dim-check {'dim-ok' if check_h else 'dim-err'}">{'OK' if check_h else 'Too Short'}</span></div>
            <div style="margin-top:4px;">↔️ e2 (Side): <span class="dim-check {'dim-ok' if rem_edge_mm >= 20 else 'dim-err'}">{rem_edge_mm:.1f} mm</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Internal ksc for quick check bar
        fy_ksc = 2500 if "A36" in default_mat_grade or "SS400" in default_mat_grade else 3500
        fu_ksc = 4000 if fy_ksc == 2500 else 4900

    # ==========================
    # 2. QUICK CHECK (Internal Logic - kg)
    # ==========================
    # (ใช้ Logic เดิมคำนวณคร่าวๆ เพื่อแสดง Progress Bar เร็วๆ)
    Ab_cm = math.pi * (d_bolt**2) / 4
    Fnv_ksc = 3720 if "A325" in b_grade else 4690
    Rn_shear = (n_rows * n_cols) * Fnv_ksc * Ab_cm
    cap_shear = (0.75 * Rn_shear) if is_lrfd else (Rn_shear / 1.5)
    
    # Simple Ratio for UI
    ratio_approx = V_design_from_tab1 / cap_shear if cap_shear > 0 else 999
    is_pass = ratio_approx <= 1.0

    # ==========================
    # 3. OUTPUT
    # ==========================
    with col_result:
        # Status Box
        status_color = "#22c55e" if is_pass else "#ef4444"
        st.markdown(f"""
        <div style="background:{status_color}; color:white; padding:10px 15px; border-radius:5px; margin-bottom:15px; display:flex; justify-content:space-between; align-items:center;">
            <span style="font-weight:bold; font-size:18px;">{'PROBABLE PASS ✅' if is_pass else 'CHECK DETAILS ⚠️'}</span>
            <span>Approx Ratio: <b>{ratio_approx:.2f}</b></span>
        </div>
        """, unsafe_allow_html=True)

        tab_draw, tab_calc = st.tabs(["📐 Drawing & Dims", "📝 Calculation Report"])
        
        # --- TAB 1: DRAWING ---
        with tab_draw:
            beam_h_mm = section_data.get('h', 400)
            beam_b_mm = section_data.get('b', 200)
            
            beam_dict = {
                'h': beam_h_mm, 'b': beam_b_mm,
                'tf': section_data.get('tf', 13), 'tw': section_data.get('tw', 8)
            }
            plate_dict = {
                'h': h_plate_input, 'w': w_plate_input, 't': pl_thick,
                'e1': dist_weld_mm, 'lv': edge_v_mm, 'weld_size': weld_sz
            }
            bolt_dict = {
                'd': d_bolt * 10, 'rows': n_rows, 'cols': n_cols,
                's_v': pitch_v_mm, 's_h': pitch_h_mm
            }

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
                except: st.error("Drawing Error")
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

        # --- TAB 2: CALCULATION REPORT ---
        with tab_calc:
            # 1. PREPARE DATA FOR REPORT (Unit Conversion)
            # Report expects: V_load (kN), Dimensions (mm), Stress (MPa)
            
            # Load: kg -> kN
            V_kN = V_design_from_tab1 / 101.97 
            
            # Material: ksc -> MPa
            Fy_MPa = 250 if fy_ksc == 2500 else 345
            Fu_MPa = 400 if fy_ksc == 2500 else 490 # Simplification for A572
            
            # Bolt: ksc -> MPa
            Fnv_MPa = 372 if "A325" in b_grade else 457 # A325=372MPa, A490=457MPa
            
            # Dictionary Packing
            plate_data_rpt = {
                't': pl_thick,          # mm
                'h': h_plate_input,     # mm
                'w': w_plate_input,     # mm
                'lv': edge_v_mm,        # mm (vertical edge)
                'l_side': rem_edge_mm,  # mm (horizontal edge / e2)
                'weld_size': weld_sz,   # mm
                'Fy': Fy_MPa,           # MPa
                'Fu': Fu_MPa            # MPa
            }
            
            bolt_data_rpt = {
                'd': d_bolt * 10,       # cm -> mm
                'rows': n_rows,
                'cols': n_cols,
                'Fnv': Fnv_MPa,         # MPa
                's_v': pitch_v_mm       # mm
            }
            
            # 2. GENERATE REPORT
            try:
                report_md = calculation_report.generate_report(
                    V_load=V_kN,
                    beam=None, # Not used in V13 report logic
                    plate=plate_data_rpt,
                    bolts=bolt_data_rpt,
                    is_lrfd=is_lrfd,
                    material_grade=default_mat_grade,
                    bolt_grade=b_grade
                )
                st.markdown(report_md, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Report Generation Error: {e}")
