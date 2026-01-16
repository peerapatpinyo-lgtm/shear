# drawing_utils.py (V18 - Technical Fabrication Version)
import plotly.graph_objects as go

# --- Standard Engineering Styles ---
C_STEEL = "#212529"   # Graphite
C_PLATE = "#0277BD"   # Steel Blue
C_BOLT = "#D32F2F"    # Red
C_DIM = "#455A64"     # Dark Slate
C_SEC = "#ECEFF1"     # Light Grey for Fill

def add_dim(fig, x0, y0, x1, y1, text, orient="H", offset=50):
    """ฟังก์ชันให้มิติมาตรฐานสากล พร้อม Tick Marks และ Extension Line ที่ชัดเจน"""
    l_w = 1.2
    if orient == "H":
        y_d = y0 + offset
        # Extension lines (เว้นระยะจากงาน 5mm)
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_d+10, line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_d+10, line=dict(color=C_DIM, width=1))
        # Dim Line & Ticks
        fig.add_shape(type="line", x0=x0, y0=y_d, x1=x1, y1=y_d, line=dict(color=C_DIM, width=l_w))
        fig.add_shape(type="line", x0=x0-5, y0=y_d-5, x1=x0+5, y1=y_d+5, line=dict(color=C_DIM, width=1.5))
        fig.add_shape(type="line", x0=x1-5, y0=y_d-5, x1=x1+5, y1=y_d+5, line=dict(color=C_DIM, width=1.5))
        fig.add_annotation(x=(x0+x1)/2, y=y_d, text=text, showarrow=False, yshift=12, font=dict(size=12, color="black"), bgcolor="white")
    else:
        x_d = x0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_d+10, y1=y0, line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_d+10, y1=y1, line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x_d, y0=y0, x1=x_d, y1=y1, line=dict(color=C_DIM, width=l_w))
        fig.add_shape(type="line", x0=x_d-5, y0=y0-5, x1=x_d+5, y1=y0+5, line=dict(color=C_DIM, width=1.5))
        fig.add_shape(type="line", x0=x_d-5, y0=y1-5, x1=x_d+5, y1=y1+5, line=dict(color=C_DIM, width=1.5))
        fig.add_annotation(x=x_d, y=(y0+y1)/2, text=text, showarrow=False, xshift=15, textangle=-90, font=dict(size=12, color="black"), bgcolor="white")

# =============================================================================
# 1. ELEVATION (FRONT) - แก้ไขระยะ Bolt และ Plate ให้ถูกต้อง
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_b, h_pl, w_pl = beam['h'], plate['h'], plate['w']
    e1, lv, s_v, s_h = plate['e1'], plate['lv'], bolts['s_v'], bolts['s_h']

    # Column (Background Support)
    fig.add_shape(type="rect", x0=-40, y0=-h_b/2-50, x1=0, y1=h_b/2+50, fillcolor=C_STEEL, line_width=0)
    
    # Shear Plate (Drawing correct geometry)
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor="rgba(2, 119, 189, 0.1)", line=dict(color=C_PLATE, width=2.5))

    # Bolts Placement & Centerlines
    for r in range(bolts['rows']):
        for c in range(bolts['cols']):
            bx, by = e1 + c*s_h, (h_pl/2 - lv) - r*s_v
            fig.add_shape(type="circle", x0=bx-bolts['d']/2, y0=by-bolts['d']/2, x1=bx+bolts['d']/2, y1=by+bolts['d']/2, fillcolor=C_BOLT, line_width=0)
            # Centerlines (Professional Tick)
            fig.add_shape(type="line", x0=bx-8, y0=by, x1=bx+8, y1=by, line=dict(color="white", width=0.5))
            fig.add_shape(type="line", x0=bx, y0=by-8, x1=bx, y1=by+8, line=dict(color="white", width=0.5))

    # --- Technical Dimensioning (Multi-level) ---
    # Vertical (Right side)
    dim_x = w_pl + 40
    add_dim(fig, w_pl, h_pl/2, w_pl, h_pl/2-lv, f"{lv}", "V", offset=40)
    for i in range(bolts['rows']-1):
        y0 = h_pl/2 - lv - i*s_v
        y1 = y0 - s_v
        add_dim(fig, w_pl, y0, w_pl, y1, f"{s_v}", "V", offset=40)
    # Overall Plate Height
    add_dim(fig, w_pl, h_pl/2, w_pl, -h_pl/2, f"H_PL = {h_pl}", "V", offset=90)

    # Horizontal (Bottom)
    add_dim(fig, 0, -h_pl/2, e1, -h_pl/2, f"{e1}", "H", offset=-50)
    add_dim(fig, 0, -h_pl/2, w_pl, -h_pl/2, f"W_PL = {w_pl}", "H", offset=-100)

    fig.update_layout(title="<b>ELEVATION VIEW (TECHNICAL SCALE)</b>", 
                      xaxis=dict(visible=False, range=[-100, w_pl+200]),
                      yaxis=dict(visible=False, range=[-h_b/2-100, h_b/2+100], scaleanchor="x", scaleratio=1),
                      plot_bgcolor="white", height=600)
    return fig

# =============================================================================
# 2. SIDE VIEW (SECTION) - เพิ่มเส้นแสดงเสาด้านหลัง (Context)
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw, t_pl, h_pl = beam['h'], beam['b'], beam['tf'], beam['tw'], plate['t'], plate['h']

    # --- เส้นคู่แนวดิ่งบอกว่าเป็นเสา (Column Flange Background) ---
    # บ่งบอกว่าหน้าตัดคานวางอยู่หน้าเสา
    col_w = 40
    fig.add_shape(type="line", x0=-b/2-col_w, y0=-h/2-100, x1=-b/2-col_w, y1=h/2+100, line=dict(color=C_STEEL, width=3))
    fig.add_shape(type="line", x0=-b/2-col_w+10, y0=-h/2-100, x1=-b/2-col_w+10, y1=h/2+100, line=dict(color=C_STEEL, width=1))

    # I-Beam Section (SVG Path)
    path = f"M {-b/2},{-h/2} L {b/2},{-h/2} L {b/2},{-h/2+tf} L {tw/2},{-h/2+tf} L {tw/2},{h/2-tf} L {b/2},{h/2-tf} L {b/2},{h/2} L {-b/2},{h/2} L {-b/2},{h/2-tf} L {-tw/2},{h/2-tf} L {-tw/2},{-h/2+tf} L {-b/2},{-h/2+tf} Z"
    fig.add_shape(type="path", path=path, fillcolor=C_SEC, line=dict(color=C_STEEL, width=2.5))
    
    # Shear Plate
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, fillcolor=C_PLATE, line=dict(color=C_STEEL, width=1.5))

    # Callouts & Annotations
    fig.add_annotation(x=tw/2+t_pl, y=0, text=f"PL {h_pl}x{t_pl}mm", showarrow=True, arrowhead=2, ax=50, ay=0)
    fig.add_annotation(x=0, y=h/2, text=f"W-Section {h}x{b}", showarrow=True, ax=0, ay=-60)

    # Core Dimensions
    add_dim(fig, -b/2, h/2, b/2, h/2, f"B={b}", "H", offset=50)
    add_dim(fig, -b/2, h/2, -b/2, -h/2, f"H={h}", "V", offset=-60)

    fig.update_layout(title="<b>SECTION VIEW (STRUCTURAL CONTEXT)</b>",
                      xaxis=dict(visible=False, range=[-b/2-150, b/2+150]),
                      yaxis=dict(visible=False, range=[-h/2-150, h/2+150], scaleanchor="x", scaleratio=1),
                      plot_bgcolor="white", height=600)
    return fig
