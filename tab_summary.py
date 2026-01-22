# tab_summary.py
import streamlit as st
import plotly.graph_objects as go

def render(data):
    """
    Render Tab: Governing Criteria with Calculation Trace Fix
    """
    # --- 1. ตรวจสอบเงื่อนไขโหมดการทำงาน ---
    is_check_mode = data['is_check_mode']
    
    # ถ้าเป็นโหมด Check ให้ใช้ Load ที่ผู้ใช้กรอก (w_load)
    # ถ้าเป็นโหมด Find Capacity ให้ใช้ Load สูงสุดที่ยอมให้ (w_safe)
    if is_check_mode:
        w_to_show = data['w_load']
        load_type_label = "Design Load (User Input)"
    else:
        w_to_show = data['w_safe']
        load_type_label = "Max Allowable Load (Capacity)"

    w_kgcm = w_to_show / 100 # แปลง kg/m -> kg/cm
    
    # ข้อมูลอื่นๆ
    is_lrfd = data['is_lrfd']
    L_cm = data['user_span'] * 100
    Ix = data['Ix']
    E = data['E']
    defl_denom = data['defl_denom']
    
    # --- 2. HEADER ---
    st.subheader(f"🏁 Governing Analysis: {data['gov_cause']}")
    
    # --- 3. วิธีทำ DEFLECTION (Detailed Trace) ---
    with st.expander("🔍 ดูวิธีคำนวณละเอียด (Calculation Trace)", expanded=True):
        st.markdown(f"#### 📐 การคำนวณการแอ่นตัว (Deflection Check)")
        st.caption(f"Status: Using {load_type_label} = {w_to_show:,.2f} kg/m")

        # สูตร LaTeX
        st.latex(r"\Delta_{act} = \frac{5 \cdot w \cdot L^4}{384 \cdot E \cdot I_x}")

        # ส่วนแทนค่า (Substitution)
        # แก้ปัญหา W = 0 โดยใช้ค่า w_to_show ที่ตรวจสอบแล้ว
        st.markdown("**แทนค่าตัวเลขลงในสูตร:**")
        
        # สร้าง String สำหรับวิธีทำ
        trace_text = rf"""
        $$ \Delta_{{act}} = \frac{{5 \cdot {w_kgcm:.4f} \cdot {L_cm:,.0f}^4}}{{384 \cdot {E:,.0f} \cdot {Ix:,.2f}}} $$
        """
        st.markdown(trace_text)

        c1, c2 = st.columns(2)
        with c1:
            st.success(f"**Δ_actual = {data['d_act']:.3f} cm**")
        with c2:
            st.info(f"**Δ_allow (L/{defl_denom}) = {data['d_allow']:.3f} cm**")

        # สรุป Ratio
        st.markdown(f"**Utilization Ratio ($\Delta$)** = {data['d_act']:.3f} / {data['d_allow']:.3f} = **{data['ratio_d']:.2%}**")

    # --- 4. กราฟแท่งเปรียบเทียบ ---
    st.divider()
    ratios = [data['ratio_v'], data['ratio_m'], data['ratio_d']]
    labels = ['Shear', 'Moment', 'Deflection']
    
    fig = go.Figure(go.Bar(
        x=labels, y=ratios,
        marker_color=['#3b82f6' if r < 1 else '#ef4444' for r in ratios],
        text=[f"{r:.2%}" for r in ratios],
        textposition='auto'
    ))
    fig.add_hline(y=1.0, line_dash="dash", line_color="red")
    fig.update_layout(title="Utilization Ratio Comparison", yaxis_range=[0, max(max(ratios)*1.2, 1.2)])
    st.plotly_chart(fig, use_container_width=True)
