# tab_summary.py
import streamlit as st
import plotly.graph_objects as go

def render(data):
    # --- 1. เตรียมตัวแปร (Data Extraction) ---
    is_lrfd = data.get('is_lrfd', False)
    method_name = "LRFD" if is_lrfd else "ASD"
    
    # Loads & Spans
    L_m = data['user_span']
    L_cm = L_m * 100
    w_kgm = data['w_load'] if data.get('is_check_mode', True) else data.get('w_safe', 0)
    w_kgcm = w_kgm / 100
    
    # Section Properties
    section_name = data.get('section_name', 'Selected Section')
    Ix = data['Ix']
    Zx = data.get('Zx', 0) # Plastic Section Modulus
    Sx = data.get('Sx', 0) # Elastic Section Modulus
    Fy = data.get('Fy', 2500) # สมมติ 2500 ksc ถ้าไม่มีข้อมูล
    E = data['E']
    
    # Limits
    defl_denom = data['defl_denom']

    st.header(f"📑 รายการคำนวณโดยละเอียด (Section: {section_name})")
    st.info(f"Design Method: **{method_name}** | Load: **{w_kgm:,.2f} kg/m** | Span: **{L_m:,.2f} m**")

    # --- ส่วนที่ 1: การแอ่นตัว (Deflection Check) ---
    with st.container(border=True):
        st.markdown("### 1️⃣ การตรวจสอบการแอ่นตัว (Serviceability Limit State)")
        st.markdown("การคำนวณการแอ่นตัวต้องใช้ **Service Load** (ไม่คูณ Load Factor)")
        
        # กางสูตร
        st.latex(r"\text{สูตร: } \Delta_{act} = \frac{5 \cdot w \cdot L^4}{384 \cdot E \cdot I_x}")
        
        # แทนค่า
        st.markdown("**แทนค่าคำนวณ:**")
        formula_defl = rf"""
        \Delta_{{act}} = \frac{{5 \cdot ({w_kgcm:.4f} \text{{ kg/cm}}) \cdot ({L_cm:,.0f} \text{{ cm}})^4}}{{384 \cdot ({E:,.0f} \text{{ kg/cm}}^2) \cdot ({Ix:,.2f} \text{{ cm}}^4)}}
        """
        st.latex(formula_defl)
        st.markdown(f"**$\Delta_{{act}}$ (คำตอบ) = `{data['d_act']:.3f}` cm**")
        
        # ค่าที่ยอมให้
        st.latex(rf"\Delta_{{all}} = \frac{{L}}{{{defl_denom}}} = \frac{{{L_cm:,.0f}}}{{{defl_denom}}} = {data['d_allow']:.3f} \text{{ cm}}")
        
        # สรุป Ratio
        r_d = data['ratio_d']
        st.markdown(f"**Ratio ($\Delta$) = {data['d_act']:.3f} / {data['d_allow']:.3f} = `{r_d:.4f}`**")

    # --- ส่วนที่ 2: แรงดัด (Flexural Strength) ---
    with st.container(border=True):
        st.markdown(f"### 2️⃣ การตรวจสอบแรงดัด (Flexural Capacity - {method_name})")
        
        # 2.1 หา Moment สูงสุด (Demand)
        st.markdown("**2.1 แรงดัดที่เกิดขึ้น (Bending Moment Demand):**")
        st.latex(r"M_{max} = \frac{w \cdot L^2}{8}")
        st.latex(rf"M_{{max}} = \frac{{{w_kgm:,.2f} \text{{ kg/m}} \cdot ({L_m} \text{{ m}})^2}}{{8}} = {data['m_act']:,.2f} \text{{ kg-m}}")
        
        # 2.2 กำลังที่ยอมให้ (Capacity)
        st.markdown(f"**2.2 กำลังที่ยอมให้ (Moment Capacity - {method_name}):**")
        if is_lrfd:
            st.latex(r"\phi M_n = 0.90 \cdot F_y \cdot Z_x")
            # สมมติการคำนวณ Zx Fy
            st.latex(rf"0.90 \cdot {Fy} \cdot {Zx:,.2f} = {data['M_cap']:,.2f} \text{{ kg-m}}")
        else:
            st.latex(r"M_n / \Omega = \frac{F_y \cdot S_x}{1.67}")
            st.latex(rf"\frac{{{Fy} \cdot {Sx:,.2f}}}{{1.67}} = {data['M_cap']:,.2f} \text{{ kg-m}}")
            
        # สรุป Ratio
        r_m = data['ratio_m']
        st.markdown(f"**Ratio (Moment) = {data['m_act']:,.2f} / {data['M_cap']:,.2f} = `{r_m:.4f}`**")

    # --- ส่วนที่ 3: แรงเฉือน (Shear Strength) ---
    with st.container(border=True):
        st.markdown(f"### 3️⃣ การตรวจสอบแรงเฉือน (Shear Capacity - {method_name})")
        
        # 3.1 หา Shear สูงสุด (Demand)
        st.latex(r"V_{max} = \frac{w \cdot L}{2}")
        st.latex(rf"V_{{max}} = \frac{{{w_kgm:,.2f} \cdot {L_m}}}{{2}} = {data['v_act']:,.2f} \text{{ kg}}")
        
        # 3.2 กำลังเฉือน (Capacity)
        st.write(f"Capacity ($V_{{cap}}$) = **{data['V_cap']:,.2f} kg**")
        
        # สรุป Ratio
        r_v = data['ratio_v']
        st.markdown(f"**Ratio (Shear) = {data['v_act']:,.2f} / {data['V_cap']:,.2f} = `{r_v:.4f}`**")

    # --- ส่วนที่ 4: สรุปผล (Final Summary) ---
    st.divider()
    gov_ratio = data['gov_ratio']
    gov_cause = data['gov_cause']
    
    st.subheader("📊 บทสรุปการออกแบบ")
    cols = st.columns(3)
    cols[0].metric("Moment Ratio", f"{r_m:.2%}")
    cols[1].metric("Shear Ratio", f"{r_v:.2%}")
    cols[2].metric("Deflection Ratio", f"{r_d:.2%}", delta=f"{r_d-1:.2%}" if r_d > 1 else None, delta_color="inverse")
    
    if gov_ratio > 1.0:
        st.error(f"⚠️ การออกแบบไม่ผ่าน: ถูกควบคุมโดย {gov_cause} (Ratio: {gov_ratio:.2%})")
    else:
        st.success(f"✅ การออกแบบผ่าน: ถูกควบคุมโดย {gov_cause} (Ratio: {gov_ratio:.2%})")

    # กราฟแท่งเพื่อดูสัดส่วน
    fig = go.Figure(go.Bar(
        x=['Shear', 'Moment', 'Deflection'],
        y=[r_v, r_m, r_d],
        marker_color=['#1e40af' if r <= 1.0 else '#b91c1c' for r in [r_v, r_m, r_d]],
        text=[f"{r:.2%}" for r in [r_v, r_m, r_d]],
        textposition='auto'
    ))
    fig.add_hline(y=1.0, line_dash="dash", line_color="red")
    fig.update_layout(title="Utilization Ratio Comparison", yaxis_tickformat='.0%')
    st.plotly_chart(fig, use_container_width=True)
