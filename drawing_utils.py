import plotly.graph_objects as go

# --- Professional Engineering Theme ---
C_STEEL = "#212529"   # Graphite
C_PLATE = "#0277BD"   # Steel Blue
C_BOLT = "#D32F2F"    # Red
C_DIM = "#455A64"     # Dark Slate
C_SEC = "#ECEFF1"     # Light Grey for Fill

def add_dim(fig, x0, y0, x1, y1, text, orient="H", offset=50):
    """ฟังก์ชันให้มิติมาตรฐานสากล พร้อม Tick Marks และ Extension Line"""
    l_w = 1.2
    if orient == "H":
        y_d = y0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_d+10, line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_d+10, line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x0, y0=y_d, x1=x1, y1=y_d, line=dict(color=C_DIM, width=l_w))
        fig.add_shape(type="line", x0=x0-5, y0=y_d-5, x1=x0+5, y1=y_d+5, line=dict(color=C_DIM, width=1.5))
        fig.add_shape(type="line", x0=x1-5, y0=y_d-5, x1=x1+5, y1=y_d+5, line=dict(color=C_DIM, width=1.5))
        fig.add_annotation(x=(x0+x1)/2, y=y_d, text=text, showarrow=False, yshift=12, font=dict(size=11), bgcolor="white")
    else:
        x_d = x0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_d+10, y1=y0, line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_d+10, y1=y1, line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x_d, y0=y0, x1=x_d, y1=y1, line=dict(color=C_DIM, width=l_w))
        fig.add_shape(type="line", x0=x_d-5, y0=y0-5, x1=x_d+5, y1=y0+5, line=dict(color=C_DIM, width=1.5))
        fig.add_shape(type="line", x0=x_d-5, y0=y1-5, x1=x_d+5, y1=y1+5, line=dict(color=C_DIM, width=1.5))
        fig.add_annotation(x=x_d, y=(y0+y1)/2, text=text, showarrow=False, xshift=15, textangle=-90, font=dict(size=11), bgcolor="white")

# 1. PLAN VIEW (มุมมองจากด้านบน)
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, bf, w_pl, t_pl = beam['tw'], beam['b'], plate['w'], plate['t']
    e1, s_h = plate['e1'], bolts['s_h']
    
    # วาดหน้าตัดเสาและคาน
    fig.add_shape(type="rect", x0=-30, y0=-bf/2, x1=0, y1=bf/2, fillcolor=C_STEEL, line_width=0)
    fig.add_shape(type="rect", x0=0, y0=-tw/2, x1=w_pl+100, y1=tw/2, fillcolor=C_SEC, line=dict(color=C_STEEL, width=2))
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=tw/2+t_pl, fillcolor=C_PLATE, line=dict(color=C_STEEL, width=1.5))

    # วาด Bolt และ Centerline
    for i in range(bolts['cols']):
        bx = e1 + i*s_h
        fig.add_shape(type="rect", x0=bx-bolts['d']/2, y0=-tw/2-5, x1=bx+bolts['d']/2, y1=tw/2+t_pl+5, fillcolor=C_BOLT, line_width=0)
        fig.add_shape(type="line", x0=bx, y0=-bf/2, x1=bx, y1=bf/2, line=dict(color=C_BOLT, width=0.5, dash="dash"))

    add_dim(fig, 0, -bf/2, w_pl, -bf/2, f"PL Width {w_pl}", "H", offset=-50)
    
    fig.update_layout(title="PLAN VIEW", xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1), plot_bgcolor="white")
    return fig

# 2. FRONT VIEW (ELEVATION)
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_b, h_pl, w_pl = beam['h'], plate['h'], plate['w']
    e1, lv, s_v, s_h = plate['e1'], plate['lv'], bolts['s_v'], bolts['s_h']

    fig.add_shape(type="rect", x0=-30, y0=-h_b/2-50, x1=0, y1=h_b/2+50, fillcolor=C_STEEL, line_width=0)
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor="rgba(2,119,189,0.1)", line=dict(color=C_PLATE, width=2))

    for r in range(bolts['rows']):
        for c in range(bolts['cols']):
            bx, by = e1 + c*s_h, (h_pl/2 - lv) - r*s_v
            fig.add_shape(type="circle", x0=bx-bolts['d']/2, y0=by-bolts['d']/2, x1=bx+bolts['d']/2, y1=by+bolts['d']/2, fillcolor=C_BOLT)

    add_dim(fig, w_pl, h_pl/2, w_pl, -h_pl/2, f"H_PL={h_pl}", "V", offset=50)
    
    fig.update_layout(title="ELEVATION VIEW", xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1), plot_bgcolor="white")
    return fig

# 3. SIDE VIEW (SECTION)
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw, t_pl, h_pl = beam['h'], beam['b'], beam['tf'], beam['tw'], plate['t'], plate['h']

    # Column Flange Background (เส้นคู่ตามที่คุณแนะนำ)
    fig.add_shape(type="line", x0=-b/2-30, y0=-h/2-50, x1=-b/2-30, y1=h/2+50, line=dict(color=C_STEEL, width=3))
    fig.add_shape(type="line", x0=-b/2-22, y0=-h/2-50, x1=-b/2-22, y1=h/2+50, line=dict(color=C_STEEL, width=1))

    # I-Beam Section
    path = f"M {-b/2},{-h/2} L {b/2},{-h/2} L {b/2},{-h/2+tf} L {tw/2},{-h/2+tf} L {tw/2},{h/2-tf} L {b/2},{h/2-tf} L {b/2},{h/2} L {-b/2},{h/2} L {-b/2},{h/2-tf} L {-tw/2},{h/2-tf} L {-tw/2},{-h/2+tf} L {-b/2},{-h/2+tf} Z"
    fig.add_shape(type="path", path=path, fillcolor=C_SEC, line=dict(color=C_STEEL, width=2.5))
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, fillcolor=C_PLATE, line=dict(color=C_STEEL, width=1.5))

    add_dim(fig, -b/2, h/2, -b/2, -h/2, f"H={h}", "V", offset=-60)
    
    fig.update_layout(title="SECTION VIEW", xaxis=dict(visible=False), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1), plot_bgcolor="white")
    return fig
