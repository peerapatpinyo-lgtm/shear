# drawing_utils.py (V13 - Dimension Fix Full Version)
import plotly.graph_objects as go

# =============================================================================
# 🎨 COLOR PALETTE & STYLES
# =============================================================================
C_COL_FILL = "#475569"    # Slate 600 (Column)
C_BEAM_FILL = "#f1f5f9"   # Slate 100 (Beam Body)
C_BEAM_OUT = "#334155"    # Slate 700 (Beam Outline)
C_PLATE_FILL = "#0ea5e9"  # Sky 500 (Plate)
C_BOLT_FILL = "#dc2626"   # Red 600 (Bolt)
C_DIM = "#374151"         # Dimension line color
C_CL = "#ef4444"          # Centerline color

# =============================================================================
# 🛠️ HELPER TOOLS
# =============================================================================
def add_cad_dim(fig, x0, y0, x1, y1, text, type="horiz", offset=40):
    """ เส้นบอกระยะ (Dimension Line) แบบเว้นระยะห่างจากตัวงาน (Offset) """
    arrow_head_style = 2  
    
    if type == "horiz":
        y_dim = y0 + offset
        # Extension Lines (เส้นช่วยดึงจากตัวงานออกมา)
        fig.add_shape(type="line", x0=x0, y0=y0 + (5 if offset>0 else -5), x1=x0, y1=y_dim + (5 if offset>0 else -5), line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x1, y0=y1 + (5 if offset>0 else -5), x1=x1, y1=y_dim + (5 if offset>0 else -5), line=dict(color=C_DIM, width=1))
        # Main Line
        fig.add_shape(type="line", x0=x0, y0=y_dim, x1=x1, y1=y_dim, line=dict(color=C_DIM, width=1.2))
        # Arrows & Text
        fig.add_annotation(x=x0, y=y_dim, ax=6, ay=0, arrowhead=arrow_head_style, arrowsize=1, arrowwidth=1, arrowcolor=C_DIM, text="")
        fig.add_annotation(x=x1, y=y_dim, ax=-6, ay=0, arrowhead=arrow_head_style, arrowsize=1, arrowwidth=1, arrowcolor=C_DIM, text="")
        fig.add_annotation(x=(x0+x1)/2, y=y_dim, text=f"<b>{text}</b>", showarrow=False, yshift=10 if offset>0 else -10,
                           font=dict(size=11, color=C_DIM, family="Arial"), bgcolor="rgba(255,255,255,0.8)")

    elif type == "vert":
        x_dim = x0 + offset
        # Extension Lines
        fig.add_shape(type="line", x0=x0 + (5 if offset>0 else -5), y0=y0, x1=x_dim + (5 if offset>0 else -5), y1=y0, line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x1 + (5 if offset>0 else -5), y0=y1, x1=x_dim + (5 if offset>0 else -5), y1=y1, line=dict(color=C_DIM, width=1))
        # Main Line
        fig.add_shape(type="line", x0=x_dim, y0=y0, x1=x_dim, y1=y1, line=dict(color=C_DIM, width=1.2))
        # Arrows & Text
        fig.add_annotation(x=x_dim, y=y0, ax=0, ay=6, arrowhead=arrow_head_style, arrowsize=1, arrowwidth=1, arrowcolor=C_DIM, text="")
        fig.add_annotation(x=x_dim, y=y1, ax=0, ay=-6, arrowhead=arrow_head_style, arrowsize=1, arrowwidth=1, arrowcolor=C_DIM, text="")
        fig.add_annotation(x=x_dim, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=14 if offset>0 else -14,
                           font=dict(size=11, color=C_DIM, family="Arial"), textangle=-90, bgcolor="rgba(255,255,255,0.8)")

def add_leader(fig, x, y, text, ax=30, ay=-30):
    fig.add_annotation(x=x, y=y, text=text, showarrow=True, arrowhead=2, ax=ax, ay=ay, 
                       font=dict(size=10), bgcolor="white", bordercolor="#cbd5e1")

def add_centerline(fig, x0, y0, x1, y1):
    fig.add_shape(type="line", x0=x0, y0=y0, x1=x1, y1=y1, line=dict(color=C_CL, width=1, dash="dashdot"), opacity=0.6)

# =============================================================================
# 1. PLAN VIEW (TOP)
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, bf = beam['tw'], beam['b']
    w_pl, t_pl, e1, l_side = plate['w'], plate['t'], plate['e1'], plate['l_side']
    d_bolt, n_cols, s_h = bolts['d'], bolts['cols'], bolts['s_h']
    
    # Range Calculation (เผื่อระยะ Dimension)
    pad = 80
    x_range = [-50, w_pl + pad]
    y_range = [-bf/2 - pad, bf/2 + pad]

    # Draw Column & Beam
    fig.add_shape(type="rect", x0=-30, y0=-bf/2-20, x1=0, y1=bf/2+20, fillcolor=C_COL_FILL, line_width=0)
    fig.add_shape(type="rect", x0=0, y0=-tw/2, x1=w_pl+40, y1=tw/2, fillcolor=C_BEAM_FILL, line=dict(color=C_BEAM_OUT, width=1.5))
    
    # Draw Plate
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=tw/2+t_pl, fillcolor=C_PLATE_FILL, line=dict(color=C_BEAM_OUT, width=1))

    # Draw Bolts (Plan View - Top heads)
    for i in range(n_cols):
        bx = e1 + i*s_h
        # Bolt shank
        fig.add_shape(type="rect", x0=bx-d_bolt/2, y0=-tw/2, x1=bx+d_bolt/2, y1=tw/2+t_pl, fillcolor=C_BOLT_FILL, line_width=0)
        # Bolt head
        fig.add_shape(type="rect", x0=bx-d_bolt*0.8, y0=tw/2+t_pl, x1=bx+d_bolt*0.8, y1=tw/2+t_pl+8, fillcolor="#991b1b", line_width=1)

    # Dimensions (เลื่อน Offset ออกมาไม่ให้ทับงาน)
    dim_y = -bf/2 - 40
    add_cad_dim(fig, 0, dim_y, e1, dim_y, f"{e1}", "horiz", offset=0)
    if n_cols > 1:
        add_cad_dim(fig, e1, dim_y, e1+s_h, dim_y, f"{s_h}", "horiz", offset=0)
    add_cad_dim(fig, 0, dim_y-35, w_pl, dim_y-35, f"W_plate={w_pl}", "horiz", offset=0)

    fig.update_layout(title="PLAN VIEW", plot_bgcolor="white", height=350,
                      xaxis=dict(visible=False, range=x_range),
                      yaxis=dict(visible=False, range=y_range, scaleanchor="x", scaleratio=1), showlegend=False)
    return fig

# =============================================================================
# 2. FRONT VIEW (ELEVATION)
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_beam = beam['h']
    h_pl, w_pl, lv, e1 = plate['h'], plate['w'], plate['lv'], plate['e1']
    s_v, s_h = bolts['s_v'], bolts['s_h']
    d_bolt, n_rows, n_cols = bolts['d'], bolts['rows'], bolts['cols']

    pad = 100
    x_range = [-60, w_pl + pad]
    y_range = [-h_beam/2 - pad, h_beam/2 + pad]

    # Draw Main Components
    fig.add_shape(type="rect", x0=-30, y0=-h_beam/2-40, x1=0, y1=h_beam/2+40, fillcolor=C_COL_FILL, line_width=0)
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor="rgba(14, 165, 233, 0.1)", line=dict(color=C_PLATE_FILL, width=2))
    
    # Bolts
    for r in range(n_rows):
        for c in range(n_cols):
            bx = e1 + c*s_h
            by = (h_pl/2 - lv) - r*s_v
            fig.add_shape(type="circle", x0=bx-d_bolt/2, y0=by-d_bolt/2, x1=bx+d_bolt/2, y1=by+d_bolt/2, fillcolor=C_BOLT_FILL, line_width=0)

    # Vertical Dimensions (Offset ออกไปทางขวาของ Plate)
    dim_x = w_pl + 40
    add_cad_dim(fig, dim_x, h_pl/2, dim_x, h_pl/2-lv, f"{lv}", "vert", offset=0)
    if n_rows > 1:
        add_cad_dim(fig, dim_x, h_pl/2-lv, dim_x, h_pl/2-lv-s_v, f"{s_v}", "vert", offset=0)
    add_cad_dim(fig, dim_x+40, h_pl/2, dim_x+40, -h_pl/2, f"H_pl={h_pl}", "vert", offset=0)

    fig.update_layout(title="ELEVATION (FRONT)", plot_bgcolor="white", height=350,
                      xaxis=dict(visible=False, range=x_range),
                      yaxis=dict(visible=False, range=y_range, scaleanchor="x", scaleratio=1))
    return fig

# =============================================================================
# 3. SIDE VIEW (SECTION)
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    t_pl, h_pl = plate['t'], plate['h']

    pad = 120
    x_range = [-b/2 - pad, b/2 + pad]
    y_range = [-h/2 - pad, h/2 + pad]

    # Draw I-Beam Section
    # Flanges
    fig.add_shape(type="rect", x0=-b/2, y0=h/2-tf, x1=b/2, y1=h/2, fillcolor=C_BEAM_FILL, line_width=1.5)
    fig.add_shape(type="rect", x0=-b/2, y0=-h/2, x1=b/2, y1=-h/2+tf, fillcolor=C_BEAM_FILL, line_width=1.5)
    # Web
    fig.add_shape(type="rect", x0=-tw/2, y0=-h/2+tf, x1=tw/2, y1=h/2-tf, fillcolor=C_BEAM_FILL, line_width=1.5)
    # Plate
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, fillcolor=C_PLATE_FILL, line_width=1)

    # Dimensions (Offset ออกมาด้านซ้ายของ Beam)
    add_cad_dim(fig, -b/2 - 50, h/2, -b/2 - 50, -h/2, f"H={h}", "vert", offset=0)
    add_cad_dim(fig, -b/2, h/2+40, b/2, h/2+40, f"B={b}", "horiz", offset=0)

    fig.update_layout(title="SIDE VIEW (SECTION)", plot_bgcolor="white", height=350,
                      xaxis=dict(visible=False, range=x_range),
                      yaxis=dict(visible=False, range=y_range, scaleanchor="x", scaleratio=1))
    return fig
