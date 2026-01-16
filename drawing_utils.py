import plotly.graph_objects as go

# --- ใช้ Palette สีเดิมที่คุณกำหนดไว้ (ดีอยู่แล้ว) ---
C_COL_FILL = "#475569"   
C_BEAM_FILL = "#f1f5f9"  
C_BEAM_OUT = "#334155"   
C_PLATE_FILL = "#0ea5e9" 
C_BOLT_FILL = "#dc2626"  
C_DIM = "black"          
C_CL = "#ef4444"         

# --- ฟังก์ชันช่วยเหลือ (คงไว้ตามต้นฉบับของคุณเพื่อความเป๊ะ) ---
def add_cad_dim(fig, x0, y0, x1, y1, text, type="horiz", offset=0):
    arrow_head_style = 2
    arrow_scale = 1.0
    arrow_width = 0.8
    if type == "horiz":
        y_dim = y0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_dim, line=dict(color=C_DIM, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_dim, line=dict(color=C_DIM, width=0.5))
        fig.add_shape(type="line", x0=x0, y0=y_dim, x1=x1, y1=y_dim, line=dict(color=C_DIM, width=1))
        fig.add_annotation(x=x0, y=y_dim, ax=5, ay=0, arrowhead=arrow_head_style, arrowsize=arrow_scale, arrowwidth=arrow_width, arrowcolor=C_DIM, text="")
        fig.add_annotation(x=x1, y=y_dim, ax=-5, ay=0, arrowhead=arrow_head_style, arrowsize=arrow_scale, arrowwidth=arrow_width, arrowcolor=C_DIM, text="")
        fig.add_annotation(x=(x0+x1)/2, y=y_dim, text=f"<b>{text}</b>", showarrow=False, yshift=8 if offset>0 else -8, font=dict(size=11, color=C_DIM), bgcolor="white")
    elif type == "vert":
        x_dim = x0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_dim, y1=y0, line=dict(color=C_DIM, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_dim, y1=y1, line=dict(color=C_DIM, width=0.5))
        fig.add_shape(type="line", x0=x_dim, y0=y0, x1=x_dim, y1=y1, line=dict(color=C_DIM, width=1))
        fig.add_annotation(x=x_dim, y=y0, ax=0, ay=-5, arrowhead=arrow_head_style, arrowsize=arrow_scale, arrowwidth=arrow_width, arrowcolor=C_DIM, text="")
        fig.add_annotation(x=x_dim, y=y1, ax=0, ay=5, arrowhead=arrow_head_style, arrowsize=arrow_scale, arrowwidth=arrow_width, arrowcolor=C_DIM, text="")
        fig.add_annotation(x=x_dim, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=12 if offset>0 else -12, font=dict(size=11, color=C_DIM), textangle=-90, bgcolor="white")

def add_leader(fig, x, y, text, ax=30, ay=-30, color="black"):
    fig.add_annotation(x=x, y=y, text=text, showarrow=True, arrowhead=2, arrowsize=1.0, arrowwidth=1, arrowcolor=color, ax=ax, ay=ay, font=dict(size=11, color=color), bgcolor="#f8f9fa", bordercolor=color)

def add_centerline(fig, x0, y0, x1, y1):
    fig.add_shape(type="line", x0=x0, y0=y0, x1=x1, y1=y1, line=dict(color=C_CL, width=1, dash="dashdot"), opacity=0.7)

# --- แก้ไขเฉพาะ SIDE VIEW (SECTION) ให้มืออาชีพขึ้น ---
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    t_pl, h_pl, lv = plate['t'], plate['h'], plate['lv']
    d_bolt, n_rows, s_v = bolts['d'], bolts['rows'], bolts['s_v']

    # 1. วาดหน้าตัดเสา (Column I-Section) ขวางอยู่ทางซ้าย ตามสเก็ตช์ที่คุณต้องการ
    col_x_offset = -b/2 - 40
    # ปีกเสา บน-ล่าง
    fig.add_shape(type="rect", x0=col_x_offset-b/2, y0=h/2+20, x1=col_x_offset+b/2, y1=h/2+20+tf, line=dict(color=C_BEAM_OUT, width=1.5), fillcolor=C_COL_FILL)
    fig.add_shape(type="rect", x0=col_x_offset-b/2, y0=-h/2-20-tf, x1=col_x_offset+b/2, y1=-h/2-20, line=dict(color=C_BEAM_OUT, width=1.5), fillcolor=C_COL_FILL)
    # เอวเสา
    fig.add_shape(type="rect", x0=col_x_offset-tw/2, y0=-h/2-20, x1=col_x_offset+tw/2, y1=h/2+20, line=dict(color=C_BEAM_OUT, width=1.5), fillcolor=C_COL_FILL)

    # 2. วาดหน้าตัดคาน (Beam I-Section)
    fig.add_shape(type="rect", x0=-b/2, y0=h/2-tf, x1=b/2, y1=h/2, line=dict(color=C_BEAM_OUT, width=1.5), fillcolor=C_BEAM_FILL)
    fig.add_shape(type="rect", x0=-b/2, y0=-h/2, x1=b/2, y1=-h/2+tf, line=dict(color=C_BEAM_OUT, width=1.5), fillcolor=C_BEAM_FILL)
    fig.add_shape(type="rect", x0=-tw/2, y0=-h/2+tf, x1=tw/2, y1=h/2-tf, line=dict(color=C_BEAM_OUT, width=1.5), fillcolor=C_BEAM_FILL)

    # 3. วาด Shear Plate และ Bolt
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, line=dict(color=C_BEAM_OUT, width=1), fillcolor=C_PLATE_FILL)
    
    by_start = h_pl/2 - lv
    for r in range(n_rows):
        by = by_start - r*s_v
        fig.add_shape(type="rect", x0=tw/2+t_pl, y0=by-d_bolt/2, x1=tw/2+t_pl+10, y1=by+d_bolt/2, fillcolor=C_BOLT_FILL, line_width=0.5)

    # 4. Dimensions (ใช้ฟังก์ชันมาตรฐานของคุณ)
    add_cad_dim(fig, -b/2, h/2, b/2, h/2, f"B={b:.0f}", offset=30)
    add_cad_dim(fig, -b/2-20, h/2, -b/2-20, -h/2, f"H={h:.0f}", "vert")
    add_leader(fig, tw/2+t_pl/2, h_pl/2, f"PL t={t_pl}", ax=40, ay=-40, color=C_PLATE_FILL)

    fig.update_layout(title="<b>SIDE VIEW (SECTION)</b>", plot_bgcolor="white", margin=dict(l=10,r=10,t=40,b=10),
                      xaxis=dict(visible=False, range=[col_x_offset-b, b+50], fixedrange=True),
                      yaxis=dict(visible=False, range=[-h-50, h+50], scaleanchor="x", scaleratio=1, fixedrange=True))
    return fig
