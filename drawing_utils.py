# drawing_utils.py (V14 - Professional Structural Edition)
import plotly.graph_objects as go

# สีมาตรฐานวิศวกรรม
C_COL_FILL = "#334155"    # เสา (Slate 700)
C_BEAM_FILL = "#f8fafc"   # คาน (Slate 50)
C_BEAM_OUT = "#1e293b"    # ขอบคาน
C_PLATE_FILL = "#0ea5e9"  # แผ่นเหล็ก (Sky 500)
C_BOLT_FILL = "#e11d48"   # โบลท์ (Rose 600)
C_DIM = "#000000"         # เส้นมิติ
C_CL = "#ef4444"          # Centerline

def add_cad_dim(fig, x0, y0, x1, y1, text, type="horiz", offset=50):
    """ เส้นบอกระยะแบบ Professional เผื่อระยะ Extension Lines """
    if type == "horiz":
        y_dim = y0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_dim + (5 if offset>0 else -5), line=dict(color=C_DIM, width=0.8))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_dim + (5 if offset>0 else -5), line=dict(color=C_DIM, width=0.8))
        fig.add_shape(type="line", x0=x0, y0=y_dim, x1=x1, y1=y_dim, line=dict(color=C_DIM, width=1.2))
        fig.add_annotation(x=x0, y=y_dim, ax=5, ay=0, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=C_DIM)
        fig.add_annotation(x=x1, y=y_dim, ax=-5, ay=0, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=C_DIM)
        fig.add_annotation(x=(x0+x1)/2, y=y_dim, text=f"<b>{text}</b>", showarrow=False, yshift=10 if offset>0 else -10, 
                           font=dict(size=12, family="Arial"), bgcolor="white")
    else:
        x_dim = x0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_dim + (5 if offset>0 else -5), y1=y0, line=dict(color=C_DIM, width=0.8))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_dim + (5 if offset>0 else -5), y1=y1, line=dict(color=C_DIM, width=0.8))
        fig.add_shape(type="line", x0=x_dim, y0=y0, x1=x_dim, y1=y1, line=dict(color=C_DIM, width=1.2))
        fig.add_annotation(x=x_dim, y=y0, ax=0, ay=-5, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=C_DIM)
        fig.add_annotation(x=x_dim, y=y1, ax=0, ay=5, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=C_DIM)
        fig.add_annotation(x=x_dim, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=15 if offset>0 else -15, 
                           textangle=-90, font=dict(size=12, family="Arial"), bgcolor="white")

# =============================================================================
# 1. PLAN VIEW
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, bf = beam['tw'], beam['b']
    w_pl, t_pl, e1, s_h = plate['w'], plate['t'], plate['e1'], bolts['s_h']
    
    # เพิ่มระยะ Padding รอบงานให้ดูโปร่ง
    limit_y = bf/2 + 80
    
    # Draw Column (Section) & Beam
    fig.add_shape(type="rect", x0=-40, y0=-bf/2-20, x1=0, y1=bf/2+20, fillcolor=C_COL_FILL, line_width=0)
    fig.add_shape(type="rect", x0=0, y0=-tw/2, x1=w_pl+60, y1=tw/2, fillcolor=C_BEAM_FILL, line=dict(color=C_BEAM_OUT, width=1.5))
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=tw/2+t_pl, fillcolor=C_PLATE_FILL, line=dict(color=C_BEAM_OUT, width=1))

    # Bolts with Correct Proportions
    for i in range(bolts['cols']):
        bx = e1 + i*s_h
        fig.add_shape(type="rect", x0=bx-bolts['d']/2, y0=-tw/2, x1=bx+bolts['d']/2, y1=tw/2+t_pl, fillcolor=C_BOLT_FILL, line_width=0)
        # Bolt Head (Hex shape approx)
        fig.add_shape(type="rect", x0=bx-bolts['d']*0.75, y0=tw/2+t_pl, x1=bx+bolts['d']*0.75, y1=tw/2+t_pl+10, fillcolor="#4c0519", line_width=1)

    # Professional Dimensions
    dim_y = -bf/2 - 50
    add_cad_dim(fig, 0, dim_y, e1, dim_y, f"{e1}", "horiz", offset=0)
    add_cad_dim(fig, 0, dim_y-40, w_pl, dim_y-40, f"PL Width = {w_pl}", "horiz", offset=0)

    fig.update_layout(title="<b>PLAN VIEW</b>", plot_bgcolor="white", height=400,
                      xaxis=dict(visible=False, range=[-80, w_pl+100]),
                      yaxis=dict(visible=False, range=[-limit_y, limit_y], scaleanchor="x", scaleratio=1))
    return fig

# =============================================================================
# 2. FRONT VIEW (ELEVATION)
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_beam, h_pl, w_pl = beam['h'], plate['h'], plate['w']
    e1, lv, s_v, s_h = plate['e1'], plate['lv'], bolts['s_v'], bolts['s_h']

    # Draw Column & Beam Hidden Lines
    fig.add_shape(type="rect", x0=-40, y0=-h_beam/2-50, x1=0, y1=h_beam/2+50, fillcolor=C_COL_FILL, line_width=0)
    fig.add_shape(type="rect", x0=0, y0=-h_beam/2, x1=w_pl+100, y1=h_beam/2, line=dict(color="#94a3b8", width=1, dash="dash"))
    
    # Draw Plate
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor="rgba(14, 165, 233, 0.2)", line=dict(color=C_PLATE_FILL, width=2.5))
    
    # Draw Bolts (Clear Circles)
    for r in range(bolts['rows']):
        for c in range(bolts['cols']):
            bx, by = e1 + c*s_h, (h_pl/2 - lv) - r*s_v
            fig.add_shape(type="circle", x0=bx-bolts['d']/2, y0=by-bolts['d']/2, x1=bx+bolts['d']/2, y1=by+bolts['d']/2, 
                          fillcolor=C_BOLT_FILL, line=dict(color="white", width=1))

    # Professional Dimensions (Offset to avoid overlap)
    dim_x = w_pl + 60
    add_cad_dim(fig, dim_x, h_pl/2, dim_x, h_pl/2-lv, f"{lv}", "vert", offset=0)
    add_cad_dim(fig, dim_x + 50, h_pl/2, dim_x + 50, -h_pl/2, f"H_pl = {h_pl}", "vert", offset=0)

    fig.update_layout(title="<b>ELEVATION VIEW</b>", plot_bgcolor="white", height=400,
                      xaxis=dict(visible=False, range=[-100, w_pl+200]),
                      yaxis=dict(visible=False, range=[-h_beam/2-100, h_beam/2+100], scaleanchor="x", scaleratio=1))
    return fig

# =============================================================================
# 3. SIDE VIEW (SECTION)
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    h_pl, t_pl = plate['h'], plate['t']

    # Draw Beam Section
    fig.add_shape(type="rect", x0=-b/2, y0=h/2-tf, x1=b/2, y1=h/2, fillcolor=C_BEAM_FILL, line=dict(color=C_BEAM_OUT, width=2))
    fig.add_shape(type="rect", x0=-b/2, y0=-h/2, x1=b/2, y1=-h/2+tf, fillcolor=C_BEAM_FILL, line=dict(color=C_BEAM_OUT, width=2))
    fig.add_shape(type="rect", x0=-tw/2, y0=-h/2+tf, x1=tw/2, y1=h/2-tf, fillcolor=C_BEAM_FILL, line=dict(color=C_BEAM_OUT, width=1.5))
    
    # Draw Plate
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, fillcolor=C_PLATE_FILL, line=dict(color=C_BEAM_OUT, width=1))

    # Dimensions
    add_cad_dim(fig, -b/2 - 60, h/2, -b/2 - 60, -h/2, f"H = {h}", "vert", offset=0)
    add_cad_dim(fig, -b/2, h/2 + 60, b/2, h/2 + 60, f"B = {b}", "horiz", offset=0)

    fig.update_layout(title="<b>SIDE VIEW (SECTION)</b>", plot_bgcolor="white", height=400,
                      xaxis=dict(visible=False, range=[-b/2-150, b/2+150]),
                      yaxis=dict(visible=False, range=[-h/2-150, h/2+150], scaleanchor="x", scaleratio=1))
    return fig
