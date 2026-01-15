import plotly.graph_objects as go

# =============================================================================
# 1. HELPER TOOLS (เครื่องมือวาดเส้นและป้ายกำกับ)
# =============================================================================
def add_cad_dim(fig, x0, y0, x1, y1, text, type="horiz", offset=0):
    """ วาดเส้นบอกระยะแบบ Engineering Drawing (ขาว-ดำ) """
    color = "black"
    arrow_size = 6
    if type == "horiz":
        y_dim = y0 + offset
        # Extension Lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_dim, line=dict(color=color, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_dim, line=dict(color=color, width=0.5))
        # Main Line
        fig.add_shape(type="line", x0=x0, y0=y_dim, x1=x1, y1=y_dim, line=dict(color=color, width=1))
        # Arrows
        fig.add_annotation(x=x0, y=y_dim, ax=arrow_size, ay=0, arrowhead=2, arrowsize=1.5, arrowcolor=color, text="")
        fig.add_annotation(x=x1, y=y_dim, ax=-arrow_size, ay=0, arrowhead=2, arrowsize=1.5, arrowcolor=color, text="")
        # Text
        fig.add_annotation(x=(x0+x1)/2, y=y_dim, text=f"<b>{text}</b>", showarrow=False, yshift=8 if offset>0 else -8,
                           font=dict(size=11, color=color, family="Arial"), bgcolor="white")

    elif type == "vert":
        x_dim = x0 + offset
        # Extension Lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_dim, y1=y0, line=dict(color=color, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_dim, y1=y1, line=dict(color=color, width=0.5))
        # Main Line
        fig.add_shape(type="line", x0=x_dim, y0=y0, x1=x_dim, y1=y1, line=dict(color=color, width=1))
        # Arrows
        fig.add_annotation(x=x_dim, y=y0, ax=0, ay=-arrow_size, arrowhead=2, arrowsize=1.5, arrowcolor=color, text="")
        fig.add_annotation(x=x_dim, y=y1, ax=0, ay=arrow_size, arrowhead=2, arrowsize=1.5, arrowcolor=color, text="")
        # Text
        fig.add_annotation(x=x_dim, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=12 if offset>0 else -12,
                           font=dict(size=11, color=color, family="Arial"), textangle=-90, bgcolor="white")

def add_leader(fig, x, y, text, ax=30, ay=-30):
    """ ป้ายกำกับแบบมีเส้นชี้ (Callout) """
    fig.add_annotation(
        x=x, y=y, text=text, showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor="black",
        ax=ax, ay=ay, font=dict(size=11, color="black"), bgcolor="white", bordercolor="black", borderpad=2
    )

# =============================================================================
# 2. MAIN DRAWING FUNCTIONS (ฟังก์ชันวาดรูปหลัก)
# =============================================================================
def create_section_view(beam, plate, bolts):
    """ สร้างรูป Section A-A (Top View) """
    fig = go.Figure()
    
    # Unpack Data
    tw = beam['tw']
    b_flange = beam['b']
    w_pl = plate['w']
    t_pl = plate['t']
    l_side = plate['l_side']
    e1 = plate['e1']
    d_bolt = bolts['d']
    n_cols = bolts['cols']
    s_h = bolts['s_h']
    
    # Limits
    zoom_y = max(b_flange, 150) * 0.7
    zoom_x = w_pl + 80

    # 1. Column (Gray Block)
    fig.add_shape(type="rect", x0=-20, y0=-zoom_y, x1=0, y1=zoom_y, line=dict(color="black", width=2), fillcolor="#e5e7eb")
    
    # 2. Beam Web (White) & CL
    fig.add_shape(type="rect", x0=10, y0=-tw/2, x1=zoom_x, y1=tw/2, line=dict(color="black", width=1.5), fillcolor="white")
    fig.add_shape(type="line", x0=-30, y0=0, x1=zoom_x, y1=0, line=dict(color="black", dash="dashdot", width=0.5))

    # 3. Fin Plate & Weld
    py_max = tw/2 + t_pl
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=py_max, line=dict(color="black", width=1.5), fillcolor="white")
    # Weld Triangle
    fig.add_trace(go.Scatter(x=[0, 6, 0, 0], y=[py_max, py_max, py_max+6, py_max], fill="toself", line_color="black", fillcolor="black", mode='lines', hoverinfo='skip'))

    # 4. Bolts
    bx_start = e1
    for i in range(n_cols):
        bx = bx_start + i*s_h
        # Shank
        fig.add_shape(type="rect", x0=bx-d_bolt/2, y0=-tw/2, x1=bx+d_bolt/2, y1=py_max, line_width=1, fillcolor="white")
        # Head
        fig.add_shape(type="rect", x0=bx-d_bolt, y0=py_max, x1=bx+d_bolt, y1=py_max+(d_bolt*0.6), line_width=1, fillcolor="white")
        # Centerline Bolt
        fig.add_shape(type="line", x0=bx, y0=-zoom_y+10, x1=bx, y1=zoom_y-10, line=dict(color="black", dash="dot", width=0.5))

    # --- Dimensions ---
    dim_y = -zoom_y + 20
    curr_x = 0
    add_cad_dim(fig, curr_x, dim_y, curr_x+e1, dim_y, f"{e1:.0f}") # e1
    curr_x += e1
    if n_cols > 1:
        for _ in range(n_cols-1):
            add_cad_dim(fig, curr_x, dim_y, curr_x+s_h, dim_y, f"{s_h:.0f}") # Spacing
            curr_x += s_h
    add_cad_dim(fig, curr_x, dim_y, w_pl, dim_y, f"{l_side:.0f}") # Edge Side
    
    # Callouts
    add_leader(fig, w_pl/2, py_max, f"<b>PL-{t_pl}mm</b>", ax=20, ay=-40)

    # Layout
    fig.update_layout(
        title=dict(text="<b>SECTION A-A</b>", x=0.5, font=dict(size=14, color="black")),
        plot_bgcolor="white", margin=dict(l=10, r=10, t=30, b=10), height=320,
        xaxis=dict(visible=False, range=[-30, zoom_x], fixedrange=True),
        yaxis=dict(visible=False, range=[-zoom_y-10, zoom_y+10], scaleanchor="x", scaleratio=1, fixedrange=True),
        showlegend=False
    )
    return fig

def create_elevation_view(beam, plate, bolts):
    """ สร้างรูป Elevation (Side View) """
    fig = go.Figure()
    
    # Unpack Data
    h_beam = beam['h']
    tf = beam['tf']
    h_pl = plate['h']
    w_pl = plate['w']
    lv = plate['lv']
    e1 = plate['e1']
    s_v = bolts['s_v']
    s_h = bolts['s_h']
    d_bolt = bolts['d']
    n_rows = bolts['rows']
    n_cols = bolts['cols']

    # 1. Beam Outline
    fig.add_shape(type="rect", x0=0, y0=-h_beam/2, x1=w_pl+60, y1=h_beam/2, line=dict(color="black", width=1)) # Outer
    fig.add_shape(type="line", x0=0, y0=h_beam/2-tf, x1=w_pl+60, y1=h_beam/2-tf, line_width=0.5) # Flange Top
    fig.add_shape(type="line", x0=0, y0=-h_beam/2+tf, x1=w_pl+60, y1=-h_beam/2+tf, line_width=0.5) # Flange Bot
    
    # 2. Column
    fig.add_shape(type="rect", x0=-20, y0=-h_beam/2-40, x1=0, y1=h_beam/2+40, line=dict(color="black", width=2), fillcolor="#e5e7eb")

    # 3. Plate
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, line=dict(color="black", width=1.5))

    # 4. Bolts
    by_start = h_pl/2 - lv
    for r in range(n_rows):
        for c in range(n_cols):
            bx = e1 + c*s_h
            by = by_start - r*s_v
            # Circle
            fig.add_shape(type="circle", x0=bx-d_bolt/2, y0=by-d_bolt/2, x1=bx+d_bolt/2, y1=by+d_bolt/2, line_color="black")
            # Cross
            fig.add_shape(type="line", x0=bx-d_bolt/2, y0=by, x1=bx+d_bolt/2, y1=by, line_width=0.5)
            fig.add_shape(type="line", x0=bx, y0=by-d_bolt/2, x1=bx, y1=by+d_bolt/2, line_width=0.5)

    # --- Dimensions ---
    dim_x = w_pl + 20
    curr_y = h_pl/2
    
    # Top Edge
    add_cad_dim(fig, dim_x, curr_y, dim_x, curr_y-lv, f"{lv:.0f}", "vert")
    curr_y -= lv
    # Pitch
    if n_rows > 1:
        for _ in range(n_rows-1):
            add_cad_dim(fig, dim_x, curr_y, dim_x, curr_y-s_v, f"{s_v:.0f}", "vert")
            curr_y -= s_v
    # Bot Edge
    add_cad_dim(fig, dim_x, curr_y, dim_x, -h_pl/2, f"{lv:.0f}", "vert")

    # Total Height
    add_cad_dim(fig, dim_x+30, h_pl/2, dim_x+30, -h_pl/2, f"H={h_pl:.0f}", "vert", offset=0)
    
    # Callout
    add_leader(fig, e1, by_start, f"<b>{n_rows*n_cols}-M{d_bolt}</b>", ax=20, ay=-30)

    # Layout
    fig.update_layout(
        title=dict(text="<b>ELEVATION</b>", x=0.5, font=dict(size=14, color="black")),
        plot_bgcolor="white", margin=dict(l=10, r=10, t=30, b=10), height=320,
        xaxis=dict(visible=False, range=[-30, w_pl+70], fixedrange=True),
        yaxis=dict(visible=False, range=[-h_beam/2-20, h_beam/2+20], scaleanchor="x", scaleratio=1, fixedrange=True),
        showlegend=False
    )
    return fig
