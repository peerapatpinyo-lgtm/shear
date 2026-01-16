import plotly.graph_objects as go

# =============================================================================
# 🎨 มาตรฐานสีและสไตล์ (Color Palette)
# =============================================================================
C_COL_OUTLINE = "#fbbf24"  # สีเหลือง (ขอบเขตเสาที่คานไปเกาะ)
C_COL_FILL = "#f8fafc"     # สีพื้นเสา
C_BEAM_FILL = "#f1f5f9"    # สีเนื้อเหล็กคาน
C_BEAM_OUT = "#334155"     # สีขอบเหล็ก
C_PLATE_FILL = "#0ea5e9"   # สี Plate (ฟ้า)
C_BOLT_FILL = "#dc2626"    # สี Bolt (แดง)
C_DIM = "#475569"          # สีเส้นบอกขนาด
C_CL = "#ef4444"           # สีเส้น Centerline

# =============================================================================
# 🛠️ ฟังก์ชันเสริมสำหรับวาด CAD (Helper Functions)
# =============================================================================
def add_cad_dim(fig, x0, y0, x1, y1, text, type="horiz", offset=0):
    """ วาดเส้นบอกขนาดมาตรฐาน CAD """
    if type == "horiz":
        y_dim = y0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_dim, line=dict(color=C_DIM, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_dim, line=dict(color=C_DIM, width=0.5))
        fig.add_shape(type="line", x0=x0, y0=y_dim, x1=x1, y1=y_dim, line=dict(color=C_DIM, width=1))
        fig.add_annotation(x=(x0+x1)/2, y=y_dim, text=f"<b>{text}</b>", showarrow=False, yshift=10, font=dict(size=10, color=C_DIM), bgcolor="white")
    elif type == "vert":
        x_dim = x0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_dim, y1=y0, line=dict(color=C_DIM, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_dim, y1=y1, line=dict(color=C_DIM, width=0.5))
        fig.add_shape(type="line", x0=x_dim, y0=y0, x1=x_dim, y1=y1, line=dict(color=C_DIM, width=1))
        fig.add_annotation(x=x_dim, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=-15, textangle=-90, font=dict(size=10, color=C_DIM), bgcolor="white")

def add_centerline(fig, x0, y0, x1, y1):
    fig.add_shape(type="line", x0=x0, y0=y0, x1=x1, y1=y1, line=dict(color=C_CL, width=1, dash="dashdot"), opacity=0.6)

# =============================================================================
# 1. PLAN VIEW (มุมมองจากด้านบน)
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, b, h = beam['tw'], beam['b'], beam['h']
    t_pl, w_pl = plate['t'], plate['w']
    
    # วาดเสา (พื้นหลังที่คานไปแปะ)
    fig.add_shape(type="rect", x0=-20, y0=-b/2-20, x1=0, y1=b/2+20, fillcolor="#e2e8f0", line_width=0)
    # วาดคาน
    fig.add_shape(type="rect", x0=0, y0=-tw/2, x1=150, y1=tw/2, fillcolor=C_BEAM_FILL, line=dict(color=C_BEAM_OUT))
    # วาด Plate
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=tw/2+t_pl, fillcolor=C_PLATE_FILL, line=dict(color=C_BEAM_OUT))
    
    add_centerline(fig, -30, 0, 160, 0)
    fig.update_layout(title="PLAN VIEW", plot_bgcolor="white", height=300, showlegend=False)
    fig.update_xaxes(visible=False, range=[-50, 150]); fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    return fig

# =============================================================================
# 2. ELEVATION VIEW (มุมมองด้านหน้า)
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_beam = beam['h']
    h_pl, w_pl = plate['h'], plate['w']
    n_rows, s_v, lv = bolts['rows'], bolts['s_v'], bolts['lv']
    
    # วาดเสา
    fig.add_shape(type="rect", x0=-40, y0=-h_beam/2-20, x1=0, y1=h_beam/2+20, fillcolor="#cbd5e1", line_width=0)
    # วาดหน้า Plate ที่แปะเสา
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor=C_PLATE_FILL, opacity=0.8)
    
    # วาด Bolt
    for i in range(n_rows):
        y_pos = h_pl/2 - lv - (i * s_v)
        fig.add_shape(type="circle", x0=w_pl/2-5, y0=y_pos-5, x1=w_pl/2+5, y1=y_pos+5, fillcolor=C_BOLT_FILL, line_width=0)

    add_cad_dim(fig, w_pl+15, h_pl/2, w_pl+15, -h_pl/2, f"H_PL={h_pl}", "vert")
    fig.update_layout(title="ELEVATION VIEW", plot_bgcolor="white", height=350, showlegend=False)
    fig.update_xaxes(visible=False, range=[-60, 100]); fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    return fig

# =============================================================================
# 3. SIDE VIEW (หน้าตัดคานเกาะเสา) - แก้ไขตามที่สั่ง
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    h_pl, t_pl, lv = plate['h'], plate['t'], plate['lv']
    n_rows, s_v = bolts['rows'], bolts['s_v']

    # --- 1. วาดความกว้างเสา (เส้นเหลือง) ที่คานไปแปะ ---
    # ให้เสากว้างกว่าคานเล็กน้อยเพื่อความชัดเจน
    b_col = b + 30 
    fig.add_shape(type="rect", x0=-b_col/2, y0=-h/2-40, x1=b_col/2, y1=h/2+40, 
                  line=dict(color=C_COL_OUTLINE, width=3), fillcolor=C_COL_FILL)

    # --- 2. วาดหน้าตัดคาน (I-Section) ---
    # ปีกบน (Top Flange)
    fig.add_shape(type="rect", x0=-b/2, y0=h/2-tf, x1=b/2, y1=h/2, line=dict(color=C_BEAM_OUT, width=1.5), fillcolor=C_BEAM_FILL)
    # ปีกล่าง (Bottom Flange)
    fig.add_shape(type="rect", x0=-b/2, y0=-h/2, x1=b/2, y1=-h/2+tf, line=dict(color=C_BEAM_OUT, width=1.5), fillcolor=C_BEAM_FILL)
    # เอวคาน (Web)
    fig.add_shape(type="rect", x0=-tw/2, y0=-h/2+tf, x1=tw/2, y1=h/2-tf, line=dict(color=C_BEAM_OUT, width=1.5), fillcolor=C_BEAM_FILL)

    # --- 3. วาด Plate และ Bolt (ด้านข้าง) ---
    # Plate จะแปะอยู่ที่เอวคาน (Web)
    p_x0 = tw/2
    p_x1 = tw/2 + t_pl
    fig.add_shape(type="rect", x0=p_x0, y0=-h_pl/2, x1=p_x1, y1=h_pl/2, fillcolor=C_PLATE_FILL, line=dict(color=C_BEAM_OUT, width=1))
    
    # Bolt แสดงเป็นสี่เหลี่ยมเล็กๆ ด้านข้าง
    for i in range(n_rows):
        y_bolt = h_pl/2 - lv - (i * s_v)
        fig.add_shape(type="rect", x0=p_x1, y0=y_bolt-4, x1=p_x1+8, y1=y_bolt+4, fillcolor=C_BOLT_FILL, line_width=0)

    # --- 4. Dimensions & Centerline ---
    # **ตัดเส้นแดง (Centerline แนวตั้ง) ออกตามสั่ง** คงไว้เฉพาะแนวนอนถ้าจำเป็น
    add_centerline(fig, -b/2-20, 0, b/2+20, 0) 
    
    add_cad_dim(fig, -b/2, h/2+10, b/2, h/2+10, f"B={b:.0f}", offset=20)
    add_cad_dim(fig, b/2+30, h/2, b/2+30, -h/2, f"H={h:.0f}", "vert")

    fig.update_layout(title="SIDE VIEW (SECTION)", plot_bgcolor="white", height=400, showlegend=False,
                      xaxis=dict(visible=False, range=[-b_col, b_col]),
                      yaxis=dict(visible=False, scaleanchor="x", scaleratio=1))
    return fig
