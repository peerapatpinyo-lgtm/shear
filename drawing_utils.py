import plotly.graph_objects as go

# =============================================================================
# 🎨 COLOR PALETTE & STYLES (คงไว้ตามมาตรฐานเดิม)
# =============================================================================
C_COL_FILL = "#475569"    # Slate 600 (เสา)
C_BEAM_FILL = "#f1f5f9"   # Slate 100 (เนื้อคาน)
C_BEAM_OUT = "#334155"    # Slate 700 (ขอบคาน)
C_PLATE_FILL = "#0ea5e9"  # Sky 500 (เพลท)
C_BOLT_FILL = "#dc2626"   # Red 600 (น็อต)
C_DIM = "black"           # สีเส้นบอกระยะ
C_CL = "#ef4444"          # สีเส้น Centerline

# =============================================================================
# 🛠️ HELPER TOOLS (คงไว้ครบถ้วนเพื่อไม่ให้เกิด Error)
# =============================================================================
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
        fig.add_annotation(x=(x0+x1)/2, y=y_dim, text=f"<b>{text}</b>", showarrow=False, yshift=8 if offset>0 else -8, font=dict(size=11, color=C_DIM, family="Arial"), bgcolor="white")
    elif type == "vert":
        x_dim = x0 + offset
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_dim, y1=y0, line=dict(color=C_DIM, width=0.5))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_dim, y1=y1, line=dict(color=C_DIM, width=0.5))
        fig.add_shape(type="line", x0=x_dim, y0=y0, x1=x_dim, y1=y1, line=dict(color=C_DIM, width=1))
        fig.add_annotation(x=x_dim, y=y0, ax=0, ay=-5, arrowhead=arrow_head_style, arrowsize=arrow_scale, arrowwidth=arrow_width, arrowcolor=C_DIM, text="")
        fig.add_annotation(x=x_dim, y=y1, ax=0, ay=5, arrowhead=arrow_head_style, arrowsize=arrow_scale, arrowwidth=arrow_width, arrowcolor=C_DIM, text="")
        fig.add_annotation(x=x_dim, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=12 if offset>0 else -12, font=dict(size=11, color=C_DIM, family="Arial"), textangle=-90, bgcolor="white")

def add_centerline(fig, x0, y0, x1, y1):
    fig.add_shape(type="line", x0=x0, y0=y0, x1=x1, y1=y1, line=dict(color=C_CL, width=1, dash="dashdot"), opacity=0.7)

# =============================================================================
# 1. PLAN VIEW (คงเดิม)
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, bf = beam['tw'], beam['b']
    w_pl, t_pl, e1 = plate['w'], plate['t'], plate['e1']
    d_bolt, n_cols, s_h = bolts['d'], bolts['cols'], bolts['s_h']
    zoom_y = bf/2 + 50  
    fig.add_shape(type="rect", x0=-30, y0=-zoom_y, x1=0, y1=zoom_y, fillcolor=C_COL_FILL, line_width=0)
    fig.add_shape(type="rect", x0=0, y0=-tw/2, x1=w_pl+50, y1=tw/2, fillcolor=C_BEAM_FILL, line=dict(color=C_BEAM_OUT))
    add_centerline(fig, -30, 0, w_pl+50, 0)
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=tw/2+t_pl, fillcolor=C_PLATE_FILL)
    fig.update_layout(title="PLAN VIEW", plot_bgcolor="white", showlegend=False, height=300)
    fig.update_xaxes(visible=False); fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    return fig

# =============================================================================
# 2. FRONT VIEW (คงเดิม)
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_pl, w_pl = plate['h'], plate['w']
    fig.add_shape(type="rect", x0=-20, y0=-h_pl, x1=0, y1=h_pl, fillcolor=C_COL_FILL)
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor=C_PLATE_FILL, opacity=0.3)
    add_cad_dim(fig, w_pl+10, h_pl/2, w_pl+10, -h_pl/2, f"H_PL={h_pl}", "vert")
    fig.update_layout(title="ELEVATION VIEW", plot_bgcolor="white", showlegend=False, height=300)
    fig.update_xaxes(visible=False); fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    return fig

# =============================================================================
# 3. SIDE VIEW (SECTION) - แก้ไขตามรูป Sketch ล่าสุด
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    t_pl, h_pl, lv = plate['t'], plate['h'], plate['lv']
    d_bolt, n_rows, s_v = bolts['d'], bolts['rows'], bolts['s_v']

    # --- 1. วาดเสา (เส้นสีเหลืองที่คุณขีดคือความกว้างหน้าตัดเสา) ---
    # สมมติให้เสามีขนาดเท่ากับคาน (หรือคุณสามารถปรับ b_col ได้)
    b_col = b + 20 
    # พื้นหลังเสา (แสดงความกว้างเสาตามเส้นสีเหลือง)
    fig.add_shape(type="rect", x0=-b_col/2, y0=-h/2-20, x1=b_col/2, y1=h/2+20, 
                  line=dict(color="#fbbf24", width=2), fillcolor="#f1f5f9") # เส้นขอบเหลืองตามสั่ง

    # --- 2. วาดหน้าตัดคาน (I-Beam) ที่มาต่อ ---
    # ปีกบน-ล่าง
    fig.add_shape(type="rect", x0=-b/2, y0=h/2-tf, x1=b/2, y1=h/2, line=dict(color=C_BEAM_OUT), fillcolor=C_BEAM_FILL)
    fig.add_shape(type="rect", x0=-b/2, y0=-h/2, x1=b/2, y1=-h/2+tf, line=dict(color=C_BEAM_OUT), fillcolor=C_BEAM_FILL)
    # เอวคาน (Web)
    fig.add_shape(type="rect", x0=-tw/2, y0=-h/2+tf, x1=tw/2, y1=h/2-tf, line=dict(color=C_BEAM_OUT), fillcolor=C_BEAM_FILL)

    # --- 3. วาด Shear Plate (แปะที่เอวคาน) ---
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, fillcolor=C_PLATE_FILL)
    
    # --- 4. Dimensions ---
    add_cad_dim(fig, -b/2, h/2+10, b/2, h/2+10, f"B={b:.0f}", offset=20)
    add_cad_dim(fig, -b/2-15, h/2, -b/2-15, -h/2, f"H={h:.0f}", "vert")

    # ตั้งค่า Layout (ตัดเส้น Grid และโชว์สัดส่วนจริง)
    fig.update_layout(title="<b>SIDE VIEW (SECTION)</b>", plot_bgcolor="white", height=350,
                      xaxis=dict(visible=False, range=[-b, b], fixedrange=True),
                      yaxis=dict(visible=False, range=[-h-50, h+50], scaleanchor="x", scaleratio=1, fixedrange=True))
    return fig
