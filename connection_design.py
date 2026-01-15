import streamlit as st
import plotly.graph_objects as go

# ==========================================
# 1. HELPER: CAD STYLE DIMENSIONS (BLACK & WHITE)
# ==========================================
def add_cad_dim(fig, x0, y0, x1, y1, text, type="horiz", offset=0):
    """ สร้างเส้นบอกระยะแบบ Drawing ขาว-ดำ หัวลูกศรทึบ """
    color = "black"
    arrow_size = 6
    # เส้นบอกระยะ (Dimension Line) - เส้นบาง
    dim_line_width = 1
    # เส้นช่วยบอกระยะ (Extension Line) - เส้นบาง
    ext_line_width = 0.8
    
    if type == "horiz":
        y_dim = y0 + offset
        # Extension Lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_dim, line=dict(color=color, width=ext_line_width))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_dim, line=dict(color=color, width=ext_line_width))
        # Main Dimension Line
        fig.add_shape(type="line", x0=x0, y0=y_dim, x1=x1, y1=y_dim, line=dict(color=color, width=dim_line_width))
        # Arrowheads (Filled Triangles)
        fig.add_annotation(x=x0, y=y_dim, ax=arrow_size, ay=0, arrowhead=2, arrowsize=1.5, arrowwidth=1, arrowcolor=color, text="")
        fig.add_annotation(x=x1, y=y_dim, ax=-arrow_size, ay=0, arrowhead=2, arrowsize=1.5, arrowwidth=1, arrowcolor=color, text="")
        # Text Label (White Background to break line)
        fig.add_annotation(x=(x0+x1)/2, y=y_dim, text=f"<b>{text}</b>", showarrow=False, yshift=8 if offset>0 else -8,
                           font=dict(size=11, color=color, family="Arial"), bgcolor="white", opacity=1)

    elif type == "vert":
        x_dim = x0 + offset
        # Extension Lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_dim, y1=y0, line=dict(color=color, width=ext_line_width))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_dim, y1=y1, line=dict(color=color, width=ext_line_width))
        # Main Dimension Line
        fig.add_shape(type="line", x0=x_dim, y0=y0, x1=x_dim, y1=y1, line=dict(color=color, width=dim_line_width))
        # Arrowheads
        fig.add_annotation(x=x_dim, y=y0, ax=0, ay=-arrow_size, arrowhead=2, arrowsize=1.5, arrowwidth=1, arrowcolor=color, text="")
        fig.add_annotation(x=x_dim, y=y1, ax=0, ay=arrow_size, arrowhead=2, arrowsize=1.5, arrowwidth=1, arrowcolor=color, text="")
        # Text Label
        fig.add_annotation(x=x_dim, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=12 if offset>0 else -12,
                           font=dict(size=11, color=color, family="Arial"), textangle=-90, bgcolor="white", opacity=1)

def add_leader_label(fig, x, y, text, ax=30, ay=-30):
    """ ป้ายกำกับพร้อมเส้นชี้ (Leader Line) แบบ CAD """
    fig.add_annotation(
        x=x, y=y, text=text,
        showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor="black",
        ax=ax, ay=ay,
        font=dict(size=11, color="black", family="Arial"),
        bgcolor="white", bordercolor="black", borderwidth=1, borderpad=3,
        align="left"
    )

# ==========================================
# 2. MAIN FUNCTION: MONOCHROME CAD STYLE
# ==========================================
def render_connection_tab(V_design, bolt_size, method, is_lrfd, section_data, conn_type, bolt_grade, T_design=0):
    
    # --- SETUP PARAMETERS ---
    d_mm = int(bolt_size[1:]) 
    h_beam = float(section_data.get('h', 300))
    b_beam = float(section_data.get('b', 150))
    tf_beam = float(section_data.get('tf', 10))
    tw_beam = float(section_data.get('tw', 8))
    clear_web_h = h_beam - 2*(tf_beam * 1.5) 

    # --- INPUTS (Simplified Layout) ---
    st.markdown("### 🏗️ Connection Detail (Black & White CAD Mode)")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        n_rows = st.number_input("Rows (V)", 2, 12, 3)
    with c2:
        n_cols = st.number_input("Cols (H)", 1, 3, 2)
    with c3:
        # Auto Pitch Logic
        def_sv = max(75.0, 3.0*d_mm)
        s_v = st.number_input("Pitch V", 0.0, 300.0, float(def_sv))
    with c4:
        def_sh = max(60.0, 3.0*d_mm)
        s_h = st.number_input("Pitch H", 0.0, 150.0, float(def_sh))

    c5, c6, c7 = st.columns(3)
    with c5:
        e1_mm = st.number_input("Gap (e1)", 10.0, 100.0, 50.0)
    with c6:
        # Auto Height Logic
        min_h = (n_rows-1)*s_v + 80
        plate_h = st.number_input("Plate H", min_value=float(min_h), value=float(min_h))
    with c7:
        plate_w = e1_mm + (n_cols-1)*s_h + 40 # Auto width based on inputs
        t_plate = st.number_input("Plate Thk", 6.0, 25.0, 10.0)

    real_lv = (plate_h - (n_rows-1)*s_v) / 2
    l_side = plate_w - (e1_mm + (n_cols-1)*s_h)
    
    st.divider()

    # =========================================================
    # DRAWING AREA (MONOCHROME)
    # =========================================================
    col_sec, col_elev = st.columns([1.2, 1])

    # --- VIEW 1: TOP SECTION (SECTION A-A) ---
    with col_sec:
        fig_sec = go.Figure()
        
        zoom_y = max(b_beam, 180) * 0.7
        zoom_x_end = plate_w + 80
        
        # 1. COLUMN (Hatch Style - Simulated with Gray)
        # ใช้สีเทาอ่อนและเส้นขอบดำหนา แทนเสา
        fig_sec.add_shape(type="rect", x0=-20, y0=-zoom_y, x1=0, y1=zoom_y, 
                          line=dict(color="black", width=2), fillcolor="#e5e7eb")
        
        # 2. BEAM WEB (Thick Lines)
        ecc = 0 # Assume centered for simplicity in this view
        fig_sec.add_shape(type="rect", x0=10, y0=ecc-tw_beam/2, x1=zoom_x_end, y1=ecc+tw_beam/2, 
                          line=dict(color="black", width=1.5), fillcolor="white")
        # BEAM FLANGE (Hidden Lines - Dashed)
        fig_sec.add_shape(type="rect", x0=10, y0=ecc-b_beam/2, x1=zoom_x_end, y1=ecc+b_beam/2, 
                          line=dict(color="black", dash="dash", width=1))
        # CENTERLINE
        fig_sec.add_shape(type="line", x0=-30, y0=0, x1=zoom_x_end, y1=0, 
                          line=dict(color="black", dash="dashdot", width=0.5))

        # 3. FIN PLATE (Solid Outline, White Fill)
        # สมมติวางขวา
        py_min = tw_beam/2
        py_max = tw_beam/2 + t_plate
        fig_sec.add_shape(type="rect", x0=0, y0=py_min, x1=plate_w, y1=py_max, 
                          line=dict(color="black", width=2), fillcolor="white")
        
        # Weld (Solid Triangle)
        fig_sec.add_trace(go.Scatter(x=[0, 6, 0, 0], y=[py_max, py_max, py_max+6, py_max], 
                                     fill="toself", fillcolor="black", line_color="black", mode='lines', hoverinfo='skip'))

        # 4. BOLTS (Rectangle with Centerline)
        b_start_x = e1_mm
        for c in range(n_cols):
            bx = b_start_x + c*s_h
            # ตัวน็อต (Bolt Shank)
            fig_sec.add_shape(type="rect", x0=bx-d_mm/2, y0=-tw_beam/2, x1=bx+d_mm/2, y1=py_max, 
                              line=dict(color="black", width=1), fillcolor="white")
            # หัวน็อต (Head)
            fig_sec.add_shape(type="rect", x0=bx-d_mm, y0=py_max, x1=bx+d_mm, y1=py_max+(d_mm*0.6), 
                              line=dict(color="black", width=1), fillcolor="white")
            # เส้น Centerline ผ่ากลางน็อต
            fig_sec.add_shape(type="line", x0=bx, y0=-zoom_y, x1=bx, y1=zoom_y, 
                              line=dict(color="black", dash="dot", width=0.5))

        # --- DIMENSIONS (CAD STYLE) ---
        dim_y = -zoom_y + 20
        curr_x = 0
        
        # e1
        add_cad_dim(fig_sec, curr_x, dim_y, curr_x+e1_mm, dim_y, f"{e1_mm:.0f}")
        curr_x += e1_mm
        
        # Spacing
        if n_cols > 1:
            for _ in range(n_cols-1):
                add_cad_dim(fig_sec, curr_x, dim_y, curr_x+s_h, dim_y, f"{s_h:.0f}")
                curr_x += s_h
        
        # Edge
        add_cad_dim(fig_sec, curr_x, dim_y, plate_w, dim_y, f"{l_side:.0f}")

        # Label
        add_leader_label(fig_sec, plate_w/2, py_max, f"<b>PL-{t_plate:.0f}mm</b>", ax=20, ay=-40)

        # Layout Settings (Strictly Black/White)
        fig_sec.update_layout(
            title=dict(text="<b>SECTION A-A</b>", x=0.5, font=dict(size=14, color="black")),
            plot_bgcolor="white", paper_bgcolor="white",
            height=350, margin=dict(l=10, r=10, t=40, b=10),
            xaxis=dict(visible=False, range=[-30, zoom_x_end], fixedrange=True),
            yaxis=dict(visible=False, range=[-zoom_y-10, zoom_y+10], scaleanchor="x", scaleratio=1, fixedrange=True),
            showlegend=False
        )
        st.plotly_chart(fig_sec, use_container_width=True)

    # --- VIEW 2: ELEVATION (SIDE VIEW) ---
    with col_elev:
        fig_elev = go.Figure()
        
        # 1. BEAM (Outline only)
        h_half = h_beam/2
        fig_elev.add_shape(type="rect", x0=0, y0=-h_half, x1=plate_w+60, y1=h_half, line=dict(color="black", width=1)) # Outer
        fig_elev.add_shape(type="line", x0=0, y0=h_half-tf_beam, x1=plate_w+60, y1=h_half-tf_beam, line=dict(color="black", width=0.5)) # Top Flange
        fig_elev.add_shape(type="line", x0=0, y0=-h_half+tf_beam, x1=plate_w+60, y1=-h_half+tf_beam, line=dict(color="black", width=0.5)) # Bot Flange

        # 2. COLUMN
        fig_elev.add_shape(type="rect", x0=-20, y0=-h_half-50, x1=0, y1=h_half+50, 
                           line=dict(color="black", width=2), fillcolor="#e5e7eb")

        # 3. PLATE
        fig_elev.add_shape(type="rect", x0=0, y0=-plate_h/2, x1=plate_w, y1=plate_h/2, 
                           line=dict(color="black", width=1.5)) # Plate Outline

        # 4. BOLTS (Circle with Cross)
        b_start_y = (plate_h/2) - real_lv
        for r in range(n_rows):
            for c in range(n_cols):
                bx = e1_mm + c*s_h
                by = b_start_y - r*s_v
                # Circle
                fig_elev.add_shape(type="circle", x0=bx-d_mm/2, y0=by-d_mm/2, x1=bx+d_mm/2, y1=by+d_mm/2, 
                                   line=dict(color="black", width=1))
                # Cross (+)
                fig_elev.add_shape(type="line", x0=bx-d_mm/2, y0=by, x1=bx+d_mm/2, y1=by, line=dict(color="black", width=0.5))
                fig_elev.add_shape(type="line", x0=bx, y0=by-d_mm/2, x1=bx, y1=by+d_mm/2, line=dict(color="black", width=0.5))

        # --- DIMENSIONS (Vertical) ---
        dim_x = plate_w + 15
        curr_y = plate_h/2
        
        # Top Edge
        add_cad_dim(fig_elev, dim_x, curr_y, dim_x, curr_y-real_lv, f"{real_lv:.0f}", "vert")
        curr_y -= real_lv
        
        # Pitch
        if n_rows > 1:
            for _ in range(n_rows-1):
                add_cad_dim(fig_elev, dim_x, curr_y, dim_x, curr_y-s_v, f"{s_v:.0f}", "vert")
                curr_y -= s_v
        
        # Bot Edge
        add_cad_dim(fig_elev, dim_x, curr_y, dim_x, -plate_h/2, f"{real_lv:.0f}", "vert")

        # Total Height
        add_cad_dim(fig_elev, dim_x+25, plate_h/2, dim_x+25, -plate_h/2, f"H={plate_h:.0f}", "vert", offset=0)

        # Label
        add_leader_label(fig_elev, e1_mm, b_start_y, f"<b>{n_rows*n_cols}-M{d_mm}</b>", ax=20, ay=-30)

        fig_elev.update_layout(
            title=dict(text="<b>ELEVATION</b>", x=0.5, font=dict(size=14, color="black")),
            plot_bgcolor="white", paper_bgcolor="white",
            height=350, margin=dict(l=10, r=10, t=40, b=10),
            xaxis=dict(visible=False, range=[-30, plate_w+60], fixedrange=True),
            yaxis=dict(visible=False, range=[-h_half-20, h_half+20], scaleanchor="x", scaleratio=1, fixedrange=True),
            showlegend=False
        )
        st.plotly_chart(fig_elev, use_container_width=True)

    return n_rows*n_cols, 10000
