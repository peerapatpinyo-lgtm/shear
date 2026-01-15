import streamlit as st
import math
import plotly.graph_objects as go

# ==========================================
# HELPER: DRAWING DIMENSIONS & SHAPES (Original Code)
# ==========================================
def add_dim_line(fig, x0, y0, x1, y1, text, color="black", offset=0, type="horiz", font_size=12, bold=False):
    arrow_len = 8
    text_bg = "rgba(255, 255, 255, 0.9)" 
    font_weight = "bold" if bold else "normal"

    if type == "horiz":
        y_pos = y0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_pos, line=dict(color=color, width=0.5, dash="dot"))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_pos, line=dict(color=color, width=0.5, dash="dot"))
        fig.add_shape(type="line", x0=x0, y0=y_pos, x1=x1, y1=y_pos, line=dict(color=color, width=1.2))
        fig.add_annotation(x=x1, y=y_pos, ax=-arrow_len, ay=0, arrowcolor=color, arrowhead=2, text="")
        fig.add_annotation(x=x0, y=y_pos, ax=arrow_len, ay=0, arrowcolor=color, arrowhead=2, text="")
        fig.add_annotation(x=(x0+x1)/2, y=y_pos, text=text, showarrow=False, yshift=12 if offset>0 else -12, 
                            font=dict(color=color, size=font_size, weight=font_weight), bgcolor=text_bg)
    elif type == "vert":
        x_pos = x0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_pos, y1=y0, line=dict(color=color, width=0.5, dash="dot"))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_pos, y1=y1, line=dict(color=color, width=0.5, dash="dot"))
        fig.add_shape(type="line", x0=x_pos, y0=y0, x1=x_pos, y1=y1, line=dict(color=color, width=1.2))
        fig.add_annotation(x=x_pos, y=y1, ax=0, ay=arrow_len, arrowcolor=color, arrowhead=2, text="")
        fig.add_annotation(x=x_pos, y=y0, ax=0, ay=-arrow_len, arrowcolor=color, arrowhead=2, text="")
        fig.add_annotation(x=x_pos, y=(y0+y1)/2, text=text, showarrow=False, xshift=18 if offset>0 else -18, 
                            font=dict(color=color, size=font_size, weight=font_weight), textangle=-90, bgcolor=text_bg)

def create_ishape(h, b, tw, tf, cx=0, cy=0, fill_col="#cbd5e1", line_col="black"):
    shapes = []
    shapes.append(dict(type="rect", x0=cx-tw/2, y0=cy-h/2+tf, x1=cx+tw/2, y1=cy+h/2-tf, fillcolor=fill_col, line_width=0))
    shapes.append(dict(type="rect", x0=cx-b/2, y0=cy+h/2-tf, x1=cx+b/2, y1=cy+h/2, fillcolor=fill_col, line=dict(color=line_col, width=1.5)))
    shapes.append(dict(type="rect", x0=cx-b/2, y0=cy-h/2, x1=cx+b/2, y1=cy-h/2+tf, fillcolor=fill_col, line=dict(color=line_col, width=1.5)))
    shapes.append(dict(type="line", x0=cx-tw/2, y0=cy-h/2+tf, x1=cx-tw/2, y1=cy+h/2-tf, line=dict(color=line_col, width=1.5)))
    shapes.append(dict(type="line", x0=cx+tw/2, y0=cy-h/2+tf, x1=cx+tw/2, y1=cy+h/2-tf, line=dict(color=line_col, width=1.5)))
    return shapes

# ==========================================
# MAIN FUNCTION (UPDATED: PLATE SIDE SELECTOR & CLEARER BEAM VISUAL)
# ==========================================
def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    
    # 1. SETUP
    is_beam_to_beam = "Beam to Beam" in conn_type
    d_mm = int(bolt_size[1:]) 
    
    # Beam Dimensions
    h_beam = float(section_data.get('h', 300))
    b_beam = float(section_data.get('b', 150))
    tf_beam = float(section_data.get('tf', 10))
    tw_beam = float(section_data.get('tw', 8))
    clear_web_h = h_beam - 2*(tf_beam * 1.5) 

    st.markdown(f"### 📐 Connection Design: **{conn_type}**")

    # --- CREATE TABS ---
    tab1, tab2 = st.tabs(["📝 Design Inputs & Check", "✏️ Shop Drawing (Section A-A)"])

    # ==========================================
    # TAB 1: INPUTS & CALCULATIONS
    # ==========================================
    with tab1:
        min_pitch, min_edge = 3 * d_mm, 1.5 * d_mm
        c1, c2, c3 = st.columns(3)
        with c1:
            st.info(f"**🔩 Bolt Config ({bolt_size})**")
            n_rows = st.number_input("Rows (V)", 2, 12, 3)
            n_cols = st.number_input("Cols (H)", 1, 3, 2)
            s_v = st.number_input("Vert. Pitch (sv)", 0.0, 300.0, float(max(75, min_pitch)))
            s_h = st.number_input("Horiz. Pitch (sh)", 0.0, 150.0, float(max(60, min_pitch))) if n_cols > 1 else 0
        with c2:
            st.warning("**📏 Plate Geometry**")
            size_mode = st.radio("Size Mode", ["Auto", "Custom"], horizontal=True, label_visibility="collapsed")
            min_req_h = (n_rows - 1) * s_v + (2 * min_edge)
            l_edge_v_input = st.number_input("Vert. Edge Input (Lv)", 0.0, 100.0, float(max(40, min_edge)))
            e1_mm = st.number_input("Gap from Support (e1)", 10.0, 200.0, 50.0) # ระยะห่างจากผิวเสาถึง Bolt แถวแรก
            
            auto_h = (n_rows - 1) * s_v + (2 * l_edge_v_input)
            if size_mode == "Custom":
                plate_h = st.number_input("Plate Height (H)", min_value=float(min_req_h), max_value=float(h_beam), value=float(auto_h))
                l_side = st.number_input("Side Margin (Ls)", 20.0, 100.0, 40.0)
            else:
                plate_h, l_side = auto_h, st.number_input("Side Margin (Ls)", 20.0, 100.0, 40.0)
        with c3:
            st.success("**🧱 Material**")
            t_plate_mm = st.number_input("Plate Thickness (t_pl)", 6.0, 50.0, 10.0)
            
            real_lv = (plate_h - (n_rows-1)*s_v) / 2
            plate_w = e1_mm + (n_cols - 1) * s_h + l_side
            
            st.write(f"**Actual Lv:** {real_lv:.1f} mm")
            st.write(f"**Total W:** {plate_w:.0f} mm")

        fit_status = "CLASH" if plate_h > clear_web_h else "OK"
        n_total = n_rows * n_cols
        V_res, Design_Shear, Design_Bear = V_design/n_total, 10000, 15000 
        
        st.divider()
        c_res1, c_res2 = st.columns(2)
        with c_res1:
            if fit_status == "CLASH": st.error(f"❌ Geometry CLASH! (Plate too high)")
            else: st.success("✅ Geometry OK")
        with c_res2:
            st.metric("Bolt Shear Ratio", f"{(V_res*n_total)/Design_Shear:.2f}")

    # ==========================================
    # TAB 2: SHOP DRAWING (IMPROVED VISUAL)
    # ==========================================
    with tab2:
        st.markdown("#### 📍 Installation Layout")
        
        # Controls
        col_ctrl1, col_ctrl2 = st.columns(2)
        with col_ctrl1:
            plate_side = st.radio("ตำแหน่งเพลท (Plate Side)", ["Right of Web", "Left of Web"], horizontal=True, index=0)
        with col_ctrl2:
            eccentricity = st.slider("ขยับแนวคาน (Eccentricity)", -50, 50, 0, 5)

        st.divider()
        col_sec, col_elev = st.columns([1.3, 1])
        supp_col = "#334155" 
        
        # --- VIEW 1: SECTION A-A (TOP VIEW) ---
        with col_sec:
            st.markdown("**SECTION A-A (Top/Plan View)**")
            fig_sec = go.Figure()
            
            view_limit_y = b_beam * 1.5

            if is_beam_to_beam:
                st.warning("Preview available for Beam-to-Column only.")
            else:
                # ---------------------------------------------------------
                # COORDINATE SYSTEM:
                # Origin (0,0) = Intersection of Column Face and Column Centerline
                # X-axis = Along the Beam
                # Y-axis = Across the Column Width
                # ---------------------------------------------------------
                
                col_face_x = 0
                
                # 1. COLUMN (Fixed)
                # วาดปีกเสา (Flange) เป็นแผ่นยาวแนวตั้ง
                fig_sec.add_shape(type="rect", 
                                  x0=col_face_x - 20, y0=-view_limit_y, 
                                  x1=col_face_x, y1=view_limit_y, 
                                  fillcolor=supp_col, line_color="black")
                
                fig_sec.add_annotation(x=col_face_x-10, y=0, text="COLUMN", textangle=-90, 
                                       font=dict(color="white", weight="bold"), showarrow=False)

                # 2. BEAM (Moves with Eccentricity)
                beam_center_y = eccentricity
                
                # Beam Web Y Coordinates
                web_y_min = beam_center_y - (tw_beam / 2)
                web_y_max = beam_center_y + (tw_beam / 2)
                
                # Beam Flange Y Coordinates
                flange_y_min = beam_center_y - (b_beam / 2)
                flange_y_max = beam_center_y + (b_beam / 2)
                
                # Beam X Coordinates
                beam_start_x = col_face_x + 15 # Gap clearance (Standard ~10-15mm)
                beam_end_x = col_face_x + plate_w + 150 # Draw beam longer than plate
                
                # [DRAW] Beam Flanges (Transparent / Outline) - เพื่อให้รู้ว่าเป็น I-Beam
                # Top Flange
                fig_sec.add_shape(type="rect", x0=beam_start_x, y0=flange_y_min, x1=beam_end_x, y1=flange_y_max,
                                  line=dict(color="gray", dash="dot"), fillcolor="rgba(200,200,200,0.1)")
                
                # [DRAW] Beam Web (Solid)
                fig_sec.add_shape(type="rect", x0=beam_start_x, y0=web_y_min, x1=beam_end_x, y1=web_y_max,
                                  fillcolor="#d4d4d8", line_color="black")
                
                # Beam Centerline Label
                fig_sec.add_shape(type="line", x0=col_face_x-50, y0=beam_center_y, x1=beam_end_x, y1=beam_center_y,
                                  line=dict(color="#b91c1c", width=1, dash="dashdot"))
                fig_sec.add_annotation(x=beam_end_x, y=beam_center_y, text="CL", font=dict(color="#b91c1c", size=10), xshift=10)

                # 3. PLATE (Attached to Column, Laps with Web)
                # Determine Side
                if plate_side == "Right of Web": # Positive Y relative to Web
                    p_y_min = web_y_max
                    p_y_max = web_y_max + t_plate_mm
                    weld_y = p_y_max # Text anchor
                else: # Left of Web (Negative Y)
                    p_y_max = web_y_min
                    p_y_min = web_y_min - t_plate_mm
                    weld_y = p_y_min
                
                p_x0 = col_face_x
                p_x1 = col_face_x + plate_w
                
                # [DRAW] Plate
                fig_sec.add_shape(type="rect", x0=p_x0, y0=p_y_min, x1=p_x1, y1=p_y_max,
                                  fillcolor="#3b82f6", line_color="black", opacity=0.9)
                
                # [DRAW] Weld Symbol (Triangle at connection)
                fig_sec.add_shape(type="path", path=f"M {p_x0},{p_y_min} L {p_x0+8},{p_y_min} L {p_x0},{(p_y_min+p_y_max)/2} Z", fillcolor="black")
                fig_sec.add_shape(type="path", path=f"M {p_x0},{p_y_max} L {p_x0+8},{p_y_max} L {p_x0},{(p_y_min+p_y_max)/2} Z", fillcolor="black")
                fig_sec.add_annotation(x=p_x0+5, y=weld_y, text="Weld", showarrow=True, arrowhead=2, ax=0, ay=20 if plate_side=="Left of Web" else -20, font=dict(size=10))

                # 4. BOLTS (Pass through Plate & Web only)
                bolt_start_x = col_face_x + e1_mm
                
                for c in range(n_cols):
                    bx = bolt_start_x + c*s_h
                    
                    # Bolt Shank (Red) - From outer face of Plate to outer face of Web
                    shank_y0 = min(p_y_min, web_y_min)
                    shank_y1 = max(p_y_max, web_y_max)
                    
                    fig_sec.add_shape(type="rect", x0=bx-d_mm/2, y0=shank_y0, x1=bx+d_mm/2, y1=shank_y1,
                                      fillcolor="#b91c1c", line_width=0)
                    
                    # Bolt Heads/Nuts (Dark Red)
                    head_h = d_mm * 0.6
                    # Side 1 (Plate Side)
                    h1_y_start = p_y_max if plate_side == "Right of Web" else p_y_min - head_h
                    h1_y_end = p_y_max + head_h if plate_side == "Right of Web" else p_y_min
                    fig_sec.add_shape(type="rect", x0=bx-d_mm, y0=h1_y_start, x1=bx+d_mm, y1=h1_y_end, fillcolor="#7f1d1d", line_color="black")
                    
                    # Side 2 (Web Side)
                    h2_y_start = web_y_min - head_h if plate_side == "Right of Web" else web_y_max
                    h2_y_end = web_y_min if plate_side == "Right of Web" else web_y_max + head_h
                    fig_sec.add_shape(type="rect", x0=bx-d_mm, y0=h2_y_start, x1=bx+d_mm, y1=h2_y_end, fillcolor="#7f1d1d", line_color="black")

                    # Centerline for Bolt
                    fig_sec.add_shape(type="line", x0=bx, y0=flange_y_min, x1=bx, y1=flange_y_max, line=dict(color="black", width=0.5, dash="dot"))

                # DIMENSIONS
                dim_y = view_limit_y - 20
                add_dim_line(fig_sec, p_x0, dim_y, p_x1, dim_y, f"Plate W={plate_w:.0f}", offset=0)
                add_dim_line(fig_sec, p_x0, dim_y-25, p_x0+e1_mm, dim_y-25, f"e1", color="#d97706", offset=0)
                
                # Thickness dims
                thk_x = beam_end_x + 20
                add_dim_line(fig_sec, thk_x, web_y_min, thk_x, web_y_max, "tw", type="vert")
                add_dim_line(fig_sec, thk_x, p_y_min, thk_x, p_y_max, "tpl", type="vert")

            layout_sec = dict(height=450, plot_bgcolor="white", 
                              margin=dict(l=20, r=20, t=40, b=20), 
                              title=dict(text="SECTION A-A (TOP VIEW)", x=0.5),
                              xaxis=dict(visible=False, fixedrange=False),
                              yaxis=dict(visible=False, fixedrange=False, scaleanchor="x", scaleratio=1))
            
            fig_sec.update_layout(**layout_sec)
            st.plotly_chart(fig_sec, use_container_width=True)

        # --- VIEW 2: ELEVATION (SIDE VIEW) ---
        with col_elev:
            st.markdown("**ELEVATION (Side View)**")
            fig_elev = go.Figure()
            
            # Draw Beam (Side Profile)
            fig_elev.add_shape(type="rect", x0=0, y0=-h_beam/2, x1=plate_w+150, y1=h_beam/2, line_color="gray", fillcolor="white")
            # Flanges lines
            fig_elev.add_shape(type="line", x0=0, y0=-h_beam/2+tf_beam, x1=plate_w+150, y1=-h_beam/2+tf_beam, line_color="gray")
            fig_elev.add_shape(type="line", x0=0, y0=h_beam/2-tf_beam, x1=plate_w+150, y1=h_beam/2-tf_beam, line_color="gray")
            
            # Draw Plate (Side Profile)
            fig_elev.add_shape(type="rect", x0=0, y0=-plate_h/2, x1=plate_w, y1=plate_h/2, 
                               line_color="#3b82f6", fillcolor="rgba(59, 130, 246, 0.2)", line_width=2)
            
            # Draw Column Edge (Left)
            fig_elev.add_shape(type="rect", x0=-20, y0=-h_beam/2-50, x1=0, y1=h_beam/2+50, fillcolor=supp_col, line_color="black")
            
            # Bolts
            b_start_x = e1_mm
            b_start_y = (plate_h/2) - real_lv 
            
            for r in range(n_rows):
                for c in range(n_cols):
                    bx = b_start_x + c*s_h
                    by = b_start_y - r*s_v
                    fig_elev.add_trace(go.Scatter(x=[bx], y=[by], mode='markers', marker=dict(size=10, color='#b91c1c'), showlegend=False))
                    # Crosshair
                    fig_elev.add_shape(type="line", x0=bx-6, y0=by, x1=bx+6, y1=by, line_color="white", line_width=1)
                    fig_elev.add_shape(type="line", x0=bx, y0=by-6, x1=bx, y1=by+6, line_color="white", line_width=1)

            # Dims
            add_dim_line(fig_elev, plate_w+30, -plate_h/2, plate_w+30, plate_h/2, f"H={plate_h:.0f}", type="vert", color="#1e40af")
            add_dim_line(fig_elev, 0, -h_beam/2-30, plate_w, -h_beam/2-30, f"W={plate_w:.0f}", type="horiz", color="#1e40af")

            fig_elev.update_layout(height=450, plot_bgcolor="white", 
                                   xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1),
                                   title=dict(text="ELEVATION VIEW", x=0.5))
            st.plotly_chart(fig_elev, use_container_width=True)

    return n_total, Design_Shear

    return n_total, Design_Shear
