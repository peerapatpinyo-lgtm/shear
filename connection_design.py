import streamlit as st
import math
import plotly.graph_objects as go

# ==========================================
# HELPER 1: ADVANCED DIMENSIONS
# ==========================================
def add_dim(fig, x0, y0, x1, y1, text, type="horiz", offset=0, color="black"):
    """ ฟังก์ชันเขียนเส้นบอกระยะแบบ Engineering Style """
    arrow_size = 6
    # Extension lines style
    ext_line = dict(color=color, width=0.5, dash="solid")
    main_line = dict(color=color, width=1)
    
    if type == "horiz":
        y_dim = y0 + offset
        # Ext lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_dim, line=ext_line)
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_dim, line=ext_line)
        # Main line
        fig.add_shape(type="line", x0=x0, y0=y_dim, x1=x1, y1=y_dim, line=main_line)
        # Arrows
        fig.add_annotation(x=x0, y=y_dim, ax=arrow_size, ay=0, arrowhead=2, arrowcolor=color, arrowwidth=1.5, text="")
        fig.add_annotation(x=x1, y=y_dim, ax=-arrow_size, ay=0, arrowhead=2, arrowcolor=color, arrowwidth=1.5, text="")
        # Text with white background
        fig.add_annotation(x=(x0+x1)/2, y=y_dim, text=f"<b>{text}</b>", showarrow=False, yshift=10 if offset>0 else -10,
                           font=dict(size=11, color=color), bgcolor="white", opacity=1)

    elif type == "vert":
        x_dim = x0 + offset
        # Ext lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_dim, y1=y0, line=ext_line)
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_dim, y1=y1, line=ext_line)
        # Main line
        fig.add_shape(type="line", x0=x_dim, y0=y0, x1=x_dim, y1=y1, line=main_line)
        # Arrows
        fig.add_annotation(x=x_dim, y=y0, ax=0, ay=-arrow_size, arrowhead=2, arrowcolor=color, arrowwidth=1.5, text="")
        fig.add_annotation(x=x_dim, y=y1, ax=0, ay=arrow_size, arrowhead=2, arrowcolor=color, arrowwidth=1.5, text="")
        # Text
        fig.add_annotation(x=x_dim, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=15 if offset>0 else -15,
                           font=dict(size=11, color=color), textangle=-90, bgcolor="white", opacity=1)

# ==========================================
# HELPER 2: CALLOUT LABEL (LEADER LINE)
# ==========================================
def add_callout(fig, x, y, text, ax=40, ay=-40, color="#333"):
    """ เส้นชี้บอกสเปค (Leader Line) """
    fig.add_annotation(
        x=x, y=y, text=text,
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.5,
        ax=ax, ay=ay,
        font=dict(size=11, color=color),
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor=color, borderwidth=1, borderpad=4,
        align="left"
    )

# ==========================================
# HELPER 3: WELD SYMBOL (TRIANGLE)
# ==========================================
def draw_weld_triangle(fig, x, y, size=6, side="right"):
    """ วาดสัญลักษณ์เชื่อมแบบสามเหลี่ยมทึบ """
    dx = size if side == "right" else -size
    # ใช้ SVG Path วาดสามเหลี่ยม
    path = f"M {x} {y} L {x+dx} {y+size} L {x} {y+size} Z"
    fig.add_shape(type="path", path=path, fillcolor="black", line_color="black")

# ==========================================
# MAIN FUNCTION
# ==========================================
def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    
    # --- DATA PREP ---
    d_mm = int(bolt_size[1:]) 
    h_beam = float(section_data.get('h', 300))
    b_beam = float(section_data.get('b', 150))
    tf_beam = float(section_data.get('tf', 10))
    tw_beam = float(section_data.get('tw', 8))
    clear_web_h = h_beam - 2*(tf_beam * 1.5) 

    st.markdown(f"### 📐 Connection Design: **{conn_type}**")

    tab1, tab2 = st.tabs(["📝 Check Inputs", "🏗️ Shop Drawing (Pro)"])

    # --- TAB 1 (INPUTS) ---
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

        # Basic Check
        n_total = n_rows * n_cols
        V_res, Design_Shear = V_design/n_total, 10000 
        st.divider()
        if plate_h > clear_web_h: st.error("❌ CLASH! Plate hits flanges.")
        else: st.success("✅ Geometry OK")

    # --- TAB 2 (PRO DRAWING) ---
    with tab2:
        c_ctrl1, c_ctrl2 = st.columns(2)
        with c_ctrl1:
            plate_side = st.radio("Side", ["Right of Web", "Left of Web"], horizontal=True, label_visibility="collapsed")
        with c_ctrl2:
            eccentricity = st.slider("Eccentricity", -50, 50, 0, 5)

        st.divider()
        col_sec, col_elev = st.columns([1.3, 1]) # ให้พื้นที่ Section มากกว่าหน่อย
        
        # Colors
        col_fill = "#e2e8f0"  # เทาอ่อน
        plate_fill = "#bfdbfe" # ฟ้าอ่อน
        line_col = "#0f172a" # ดำเข้มเกือบดำ
        
        # =========================================================
        # VIEW 1: SECTION A-A (TOP VIEW) - CAD STYLE
        # =========================================================
        with col_sec:
            fig_sec = go.Figure()
            
            # Setup Limits
            zoom_y = max(b_beam, 180) * 0.7
            zoom_x_end = plate_w + 120
            
            # 1. COLUMN (HATCHED)
            # ใช้ fillpattern แสดงว่าเป็นเหล็กตัด (Diagonal lines)
            fig_sec.add_shape(type="rect", x0=-20, y0=-zoom_y, x1=0, y1=zoom_y, 
                              line=dict(color=line_col, width=2),
                              fillcolor="white", fillpattern=dict(shape="/", size=5, solidity=0.3))
            
            # 2. BEAM
            beam_cy = eccentricity
            
            # Web
            fig_sec.add_shape(type="rect", x0=10, y0=beam_cy-tw_beam/2, x1=zoom_x_end, y1=beam_cy+tw_beam/2, 
                              fillcolor="#f4f4f5", line=dict(color=line_col, width=1))
            # Flanges (Dashed Outline)
            fig_sec.add_shape(type="rect", x0=10, y0=beam_cy-b_beam/2, x1=zoom_x_end, y1=beam_cy+b_beam/2, 
                              line=dict(color="gray", dash="longdashdot", width=0.5))
            # Centerline
            fig_sec.add_shape(type="line", x0=-30, y0=beam_cy, x1=zoom_x_end, y1=beam_cy, 
                              line=dict(color="red", width=1, dash="dashdot"))

            # 3. PLATE & WELD
            if plate_side == "Right of Web":
                py_min, py_max = beam_cy + tw_beam/2, beam_cy + tw_beam/2 + t_plate_mm
                weld_y = py_max
                weld_side = "right"
                callout_ay = -40
            else:
                py_min, py_max = beam_cy - tw_beam/2 - t_plate_mm, beam_cy - tw_beam/2
                weld_y = py_min - 6 # Adjust for weld size
                weld_side = "left"
                callout_ay = 40
            
            # Plate
            fig_sec.add_shape(type="rect", x0=0, y0=py_min, x1=plate_w, y1=py_max, 
                              fillcolor=plate_fill, line=dict(color=line_col, width=1.5))
            
            # Weld Symbol (Triangle)
            draw_weld_triangle(fig_sec, 0, weld_y, size=6, side=weld_side)
            
            # 4. BOLTS
            b_start_x = e1_mm
            for c in range(n_cols):
                bx = b_start_x + c*s_h
                # Shank (Through Plate & Web)
                fig_sec.add_shape(type="rect", x0=bx-d_mm/2, y0=min(py_min, beam_cy-tw_beam/2), x1=bx+d_mm/2, y1=max(py_max, beam_cy+tw_beam/2), fillcolor=line_col)
                # Head Top
                fig_sec.add_shape(type="rect", x0=bx-d_mm, y0=py_max, x1=bx+d_mm, y1=py_max+(d_mm*0.6), fillcolor=line_col)
                # Head Bottom
                fig_sec.add_shape(type="rect", x0=bx-d_mm, y0=py_min-(d_mm*0.6), x1=bx+d_mm, y1=py_min, fillcolor=line_col)

            # --- ANNOTATIONS & DIMENSIONS ---
            dim_y = -zoom_y + 15
            
            # Chain Dims
            curr_x = 0
            add_dim(fig_sec, curr_x, dim_y, curr_x+e1_mm, dim_y, f"{e1_mm:.0f}", "horiz", color="#0369a1")
            curr_x += e1_mm
            if n_cols > 1:
                for _ in range(n_cols-1):
                    add_dim(fig_sec, curr_x, dim_y, curr_x+s_h, dim_y, f"{s_h:.0f}", "horiz", color="#b91c1c")
                    curr_x += s_h
            add_dim(fig_sec, curr_x, dim_y, plate_w, dim_y, f"{l_side:.0f}", "horiz", color="#0369a1")
            
            # Total Width
            add_dim(fig_sec, 0, dim_y-25, plate_w, dim_y-25, f"W={plate_w}", "horiz", offset=0, color="black")

            # Callouts
            add_callout(fig_sec, plate_w/2, py_max, f"<b>PL-{t_plate_mm}mm</b>", ax=30, ay=callout_ay)
            add_callout(fig_sec, plate_w+20, beam_cy, f"Beam Web<br>tw={tw_beam}", ax=40, ay=0)
            add_callout(fig_sec, -10, zoom_y-20, "Column", ax=40, ay=0)

            # Layout
            fig_sec.update_layout(
                title=dict(text="SECTION A-A", font=dict(size=14), x=0.5, y=0.98),
                height=400, margin=dict(l=20, r=20, t=40, b=20), plot_bgcolor="white",
                xaxis=dict(visible=False, range=[-50, zoom_x_end], fixedrange=True),
                yaxis=dict(visible=False, range=[-zoom_y-30, zoom_y+30], scaleanchor="x", scaleratio=1, fixedrange=True),
                dragmode="pan", shapes=[dict(type='rect', xref='paper', yref='paper', x0=0, y0=0, x1=1, y1=1, line=dict(color='black', width=2))] # Border
            )
            st.plotly_chart(fig_sec, use_container_width=True)

        # =========================================================
        # VIEW 2: ELEVATION (SIDE VIEW) - CAD STYLE
        # =========================================================
        with col_elev:
            fig_elev = go.Figure()
            
            view_h = h_beam * 0.65
            view_w = plate_w + 80
            
            # 1. BEAM (Outline)
            # Flanges
            fig_elev.add_shape(type="line", x0=0, y0=h_beam/2, x1=view_w, y1=h_beam/2, line=dict(color=line_col, width=1))
            fig_elev.add_shape(type="line", x0=0, y0=h_beam/2-tf_beam, x1=view_w, y1=h_beam/2-tf_beam, line=dict(color=line_col, width=1))
            fig_elev.add_shape(type="line", x0=0, y0=-h_beam/2, x1=view_w, y1=-h_beam/2, line=dict(color=line_col, width=1))
            fig_elev.add_shape(type="line", x0=0, y0=-h_beam/2+tf_beam, x1=view_w, y1=-h_beam/2+tf_beam, line=dict(color=line_col, width=1))
            # Web Hidden Line (Optional - skipped for clarity)
            
            # 2. COLUMN
            fig_elev.add_shape(type="rect", x0=-20, y0=-view_h, x1=0, y1=view_h, 
                               line=dict(color=line_col, width=2), fillcolor="white", 
                               fillpattern=dict(shape="/", size=5, solidity=0.3))
            
            # 3. PLATE
            fig_elev.add_shape(type="rect", x0=0, y0=-plate_h/2, x1=plate_w, y1=plate_h/2, 
                               line=dict(color="#2563eb", width=2), fillcolor="rgba(59, 130, 246, 0.1)")
            
            # 4. BOLTS (Cross Mark + Circle)
            b_start_y = (plate_h/2) - real_lv
            for r in range(n_rows):
                for c in range(n_cols):
                    bx = e1_mm + c*s_h
                    by = b_start_y - r*s_v
                    # Bolt Hole
                    fig_elev.add_shape(type="circle", x0=bx-d_mm/2, y0=by-d_mm/2, x1=bx+d_mm/2, y1=by+d_mm/2, line_color=line_col)
                    # Cross center
                    fig_elev.add_shape(type="line", x0=bx-2, y0=by, x1=bx+2, y1=by, line_width=1)
                    fig_elev.add_shape(type="line", x0=bx, y0=by-2, x1=bx, y1=by+2, line_width=1)

            # --- DIMENSIONS ---
            dim_x = plate_w + 20
            
            # Chain Vert
            curr_y = plate_h/2
            add_dim(fig_elev, dim_x, curr_y, dim_x, curr_y-real_lv, f"{real_lv:.0f}", "vert", color="#0369a1")
            curr_y -= real_lv
            if n_rows > 1:
                for _ in range(n_rows-1):
                    add_dim(fig_elev, dim_x, curr_y, dim_x, curr_y-s_v, f"{s_v:.0f}", "vert", color="#b91c1c")
                    curr_y -= s_v
            add_dim(fig_elev, dim_x, curr_y, dim_x, -plate_h/2, f"{real_lv:.0f}", "vert", color="#0369a1")
            
            # Total H
            add_dim(fig_elev, dim_x+25, plate_h/2, dim_x+25, -plate_h/2, f"H={plate_h}", "vert", color="black")

            # Callout
            add_callout(fig_elev, e1_mm, b_start_y, f"{n_rows*n_cols}-M{d_mm}", ax=20, ay=-30)

            # Layout
            fig_elev.update_layout(
                title=dict(text="ELEVATION", font=dict(size=14), x=0.5, y=0.98),
                height=400, margin=dict(l=20, r=20, t=40, b=20), plot_bgcolor="white",
                xaxis=dict(visible=False, range=[-30, view_w], fixedrange=True),
                yaxis=dict(visible=False, range=[-view_h, view_h], scaleanchor="x", scaleratio=1, fixedrange=True),
                dragmode="pan", shapes=[dict(type='rect', xref='paper', yref='paper', x0=0, y0=0, x1=1, y1=1, line=dict(color='black', width=2))]
            )
            st.plotly_chart(fig_elev, use_container_width=True)

    return n_total, Design_Shear
