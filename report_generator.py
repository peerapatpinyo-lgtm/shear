# report_generator.py
# Version: 11.0 (Auto-Connection Design & Bolt Count)
import streamlit as st
from datetime import datetime
import math

def render_report_tab(beam_data, conn_data):
    # --- 1. Control Panel ---
    st.markdown("### 🖨️ Engineering Report Generation")
    
    with st.expander("⚙️ Project Settings", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            project = st.text_input("Project Name", value="Warehouse Mezzanine Structure")
            client = st.text_input("Client / Owner", value="Siam Industrial Corp.")
        with c2:
            engineer = st.text_input("Designed By", value="Eng. Somchai (PE. Level III)")
            doc_ref = st.text_input("Document Ref.", value=f"STR-{datetime.now().strftime('%Y%m')}-001")

    if not beam_data:
        st.warning("⚠️ No analysis data found. Please run the calculation in Tab 1 first.")
        return

    # --- 2. Data Preparation ---
    sec = beam_data.get('sec_name', 'Unknown')
    span = beam_data.get('user_span', 0)
    fy = beam_data.get('Fy', 2500)
    
    # Loads
    m_act, m_cap = beam_data.get('m_act', 0), beam_data.get('mn', 0)
    v_act, v_cap = beam_data.get('v_act', 0), beam_data.get('vn', 0)
    d_act, d_all = beam_data.get('defl_act', 0), beam_data.get('defl_all', 0)
    
    # Ratios
    r_m, r_v, r_d = beam_data.get('ratio_m', 0), beam_data.get('ratio_v', 0), beam_data.get('ratio_d', 0)
    max_r = max(r_m, r_v, r_d)
    is_pass = max_r <= 1.0
    run_date = datetime.now().strftime("%d-%b-%Y")

    # ==========================================
    # 🔩 AUTO-CALCULATE BOLTS (NEW FEATURE!)
    # ==========================================
    # สมมติฐาน: ใช้ Bolt M20 Grade A325 (High Strength)
    # รับแรงเฉือนได้ประมาณ 7,500 kg/ตัว (Single Shear, Conservative)
    bolt_size = "M20"
    bolt_grade = "A325 / 8.8"
    bolt_shear_cap = 7500 # kg/bolt
    
    # คำนวณจำนวนน๊อต
    req_bolts = v_act / bolt_shear_cap
    num_bolts = math.ceil(req_bolts)
    
    # ขั้นต่ำต้องมี 2 ตัวเสมอเพื่อกันการหมุน
    if num_bolts < 2:
        num_bolts = 2
        
    # จัดเรียง (Pattern) อย่างง่าย
    rows = num_bolts
    cols = 1
    if num_bolts > 4: # ถ้าเกิน 4 ตัว ให้แบ่งเป็น 2 แถว
        cols = 2
        rows = math.ceil(num_bolts / 2)
        # ปรับจำนวนรวมให้ลงตัวกับแถว
        num_bolts = rows * cols 

    # ==========================================

    # --- 3. REPORT CANVAS ---
    st.markdown("---")
    with st.container(border=True):
        
        # HEADER
        st.markdown(f"""
        <div style="border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 20px;">
            <table style="width:100%; border:none;">
                <tr>
                    <td style="width:60%; vertical-align:top;">
                        <h2 style="margin:0; color:#1e3a8a;">STRUCTURAL CALCULATION SHEET</h2>
                        <span style="font-size:12px; color:#555;">REF: AISC 360-16 | LRFD METHOD</span>
                    </td>
                    <td style="width:40%; text-align:right; font-size:12px;">
                        <b>Doc No:</b> {doc_ref}<br><b>Date:</b> {run_date}
                    </td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"**PROJECT:** {project} | **CLIENT:** {client} | **ENGINEER:** {engineer}")
        st.markdown("---")

        # 1. SUMMARY RESULT
        if is_pass:
            st.markdown(f"""
            <div style="background:#f0fdf4; border:1px solid #166534; padding:10px; border-radius:5px; margin-bottom:15px;">
                <h3 style="color:#166534; margin:0;">✅ RESULT: PASSED (Ratio {max_r:.2f})</h3>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background:#fef2f2; border:1px solid #dc2626; padding:10px; border-radius:5px; margin-bottom:15px;">
                <h3 style="color:#dc2626; margin:0;">❌ RESULT: FAILED (Ratio {max_r:.2f})</h3>
            </div>""", unsafe_allow_html=True)

        # 2. ANALYSIS TABLE
        st.markdown("#### 1. ANALYSIS RESULTS")
        def r_row(name, dem, cap, unit, r):
             status = "✅" if r <= 1 else "❌"
             st.markdown(f"""
             <div style="display:flex; justify-content:space-between; border-bottom:1px dashed #ddd; padding:5px 0;">
                <div style="width:30%;"><b>{name}</b></div>
                <div style="width:20%;">{dem:,.0f} {unit}</div>
                <div style="width:20%;">{cap:,.0f} {unit}</div>
                <div style="width:15%;">R = {r:.2f}</div>
                <div style="width:10%; text-align:right;">{status}</div>
             </div>
             """, unsafe_allow_html=True)
        
        st.markdown(f"<div style='background:#eee; padding:5px; font-weight:bold; display:flex;'><div style='width:30%'>Item</div><div style='width:20%'>Demand</div><div style='width:20%'>Capacity</div><div style='width:15%'>Ratio</div><div style='width:10%; text-align:right;'>Result</div></div>", unsafe_allow_html=True)
        r_row("Moment", m_act, m_cap, "kg-m", max(beam_data.get('ratio_m',0),0))
        r_row("Shear", v_act, v_cap, "kg", max(beam_data.get('ratio_v',0),0))
        r_row("Deflection", d_act, d_all, "cm", max(beam_data.get('ratio_d',0),0))

        st.markdown("<br>", unsafe_allow_html=True)

        # 3. CONNECTION DESIGN (ส่วนที่เพิ่มใหม่!)
        st.markdown("#### 2. CONNECTION DESIGN (BOLT CALCULATION)")
        
        with st.container(border=True):
            c_bolt1, c_bolt2 = st.columns([1, 1])
            
            with c_bolt1:
                st.markdown("**🔩 Bolt Specification**")
                st.markdown(f"""
                - **Size:** {bolt_size} (Metric)
                - **Grade:** {bolt_grade}
                - **Shear Cap:** {bolt_shear_cap:,} kg/bolt
                - **Hole Type:** Standard
                """)
            
            with c_bolt2:
                st.markdown("**📐 Design Output**")
                st.markdown(f"""
                - Shear Force ($V_u$): **{v_act:,.0f} kg**
                - Calculation: ${v_act:,.0f} / {bolt_shear_cap:,}$
                - **REQUIRED BOLTS:** <span style='font-size:24px; color:#d97706; font-weight:bold;'>{num_bolts} PCS.</span>
                """, unsafe_allow_html=True)
                
        # แสดง Diagram จำลองการจัดเรียงน๊อต
        st.markdown("**Suggested Bolt Pattern (Pattern Layout):**")
        
        # สร้าง ASCII Art แบบง่ายๆ เพื่อโชว์ตำแหน่งน๊อต
        bolt_visual = ""
        for i in range(rows):
            line = "|"
            for j in range(cols):
                line += "  (+)  " # สัญลักษณ์หัวน๊อต
            line += "|\n"
            bolt_visual += line
        
        st.code(f"""
    PLATE / BEAM WEB
   +-----------------+
   |                 |
{bolt_visual}   |                 |
   +-----------------+
   Arrangement: {rows} Rows x {cols} Columns
        """, language="text")

        st.caption("*Note: This is a preliminary connection design based on shear capacity only. Please verify edge distance and plate thickness.")

        # FOOTER
        st.markdown("<br><br>__________________________<br>Signature / Approved By", unsafe_allow_html=True)
