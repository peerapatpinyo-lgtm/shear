# tab_summary.py
import streamlit as st
import plotly.graph_objects as go

def render(data):
    st.subheader(f"🏁 Governing Analysis: {data['gov_cause']}")
    
    # --- 1. เตรียมตัวแปรและหน่วย ---
    # ตรวจสอบ Load ตามโหมดที่ใช้งาน
    w_to_use = data['w_load'] if data['is_check_mode'] else data['w_safe']
    w_kgcm = w_to_use / 100  # แปลง kg/m เป็น kg/cm
    
    L_m = data['user_span']
    L_cm = L_m * 100
    E = data['E']       # 2,040,000 kg/cm²
    Ix = data['Ix']     # cm⁴
    
    # --- 2. ส่วนแสดงวิธีทำแบบละเอียด ---
    with st.container(border=True):
        st.markdown("### 📝 รายละเอียดการคำนวณการแอ่นตัว (Deflection Trace)")
        
        # กางสูตรมาตรฐาน
        st.markdown("**1. สูตรคำนวณมาตรฐาน (Simple Span, UDL):**")
        st.latex(r"\Delta_{act} = \frac{5 \cdot w \cdot L^4}{384 \cdot E \cdot I_x}")
        
        # แสดงรายการตัวแปรพร้อมหน่วย
        st.markdown("**2. รายการตัวแปรที่ใช้ (Input Variables):**")
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            st.markdown(f"""
            - $w$ = `{w_kgcm:.4f}` kg/cm
            - $L$ = `{L_cm:,.0f}` cm
            """)
        with col_v2:
            st.markdown(f"""
            - $E$ = `{E:,.0f}` kg/cm²
            - $I_x$ = `{Ix:,.2f}` cm⁴
            """)

        # แสดงการแทนค่าแบบมีหน่วยกำกับ
        st.markdown("**3. การแทนค่าลงในสมการ (Substitution with Units):**")
        
        # ใช้ LaTeX แสดงการแทนค่าพร้อมหน่วย
        formula_with_units = rf"""
        \Delta_{{act}} = \frac{{5 \cdot ({w_kgcm:.4f} \text{{ kg/cm}}) \cdot ({L_cm:,.0f} \text{{ cm}})^4}}{{384 \cdot ({E:,.0f} \text{{ kg/cm}}^2) \cdot ({Ix:,.2f} \text{{ cm}}^4)}}
        """
        st.latex(formula_with_units)

        # สรุปผลลัพธ์การตัดหน่วย
        st.markdown("**4. ผลลัพธ์สุดท้าย (Final Result):**")
        d_act = data['d_act']
        d_all = data['d_allow']
        
        # แสดงผลลัพธ์การคำนวณ
        st.markdown(f"""
        <div style="background-color: #f8fafc; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0;">
            <table style="width:100%">
                <tr>
                    <td><b>Actual Deflection ($\Delta_{{act}}$):</b></td>
                    <td style="text-align:right; color:#2563eb; font-size:1.2em;"><b>{d_act:.3f} cm</b></td>
                </tr>
                <tr>
                    <td><b>Allowable Deflection ($\Delta_{{all}}$):</b></td>
                    <td style="text-align:right;">{d_all:.3f} cm (L/{data['defl_denom']})</td>
                </tr>
                <tr style="border-top: 1px solid #cbd5e1;">
                    <td><b>Utilization Ratio:</b></td>
                    <td style="text-align:right; font-weight:bold;">{data['ratio_d']:.2%}</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    # --- 3. การตรวจสอบความแข็งแรง (Moment Check) ---
    with st.expander("⚖️ ตรวจสอบค่าโมเมนต์ดัด (Moment Check Detail)"):
        st.markdown("**การแทนค่าโมเมนต์:**")
        st.latex(rf"M_{{max}} = \frac{{w \cdot L^2}}{{8}} = \frac{{{w_to_use:,.2f} \text{{ kg/m}} \cdot ({L_m} \text{{ m}})^2}}{{8}}")
        st.latex(rf"M_{{act}} = {data['m_act']:,.2f} \text{{ kg-m}}")
        st.write(f"Capacity ($M_{{cap}}$) = **{data['M_cap']:,.2f} kg-m**")

    # --- 4. กราฟเปรียบเทียบ Utilization ---
    st.divider()
    ratios = [data['ratio_v'], data['ratio_m'], data['ratio_d']]
    labels = ['Shear (V)', 'Moment (M)', 'Deflection (Δ)']
    
    fig = go.Figure(go.Bar(
        x=labels, y=ratios,
        marker_color=['#3b82f6' if r <= 1.0 else '#ef4444' for r in ratios],
        text=[f"{r:.1%}" for r in ratios],
        textposition='outside'
    ))
    fig.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="Limit")
    fig.update_layout(yaxis_range=[0, max(max(ratios)*1.3, 1.2)], template="simple_white")
    st.plotly_chart(fig, use_container_width=True)
