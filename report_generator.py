# report_generator.py
# Version: 10.0 (The Ultimate Professional Edition - World Class Standard)
import streamlit as st
from datetime import datetime

def render_report_tab(beam_data, conn_data):
    # --- 1. Control Panel (Input) ---
    st.markdown("### 🖨️ Engineering Report Generation")
    st.caption("Generate professional structural calculation sheets compliant with AISC 360-16.")
    
    with st.expander("⚙️ Project & Document Settings", expanded=False):
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
    # Member Data
    sec = beam_data.get('sec_name', 'Unknown Section')
    span = beam_data.get('user_span', 0)
    fy = beam_data.get('Fy', 2500)
    grade = beam_data.get('grade', 'SS400/A36')
    
    # Analysis Data
    m_act, m_cap = beam_data.get('m_act', 0), beam_data.get('mn', 0)
    v_act, v_cap = beam_data.get('v_act', 0), beam_data.get('vn', 0)
    d_act, d_all = beam_data.get('defl_act', 0), beam_data.get('defl_all', 0)
    
    # Ratios
    r_m = beam_data.get('ratio_m', 0)
    r_v = beam_data.get('ratio_v', 0)
    r_d = beam_data.get('ratio_d', 0)
    max_r = max(r_m, r_v, r_d)
    is_pass = max_r <= 1.0

    # Connection Data
    conn_type = conn_data.get('type', 'Not Specified')
    conn_summ = conn_data.get('summary', 'Pending Design')

    # Date
    run_date = datetime.now().strftime("%d-%b-%Y")

    # --- 3. THE REPORT CANVAS (A4 Simulation) ---
    st.markdown("---")
    
    # ใช้ Container แบบมีขอบ เพื่อจำลองกระดาษ
    with st.container(border=True):
        
        # ================= HEADER BLOCK =================
        # Header Layout: Logo/Title | Project Info
        st.markdown(f"""
        <div style="border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 20px;">
            <table style="width:100%; border:none;">
                <tr>
                    <td style="width:60%; vertical-align:top;">
                        <h2 style="margin:0; color:#1e3a8a; font-family:'Helvetica', sans-serif;">STRUCTURAL CALCULATION SHEET</h2>
                        <span style="font-size:12px; color:#555;">REF STANDARD: AISC 360-16 (LRFD METHOD)</span>
                    </td>
                    <td style="width:40%; font-size:12px; text-align:right; color:#333;">
                        <b>Ref No:</b> {doc_ref}<br>
                        <b>Date:</b> {run_date}<br>
                        <b>Page:</b> 1 OF 1
                    </td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

        # ================= PROJECT INFO =================
        st.markdown(f"""
        **PROJECT:** {project}  
        **CLIENT:** {client}  
        **ENGINEER:** {engineer}
        """)
        st.markdown("---")

        # ================= SECTION 1: DESIGN BASIS & MATERIAL =================
        st.markdown("#### 1. DESIGN BASIS & PROPERTIES")
        
        col_mat1, col_mat2, col_mat3 = st.columns(3)
        with col_mat1:
            st.markdown("**BEAM PROFILE**")
            st.info(f"**{sec}**")
            st.caption("Hot Rolled Structural Steel")
        
        with col_mat2:
            st.markdown("**MATERIAL SPECS**")
            st.markdown(f"""
            - Grade: **{grade}**
            - Yield ($F_y$): {fy:,} ksc
            - Modulus ($E$): 2.04 x $10^6$ ksc
            """)
            
        with col_mat3:
            st.markdown("**GEOMETRY**")
            st.markdown(f"""
            - Span ($L$): {span:.2f} m
            - Unbraced Length ($L_b$): {beam_data.get('Lb', 0):.2f} m
            - Service Class: Floor Beam
            """)

        # ================= SECTION 2: MEMBER CAPACITY CHECK =================
        st.markdown("#### 2. MEMBER CAPACITY CHECK (D/C RATIO)")
        
        # Helper Style for Result Box
        def result_badge(ratio):
            color = "#dcfce7" if ratio <= 1.0 else "#fee2e2" # green-100 / red-100
            text_color = "#166534" if ratio <= 1.0 else "#991b1b"
            status = "OK" if ratio <= 1.0 else "N.G."
            return f"""
            <div style="background-color:{color}; color:{text_color}; padding:5px; border-radius:4px; text-align:center; font-weight:bold; font-size:14px;">
                {ratio:.2f} ({status})
            </div>
            """

        # Table Header
        c_h1, c_h2, c_h3, c_h4 = st.columns([2, 1.5, 1.5, 1])
        c_h1.markdown("**CHECK ITEM**")
        c_h2.markdown("**DEMAND ($U$)**")
        c_h3.markdown("**CAPACITY ($\phi R_n$)**")
        c_h4.markdown("**RATIO**")
        st.divider()

        # 2.1 Moment
        c_r1_1, c_r1_2, c_r1_3, c_r1_4 = st.columns([2, 1.5, 1.5, 1])
        c_r1_1.markdown("**(1) FLEXURAL STRENGTH**\n<span style='font-size:12px; color:#666'>Limit State: Yielding / LTB</span>", unsafe_allow_html=True)
        c_r1_2.markdown(f"$M_u$ = {m_act:,.0f} kg-m")
        c_r1_3.markdown(f"$\phi M_n$ = {m_cap:,.0f} kg-m")
        c_r1_4.markdown(result_badge(r_m), unsafe_allow_html=True)

        # 2.2 Shear
        c_r2_1, c_r2_2, c_r2_3, c_r2_4 = st.columns([2, 1.5, 1.5, 1])
        c_r2_1.markdown("**(2) SHEAR STRENGTH**\n<span style='font-size:12px; color:#666'>Limit State: Shear Yielding</span>", unsafe_allow_html=True)
        c_r2_2.markdown(f"$V_u$ = {v_act:,.0f} kg")
        c_r2_3.markdown(f"$\phi V_n$ = {v_cap:,.0f} kg")
        c_r2_4.markdown(result_badge(r_v), unsafe_allow_html=True)

        # 2.3 Deflection
        c_r3_1, c_r3_2, c_r3_3, c_r3_4 = st.columns([2, 1.5, 1.5, 1])
        c_r3_1.markdown("**(3) SERVICEABILITY**\n<span style='font-size:12px; color:#666'>Limit: L/360 or user defined</span>", unsafe_allow_html=True)
        c_r3_2.markdown(f"$\Delta_{{act}}$ = {d_act:.2f} cm")
        c_r3_3.markdown(f"$\Delta_{{all}}$ = {d_all:.2f} cm")
        c_r3_4.markdown(result_badge(r_d), unsafe_allow_html=True)

        # ================= SECTION 3: CONNECTION SPECIFICATION =================
        st.markdown("#### 3. CONNECTION DETAILS & NOTES")
        
        with st.container(border=True):
            col_conn1, col_conn2 = st.columns([1, 2])
            
            with col_conn1:
                st.markdown("**CONNECTION TYPE**")
                st.markdown(f"### {conn_type}")
                st.caption("Design Method: AISC Manual Part 10")
            
            with col_conn2:
                st.markdown("**SPECIFICATIONS (ข้อกำหนดประกอบแบบ)**")
                # แสดงเป็น Bullet ที่ดูสะอาด
                st.markdown(f"""
                * **Fasteners:** High Strength Bolts ASTM A325 / Grade 8.8
                * **Welding:** E70xx Electrode, Min. 6mm Fillet Weld (unless noted otherwise)
                * **Surface Prep:** SSPC-SP2 (Hand Tool Cleaning)
                * **Painting:** Rust-preventive primer 2 coats (Min. DFT 80 microns)
                * **Remarks:** {conn_summ}
                """)

        # ================= SECTION 4: FINAL CONCLUSION =================
        st.markdown("<br>", unsafe_allow_html=True)
        
        if is_pass:
            # Professional Box for PASSED
            st.markdown(f"""
            <div style="border: 2px solid #166534; background-color: #f0fdf4; padding: 15px; border-radius: 5px;">
                <h3 style="color: #166534; margin:0;">✅ CALCULATION RESULT: PASSED</h3>
                <p style="margin:5px 0 0 0;">The structural member <b>PASSES</b> all design checks according to AISC 360-16. 
                Maximum Utilization Ratio = <b>{max_r:.2f}</b></p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Professional Box for FAILED
            st.markdown(f"""
            <div style="border: 2px solid #dc2626; background-color: #fef2f2; padding: 15px; border-radius: 5px;">
                <h3 style="color: #dc2626; margin:0;">❌ CALCULATION RESULT: FAILED</h3>
                <p style="margin:5px 0 0 0;">The structural member <b>DOES NOT MEET</b> the design requirements. 
                Please revise the section size or span length.</p>
            </div>
            """, unsafe_allow_html=True)

        # ================= FOOTER & SIGNATURE =================
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        
        # Signature Block
        sig_c1, sig_c2, sig_c3 = st.columns(3)
        with sig_c1:
            st.markdown("_______________________")
            st.markdown(f"**{engineer}**")
            st.caption("Structural Engineer")
        
        with sig_c2:
            st.markdown("_______________________")
            st.markdown(f"**{client}**")
            st.caption("Owner / Client")
            
        with sig_c3:
            st.markdown("_______________________")
            st.markdown("**Approver**")
            st.caption("Professional Engineer (PE)")

        # Disclaimer
        st.markdown("---")
        st.caption("Disclaimer: This report is computer-generated by Structural Insight Engine. The engineer of record must verify all input data and results before construction.")
