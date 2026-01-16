# drawing_utils.py (V15 - Senior Structural Engineer Edition)
import plotly.graph_objects as go

# Color System - Professional Dark Theme for Steel
C_STEEL_DARK = "#1e293b"   # เสา/ชิ้นงานหลัก
C_BEAM_BODY = "#f1f5f9"    # ตัวคาน
C_PLATE = "#0369a1"        # แผ่นเหล็ก (Deep Sky)
C_BOLT = "#be123c"         # โบลท์ (Crimson)
C_DIM_LINE = "#475569"     # เส้นมิติ (Slate)
C_CL_LINE = "#dc2626"      # เส้นศูนย์กลาง

def add_pro_dim(fig, x0, y0, x1, y1, text, mode="H", offset=60):
    """ เส้นบอกมิติระดับอาวุโส: มี Extension line และกึ่งกลางตัวเลข """
    line_w = 1.0
    text_size = 12
    
    if mode == "H":
        y_pos = y0 + offset
        # Extension lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_pos + (10 if offset>0 else -10), line=dict(color=C_DIM_LINE, width=line_w))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_pos + (10 if offset>0 else -10), line=dict(color=C_DIM_LINE, width=line_w))
        # Main Dimension Line
        fig.add_shape(type="line", x0=x0, y0=y_pos, x1=x1, y1=y_pos, line=dict(color=C_DIM_LINE, width=line_w + 0.5))
        # Tick marks (เฉียง 45 องศา แทนลูกศรแบบเดิม)
        for x in [x0, x1]:
            fig.add_shape(type="line", x0=x-3, y0=y_pos-3, x1=x+3, y1=y_pos+3, line=dict(color=C_DIM_LINE, width=1.5))
        # Text label
        fig.add_annotation(x=(x0+x1)/2, y=y_pos, text=f"<b>{text}</b>", showarrow=False, yshift=12 if offset>0 else -12,
                           font=dict(size=text_size, color="black"), bgcolor="white")
    else:
        x_pos = x0 + offset
        # Extension lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_pos + (10 if offset>0 else -10), y1=y0, line=dict(color=C_DIM_LINE, width=line_w))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_pos + (10 if offset>0 else -10), y1=y1, line=dict(color=C_DIM_LINE, width=line_w))
        # Main Dimension Line
        fig.add_shape(type="line", x0=x_pos, y0=y0, x1=x_pos, y1=y1, line=dict(color=C_DIM_LINE, width=line_w + 0.5))
        # Tick marks
        for y in [y0, y1]:
            fig.add_shape(type="line", x0=x_pos-3, y0=y-3, x1=x_pos+3, y1=y+3, line=dict(color=C_DIM_LINE, width=1.5))
        # Text label
        fig.add_annotation(x=x_pos, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=18 if offset>0 else -18,
                           textangle=-90, font=dict(size=text_size, color="black"), bgcolor="white")

# =============================================================================
# 1. PLAN VIEW (Senior Quality)
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, bf = beam['tw'], beam['b']
    w_pl, t_pl, e1, s_h = plate['w'], plate['t'], plate['e1'], bolts['s_h']
    
    # วาด Column Flange (หนาขึ้น ดูมีน้ำหนัก)
    fig.add_shape(type="rect", x0=-25, y0=-bf/2, x1=0, y1=bf/2, fillcolor=C_STEEL_DARK, line_width=0)
    # วาด Beam (เห็นความหนา Web)
    fig.add_shape(type="rect", x0=0, y0=-tw/2, x1=w_pl+100, y1=tw/2, fillcolor=C_BEAM_BODY, line=dict(color=C_STEEL_DARK, width=1.5))
    # แผ่น Shear Plate
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=tw/2+t_pl, fillcolor=C_PLATE, line=dict(color=C_STEEL_DARK, width=1))

    # Bolts Details (หัวโบลท์หกเหลี่ยมจำลอง)
    for i in range(bolts['cols']):
        bx = e1 + i*s_h
        fig.add_shape(type="rect", x0=bx-bolts['d']/2, y0=-tw/2-5, x1=bx+bolts['d']/2, y1=tw/2+t_pl+5, fillcolor=C_BOLT, line_width=0)

    # Dimensions
    add_pro_dim(fig, 0, -bf/2, e1, -bf/2, f"{e1}", "H", offset=-50)
    add_pro_dim(fig, 0, -bf/2, w_pl, -bf/2, f"W_pl={w_pl}", "H", offset=-90)

    fig.update_layout(title="<b>PLAN VIEW (SCALE 1:1)</b>", plot_bgcolor="white", height=450,
                      xaxis=dict(visible=False, range=[-100, w_pl+200]),
                      yaxis=dict(visible=False, range=[-bf/2-150, bf/2+150], scaleanchor="x", scaleratio=1))
    return fig

# =============================================================================
# 2. ELEVATION VIEW (Senior Quality)
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_b, h_pl, w_pl = beam['h'], plate['h'], plate['w']
    e1, lv, s_v, s_h = plate['e1'], plate['lv'], bolts['s_v'], bolts['s_h']

    # Column Background
    fig.add_shape(type="rect", x0=-30, y0=-h_b/2-100, x1=0, y1=h_b/2+100, fillcolor=C_STEEL_DARK, line_width=0)
    # Hidden Beam Lines (แสดงแนวปีกคาน Top/Bottom Flange)
    for y in [h_b/2, h_b/2-beam['tf'], -h_b/2+beam['tf'], -h_b/2]:
        fig.add_shape(type="line", x0=0, y0=y, x1=w_pl+150, y1=y, line=dict(color="#94a3b8", width=1, dash="dot"))
    
    # Shear Plate (กึ่งโปร่งใสเพื่อให้เห็นเส้น Grid)
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor="rgba(3, 105, 161, 0.15)", line=dict(color=C_PLATE, width=2))
    
    # Bolts with Cross marks (+)
    for r in range(bolts['rows']):
        for c in range(bolts['cols']):
            bx, by = e1 + c*s_h, (h_pl/2 - lv) - r*s_v
            fig.add_shape(type="circle", x0=bx-bolts['d']/2, y0=by-bolts['d']/2, x1=bx+bolts['d']/2, y1=by+bolts['d']/2, fillcolor=C_BOLT, line_width=0)
            # Center mark
            fig.add_shape(type="line", x0=bx-5, y0=by, x1=bx+5, y1=by, line=dict(color="white", width=0.5))
            fig.add_shape(type="line", x0=bx, y0=by-5, x1=bx, y1=by+5, line=dict(color="white", width=0.5))

    # Dimensions (จัดวางแบบสะอาดตา)
    add_pro_dim(fig, w_pl, h_pl/2, w_pl, h_pl/2-lv, f"{lv}", "V", offset=60)
    add_pro_dim(fig, w_pl, h_pl/2-lv, w_pl, h_pl/2-lv-s_v, f"{s_v}", "V", offset=60)
    add_pro_dim(fig, w_pl, h_pl/2, w_pl, -h_pl/2, f"H_pl={h_pl}", "V", offset=110)

    fig.update_layout(title="<b>ELEVATION (CONNECTION DETAIL)</b>", plot_bgcolor="white", height=500,
                      xaxis=dict(visible=False, range=[-100, w_pl+250]),
                      yaxis=dict(visible=False, range=[-h_b/2-150, h_b/2+150], scaleanchor="x", scaleratio=1))
    return fig

# =============================================================================
# 3. SIDE VIEW (Senior Quality)
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    h_pl, t_pl = plate['h'], plate['t']

    # Draw Beam Section (คมชัดทุกองศา)
    path = f"M {-b/2},{-h/2} L {b/2},{-h/2} L {b/2},{-h/2+tf} L {tw/2},{-h/2+tf} L {tw/2},{h/2-tf} L {b/2},{h/2-tf} L {b/2},{h/2} L {-b/2},{h/2} L {-b/2},{h/2-tf} L {-tw/2},{h/2-tf} L {-tw/2},{-h/2+tf} L {-b/2},{-h/2+tf} Z"
    fig.add_shape(type="path", path=path, fillcolor=C_BEAM_BODY, line=dict(color=C_STEEL_DARK, width=2))
    
    # Plate
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, fillcolor=C_PLATE, line=dict(color=C_STEEL_DARK, width=1))

    # Label & Callout
    fig.add_annotation(x=0, y=h/2, text=f"BEAM {h}x{b}", showarrow=True, arrowhead=2, ay=-40, ax=40)

    # Dimensions
    add_pro_dim(fig, -b/2, h/2, -b/2, -h/2, f"H={h}", "V", offset=-70)
    add_pro_dim(fig, -b/2, h/2, b/2, h/2, f"B={b}", "H", offset=50)

    fig.update_layout(title="<b>SECTION VIEW</b>", plot_bgcolor="white", height=450,
                      xaxis=dict(visible=False, range=[-b/2-200, b/2+200]),
                      yaxis=dict(visible=False, range=[-h/2-200, h/2+200], scaleanchor="x", scaleratio=1))
    return fig
