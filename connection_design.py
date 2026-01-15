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

def create_ishape(h, b, tw, tf, cx=0, cy=0, fill_col="#cbd5e1", line_col="black"):
    shapes = []
    shapes.append(dict(type="rect", x0=cx-tw/2, y0=cy-h/2+tf, x1=cx+tw/2, y1=cy+h/2-tf, fillcolor=fill_col, line_width=0))
    shapes.append(dict(type="rect", x0=cx-b/2, y0=cy+h/2-tf, x1=cx+b/2, y1=cy+h/2, fillcolor=fill_col, line=dict(color=line_col, width=1.5)))
    shapes.append(dict(type="rect", x0=cx-b/2, y0=cy-h/2, x1=cx+b/2, y1=cy-h/2+tf, fillcolor=fill_col, line=dict(color=line_col, width=1.5)))
    shapes.append(dict(type="line", x0=cx-tw/2, y0=cy-h/2+tf, x1=cx-tw/2, y1=cy+h/2-tf, line=dict(color=line_col, width=1.5)))
    shapes.append(dict(type="line", x0=cx+tw/2, y0=cy-h/2+tf, x1=cx+tw/2, y1=cy+h/2-tf, line=dict(color=line_col, width=1.5)))
    return shapes

# ==========================================
# MAIN FUNCTION
# ==========================================
def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    
    # 1. SETUP
    is_beam_to_beam = "Beam to Beam" in conn_type
    d_mm = int(bolt_size[1:]) 
    
    h_beam = float(section_data.get('h', 300))
    b_beam = float(section_data.get('b', 150))
    tf_beam = float(section_data.get('tf', 10))
    tw_beam = float(section_data.get('tw', 8))
    clear_web_h = h_beam - 2*(tf_beam * 1.5) 

    # 2. INPUTS
    st.markdown(f"### 📐 Connection Design: **{conn_type}**")
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
    c_head, c_opt = st.columns([2, 1])
    with c_head: st.subheader("📐 Structural Shop Drawings")
    with c_opt: use_true_scale = st.checkbox("🔒 Fix Aspect Ratio (1:1)", value=False)
    
    supp_col = "#334155" 

    col_sec, col_elev, col_res = st.columns([1.1, 1.1, 0.8])
    
    # --- VIEW 1: SECTION A-A ---
    with col_sec:
        st.markdown("**SECTION A-A** (Top/Cut View)")
        fig_sec = go.Figure()
        
        # --- SUPPORT LOGIC ---
        if is_beam_to_beam:
            # === Beam to Beam ===
            h_main, b_main = h_beam * 1.5, b_beam * 1.2
            tw_main, tf_main = tw_beam * 1.2, tf_beam * 1.2
            main_cx = -tw_main / 2  
            main_shapes = create_ishape(h_main, b_main, tw_main, tf_main, cx=main_cx, cy=0, fill_col="#475569", line_col="black")
            for s in main_shapes: fig_sec.add_shape(s)
            fig_sec.add_annotation(x=main_cx, y=-h_main/2-20, text="MAIN BEAM", showarrow=False, font=dict(weight="bold", color="#475569"))
            
        else:
            # === Beam to Column ===
            col_width = b_beam * 1.5
            col_height_viz = h_beam * 1.6 
            col_web_thk = 10 

            # 1. Column Flange (Solid Block)
            fig_sec.add_shape(type="rect", 
                              x0=-col_width/2, y0=-col_height_viz/2, 
                              x1=0, y1=col_height_viz/2, 
                              fillcolor="#334155", line_color="black")
            
            # 2. Hidden Web Line (เส้นประแสดงแนวเอวเสาที่อยู่ด้านหลัง)
            # เพื่อบอกว่าเราเชื่อมเข้าที่ Center ของเสาพอดี
            fig_sec.add_shape(type="rect", 
                              x0=-col_width/2, y0=-col_web_thk/2, 
                              x1=0, y1=col_web_thk/2, 
                              line=dict(color="white", width=1, dash="dot"), fillcolor="rgba(0,0,0,0)")

            fig_sec.add_annotation(x=-col_width/4, y=-col_height_viz/2-20, text="COLUMN FLANGE", showarrow=False, font=dict(weight="bold", color="#334155"))
            add_dim_line(fig_sec, -col_width/2, col_height_viz/2+10, 0, col_height_viz/2+10, "Col. Width", type="horiz", offset=0)

        # --- Fin Plate ---
        plate_x0, plate_x1 = 0, t_plate_mm
        p_color = "#ef4444" if fit_status == "CLASH" else "#3b82f6"
        fig_sec.add_shape(type="rect", x0=plate_x0, y0=-plate_h/2, x1=plate_x1, y1=plate_h/2, fillcolor=p_color, line_color="black", opacity=0.9)
        
        # Weld
        weld_size = 6
        fig_sec.add_trace(go.Scatter(x=[0, weld_size, 0, 0], y=[plate_h/2, plate_h/2, plate_h/2+weld_size, plate_h/2], fill="toself", fillcolor="black", mode="lines", line=dict(width=1), showlegend=False))
        fig_sec.add_trace(go.Scatter(x=[0, weld_size, 0, 0], y=[-plate_h/2, -plate_h/2, -plate_h/2-weld_size, -plate_h/2], fill="toself", fillcolor="black", mode="lines", line=dict(width=1), showlegend=False))

        # --- Secondary Beam ---
        # วาด Beam ให้อยู่ที่ Y=0 (Center) เสมอ เพื่อให้ตรงกับ Center เสา
        beam_web_x0 = plate_x1
        beam_web_x1 = plate_x1 + tw_beam
        beam_center_x = (beam_web_x0 + beam_web_x1) / 2 
        
        fig_sec.add_shape(type="rect", x0=beam_web_x0, y0=-h_beam/2 + tf_beam, x1=beam_web_x1, y1=h_beam/2 - tf_beam, fillcolor="#d4d4d8", line_color="black")
        flange_x0 = beam_center_x - b_beam/2
        flange_x1 = beam_center_x + b_beam/2
        fig_sec.add_shape(type="rect", x0=flange_x0, y0=h_beam/2 - tf_beam, x1=flange_x1, y1=h_beam/2, fillcolor="#a1a1aa", line_color="black")
        fig_sec.add_shape(type="rect", x0=flange_x0, y0=-h_beam/2, x1=flange_x1, y1=-h_beam/2 + tf_beam, fillcolor="#a1a1aa", line_color="black")

        # --- Centerline (CL) ---
        # เส้นสำคัญที่บอกว่าทุกอย่าง Aligned กัน
        fig_sec.add_shape(type="line", x0=-100, y0=0, x1=flange_x1+50, y1=0, line=dict(color="#b91c1c", width=1, dash="dashdot"))
        fig_sec.add_annotation(x=flange_x1+60, y=0, text="CL", showarrow=False, font=dict(color="#b91c1c", weight="bold"))

        # --- Bolts ---
        bolt_y_start_coord = plate_h/2 - real_lv
        bolt_head_h, nut_h = d_mm * 0.6, d_mm * 0.8
        for r in range(n_rows):
            by = bolt_y_start_coord - r*s_v
            fig_sec.add_shape(type="rect", x0=plate_x0-5, y0=by-d_mm/2, x1=beam_web_x1+5, y1=by+d_mm/2, fillcolor="#b91c1c", line_width=0)
            fig_sec.add_shape(type="rect", x0=plate_x0 - bolt_head_h, y0=by-d_mm*0.8, x1=plate_x0, y1=by+d_mm*0.8, fillcolor="#7f1d1d", line_color="black")
            fig_sec.add_shape(type="rect", x0=beam_web_x1, y0=by-d_mm*0.8, x1=beam_web_x1 + nut_h, y1=by+d_mm*0.8, fillcolor="#7f1d1d", line_color="black")
            fig_sec.add_shape(type="line", x0=-20, y0=by, x1=flange_x1+20, y1=by, line=dict(color="black", width=0.5, dash="dashdot"))

        # Dimensions
        stack_y = plate_h/2 + 30
        add_dim_line(fig_sec, 0, stack_y, t_plate_mm, stack_y, f"t_pl", offset=0, type="horiz")
        add_dim_line(fig_sec, beam_web_x0, stack_y, beam_web_x1, stack_y, f"tw", offset=0, type="horiz")
        add_dim_line(fig_sec, flange_x1, -h_beam/2, flange_x1, h_beam/2, f"h={h_beam:.0f}", offset=20, type="vert", bold=True)

        layout_sec = dict(height=550, plot_bgcolor="white", margin=dict(l=10, r=10, t=30, b=30), title=dict(text="SECTION A-A", x=0.5, y=0.02), dragmode="pan")
        if use_true_scale:
            left_lim = -150 if not is_beam_to_beam else -100
            layout_sec['xaxis'] = dict(visible=False, fixedrange=False, range=[left_lim, flange_x1+80])
            layout_sec['yaxis'] = dict(visible=False, scaleanchor="x", scaleratio=1, fixedrange=False)
        else:
            layout_sec['xaxis'] = dict(visible=False, fixedrange=False)
            layout_sec['yaxis'] = dict(visible=False, fixedrange=False)
        fig_sec.update_layout(**layout_sec)
        st.plotly_chart(fig_sec, use_container_width=True)

    # --- VIEW 2: ELEVATION ---
    with col_elev:
        st.markdown("**ELEVATION** (Side View)")
        fig_elev = go.Figure()
        
        beam_top, beam_bot = h_beam/2, -h_beam/2
        plate_top, plate_bot = plate_h/2, -plate_h/2
        bolt_x_start, bolt_y_start = e1_mm, plate_top - real_lv
        
        fig_elev.add_shape(type="rect", x0=-40, y0=beam_bot-20, x1=0, y1=beam_top+20, fillcolor=supp_col, line_color="black") 
        fig_elev.add_shape(type="rect", x0=-20, y0=beam_top-tf_beam, x1=plate_w+50, y1=beam_top, fillcolor="#e4e4e7", opacity=0.5, line_width=0) 
        fig_elev.add_shape(type="rect", x0=-20, y0=beam_bot, x1=plate_w+50, y1=beam_bot+tf_beam, fillcolor="#e4e4e7", opacity=0.5, line_width=0) 
        fig_elev.add_shape(type="rect", x0=0, y0=plate_bot, x1=plate_w, y1=plate_top, fillcolor="rgba(59, 130, 246, 0.2)", line=dict(color="#2563eb", width=2))
        
        for r in range(n_rows):
            for c in range(n_cols):
                bx, by = bolt_x_start + c*s_h, bolt_y_start - r*s_v
                fig_elev.add_trace(go.Scatter(x=[bx], y=[by], mode='markers', marker=dict(size=9, color='#b91c1c'), showlegend=False))
                fig_elev.add_shape(type="line", x0=bx-6, y0=by, x1=bx+6, y1=by, line=dict(color="black", width=0.5))
                fig_elev.add_shape(type="line", x0=bx, y0=by-6, x1=bx, y1=by+6, line=dict(color="black", width=0.5))

        add_dim_line(fig_elev, 0, plate_bot, plate_w, plate_bot, f"W={plate_w:.0f}", color="#1e40af", offset=-40, type="horiz", bold=True)
        add_dim_line(fig_elev, plate_w, plate_top, plate_w, plate_bot, f"H={plate_h:.0f}", color="#1e40af", offset=90, type="vert", bold=True)
        add_dim_line(fig_elev, 0, plate_top, e1_mm, plate_top, f"e1={e1_mm:.0f}", color="#d97706", offset=40, type="horiz")
        if n_cols > 1: add_dim_line(fig_elev, bolt_x_start, plate_top, bolt_x_start + (n_cols-1)*s_h, plate_top, f"{n_cols-1}@sh", color="#c0392b", offset=40, type="horiz")
        add_dim_line(fig_elev, plate_w, plate_top, plate_w, bolt_y_start, f"Lv", color="#16a34a", offset=40, type="vert")
        if n_rows > 1: add_dim_line(fig_elev, plate_w, bolt_y_start, plate_w, bolt_y_start - (n_rows-1)*s_v, f"{n_rows-1}@sv", color="#c0392b", offset=60, type="vert")

        layout_elev = dict(height=550, margin=dict(l=10, r=10, t=30, b=30), plot_bgcolor="white", title=dict(text="ELEVATION VIEW", x=0.5, y=0.02), dragmode="pan")
        if use_true_scale:
            layout_elev['xaxis'] = dict(visible=False, range=[-50, plate_w+120], fixedrange=False)
            layout_elev['yaxis'] = dict(visible=False, range=[-h_beam/2-50, h_beam/2+50], scaleanchor="x", scaleratio=1, fixedrange=False)
        else:
            layout_elev['xaxis'] = dict(visible=False, fixedrange=False)
            layout_elev['yaxis'] = dict(visible=False, fixedrange=False)
        fig_elev.update_layout(**layout_elev)
        st.plotly_chart(fig_elev, use_container_width=True)

    # --- VIEW 3: RESULTS ---
    with col_res:
        st.subheader("📝 Check Results")
        if fit_status == "CLASH": st.error(f"❌ CLASH!")
        with st.expander("Ratio Check", expanded=True):
            st.metric("Bolt Shear", f"{(V_res*n_total)/Design_Shear:.2f}")
            st.metric("Bearing", f"{V_design/Design_Bear:.2f}")

    return n_total, Design_Shear
