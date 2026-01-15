import plotly.graph_objects as go

# =============================================================================
# 🎨 COLOR PALETTE & STYLES
# =============================================================================
C_COL_FILL = "#475569"    # Slate 600 (เสา)
C_BEAM_FILL = "#f1f5f9"   # Slate 100 (เนื้อคาน)
C_BEAM_OUT = "#334155"    # Slate 700 (ขอบคาน)
C_PLATE_FILL = "#0ea5e9"  # Sky 500 (เพลท)
C_BOLT_FILL = "#dc2626"   # Red 600 (น็อต)
C_DIM = "black"           # สีเส้นบอกระยะ
C_CL = "#ef4444"          # สีเส้น Centerline

# =============================================================================
# 🛠️ HELPER TOOLS
# =============================================================================
def add_cad_dim(fig, x0, y0, x1, y1, text, type="horiz", offset=0):
    """ เส้นบอกระยะ (Dimension Line) """
    arrow_size = 6
    if type == "horiz":
        y_dim = y0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_dim, line=dict(color=C_DIM, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_dim, line=dict(color=C_DIM, width=0.5))
        fig.add_shape(type="line", x0=x0, y0=y_dim, x1=x1, y1=y_dim, line=dict(color=C_DIM, width=1))
        fig.add_annotation(x=x0, y=y_dim, ax=arrow_size, ay=0, arrowhead=2, arrowsize=1.5, arrowcolor=C_DIM, text="")
        fig.add_annotation(x=x1, y=y_dim, ax=-arrow_size, ay=0, arrowhead=2, arrowsize=1.5, arrowcolor=C_DIM, text="")
        fig.add_annotation(x=(x0+x1)/2, y=y_dim, text=f"<b>{text}</b>", showarrow=False, yshift=8 if offset>0 else -8,
                           font=dict(size=11, color=C_DIM, family="Arial"), bgcolor="white")

    elif type == "vert":
        x_dim = x0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_dim, y1=y0, line=dict(color=C_DIM, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_dim, y1=y1, line=dict(color=C_DIM, width=0.5))
        fig.add_shape(type="line", x0=x_dim, y0=y0, x1=x_dim, y1=y1, line=dict(color=C_DIM, width=1))
        fig.add_annotation(x=x_dim, y=y0, ax=0, ay=-arrow_size, arrowhead=2, arrowsize=1.5, arrowcolor=C_DIM, text="")
        fig.add_annotation(x=x_dim, y=y1, ax=0, ay=arrow_size, arrowhead=2, arrowsize=1.5, arrowcolor=C_DIM, text="")
        fig.add_annotation(x=x_dim, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=12 if offset>0 else -12,
                           font=dict(size=11, color=C_DIM, family="Arial"), textangle=-90, bgcolor="white")

def add_leader(fig, x, y, text, ax=30, ay=-30, color="black"):
    """ ป้ายชี้บอก (Callout) """
    fig.add_annotation(
        x=x, y=y, text=text, showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=color,
        ax=ax, ay=ay, font=dict(size=11, color=color), bgcolor="#f8f9fa", bordercolor=color, borderpad=3
    )

def add_centerline(fig, x0, y0, x1, y1):
    fig.add_shape(type="line", x0=x0, y0=y0, x1=x1, y1=y1, line=dict(color=C_CL, width=1, dash="dashdot"), opacity=0.7)

# =============================================================================
# 1. PLAN VIEW (TOP) - Adjusted Scale
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, bf = beam['tw'], beam['b']
    w_pl, t_pl, e1, l_side = plate['w'], plate['t'], plate['e1'], plate['l_side']
    d_bolt, n_cols, s_h = bolts['d'], bolts['cols'], bolts['s_h']
    
    # --- SCALING ADJUSTMENT ---
    # Y-Limit: อิงจากความกว้างปีกคาน + เผื่อที่ให้ Callout นิดหน่อย (กระชับขึ้น)
    zoom_y = bf/2 + 50  
    # X-Limit: อิงจากความยาวเพลท + เผื่อที่ให้ Leader line ด้านขวา
    zoom_x_end = w_pl + 60
    zoom_x_start = -30 # เผื่อให้เห็นเสาด้านซ้าย

    # Column
    fig.add_shape(type="rect", x0=zoom_x_start, y0=-zoom_y, x1=0, y1=zoom_y, line=dict(color=C_BEAM_OUT, width=2), fillcolor=C_COL_FILL)
    
    # Beam Web
    fig.add_shape(type="rect", x0=10, y0=-tw/2, x1=zoom_x_end, y1=tw/2, line=dict(color=C_BEAM_OUT, width=1.5), fillcolor=C_BEAM_FILL)
    add_centerline(fig, zoom_x_start, 0, zoom_x_end, 0)

    # Fin Plate
    py_max = tw/2 + t_pl
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=py_max, line=dict(color=C_BEAM_OUT, width=1.5), fillcolor=C_PLATE_FILL)
    fig.add_trace(go.Scatter(x=[0, 6, 0, 0], y=[py_max, py_max, py_max+6, py_max], fill="toself", line_color="black", fillcolor="black", mode='lines', hoverinfo='skip'))

    # Bolts
    bx_start = e1
    for i in range(n_cols):
        bx = bx_start + i*s_h
        fig.add_shape(type="rect", x0=bx-d_bolt/2, y0=-tw/2, x1=bx+d_bolt/2, y1=py_max, line_width=1, fillcolor=C_BOLT_FILL)
        fig.add_shape(type="rect", x0=bx-d_bolt, y0=py_max, x1=bx+d_bolt, y1=py_max+(d_bolt*0.6), line_width=1, fillcolor=C_BOLT_FILL)
        add_centerline(fig, bx, -zoom_y+10, bx, zoom_y-10)

    # Dimensions
    dim_y = -zoom_y + 20
    curr_x = 0
    add_cad_dim(fig, curr_x, dim_y, curr_x+e1, dim_y, f"{e1:.0f}")
    curr_x += e1
    if n_cols > 1:
        for _ in range(n_cols-1):
            add_cad_dim(fig, curr_x, dim_y, curr_x+s_h, dim_y, f"{s_h:.0f}")
            curr_x += s_h
    add_cad_dim(fig, curr_x, dim_y, w_pl, dim_y, f"{l_side:.0f}")

    add_leader(fig, w_pl/2, py_max, f"<b>PL-{t_pl}mm</b>", ax=20, ay=-35, color=C_PLATE_FILL)

    # Layout (กระชับ Margin)
    fig.update_layout(title="<b>PLAN VIEW</b>", plot_bgcolor="white", margin=dict(l=5,r=5,t=30,b=5), height=280,
                      xaxis=dict(visible=False, range=[zoom_x_start, zoom_x_end], fixedrange=True),
                      yaxis=dict(visible=False, range=[-zoom_y, zoom_y], scaleanchor="x", scaleratio=1, fixedrange=True), showlegend=False)
    return fig

# =============================================================================
# 2. FRONT VIEW (ELEVATION) - Adjusted Scale
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_beam, tf = beam['h'], beam['tf']
    h_pl, w_pl, lv, e1 = plate['h'], plate['w'], plate['lv'], plate['e1']
    s_v, s_h = bolts['s_v'], bolts['s_h']
    d_bolt, n_rows, n_cols = bolts['d'], bolts['rows'], bolts['cols']

    # --- SCALING ADJUSTMENT ---
    # Y-Limit: อิงความลึกคาน + เผื่อที่สำหรับ Dimension ด้านล่างและบน
    zoom_y_limit = h_beam/2 + 40
    # X-Limit: อิงความกว้างเพลท + เผื่อที่สำหรับ Dimension ด้านขวา
    zoom_x_end = w_pl + 60
    zoom_x_start = -25 # เผื่อเห็นเสา

    # Beam Outline
    fig.add_shape(type="rect", x0=0, y0=-h_beam/2, x1=zoom_x_end, y1=h_beam/2, line=dict(color="#94a3b8", width=1, dash="dash"))
    fig.add_shape(type="line", x0=0, y0=h_beam/2-tf, x1=zoom_x_end, y1=h_beam/2-tf, line=dict(color="#94a3b8", width=0.5, dash="dash"))
    fig.add_shape(type="line", x0=0, y0=-h_beam/2+tf, x1=zoom_x_end, y1=-h_beam/2+tf, line=dict(color="#94a3b8", width=0.5, dash="dash"))

    # Column
    fig.add_shape(type="rect", x0=zoom_x_start, y0=-zoom_y_limit, x1=0, y1=zoom_y_limit, line=dict(color=C_BEAM_OUT, width=2), fillcolor=C_COL_FILL)

    # Plate
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, line=dict(color=C_PLATE_FILL, width=2), fillcolor="rgba(14, 165, 233, 0.1)")

    # Bolts
    by_start = h_pl/2 - lv
    for r in range(n_rows):
        for c in range(n_cols):
            bx = e1 + c*s_h
            by = by_start - r*s_v
            fig.add_shape(type="circle", x0=bx-d_bolt/2, y0=by-d_bolt/2, x1=bx+d_bolt/2, y1=by+d_bolt/2, line=dict(color=C_BOLT_FILL, width=1.5))
            fig.add_shape(type="line", x0=bx-d_bolt/2, y0=by, x1=bx+d_bolt/2, y1=by, line=dict(color=C_BOLT_FILL, width=1))
            fig.add_shape(type="line", x0=bx, y0=by-d_bolt/2, x1=bx, y1=by+d_bolt/2, line=dict(color=C_BOLT_FILL, width=1))

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
    add_cad_dim(fig, dim_x+35, h_pl/2, dim_x+35, -h_pl/2, f"H={h_pl:.0f}", "vert", offset=0)

    # Layout (กระชับ Margin)
    fig.update_layout(title="<b>ELEVATION</b> (Front View)", plot_bgcolor="white", margin=dict(l=5,r=30,t=30,b=5), height=280,
                      xaxis=dict(visible=False, range=[zoom_x_start, zoom_x_end], fixedrange=True),
                      yaxis=dict(visible=False, range=[-zoom_y_limit, zoom_y_limit], scaleanchor="x", scaleratio=1, fixedrange=True), showlegend=False)
    return fig

# =============================================================================
# 3. SIDE VIEW (SECTION) - Adjusted Scale
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    t_pl, h_pl, lv = plate['t'], plate['h'], plate['lv']
    d_bolt, n_rows, s_v = bolts['d'], bolts['rows'], bolts['s_v']

    # --- SCALING ADJUSTMENT ---
    col_w_visual = b + 80
    # Y-Limit: อิงความลึกคาน + เผื่อที่สำหรับ Callout ด้านบน/ล่าง
    zoom_y_limit = h/2 + 40
    # X-Limit: อิงความกว้างเสาที่สมมติขึ้น + เผื่อที่ด้านข้างนิดหน่อย
    zoom_x_limit = col_w_visual/2 + 30

    # Column Background
    fig.add_shape(type="line", x0=-col_w_visual/2, y0=-zoom_y_limit, x1=-col_w_visual/2, y1=zoom_y_limit, line=dict(color=C_COL_FILL, width=3))
    fig.add_shape(type="line", x0=col_w_visual/2, y0=-zoom_y_limit, x1=col_w_visual/2, y1=zoom_y_limit, line=dict(color=C_COL_FILL, width=3))
    fig.add_trace(go.Scatter(x=[-col_w_visual/2, col_w_visual/2, col_w_visual/2, -col_w_visual/2],
                             y=[-zoom_y_limit, -zoom_y_limit, zoom_y_limit, zoom_y_limit],
                             fill="toself", mode='none', fillcolor='rgba(71, 85, 105, 0.1)', hoverinfo='skip'))

    # I-Beam Section
    fig.add_shape(type="rect", x0=-b/2, y0=h/2-tf, x1=b/2, y1=h/2, line=dict(color=C_BEAM_OUT, width=1.5), fillcolor=C_BEAM_FILL)
    fig.add_shape(type="rect", x0=-b/2, y0=-h/2, x1=b/2, y1=-h/2+tf, line=dict(color=C_BEAM_OUT, width=1.5), fillcolor=C_BEAM_FILL)
    fig.add_shape(type="rect", x0=-tw/2, y0=-h/2+tf, x1=tw/2, y1=h/2-tf, line=dict(color=C_BEAM_OUT, width=1.5), fillcolor=C_BEAM_FILL)

    # Plate & Bolts
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, line=dict(color=C_BEAM_OUT, width=1.5), fillcolor=C_PLATE_FILL)
    bolt_x = tw/2 + t_pl
    by_start = h_pl/2 - lv
    for r in range(n_rows):
        by = by_start - r*s_v
        fig.add_shape(type="rect", x0=bolt_x, y0=by-d_bolt/2, x1=bolt_x+(d_bolt*0.6), y1=by+d_bolt/2, line=dict(color=C_BOLT_FILL, width=1), fillcolor=C_BOLT_FILL)
        add_centerline(fig, -b/2, by, b/2, by)

    add_centerline(fig, 0, -zoom_y_limit, 0, zoom_y_limit)

    # Labels
    add_leader(fig, b/2, h/2-tf/2, f"<b>Beam {h:.0f}</b>", ax=30, ay=-20, color=C_BEAM_OUT)
    fig.add_annotation(x=-col_w_visual/2, y=-zoom_y_limit+10, text="<b>Column</b>", ax=-30, ay=0, showarrow=True, arrowcolor=C_COL_FILL, font=dict(color=C_COL_FILL, size=10))

    # Layout (กระชับ Margin)
    fig.update_layout(title="<b>SIDE VIEW</b> (Section)", plot_bgcolor="white", margin=dict(l=5,r=5,t=30,b=5), height=280,
                      xaxis=dict(visible=False, range=[-zoom_x_limit, zoom_x_limit], fixedrange=True),
                      yaxis=dict(visible=False, range=[-zoom_y_limit, zoom_y_limit], scaleanchor="x", scaleratio=1, fixedrange=True), showlegend=False)
    return fig
