import plotly.graph_objects as go

# =============================================================================
# 🎨 COLOR PALETTE & STYLES (คงไว้ตามมาตรฐานเดิมของคุณ)
# =============================================================================
C_COL_FILL = "#475569"    # Slate 600 (เสา)
C_BEAM_FILL = "#f1f5f9"   # Slate 100 (เนื้อคาน)
C_BEAM_OUT = "#334155"    # Slate 700 (ขอบคาน)
C_PLATE_FILL = "#0ea5e9"  # Sky 500 (เพลท)
C_BOLT_FILL = "#dc2626"   # Red 600 (น็อต)
C_DIM = "black"           # สีเส้นบอกระยะ
C_CL = "#ef4444"          # สีเส้น Centerline

# =============================================================================
# 🛠️ HELPER TOOLS (คงไว้ครบถ้วน)
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

def add_leader(fig, x, y, text, ax=30, ay=-30, color="black"):
    fig.add_annotation(x=x, y=y, text=text, showarrow=True, arrowhead=2, arrowsize=1.0, arrowwidth=1, arrowcolor=color, ax=ax, ay=ay, font=dict(size=11, color=color), bgcolor="#f8f9fa", bordercolor=color, borderpad=3)

def add_centerline(fig, x0, y0, x1, y1):
    fig.add_shape(type="line", x0=x0, y0=y0, x1=x1, y1=y1, line=dict(color=C_CL, width=1, dash="dashdot"), opacity=0.7)

# =============================================================================
# 1. PLAN VIEW (คงเดิม)
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, bf = beam['tw'], beam['b']
    w_pl, t_pl, e1, l_side = plate['w'], plate['t'], plate['e1'], plate['l_side']
    d_bolt, n_cols, s_h = bolts['d'], bolts['cols'], bolts['s_h']
    zoom_y = bf/2 + 50  
    zoom_x_end = w_pl + 60
    zoom_x_start = -30
    fig.add_shape(type="rect", x0=zoom_x_start, y0=-zoom_y, x1=0, y1=zoom_y, line=dict(color=C_BEAM_OUT, width=2), fillcolor=C_COL_FILL)
    fig.add_shape(type="rect", x0=10, y0=-tw/2, x1=zoom_x_end, y1=tw/2, line=dict(color=C_BEAM_OUT, width=1.5), fillcolor=C_BEAM_FILL)
    add_centerline(fig, zoom_x_start, 0, zoom_x_end, 0)
    py_max = tw/2 + t_pl
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=py_max, line=dict(color=C_BEAM_OUT, width=1.5), fillcolor=C_PLATE_FILL)
    bx_start = e1
    for i in range(n_cols):
        bx = bx_start + i*s_h
        fig.add_shape(type="rect", x0=bx-d_bolt/2, y0=-tw/2, x1=bx+d_bolt/2, y1=py_max, line_width=1, fillcolor=C_BOLT_FILL)
    dim_y = -zoom_y + 20
    add_cad_dim(fig, 0, dim_y, w_pl, dim_y, f"W={w_pl:.0f}")
    fig.update_layout(title="<b>PLAN VIEW</b>", plot_bgcolor="white", margin=dict(l=5,r=5,t=30,b=30), height=300, xaxis=dict(visible=False, range=[zoom_x_start, zoom_x_end], fixedrange=True), yaxis=dict(visible=False, range=[-zoom_y-30, zoom_y], scaleanchor="x", scaleratio=1, fixedrange=True), showlegend=False)
    return fig

# =============================================================================
# 2. FRONT VIEW (คงเดิม)
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_beam, tf = beam['h'], beam['tf']
    h_pl, w_pl, lv, e1 = plate['h'], plate['w'], plate['lv'], plate['e1']
    s_v, s_h = bolts['s_v'], bolts['s_h']
    d_bolt, n_rows, n_cols = bolts['d'], bolts['rows'], bolts['cols']
    zoom_y_limit = h_beam/2 + 50
    zoom_x_end = w_pl + 70
    zoom_x_start = -25
    fig.add_shape(type="rect", x0=zoom_x_start, y0=-zoom_y_limit, x1=0, y1=zoom_y_limit, line=dict(color=C_BEAM_OUT, width=2), fillcolor=C_COL_FILL)
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, line=dict(color=C_PLATE_FILL, width=2), fillcolor="rgba(14, 165, 233, 0.1)")
    by_start = h_pl/2 - lv
    for r in range(n_rows):
        for c in range(n_cols):
            bx = e1 + c*s_h
            by = by_start - r*s_v
            fig.add_shape(type="circle", x0=bx-d_bolt/2, y0=by-d_bolt/2, x1=bx+d_bolt/2, y1=by+d_bolt/2, line=dict(color=C_BOLT_FILL, width=1.5))
    dim_x = w_pl + 15
    add_cad_dim(fig, dim_x, h_pl/2, dim_x, -h_pl/2, f"H={h_pl:.0f}", "vert")
    fig.update_layout(title="<b>ELEVATION</b>", plot_bgcolor="white", margin=dict(l=5,r=35,t=30,b=30), height=320, xaxis=dict(visible=False, range=[zoom_x_start, zoom_x_end], fixedrange=True), yaxis=dict(visible=False, range=[-zoom_y_limit-30, zoom_y_limit], scaleanchor="x", scaleratio=1, fixedrange=True), showlegend=False)
    return fig

# =============================================================================
# 3. SIDE VIEW (จุดที่มีการแก้ไขหน้าตัดเสา)
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    t_pl, h_pl, lv = plate['t'], plate['h'], plate['lv']
    d_bolt, n_rows, s_v = bolts['d'], bolts['rows'], bolts['s_v']

    # --- 1. หน้าตัดเสา (Column I-Section) วาดทางซ้ายสุด ---
    # ใช้ขนาดเดียวกับคานเพื่อให้สัดส่วนดูสมจริงตามรูป sketch
    col_x_center = -b/2 - 5  # ระยะห่างเล็กน้อยจากคาน
    # ปีกเสา (Flanges)
    fig.add_shape(type="rect", x0=col_x_center-b/2, y0=h/2, x1=col_x_center+b/2, y1=h/2+tf, line=dict(color=C_BEAM_OUT, width=1.5), fillcolor=C_COL_FILL)
    fig.add_shape(type="rect", x0=col_x_center-b/2, y0=-h/2-tf, x1=col_x_center+b/2, y1=-h/2, line=dict(color=C_BEAM_OUT, width=1.5), fillcolor=C_COL_FILL)
    # เอวเสา (Web)
    fig.add_shape(type="rect", x0=col_x_center-tw/2, y0=-h/2, x1=col_x_center+tw/2, y1=h/2, line=dict(color=C_BEAM_OUT, width=1.5), fillcolor=C_COL_FILL)

    # --- 2. หน้าตัดคาน (Beam I-Section) ---
    fig.add_shape(type="rect", x0=-b/2, y0=h/2-tf, x1=b/2, y1=h/2, line=dict(color=C_BEAM_OUT, width=1.5), fillcolor=C_BEAM_FILL)
    fig.add_shape(type="rect", x0=-b/2, y0=-h/2, x1=b/2, y1=-h/2+tf, line=dict(color=C_BEAM_OUT, width=1.5), fillcolor=C_BEAM_FILL)
    fig.add_shape(type="rect", x0=-tw/2, y0=-h/2+tf, x1=tw/2, y1=h/2-tf, line=dict(color=C_BEAM_OUT, width=1.5), fillcolor=C_BEAM_FILL)

    # --- 3. Shear Plate และ Bolt ---
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, line=dict(color=C_BEAM_OUT, width=1.5), fillcolor=C_PLATE_FILL)
    bolt_x = tw/2 + t_pl
    by_start = h_pl/2 - lv
    for r in range(n_rows):
        by = by_start - r*s_v
        fig.add_shape(type="rect", x0=bolt_x, y0=by-d_bolt/2, x1=bolt_x+10, y1=by+d_bolt/2, line=dict(color=C_BOLT_FILL, width=1), fillcolor=C_BOLT_FILL)

    # --- 4. Dimensions ---
    add_cad_dim(fig, -b/2, h/2, b/2, h/2, f"B={b:.0f}", offset=35)
    add_cad_dim(fig, -b/2-25, h/2, -b/2-25, -h/2, f"H={h:.0f}", "vert")

    fig.update_layout(title="<b>SIDE VIEW</b>", plot_bgcolor="white", margin=dict(l=5,r=5,t=30,b=5), height=300, xaxis=dict(visible=False, range=[col_x_center-b, b+50], fixedrange=True), yaxis=dict(visible=False, range=[-h-50, h+50], scaleanchor="x", scaleratio=1, fixedrange=True), showlegend=False)
    return fig
