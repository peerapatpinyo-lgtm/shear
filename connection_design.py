import streamlit as st
import plotly.graph_objects as go

# ==========================================
# HELPER: DIMENSIONS & ANNOTATIONS
# ==========================================
def add_dim(fig, x0, y0, x1, y1, text, type="horiz", offset=0, color="#1e293b"):
    """ ฟังก์ชันเขียนเส้นบอกระยะที่ปรับปรุงหัวลูกศรให้ชัดขึ้น """
    arrow_size = 8
    ext_line = dict(color=color, width=0.5, dash="solid")
    main_line = dict(color=color, width=1.2)
    
    if type == "horiz":
        y_dim = y0 + offset
        # เส้นขีดตั้ง (Extensions)
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_dim, line=ext_line)
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_dim, line=ext_line)
        # เส้นนอน (Main)
        fig.add_shape(type="line", x0=x0, y0=y_dim, x1=x1, y1=y_dim, line=main_line)
        # หัวลูกศร (Arrowheads using annotations)
        fig.add_annotation(x=x0, y=y_dim, ax=arrow_size, ay=0, arrowhead=2, arrowcolor=color, arrowwidth=1.5, text="")
        fig.add_annotation(x=x1, y=y_dim, ax=-arrow_size, ay=0, arrowhead=2, arrowcolor=color, arrowwidth=1.5, text="")
        # ตัวหนังสือ (Text)
        fig.add_annotation(x=(x0+x1)/2, y=y_dim, text=f"<b>{text}</b>", showarrow=False, yshift=10 if offset>0 else -10,
                           font=dict(size=12, color=color), bgcolor="rgba(255,255,255,0.9)")

    elif type == "vert":
        x_dim = x0 + offset
        # เส้นขีดนอน (Extensions)
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_dim, y1=y0, line=ext_line)
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_dim, y1=y1, line=ext_line)
        # เส้นตั้ง (Main)
        fig.add_shape(type="line", x0=x_dim, y0=y0, x1=x_dim, y1=y1, line=main_line)
        # หัวลูกศร
        fig.add_annotation(x=x_dim, y=y0, ax=0, ay=-arrow_size, arrowhead=2, arrowcolor=color, arrowwidth=1.5, text="")
        fig.add_annotation(x=x_dim, y=y1, ax=0, ay=arrow_size, arrowhead=2, arrowcolor=color, arrowwidth=1.5, text="")
        # ตัวหนังสือ
        fig.add_annotation(x=x_dim, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=15 if offset>0 else -15,
                           font=dict(size=12, color=color), textangle=-90, bgcolor="rgba(255,255,255,0.9)")

def add_leader(fig, x, y, text, ax=40, ay=-40):
    """ ป้ายกำกับแบบมีเส้นชี้ (Callout) """
    fig.add_annotation(
        x=x, y=y, text=text,
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.5,
        ax=ax, ay=ay,
        font=dict(size=11, color="#333"),
        bgcolor="#f1f5f9", bordercolor="#333", borderwidth=1, borderpad=4,
        opacity=0.9
    )

# ==========================================
# MAIN FUNCTION
# ==========================================
def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    
    # 1. SETUP DATA
    d_mm = int(bolt_size[1:]) 
    h_beam = float(section_data.get('h', 300))
    b_beam = float(section_data.get('b', 150))
    tf_beam = float(section_data.get('tf', 10))
    tw_beam = float(section_data.get('tw', 8))
    clear_web_h = h_beam - 2*(tf_beam * 1.5) 

    st.markdown(f"### 📐 Connection: **{conn_type}**")

    # TABS
    tab1, tab2 = st.tabs(["📝 Inputs & Checks", "🎨 Shop Drawing (Color Code)"])

    # --- TAB 1: INPUTS ---
    with tab1:
        min_pitch, min_edge = 3 * d_mm, 1.5 * d_mm
        c1, c2, c3 = st.columns(3)
        with c1:
            st.info(f"**🔩 Bolt: {bolt_size}**")
            n_rows = st.number_input("Rows (V)", 2, 12, 3)
            n_cols = st.number_input("Cols (H)", 1, 3, 2)
            s_v = st.number_input("Vert. Pitch (sv)", 0.0, 300.0, float(max(75, min_pitch)))
            s_h = st.number_input("Horiz. Pitch (sh)", 0.0, 150.0, float(max(60, min_pitch))) if n_cols > 1 else 0
        with c2:
            st.warning("**📏 Plate**")
            size_mode = st.radio("Height Mode", ["Auto", "Custom"], horizontal=True, label_visibility="collapsed")
            l_edge_v_input = st.number_input("Vert. Edge (Lv)", 0.0, 100.0, float(max(40, min_edge)))
            e1_mm = st.number_input("Gap (e1)", 10.0, 200.0, 50.0)
            
            auto_h = (n_rows - 1) * s_v + (2 * l_edge_v_input)
            plate_h = st.number_input("Height (H)", min_value=100.0, max_value=float(h_beam), value=float(auto_h)) if size_mode=="Custom" else auto_h
            l_side = st.number_input("Side (Ls)", 20.0, 100.0, 40.0)
        with c3:
            st.success("**🧱 Specs**")
            t_plate_mm = st.number_input("Thk (t_pl)", 6.0, 50.0, 10.0)
            
            real_lv = (plate_h - (n_rows-1)*s_v) / 2
            plate_w = e1_mm + (n_cols - 1) * s_h + l_side
            n_total = n_rows * n_cols
            Design_Shear = 10000 # Dummy
            
            st.write(f"**H:** {plate_h:.0f} mm | **W:** {plate_w:.0f} mm")
            if plate_h > clear_web_h: st.error("❌ CLASH!")
            else: st.success("✅ Geometry OK")

    # --- TAB 2: DRAWING ---
    with tab2:
        c_ctrl1, c_ctrl2 = st.columns(2)
        with c_ctrl1:
            plate_side = st.radio("Side", ["Right", "Left"], horizontal=True, label_visibility="collapsed")
        with c_ctrl2:
            eccentricity = st.slider("Eccentricity", -50, 50, 0, 10)

        st.divider()
        col_sec, col_elev = st.columns([1.3, 1])

        # COLORS
        c_col = "#64748b"   # Column (Dark Grey)
        c_beam = "#e4e4e7"  # Beam (Light Grey)
        c_plate = "#3b82f6" # Plate (Blue)
        c_bolt = "#ef4444"  # Bolt (Red)
        c_dim = "#0f172a"   # Dim (Black)

        # ---------------------------------------------------------
        # VIEW 1: SECTION A-A (TOP)
        # ---------------------------------------------------------
        with col_sec:
            fig_sec = go.Figure()
            
            # Limits
            zoom_y = max(b_beam, 180) * 0.75
            zoom_x_end = plate_w + 100

            # 1. COLUMN (Solid Dark Box)
            fig_sec.add_shape(type="rect", x0=-20, y0=-zoom_y, x1=0, y1=zoom_y, fillcolor=c_col, line_color="black")
            
            # 2. BEAM
            beam_cy = eccentricity
            # Web
            fig_sec.add_shape(type="rect", x0=10, y0=beam_cy-tw_beam/2, x1=zoom_x_end, y1=beam_cy+tw_beam/2, fillcolor=c_beam, line_color="black")
            # Flange (Dashed)
            fig_sec.add_shape(type="rect", x0=10, y0=beam_cy-b_beam/2, x1=zoom_x_end, y1=beam_cy+b_beam/2, line=dict(color="gray", dash="dot"))
            
            # 3. PLATE
            if plate_side == "Right":
                py_min, py_max = beam_cy + tw_beam/2, beam_cy + tw_beam/2 + t_plate_mm
                annot_pos_y = py_max
                annot_ay = -40
            else:
                py_min, py_max = beam_cy - tw_beam/2 - t_plate_mm, beam_cy - tw_beam/2
                annot_pos_y = py_min
                annot_ay = 40
            
            fig_sec.add_shape(type="rect", x0=0, y0=py_min, x1=plate_w, y1=py_max, fillcolor=c_plate, line_color="black", opacity=0.9)
            
            # 4. BOLTS
            b_start_x = e1_mm
            for c in range(n_cols):
                bx = b_start_x + c*s_h
                fig_sec.add_shape(type="rect", x0=bx-d_mm/2, y0=min(py_min, beam_cy-tw_beam/2), x1=bx+d_mm/2, y1=max(py_max, beam_cy+tw_beam/2), fillcolor=c_bolt, line_width=0)
                # Heads
                fig_sec.add_shape(type="rect", x0=bx-d_mm, y0=py_max, x1=bx+d_mm, y1=py_max+(d_mm*0.6), fillcolor="#b91c1c")
                fig_sec.add_shape(type="rect", x0=bx-d_mm, y0=py_min-(d_mm*0.6), x1=bx+d_mm, y1=py_min, fillcolor="#b91c1c")

            # --- ANNOTATIONS ---
            dim_y = -zoom_y + 20
            
            # Chain Dims
            curr_x = 0
            add_dim(fig_sec, curr_x, dim_y, curr_x+e1_mm, dim_y, f"{e1_mm:.0f}", "horiz", color=c_dim)
            curr_x += e1_mm
            if n_cols > 1:
                for _ in range(n_cols-1):
                    add_dim(fig_sec, curr_x, dim_y, curr_x+s_h, dim_y, f"{s_h:.0f}", "horiz", color="#b91c1c")
                    curr_x += s_h
            add_dim(fig_sec, curr_x, dim_y, plate_w, dim_y, f"{l_side:.0f}", "horiz", color=c_dim)

            # Labels (Callouts)
            add_leader(fig_sec, -10, zoom_y-20, "<b>Column</b><br>(Support)", ax=40, ay=0)
            add_leader(fig_sec, plate_w/2, annot_pos_y, f"<b>Fin Plate</b><br>t={t_plate_mm}", ax=30, ay=annot_ay)
            add_leader(fig_sec, plate_w+20, beam_cy, f"<b>Beam Web</b><br>tw={tw_beam}", ax=30, ay=0)

            fig_sec.update_layout(
                title="SECTION A-A (Top View)", 
                height=400, margin=dict(l=10,r=10,t=40,b=10), plot_bgcolor="white",
                xaxis=dict(visible=False, range=[-40, zoom_x_end], fixedrange=True),
                yaxis=dict(visible=False, range=[-zoom_y-10, zoom_y+10], scaleanchor="x", scaleratio=1, fixedrange=True),
                dragmode="pan"
            )
            st.plotly_chart(fig_sec, use_container_width=True)

        # ---------------------------------------------------------
        # VIEW 2: ELEVATION (SIDE)
        # ---------------------------------------------------------
        with col_elev:
            fig_elev = go.Figure()
            view_h = h_beam * 0.7
            
            # 1. BEAM & COLUMN
            fig_elev.add_shape(type="rect", x0=0, y0=-h_beam/2, x1=plate_w+60, y1=h_beam/2, line_color="gray", fillcolor="white") # Beam Outline
            fig_elev.add_shape(type="rect", x0=-20, y0=-view_h, x1=0, y1=view_h, fillcolor=c_col, line_color="black") # Column
            
            # 2. PLATE
            fig_elev.add_shape(type="rect", x0=0, y0=-plate_h/2, x1=plate_w, y1=plate_h/2, fillcolor=c_plate, line_color="#1d4ed8", opacity=0.3)
            
            # 3. BOLTS
            b_start_y = (plate_h/2) - real_lv 
            for r in range(n_rows):
                for c in range(n_cols):
                    bx = e1_mm + c*s_h
                    by = b_start_y - r*s_v
                    fig_elev.add_shape(type="circle", x0=bx-d_mm/2, y0=by-d_mm/2, x1=bx+d_mm/2, y1=by+d_mm/2, fillcolor=c_bolt, line_color="black")
                    fig_elev.add_shape(type="line", x0=bx-2, y0=by, x1=bx+2, y1=by, line_color="white") # Cross
                    fig_elev.add_shape(type="line", x0=bx, y0=by-2, x1=bx, y1=by+2, line_color="white") # Cross

            # --- DIMS ---
            dim_x = plate_w + 15
            curr_y = plate_h/2
            add_dim(fig_elev, dim_x, curr_y, dim_x, curr_y-real_lv, f"{real_lv:.0f}", "vert", color=c_dim)
            curr_y -= real_lv
            if n_rows > 1:
                for _ in range(n_rows-1):
                    add_dim(fig_elev, dim_x, curr_y, dim_x, curr_y-s_v, f"{s_v:.0f}", "vert", color="#b91c1c")
                    curr_y -= s_v
            add_dim(fig_elev, dim_x, curr_y, dim_x, -plate_h/2, f"{real_lv:.0f}", "vert", color=c_dim)
            
            # Callout Bolt
            add_leader(fig_elev, e1_mm, b_start_y, f"<b>{n_total} Bolts</b><br>M{d_mm}", ax=20, ay=-40)

            fig_elev.update_layout(
                title="ELEVATION (Side View)",
                height=400, margin=dict(l=10,r=10,t=40,b=10), plot_bgcolor="white",
                xaxis=dict(visible=False, range=[-30, plate_w+80], fixedrange=True),
                yaxis=dict(visible=False, range=[-view_h, view_h], scaleanchor="x", scaleratio=1, fixedrange=True),
                dragmode="pan"
            )
            st.plotly_chart(fig_elev, use_container_width=True)

    return n_total, Design_Shear
