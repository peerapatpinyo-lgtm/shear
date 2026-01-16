import plotly.graph_objects as go

# =============================================================================
# 🎨 ENGINEERING COLOR PALETTE
# =============================================================================
C_COL_LINE = "#eab308"    # เส้นหน้าเสา (สีเหลือง)
C_STEEL_OUT = "#0f172a"   # ขอบเหล็ก
C_STEEL_FILL = "#f8fafc"  # เนื้อเหล็ก
C_PLATE = "#38bdf8"       # Shear Plate
C_BOLT = "#e11d48"        # Bolt
C_DIM = "#475569"         # เส้นบอกระยะ

# =============================================================================
# 📏 DIMENSION SYSTEM (Engineering Standard)
# =============================================================================
def add_eng_dim(fig, x0, y0, x1, y1, text, mode="h", offset=35):
    """ วาดเส้นบอกระยะแบบวิศวกรรม (Engineering Ticks) """
    loc = (y0 + offset) if mode == "h" else (x0 + offset)
    
    if mode == "h":
        # Extension lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=loc+(5 if offset>0 else -5), line=dict(color=C_DIM, width=0.6))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=loc+(5 if offset>0 else -5), line=dict(color=C_DIM, width=0.6))
        # Dimension line
        fig.add_shape(type="line", x0=x0, y0=loc, x1=x1, y1=loc, line=dict(color=C_DIM, width=1))
        # Ticks
        for x in [x0, x1]:
            fig.add_shape(type="line", x0=x-3, y0=loc-3, x1=x+3, y1=loc+3, line=dict(color=C_DIM, width=1.5))
        # Text
        fig.add_annotation(x=(x0+x1)/2, y=loc, text=text, showarrow=False, yshift=12 if offset>0 else -12, font=dict(size=11, family="Arial Black"))
    else:
        # Extension lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=loc+(5 if offset>0 else -5), y1=y0, line=dict(color=C_DIM, width=0.6))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=loc+(5 if offset>0 else -5), y1=y1, line=dict(color=C_DIM, width=0.6))
        # Dimension line
        fig.add_shape(type="line", x0=loc, y0=y0, x1=loc, y1=y1, line=dict(color=C_DIM, width=1))
        # Ticks
        for y in [y0, y1]:
            fig.add_shape(type="line", x0=loc-3, y0=y-3, x1=loc+3, y1=y+3, line=dict(color=C_DIM, width=1.5))
        # Text
        fig.add_annotation(x=loc, y=(y0+y1)/2, text=text, showarrow=False, xshift=18 if offset>0 else -18, textangle=-90, font=dict(size=11, family="Arial Black"))

# =============================================================================
# 1. PLAN VIEW
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, b, w_pl, t_pl = beam['tw'], beam['b'], plate['w'], plate['t']
    
    # Face of Column (Yellow Reference)
    fig.add_shape(type="line", x0=0, y0=-b/2-20, x1=0, y1=b/2+20, line=dict(color=C_COL_LINE, width=4))
    # Beam & Plate (Flush to Column)
    fig.add_shape(type="rect", x0=0, y0=-tw/2, x1=w_pl+40, y1=tw/2, fillcolor=C_STEEL_FILL, line=dict(color=C_STEEL_OUT))
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=tw/2+t_pl, fillcolor=C_PLATE, line=dict(color=C_STEEL_OUT))
    
    add_eng_dim(fig, 0, tw/2+t_pl, w_pl, tw/2+t_pl, f"Wp={w_pl}", "h", 30)
    
    fig.update_layout(title="<b>PLAN VIEW</b>", plot_bgcolor="white", height=300, 
                      xaxis=dict(visible=False, range=[-30, w_pl+60]), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1))
    return fig

# =============================================================================
# 2. ELEVATION VIEW (Front) - แก้ไข Bolt ชิดขอบ
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_b, h_pl, w_pl = beam['h'], plate['h'], plate['w']
    # ป้องกัน Error 'lv' และจัด Bolt ให้อยู่กลาง Plate
    lv = plate.get('lv', bolts.get('lv', 40))
    s_v, n_rows = bolts['s_v'], bolts['rows']
    
    # Column Ref
    fig.add_shape(type="line", x0=0, y0=-h_b/2-20, x1=0, y1=h_b/2+20, line=dict(color=C_COL_LINE, width=4))
    # Plate
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor=C_PLATE, line=dict(color=C_STEEL_OUT))
    
    # Bolts: จัดให้อยู่กลางความกว้าง Plate เสมอ (e1 = w_pl/2)
    bolt_x = w_pl / 2
    for i in range(n_rows):
        y_bolt = h_pl/2 - lv - (i * s_v)
        fig.add_shape(type="circle", x0=bolt_x-6, y0=y_bolt-6, x1=bolt_x+6, y1=y_bolt+6, 
                      fillcolor=C_BOLT, line=dict(color="black", width=1))

    # Dimensions
    add_eng_dim(fig, w_pl, h_pl/2, w_pl, -h_pl/2, f"Hp={h_pl}", "v", 30)
    add_eng_dim(fig, 0, h_pl/2, bolt_x, h_pl/2, f"e={bolt_x}", "h", 25)
    
    fig.update_layout(title="<b>ELEVATION VIEW</b>", plot_bgcolor="white", height=400,
                      xaxis=dict(visible=False, range=[-30, w_pl+60]), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1))
    return fig

# =============================================================================
# 3. SIDE VIEW (Section) - แก้ไขตามสเก็ตช์ (Flush Column & Correct Dim)
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    h_pl, t_pl = plate['h'], plate['t']
    lv = plate.get('lv', bolts.get('lv', 40))
    s_v, n_rows = bolts['s_v'], bolts['rows']

    # 1. หน้าแปลนเสา (สีเหลือง) - คานวิ่งมาแตะพอดี
    fig.add_shape(type="line", x0=-b/2, y0=-h/2-40, x1=-b/2, y1=h/2+40, line=dict(color=C_COL_LINE, width=4))

    # 2. คาน I-Beam (เริ่มวาดจากหน้าเสา x = -b/2)
    # Top Flange
    fig.add_shape(type="rect", x0=-b/2, y0=h/2-tf, x1=b/2, y1=h/2, fillcolor=C_STEEL_FILL, line=dict(color=C_STEEL_OUT))
    # Bottom Flange
    fig.add_shape(type="rect", x0=-b/2, y0=-h/2, x1=b/2, y1=-h/2+tf, fillcolor=C_STEEL_FILL, line=dict(color=C_STEEL_OUT))
    # Web
    fig.add_shape(type="rect", x0=-tw/2, y0=-h/2+tf, x1=tw/2, y1=h/2-tf, fillcolor=C_STEEL_FILL, line=dict(color=C_STEEL_OUT))

    # 3. Shear Plate (ติดกับ Web)
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, fillcolor=C_PLATE, line=dict(color=C_STEEL_OUT))
    
    # 4. Bolts
    for i in range(n_rows):
        y_bolt = h_pl/2 - lv - (i * s_v)
        fig.add_shape(type="rect", x0=tw/2+t_pl, y0=y_bolt-4, x1=tw/2+t_pl+10, y1=y_bolt+4, 
                      fillcolor=C_BOLT, line=dict(color="black", width=0.5))
    
    # 5. Dimensions (จัดตำแหน่งตามรูปสเก็ตช์)
    add_eng_dim(fig, -b/2, h/2, 0, h/2, "b/2", "h", 45)
    add_eng_dim(fig, 0, h/2, b/2, h/2, "b/2", "h", 45)
    add_eng_dim(fig, b/2, h/2, b/2, -h/2, f"H={h}", "v", 40)
    add_eng_dim(fig, tw/2, -h_pl/2, tw/2+t_pl, -h_pl/2, f"t={t_pl}", "h", -40)

    fig.update_layout(title="<b>SIDE VIEW (SECTION)</b>", plot_bgcolor="white", height=500,
                      xaxis=dict(visible=False, range=[-b, b+50]), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1))
    return fig
