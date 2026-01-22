# tab_summary.py
import streamlit as st
import plotly.graph_objects as go

def render(data):
    """
    Render Tab: Governing Criteria with Detailed Mathematical Trace
    """
    # --- 1. ข้อมูลพื้นฐาน ---
    is_lrfd = data['is_lrfd']
    method = "LRFD" if is_lrfd else "ASD"
    
    # ดึงค่าจาก results_context
    L_m = data['user_span']
    L_cm = L_m * 100
    w_kgm = data['w_load']
    w_kgcm = w_kgm / 100 
    Ix = data['Ix']
    E = data['E']
    defl_denom = data['defl_denom']
    
    # อัตราส่วน
    r_m = data['ratio_m']
    r_v = data['ratio_v']
    r_d = data['ratio_d']
    gov_ratio = data['gov_ratio']
    gov_cause = data['gov_cause']

    # --- 2. สรุปผลการออกแบบ (Executive Summary) ---
    st.subheader("🏁 Design Verdict")
    
    is_pass = gov_ratio <= 1.0
    status_text = "PASS ✅" if is_pass else "FAIL ❌"
    status_color = "#16a34a" if is_pass else "#dc2626"
    
    st.markdown(f"""
    <div style="background-color: {status_color}15; padding: 20px; border-radius: 12px; border-left: 8px solid {status_color};">
        <h3 style="margin:0; color: {status_color};">{status_text} - Controlled by {gov_cause}</h3>
        <p style="margin:5px 0 0 0; font-size: 1.2em;">Max Utilization Ratio: <b>{gov_ratio:.2%}</b></p>
    </div>
    """, unsafe_allow_html=True)

    # --- 3. แสดงวิธีทำ (Detailed Calculation Trace) ---
    st.divider()
    st.markdown("### 📝 Calculation Trace (กางสูตรคำนวณ)")
    
    col1, col2 = st.columns(2)

    with col1:
        # --- ส่วนของ DEFLECTION ---
        with st.container(border=True):
            st.markdown("#### 📏 1. Deflection Serviceability")
            st.write("ตรวจสอบการแอ่นตัว (ใช้ Service Load ไม่คูณ Factor)")
            
            # แสดงสมการหลัก
            st.latex(r"\Delta_{act} = \frac{5 w L^4}{384 E I_x}")
            
            # แทนค่า
            st.markdown("**Substitution:**")
            st.write(f"- $w$ = {w_kgcm:.4f} kg/cm (Uniform Load)")
            st.write(f"- $L$ = {L_cm:,.0f} cm (Span)")
            st.write(f"- $E$ = {E:,.0f} kg/cm² (Elastic Modulus)")
            st.write(f"- $I_x$ = {Ix:,.2f} cm⁴ (Inertia)")
            
            # ผลลัพธ์ Actual
            st.info(f"**Δ_actual** = {data['d_act']:.3f} cm")
            
            # ขีดจำกัด
            st.latex(rf"\Delta_{{all}} = \frac{{L}}{{{defl_denom}}}")
            st.write(f"**Δ_allow** = {L_cm:,.0f} / {defl_denom} = **{data['d_allow']:.3f} cm**")
            
            # สรุป Ratio
            st.markdown(f"**Ratio (Δ) = {data['d_act']:.3f} / {data['d_allow']:.3f} = `{r_d:.4f}`**")

    with col2:
        # --- ส่วนของ MOMENT ---
        with st.container(border=True):
            st.markdown(f"#### ⚖️ 2. Flexural Strength ({method})")
            st.write("ตรวจสอบแรงดัด (Strength Limit State)")
            
            # สมการ Demand
            st.latex(r"M_{req} = \frac{w_{fact} L^2}{8}")
            st.write(f"- $M_{{req}}$ (Demand) = **{data['m_act']:,.0f} kg-m**")
            
            # สมการ Capacity
            if is_lrfd:
                st.latex(r"\phi M_n = 0.90 \times F_y \times Z_x \text{ (Simplified)}")
            else:
                st.latex(r"M_n / \Omega = (F_y \times Z_x) / 1.67 \text{ (Simplified)}")
                
            st.write(f"- $M_{{cap}}$ (Capacity) = **{data['M_cap']:,.0f} kg-m**")
            
            # สรุป Ratio
            st.markdown(f"**Ratio (M) = {data['m_act']:,.0f} / {data['M_cap']:,.0f} = `{r_m:.4f}`**")

            st.divider()
            # Shear Ratio (สรุปสั้น)
            st.markdown(f"**Shear Ratio (V):** `{r_v:.4f}`")

    # --- 4. กราฟเปรียบเทียบ (Comparison Chart) ---
    st.divider()
    st.markdown("### 📊 Utilization Comparison")
    
    labels = ['Shear (V)', 'Moment (M)', 'Deflection (Δ)']
    values = [r_v, r_m, r_d]
    colors = ['#94a3b8', '#94a3b8', '#94a3b8']
    
    # ไฮไลท์ตัวที่สูงที่สุด
    max_idx = values.index(max(values))
    colors[max_idx] = status_color

    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker_color=colors,
        text=[f"{v:.1%}" for v in values],
        textposition='outside'
    ))
    
    fig.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="Limit (1.0)")
    fig.update_layout(yaxis_range=[0, max(max(values)*1.3, 1.1)], height=400, template="plotly_white")
    
    st.plotly_chart(fig, use_container_width=True)

    # --- 5. สรุปบทวิเคราะห์ ---
    st.markdown("#### 💡 Engineering Insight")
    if r_d > r_m:
        st.warning(f"""
        **ผลการวิเคราะห์:** คานนี้ถูกควบคุมด้วย **Deflection** (การแอ่นตัว) 
        ซึ่งหมายความว่าแม้เหล็กจะยังไม่พังในเชิงโครงสร้าง แต่การใช้งานจริงจะพบการแอ่นตัวที่มากเกินพิกัด L/{defl_denom}
        \n**วิธีแก้ไขที่ประหยัดที่สุด:** ให้เพิ่มความลึกหน้าตัด (Depth) แทนการเพิ่มความกว้าง เพราะค่า $I_x$ เพิ่มขึ้นเป็นกำลังสามของความสูง
        """)
    else:
        st.info("**ผลการวิเคราะห์:** คานนี้ถูกควบคุมด้วย **Strength** (กำลังของวัสดุ) เป็นการออกแบบที่มีประสิทธิภาพด้านความแข็งแรง")
