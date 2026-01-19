# report_generator.py (V25 - Ultimate Senior Global Edition)
import streamlit as st
import streamlit.components.v1 as components

def get_connection_logic(res, p):
    """
    Advanced Logic: คำนวณความสูงแผ่นเหล็กและจำนวนโบลต์ตามแรงที่เกิดขึ้นจริง
    อ้างอิงมาตรฐาน AISC 360-22
    """
    v_act = res.get('v_act', 0)
    h_beam = p.get('h', 0)
    
    # คำนวณจำนวนแถวโบลต์ (M20 Gr 8.8 รับแรงเฉือนได้ประมาณ 3,800 - 4,400 kg ตามการออกแบบ)
    rows = max(2, int(v_act / 3800) + 1)
    pitch = 75   # mm (ระยะห่างมาตรฐาน)
    edge = 40    # mm (ระยะขอบมาตรฐานขั้นต่ำสำหรับ M20)
    plate_h = (rows - 1) * pitch + (2 * edge)
    
    # ตรวจสอบ Clearance ไม่ให้แผ่นเหล็กชนปีกคาน (Flanges)
    if plate_h > (h_beam - 60):
        rows = max(2, rows - 1)
        plate_h = (rows - 1) * pitch + (2 * edge)

    return {
        "rows": rows, "pitch": pitch, "edge": edge,
        "plate_h": int(plate_h),
        "plate_t": max(9, int(p.get('tw', 6) + 3)),
        "weld_size": 6 if p.get('tw', 6) <= 10 else 8
    }

def render_report_tab(method, is_lrfd, sec_name, steel_grade, p, res, bolt):
    """
    ฟังก์ชันหลักในการสร้าง Report และ Drawing แบบสมบูรณ์
    """
    conn = get_connection_logic(res, p)
    v_cap = res.get('v_cap', 1)
    v_act = res.get('v_act', 0)
    util_ratio = (v_act / v_cap) * 100

    # --- SVG PRECISION DRAWING CONFIG ---
    c_w, c_h = 600, 550  # Canvas Size
    p_w = 80             # Plate Width
    p_h = conn['plate_h']
    
    start_x = 180        # จุดเริ่มวาดแผ่นเหล็ก (X)
    start_y = (c_h - p_h) / 2  # จุดเริ่มวาด (Y) เพื่อให้รูปอยู่กลาง Canvas
    bolt_x = start_x + (p_w / 2)
    
    # 1. หัวลูกศรแบบวิศวกรรม (Precision Markers)
    svg_defs = """
    <defs>
        <marker id="arrow-start" markerWidth="10" markerHeight="10" refX="0" refY="5" orient="auto">
            <path d="M10,0 L0,5 L10,10 Z" fill="#475569" />
        </marker>
        <marker id="arrow-end" markerWidth="10" markerHeight="10" refX="10" refY="5" orient="auto">
            <path d="M0,0 L10,5 L0,10 Z" fill="#475569" />
        </marker>
        <marker id="arrow-red" markerWidth="8" markerHeight="8" refX="8" refY="4" orient="auto">
            <path d="M0,0 L8,4 L0,8 Z" fill="#ef4444" />
        </marker>
    </defs>
    """

    # 2. วาดโบลต์และระยะห่าง (Bolts & Pitch Dimensions)
    bolt_group = ""
    dim_group = ""
    
    for i in range(conn['rows']):
        current_bolt_y = start_y + conn['edge'] + (i * conn['pitch'])
        
        # สัญลักษณ์โบลต์ (Center-cross circle)
        bolt_group += f"""
        <g transform="translate({bolt_x}, {current_bolt_y})">
            <circle r="6" fill="white" stroke="#0f172a" stroke-width="1.5"/>
            <line x1="-4" y1="-4" x2="4" y2="4" stroke="#0f172a" stroke-width="1"/>
            <line x1="4" y1="-4" x2="-4" y2="4" stroke="#0f172a" stroke-width="1"/>
        </g>
        """
        
        # เส้นบอกระยะ Pitch (75mm) - ลูกศรชี้ระหว่างจุดต่อจุด
        if i < conn['rows'] - 1:
            next_bolt_y = current_bolt_y + conn['pitch']
            dim_y_mid = (current_bolt_y + next_bolt_y) / 2
            dim_group += f"""
            <line x1="{bolt_x + 40}" y1="{current_bolt_y}" x2="{bolt_x + 40}" y2="{next_bolt_y}" stroke="#475569" stroke-width="1" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)"/>
            <text x="{bolt_x + 50}" y="{dim_y_mid + 4}" font-size="12" fill="#475569" font-family="Arial">{conn['pitch']} mm</text>
            """

    # 3. บอกระยะขอบ (Edge Distance) - ป้องกันการตกหล่นข้อมูลสำคัญ
    dim_group += f"""
    <line x1="{bolt_x + 40}" y1="{start_y}" x2="{bolt_x + 40}" y2="{start_y + conn['edge']}" stroke="#94a3b8" stroke-width="1" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)"/>
    <text x="{bolt_x + 50}" y="{start_y + conn['edge']/2 + 4}" font-size="11" fill="#94a3b8">e={conn['edge']} mm</text>
    """

    # HTML Output
    html_content = f"""
    <div style="background:#f1f5f9; padding:30px; font-family:'Inter', sans-serif;">
        <div style="max-width:850px; margin:auto; background:white; border-radius:8px; box-shadow:0 10px 25px rgba(0,0,0,0.1); overflow:hidden; border:1px solid #e2e8f0;">
            
            <div style="background:#0f172a; padding:30px 40px; color:white; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h1 style="margin:0; font-size:22px; font-weight:800; letter-spacing:0.5px;">STRUCTURAL CALCULATION REPORT</h1>
                    <p style="margin:5px 0 0; color:#94a3b8; font-size:12px;">AISC 360-22 Steel Construction Manual</p>
                </div>
                <div style="background:{'#10b981' if util_ratio <= 100 else '#ef4444'}; padding:10px 20px; border-radius:4px; text-align:center;">
                    <div style="font-size:10px; opacity:0.8;">UTILIZATION</div>
                    <div style="font-size:20px; font-weight:900;">{util_ratio:.1f}%</div>
                </div>
            </div>

            <div style="padding:40px;">
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:30px; margin-bottom:30px; font-size:13px; border-bottom:1px solid #f1f5f9; padding-bottom:20px;">
                    <div>
                        <p style="margin:5px 0; color:#64748b;">Member Section: <b style="color:#1e293b;">{sec_name}</b></p>
                        <p style="margin:5px 0; color:#64748b;">Steel Grade: <b style="color:#1e293b;">{steel_grade}</b></p>
                    </div>
                    <div>
                        <p style="margin:5px 0; color:#64748b;">Design Shear (φVn): <b style="color:#1e293b;">{v_cap:,.0f} kg</b></p>
                        <p style="margin:5px 0; color:#64748b;">Applied Shear (Vu): <b style="color:#ef4444;">{v_act:,.0f} kg</b></p>
                    </div>
                </div>

                <div style="border:1px solid #e2e8f0; border-radius:8px; background:#ffffff; position:relative;">
                    <div style="position:absolute; top:15px; left:20px; font-size:11px; font-weight:bold; color:#1e293b; text-transform:uppercase;">Typical Connection Elevation</div>
                    <svg width="100%" height="{c_h}" viewBox="0 0 {c_w} {c_h}">
                        {svg_defs}
                        
                        <rect x="{start_x - 15}" y="30" width="15" height="{c_h-60}" fill="#cbd5e1"/>
                        
                        <line x1="{start_x}" y1="60" x2="{c_w - 50}" y2="60" stroke="#e2e8f0" stroke-width="2" stroke-dasharray="8,4"/>
                        <line x1="{start_x}" y1="{c_h - 60}" x2="{c_w - 50}" y2="{c_h - 60}" stroke="#e2e8f0" stroke-width="2" stroke-dasharray="8,4"/>
                        
                        <rect x="{start_x}" y="{start_y}" width="{p_w}" height="{p_h}" fill="#3b82f6" fill-opacity="0.05" stroke="#3b82f6" stroke-width="2.5"/>
                        
                        {bolt_group}
                        {dim_group}
                        
                        <line x1="{c_w - 100}" y1="{start_y}" x2="{c_w - 100}" y2="{start_y + p_h}" stroke="#0f172a" stroke-width="1.5" marker-start="url(#arrow-start)" marker-end="url(#arrow-end)"/>
                        <text x="{c_w - 85}" y="{start_y + p_h/2}" font-size="13" font-weight="900" fill="#0f172a" transform="rotate(90 {c_w - 85},{start_y + p_h/2})">PLATE HEIGHT: {p_h} mm</text>
                        
                        <path d="M{start_x} {start_y + 30} L{start_x - 60} {start_y - 20} L{start_x - 120} {start_y - 20}" fill="none" stroke="#ef4444" stroke-width="1.5" marker-end="url(#arrow-red)"/>
                        <text x="{start_x - 120}" y="{start_y - 30}" font-size="11" font-weight="bold" fill="#ef4444">WELD FILLET {conn['weld_size']} mm (TYP)</text>
                    </svg>
                </div>

                <div style="margin-top:30px; display:grid; grid-template-columns: 1fr 1fr; gap:40px; font-size:12px; border-top:2px solid #f1f5f9; padding-top:20px; color:#475569;">
                    <div>
                        <p><b>PLATE:</b> Thickness {conn['plate_t']} mm | Grade A36/SS400</p>
                        <p><b>WELDING:</b> AWS E70XX Electrode</p>
                    </div>
                    <div>
                        <p><b>BOLTS:</b> {bolt.get('size','M20')} Grade 8.8 (High Strength)</p>
                        <p><b>HOLES:</b> Standard Clearance (+2mm)</p>
                    </div>
                </div>
            </div>

            <div style="background:#f8fafc; padding:20px 40px; border-top:1px solid #e2e8f0; display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:10px; color:#94a3b8;">Issued by Beam Insight Pro v25.0 | Jan 2026</span>
                <div style="text-align:center;">
                    <div style="width:140px; height:1px; background:#0f172a; margin-bottom:5px;"></div>
                    <span style="font-size:11px; font-weight:bold; color:#0f172a;">SENIOR ENGINEER REVIEW</span>
                </div>
            </div>
        </div>
    </div>
    """
    components.html(html_content, height=1450, scrolling=True)
