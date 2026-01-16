import plotly.graph_objects as go

# =============================================================================
# 🎨 STYLE GUIDE: Engineering Standard
# =============================================================================
C_YELLOW_COL = "#eab308"   # เส้นอ้างอิงหน้าเสา (ตามสเก็ตช์)
C_STEEL_OUT = "#1e293b"    # ขอบเหล็ก
C_STEEL_FILL = "#f1f5f9"   # เนื้อเหล็กคาน
C_PLATE = "#0ea5e9"        # Shear Plate
C_BOLT = "#be123c"         # Bolt
C_DIM = "#475569"          # เส้นบอกขนาด

# =============================================================================
# 📏 ADVANCED DIMENSIONING (Clean & Consistent)
# =============================================================================
def add_eng_dim(fig, x0, y0, x1, y1, text, mode="h", offset=25):
    """ วาดเส้นบอกระยะแบบ Engineering พร้อม Tick marks """
    loc = (y0 + offset) if mode == "h" else (x0 + offset)
    
    if mode == "h":
        # Extension lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=loc+5, line=dict(color=C_DIM, width=0.8))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=loc+5, line=dict(color=C_DIM, width=0.8))
        # Dim line
        fig.add_shape(type="line", x0=x0, y0=loc, x1=x1, y1=loc, line=dict(color=C_DIM, width=1))
        # Ticks (แทนลูกศรเพื่อให้ดูเป็นแบบวิศวกรรมขึ้น)
        for x_tick in [x0, x1]:
            fig.add_shape(type="line", x0=x_tick-2, y0=loc-4, x1=x_tick+2, y1=loc+4, line=dict(color=C_DIM, width=1.2))
        # Text
        fig.add_annotation(x=(x0+x1)/2, y=loc, text=text, showarrow=False, yshift=10, font=dict(size=11, family="Arial"))
    else:
        # Extension lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=loc+5, y1=y0, line=dict(color=C_DIM, width=0.8))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=loc+5, y1=y1, line=dict(color=C_DIM, width=0.8))
        # Dim line
        fig.add_shape(type="line", x0=loc, y0=y0, x1=loc, y1=y1, line=dict(color=C_DIM, width=1))
        # Ticks
        for y_tick in [y0, y1]:
            fig.add_shape(type="line", x0=loc-4, y0=y_tick-2, x1=loc+4, y1=y_tick+2, line=dict(color=C_DIM, width=1.2))
        # Text
        fig.add_annotation(x=loc, y=(y0+y1)/2, text=text, showarrow=False, xshift=15, textangle=-90, font=dict(size=11, family="Arial"))

# =============================================================================
# 1. PLAN VIEW (จัดให้สมมาตร)
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, b, w_pl, t_pl = beam['tw'], beam['b'], plate['w'], plate['t']
    
    # Column Boundary (เส้นอ้างอิงเสา)
    fig.add_shape(type="line", x0=0, y0=-b/2-20, x1=0, y1=b/2+20, line=dict(color=C_YELLOW_COL, width=3))
    
    # Beam & Plate
    fig.add_shape(type="rect", x0=0, y0=-tw/2, x1=w_pl+30, y1=tw/2, fillcolor=C_STEEL_FILL, line=dict(color=C_STEEL_OUT))
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=tw/2+t_pl, fillcolor=C_PLATE, line=dict(color=C_STEEL_OUT))
    
    add_eng_dim(fig, 0, tw/2+t_pl, w_pl, tw/2+t_pl, f"Wp={w_pl}", "h", 30)
    
    fig.update_layout(title="PLAN VIEW", plot_bgcolor="white", height=300, margin=dict(l=40,r=40,t=40,b=40),
                      xaxis=dict(visible=False, range=[-20, w_pl+50]), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1))
    return fig

# =============================================================================
# 2. ELEVATION VIEW (เน้นหน้า Plate)
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_b, h_pl, w_pl = beam['h'], plate['h'], plate['w']
    lv, s_v, n_rows = plate.get('lv', 35), bolts['s_v'], bolts['rows']
    
    fig.add_shape(type="line", x0=0, y0=-h_b/2-20, x1=0, y1=h_b/2+20, line=dict(color=C_YELLOW_COL, width=3))
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor=C_PLATE, line=dict(color=C_STEEL_OUT))
    
    for i in range(n_rows):
        y_bolt = h_pl/2 - lv - (i * s_v)
        fig.add_shape(type="circle", x0=w_pl/2-5, y0=y_bolt-5, x1=w_pl/2+5, y1=y_bolt+5, fillcolor=C_BOLT)

    add_eng_dim(fig, w_pl, h_pl/2, w_pl, -h_pl/2, f"Hp={h_pl}", "v", 30)
    
    fig.update_layout(title="ELEVATION", plot_bgcolor="white", height=350, margin=dict(l=40,r=40,t=40,b=40),
                      xaxis=dict(visible=False, range=[-20, w_pl+60]), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1))
    return fig

# =============================================================================
# 3. SIDE VIEW (SECTION) - แก้ไขตามสเก็ตช์ 100%
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    h_pl, t_pl = plate['h'], plate['t']
    lv, s_v, n_rows = plate.get('lv', 35), bolts['s_v'], bolts['rows']

    # วาดหน้าเสาสีเหลือง ประคองซ้าย-ขวา ตามรูปสเก็ตช์
    fig.add_shape(type="line", x0=-b/2, y0=-h/2-40, x1=-b/2, y1=h/2+40, line=dict(color=C_YELLOW_COL, width=3))
    fig.add_shape(type="line", x0=b/2, y0=-h/2-40, x1=b/2, y1=h/2+40, line=dict(color=C_YELLOW_COL, width=3))

    # I-Section คาน
    fig.add_shape(type="rect", x0=-b/2, y0=h/2-tf, x1=b/2, y1=h/2, fillcolor=C_STEEL_FILL, line=dict(color=C_STEEL_OUT))
    fig.add_shape(type="rect", x0=-b/2, y0=-h/2, x1=b/2, y1=-h/2+tf, fillcolor=C_STEEL_FILL, line=dict(color=C_STEEL_OUT))
    fig.add_shape(type="rect", x0=-tw/2, y0=-h/2+tf, x1=tw/2, y1=h/2-tf, fillcolor=C_STEEL_FILL, line=dict(color=C_STEEL_OUT))

    # Shear Plate
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, fillcolor=C_PLATE, line=dict(color=C_STEEL_OUT))
    
    # Bolts
    for i in range(n_rows):
        y_bolt = h_pl/2 - lv - (i * s_v)
        fig.add_shape(type="rect", x0=tw/2+t_pl, y0=y_bolt-4, x1=tw/2+t_pl+10, y1=y_bolt+4, fillcolor=C_BOLT, line_width=0)
    
    # บอกระยะตามสเก็ตช์ (b/2, -b/2, H)
    add_eng_dim(fig, -b/2, h/2, 0, h/2, "b/2", "h", 40)
    add_eng_dim(fig, 0, h/2, b/2, h/2, "-b/2", "h", 40)
    add_eng_dim(fig, b/2, h/2, b/2, -h/2, f"H={h}", "v", 40)

    fig.update_layout(title="SIDE SECTION", plot_bgcolor="white", height=450, margin=dict(l=10,r=10,t=50,b=10),
                      xaxis=dict(visible=False, range=[-b, b+50]), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1))
    return fig
