# report_generator.py
# Version: 12.0 (Linked Data Edition - Pull from Tab 2)
import streamlit as st
from datetime import datetime
import math

def render_report_tab(beam_data, conn_data):
    # --- 1. Control Panel ---
    st.markdown("### 🖨️ Final Engineering Report")
    
    with st.expander("⚙️ Document Settings", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            project = st.text_input("Project Name", value="Warehouse Mezzanine Structure")
            client = st.text_input("Client", value="Siam Industrial Corp.")
        with c2:
            engineer = st.text_input("Engineer", value="Eng. Somchai (PE. Level III)")
            doc_ref = st.text_input("Ref No.", value=f"STR-{datetime.now().strftime('%Y%m')}-001")

    # --- Validation: Check Data Source ---
    if not beam_data:
        st.warning("⚠️ Warning: Beam Analysis data (Tab 1) is missing.")
        return
    
    # เช็คว่า Tab 2 คำนวณมาหรือยัง?
    if not conn_data or conn_data.get('status') != 'calculated':
        st.warning("⚠️ Warning: Connection Design data (Tab 2) is missing or not calculated yet.")
        st.info("Please go to Tab 2 and click 'Calculate Connection' first.")
        return

    # --- 2. Data Extraction (Pulling Real Data) ---
    # Beam Data (Tab 1)
    sec = beam_data.get('sec_name', '-')
    m_act = beam_data.get('m_act', 0)
    v_act = beam_data.get('v_act', 0) # แรงเฉือนที่เกิดขึ้นจริง
    max_r_beam = max(beam_data.get('ratio_m', 0), beam_data.get('ratio_v', 0))

    # Connection Data (Tab 2) - ดึงค่าจริงที่คำนวณแล้วมาเลย
    c_type = conn_data.get('type', 'Shear Connection')
    c_bolts = conn_data.get('bolt_qty', 0)       # จำนวนน๊อตจาก Tab 2
    c_dia = conn_data.get('bolt_size', '-')      # ขนาดน๊อต (M20)
    c_grade = conn_data.get('bolt_grade', '-')   # เกรด (A325)
    c_plate_t = conn_data.get('plate_thick', 0)  # ความหนาเพลท
    c_capacity = conn_data.get('capacity', 0)    # กำลังรับแรงของจุดต่อที่คำนวณได้
    
    # --- 3. Final Cross-Check Logic ---
    # ตรวจสอบว่า จุดต่อ (Tab 2) รับแรงจากคาน (Tab 1) ไหวไหม?
    # V_connection >= V_beam ?
    conn_ratio = v_act / c_capacity if c_capacity > 0 else 999
    is_conn_pass = conn_ratio <= 1.0
    
    # สรุปภาพรวม (Beam + Connection ต้องผ่านทั้งคู่)
    is_all_pass = (max_r_beam <= 1.0) and is_conn_pass
    run_date = datetime.now().strftime("%d-%b-%Y")

    # --- 4. REPORT CANVAS ---
    st.markdown("---")
    with st.container(border=True):
        
        # HEADER
        st.markdown(f"""
        <div style="border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 20px;">
            <table style="width:100%;">
                <tr>
                    <td style="width:70%;">
                        <h2 style="margin:0; color:#1e3a8a;">STRUCTURAL CALCULATION SHEET</h2>
                        <span style="font-size:12px; color:#555;">REF: AISC 360-16 | LRFD METHOD</span>
                    </td>
                    <td style="width:30%; text-align:right; font-size:12px;">
                        <b>Doc No:</b> {doc_ref}<br><b>Date:</b> {run_date}
                    </td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"**PROJECT:** {project} | **ENGINEER:** {engineer}")
        st.divider()

        # PART 1: BEAM CHECK SUMMARY
        st.markdown("#### 1. BEAM ANALYSIS RESULT (FROM TAB 1)")
        c_b1, c_b2, c_b3 = st.columns(3)
        c_b1.metric("Beam Section", sec)
        c_b2.metric("Shear Force ($V_u$)", f"{v_act:,.0f} kg")
        c_b3.metric("Beam Status", "✅ PASS" if max_r_beam<=1 else "❌ FAIL")
        
        st.divider()

        # PART 2: CONNECTION CHECK (LINKED DATA)
        st.markdown("#### 2. CONNECTION DESIGN VERIFICATION (FROM TAB 2)")
        
        # แสดงข้อมูลที่ดึงมาจาก Tab 2
        with st.container(border=True):
            col_spec, col_verify = st.columns([1.2, 1])
            
            with col_spec:
                st.markdown("**🔹 DESIGN SPECIFICATION**")
                st.markdown(f"**Type:** {c_type}")
                st.markdown(f"""
                - **Bolt Size:** {c_dia}
                - **Bolt Grade:** {c_grade}
                - **Total Bolts:** <span style='font-size:20px; font-weight:bold; color:#1e3a8a;'>{c_bolts} pcs.</span>
                - **Plate Thickness:** {c_plate_t} mm
                """, unsafe_allow_html=True)
            
            with col_verify:
                st.markdown("**🔹 CAPACITY CHECK**")
                st.write(f"Demand ($V_u$ from Beam): **{v_act:,.0f} kg**")
                st.write(f"Capacity ($\phi R_n$ from Conn): **{c_capacity:,.0f} kg**")
                
                # Check Ratio
                if is_conn_pass:
                    st.markdown(f"""
                    <div style="background:#dcfce7; color:#166534; padding:8px; border-radius:4px; text-align:center; margin-top:10px;">
                        <b>✅ OK (Ratio {conn_ratio:.2f})</b>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background:#fee2e2; color:#991b1b; padding:8px; border-radius:4px; text-align:center; margin-top:10px;">
                        <b>❌ INSUFFICIENT (Ratio {conn_ratio:.2f})</b>
                    </div>""", unsafe_allow_html=True)

        # PART 3: DRAWING / PATTERN VISUALIZATION
        st.markdown("**🔹 BOLT ARRANGEMENT (CONCEPTUAL)**")
        # Generate Visualization based on Real Bolt Count
        try:
            qty = int(c_bolts)
            cols = 2 if qty >= 4 else 1
            rows = math.ceil(qty / cols)
            
            bolt_viz = ""
            for r in range(rows):
                line = "|"
                for c in range(cols):
                    if (r * cols + c) < qty:
                        line += "  (X)  " # Bolt
                    else:
                        line += "       " # Empty
                line += "|\n"
                bolt_viz += line
            
            st.code(f"   [TOP]\n   +-------+\n{bolt_viz}   +-------+", language="text")
        except:
            st.caption("Cannot visualize pattern (Invalid bolt quantity)")

        # FINAL CONCLUSION
        st.markdown("---")
        if is_all_pass:
             st.success("##### ✅ FINAL CONCLUSION: APPROVED FOR CONSTRUCTION")
        else:
             st.error("##### ❌ FINAL CONCLUSION: REVISE DESIGN (Check Beam or Connection Capacity)")
             
        # SIGNATURE
        st.markdown("<br><br><br>__________________________<br>Professional Engineer Signature", unsafe_allow_html=True)
