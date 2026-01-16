# แก้ไขเฉพาะฟังก์ชันที่มีปัญหาเรื่อง Bolt ชิดขอบ

def create_front_view(beam, plate, bolts):
    fig = go.Figure()
    h_b, h_pl, w_pl = beam['h'], plate['h'], plate['w']
    # กำหนดค่า Edge Distance ให้ชัดเจน (ถ้าไม่มีใน input ให้ใช้ default ที่ปลอดภัย)
    lv = plate.get('lv', 40)  # ระยะจากขอบบนถึง Bolt ตัวแรก
    s_v = bolts['s_v']        # ระยะห่างระหว่าง Bolt (Pitch)
    n_rows = bolts['rows']
    
    # วาด Column Reference
    fig.add_shape(type="line", x0=0, y0=-h_b/2-10, x1=0, y1=h_b/2+10, line=dict(color=C_COL_LINE, width=4))
    # วาด Plate
    fig.add_shape(type="rect", x0=0, y0=-h_pl/2, x1=w_pl, y1=h_pl/2, fillcolor=C_PLATE, line=dict(color=C_STEEL_OUT))
    
    # --- จุดที่แก้ไข: วาด Bolt ให้อยู่กึ่งกลางความกว้าง Plate ---
    bolt_x_center = w_pl / 2  # บังคับให้อยู่กลาง Plate เสมอ
    for i in range(n_rows):
        y_bolt = h_pl/2 - lv - (i * s_v)
        fig.add_shape(type="circle", 
                      x0=bolt_x_center-6, y0=y_bolt-6, 
                      x1=bolt_x_center+6, y1=y_bolt+6, 
                      fillcolor=C_BOLT, line_width=1, line_color="black")

    add_dim(fig, w_pl, h_pl/2, w_pl, -h_pl/2, f"Hp={h_pl}", "v", 35)
    # เพิ่ม Dimension บอกระยะขอบ (Edge Distance) เพื่อความชัดเจน
    add_dim(fig, 0, h_pl/2, bolt_x_center, h_pl/2, f"e={bolt_x_center}", "h", 20)
    
    fig.update_layout(title="<b>ELEVATION VIEW (FRONT)</b>", plot_bgcolor="white", height=400,
                      xaxis=dict(visible=False, range=[-30, w_pl+60]), 
                      yaxis=dict(visible=False, scaleanchor="x", scaleratio=1))
    return fig

def create_side_view(beam, plate, bolts):
    # ... (ส่วนประกอบคานคงเดิม) ...
    # ใน Side View ให้ปรับระยะ Bolt Shank ให้สมดุล
    p_x_end = tw/2 + t_pl
    for i in range(n_rows):
        y_bolt = h_pl/2 - lv - (i * s_v)
        # วาด Bolt ที่พุ่งออกมาจาก Plate (Shank & Nut)
        fig.add_shape(type="rect", x0=p_x_end, y0=y_bolt-5, x1=p_x_end+12, y1=y_bolt+5, 
                      fillcolor=C_BOLT, line=dict(color="black", width=0.5))
    # ... (ส่วนอื่นคงเดิม) ...
