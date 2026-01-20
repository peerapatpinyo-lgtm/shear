# report_generator.py
# Version: 13.0 (Bulletproof - Works with or without Tab 2)
import streamlit as st
from datetime import datetime
import math

def render_report_tab(beam_data, conn_data):
    # --- 1. ส่วนตั้งค่า (Header Input) ---
    st.markdown("### 🖨️ Engineering Report")
    
    with st.expander("⚙️ ตั้งค่าหัวกระดาษ (Document Settings)", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            project = st.text_input("ชื่อโครงการ", value="โครงการก่อสร้างชั้นลอย (Mezzanine Project)")
            client = st.text_input("เจ้าของงาน", value="บจก. สยามอินดัสเทรียล")
        with c2:
            engineer = st.text_input("วิศวกร", value="นายสมชาย ใจดี (สย. 12345)")
            doc_ref = st.text_input("เลขที่เอกสาร", value=f"CALC-{datetime.now().strftime('%y%m')}-001")

    # --- 2. ตรวจสอบข้อมูลจาก Tab 1 (Beam) ---
    if not beam_data:
        st.error("⚠️ ไม่พบข้อมูลการคำนวณคาน (กรุณากดคำนวณที่ Tab 1 ก่อน)")
        return

    # ดึงค่าแรงจากคาน (Tab 1)
    sec = beam_data.get('sec_name', 'Unknown Section')
    v_act = beam_data.get('v_act', 0)     # แรงเฉือนที่เกิดขึ้นจริง (Demand)
    m_act = beam_data.get('m_act', 0)
    
    # ดึงค่า Capacity ของคาน
    v_cap = beam_data.get('vn', 0)
    m_cap = beam_data.get('mn', 0)
    
    # Ratio ของคาน
    r_v = beam_data.get('ratio_v', 0)
    r_m = beam_data.get('ratio_m', 0)
    r_d = beam_data.get('ratio_d', 0)
    
    is_beam_pass = max(r_v, r_m, r_d) <= 1.0

    # --- 3. จัดการข้อมูลจุดต่อ (Connection Logic) ---
    # ถ้าไม่มีข้อมูลจาก Tab 2 ให้คำนวณสดๆ ตรงนี้เลย (Fallback Mode)
    
    use_auto_calc = False
    
    if not conn_data or conn_data.get('status') != 'calculated':
        # --- โหมดคำนวณเอง (Auto-Design) ---
        use_auto_calc = True
        bolt_grade = "A325 (Auto)"
        bolt_size = "M20"
        bolt_shear_cap = 7400 # kg/bolt (โดยประมาณ)
        
        # คำนวณจำนวนน๊อตที่ต้องใช้รับ v_act
        req_bolts = v_act / bolt_shear_cap
        final_bolts = max(2, math.ceil(req_bolts)) # ขั้นต่ำ 2 ตัว
        
        conn_cap = final_bolts * bolt_shear_cap
        plate_t = 10 # mm (สมมติมาตรฐาน)
        
        conn_msg = "⚠️ Auto-Calculated (Based on Beam Shear)"
        
    else:
        # --- โหมดดึงข้อมูลจาก Tab 2 (Linked Data) ---
        bolt_grade = conn_data.get('bolt_grade', 'A325')
        bolt_size = conn_data.get('bolt_size', 'M20')
        final_bolts = conn_data.get('bolt_qty', 0)
        conn_cap = conn_data.get('capacity', 0)
        plate_t = conn_data.get('plate_thick', 0)
        conn_msg = "✅ Verified Design (From Tab 2)"

    # คำนวณ Ratio ของจุดต่อ
    conn_ratio = v_act / conn_cap if conn_cap > 0 else 999
    is_conn_pass = conn_ratio <= 1.0
    
    # สรุปภาพรวม
    final_pass = is_beam_pass and is_conn_pass
    run_date = datetime.now().strftime("%d-%b-%Y")

    # --- 4. แสดงผลรายงาน (Report Canvas) ---
    st.markdown("---")
    
    # กรอบจำลอง A4
    with st.container(border=True):
        
        # === HEADER ===
        st.markdown(f"""
        <div style="border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 15px;">
            <h2 style="margin:0; color:#1e3a8a;">รายการคำนวณโครงสร้าง (Structural Report)</h2>
            <span style="font-size:12px; color:#555;">REF STANDARD: AISC 360-16 (LRFD)</span>
        </div>
        """, unsafe_allow_html=True)
        
        c_h1, c_h2 = st.columns([2, 1])
        with c_h1:
            st.write(f"**PROJECT:** {project}")
            st.write(f"**OWNER:** {client}")
            st.write(f"**ENGINEER:** {engineer}")
        with c_h2:
            st.write(f"**DOC NO:** {doc_ref}")
            st.write(f"**DATE:** {run_date}")
            
        st.markdown("---")

        # === PART 1: BEAM CHECK ===
        st.markdown("#### 1. ผลการตรวจสอบคานเหล็ก (Beam Analysis)")
        st.info(f"หน้าตัด: **{sec}** | Span: {beam_data.get('user_span',0)} m.")

        # Table Header
        cols = st.columns([2, 1.5, 1.5, 1, 1])
        headers = ["Item", "Demand", "Capacity", "Ratio", "Result"]
        for col, h in zip(cols, headers):
            col.markdown(f"**{h}**")
        st.divider()

        # Rows
        def show_row(label, dem, cap, unit, ratio):
            c1, c2, c3, c4, c5 = st.columns([2, 1.5, 1.5, 1, 1])
            c1.write(label)
            c2.write(f"{dem:,.0f} {unit}")
            c3.write(f"{cap:,.0f} {unit}")
            c4.write(f"{ratio:.2f}")
            c5.write("✅ OK" if ratio<=1 else "❌ NG")

        show_row("Moment (แรงดัด)", m_act, m_cap, "kg-m", r_m)
        show_row("Shear (แรงเฉือน)", v_act, v_cap, "kg", r_v)
        show_row("Deflection (ระยะแอ่น)", beam_data.get('defl_act',0), beam_data.get('defl_all',0), "cm", r_d)

        # === PART 2: CONNECTION DESIGN ===
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 2. รายละเอียดจุดต่อ (Connection Detail)")
        
        # แสดงสถานะข้อมูล
        if use_auto_calc:
            st.caption(f"ℹ️ หมายเหตุ: {conn_msg} (เนื่องจากยังไม่ได้คำนวณที่ Tab 2 ระบบจึงคำนวณให้อัตโนมัติ)")
        else:
            st.caption(f"ℹ️ แหล่งข้อมูล: {conn_msg}")

        with st.container(border=True):
            col_d1, col_d2 = st.columns(2)
            
            with col_d1:
                st.markdown("**📝 Specification:**")
                st.write(f"- Bolt Size: **{bolt_size}**")
                st.write(f"- Grade: **{bolt_grade}**")
                st.write(f"- Plate Thickness: **{plate_t} mm**")
                
            with col_d2:
                st.markdown("**🧮 Calculation:**")
                st.write(f"- Shear Force ($V_u$): {v_act:,.0f} kg")
                st.markdown(f"- **Required Bolts:** `{final_bolts}` **pcs.**")
                
                # Visual Check
                status_color = "green" if is_conn_pass else "red"
                status_text = "PASSED" if is_conn_pass else "FAILED"
                st.markdown(f"<span style='color:{status_color}; font-weight:bold;'>Verification: {status_text} (Ratio {conn_ratio:.2f})</span>", unsafe_allow_html=True)

        # === PART 3: BOLT PATTERN VISUALIZATION ===
        st.markdown("**🔹 แบบร่างการจัดเรียงน๊อต (Conceptual Pattern)**")
        
        # Logic วาดรูป ASCII
        try:
            qty = int(final_bolts)
            n_cols = 2 if qty >= 4 else 1
            n_rows = math.ceil(qty / n_cols)
            
            drawing = ""
            for r in range(n_rows):
                line = "   |"
                for c in range(n_cols):
                    if (r * n_cols + c) < qty:
                        line += "  (⊕)  " # Bolt Symbol
                    else:
                        line += "       "
                line += "|   \n"
                drawing += line
            
            st.code(f"""
    [ BEAM WEB / PLATE ]
   +-------------------+
{drawing}   +-------------------+
    Total: {qty} Bolts ({n_rows} Rows x {n_cols} Cols)
            """, language="text")
        except:
            st.write("-")

        # === FOOTER ===
        st.markdown("---")
        if final_pass:
            st.success("##### ✅ สรุปผล: โครงสร้างและจุดต่อ ผ่านเกณฑ์มาตรฐาน (APPROVED)")
        else:
            st.error("##### ❌ สรุปผล: ไม่ผ่านเกณฑ์ กรุณาตรวจสอบขนาดหน้าตัดหรือจุดต่อ (REVISE REQUIRED)")
            
        st.write("")
        col_s1, col_s2 = st.columns(2)
        col_s1.markdown("..................................................<br>ผู้ออกแบบ (Engineer)", unsafe_allow_html=True)
        col_s2.markdown("..................................................<br>ผู้ตรวจสอบ (Approver)", unsafe_allow_html=True)
