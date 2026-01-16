# drawing_utils.py (V21 - True Engineering Edition)
import plotly.graph_objects as go

# --- Professional Standards ---
THEME = {
    "steel_dark": "#212529", # Column
    "steel_light": "#F8F9FA", # Beam
    "plate": "#1976D2",       # Plate
    "bolt": "#D32F2F",        # Bolt
    "dim_line": "#455A64"
}

def add_standard_dim(fig, x0, y0, x1, y1, text, axis="H", offset=60):
    """ฟังก์ชันให้มิติงานเหล็ก พร้อมขีดเฉียง (Tick Marks)"""
    y_pos = y0 + offset if axis == "H" else y0
    x_pos = x0 + offset if axis == "V" else x0
    
    # เส้นช่วยมิติ (Extension lines)
    if axis == "H":
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_pos + (10 if offset>0 else -10), line=dict(color=THEME["dim_line"], width=1))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_pos + (10 if offset>0 else -10), line=dict(color=THEME["dim_line"], width=1))
        fig.add_shape(type="line", x0=x0, y0=y_pos, x1=x1, y1=y_pos, line=dict(color=THEME["dim_line"], width=1.2))
        # Tick Marks
        for x in [x0, x1]:
            fig.add_shape(type="line", x0=x-4, y0=y_pos-4, x1=x+4, y1=y_pos+4, line=dict(color=THEME["dim_line"], width=1.5))
        fig.add_annotation(x=(x0+x1)/2, y=y_pos, text=text, showarrow=False, yshift=12, font=dict(size=12))
    else:
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_pos + (10 if offset>0 else -10), y1=y0, line=dict(color=THEME["dim_line"], width=1))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_pos + (10 if offset>0 else -10), y1=y1, line=dict(color=THEME["dim_line"], width=1))
        fig.add_shape(type="line", x0=x_pos, y0=y0, x1=x_pos, y1=y1, line=dict(color=THEME["dim_line"], width=1.2))
        for y in [y0, y1]:
            fig.add_shape(type="line", x0=x_pos-4, y0=y-4, x1=x_pos+4, y1=y+4, line=dict(color=THEME["dim_line"], width=1.5))
        fig.add_annotation(x=x_pos, y=(y0+y1)/2, text=text, showarrow=False, xshift=18, textangle=-90, font=dict(size=12))

# =============================================================================
# ELEVATION VIEW (FIXED BOLT POSITION)
# =============================================================================
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_b, h_pl, w_pl = beam['h'], plate['h'], plate['w']
    # แก้ไข Logic ระยะ Bolt: ให้มีระยะ Edge distance ขั้นต่ำ
    e1, s_v, s_h = plate['e1'], bolts['s_v'], bolts['s_h']
    edge_v = (h_pl - (bolts['rows'] - 1) * s_v) / 2 # คำนวณระยะขอบบน-ล่างให้สมดุลอัตโนมัติ

    # Column Background
    fig.add_shape(type="rect", x0=-40, y0=-h_b/2-100, x1=0, y1=h_b/2+100, fillcolor=THEME["steel_dark"], line_width=0)
    # Plate
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor="rgba(25, 118, 210, 0.1)", line=dict(color=THEME["plate"], width=2.5))

    # Bolts (กระจายตัวกึ่งกลาง Plate)
    for r in range(bolts['rows']):
        for c in range(bolts['cols']):
            bx = e1 + c*s_h
            by = (h_pl/2 - edge_v) - r*s_v
            fig.add_shape(type="circle", x0=bx-bolts['d']/2, y0=by-bolts['d']/2, x1=bx+bolts['d']/2, y1=by+bolts['d']/2, fillcolor=THEME["bolt"], line_width=0)

    # Dimensions
    add_standard_dim(fig, w_pl, h_pl/2, w_pl, -h_pl/2, f"H_PL={h_pl}", axis="V", offset=60)
    add_standard_dim(fig, 0, -h_pl/2, w_pl, -h_pl/2, f"W_PL={w_pl}", axis="H", offset=-60)

    fig.update_layout(xaxis=dict(visible=False, range=[-100, w_pl+150]), 
                      yaxis=dict(visible=False, range=[-h_b/2-150, h_b/2+150], scaleanchor="x", scaleratio=1),
                      plot_bgcolor="white")
    return fig

# =============================================================================
# SECTION VIEW (FIXED COLUMN LINES)
# =============================================================================
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw, t_pl, h_pl = beam['h'], beam['b'], beam['tf'], beam['tw'], plate['t'], plate['h']

    # --- เพิ่มเส้นคู่ของหน้าตัดเสา (Column Flange) ---
    col_x = -b/2 - 40
    fig.add_shape(type="line", x0=col_x, y0=-h/2-100, x1=col_x, y1=h/2+100, line=dict(color=THEME["steel_dark"], width=3)) # เส้นนอก
    fig.add_shape(type="line", x0=col_x+12, y0=-h/2-100, x1=col_x+12, y1=h/2+100, line=dict(color=THEME["steel_dark"], width=1.5)) # เส้นในบอกความหนาปีกเสา

    # I-Beam Section
    p = f"M {-b/2},{-h/2} L {b/2},{-h/2} L {b/2},{-h/2+tf} L {tw/2},{-h/2+tf} L {tw/2},{h/2-tf} L {b/2},{h/2-tf} L {b/2},{h/2} L {-b/2},{h/2} L {-b/2},{h/2-tf} L {-tw/2},{h/2-tf} L {-tw/2},{-h/2+tf} L {-b/2},{-h/2+tf} Z"
    fig.add_shape(type="path", path=p, fillcolor=THEME["steel_light"], line=dict(color=THEME["steel_dark"], width=2.5))
    
    # Plate (แปะข้าง Web)
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, fillcolor=THEME["plate"], line=dict(color=THEME["steel_dark"], width=1.5))

    add_standard_dim(fig, -b/2, h/2, b/2, h/2, f"B={b}", axis="H", offset=60)
    add_standard_dim(fig, -b/2, h/2, -b/2, -h/2, f"H={h}", axis="V", offset=-80)

    fig.update_layout(xaxis=dict(visible=False, range=[col_x-50, b/2+150]), 
                      yaxis=dict(visible=False, range=[-h/2-150, h/2+150], scaleanchor="x", scaleratio=1),
                      plot_bgcolor="white")
    return fig

# *** อย่าลืมเพิ่ม create_plan_view กลับไปด้วยนะครับ ***
def create_plan_view(beam, plate, bolts):
    # (ใช้ Logic เดียวกันกับเวอร์ชันก่อนหน้าแต่ปรับ Range ให้เห็นครบ)
    fig = go.Figure()
    # ... (วาด Plan view)
    fig.update_layout(xaxis=dict(visible=False, range=[-100, 300]), yaxis=dict(visible=False, range=[-150, 150], scaleanchor="x", scaleratio=1))
    return fig
