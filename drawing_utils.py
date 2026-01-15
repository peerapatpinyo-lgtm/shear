import plotly.graph_objects as go

# =============================================================================
# 🛠️ HELPER TOOLS: CLEAN STYLE
# =============================================================================
def add_cad_dim(fig, x0, y0, x1, y1, text, type="horiz", offset=0):
    """ เส้นบอกระยะแบบเรียบง่าย (Clean Dimension) """
    color = "black"
    arrow_size = 6
    if type == "horiz":
        y_dim = y0 + offset
        # Lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_dim, line=dict(color=color, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_dim, line=dict(color=color, width=0.5))
        fig.add_shape(type="line", x0=x0, y0=y_dim, x1=x1, y1=y_dim, line=dict(color=color, width=1))
        # Arrows
        fig.add_annotation(x=x0, y=y_dim, ax=arrow_size, ay=0, arrowhead=2, arrowsize=1.5, arrowcolor=color, text="")
        fig.add_annotation(x=x1, y=y_dim, ax=-arrow_size, ay=0, arrowhead=2, arrowsize=1.5, arrowcolor=color, text="")
        # Text
        fig.add_annotation(x=(x0+x1)/2, y=y_dim, text=f"<b>{text}</b>", showarrow=False, yshift=8 if offset>0 else -8,
                           font=dict(size=11, color=color, family="Arial"), bgcolor="white")

    elif type == "vert":
        x_dim = x0 + offset
        # Lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_dim, y1=y0, line=dict(color=color, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_dim, y1=y1, line=dict(color=color, width=0.5))
        fig.add_shape(type="line", x0=x_dim, y0=y0, x1=x_dim, y1=y1, line=dict(color=color, width=1))
        # Arrows
        fig.add_annotation(x=x_dim, y=y0, ax=0, ay=-arrow_size, arrowhead=2, arrowsize=1.5, arrowcolor=color, text="")
        fig.add_annotation(x=x_dim, y=y1, ax=0, ay=arrow_size, arrowhead=2, arrowsize=1.5, arrowcolor=color, text="")
        # Text
        fig.add_annotation(x=x_dim, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=12 if offset>0 else -12,
                           font=dict(size=11, color=color, family="Arial"), textangle=-90, bgcolor="white")

def add_leader(fig, x, y, text, ax=30, ay=-30):
    """ ป้ายชี้บอก (Callout) """
    fig.add_annotation(
        x=x, y=y, text=text, showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor="#333",
        ax=ax, ay=ay, font=dict(size=11, color="black"), bgcolor="#f8f9fa", bordercolor="#ddd", borderpad=3
    )

def add_centerline(fig, x0, y0, x1, y1):
    fig.add_shape(type="line", x0=x0, y0=y0, x1=x1, y1=y1, line=dict(color="#d55", width=1, dash="dashdot"), opacity=0.5)

# =============================================================================
# 1. PLAN VIEW (TOP)
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, bf = beam['tw'], beam['b']
    w_pl, t_pl, e1, l_side = plate['w'], plate['t'], plate['e1'], plate['l_side']
    d_bolt, n_cols, s_h = bolts['d'], bolts['cols'], bolts['s_h']
    
    zoom_y = max(bf, 160) * 0.7
    zoom_x = w_pl + 80

    # Column (Gray Block)
    fig.add_shape(type="rect", x0=-20, y0=-zoom_y, x1=0, y1=zoom_y, line=dict(color="black", width=2), fillcolor="#e2e8f0")
    
    # Beam Web (White)
    fig.add_shape(type="rect", x0=10, y0=-tw/2, x1=zoom_x, y1=tw/2, line=dict(color="black", width=1.5), fillcolor="white")
    add_centerline(fig, -30, 0, zoom_x, 0)

    # Fin Plate
    py_max = tw/2 + t_pl
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=py_max, line=dict(color="black", width=1.5), fillcolor="#f1f5f9")
    # Weld Triangle (Simple)
    fig.add_trace(go.Scatter(x=[0, 6, 0, 0], y=[py_max, py_max, py_max+6, py_max], fill="toself", line_color="black", fillcolor="black", mode='lines', hoverinfo='skip'))

    # Bolts
    bx_start = e1
    for i in range(n_cols):
        bx = bx_start + i*s_h
        # Shank & Head
        fig.add_shape(type="rect", x0=bx-d_bolt/2, y0=-tw/2, x1=bx+d_bolt/2, y1=py_max, line_width=1, fillcolor="white")
        fig.add_shape(type="rect", x0=bx-d_bolt, y0=py_max, x1=bx+d_bolt, y1=py_max+(d_bolt*0.6), line_width=1, fillcolor="white")
        add_centerline(fig, bx, -zoom_y+20, bx, zoom_y-20)

    # Dimensions
    dim_y = -zoom_y + 20
    curr_x = 0
    add_cad_dim(fig, curr_x, dim_y, curr_x+e1, dim_y, f"{e1:.0f}") # e1
    curr_x += e1
    if n_cols > 1:
        for _ in range(n_cols-1):
            add_cad_dim(fig, curr_x, dim_y, curr_x+s_h, dim_y, f"{s_h:.0f}") # Pitch
            curr_x += s_h
    add_cad_dim(fig, curr_x, dim_y, w_pl, dim_y, f"{l_side:.0f}") # Edge

    # Label
    add_leader(fig, w_pl/2, py_max, f"<b>PL-{t_pl}mm</b>", ax=20, ay=-40)

    fig.update_layout(title="<b>PLAN VIEW</b>", plot_bgcolor="white", margin=dict(l=10,r=10,t=30,b=10), height=280,
                      xaxis=dict(visible=False, range=[-30, zoom_x], fixedrange=True),
                      yaxis=dict(visible=False, range=[-zoom_y, zoom_y], scaleanchor="x", scaleratio=1, fixedrange=True), showlegend=False)
    return fig

# =============================================================================
# 2. FRONT VIEW (ELEVATION)
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_beam, tf = beam['h'], beam['tf']
    h_pl, w_pl, lv, e1 = plate['h'], plate['w'], plate['lv'], plate['e1']
    s_v, s_h = bolts['s_v'], bolts['s_h']
    d_bolt, n_rows, n_cols = bolts['d'], bolts['rows'], bolts['cols']

    # Beam Outline
    fig.add_shape(type="rect", x0=0, y0=-h_beam/2, x1=w_pl+60, y1=h_beam/2, line=dict(color="gray", width=0.5, dash="dash"))
    fig.add_shape(type="line", x0=0, y0=h_beam/2-tf, x1=w_pl+60, y1=h_beam/2-tf, line=dict(color="gray", width=0.5, dash="dash"))
    fig.add_shape(type="line", x0=0, y0=-h_beam/2+tf, x1=w_pl+60, y1=-h_beam/2+tf, line=dict(color="gray", width=0.5, dash="dash"))

    # Column
    fig.add_shape(type="rect", x0=-20, y0=-h_beam/2-20, x1=0, y1=h_beam/2+20, line=dict(color="black", width=2), fillcolor="#e2e8f0")

    # Plate
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, line=dict(color="black", width=1.5), fillcolor="white")

    # Bolts
    by_start = h_pl/2 - lv
    for r in range(n_rows):
        for c in range(n_cols):
            bx = e1 + c*s_h
            by = by_start - r*s_v
            fig.add_shape(type="circle", x0=bx-d_bolt/2, y0=by-d_bolt/2, x1=bx+d_bolt/2, y1=by+d_bolt/2, line_color="black")
            fig.add_shape(type="line", x0=bx-d_bolt/2, y0=by, x1=bx+d_bolt/2, y1=by, line_width=0.5)
            fig.add_shape(type="line", x0=bx, y0=by-d_bolt/2, x1=bx, y1=by+d_bolt/2, line_width=0.5)

    # Dimensions
    dim_x = w_pl + 15
    curr_y = h_pl/2
    
    add_cad_dim(fig, dim_x, curr_y, dim_x, curr_y-lv, f"{lv:.0f}", "vert")
    curr_y -= lv
    if n_rows > 1:
        for _ in range(n_rows-1):
            add_cad_dim(fig, dim_x, curr_y, dim_x, curr_y-s_v, f"{s_v:.0f}", "vert")
            curr_y -= s_v
    add_cad_dim(fig, dim_x, curr_y, dim_x, -h_pl/2, f"{lv:.0f}", "vert")

    # Total Height
    add_cad_dim(fig, dim_x+30, h_pl/2, dim_x+30, -h_pl/2, f"H={h_pl:.0f}", "vert", offset=0)

    fig.update_layout(title="<b>ELEVATION</b>", plot_bgcolor="white", margin=dict(l=10,r=30,t=30,b=10), height=280,
                      xaxis=dict(visible=False, range=[-30, w_pl+70], fixedrange=True),
                      yaxis=dict(visible=False, range=[-h_beam/2-40, h_beam/2+40], scaleanchor="x", scaleratio=1, fixedrange=True), showlegend=False)
    return fig

# =============================================================================
# 3. SIDE VIEW (SECTION)
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    t_pl, h_pl, lv = plate['t'], plate['h'], plate['lv']
    d_bolt, n_rows, s_v = bolts['d'], bolts['rows'], bolts['s_v']

    # Column Face
    fig.add_shape(type="line", x0=-b/2, y0=-h/2-20, x1=-b/2, y1=h/2+20, line=dict(color="black", width=2))
    
    # I-Beam Section (Solid White)
    fig.add_shape(type="rect", x0=-b/2, y0=h/2-tf, x1=b/2, y1=h/2, line=dict(color="black", width=1.5), fillcolor="white")
    fig.add_shape(type="rect", x0=-b/2, y0=-h/2, x1=b/2, y1=-h/2+tf, line=dict(color="black", width=1.5), fillcolor="white")
    fig.add_shape(type="rect", x0=-tw/2, y0=-h/2+tf, x1=tw/2, y1=h/2-tf, line=dict(color="black", width=1.5), fillcolor="white")

    # Plate
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, line=dict(color="black", width=1.5), fillcolor="#ddd")

    # Bolts
    bolt_x = tw/2 + t_pl
    by_start = h_pl/2 - lv
    for r in range(n_rows):
        by = by_start - r*s_v
        fig.add_shape(type="rect", x0=bolt_x, y0=by-d_bolt/2, x1=bolt_x+(d_bolt*0.6), y1=by+d_bolt/2, line=dict(color="black", width=1), fillcolor="white")
        add_centerline(fig, -b/2, by, b/2, by)

    add_centerline(fig, 0, -h/2-30, 0, h/2+30)

    # Label
    add_leader(fig, b/2, h/2-tf/2, f"<b>{h:.0f}x{b:.0f}</b>", ax=30, ay=-20)

    fig.update_layout(title="<b>SIDE VIEW</b>", plot_bgcolor="white", margin=dict(l=10,r=10,t=30,b=10), height=280,
                      xaxis=dict(visible=False, range=[-b/2-30, b/2+50], fixedrange=True),
                      yaxis=dict(visible=False, range=[-h/2-40, h/2+40], scaleanchor="x", scaleratio=1, fixedrange=True), showlegend=False)
    return fig
