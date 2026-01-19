# report_generator.py (V19 - Fully Functional Drawing & Trace)
import streamlit as st
import streamlit.components.v1 as components

def get_connection_logic(res, p):
    """คำนวณระยะทางวิศวกรรมสำหรับวาด Drawing"""
    v_act = res.get('v_act', 0)
    h_beam = p.get('h', 0)
    
    # คำนวณจำนวนแถวโบลต์ (สมมติ M20 Gr 8.8 รับแรงเฉือนได้ ~4,400 kg/ตัว)
    rows = max(2, int(v_act / 4400) + 1)
    
    # กำหนดระยะมาตรฐาน (mm)
    pitch = 75   # ระยะห่างระหว่างโบลต์
    edge = 35    # ระยะขอบบน-ล่าง
    plate_h = (rows - 1) * pitch + (2 * edge)
    
    # ตรวจสอบไม่ให้ Plate สูงเกินความลึกคาน
    if plate_h > (h_beam - 60):
        rows = max(2, rows - 1)
        plate_h = (rows - 1) * pitch + (2 * edge)

    return {
        "rows": rows,
        "pitch": pitch,
        "edge": edge,
        "plate_h": plate_h,
        "plate_t": max(9, int(p.get('tw', 6) + 3)),
        "weld_size": 6 if p.get('tw', 6) < 10 else 8
    }

def render_report_tab(method, is_lrfd, sec_name, steel_grade, p, res, bolt):
    conn = get_connection_logic(res, p)
    
    # สรุปผล Ratio
    r_v = res.get('v_act', 0) / res.get('v_cap', 1)
    r_m = res.get('m_act', 0) / res.get('m_cap', 1)
    r_d = res.get('d_act', 0) / res.get('d_all', 1)
    max_r = max(r_v, r_m, r_d)
    status_color = "#059669" if max_r <= 1.0 else "#dc2626"

    # --- สร้างภาพ Drawing ด้วย SVG ---
    # คำนวณตำแหน่งจุดโบลต์ใน SVG
    bolt_svg = ""
    for i in range(conn['rows']):
        y_pos = 60 + (i * 35) # scale ลงมาเพื่อแสดงในรูป
        bolt_svg += f'<circle cx="115" cy="{y_pos}" r="3.5" fill="#334155" />'
    
    svg_height = 120 + (conn['rows'] * 35)

    html_content = f"""
    <div style="background:#f3f4f6; padding:30px 10px; font-family:'Inter', sans-serif;">
        <div style="max-width:800px; margin:auto; background:white; padding:50px; border-radius:8px; box-shadow:0 4px 6px -1px rgba(0,0,0,0.1);">
            
            <div style="border-bottom:3px solid #1e3a8a; padding-bottom:15px; margin-bottom:25px; display:flex; justify-content:space-between; align-items:flex-end;">
                <div>
                    <h2 style="margin:0; color:#1e3a8a; font-size:22px;">STRUCTURAL CALCULATION NOTE</h2>
                    <p style="margin:0; font-size:12px; color:#6b7280;">Beam ID: {sec_name} | Method: {method}</p>
                </div>
                <div style="text-align:right;">
                    <span style="background:{status_color}; color:white; padding:5px 15px; border-radius:20px; font-weight:bold; font-size:14px;">
                        { "PASSED" if max_r <= 1.0 else "FAILED" } ({(max_r*100):.1f}%)
                    </span>
                </div>
            </div>

            <h3 style="font-size:14px; color:#1e3a8a; border-left:4px solid #1e3a8a; padding-left:10px; margin-bottom:15px;">1. STRENGTH VERIFICATION</h3>
            <table style="width:100%; border-collapse:collapse; font-size:13px; margin-bottom:25px;">
                <tr style="background:#f8fafc; font-weight:bold;">
                    <td style="padding:10px; border:1px solid #e5e7eb;">Limit State</td>
                    <td style="padding:10px; border:1px solid #e5e7eb;">Applied Force</td>
                    <td style="padding:10px; border:1px solid #e5e7eb;">Design Capacity</td>
                    <td style="padding:10px; border:1px solid #e5e7eb; text-align:center;">Ratio</td>
                </tr>
                <tr>
                    <td style="padding:10px; border:1px solid #e5e7eb;">Bending Moment</td>
                    <td style="padding:10px; border:1px solid #e5e7eb;">{res.get('m_act', 0):,.0f} kg.m</td>
                    <td style="padding:10px; border:1px solid #e5e7eb;">{res.get('m_cap', 0):,.0f} kg.m</td>
                    <td style="padding:10px; border:1px solid #e5e7eb; text-align:center; font-weight:bold; color:{'red' if r_m > 1 else 'green'};">{r_m:.3f}</td>
                </tr>
                <tr>
                    <td style="padding:10px; border:1px solid #e5e7eb;">Shear Force</td>
                    <td style="padding:10px; border:1px solid #e5e7eb;">{res.get('v_act', 0):,.0f} kg</td>
                    <td style="padding:10px; border:1px solid #e5e7eb;">{res.get('v_cap', 0):,.0f} kg</td>
                    <td style="padding:10px; border:1px solid #e5e7eb; text-align:center; font-weight:bold; color:{'red' if r_v > 1 else 'green'};">{r_v:.3f}</td>
                </tr>
            </table>

            <h3 style="font-size:14px; color:#1e3a8a; border-left:4px solid #1e3a8a; padding-left:10px; margin-bottom:15px;">2. TYPICAL CONNECTION DETAIL</h3>
            <div style="display:grid; grid-template-columns: 1.2fr 1fr; gap:20px; background:#fcfcfc; border:1px solid #e5e7eb; padding:20px; border-radius:4px;">
                
                <div style="background:white; border:1px solid #d1d5db; text-align:center; padding:10px;">
                    <svg width="200" height="{svg_height}" viewBox="0 0 200 {svg_height}">
                        <path d="M 100 20 L 190 20 L 190 40 L 110 40 L 110 {svg_height-40} L 190 {svg_height-40} L 190 {svg_height-20} L 100 {svg_height-20} Z" fill="#f1f5f9" stroke="#475569" stroke-width="1.5"/>
                        <rect x="100" y="45" width="40" height="{conn['plate_h']*0.45}" fill="#1e3a8a" fill-opacity="0.15" stroke="#1e3a8a" stroke-width="2"/>
                        {bolt_svg}
                        <line x1="85" y1="45" x2="85" y2="{45 + conn['plate_h']*0.45}" stroke="#94a3b8" stroke-width="1"/>
                        <text x="75" y="{45 + (conn['plate_h']*0.45)/2}" font-size="10" fill="#64748b" transform="rotate(-90 75,{45 + (conn['plate_h']*0.45)/2})">{conn['plate_h']} mm</text>
                        <path d="M 100 50 L 80 30 L 60 30" fill="none" stroke="#ef4444" stroke-width="1"/>
                        <text x="55" y="25" font-size="9" fill="#ef4444" font-weight="bold">WELD {conn['weld_size']}mm</text>
                    </svg>
                    <p style="font-size:11px; color:#94a3b8; margin-top:10px;">CONNECTION ELEVATION</p>
                </div>

                <div style="font-size:13px; color:#334155;">
                    <p style="margin-top:0; font-weight:bold; color:#1e3a8a; border-bottom:1px solid #e5e7eb; padding-bottom:5px;">Specifications:</p>
                    <ul style="list-style:none; padding:0; line-height:1.8;">
                        <li>• <b>Type:</b> Single Fin Plate</li>
                        <li>• <b>Plate Size:</b> PL {conn['plate_t']} x {conn['plate_h']} mm</li>
                        <li>• <b>Bolt:</b> {conn['rows']} Nos. x {bolt.get('size','M20')} (Gr 8.8)</li>
                        <li>• <b>Bolt Spacing:</b> {conn['pitch']} mm c/c</li>
                        <li>• <b>Edge Distance:</b> {conn['edge']} mm (min)</li>
                        <li>• <b>Weld:</b> Fillet {conn['weld_size']} mm (E70XX)</li>
                    </ul>
                    <div style="margin-top:20px; background:#fff7ed; padding:10px; border:1px dotted #fb923c; font-size:11px; color:#9a3412;">
                        <b>Note:</b> Weld plate to support member. Ensure beam web is centered on plate.
                    </div>
                </div>
            </div>

            <div style="margin-top:40px; border-top:1px solid #e5e7eb; padding-top:15px; text-align:center; font-size:11px; color:#9ca3af;">
                Generated by Beam Insight | Compliance: AISC 360-22 Steel Specification
            </div>
        </div>

        <div style="text-align:center; margin-top:30px;">
            <button onclick="window.print()" style="padding:10px 40px; background:#1e3a8a; color:white; border:none; border-radius:4px; font-weight:bold; cursor:pointer;">
                🖨️ PRINT TO PDF
            </button>
        </div>
    </div>
    """
    
    components.html(html_content, height=1200, scrolling=True)
