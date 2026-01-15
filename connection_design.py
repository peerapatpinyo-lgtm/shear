import streamlit as st
import math
import plotly.graph_objects as go

# ==========================================
# HELPER: DRAWING DIMENSIONS (ENHANCED)
# ==========================================
def add_dim_line(fig, x0, y0, x1, y1, text, color="black", offset=0, type="horiz", font_size=11, bold=False):
    arrow_len = 6
    text_bg = "rgba(255, 255, 255, 1.0)"  # พื้นหลังทึบ อ่านง่าย
    font_weight = "bold" if bold else "normal"
    
    # Dash Line Style
    dash_style = "dot"

    if type == "horiz":
        y_pos = y0 + offset
        # Extension Lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_pos, line=dict(color=color, width=0.5, dash=dash_style))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_pos, line=dict(color=color, width=0.5, dash=dash_style))
        # Main Line
        fig.add_shape(type="line", x0=x0, y0=y_pos, x1=x1, y1=y_pos, line=dict(color=color, width=1.2))
        # Arrows
        fig.add_annotation(x=x1, y=y_pos, ax=-arrow_len, ay=0, arrowcolor=color, arrowhead=2, arrowwidth=1.5, text="")
        fig.add_annotation(x=x0, y=y_pos, ax=arrow_len, ay=0, arrowcolor=color, arrowhead=2, arrowwidth=1.5, text="")
        # Text
        fig.add_annotation(x=(x0+x1)/2, y=y_pos, text=text, showarrow=False, yshift=10 if offset>0 else -10, 
                            font=dict(color=color, size=font_size, weight=font_weight), bgcolor=text_bg, bordercolor=color, borderwidth=0)

    elif type == "vert":
        x_pos = x0 + offset
        # Extension Lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_pos, y1=y0, line=dict(color=color, width=0.5, dash=dash_style))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_pos, y1=y1, line=dict(color=color, width=0.5, dash=dash_style))
        # Main Line
        fig.add_shape(type="line", x0=x_pos, y0=y0, x1=x_pos, y1=y1, line=dict(color=color, width=1.2))
        # Arrows
        fig.add_annotation(x=x_pos, y=y1, ax=0, ay=arrow_len, arrowcolor=color, arrowhead=2, arrowwidth=1.5, text="")
        fig.add_annotation(x=x_pos, y=y0, ax=0, ay=-arrow_len, arrowcolor=color, arrowhead=2, arrowwidth=1.5, text="")
        # Text
        fig.add_annotation(x=x_pos, y=(y0+y1)/2, text=text, showarrow=False, xshift=15 if offset>0 else -15, 
                            font=dict(color=color, size=font_size, weight=font_weight), textangle=-90, bgcolor=text_bg, bordercolor=color, borderwidth=0)

# ==========================================
# MAIN FUNCTION (FULL DETAILING)
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
    tab1, tab2 = st.tabs(["📝 Design Inputs & Check", "✏️ Shop Drawing (Detailed)"])

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
    # TAB 2: SHOP DRAWING (DETAILED ANNOTATIONS)
    # ==========================================
    with tab2:
        st.markdown("#### 📍 Installation Layout")
        
        c_ctrl1, c_ctrl2 = st.columns(2)
        with c_ctrl1:
            plate_side = st.radio("ตำแหน่งเพลท", ["Right of Web", "Left of Web"], horizontal=True, label_visibility="collapsed")
        with c_ctrl2:
            eccentricity = st.slider("เยื้องศูนย์ (Eccentricity)", -50, 50, 0, 5)

        st.divider()
        col_sec, col_elev = st.columns([1.2, 1])
        supp_col = "#334155" 
        dim_color = "#0369a1" # สีน้ำเงินเข้มสำหรับเส้นบอกระยะ
        bolt_dim_col = "#b91c1c" # สีแดงสำหรับระยะ Bolt
        
        # --- VIEW 1: SECTION A-A (TOP VIEW) ---
        with col_sec:
            st.markdown("**SECTION A-A (Top)**")
            fig_sec = go.Figure()
            
            zoom_y = max(b_beam, 150) * 0.8  
            zoom_x_start = -50
            zoom_x_end = plate_w + 100 
            
            # 1. COLUMN & BEAM
            fig_sec.add_shape(type="rect", x0=-20, y0=-zoom_y, x1=0, y1=zoom_y, fillcolor=supp_col, line_color="black")
            beam_cy = eccentricity
            beam_x_end = zoom_x_end - 20 
            
            # Beam
            fig_sec.add_shape(type="rect", x0=10, y0=beam_cy-tw_beam/2, x1=beam_x_end, y1=beam_cy+tw_beam/2, fillcolor="#d4d4d8", line_color="black") # Web
            fig_sec.add_shape(type="rect", x0=10, y0=beam_cy-b_beam/2, x1=beam_x_end, y1=beam_cy+b_beam/2, line=dict(color="gray", dash="dot")) # Flange
            fig_sec.add_shape(type="line", x0=-30, y0=beam_cy, x1=beam_x_end, y1=beam_cy, line=dict(color="#b91c1c", width=1, dash="dashdot")) # CL

            # 2. PLATE & BOLTS
            if plate_side == "Right of Web":
                py_min, py_max = beam_cy + tw_beam/2, beam_cy + tw_beam/2 + t_plate_mm
                annot_y = py_max + 15
            else:
                py_min, py_max = beam_cy - tw_beam/2 - t_plate_mm, beam_cy - tw_beam/2
                annot_y = py_min - 15
            
            # Draw Plate
            fig_sec.add_shape(type="rect", x0=0, y0=py_min, x1=plate_w, y1=py_max, fillcolor="#3b82f6", line_color="black", opacity=0.9)
            
            # Annotation: PL Thickness
            fig_sec.add_annotation(x=plate_w/2, y=annot_y, text=f"PL {t_plate_mm:.0f}mm", showarrow=False, font=dict(size=10, color="blue"))

            # Weld
            weld_y = py_max if plate_side == "Right of Web" else py_min
            fig_sec.add_annotation(x=5, y=weld_y, text="6mm", showarrow=True, arrowhead=2, ay=-20 if plate_side=="Right of Web" else 20, font=dict(size=10))

            # Bolts
            b_start_x = e1_mm
            for c in range(n_cols):
                bx = b_start_x + c*s_h
                fig_sec.add_shape(type="rect", x0=bx-d_mm/2, y0=min(py_min, beam_cy-tw_beam/2), x1=bx+d_mm/2, y1=max(py_max, beam_cy+tw_beam/2), fillcolor="#b91c1c", line_width=0)
                # Heads
                head_h = d_mm * 0.6
                fig_sec.add_shape(type="rect", x0=bx-d_mm, y0=py_max, x1=bx+d_mm, y1=py_max+head_h, fillcolor="#7f1d1d")
                fig_sec.add_shape(type="rect", x0=bx-d_mm, y0=py_min-head_h, x1=bx+d_mm, y1=py_min, fillcolor="#7f1d1d")

            # --- DETAILED DIMENSIONS (CHAIN) ---
            dim_y_base = -zoom_y + 20 # ตำแหน่งเส้นบอกระยะด้านล่าง
            
            # 1. Chain: e1 -> Spacing -> End
            current_x = 0
            # e1
            add_dim_line(fig_sec, current_x, dim_y_base, current_x + e1_mm, dim_y_base, f"{e1_mm:.0f}", color=dim_color)
            current_x += e1_mm
            
            # Spacing (Show only if cols > 1)
            if n_cols > 1:
                for _ in range(n_cols - 1):
                    add_dim_line(fig_sec, current_x, dim_y_base, current_x + s_h, dim_y_base, f"{s_h:.0f}", color=bolt_dim_col)
                    current_x += s_h
            
            # Edge Distance (Ls)
            add_dim_line(fig_sec, current_x, dim_y_base, plate_w, dim_y_base, f"{l_side:.0f}", color=dim_color)
            
            # 2. Overall Width (Lower down)
            add_dim_line(fig_sec, 0, dim_y_base, plate_w, dim_y_base, f"W = {plate_w:.0f}", color="black", offset=-25, bold=True)

            layout_sec = dict(
                height=350, margin=dict(l=10, r=10, t=30, b=10), plot_bgcolor="white",
                xaxis=dict(visible=False, range=[zoom_x_start, zoom_x_end], fixedrange=True),
                yaxis=dict(visible=False, range=[-zoom_y, zoom_y], scaleanchor="x", scaleratio=1, fixedrange=True),
                dragmode="pan"
            )
            fig_sec.update_layout(**layout_sec)
            st.plotly_chart(fig_sec, use_container_width=True)

        # --- VIEW 2: ELEVATION (SIDE VIEW) ---
        with col_elev:
            st.markdown("**ELEVATION (Side)**")
            fig_elev = go.Figure()
            
            elev_zoom_y = h_beam * 0.7 
            elev_zoom_x = plate_w + 80
            
            # Visuals
            fig_elev.add_shape(type="rect", x0=0, y0=-h_beam/2, x1=elev_zoom_x, y1=h_beam/2, line_color="gray", fillcolor="white")
            fig_elev.add_shape(type="line", x0=0, y0=-h_beam/2+tf_beam, x1=elev_zoom_x, y1=-h_beam/2+tf_beam, line_color="gray")
            fig_elev.add_shape(type="line", x0=0, y0=h_beam/2-tf_beam, x1=elev_zoom_x, y1=h_beam/2-tf_beam, line_color="gray")
            fig_elev.add_shape(type="rect", x0=0, y0=-plate_h/2, x1=plate_w, y1=plate_h/2, line_color="#3b82f6", fillcolor="rgba(59, 130, 246, 0.2)", line_width=2)
            fig_elev.add_shape(type="rect", x0=-20, y0=-elev_zoom_y, x1=0, y1=elev_zoom_y, fillcolor=supp_col, line_color="black")
            
            # Bolts
            b_start_y = (plate_h/2) - real_lv 
            for r in range(n_rows):
                for c in range(n_cols):
                    bx = e1_mm + c*s_h
                    by = b_start_y - r*s_v
                    fig_elev.add_trace(go.Scatter(x=[bx], y=[by], mode='markers', marker=dict(size=8, color='#b91c1c'), showlegend=False))

            # --- DETAILED DIMENSIONS (VERTICAL CHAIN) ---
            dim_x_base = plate_w + 15 # ตำแหน่งเส้นบอกระยะด้านขวา
            
            # 1. Chain: Lv -> Spacing -> Lv
            current_y = plate_h/2
            
            # Top Lv
            add_dim_line(fig_elev, dim_x_base, current_y, dim_x_base, current_y - real_lv, f"{real_lv:.0f}", type="vert", color=dim_color)
            current_y -= real_lv
            
            # Pitch (sv)
            if n_rows > 1:
                for _ in range(n_rows - 1):
                    add_dim_line(fig_elev, dim_x_base, current_y, dim_x_base, current_y - s_v, f"{s_v:.0f}", type="vert", color=bolt_dim_col)
                    current_y -= s_v
            
            # Bottom Lv
            add_dim_line(fig_elev, dim_x_base, current_y, dim_x_base, -plate_h/2, f"{real_lv:.0f}", type="vert", color=dim_color)
            
            # 2. Overall Height (Far right)
            add_dim_line(fig_elev, dim_x_base, plate_h/2, dim_x_base, -plate_h/2, f"H = {plate_h:.0f}", type="vert", color="black", offset=25, bold=True)

            layout_elev = dict(
                height=350, margin=dict(l=10, r=10, t=30, b=10), plot_bgcolor="white",
                xaxis=dict(visible=False, range=[-30, elev_zoom_x], fixedrange=True),
                yaxis=dict(visible=False, range=[-elev_zoom_y, elev_zoom_y], scaleanchor="x", scaleratio=1, fixedrange=True),
                dragmode="pan"
            )
            fig_elev.update_layout(**layout_elev)
            st.plotly_chart(fig_elev, use_container_width=True)

    return n_total, Design_Shear
