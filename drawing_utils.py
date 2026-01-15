import plotly.graph_objects as go

# =============================================================================
# 🛠️ HELPER TOOLS (เครื่องมือเขียนแบบมาตรฐาน)
# =============================================================================
def add_cad_dim(fig, x0, y0, x1, y1, text, type="horiz", offset=0, color="black"):
    """ สร้างเส้นบอกระยะ Dimension Line มาตรฐาน CAD """
    arrow_size = 5
    # Style constants
    line_style = dict(color=color, width=1)   # Main Dim Line
    ext_style = dict(color=color, width=0.5)  # Extension Line
    
    if type == "horiz":
        y_dim = y0 + offset
        # Ext Lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_dim, line=ext_style)
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_dim, line=ext_style)
        # Main Line
        fig.add_shape(type="line", x0=x0, y0=y_dim, x1=x1, y1=y_dim, line=line_style)
        # Arrows (Filled Triangle)
        fig.add_annotation(x=x0, y=y_dim, ax=arrow_size, ay=0, arrowhead=2, arrowsize=1.5, arrowcolor=color, text="")
        fig.add_annotation(x=x1, y=y_dim, ax=-arrow_size, ay=0, arrowhead=2, arrowsize=1.5, arrowcolor=color, text="")
        # Text
        fig.add_annotation(x=(x0+x1)/2, y=y_dim, text=f"<b>{text}</b>", showarrow=False, yshift=7 if offset>0 else -7,
                           font=dict(size=10, color=color, family="Arial"), bgcolor="white")

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
        fig.add_annotation(x=x_dim, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=10 if offset>0 else -10,
                           font=dict(size=10, color=color, family="Arial"), textangle=-90, bgcolor="white")

def add_leader(fig, x, y, text, ax=30, ay=-30):
    """ ป้ายกำกับพร้อมเส้นชี้ (Leader Line) """
    fig.add_annotation(
        x=x, y=y, text=text, showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor="black",
        ax=ax, ay=ay, font=dict(size=10, color="black"), bgcolor="rgba(255,255,255,0.8)", bordercolor="black", borderpad=2
    )

def add_centerline(fig, x0, y0, x1, y1):
    """ เส้น Centerline (ยาว-สั้น-ยาว) """
    fig.add_shape(type="line", x0=x0, y0=y0, x1=x1, y1=y1, 
                  line=dict(color="red", width=0.8, dash="dashdot"), opacity=0.7)

# =============================================================================
# 📐 VIEW 1: PLAN VIEW (TOP SECTION) - รูปตัดมองจากด้านบน
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    # Unpack
    tw, bf = beam['tw'], beam['b']
    w_pl, t_pl, e1, l_side = plate['w'], plate['t'], plate['e1'], plate['l_side']
    d_bolt, n_cols, s_h = bolts['d'], bolts['cols'], bolts['s_h']
    
    zoom_y = max(bf, 150) * 0.6
    zoom_x = w_pl + 60

    # 1. Column (Cut Section)
    fig.add_shape(type="rect", x0=-20, y0=-zoom_y, x1=0, y1=zoom_y, line=dict(color="black", width=2), fillcolor="#e2e8f0")
    # 2. Beam Web (Cut Section)
    fig.add_shape(type="rect", x0=10, y0=-tw/2, x1=zoom_x, y1=tw/2, line=dict(color="black", width=1.5), fillcolor="white")
    # 3. Fin Plate (Top View)
    py_max = tw/2 + t_pl
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=py_max, line=dict(color="black", width=1.5), fillcolor="white")
    
    # 4. Weld & Centerline
    fig.add_trace(go.Scatter(x=[0, 5, 0, 0], y=[py_max, py_max, py_max+5, py_max], fill="toself", line_color="black", fillcolor="black", mode='lines', hoverinfo='skip'))
    add_centerline(fig, -30, 0, zoom_x, 0) # Beam CL

    # 5. Bolts
    bx_start = e1
    for i in range(n_cols):
        bx = bx_start + i*s_h
        # Shank
        fig.add_shape(type="rect", x0=bx-d_bolt/2, y0=-tw/2, x1=bx+d_bolt/2, y1=py_max, line_width=1, fillcolor="white")
        # Head
        fig.add_shape(type="rect", x0=bx-d_bolt, y0=py_max, x1=bx+d_bolt, y1=py_max+(d_bolt*0.6), line_width=1, fillcolor="white")
        # Bolt CL
        add_centerline(fig, bx, -zoom_y+10, bx, zoom_y-10)

    # Dimensions
    dim_y = -zoom_y + 15
    curr_x = 0
    add_cad_dim(fig, curr_x, dim_y, curr_x+e1, dim_y, f"{e1:.0f}")
    curr_x += e1
    if n_cols > 1:
        for _ in range(n_cols-1):
            add_cad_dim(fig, curr_x, dim_y, curr_x+s_h, dim_y, f"{s_h:.0f}")
            curr_x += s_h
    add_cad_dim(fig, curr_x, dim_y, w_pl, dim_y, f"{l_side:.0f}")

    # Layout
    fig.update_layout(
        title=dict(text="<b>1. PLAN VIEW</b> (Top Section)", x=0.5, font=dict(size=12)),
        plot_bgcolor="white", margin=dict(l=5, r=5, t=30, b=5), height=250,
        xaxis=dict(visible=False, range=[-30, zoom_x], fixedrange=True),
        yaxis=dict(visible=False, range=[-zoom_y-10, zoom_y+10], scaleanchor="x", scaleratio=1, fixedrange=True),
        showlegend=False
    )
    return fig

# =============================================================================
# 📐 VIEW 2: FRONT ELEVATION - รูปด้านหน้า (มองเข้าหา Plate)
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    # Unpack
    h_beam, tf = beam['h'], beam['tf']
    h_pl, w_pl, lv, e1 = plate['h'], plate['w'], plate['lv'], plate['e1']
    s_v, s_h = bolts['s_v'], bolts['s_h']
    d_bolt, n_rows, n_cols = bolts['d'], bolts['rows'], bolts['cols']

    # 1. Beam Outline (Phantom Line)
    fig.add_shape(type="rect", x0=0, y0=-h_beam/2, x1=w_pl+50, y1=h_beam/2, line=dict(color="gray", width=0.5, dash="dash"))
    fig.add_shape(type="line", x0=0, y0=h_beam/2-tf, x1=w_pl+50, y1=h_beam/2-tf, line=dict(color="gray", width=0.5, dash="dash"))
    fig.add_shape(type="line", x0=0, y0=-h_beam/2+tf, x1=w_pl+50, y1=-h_beam/2+tf, line=dict(color="gray", width=0.5, dash="dash"))

    # 2. Column (Side)
    fig.add_shape(type="rect", x0=-20, y0=-h_beam/2-20, x1=0, y1=h_beam/2+20, line=dict(color="black", width=2), fillcolor="#e2e8f0")

    # 3. Plate (Main Object)
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, line=dict(color="black", width=1.5))
    
    # 4. Bolts Pattern
    by_start = h_pl/2 - lv
    for r in range(n_rows):
        for c in range(n_cols):
            bx = e1 + c*s_h
            by = by_start - r*s_v
            # Hole
            fig.add_shape(type="circle", x0=bx-d_bolt/2, y0=by-d_bolt/2, x1=bx+d_bolt/2, y1=by+d_bolt/2, line_color="black")
            # Cross Mark
            fig.add_shape(type="line", x0=bx-d_bolt/2-2, y0=by, x1=bx+d_bolt/2+2, y1=by, line_width=0.5)
            fig.add_shape(type="line", x0=bx, y0=by-d_bolt/2-2, x1=bx, y1=by+d_bolt/2+2, line_width=0.5)

    # Centerlines
    add_centerline(fig, -10, 0, w_pl+20, 0) # Horizontal CL

    # Dimensions (Vertical)
    dim_x = w_pl + 15
    curr_y = h_pl/2
    add_cad_dim(fig, dim_x, curr_y, dim_x, curr_y-lv, f"{lv:.0f}", "vert")
    curr_y -= lv
    if n_rows > 1:
        for _ in range(n_rows-1):
            add_cad_dim(fig, dim_x, curr_y, dim_x, curr_y-s_v, f"{s_v:.0f}", "vert")
            curr_y -= s_v
    add_cad_dim(fig, dim_x, curr_y, dim_x, -h_pl/2, f"{lv:.0f}", "vert")

    # Layout
    fig.update_layout(
        title=dict(text="<b>2. FRONT VIEW</b> (Elevation)", x=0.5, font=dict(size=12)),
        plot_bgcolor="white", margin=dict(l=5, r=25, t=30, b=5), height=250,
        xaxis=dict(visible=False, range=[-30, w_pl+60], fixedrange=True),
        yaxis=dict(visible=False, range=[-h_beam/2-30, h_beam/2+30], scaleanchor="x", scaleratio=1, fixedrange=True),
        showlegend=False
    )
    return fig

# =============================================================================
# 📐 VIEW 3: SIDE VIEW - รูปด้านข้าง (มองเห็นหน้าตัดคาน)
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    # Unpack
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    t_pl, h_pl = plate['t'], plate['h']

    # 1. Column Face (Background)
    fig.add_shape(type="line", x0=-b/2-20, y0=-h/2-20, x1=-b/2-20, y1=h/2+20, line=dict(color="black", width=2)) # Column Flange Line
    # Hatching area representation
    fig.add_shape(type="rect", x0=-b/2-40, y0=-h/2-20, x1=-b/2-20, y1=h/2+20, fillcolor="#e2e8f0", line_width=0)

    # 2. I-Beam Section (Cross Section)
    # Flanges
    fig.add_shape(type="rect", x0=-b/2, y0=h/2-tf, x1=b/2, y1=h/2, line=dict(color="black", width=1.5), fillcolor="white") # Top
    fig.add_shape(type="rect", x0=-b/2, y0=-h/2, x1=b/2, y1=-h/2+tf, line=dict(color="black", width=1.5), fillcolor="white") # Bot
    # Web
    fig.add_shape(type="rect", x0=-tw/2, y0=-h/2+tf, x1=tw/2, y1=h/2-tf, line=dict(color="black", width=1.5), fillcolor="white")
    
    # 3. Fin Plate (Protruding from Column - Behind or Side)
    # ในมุมนี้ Plate จะขนานกับ Web แต่อยู่ด้านข้าง
    # สมมติ Plate อยู่ขวา
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, line=dict(color="black", width=1.5), fillcolor="#cbd5e1")
    
    # 4. Bolts (Side view of heads)
    # แสดงหัวน็อตเรียงลงมา
    n_rows = bolts['rows']
    s_v = bolts['s_v']
    lv = plate['lv']
    d_bolt = bolts['d']
    by_start = h_pl/2 - lv
    
    bolt_head_thk = d_bolt * 0.6
    bolt_x_start = tw/2 + t_pl
    
    for r in range(n_rows):
        by = by_start - r*s_v
        # Bolt Head
        fig.add_shape(type="rect", x0=bolt_x_start, y0=by-d_bolt/2, x1=bolt_x_start+bolt_head_thk, y1=by+d_bolt/2, line=dict(color="black", width=1), fillcolor="white")
        # Centerline
        add_centerline(fig, -b/2-10, by, b/2+10, by)

    # Centerlines
    add_centerline(fig, 0, -h/2-20, 0, h/2+20) # Vert CL

    # Layout
    fig.update_layout(
        title=dict(text="<b>3. SIDE VIEW</b> (Section B-B)", x=0.5, font=dict(size=12)),
        plot_bgcolor="white", margin=dict(l=20, r=20, t=30, b=20), height=250,
        xaxis=dict(visible=False, range=[-b/2-50, b/2+50], fixedrange=True),
        yaxis=dict(visible=False, range=[-h/2-30, h/2+30], scaleanchor="x", scaleratio=1, fixedrange=True),
        showlegend=False
    )
    return fig
