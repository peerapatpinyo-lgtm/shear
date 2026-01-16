import plotly.graph_objects as go

# --- Theme Configuration ---
C_STEEL = "#263238"   # สีขอบเหล็ก
C_FILL = "#ECEFF1"    # สีเนื้อเหล็ก
C_PLATE = "#1976D2"   # สี Plate
C_BOLT = "#D32F2F"    # สี Bolt

def draw_i_section(fig, xc, yc, h, b, tf, tw, color=C_FILL, horizontal=False):
    """ฟังก์ชันวาดหน้าตัดเหล็กรูปตัว I (I-Beam/Column Section)"""
    if not horizontal:
        p = f"M {xc-b/2},{yc-h/2} L {xc+b/2},{yc-h/2} L {xc+b/2},{yc-h/2+tf} L {xc+tw/2},{yc-h/2+tf} L {xc+tw/2},{yc+h/2-tf} L {xc+b/2},{yc+h/2-tf} L {xc+b/2},{yc+h/2} L {xc-b/2},{yc+h/2} L {xc-b/2},{yc+h/2-tf} L {xc-tw/2},{yc+h/2-tf} L {xc-tw/2},{yc-h/2+tf} L {xc-b/2},{yc-h/2+tf} Z"
    else: # สำหรับวาดแนวนอน
        p = f"M {xc-h/2},{yc-b/2} L {xc-h/2+tf},{yc-b/2} L {xc-h/2+tf},{yc-tw/2} L {xc+h/2-tf},{yc-tw/2} L {xc+h/2-tf},{yc-b/2} L {xc+h/2},{yc-b/2} L {xc+h/2},{yc+b/2} L {xc+h/2-tf},{yc+b/2} L {xc+h/2-tf},{yc+tw/2} L {xc-h/2+tf},{yc+tw/2} L {xc-h/2+tf},{yc+b/2} L {xc-h/2},{yc+b/2} Z"
    fig.add_shape(type="path", path=p, fillcolor=color, line=dict(color=C_STEEL, width=2))

# 1. SIDE VIEW (SECTION): มองด้านข้าง เห็นหน้าตัดทั้งเสาและคาน
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw, t_pl, h_pl = beam['h'], beam['b'], beam['tf'], beam['tw'], plate['t'], plate['h']
    
    # วาดหน้าตัดเสา (Column Section) ตามรูปที่คุณร่างสีแดงมา
    # สมมติเสาขนาดเท่าคานเพื่อให้เห็นภาพสัดส่วน
    draw_i_section(fig, xc=-b/2-25, yc=0, h=h+100, b=b, tf=tf+2, tw=tw+2, color="#CFD8DC")
    
    # วาดหน้าตัดคาน (Beam Section)
    draw_i_section(fig, xc=b/2, yc=0, h=h, b=b, tf=tf, tw=tw)
    
    # วาด Plate แปะข้าง Web คาน
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, fillcolor=C_PLATE, line_width=0)
    
    fig.update_layout(xaxis=dict(visible=False, range=[-b-100, b+100]), 
                      yaxis=dict(visible=False, range=[-h/2-100, h/2+100], scaleanchor="x"),
                      plot_bgcolor="white", margin=dict(l=0,r=0,t=40,b=0), title="SIDE VIEW (SECTION)")
    return fig

# 2. PLAN VIEW: มองจากด้านบน
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, bf, w_pl, t_pl, h_b = beam['tw'], beam['b'], plate['w'], plate['t'], beam['h']
    
    # เสา (มองบน เห็นปีกเสาและเอวเสา)
    fig.add_shape(type="rect", x0=-25, y0=-bf/2, x1=0, y1=bf/2, fillcolor="#CFD8DC", line=dict(color=C_STEEL)) # ปีกเสา
    fig.add_shape(type="rect", x0=-25-tw-10, y0=-tw/2, x1=-25, y1=tw/2, fillcolor="#CFD8DC", line=dict(color=C_STEEL)) # เอวเสา
    
    # คาน (มองบน)
    fig.add_shape(type="rect", x0=0, y0=-tw/2, x1=w_pl+100, y1=tw/2, fillcolor=C_FILL, line=dict(color=C_STEEL, width=2))
    # Plate
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=tw/2+t_pl, fillcolor=C_PLATE, line_width=0)
    
    fig.update_layout(xaxis=dict(visible=False, range=[-100, w_pl+150]), 
                      yaxis=dict(visible=False, range=[-bf/2-50, bf/2+50], scaleanchor="x"),
                      plot_bgcolor="white", margin=dict(l=0,r=0,t=40,b=0), title="PLAN VIEW")
    return fig

# 3. ELEVATION VIEW: มองจากด้านหน้า
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_pl, w_pl, s_v, rows, e1 = plate['h'], plate['w'], bolts['s_v'], bolts['rows'], plate['e1']
    edge_v = (h_pl - (rows - 1) * s_v) / 2 

    # พื้นหลังคือหน้าปีกเสา (Column Flange)
    fig.add_shape(type="rect", x0=-100, y0=-h_pl/2-100, x1=0, y1=h_pl/2+100, fillcolor="#CFD8DC", line_width=0)
    # Plate
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor="rgba(25,118,210,0.1)", line=dict(color=C_PLATE, width=2))

    for r in range(rows):
        by = (h_pl/2 - edge_v) - r*s_v
        fig.add_shape(type="circle", x0=e1-10, y0=by-10, x1=e1+10, y1=by+10, fillcolor=C_BOLT, line_width=0)

    fig.update_layout(xaxis=dict(visible=False, range=[-150, w_pl+100]), 
                      yaxis=dict(visible=False, range=[-h_pl/2-120, h_pl/2+120], scaleanchor="x"),
                      plot_bgcolor="white", margin=dict(l=0,r=0,t=40,b=0), title="ELEVATION VIEW (FRONT)")
    return fig
