# report_generator.py (V13 - Fixed Version)
import streamlit as st
import streamlit.components.v1 as components

def render_report_tab(method, is_lrfd, sec_name, steel_grade, p, res, bolt):
    """
    ฟังก์ชันสร้างรายงาน โดยแก้ปัญหา ValueError จากการสลับประเภทข้อมูล
    steel_grade: รับค่าเป็น String (ชื่อเกรด)
    """
    # ดึงค่า Fy จากการคำนวณมาแสดงผล (ถ้ามี) หรือใช้ค่าจากที่คำนวณใน res
    # เราจะใช้ค่าที่ส่งผ่านมาแสดงใน Report
    
    w_safe = res.get('w_safe', 0)
    cause = res.get('cause', 'N/A')
    v_act = res.get('v_act', 0)
    v_cap = res.get('v_cap', 1)
    m_act = res.get('m_act', 0)
    m_cap = res.get('m_cap', 1)
    d_act = res.get('d_act', 0)
    d_all = res.get('d_all', 1)

    html_content = f"""<div style="background-color:#ffffff;padding:30px;border-radius:10px;border:1px solid #d1d5db;font-family:sans-serif;color:#111827;">
<div style="border-bottom:2px solid #1e40af;margin-bottom:20px;padding-bottom:10px;">
<h2 style="margin:0;color:#1e40af;">DESIGN CALCULATION REPORT</h2>
<p style="margin:0;font-size:14px;color:#6b7280;">Steel Beam Verification | Method: {method}</p>
</div>

<div style="margin-bottom:20px;">
<h4 style="color:#1e40af;margin-bottom:10px;">1. Section & Material Properties</h4>
<table style="width:100%;border-collapse:collapse;font-size:14px;">
<tr><td style="padding:8px;background:#f3f4f6;font-weight:bold;border:1px solid #e5e7eb;width:30%;">Selected Section:</td><td style="padding:8px;border:1px solid #e5e7eb;">{sec_name}</td></tr>
<tr><td style="padding:8px;background:#f3f4f6;font-weight:bold;border:1px solid #e5e7eb;">Steel Grade:</td><td style="padding:8px;border:1px solid #e5e7eb;">{steel_grade}</td></tr>
<tr><td style="padding:8px;background:#f3f4f6;font-weight:bold;border:1px solid #e5e7eb;">Governing Load:</td><td style="padding:8px;border:1px solid #e5e7eb;color:#dc2626;font-weight:bold;font-size:16px;">{w_safe:,.0f} kg/m</td></tr>
<tr><td style="padding:8px;background:#f3f4f6;font-weight:bold;border:1px solid #e5e7eb;">Failure Mode:</td><td style="padding:8px;border:1px solid #e5e7eb;font-weight:bold;">{cause}</td></tr>
</table>
</div>

<h4 style="color:#1e40af;margin-bottom:10px;">2. Capacity Check Details</h4>
<table style="width:100%;border-collapse:collapse;text-align:center;font-size:14px;margin-bottom:20px;">
<thead><tr style="background:#1e40af;color:white;"><th style="padding:10px;border:1px solid #e5e7eb;">Check Item</th><th style="padding:10px;border:1px solid #e5e7eb;">Actual Demand</th><th style="padding:10px;border:1px solid #e5e7eb;">Design Capacity</th><th style="padding:10px;border:1px solid #e5e7eb;">Ratio</th></tr></thead>
<tbody>
<tr><td style="padding:10px;border:1px solid #e5e7eb;text-align:left;">Shear Strength</td><td style="padding:10px;border:1px solid #e5e7eb;">{v_act:,.0f} kg</td><td style="padding:10px;border:1px solid #e5e7eb;">{v_cap:,.0f} kg</td><td style="padding:10px;border:1px solid #e5e7eb;font-weight:bold;">{(v_act/v_cap):.3f}</td></tr>
<tr><td style="padding:10px;border:1px solid #e5e7eb;text-align:left;">Moment Resistance</td><td style="padding:10px;border:1px solid #e5e7eb;">{m_act:,.0f} kg.m</td><td style="padding:10px;border:1px solid #e5e7eb;">{m_cap/100:,.0f} kg.m</td><td style="padding:10px;border:1px solid #e5e7eb;font-weight:bold;">{(m_act/(m_cap/100)):.3f}</td></tr>
<tr><td style="padding:10px;border:1px solid #e5e7eb;text-align:left;">Deflection</td><td style="padding:10px;border:1px solid #e5e7eb;">{d_act:.3f} cm</td><td style="padding:10px;border:1px solid #e5e7eb;">{d_all:.3f} cm</td><td style="padding:10px;border:1px solid #e5e7eb;font-weight:bold;">{(d_act/d_all):.3f}</td></tr>
</tbody></table>

<h4 style="color:#1e40af;margin-bottom:10px;">3. Connection: {bolt.get('type', 'N/A')}</h4>
<table style="width:100%;border-collapse:collapse;font-size:14px;">
<tr><td style="padding:8px;background:#f3f4f6;font-weight:bold;border:1px solid #e5e7eb;width:30%;">Bolt Grade & Size:</td><td style="padding:8px;border:1px solid #e5e7eb;">{bolt.get('grade', 'N/A')} - {bolt.get('size', 'N/A')}</td></tr>
<tr><td style="padding:8px;background:#f3f4f6;font-weight:bold;border:1px solid #e5e7eb;">Quantity:</td><td style="padding:8px;border:1px solid #e5e7eb;">{bolt.get('qty', 0)} Nos.</td></tr>
</table>
</div>"""

    components.html(html_content, height=800, scrolling=True)
