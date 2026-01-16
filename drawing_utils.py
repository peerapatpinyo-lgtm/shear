# drawing_utils.py (V22 - Professional Signature Edition)
import plotly.graph_objects as go

# --- Global Engineering Theme ---
STYLE = {
    "col_main": "#263238", "col_edge": "#37474F",
    "beam_fill": "#F1F8E9", "beam_line": "#1B5E20",
    "plate_fill": "rgba(2, 136, 209, 0.15)", "plate_line": "#0277BD",
    "bolt": "#D32F2F", "dim": "#546E7A"
}

def add_pro_dim(fig, x0, y0, x1, y1, text, axis="H", offset=50):
    """ฟังก์ชันให้มิติงานเหล็กระดับสากล (Tick Marks & Extension Lines)"""
    y_d = y0 + offset if axis == "H" else y0
    x_d = x0 + offset if axis == "V" else x0
    
    # Extension lines
    if axis == "H":
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x0, y1=y_d+8, line=dict(color=STYLE["dim"], width=1))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x1, y1=y_d+8, line=dict(color=STYLE["dim"], width=1))
        fig.add_shape(type="line", x0=x0, y0=y_d, x1=x1, y1=y_d, line=dict(color=STYLE["dim"], width=1.5))
        for x in [x0, x1]:
            fig.add_shape(type="line", x0=x-4, y0=y_d-4, x1=x+4, y1=y_d+4, line=dict(color=STYLE["dim"], width=2))
        fig.add_annotation(x=(x0+x1)/2, y=y_d, text=f"<b>{text}</b>", showarrow=False, yshift=15, font=dict(size=12))
    else:
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x_d+8, y1=y0, line=dict(color=STYLE["dim"], width=1))
        fig.add_shape(type="line", x0=x1, y0=y1, x1=x_d+8, y1=y1, line=dict(color=STYLE["dim"], width=1))
        fig.add_shape(type="line", x0=x_d, y0=y0, x1=x_d, y1=y1, line=dict(color=STYLE["dim"], width=1.5))
        for y in [y0, y1]:
            fig.add_shape(type="line", x0=x_d-4, y0=y-4, x1=x_d+4, y1=y+4, line=dict(color=STYLE["dim"], width=2))
        fig.add_annotation(x=x_d, y=(y0+y1)/2, text=f"<b>{text}</b>", showarrow=False, xshift=20, textangle=-90, font=dict(size=12))

# --- 1. FRONT VIEW: ปรับระยะโบลท์ให้กึ่งกลางและปลอดภัย ---
def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_b, h_pl, w_pl = beam['h'], plate['h'], plate['w']
    s_v, s_h, rows, cols = bolts['s_v'], bolts['s_h'], bolts['rows'], bolts['cols']
    e1 = plate['e1']
    
    # คำนวณระยะขอบแนวตั้งให้สมดุล (Auto Centering)
    v_total_pitch = (rows - 1) * s_v
    edge_v = (h_pl - v_total_pitch) / 2 # ระยะจากขอบบนถึงโบลท์ตัวแรก

    # Column Flange
    fig.add_shape(type="rect", x0=-40, y0=-h_b/2-100, x1=0, y1=h_b/2+100, fillcolor=STYLE["col_main"], line_width=0)
    # Shear Plate
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor=STYLE["plate_fill"], line=dict(color=STYLE["plate_line"], width=2.5))

    # Bolts
    for r in range(rows):
        for c in range(cols):
            bx = e1 + c*s_h
            by = (h_pl/2 - edge_v) - r*s_v
            fig.add_shape(type="circle", x0=bx-8, y0=by-8, x1=bx+8, y1=by+8, fillcolor=STYLE["bolt"], line_width=0)

    add_pro_dim(fig, w_pl, h_pl/2, w_pl, -h_pl/2, f"H_PL={h_pl}", "V", 60)
    add_pro_dim(fig, 0, -h_pl/2, w_pl, -h_pl/2, f"W_PL={w_pl}", "H", -60)

    fig.update_layout(xaxis=dict(visible=False, range=[-100, w_pl+150]), yaxis=dict(visible=False, range=[-h_b/2-150, h_b/2+150], scaleanchor="x", scaleratio=1), plot_bgcolor="white")
    return fig

# --- 2. SECTION VIEW: เพิ่มเส้นคู่ปีกเสาและตำแหน่งคานที่ถูกต้อง ---
def create_side_view(beam, plate, bolts):
    fig = go.Figure()
    h, b, tf, tw, t_pl, h_pl = beam['h'], beam['b'], beam['tf'], beam['tw'], plate['t'], plate['h']

    # วาดหน้าตัดเสาด้านหลัง (เส้นคู่ 2 ชุด เพื่อบอกความหนาปีกเสา)
    col_x = -b/2 - 60
    # ปีกเสาด้านนอก
    fig.add_shape(type="line", x0=col_x, y0=-h/2-100, x1=col_x, y1=h/2+100, line=dict(color=STYLE["col_main"], width=3))
    # ปีกเสาด้านใน (หนา 12mm โดยประมาณ)
    fig.add_shape(type="line", x0=col_x+12, y0=-h/2-100, x1=col_x+12, y1=h/2+100, line=dict(color=STYLE["col_main"], width=1.5))

    # I-Beam Section (SVG Path เพื่อความคมชัด)
    p = f"M {-b/2},{-h/2} L {b/2},{-h/2} L {b/2},{-h/2+tf} L {tw/2},{-h/2+tf} L {tw/2},{h/2-tf} L {b/2},{h/2-tf} L {b/2},{h/2} L {-b/2},{h/2} L {-b/2},{h/2-tf} L {-tw/2},{h/2-tf} L {-tw/2},{-h/2+tf} L {-b/2},{-h/2+tf} Z"
    fig.add_shape(type="path", path=p, fillcolor=STYLE["beam_fill"], line=dict(color=STYLE["col_main"], width=2.5))
    
    # Plate แปะข้าง Web
    fig.add_shape(type="rect", x0=tw/2, y0=-h_pl/2, x1=tw/2+t_pl, y1=h_pl/2, fillcolor=STYLE["plate_line"], line_width=0)

    add_pro_dim(fig, -b/2, h/2, b/2, h/2, f"B={b}", "H", 60)
    add_pro_dim(fig, -b/2, h/2, -b/2, -h/2, f"H={h}", "V", -80)

    fig.update_layout(xaxis=dict(visible=False, range=[col_x-50, b/2+150]), yaxis=dict(visible=False, range=[-h/2-150, h/2+150], scaleanchor="x", scaleratio=1), plot_bgcolor="white")
    return fig

# --- 3. PLAN VIEW: ปรับสัดส่วนให้เห็นภาพรวม ---
def create_plan_view(beam, plate, bolts):
    fig = go.Figure()
    tw, bf, w_pl, t_pl, e1, s_h = beam['tw'], beam['b'], plate['w'], plate['t'], plate['e1'], bolts['s_h']
    
    # Column
    fig.add_shape(type="rect", x0=-40, y0=-bf/2, x1=0, y1=bf/2, fillcolor=STYLE["col_main"], line_width=0)
    # Beam
    fig.add_shape(type="rect", x0=0, y0=-tw/2, x1=w_pl+150, y1=tw/2, fillcolor=STYLE["beam_fill"], line=dict(color=STYLE["col_main"], width=2))
    # Plate
    fig.add_shape(type="rect", x0=0, y0=tw/2, x1=w_pl, y1=tw/2+t_pl, fillcolor=STYLE["plate_line"], line_width=0)

    # Bolts (Top View)
    for i in range(bolts['cols']):
        bx = e1 + i*s_h
        fig.add_shape(type="rect", x0=bx-6, y0=-tw/2-10, x1=bx+6, y1=tw/2+t_pl+10, fillcolor=STYLE["bolt"], line_width=0)

    add_pro_dim(fig, 0, -bf/2, w_pl, -bf/2, f"W_PL={w_pl}", "H", -60)
    fig.update_layout(xaxis=dict(visible=False, range=[-100, w_pl+200]), yaxis=dict(visible=False, range=[-bf/2-100, bf/2+100], scaleanchor="x", scaleratio=1), plot_bgcolor="white")
    return fig
