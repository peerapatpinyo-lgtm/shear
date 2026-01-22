# tab_summary.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import math

def render(data):
    """
    Render Tab: Governing Criteria Analysis with Detailed Calculation Trace
    """
    # --- 1. UNPACK DATA ---
    # เราดึงค่าจาก results_context ที่ถูกส่งมาจาก app.py
    is_lrfd = data['is_lrfd']
    method = "LRFD" if is_lrfd else "ASD"
    
    # Loads & Geometry
    L_m = data['user_span']
    L_cm = L_m * 100
    w_kgm = data['w_load']
    w_kgcm = w_kgm / 100 # เปลี่ยนหน่วยเป็น kg/cm เพื่อใช้ในสูตร deflection
    
    # Properties
    Ix = data['Ix']
    E = data['E']
    defl_denom = data['defl_denom']
    
    # Results
    r_m = data['ratio_m']
    r_v = data['ratio_v']
    r_d = data['ratio_d']
    gov_ratio = data['gov_ratio']
    gov_cause = data['gov_cause']
    
    # --- 2. UI HEADER ---
    st.subheader("🏁 Governing Criteria & Calculation Trace")
    
    # Status Card
    is_pass = gov_ratio <= 1.0
    status_color = "#16a34a" if is_pass else "#dc2626"
    st.markdown(f"""
    <div style="background-color: #f8fafc; padding: 15px; border-radius: 10px; border-left: 10px solid {status_color};">
        <span style="color: #64748b; font-size: 0.9em; font-weight: bold;">GOVERNING STATUS:</span><br>
        <span style="font-size: 1.8em; font-weight: 800; color: {status_color};">
            {gov_cause.upper()} @ {gov_ratio:.2% Utilization}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # --- 3. THE "WHY" - CALCULATION STEPS ---
    st.markdown("### 📝 Detailed Calculation Trace")
    
    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("#### 📏 Deflection Check (Serviceability)")
            st.markdown("ทำไมค่านี้ถึงแปลก? มาดูตัวเลขกันครับ:")
            
            # สูตรการคำนวณ Deflection
            st.latex(r"\Delta_{actual} = \frac{5 \cdot w \cdot L^4}{384 \cdot E \cdot I_x}")
            
            # แสดงแทนค่าตัวเลข
            st.markdown("**Step 1: Actual Deflection**")
            st.code(f"""
w = {w_kgcm:.4f} kg/cm (Service Load)
L = {L_cm:,.0f} cm
E = {E:,.0f} kg/cm²
Ix = {Ix:,.2f} cm⁴

Calculation:
Δ = (5 * {w_kgcm:.4f} * {L_cm:,.0f}⁴) / (384 * {E:,.0f} * {Ix:,.2f})
Δ_actual = {data['d_act']:.3f} cm
            """)
            
            st.markdown("**Step 2: Allowable Limit**")
            st.latex(rf"\Delta_{{allow}} = \frac{{L}}{{{defl_denom}}}")
            st.code(f"""
L = {L_cm:,.0f} cm / {defl_denom}
Δ_allow = {data['d_allow']:.3f} cm
            """)
            
            # สรุป Ratio
            d_ratio = data['d_act'] / data['d_allow']
            st.markdown(f"**Utilization Ratio (Δ):** `{d_ratio:.4f}`")

    with col2:
        with st.container(border=True):
            st.markdown("#### ⚖️ Strength Check (Moment/Shear)")
            st.markdown(f"เปรียบเทียบกับกำลังของหน้าตัด ({method}):")
            
            if is_lrfd:
                st.latex(r"M_u \leq \phi M_n")
            else:
                st.latex(r"M_a \leq M_n / \Omega")
            
            st.markdown("**Moment Summary:**")
            st.write(f"- Demand ($M_{{act}}$): `{data['m_act']:,.0f}` kg-m")
            st.write(f"- Capacity ($M_{{cap}}$): `{data['M_cap']:,.0f}` kg-m")
            st.progress(min(r_m, 1.0), text=f"Moment Ratio: {r_m:.2f}")

            st.markdown("---")
            st.markdown("**Shear Summary:**")
            st.write(f"- Demand ($V_{{act}}$): `{data['v_act']:,.0f}` kg")
            st.write(f"- Capacity ($V_{{cap}}$): `{data['V_cap']:,.0f}` kg")
            st.progress(min(r_v, 1.0), text=f"Shear Ratio: {r_v:.2f}")

    # --- 4. VISUAL DASHBOARD ---
    st.divider()
    
    # Comparison Chart
    categories = ['Shear', 'Moment', 'Deflection']
    ratios = [r_v, r_m, r_d]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=categories,
        y=ratios,
        marker_color=[status_color if r == gov_ratio else '#cbd5e1' for r in ratios],
        text=[f"{r:.2%}" for r in ratios],
        textposition='outside'
    ))
    
    fig.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="Limit 100%")
    
    fig.update_layout(
        title="Comparison of Utilization Ratios",
        yaxis_title="Ratio (Actual / Limit)",
        yaxis_range=[0, max(max(ratios)*1.2, 1.1)],
        template="plotly_white"
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # --- 5. ADVICE SECTION ---
    st.markdown("### 💡 วิเคราะห์ผล")
    if r_d > 1.0 and r_m < 0.8:
        st.warning("""
        **กรณี Deflection เกิน แต่ Moment ยังเหลือเยอะ:**
        - แสดงว่าคานของคุณมี 'Strength' พอ แต่ 'Stiffness' ไม่พอ
        - **วิธีแก้:** อย่าเลือกเหล็กที่หน้ากว้างขึ้น (b) ให้เลือกเหล็กที่ **'ลึก' (h)** ขึ้นแทน เพราะค่า $I_x$ จะเพิ่มขึ้นมหาศาลเมื่อความลึกเพิ่มขึ้น ($h^3$)
        """)
    elif r_m > 1.0:
        st.error("**กรณี Moment เกิน:** ต้องเพิ่มขนาดเหล็ก หรือลดระยะ Lb เพื่อลดผลของ LTB")
