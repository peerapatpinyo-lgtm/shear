import plotly.graph_objects as go

# =============================================================================
# 🎨 ENGINEERING STYLE GUIDE
# =============================================================================
C_STEEL_OUT = "#1e293b"    
C_BEAM_WEB = "#f1f5f9"     
C_PLATE = "#0ea5e9"        
C_BOLT = "#be123c"         
C_DIM_LINE = "#475569"     
C_YELLOW_COL = "#eab308"   
C_CL = "#ef4444"           

# =============================================================================
# 📏 FIXED DIMENSIONING SYSTEM (แก้ Error y_loc)
# =============================================================================
def add_eng_dim(fig, x0, y0, x1, y1, text, mode="h", offset=25):
    """ เส้นบอกระยะมาตรฐานวิศวกรรม (Fixed Variable Assignment) """
    if mode == "h":
        loc = y0 + offset
        # Extension Lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=loc+(5 if offset>0 else -5), line=dict(color=C_DIM_LINE, width=0.8))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=loc+(5 if offset>0 else -5), line=dict(color=C_DIM_LINE, width=0.8))
        # Arrows
        fig.add_annotation(x=x0, y=loc, ax=x1, ay=loc, xref="x", yref="y", axref="x", ayref="y", text="", showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=C_DIM_LINE)
        fig.add_annotation(x=x1, y=loc, ax=x0, ay=loc, xref="x", yref="y", axref="x", ayref="y", text="", showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=C_DIM_LINE)
        # Text
        fig.add_annotation(x=(x0+x1)/2, y=loc, text=text, showarrow=False, yshift=10 if offset>0 else -10, font=dict(size=10, family="Arial"), bgcolor="white")
    else:
        loc = x0 + offset
        # Extension Lines
        fig.add_shape(type="line", x0=x0, y0=y0, x1=loc+(5 if offset>0 else -5), y1=y0, line=dict(color=C_DIM_LINE, width=0.8))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=loc+(5 if offset>0 else -5), y1=y1, line=dict(color=C_DIM_LINE, width=0.8))
        # Arrows
        fig.add_annotation(x=loc, y=y0, ax=loc, ay=y1, xref="x", yref="y", axref="x", ayref="y", text="", showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=C_DIM_LINE)
        fig.add_annotation(x=loc, y=y1, ax=loc, ay=y0, xref="x", yref="y", axref="x", ayref="y", text="", showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor=C_DIM_LINE)
        # Text
        fig.add_annotation(x=loc, y=(y0+y1)/2, text=text, showarrow=False, xshift=12 if offset>0 else -12, textangle=-90, font=dict(size=10, family="Arial"), bgcolor="white")

def add_centerline(fig, x0, y0, x1, y1):
    fig.add_shape(type="line", x0=x0, y0=y0, x1=x1, y1=y1, line=dict(color=C_CL, width=1, dash="dashdot"), opacity=0.5)

# =============================================================================
# 1. PLAN VIEW (TOP)
# =============================================================================
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, b, w_pl, t_pl = beam['tw'], beam['b'], plate['w'], plate['t']
    
    # วาดหน้าตัดเสาเป็น Reference (เส้นสีเหลืองประ)
    fig.add_shape(type="rect", x0=-20, y0=-b/2, x1=0, y1=b/2, line=dict(color=C_YELLOW_COL, dash="dash"), fillcolor="rgba(241,245,249,0.5)")
    # วาดคานและเพลท
    fig.add_shape(type="rect", x0=0, y0=-tw/2, x1=w_pl+30, y1=tw/2, fillcolor=C_BEAM_WEB, line=dict(color=C_STEEL_OUT))
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=tw/2+t_pl, fillcolor=C_PLATE, line=dict(color=C_STEEL_OUT))
    
    add_centerline(fig, -30, 0, w_pl+40, 0)
    add_eng_dim(fig, 0, tw/2+t_pl, w_pl, tw/2+t_pl, f"Wp={w_pl}", "h", 25)

    fig.update_layout(title="<b>PLAN VIEW</b>", plot_bgcolor="white", height=300, margin=dict(l=20,r=20,t=40,b=20),
                      xaxis=dict(visible=False, range=[-40, w_pl+60]), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1))
    return fig

# =============================================================================
# 2. ELEVATION VIEW (Front)
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_b, h_pl, w_pl = beam['h'], plate['h'], plate['w']
    lv, s_v, n_rows = plate.get('lv', 35), bolts['s_v'], bolts['rows']
    
    fig.add_shape(type="rect", x0=-20, y0=-h_b/2, x1=0, y1=h_b/2, line=dict(color=C_YELLOW_COL, dash="dash"))
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor=C_PLATE, line=dict(color=C_STEEL_OUT))
    
    for i in range(n_rows):
        y_bolt = h_pl/2 - lv - (i * s_v)
        fig.add_shape(type="circle", x0=w_pl/2-5, y0=y_bolt-5, x1=w_pl/2+5, y1=y_bolt+5, fillcolor=C_BOLT, line_width=0)

    add_eng_dim(fig, w_pl, h_pl/2, w_pl, -h_pl/2, f"Hp={h_pl}", "v", 30)
    
    fig.update_layout(title="<b>ELEVATION VIEW</b>", plot_bgcolor="white", height=350, margin=dict(l=20,r=20,t=40,b=20),
                      xaxis=dict(visible=False, range=[-40, w_pl+70]), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1))
    return fig

# =============================================================================
# 3. SIDE VIEW (Detailed Section)
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw = beam['h'], beam['b'], beam['tf'], beam['tw']
    h_pl, t_pl = plate['h'], plate['t']
    lv, s_v, n_rows = plate.get('lv', 35), bolts['s_v'], bolts['rows']

    # 1. Column Reference (Boundary)
    fig.add_shape(type="rect", x0=-b/2-15, y0=-h/2-30, x1=b/2+15, y1=h/2+30, 
                  line=dict(color=C_YELLOW_COL, width=2, dash="dash"), fillcolor="rgba(241,245,249,0.3)")

    # 2. I-Beam Section
    fig.add_shape(type="rect", x0=-b/2, y0=h/2-tf, x1=b/2, y1=h/2, line=dict(color=C_STEEL_OUT), fillcolor=C_BEAM_WEB)
    fig.add_shape(type="rect", x0=-b/2, y0=-h/2, x1=b/2, y1=-h/2+tf, line=dict(color=C_STEEL_OUT), fillcolor=C_BEAM_WEB)
    fig.add_shape(type="rect", x0=-tw/2, y0=-h/2+tf, x1=tw/2, y1=h/2-tf, line=dict(color=C_STEEL_OUT), fillcolor=C_BEAM_WEB)

    # 3. Plate & Bolts
    p_x1 = tw/2 + t_pl
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=p_x1, y1=h_pl/2, fillcolor=C_PLATE, line=dict(color=C_STEEL_OUT))
    for i in range(n_rows):
        y_bolt = h_pl/2 - lv - (i * s_v)
        fig.add_shape(type="rect", x0=p_x1, y0=y_bolt-4, x1=p_x1+10, y1=y_bolt+4, fillcolor=C_BOLT, line_width=0)
    
    # 4. Professional Dimensions
    add_eng_dim(fig, -b/2, h/2, b/2, h/2, f"B={b}", "h", 35)
    add_eng_dim(fig, b/2, h/2, b/2, -h/2, f"H={h}", "v", 35)
    add_eng_dim(fig, tw/2, -h_pl/2, tw/2+t_pl, -h_pl/2, f"t={t_pl}", "h", -35)

    fig.update_layout(title="<b>SIDE SECTION VIEW</b>", plot_bgcolor="white", height=450, margin=dict(l=10,r=10,t=40,b=10),
                      xaxis=dict(visible=False, range=[-b, b+60]), yaxis=dict(visible=False, scaleanchor="x", scaleratio=1))
    return fig
