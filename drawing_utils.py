import plotly.graph_objects as go

# --- Global Engineering Styles ---
C_STEEL_OUTLINE = "#1A1A1A"
C_STEEL_FILL = "#F0F0F0" # สีเหล็กใหม่
C_PLATE = "#1976D2"
C_BOLT = "#D32F2F"
C_DIM = "#37474F"

def add_pro_dim(fig, x0, y0, x1, y1, text, axis="H", offset=40):
    """เส้นบอกระยะแบบ Engineering พร้อม Tick Marks"""
    y_p = y0 + offset if axis == "H" else y0
    x_p = x0 + offset if axis == "V" else x0
    # Extension lines
    fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_p+(5 if offset>0 else -5), line=dict(color=C_DIM, width=1))
    fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_p+(5 if offset>0 else -5), line=dict(color=C_DIM, width=1))
    # Dim line
    if axis == "H":
        fig.add_shape(type="line", x0=x0, y0=y_p, x1=x1, y1=y_p, line=dict(color=C_DIM, width=1.2))
        for x in [x0, x1]: fig.add_shape(type="line", x0=x-4, y0=y_p-4, x1=x+4, y1=y_p+4, line=dict(color=C_DIM, width=2))
        fig.add_annotation(x=(x0+x1)/2, y=y_p, text=f"<b>{text}</b>", showarrow=False, yshift=15, font=dict(size=12))
    else:
        fig.add_shape(type="line", x0=x_p, y0=y0, x1=x_p, y1=y1, line=dict(color=C_DIM, width=1.2))
        for y in [y0, y1]: fig.add_shape(type="line", x0=x_p-4, y0=y-4, x1=x_p+4, y1=y+4, line=dict(color=C_DIM, width=2))
        fig.add_annotation(x=x_p, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=25, textangle=-90, font=dict(size=12))

# 1. SIDE VIEW (SECTION) - มองเห็นหน้าตัดเสาและคาน
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw, t_pl, h_pl = beam['h'], beam['b'], beam['tf'], beam['tw'], plate['t'], plate['h']
    
    # วาดหน้าตัดเสา (Column Section - H Shape)
    col_x = -b/2 - 50
    path_col = (f"M {col_x-b/2},{-h/2-50} L {col_x+b/2},{-h/2-50} L {col_x+b/2},{-h/2-50+tf} L {col_x+tw/2},{-h/2-50+tf} "
                f"L {col_x+tw/2},{h/2+50-tf} L {col_x+b/2},{h/2+50-tf} L {col_x+b/2},{h/2+50} L {col_x-b/2},{h/2+50} Z")
    fig.add_shape(type="path", path=path_col, fillcolor="#E0E0E0", line=dict(color=C_STEEL_OUTLINE, width=2))

    # วาดหน้าตัดคาน (Beam Section - I Shape)
    path_beam = (f"M {-b/2},{-h/2} L {b/2},{-h/2} L {b/2},{-h/2+tf} L {tw/2},{-h/2+tf} "
                 f"L {tw/2},{h/2-tf} L {b/2},{h/2-tf} L {b/2},{h/2} L {-b/2},{h/2} Z")
    fig.add_shape(type="path", path=path_beam, fillcolor=C_STEEL_FILL, line=dict(color=C_STEEL_OUTLINE, width=2))

    # วาด Shear Plate
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, fillcolor=C_PLATE, line_width=0)

    add_pro_dim(fig, -b/2, h/2, b/2, h/2, f"B={b}", "H", 50)
    add_pro_dim(fig, -b/2, h/2, -b/2, -h/2, f"H={h}", "V", -70)
    
    fig.update_layout(xaxis=dict(visible=False, range=[-b*2, b*1.5]), yaxis=dict(visible=False, scaleanchor="x"), 
                      plot_bgcolor="white", margin=dict(l=10,r=10,t=40,b=10), title="SIDE VIEW (SECTION)")
    return fig

# 2. ELEVATION VIEW (FRONT) - รายละเอียด Bolt และระยะ Pitch
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_pl, w_pl, s_v, rows, e1 = plate['h'], plate['w'], bolts['s_v'], bolts['rows'], plate['e1']
    
    # หน้าปีกเสา (Flange)
    fig.add_shape(type="rect", x0=-80, y0=-h_pl/2-60, x1=0, y1=h_pl/2+60, fillcolor="#E0E0E0", line_width=0)
    # Plate
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor="rgba(25,118,210,0.08)", line=dict(color=C_PLATE, width=2))
    
    start_y = h_pl/2 - 40 # Edge distance 40mm
    for i in range(rows):
        by = start_y - (i * s_v)
        fig.add_shape(type="circle", x0=e1-10, y0=by-10, x1=e1+10, y1=by+10, fillcolor=C_BOLT, line_width=0)
        if i < rows - 1:
            add_pro_dim(fig, w_pl, by, w_pl, by-s_v, f"{int(s_v)}", "V", 30)

    add_pro_dim(fig, w_pl+40, h_pl/2, w_pl+40, -h_pl/2, f"H_PL={h_pl}", "V", 40)
    fig.update_layout(xaxis=dict(visible=False, range=[-120, w_pl+150]), yaxis=dict(visible=False, scaleanchor="x"), 
                      plot_bgcolor="white", margin=dict(l=10,r=10,t=40,b=10), title="ELEVATION VIEW (FRONT)")
    return fig

# 3. PLAN VIEW - รอยเชื่อมและทิศทางจากด้านบน
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, bf, w_pl, t_pl = beam['tw'], beam['b'], plate['w'], plate['t']
    
    # ปีกเสา (Top View)
    fig.add_shape(type="rect", x0=-20, y0=-bf/2, x1=0, y1=bf/2, fillcolor="#E0E0E0", line=dict(color=C_STEEL_OUTLINE))
    # คาน Web และ Plate
    fig.add_shape(type="rect", x0=0, y0=-tw/2, x1=w_pl+100, y1=tw/2, fillcolor=C_STEEL_FILL, line=dict(color=C_STEEL_OUTLINE))
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=tw/2+t_pl, fillcolor=C_PLATE, line_width=0)
    # รอยเชื่อม (Welding Symbol)
    fig.add_shape(type="path", path=f"M 0,{tw/2} L -6,{tw/2+6} L 0,{tw/2+t_pl} Z", fillcolor="black")

    add_pro_dim(fig, 0, -bf/2, w_pl, -bf/2, f"W_PL={w_pl}", "H", -50)
    fig.update_layout(xaxis=dict(visible=False, range=[-80, w_pl+150]), yaxis=dict(visible=False, scaleanchor="x"), 
                      plot_bgcolor="white", margin=dict(l=10,r=10,t=40,b=10), title="PLAN VIEW")
    return fig
