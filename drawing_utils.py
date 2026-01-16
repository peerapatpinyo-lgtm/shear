import plotly.graph_objects as go

# =============================================================================
# 🎨 STYLE CONFIG
# =============================================================================
C_YELLOW_COL = "#eab308"   # เส้นขอบเสา (ความกว้างเสา)
C_STEEL_OUT = "#0f172a"    
C_STEEL_FILL = "#f8fafc"   
C_PLATE = "#0ea5e9"        
C_BOLT = "#be123c"         
C_DIM = "#475569"          

# =============================================================================
# 📏 DIMENSION SYSTEM
# =============================================================================
def add_eng_dim(fig, x0, y0, x1, y1, text, mode="h", offset=30):
    loc = (y0 + offset) if mode == "h" else (x0 + offset)
    if mode == "h":
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=loc+5, line=dict(color=C_DIM, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=loc+5, line=dict(color=C_DIM, width=0.5))
        fig.add_shape(type="line", x0=x0, y0=loc, x1=x1, y1=loc, line=dict(color=C_DIM, width=1))
        for x in [x0, x1]:
            fig.add_shape(type="line", x0=x-3, y0=loc-3, x1=x+3, y1=loc+3, line=dict(color=C_DIM, width=1.5))
        fig.add_annotation(x=(x0+x1)/2, y=loc, text=text, showarrow=False, yshift=12, font=dict(size=11, family="Arial Black"))
    else:
        fig.add_shape(type="line", x0=x0, y0=y0, x1=loc+5, y1=y0, line=dict(color=C_DIM, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=loc+5, y1=y1, line=dict(color=C_DIM, width=0.5))
        fig.add_shape(type="line", x0=loc, y0=y0, x1=loc, y1=y1, line=dict(color=C_DIM, width=1))
        for y in [y0, y1]:
            fig.add_shape(type="line", x0=loc-3, y0=y-3, x1=loc+3, y1=y+3, line=dict(color=C_DIM, width=1.5))
        fig.add_annotation(x=loc, y=(y0+y1)/2, text=text, showarrow=False, xshift=18, textangle=-90, font=dict(size=11, family="Arial Black"))

# =============================================================================
# 1. PLAN VIEW
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, b, w_pl, t_pl = beam['tw'], beam['b'], plate['w'], plate['t']
    # วาดเส้นหน้าเสาสองฝั่ง (Plan View)
    fig.add_shape(type="line", x0=0, y0=-b/2-10, x1=0, y1=b/2+10, line=dict(color=C_YELLOW_COL, width=4))
    fig.add_shape(type="rect", x0=0, y0=-tw/2, x1=w_pl+30, y1=tw/2, fillcolor=C_STEEL_FILL, line=dict(color=C_STEEL_OUT))
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=tw/2+t_pl, fillcolor=C_PLATE, line=dict(color=C_STEEL_OUT))
    add_eng_dim(fig, 0, tw/2+t_pl, w_pl, tw/2+t_pl, f"Wp={w_pl}", "h", 25)
    fig.update_layout(title="<b>PLAN VIEW</b>", plot_bgcolor="white", height=300, 
                      xaxis=dict(visible=False, range=[-20, w_pl+50]), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1))
    return fig

# =============================================================================
# 2. ELEVATION VIEW
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_b, h_pl, w_pl = beam['h'], plate['h'], plate['w']
    lv, s_v, n_rows = plate.get('lv', 40), bolts['s_v'], bolts['rows']
    fig.add_shape(type="line", x0=0, y0=-h_b/2-20, x1=0, y1=h_b/2+20, line=dict(color=C_YELLOW_COL, width=4))
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor=C_PLATE, line=dict(color=C_STEEL_OUT))
    bolt_x = w_pl / 2
    for i in range(n_rows):
        y_bolt = h_pl/2 - lv - (i * s_v)
        fig.add_shape(type="circle", x0=bolt_x-5, y0=y_bolt-5, x1=bolt_x+5, y1=y_bolt+5, fillcolor=C_BOLT)
    add_eng_dim(fig, w_pl, h_pl/2, w_pl, -h_pl/2, f"Hp={h_pl}", "v", 30)
    fig.update_layout(title="<b>ELEVATION VIEW</b>", plot_bgcolor="white", height=350,
                      xaxis=dict(visible=False, range=[-20, w_pl+50]), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1))
    return fig

# =============================================================================
# 3. SIDE VIEW (SECTION) - อัปเดตเส้นเสาสองฝั่ง
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    h_pl, t_pl = plate['h'], plate['t']
    lv, s_v, n_rows = plate.get('lv', 40), bolts['s_v'], bolts['rows']

    # 1. เส้นขอบเสาด้านซ้ายและขวา (Column Width)
    fig.add_shape(type="line", x0=-b/2-10, y0=-h/2-40, x1=-b/2-10, y1=h/2+40, line=dict(color=C_YELLOW_COL, width=3)) # Left
    fig.add_shape(type="line", x0=b/2+10, y0=-h/2-40, x1=b/2+10, y1=h/2+40, line=dict(color=C_YELLOW_COL, width=3))  # Right

    # 2. I-Beam (วาดให้อยู่กึ่งกลาง และ Flush กับหน้าแปลนเสา)
    fig.add_shape(type="rect", x0=-b/2, y0=h/2-tf, x1=b/2, y1=h/2, fillcolor=C_STEEL_FILL, line=dict(color=C_STEEL_OUT)) # Top Flange
    fig.add_shape(type="rect", x0=-b/2, y0=-h/2, x1=b/2, y1=-h/2+tf, fillcolor=C_STEEL_FILL, line=dict(color=C_STEEL_OUT)) # Bot Flange
    fig.add_shape(type="rect", x0=-tw/2, y0=-h/2+tf, x1=tw/2, y1=h/2-tf, fillcolor=C_STEEL_FILL, line=dict(color=C_STEEL_OUT)) # Web

    # 3. Shear Plate
    p_x1 = tw/2 + t_pl
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=p_x1, y1=h_pl/2, fillcolor=C_PLATE, line=dict(color=C_STEEL_OUT))
    for i in range(n_rows):
        y_bolt = h_pl/2 - lv - (i * s_v)
        fig.add_shape(type="rect", x0=p_x1, y0=y_bolt-4, x1=p_x1+10, y1=y_bolt+4, fillcolor=C_BOLT, line_width=0)
    
    # 4. Dimensions บอกระยะสมมาตร
    add_eng_dim(fig, -b/2, h/2, 0, h/2, "b/2", "h", 50)
    add_eng_dim(fig, 0, h/2, b/2, h/2, "b/2", "h", 50)
    add_eng_dim(fig, b/2, h/2, b/2, -h/2, f"H={h}", "v", 40)

    fig.update_layout(title="<b>SIDE VIEW (SECTION)</b>", plot_bgcolor="white", height=500,
                      xaxis=dict(visible=False, range=[-b-20, b+40]), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1))
    return fig
