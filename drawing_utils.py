import plotly.graph_objects as go

# =============================================================================
# 🎨 ENGINEERING COLORS & STYLES
# =============================================================================
C_COL_LINE = "#eab308"    # เส้นอ้างอิงหน้าเสา (สีเหลือง)
C_STEEL_OUT = "#0f172a"   # ขอบเหล็ก (Midnight Blue)
C_STEEL_FILL = "#f8fafc"  # เนื้อเหล็ก
C_PLATE = "#38bdf8"       # Shear Plate (Sky Blue)
C_BOLT = "#e11d48"        # Bolt (Rose Red)
C_DIM = "#475569"         # เส้นบอกระยะ (Slate)

# =============================================================================
# 📏 DIMENSION SYSTEM (Standard Engineering Ticks)
# =============================================================================
def add_dim(fig, x0, y0, x1, y1, text, mode="h", offset=30):
    loc = (y0 + offset) if mode == "h" else (x0 + offset)
    line_w = 1
    
    if mode == "h":
        # Extension & Dim line
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=loc+5, line=dict(color=C_DIM, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=loc+5, line=dict(color=C_DIM, width=0.5))
        fig.add_shape(type="line", x0=x0, y0=loc, x1=x1, y1=loc, line=dict(color=C_DIM, width=line_w))
        # Ticks
        for x in [x0, x1]:
            fig.add_shape(type="line", x0=x-3, y0=loc-3, x1=x+3, y1=loc+3, line=dict(color=C_DIM, width=1.5))
        fig.add_annotation(x=(x0+x1)/2, y=loc, text=text, showarrow=False, yshift=12, font=dict(size=12))
    else:
        # Extension & Dim line
        fig.add_shape(type="line", x0=x0, y0=y0, x1=loc+5, y1=y0, line=dict(color=C_DIM, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=loc+5, y1=y1, line=dict(color=C_DIM, width=0.5))
        fig.add_shape(type="line", x0=loc, y0=y0, x1=loc, y1=y1, line=dict(color=C_DIM, width=line_w))
        # Ticks
        for y in [y0, y1]:
            fig.add_shape(type="line", x0=loc-3, y0=y-3, x1=loc+3, y1=y+3, line=dict(color=C_DIM, width=1.5))
        fig.add_annotation(x=loc, y=(y0+y1)/2, text=text, showarrow=False, xshift=18, textangle=-90, font=dict(size=12))

# =============================================================================
# 1. PLAN VIEW
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, b, w_pl, t_pl = beam['tw'], beam['b'], plate['w'], plate['t']
    
    # Column Face (Yellow line)
    fig.add_shape(type="line", x0=0, y0=-b/2-10, x1=0, y1=b/2+10, line=dict(color=C_COL_LINE, width=4))
    # Beam & Plate (Flush to Column Face)
    fig.add_shape(type="rect", x0=0, y0=-tw/2, x1=w_pl+20, y1=tw/2, fillcolor=C_STEEL_FILL, line=dict(color=C_STEEL_OUT))
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=tw/2+t_pl, fillcolor=C_PLATE, line=dict(color=C_STEEL_OUT))
    
    add_dim(fig, 0, tw/2+t_pl, w_pl, tw/2+t_pl, f"Wp={w_pl}", "h", 30)
    fig.update_layout(title="PLAN VIEW", plot_bgcolor="white", height=300, showlegend=False,
                      xaxis=dict(visible=False, range=[-20, w_pl+40]), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1))
    return fig

# =============================================================================
# 2. ELEVATION VIEW (Front)
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_b, h_pl, w_pl = beam['h'], plate['h'], plate['w']
    lv, s_v, n_rows = plate.get('lv', 35), bolts['s_v'], bolts['rows']
    
    # Column Reference
    fig.add_shape(type="line", x0=0, y0=-h_b/2-10, x1=0, y1=h_b/2+10, line=dict(color=C_COL_LINE, width=4))
    # Plate
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor=C_PLATE, line=dict(color=C_STEEL_OUT))
    
    # Bolts
    for i in range(n_rows):
        y_bolt = h_pl/2 - lv - (i * s_v)
        fig.add_shape(type="circle", x0=w_pl/2-5, y0=y_bolt-5, x1=w_pl/2+5, y1=y_bolt+5, fillcolor=C_BOLT, line_width=0)

    add_dim(fig, w_pl, h_pl/2, w_pl, -h_pl/2, f"Hp={h_pl}", "v", 25)
    fig.update_layout(title="ELEVATION VIEW", plot_bgcolor="white", height=350,
                      xaxis=dict(visible=False, range=[-20, w_pl+50]), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1))
    return fig

# =============================================================================
# 3. SIDE VIEW (SECTION) - อ้างอิงตามรูปสเก็ตช์ 100%
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    h_pl, t_pl = plate['h'], plate['t']
    lv, s_v, n_rows = plate.get('lv', 35), bolts['s_v'], bolts['rows']

    # Draw Column Section (หน้าตัดเสาที่เรามองเห็น)
    # ตามรูปสเก็ตช์ คานจะเชื่อมกับ "หน้าแปลนเสา"
    fig.add_shape(type="line", x0=-b/2, y0=-h/2-20, x1=-b/2, y1=h/2+20, line=dict(color=C_COL_LINE, width=3))

    # Draw I-Beam (Flush to the yellow line)
    # Flanges
    fig.add_shape(type="rect", x0=-b/2, y0=h/2-tf, x1=b/2, y1=h/2, fillcolor=C_STEEL_FILL, line=dict(color=C_STEEL_OUT))
    fig.add_shape(type="rect", x0=-b/2, y0=-h/2, x1=b/2, y1=-h/2+tf, fillcolor=C_STEEL_FILL, line=dict(color=C_STEEL_OUT))
    # Web
    fig.add_shape(type="rect", x0=-tw/2, y0=-h/2+tf, x1=tw/2, y1=h/2-tf, fillcolor=C_STEEL_FILL, line=dict(color=C_STEEL_OUT))

    # Shear Plate (Attached to Web)
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, fillcolor=C_PLATE, line=dict(color=C_STEEL_OUT))
    
    # Bolts (Showing bolt heads)
    for i in range(n_rows):
        y_bolt = h_pl/2 - lv - (i * s_v)
        fig.add_shape(type="rect", x0=tw/2+t_pl, y0=y_bolt-4, x1=tw/2+t_pl+8, y1=y_bolt+4, fillcolor=C_BOLT, line_width=0)
    
    # Dimensions (ตามที่สเก็ตช์ไว้: H=400, B=200)
    add_dim(fig, -b/2, h/2, b/2, h/2, f"B={b}", "h", 35)
    add_dim(fig, -b/2, h/2, -b/2, -h/2, f"H={h}", "v", -35)
    add_dim(fig, tw/2, -h_pl/2, tw/2+t_pl, -h_pl/2, f"t={t_pl}", "h", -35)

    fig.update_layout(title="DETAILED SECTION VIEW", plot_bgcolor="white", height=450, margin=dict(l=50,r=50,t=50,b=50),
                      xaxis=dict(visible=False, range=[-b, b]), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1))
    return fig
