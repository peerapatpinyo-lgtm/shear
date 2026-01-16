# drawing_utils.py (V17 - Ultra-Pro Engineering Output)
import plotly.graph_objects as go

# --- Professional Engineering Theme ---
THEME = {
    "plate": "#0277BD",      # Deep Professional Blue
    "beam_fill": "#F8F9FA",   # Clean Off-white
    "beam_outline": "#212529",# Graphite Black
    "bolt": "#C62828",       # Industrial Red
    "dim": "#546E7A",        # Slate Blue-Grey
    "grid": "#ECEFF1"        # Subtle Grid
}

def add_smart_dim(fig, x0, y0, x1, y1, text, axis="H", level=1):
    """ระบบเส้นมิติอัจฉริยะ ปรับระยะห่างอัตโนมัติ (level 1, 2, 3)"""
    gap = 45 * level  # เว้นระยะห่างตามชั้นของ Dimension
    
    if axis == "H":
        y_d = y0 + gap
        # Extension Lines (เว้นห่างจากชิ้นงาน 5 หน่วย)
        fig.add_shape(type="line", x0=x0, y0=y0+5, x1=x0, y1=y_d+8, line=dict(color=THEME["dim"], width=1))
        fig.add_shape(type="line", x0=x1, y0=y0+5, x1=x1, y1=y_d+8, line=dict(color=THEME["dim"], width=1))
        # Dim Line
        fig.add_shape(type="line", x0=x0, y0=y_d, x1=x1, y1=y_d, line=dict(color=THEME["dim"], width=1.2))
        # Tick Marks
        for x in [x0, x1]:
            fig.add_shape(type="line", x0=x-4, y0=y_d-4, x1=x+4, y1=y_d+4, line=dict(color=THEME["dim"], width=1.5))
    else:
        x_d = x0 + gap
        fig.add_shape(type="line", x0=x0+5, y0=y0, x1=x_d+8, y1=y0, line=dict(color=THEME["dim"], width=1))
        fig.add_shape(type="line", x0=x0+5, y0=y1, x1=x_d+8, y1=y1, line=dict(color=THEME["dim"], width=1))
        fig.add_shape(type="line", x0=x_d, y0=y0, x1=x_d, y1=y1, line=dict(color=THEME["dim"], width=1.2))
        for y in [y0, y1]:
            fig.add_shape(type="line", x0=x_d-4, y0=y-4, x1=x_d+4, y1=y+4, line=dict(color=THEME["dim"], width=1.5))

    # Text Annotation
    fig.add_annotation(
        x=(x0+x1)/2 if axis=="H" else x_d,
        y=y_d if axis=="H" else (y0+y1)/2,
        text=text, showarrow=False,
        font=dict(size=12, color="#000000"),
        bgcolor="rgba(255,255,255,0.9)",
        textangle=0 if axis=="H" else -90,
        xshift=0 if axis=="H" else 15,
        yshift=15 if axis=="H" else 0
    )

# =============================================================================
# 1. PLAN VIEW (Refined)
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, bf, w_pl, t_pl = beam['tw'], beam['b'], plate['w'], plate['t']
    e1, s_h = plate['e1'], bolts['s_h']

    # Column & Beam Body
    fig.add_shape(type="rect", x0=-40, y0=-bf/2, x1=0, y1=bf/2, fillcolor="#263238", line_width=0)
    fig.add_shape(type="rect", x0=0, y0=-tw/2, x1=w_pl+120, y1=tw/2, fillcolor=THEME["beam_fill"], line=dict(color=THEME["beam_outline"], width=2))
    
    # Shear Plate
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=tw/2+t_pl, fillcolor=THEME["plate"], line=dict(color=THEME["beam_outline"], width=1.5))

    # Bolts with Centerlines
    for i in range(bolts['cols']):
        bx = e1 + i*s_h
        fig.add_shape(type="rect", x0=bx-bolts['d']/2, y0=-tw/2-8, x1=bx+bolts['d']/2, y1=tw/2+t_pl+8, fillcolor=THEME["bolt"], line_width=0)
        # Centerline dash
        fig.add_shape(type="line", x0=bx, y0=-bf/2-20, x1=bx, y1=bf/2+20, line=dict(color=THEME["bolt"], width=0.5, dash="dash"))

    # Progressive Dimensions
    add_smart_dim(fig, 0, -bf/2-30, e1, -bf/2-30, f"{e1}", "H", level=1)
    add_smart_dim(fig, 0, -bf/2-30, w_pl, -bf/2-30, f"PL Width {w_pl}", "H", level=2)

    fig.update_layout(
        title="<b>PLAN VIEW - CONNECTION DETAIL</b>",
        xaxis=dict(visible=False, range=[-100, w_pl+200]),
        yaxis=dict(visible=False, range=[-bf/2-150, bf/2+150], scaleanchor="x", scaleratio=1),
        plot_bgcolor="white", margin=dict(t=50, b=50, l=50, r=50)
    )
    return fig

# =============================================================================
# 2. FRONT VIEW (Elevation - Detailed)
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_b, h_pl, w_pl = beam['h'], plate['h'], plate['w']
    e1, lv, s_v, s_h = plate['e1'], plate['lv'], bolts['s_v'], bolts['s_h']

    # Draw Column Section
    fig.add_shape(type="rect", x0=-40, y0=-h_b/2-100, x1=0, y1=h_b/2+100, fillcolor="#263238", line_width=0)
    
    # Beam Outlines (Hidden)
    for y in [h_b/2, -h_b/2]:
        fig.add_shape(type="line", x0=0, y0=y, x1=w_pl+150, y1=y, line=dict(color="#B0BEC5", width=1, dash="dot"))

    # Plate (With slight transparency for professional look)
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor="rgba(2, 119, 189, 0.15)", line=dict(color=THEME["plate"], width=2.5))

    # Bolts with Crosshairs
    for r in range(bolts['rows']):
        for c in range(bolts['cols']):
            bx, by = e1 + c*s_h, (h_pl/2 - lv) - r*s_v
            fig.add_shape(type="circle", x0=bx-bolts['d']/2, y0=by-bolts['d']/2, x1=bx+bolts['d']/2, y1=by+bolts['d']/2, fillcolor=THEME["bolt"], line_width=0)
            # Center Mark
            fig.add_shape(type="line", x0=bx-6, y0=by, x1=bx+6, y1=by, line=dict(color="white", width=0.5))
            fig.add_shape(type="line", x0=bx, y0=by-6, x1=bx, y1=by+6, line=dict(color="white", width=0.5))

    # Dimension Stack
    dim_x = w_pl + 40
    add_smart_dim(fig, dim_x, h_pl/2, dim_x, h_pl/2-lv, f"{lv}", "V", level=1)
    add_smart_dim(fig, dim_x, h_pl/2-lv, dim_x, h_pl/2-lv-s_v, f"{s_v}", "V", level=1)
    add_smart_dim(fig, dim_x, h_pl/2, dim_x, -h_pl/2, f"PL Height {h_pl}", "V", level=2)

    fig.update_layout(
        title="<b>ELEVATION - FRONT VIEW</b>",
        xaxis=dict(visible=False, range=[-100, w_pl+250]),
        yaxis=dict(visible=False, range=[-h_b/2-150, h_b/2+150], scaleanchor="x", scaleratio=1),
        plot_bgcolor="white"
    )
    return fig

# =============================================================================
# 3. SIDE VIEW (Sectional - World Class)
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw, t_pl, h_pl = beam['h'], beam['b'], beam['tf'], beam['tw'], plate['t'], plate['h']

    # Path-based I-Beam (Perfect Geometry)
    path = f"M {-b/2},{-h/2} L {b/2},{-h/2} L {b/2},{-h/2+tf} L {tw/2},{-h/2+tf} L {tw/2},{h/2-tf} L {b/2},{h/2-tf} L {b/2},{h/2} L {-b/2},{h/2} L {-b/2},{h/2-tf} L {-tw/2},{h/2-tf} L {-tw/2},{-h/2+tf} L {-b/2},{-h/2+tf} Z"
    fig.add_shape(type="path", path=path, fillcolor=THEME["beam_fill"], line=dict(color=THEME["beam_outline"], width=2.5))
    
    # Connection Plate
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, fillcolor=THEME["plate"], line=dict(color=THEME["beam_outline"], width=1.5))

    # Leader Line Callout
    fig.add_annotation(x=tw/2+t_pl, y=h_pl/3, text=f"Shear Plate t={t_pl}mm", showarrow=True, arrowhead=2, ax=60, ay=-30, bgcolor="white", bordercolor=THEME["plate"])

    # Core Dimensions
    add_smart_dim(fig, -b/2-40, h/2, -b/2-40, -h/2, f"H = {h}", "V", level=1)
    add_smart_dim(fig, -b/2, h/2+40, b/2, h/2+40, f"B = {b}", "H", level=1)

    fig.update_layout(
        title="<b>SECTION VIEW - BEAM PROFILE</b>",
        xaxis=dict(visible=False, range=[-b/2-200, b/2+200]),
        yaxis=dict(visible=False, range=[-h/2-200, h/2+200], scaleanchor="x", scaleratio=1),
        plot_bgcolor="white"
    )
    return fig
