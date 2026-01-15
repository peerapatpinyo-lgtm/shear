import streamlit as st
import math
import plotly.graph_objects as go

# ==========================================
# HELPER: DRAWING DIMENSIONS & SHAPES
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

# ==========================================
# MAIN FUNCTION (ENGINEERING CORRECTED: ROTATED 90 DEG)
# ==========================================
def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    
    # 1. SETUP & DATA RETRIEVAL
    is_beam_to_beam = "Beam to Beam" in conn_type
    d_mm = int(bolt_size[1:]) 
    
    # Beam Sections
    h_beam = float(section_data.get('h', 300)) # Depth
    b_beam = float(section_data.get('b', 150)) # Flange Width
    tf_beam = float(section_data.get('tf', 10))
    tw_beam = float(section_data.get('tw', 8))
    clear_web_h = h_beam - 2*(tf_beam * 1.5) 

    st.markdown(f"### 📐 Connection Design: **{conn_type}**")

    # --- TABS ---
    tab1, tab2 = st.tabs(["📝 Design Inputs & Check", "✏️ Shop Drawing (Engineering Detail)"])

    # ==========================================
    # TAB 1: INPUTS
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
            e1_mm = st.number_input("Gap from Support (e1)", 10.0, 200.0, 50.0)
            
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
            plate_w = e1_mm + (n_cols - 1) * s_h + l_side # ความกว้างแผ่น (แนวนอน)
            
            st.write(f"**Lv (Edge V):** {real_lv:.1f} mm")
            st.write(f"**Plate Width (W):** {plate_w:.0f} mm")

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
    # TAB 2: SHOP DRAWING (ROTATED 90 DEG - CORRECT VIEW)
    # ==========================================
    with tab2:
        st.markdown("#### 📍 Connection Detail")
        
        c_ctrl1, c_ctrl2 = st.columns(2)
        with c_ctrl1:
            plate_side = st.radio("ตำแหน่งเพลท", ["Right of Web", "Left of Web"], horizontal=True, label_visibility="collapsed")
        with c_ctrl2:
            eccentricity = st.slider("Eccentricity (e)", -50, 50, 0, 5, help="การเยื้องศูนย์ของคาน")

        st.divider()
        col_sec, col_elev = st.columns([1, 1])
        supp_col = "#334155" 
        
        # =========================================================
        # VIEW 1: SECTION A-A (TOP VIEW - ROTATED VERTICALLY)
        # =========================================================
        with col_sec:
            st.markdown("**SECTION A-A (Top View)**")
            fig_sec = go.Figure()
            
            # --- Coordinates Setup ---
            # Column Face is at Y = 0
            # Beam Center is at X = eccentricity
            
            beam_cx = eccentricity
            
            # 1. COLUMN (Flange) - Placed at Bottom (Y <= 0)
            col_width_viz = max(b_beam * 1.5, 200)
            fig_sec.add_shape(type="rect", 
                              x0=-col_width_viz/2, y0=-20, 
                              x1=col_width_viz/2, y1=0, 
                              fillcolor=supp_col, line_color="black")
            fig_sec.add_annotation(x=0, y=-10, text="COLUMN FLANGE", font=dict(color="white", size=10), showarrow=False)

            # 2. BEAM (Projecting UPWARDS, Y > 0)
            beam_len_viz = plate_w + 100
            
            # Beam Web (Vertical Strip in this view)
            web_x0 = beam_cx - tw_beam/2
            web_x1 = beam_cx + tw_beam/2
            fig_sec.add_shape(type="rect", 
                              x0=web_x0, y0=10, 
                              x1=web_x1, y1=beam_len_viz, 
                              fillcolor="#d4d4d8", line_color="black")
            
            # Beam Flanges (Outlines)
            flange_x0 = beam_cx - b_beam/2
            flange_x1 = beam_cx + b_beam/2
            fig_sec.add_shape(type="rect", x0=flange_x0, y0=10, x1=flange_x1, y1=beam_len_viz, line=dict(color="gray", dash="dot"))
            
            # Centerline (Vertical)
            fig_sec.add_shape(type="line", x0=beam_cx, y0=-30, x1=beam_cx, y1=beam_len_viz, line=dict(color="#b91c1c", width=1, dash="dashdot"))

            # 3. FIN PLATE (Vertical Strip next to Web)
            if plate_side == "Right of Web":
                px0, px1 = web_x1, web_x1 + t_plate_mm
            else:
                px0, px1 = web_x0 - t_plate_mm, web_x0
            
            py0, py1 = 0, plate_w 
            
            # Draw Plate
            fig_sec.add_shape(type="rect", x0=px0, y0=py0, x1=px1, y1=py1, fillcolor="#3b82f6", line_color="black", opacity=0.9)
            
            # Weld Symbol
            fig_sec.add_annotation(x=px1 if plate_side=="Right of Web" else px0, y=5, text="Weld", 
                                   ax=20 if plate_side=="Right of Web" else -20, ay=0, showarrow=True, arrowhead=2, font=dict(size=9))

            # 4. BOLTS
            bolt_start_y = e1_mm
            
            for c in range(n_cols):
                by = bolt_start_y + c*s_h 
                
                # Bolt Shank
                sx0 = min(px0, web_x0)
                sx1 = max(px1, web_x1)
                fig_sec.add_shape(type="rect", x0=sx0, y0=by-d_mm/2, x1=sx1, y1=by+d_mm/2, fillcolor="#b91c1c", line_width=0)
                
                # Heads
                head_h = d_mm * 0.6
                # Plate Side Head
                h1_x0 = px1 if plate_side == "Right of Web" else px0 - head_h
                h1_x1 = px1 + head_h if plate_side == "Right of Web" else px0
                fig_sec.add_shape(type="rect", x0=h1_x0, y0=by-d_mm, x1=h1_x1, y1=by+d_mm, fillcolor="#7f1d1d", line_color="black")
                
                # Web Side Head
                h2_x0 = web_x0 - head_h if plate_side == "Right of Web" else web_x1
                h2_x1 = web_x0 if plate_side == "Right of Web" else web_x1 + head_h
                fig_sec.add_shape(type="rect", x0=h2_x0, y0=by-d_mm, x1=h2_x1, y1=by+d_mm, fillcolor="#7f1d1d", line_color="black")
                
                # CL Bolt
                fig_sec.add_shape(type="line", x0=flange_x0, y0=by, x1=flange_x1, y1=by, line=dict(color="black", width=0.5, dash="dot"))

            # Dimensions (Rotated)
            dim_x_right = max(flange_x1, px1) + 20
            add_dim_line(fig_sec, dim_x_right, 0, dim_x_right, plate_w, f"W={plate_w:.0f}", type="vert", offset=0)
            add_dim_line(fig_sec, dim_x_right, 0, dim_x_right, e1_mm, "e1", type="vert", color="#d97706", offset=-15)

            # View Settings
            fig_sec.update_layout(
                height=380, margin=dict(l=10, r=10, t=30, b=10), plot_bgcolor="white",
                xaxis=dict(visible=False, fixedrange=True, range=[beam_cx-b_beam/1.5, beam_cx+b_beam/1.5]),
                yaxis=dict(visible=False, scaleanchor="x", scaleratio=1, fixedrange=True, range=[-30, beam_len_viz]),
                title=dict(text="SECTION A-A (TOP)", x=0.5, font=dict(size=12))
            )
            st.plotly_chart(fig_sec, use_container_width=True)

        # =========================================================
        # VIEW 2: ELEVATION (SIDE VIEW)
        # =========================================================
        with col_elev:
            st.markdown("**ELEVATION (Side)**")
            fig_elev = go.Figure()
            
            # 1. Column
            fig_elev.add_shape(type="rect", x0=-30, y0=-h_beam/2-20, x1=0, y1=h_beam/2+20, fillcolor=supp_col, line_color="black")
            
            # 2. Beam
            viz_len = plate_w + 100
            fig_elev.add_shape(type="rect", x0=0, y0=-h_beam/2, x1=viz_len, y1=h_beam/2, line_color="gray", fillcolor="white")
            fig_elev.add_shape(type="line", x0=0, y0=-h_beam/2+tf_beam, x1=viz_len, y1=-h_beam/2+tf_beam, line_color="gray")
            fig_elev.add_shape(type="line", x0=0, y0=h_beam/2-tf_beam, x1=viz_len, y1=h_beam/2-tf_beam, line_color="gray")
            
            # 3. Plate
            fig_elev.add_shape(type="rect", x0=0, y0=-plate_h/2, x1=plate_w, y1=plate_h/2, 
                               line_color="#3b82f6", fillcolor="rgba(59, 130, 246, 0.2)", line_width=2)
            
            # 4. Bolts
            start_y = (plate_h/2) - real_lv
            for r in range(n_rows):
                for c in range(n_cols):
                    bx = e1_mm + c*s_h
                    by = start_y - r*s_v
                    fig_elev.add_trace(go.Scatter(x=[bx], y=[by], mode='markers', marker=dict(size=9, color='#b91c1c'), showlegend=False))
                    fig_elev.add_shape(type="line", x0=bx-5, y0=by, x1=bx+5, y1=by, line_width=1)
                    fig_elev.add_shape(type="line", x0=bx, y0=by-5, x1=bx, y1=by+5, line_width=1)

            # Dimensions
            add_dim_line(fig_elev, plate_w+10, -plate_h/2, plate_w+10, plate_h/2, f"H={plate_h:.0f}", type="vert", color="#1e40af")
            add_dim_line(fig_elev, 0, -plate_h/2-20, plate_w, -plate_h/2-20, f"W={plate_w:.0f}", type="horiz", color="#1e40af")

            fig_elev.update_layout(
                height=380, margin=dict(l=10, r=10, t=30, b=10), plot_bgcolor="white",
                xaxis=dict(visible=False, fixedrange=True, range=[-40, viz_len]),
                yaxis=dict(visible=False, scaleanchor="x", scaleratio=1, fixedrange=True, range=[-h_beam/1.5, h_beam/1.5]),
                title=dict(text="ELEVATION (SIDE)", x=0.5, font=dict(size=12))
            )
            st.plotly_chart(fig_elev, use_container_width=True)

    return n_total, Design_Shear
