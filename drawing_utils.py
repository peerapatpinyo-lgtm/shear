# drawing_utils.py (V20 - Master Class Production)
import plotly.graph_objects as go

# --- Professional Standards ---
THEME = {
    "steel_dark": "#263238", # เสา
    "steel_light": "#F5F5F5", # คาน
    "plate": "#1976D2",       # Plate
    "bolt": "#D32F2F",        # Bolt
    "dim_line": "#546E7A",    # Dimension
    "text": "#000000"
}

def add_standard_dim(fig, x0, y0, x1, y1, text, axis="H", offset=60):
    """ฟังก์ชันให้ระยะมาตรฐานวิศวกรรมสากล"""
    if axis == "H":
        y_pos = y0 + offset
        # Extension lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_pos + (10 if offset>0 else -10), line=dict(color=THEME["dim_line"], width=1))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_pos + (10 if offset>0 else -10), line=dict(color=THEME["dim_line"], width=1))
        # Main line & Ticks
        fig.add_shape(type="line", x0=x0, y0=y_pos, x1=x1, y1=y_pos, line=dict(color=THEME["dim_line"], width=1.2))
        fig.add_shape(type="line", x0=x0-4, y0=y_pos-4, x1=x0+4, y1=y_pos+4, line=dict(color=THEME["dim_line"], width=1.5))
        fig.add_shape(type="line", x0=x1-4, y0=y_pos-4, x1=x1+4, y1=y_pos+4, line=dict(color=THEME["dim_line"], width=1.5))
        fig.add_annotation(x=(x0+x1)/2, y=y_pos, text=f"<b>{text}</b>", showarrow=False, yshift=12 if offset>0 else -12, font=dict(size=11))
    else:
        x_pos = x0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_pos + (10 if offset>0 else -10), y1=y0, line=dict(color=THEME["dim_line"], width=1))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_pos + (10 if offset>0 else -10), y1=y1, line=dict(color=THEME["dim_line"], width=1))
        fig.add_shape(type="line", x0=x_pos, y0=y0, x1=x_pos, y1=y1, line=dict(color=THEME["dim_line"], width=1.2))
        fig.add_shape(type="line", x0=x_pos-4, y0=y0-4, x1=x_pos+4, y1=y0+4, line=dict(color=THEME["dim_line"], width=1.5))
        fig.add_shape(type="line", x0=x_pos-4, y0=y1-4, x1=x_pos+4, y1=y1+4, line=dict(color=THEME["dim_line"], width=1.5))
        fig.add_annotation(x=x_pos, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=18 if offset>0 else -18, textangle=-90, font=dict(size=11))

# =============================================================================
# 1. PLAN VIEW
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, bf, w_pl, t_pl = beam['tw'], beam['b'], plate['w'], plate['t']
    e1, s_h = plate['e1'], bolts['s_h']
    
    # เสา (Column Flange)
    fig.add_shape(type="rect", x0=-40, y0=-bf/2, x1=0, y1=bf/2, fillcolor=THEME["steel_dark"], line_width=0)
    # คาน (Beam Web)
    fig.add_shape(type="rect", x0=0, y0=-tw/2, x1=w_pl+150, y1=tw/2, fillcolor=THEME["steel_light"], line=dict(color=THEME["steel_dark"], width=2))
    # Plate
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=tw/2+t_pl, fillcolor=THEME["plate"], line=dict(color=THEME["steel_dark"], width=1))

    # Bolts
    for i in range(bolts['cols']):
        bx = e1 + i*s_h
        fig.add_shape(type="rect", x0=bx-bolts['d']/2, y0=-tw/2-10, x1=bx+bolts['d']/2, y1=tw/2+t_pl+10, fillcolor=THEME["bolt"], line_width=0)

    add_standard_dim(fig, 0, -bf/2, w_pl, -bf/2, f"W_PL={w_pl}", axis="H", offset=-50)

    fig.update_layout(xaxis=dict(visible=False, range=[-100, w_pl+200]), 
                      yaxis=dict(visible=False, range=[-bf/2-100, bf/2+100], scaleanchor="x", scaleratio=1),
                      plot_bgcolor="white", height=400, margin=dict(l=20, r=20, t=40, b=20))
    return fig

# =============================================================================
# 2. ELEVATION VIEW (FRONT)
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_b, h_pl, w_pl = beam['h'], plate['h'], plate['w']
    e1, lv, s_v, s_h = plate['e1'], plate['lv'], bolts['s_v'], bolts['s_h']

    # Column
    fig.add_shape(type="rect", x0=-40, y0=-h_b/2-50, x1=0, y1=h_b/2+50, fillcolor=THEME["steel_dark"], line_width=0)
    # Plate
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor="rgba(25, 118, 210, 0.1)", line=dict(color=THEME["plate"], width=2.5))

    # Bolts with proper Edge Distance check
    for r in range(bolts['rows']):
        for c in range(bolts['cols']):
            bx, by = e1 + c*s_h, (h_pl/2 - lv) - r*s_v
            fig.add_shape(type="circle", x0=bx-bolts['d']/2, y0=by-bolts['d']/2, x1=bx+bolts['d']/2, y1=by+bolts['d']/2, fillcolor=THEME["bolt"])

    # Double Level Dimensions
    add_standard_dim(fig, w_pl, h_pl/2, w_pl, h_pl/2-lv, f"{lv}", axis="V", offset=40)
    add_standard_dim(fig, w_pl, h_pl/2, w_pl, -h_pl/2, f"H_PL={h_pl}", axis="V", offset=90)

    fig.update_layout(xaxis=dict(visible=False, range=[-100, w_pl+250]), 
                      yaxis=dict(visible=False, range=[-h_b/2-100, h_b/2+100], scaleanchor="x", scaleratio=1),
                      plot_bgcolor="white", height=400, margin=dict(l=20, r=20, t=40, b=20))
    return fig

# =============================================================================
# 3. SECTION VIEW (SIDE)
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw, t_pl, h_pl = beam['h'], beam['b'], beam['tf'], beam['tw'], plate['t'], plate['h']

    # --- หัวใจสำคัญ: เส้นคู่บอกระดับเสาที่ด้านหลัง ---
    fig.add_shape(type="line", x0=-b/2-40, y0=-h/2-100, x1=-b/2-40, y1=h/2+100, line=dict(color=THEME["steel_dark"], width=3))
    fig.add_shape(type="line", x0=-b/2-32, y0=-h/2-100, x1=-b/2-32, y1=h/2+100, line=dict(color=THEME["steel_dark"], width=1))

    # I-Beam Section
    p = f"M {-b/2},{-h/2} L {b/2},{-h/2} L {b/2},{-h/2+tf} L {tw/2},{-h/2+tf} L {tw/2},{h/2-tf} L {b/2},{h/2-tf} L {b/2},{h/2} L {-b/2},{h/2} L {-b/2},{h/2-tf} L {-tw/2},{h/2-tf} L {-tw/2},{-h/2+tf} L {-b/2},{-h/2+tf} Z"
    fig.add_shape(type="path", path=p, fillcolor=THEME["steel_light"], line=dict(color=THEME["steel_dark"], width=2.5))
    
    # Plate Position (แปะข้าง Web)
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, fillcolor=THEME["plate"], line=dict(color=THEME["steel_dark"], width=1.5))

    add_standard_dim(fig, -b/2, h/2, -b/2, -h/2, f"H={h}", axis="V", offset=-70)
    add_standard_dim(fig, -b/2, h/2, b/2, h/2, f"B={b}", axis="H", offset=50)

    fig.update_layout(xaxis=dict(visible=False, range=[-b/2-200, b/2+200]), 
                      yaxis=dict(visible=False, range=[-h/2-150, h/2+150], scaleanchor="x", scaleratio=1),
                      plot_bgcolor="white", height=400, margin=dict(l=20, r=20, t=40, b=20))
    return fig
