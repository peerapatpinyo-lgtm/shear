import plotly.graph_objects as go

# =============================================================================
# 🎨 STYLE CONFIGURATION
# =============================================================================
C_YELLOW_REF = "#eab308"  # เส้นหน้าเสา (สีเหลืองที่คุณเขียน)
C_STEEL_OUT = "#1e293b"   # ขอบเหล็ก
C_STEEL_FILL = "#f8fafc"  # เนื้อเหล็ก
C_PLATE = "#38bdf8"       # Shear Plate
C_BOLT = "#e11d48"        # Bolt
C_DIM = "#475569"         # เส้นบอกระยะ

# =============================================================================
# 📏 ENGINEERING DIMENSION FUNCTION (Ticks Style)
# =============================================================================
def add_eng_dim(fig, x0, y0, x1, y1, text, mode="h", offset=35):
    loc = (y0 + offset) if mode == "h" else (x0 + offset)
    
    if mode == "h":
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=loc+5, line=dict(color=C_DIM, width=0.6))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=loc+5, line=dict(color=C_DIM, width=0.6))
        fig.add_shape(type="line", x0=x0, y0=loc, x1=x1, y1=loc, line=dict(color=C_DIM, width=1))
        # Ticks
        for x in [x0, x1]:
            fig.add_shape(type="line", x0=x-3, y0=loc-3, x1=x+3, y1=loc+3, line=dict(color=C_DIM, width=1.5))
        fig.add_annotation(x=(x0+x1)/2, y=loc, text=text, showarrow=False, yshift=12, font=dict(size=12, family="Arial Black"))
    else:
        fig.add_shape(type="line", x0=x0, y0=y0, x1=loc+5, y1=y0, line=dict(color=C_DIM, width=0.6))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=loc+5, y1=y1, line=dict(color=C_DIM, width=0.6))
        fig.add_shape(type="line", x0=loc, y0=y0, x1=loc, y1=y1, line=dict(color=C_DIM, width=1))
        # Ticks
        for y in [y0, y1]:
            fig.add_shape(type="line", x0=loc-3, y0=y-3, x1=loc+3, y1=y+3, line=dict(color=C_DIM, width=1.5))
        fig.add_annotation(x=loc, y=(y0+y1)/2, text=text, showarrow=False, xshift=20, textangle=-90, font=dict(size=12, family="Arial Black"))

# =============================================================================
# 3. SIDE VIEW (SECTION) - วาดตามที่คุณเขียนแก้ด้วยเส้นสีแดง
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    h_pl, t_pl = plate['h'], plate['t']
    lv = plate.get('lv', 40)
    s_v, n_rows = bolts['s_v'], bolts['rows']

    # 1. เส้นหน้าแปลนเสา (เส้นสีเหลืองที่คุณขีดลงมา)
    fig.add_shape(type="line", x0=-b/2, y0=-h/2-50, x1=-b/2, y1=h/2+50, line=dict(color=C_YELLOW_REF, width=4))

    # 2. คาน I-Beam: ต้อง Flush (แนบ) กับเส้นเหลืองที่ x = -b/2
    # ปีกบน
    fig.add_shape(type="rect", x0=-b/2, y0=h/2-tf, x1=b/2, y1=h/2, fillcolor=C_STEEL_FILL, line=dict(color=C_STEEL_OUT))
    # ปีกล่าง
    fig.add_shape(type="rect", x0=-b/2, y0=-h/2, x1=b/2, y1=-h/2+tf, fillcolor=C_STEEL_FILL, line=dict(color=C_STEEL_OUT))
    # เอวคาน (Web)
    fig.add_shape(type="rect", x0=-tw/2, y0=-h/2+tf, x1=tw/2, y1=h/2-tf, fillcolor=C_STEEL_FILL, line=dict(color=C_STEEL_OUT))

    # 3. Shear Plate (แนบกับ Web และหน้าแปลนเสา)
    p_x_start = tw/2
    p_x_end = tw/2 + t_pl
    fig.add_shape(type="rect", x0=p_x_start, y0=-h_pl/2, x1=p_x_end, y1=h_pl/2, fillcolor=C_PLATE, line=dict(color=C_STEEL_OUT))
    
    # 4. โบลท์ (Bolt) - วาดหัวน็อตที่โผล่ออกมา
    for i in range(n_rows):
        y_bolt = h_pl/2 - lv - (i * s_v)
        fig.add_shape(type="rect", x0=p_x_end, y0=y_bolt-5, x1=p_x_end+12, y1=y_bolt+5, fillcolor=C_BOLT, line_width=0)

    # 5. การบอกระยะ (Dimensions) - ตามรูปที่คุณสเก็ตช์ b/2 และ -b/2
    add_eng_dim(fig, -b/2, h/2, 0, h/2, "b/2", "h", 50)
    add_eng_dim(fig, 0, h/2, b/2, h/2, "-b/2", "h", 50)
    add_eng_dim(fig, b/2, h/2, b/2, -h/2, f"H={h}", "v", 40)

    fig.update_layout(title="<b>SIDE VIEW (SECTION) - AS SKETCHED</b>", plot_bgcolor="white", height=500,
                      xaxis=dict(visible=False, range=[-b*0.8, b*1.2]), 
                      yaxis=dict(visible=False, scaleanchor="x", scaleratio=1))
    return fig

# ฟังก์ชันหน้าอื่นๆ (Elevation/Plan) ให้ใช้โครงสร้างคล้ายกันเพื่อความเป็นเอกภาพ
