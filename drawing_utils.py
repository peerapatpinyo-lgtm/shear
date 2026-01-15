import plotly.graph_objects as go

# =============================================================================
# 🛠️ HELPER TOOLS: CAD STANDARD
# =============================================================================
def add_cad_dim(fig, x0, y0, x1, y1, text, type="horiz", offset=0, color="black", text_size=11):
    """ สร้างเส้นบอกระยะมาตรฐาน (Chain Dimension) """
    arrow_size = 6
    line_style = dict(color=color, width=1)
    ext_style = dict(color=color, width=0.5) # เส้น Extension บางๆ
    
    if type == "horiz":
        y_dim = y0 + offset
        # Ext Lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_dim, line=ext_style)
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_dim, line=ext_style)
        # Main Line
        fig.add_shape(type="line", x0=x0, y0=y_dim, x1=x1, y1=y_dim, line=line_style)
        # Arrows
        fig.add_annotation(x=x0, y=y_dim, ax=arrow_size, ay=0, arrowhead=2, arrowsize=1.5, arrowcolor=color, text="")
        fig.add_annotation(x=x1, y=y_dim, ax=-arrow_size, ay=0, arrowhead=2, arrowsize=1.5, arrowcolor=color, text="")
        # Text
        fig.add_annotation(x=(x0+x1)/2, y=y_dim, text=f"<b>{text}</b>", showarrow=False, yshift=8 if offset>0 else -8,
                           font=dict(size=text_size, color=color, family="Arial"), bgcolor="white", opacity=1)

    elif type == "vert":
        x_dim = x0 + offset
        # Ext Lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_dim, y1=y0, line=ext_style)
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_dim, y1=y1, line=ext_style)
        # Main Line
        fig.add_shape(type="line", x0=x_dim, y0=y0, x1=x_dim, y1=y1, line=line_style)
        # Arrows
        fig.add_annotation(x=x_dim, y=y0, ax=0, ay=-arrow_size, arrowhead=2, arrowsize=1.5, arrowcolor=color, text="")
        fig.add_annotation(x=x_dim, y=y1, ax=0, ay=arrow_size, arrowhead=2, arrowsize=1.5, arrowcolor=color, text="")
        # Text
        fig.add_annotation(x=x_dim, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=12 if offset>0 else -12,
                           font=dict(size=text_size, color=color, family="Arial"), textangle=-90, bgcolor="white", opacity=1)

def add_callout(fig, x, y, text, ax=40, ay=-40, align="left"):
    """ ป้ายชี้บอกชื่อชิ้นส่วน (Component Label) """
    fig.add_annotation(
        x=x, y=y, text=text, showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.5, arrowcolor="#333",
        ax=ax, ay=ay, font=dict(size=11, color="black"), bgcolor="#f8f9fa", bordercolor="#333", borderwidth=1, borderpad=3,
        align=align
    )

def add_centerline(fig, x0, y0, x1, y1):
    """ เส้น Centerline สีแดงจางๆ """
    fig.add_shape(type="line", x0=x0, y0=y0, x1=x1, y1=y1, line=dict(color="red", width=0.8, dash="dashdot"), opacity=0.6)

# =============================================================================
# 📐 VIEW 1: PLAN VIEW (TOP)
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, bf = beam['tw'], beam['b']
    w_pl, t_pl, e1, l_side = plate['w'], plate['t'], plate['e1'], plate['l_side']
    d_bolt, n_cols, s_h = bolts['d'], bolts['cols'], bolts['s_h']
    
    zoom_y = max(bf, 160) * 0.7
    zoom_x = w_pl + 80

    # 1. Column (Section)
    fig.add_shape(type="rect", x0=-20, y0=-zoom_y, x1=0, y1=zoom_y, line=dict(color="black", width=2), fillcolor="#cbd5e1") # Hatch gray
    
    # 2. Beam Web
    fig.add_shape(type="rect", x0=10, y0=-tw/2, x1=zoom_x, y1=tw/2, line=dict(color="black", width=1.5), fillcolor="white")
    add_centerline(fig, -30, 0, zoom_x, 0)
    
    # 3. Fin Plate
    py_max = tw/2 + t_pl
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=py_max, line=dict(color="black", width=1.5), fillcolor="#f1f5f9")
    # Weld
    fig.add_trace(go.Scatter(x=[0, 6, 0, 0], y=[py_max, py_max, py_max+6, py_max], fill="toself", line_color="black", fillcolor="black", mode='lines', hoverinfo='skip'))

    # 4. Bolts
    bx_start = e1
    for i in range(n_cols):
        bx = bx_start + i*s_h
        fig.add_shape(type="rect", x0=bx-d_bolt/2, y0=-tw/2, x1=bx+d_bolt/2, y1=py_max, line_width=1, fillcolor="white") # Shank
        fig.add_shape(type="rect", x0=bx-d_bolt, y0=py_max, x1=bx+d_bolt, y1=py_max+(d_bolt*0.6), line_width=1, fillcolor="white") # Head
        add_centerline(fig, bx, -zoom_y+20, bx, zoom_y-20)

    # --- DIMENSIONS ---
    dim_y = -zoom_y + 25
    curr_x = 0
    # Gap (e1)
    add_cad_dim(fig, curr_x, dim_y, curr_x+e1, dim_y, f"e1={e1:.0f}")
    curr_x += e1
    # Pitch (sh)
    if n_cols > 1:
        for _ in range(n_cols-1):
            add_cad_dim(fig, curr_x, dim_y, curr_x+s_h, dim_y, f"sh={s_h:.0f}")
            curr_x += s_h
    # Edge (Ls)
    add_cad_dim(fig, curr_x, dim_y, w_pl, dim_y, f"Ls={l_side:.0f}")

    # Callouts
    add_callout(fig, w_pl/2, py_max, f"<b>Fin Plate</b><br>t={t_pl}mm", ax=20, ay=-40)
    add_callout(fig, w_pl+20, 0, f"<b>Beam Web</b><br>tw={tw}", ax=20, ay=30)

    fig.update_layout(title="<b>PLAN VIEW</b> (Top Section)", plot_bgcolor="white", margin=dict(l=10,r=10,t=30,b=10), height=300,
                      xaxis=dict(visible=False, range=[-30, zoom_x], fixedrange=True),
                      yaxis=dict(visible=False, range=[-zoom_y, zoom_y], scaleanchor="x", scaleratio=1, fixedrange=True), showlegend=False)
    return fig

# =============================================================================
# 📐 VIEW 2: ELEVATION (FRONT)
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_beam, tf = beam['h'], beam['tf']
    h_pl, w_pl, lv, e1 = plate['h'], plate['w'], plate['lv'], plate['e1']
    s_v, s_h = bolts['s_v'], bolts['s_h']
    d_bolt, n_rows, n_cols = bolts['d'], bolts['rows'], bolts['cols']

    # 1. Beam Outline (Phantom)
    fig.add_shape(type="rect", x0=0, y0=-h_beam/2, x1=w_pl+60, y1=h_beam/2, line=dict(color="gray", width=0.5, dash="dash"))
    fig.add_shape(type="line", x0=0, y0=h_beam/2-tf, x1=w_pl+60, y1=h_beam/2-tf, line=dict(color="gray", width=0.5, dash="dash"))
    fig.add_shape(type="line", x0=0, y0=-h_beam/2+tf, x1=w_pl+60, y1=-h_beam/2+tf, line=dict(color="gray", width=0.5, dash="dash"))

    # 2. Column
    fig.add_shape(type="rect", x0=-20, y0=-h_beam/2-20, x1=0, y1=h_beam/2+20, line=dict(color="black", width=2), fillcolor="#cbd5e1")

    # 3. Plate
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, line=dict(color="black", width=1.5), fillcolor="white")

    # 4. Bolts
    by_start = h_pl/2 - lv
    for r in range(n_rows):
        for c in range(n_cols):
            bx = e1 + c*s_h
            by = by_start - r*s_v
            fig.add_shape(type="circle", x0=bx-d_bolt/2, y0=by-d_bolt/2, x1=bx+d_bolt/2, y1=by+d_bolt/2, line_color="black")
            fig.add_shape(type="line", x0=bx-d_bolt/2, y0=by, x1=bx+d_bolt/2, y1=by, line_width=0.5) # Cross
            fig.add_shape(type="line", x0=bx, y0=by-d_bolt/2, x1=bx, y1=by+d_bolt/2, line_width=0.5) # Cross

    add_centerline(fig, -10, 0, w_pl+20, 0) # Plate Center

    # --- DIMENSIONS ---
    dim_x = w_pl + 15
    curr_y = h_pl/2
    
    # Vert Chain
    add_cad_dim(fig, dim_x, curr_y, dim_x, curr_y-lv, f"Lv={lv:.0f}", "vert")
    curr_y -= lv
    if n_rows > 1:
        for _ in range(n_rows-1):
            add_cad_dim(fig, dim_x, curr_y, dim_x, curr_y-s_v, f"sv={s_v:.0f}", "vert")
            curr_y -= s_v
    add_cad_dim(fig, dim_x, curr_y, dim_x, -h_pl/2, f"Lv={lv:.0f}", "vert")

    # Overall Height
    add_cad_dim(fig, dim_x+30, h_pl/2, dim_x+30, -h_pl/2, f"H={h_pl:.0f}", "vert", offset=0)

    # Callouts
    add_callout(fig, e1, by_start, f"<b>{n_rows*n_cols} Bolts</b><br>M{d_bolt}", ax=30, ay=-40)
    add_callout(fig, -10, -h_beam/2-10, "<b>Column</b>", ax=-20, ay=20)

    fig.update_layout(title="<b>ELEVATION</b> (Front View)", plot_bgcolor="white", margin=dict(l=10,r=30,t=30,b=10), height=300,
                      xaxis=dict(visible=False, range=[-30, w_pl+70], fixedrange=True),
                      yaxis=dict(visible=False, range=[-h_beam/2-40, h_beam/2+40], scaleanchor="x", scaleratio=1, fixedrange=True), showlegend=False)
    return fig

# =============================================================================
# 📐 VIEW 3: SIDE VIEW (SECTION)
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    t_pl, h_pl, lv = plate['t'], plate['h'], plate['lv']
    d_bolt, n_rows, s_v = bolts['d'], bolts['rows'], bolts['s_v']

    # 1. Column Face
    fig.add_shape(type="rect", x0=-b/2-30, y0=-h/2-20, x1=-b/2, y1=h/2+20, line_width=0, fillcolor="#e2e8f0")
    fig.add_shape(type="line", x0=-b/2, y0=-h/2-20, x1=-b/2, y1=h/2+20, line=dict(color="black", width=2))

    # 2. I-Beam Section
    # Flanges
    fig.add_shape(type="rect", x0=-b/2, y0=h/2-tf, x1=b/2, y1=h/2, line=dict(color="black", width=1.5), fillcolor="white") # Top
    fig.add_shape(type="rect", x0=-b/2, y0=-h/2, x1=b/2, y1=-h/2+tf, line=dict(color="black", width=1.5), fillcolor="white") # Bot
    # Web
    fig.add_shape(type="rect", x0=-tw/2, y0=-h/2+tf, x1=tw/2, y1=h/2-tf, line=dict(color="black", width=1.5), fillcolor="white")
    
    # 3. Plate (Side)
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, line=dict(color="black", width=1.5), fillcolor="#cbd5e1")
    
    # 4. Bolts (Side Heads)
    bolt_x = tw/2 + t_pl
    by_start = h_pl/2 - lv
    for r in range(n_rows):
        by = by_start - r*s_v
        fig.add_shape(type="rect", x0=bolt_x, y0=by-d_bolt/2, x1=bolt_x+(d_bolt*0.6), y1=by+d_bolt/2, line=dict(color="black", width=1), fillcolor="white")
        add_centerline(fig, -b/2, by, b/2, by)

    add_centerline(fig, 0, -h/2-30, 0, h/2+30)

    # Callouts
    add_callout(fig, b/2, h/2, f"<b>Beam</b><br>{h:.0f}x{b:.0f}", ax=30, ay=-20)
    add_callout(fig, tw/2+t_pl, 0, "<b>Fin Plate</b>", ax=40, ay=0)

    fig.update_layout(title="<b>SIDE VIEW</b> (Section)", plot_bgcolor="white", margin=dict(l=10,r=10,t=30,b=10), height=300,
                      xaxis=dict(visible=False, range=[-b/2-40, b/2+60], fixedrange=True),
                      yaxis=dict(visible=False, range=[-h/2-40, h/2+40], scaleanchor="x", scaleratio=1, fixedrange=True), showlegend=False)
    return fig
