import plotly.graph_objects as go

# --- Professional Engineering Theme ---
C_COL_FILL = "#37474F"   # สีเสา (Steel Anthracite)
C_BEAM_FILL = "#ECEFF1"  # สีคาน
C_PLATE = "#1976D2"      # สี Plate
C_BOLT = "#D32F2F"       # สี Bolt
C_DIM = "#263238"        # สีเส้นมิติ

def add_pro_dim(fig, x0, y0, x1, y1, text, axis="H", offset=40):
    """เส้นบอกขนาดที่คมชัดและเว้นระยะพอดีกับชิ้นงาน"""
    y_d = y0 + offset if axis == "H" else y0
    x_d = x0 + offset if axis == "V" else x0
    
    # Tick marks & Dimension line
    fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_d+(5 if offset>0 else -5), line=dict(color=C_DIM, width=1))
    fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_d+(5 if offset>0 else -5), line=dict(color=C_DIM, width=1))
    
    if axis == "H":
        fig.add_shape(type="line", x0=x0, y0=y_d, x1=x1, y1=y_d, line=dict(color=C_DIM, width=1.5))
        for x in [x0, x1]:
            fig.add_shape(type="line", x0=x-3, y0=y_d-3, x1=x+3, y1=y_d+3, line=dict(color=C_DIM, width=2))
        fig.add_annotation(x=(x0+x1)/2, y=y_d, text=f"<b>{text}</b>", showarrow=False, yshift=12, font=dict(size=14))
    else:
        fig.add_shape(type="line", x0=x_d, y0=y0, x1=x_d, y1=y1, line=dict(color=C_DIM, width=1.5))
        for y in [y0, y1]:
            fig.add_shape(type="line", x0=x_d-3, y0=y-3, x1=x_d+3, y1=y+3, line=dict(color=C_DIM, width=2))
        fig.add_annotation(x=x_d, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=20, textangle=-90, font=dict(size=14))

# 1. PLAN VIEW: แก้ไขความกว้างเสา (ตรงตามเส้นสีแดงที่คุณวง)
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, bf, w_pl, t_pl = beam['tw'], beam['b'], plate['w'], plate['t']
    col_width = 250 # ความกว้างเสาที่สมจริง

    # วาดเสา (Column Section) - แสดงปีกและเอวเสา
    fig.add_shape(type="rect", x0=-col_width, y0=-bf/2, x1=0, y1=bf/2, fillcolor=C_COL_FILL, line_width=1)
    
    # วาดคาน (Beam)
    fig.add_shape(type="rect", x0=0, y0=-tw/2, x1=w_pl+100, y1=tw/2, fillcolor=C_BEAM_FILL, line=dict(color=C_DIM, width=2))
    
    # วาด Plate
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=tw/2+t_pl, fillcolor=C_PLATE, line_width=0)

    add_pro_dim(fig, 0, -bf/2, w_pl, -bf/2, f"W_PL={w_pl}", "H", -50)
    
    # ปรับ Zoom ให้เห็นงานใหญ่ขึ้น
    fig.update_layout(xaxis=dict(visible=False, range=[-col_width-20, w_pl+120]), 
                      yaxis=dict(visible=False, range=[-bf/2-80, bf/2+80], scaleanchor="x"),
                      plot_bgcolor="white", margin=dict(l=0,r=0,t=0,b=0))
    return fig

# 2. ELEVATION VIEW: เน้นการจัดวาง Bolt ที่ได้สเกล
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_pl, w_pl, s_v, rows, e1 = plate['h'], plate['w'], bolts['s_v'], bolts['rows'], plate['e1']
    edge_v = (h_pl - (rows - 1) * s_v) / 2 

    # พื้นหลังเสา
    fig.add_shape(type="rect", x0=-80, y0=-h_pl/2-50, x1=0, y1=h_pl/2+50, fillcolor=C_COL_FILL, line_width=0)
    # Plate
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor="rgba(25,118,210,0.1)", line=dict(color=C_PLATE, width=2.5))

    for r in range(rows):
        by = (h_pl/2 - edge_v) - r*s_v
        fig.add_shape(type="circle", x0=e1-10, y0=by-10, x1=e1+10, y1=by+10, fillcolor=C_BOLT, line_width=0)

    add_pro_dim(fig, w_pl, h_pl/2, w_pl, -h_pl/2, f"H_PL={h_pl}", "V", 50)
    fig.update_layout(xaxis=dict(visible=False, range=[-100, w_pl+100]), 
                      yaxis=dict(visible=False, range=[-h_pl/2-80, h_pl/2+80], scaleanchor="x"),
                      plot_bgcolor="white", margin=dict(l=0,r=0,t=0,b=0))
    return fig

# 3. SECTION VIEW: แก้ไขเสาให้มีความกว้างตามเส้นแดง
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw, t_pl, h_pl = beam['h'], beam['b'], beam['tf'], beam['tw'], plate['t'], plate['h']
    col_depth = 300 # ความกว้างเสาในมุมมองด้านข้าง

    # วาดเสาที่มีความกว้าง (ตรงตามเส้นสีแดงที่คุณต้องการ)
    fig.add_shape(type="rect", x0=-col_depth, y0=-h/2-50, x1=-b/2-10, y1=h/2+50, fillcolor=C_COL_FILL, line_width=1)

    # วาด I-Beam
    p = f"M {-b/2},{-h/2} L {b/2},{-h/2} L {b/2},{-h/2+tf} L {tw/2},{-h/2+tf} L {tw/2},{h/2-tf} L {b/2},{h/2-tf} L {b/2},{h/2} L {-b/2},{h/2} L {-b/2},{h/2-tf} L {-tw/2},{h/2-tf} L {-tw/2},{-h/2+tf} L {-b/2},{-h/2+tf} Z"
    fig.add_shape(type="path", path=p, fillcolor=C_BEAM_FILL, line=dict(color=C_DIM, width=2))
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, fillcolor=C_PLATE, line_width=0)

    add_pro_dim(fig, -b/2, h/2, b/2, h/2, f"B={b}", "H", 60)
    add_pro_dim(fig, -b/2, h/2, -b/2, -h/2, f"H={h}", "V", -80)

    fig.update_layout(xaxis=dict(visible=False, range=[-col_depth-50, b/2+80]), 
                      yaxis=dict(visible=False, range=[-h/2-120, h/2+120], scaleanchor="x"),
                      plot_bgcolor="white", margin=dict(l=0,r=0,t=0,b=0))
    return fig
