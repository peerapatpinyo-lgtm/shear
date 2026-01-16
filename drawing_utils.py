import plotly.graph_objects as go

# --- Professional Engineering Standards ---
C_STEEL_OUTLINE = "#212121"
C_STEEL_FILL = "#F5F5F5"
C_PLATE = "#1976D2"
C_BOLT = "#D32F2F"
C_DIM = "#455A64"

def draw_i_profile(fig, x_center, y_center, h, b, tf, tw, color=C_STEEL_FILL):
    """วาดหน้าตัดเหล็กรูปตัว I (I-Beam Section) แบบแม่นยำ"""
    path = (f"M {x_center-b/2},{y_center-h/2} L {x_center+b/2},{y_center-h/2} "
            f"L {x_center+b/2},{y_center-h/2+tf} L {x_center+tw/2},{y_center-h/2+tf} "
            f"L {x_center+tw/2},{y_center+h/2-tf} L {x_center+b/2},{y_center+h/2-tf} "
            f"L {x_center+b/2},{y_center+h/2} L {x_center-b/2},{y_center+h/2} "
            f"L {x_center-b/2},{y_center+h/2-tf} L {x_center-tw/2},{y_center+h/2-tf} "
            f"L {x_center-tw/2},{y_center-h/2+tf} L {x_center-b/2},{y_center-h/2+tf} Z")
    fig.add_shape(type="path", path=path, fillcolor=color, line=dict(color=C_STEEL_OUTLINE, width=2))

def add_eng_dim(fig, x0, y0, x1, y1, text, axis="H", offset=40):
    """เส้นบอกระยะมาตรฐานวิศวกรรม (Tick Marks)"""
    if axis == "H":
        y_d = y0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_d+5, line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_d+5, line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x0, y0=y_d, x1=x1, y1=y_d, line=dict(color=C_DIM, width=1.5))
        for x in [x0, x1]:
            fig.add_shape(type="line", x0=x-4, y0=y_d-4, x1=x+4, y1=y_d+4, line=dict(color=C_DIM, width=2))
        fig.add_annotation(x=(x0+x1)/2, y=y_d, text=f"<b>{text}</b>", showarrow=False, yshift=15, font=dict(size=12))
    else:
        x_d = x0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_d+5, y1=y0, line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_d+5, y1=y1, line=dict(color=C_DIM, width=1))
        fig.add_shape(type="line", x0=x_d, y0=y0, x1=x_d, y1=y1, line=dict(color=C_DIM, width=1.5))
        for y in [y0, y1]:
            fig.add_shape(type="line", x0=x_d-4, y0=y-4, x1=x_d+4, y1=y+4, line=dict(color=C_DIM, width=2))
        fig.add_annotation(x=x_d, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=25, textangle=-90, font=dict(size=12))

# 1. SIDE VIEW (SECTION): แก้ไขตามรูปสเก็ตช์สีแดง (เห็นหน้าตัดเสา)
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw, t_pl, h_pl = beam['h'], beam['b'], beam['tf'], beam['tw'], plate['t'], plate['h']
    
    # เสา (Column) - วาดหน้าตัด I-Shape ด้านซ้าย
    draw_i_profile(fig, x_center=-b/2-40, y_center=0, h=h+100, b=b, tf=tf+5, tw=tw+5, color="#CFD8DC")
    
    # คาน (Beam) - วาดหน้าตัด I-Shape ด้านขวา
    draw_i_profile(fig, x_center=b/2, y_center=0, h=h, b=b, tf=tf, tw=tw)
    
    # Shear Plate แปะข้างคาน
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, fillcolor=C_PLATE, line_width=0)
    
    add_eng_dim(fig, -b/2, h/2, b/2, h/2, f"B={b}", "H", 60)
    add_eng_dim(fig, -b/2, h/2, -b/2, -h/2, f"H={h}", "V", -60)
    
    fig.update_layout(plot_bgcolor="white", xaxis=dict(visible=False, range=[-b*1.5, b*2]), 
                      yaxis=dict(visible=False, scaleanchor="x"), margin=dict(l=10,r=10,t=10,b=10))
    return fig

# 2. ELEVATION VIEW (FRONT): วาดตามรูป image_f51884.png
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_pl, w_pl, s_v, rows, e1 = plate['h'], plate['w'], bolts['s_v'], bolts['rows'], plate['e1']
    
    # หน้าปีกเสา (Background)
    fig.add_shape(type="rect", x0=-60, y0=-h_pl/2-50, x1=0, y1=h_pl/2+50, fillcolor="#CFD8DC", line_width=0)
    # Plate
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor="rgba(25,118,210,0.1)", line=dict(color=C_PLATE, width=2))
    
    # วาดโบลท์และระยะ Pitch
    start_y = h_pl/2 - 40 # ระยะขอบบนตามแบบ
    for i in range(rows):
        by = start_y - (i * s_v)
        fig.add_shape(type="circle", x0=e1-10, y0=by-10, x1=e1+10, y1=by+10, fillcolor=C_BOLT, line_width=0)
        if i < rows - 1: # บอกระยะ Pitch ระหว่างตัว
            add_eng_dim(fig, w_pl, by, w_pl, by-s_v, f"{int(s_v)}", "V", 30)

    add_eng_dim(fig, w_pl+40, h_pl/2, w_pl+40, -h_pl/2, f"H_PL={h_pl}", "V", 40)
    fig.update_layout(plot_bgcolor="white", xaxis=dict(visible=False, range=[-100, w_pl+150]), 
                      yaxis=dict(visible=False, scaleanchor="x"), margin=dict(l=10,r=10,t=10,b=10))
    return fig

# 3. PLAN VIEW: มองจากด้านบน
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, bf, w_pl, t_pl = beam['tw'], beam['b'], plate['w'], plate['t']
    
    # ปีกเสา
    fig.add_shape(type="rect", x0=-20, y0=-bf/2, x1=0, y1=bf/2, fillcolor="#CFD8DC", line=dict(color=C_STEEL_OUTLINE))
    # คาน Web
    fig.add_shape(type="rect", x0=0, y0=-tw/2, x1=w_pl+100, y1=tw/2, fillcolor=C_STEEL_FILL, line=dict(color=C_STEEL_OUTLINE))
    # Plate และรอยเชื่อม
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=tw/2+t_pl, fillcolor=C_PLATE, line_width=0)
    fig.add_shape(type="path", path=f"M 0,{tw/2} L -5,{tw/2+5} L 0,{tw/2+t_pl} Z", fillcolor="black") # Weld symbol
    
    add_eng_dim(fig, 0, -bf/2, w_pl, -bf/2, f"W_PL={w_pl}", "H", -40)
    fig.update_layout(plot_bgcolor="white", xaxis=dict(visible=False, range=[-80, w_pl+150]), 
                      yaxis=dict(visible=False, scaleanchor="x"), margin=dict(l=10,r=10,t=10,b=10))
    return fig
