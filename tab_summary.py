# tab_summary.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

def render(data):
    # --- 1. การกางวิธีทำแบบมีหน่วย (คงเดิมจากที่คุยกัน) ---
    st.subheader(f"🏁 Governing Analysis: {data['gov_cause']}")
    
    # ดึงค่าพื้นฐาน
    w_fixed = data['w_load'] if data['is_check_mode'] else data['w_safe']
    E = data['E']
    Ix = data['Ix']
    M_cap = data['M_cap']
    V_cap = data['V_cap']
    defl_limit_denom = data['defl_denom']

    # --- 2. สร้างตารางวิเคราะห์ความไว (Sensitivity Analysis Table) ---
    st.markdown("### 📊 ตารางวิเคราะห์ผลกระทบของระยะ Span (Span Sensitivity)")
    st.write("ตารางนี้แสดงให้เห็นว่าเมื่อระยะ Span เปลี่ยนไป ตัวแปรไหนจะเริ่มวิกฤตก่อนกัน (คำนวณที่ Load คงที่)")

    span_scenarios = [2.0, 4.0, 6.0, 8.0, 10.0, 12.0]
    # แทรกระยะปัจจุบันเข้าไปในตารางด้วยเพื่อให้เทียบง่าย
    if data['user_span'] not in span_scenarios:
        span_scenarios.append(data['user_span'])
    span_scenarios.sort()

    rows = []
    for s in span_scenarios:
        # คำนวณ Moment Ratio
        m_act = (w_fixed * s**2) / 8
        r_m = m_act / M_cap
        
        # คำนวณ Deflection Ratio
        # Δ_act = (5 * (w/100) * (s*100)^4) / (384 * E * Ix)
        d_act = (5 * (w_fixed/100) * (s*100)**4) / (384 * E * Ix)
        d_all = (s * 100) / defl_limit_denom
        r_d = d_act / d_all
        
        # Determine Governing
        gov = "Moment" if r_m > r_d else "Deflection"
        status = "🔴 FAIL" if max(r_m, r_d) > 1.0 else "🟢 PASS"
        
        rows.append({
            "Span (m)": f"{s:.2f} m",
            "Moment Ratio": f"{r_m:.2%}",
            "Deflection Ratio": f"{r_d:.2%}",
            "Governing Criteria": gov,
            "Status": status
        })

    df = pd.DataFrame(rows)
    
    # แสดงตารางพร้อมการไฮไลท์แถวปัจจุบัน
    st.table(df)

    st.info("""
    **💡 วิธีอ่านตาราง:** จะสังเกตได้ว่าเมื่อ Span สั้น **Moment** มักจะเป็นตัวคุม แต่พอ Span ยาวขึ้นเรื่อยๆ 
    **Deflection Ratio** จะพุ่งแซงหน้าไปอย่างรวดเร็วเนื่องจากผลของ $L^4$
    """)

    # --- 3. ส่วนการกางวิธีทำ (Substitution Trace) ---
    with st.expander("📝 ดูวิธีแทนค่าและหน่วยละเอียด (Calculation Trace)", expanded=False):
        w_kgcm = w_fixed / 100
        L_cm = data['user_span'] * 100
        
        st.latex(r"\Delta_{act} = \frac{5 \cdot w \cdot L^4}{384 \cdot E \cdot I_x}")
        formula_with_units = rf"""
        \Delta_{{act}} = \frac{{5 \cdot ({w_kgcm:.4f} \text{{ kg/cm}}) \cdot ({L_cm:,.0f} \text{{ cm}})^4}}{{384 \cdot ({E:,.0f} \text{{ kg/cm}}^2) \cdot ({Ix:,.2f} \text{{ cm}}^4)}} = {data['d_act']:.3f} \text{{ cm}}
        """
        st.latex(formula_with_units)
        
        st.latex(rf"\Delta_{{all}} = \frac{{L}}{{{defl_limit_denom}}} = \frac{{{L_cm:,.0f} \text{{ cm}}}}{{{defl_limit_denom}}} = {data['d_allow']:.3f} \text{{ cm}}")

    # --- 4. กราฟ Utilization (เดิม) ---
    ratios = [data['ratio_v'], data['ratio_m'], data['ratio_d']]
    labels = ['Shear', 'Moment', 'Deflection']
    fig = go.Figure(go.Bar(
        x=labels, y=ratios,
        marker_color=['#3b82f6' if r <= 1.0 else '#ef4444' for r in ratios],
        text=[f"{r:.1%}" for r in ratios],
        textposition='outside'
    ))
    fig.add_hline(y=1.0, line_dash="dash", line_color="red")
    fig.update_layout(title="Current Span Utilization", yaxis_tickformat='.0%')
    st.plotly_chart(fig, use_container_width=True)
