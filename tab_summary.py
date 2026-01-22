# tab_summary.py
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

def render(data):
    """
    Render Tab: Governing Criteria Analysis
    Analyzes which factor (Shear, Moment, or Deflection) is controlling the design.
    """
    # --- 1. UNPACK DATA ---
    gov_cause = data['gov_cause']  # e.g., "Moment", "Shear", "Deflection"
    gov_ratio = data['gov_ratio']
    
    # Ratios
    r_m = data['ratio_m']
    r_v = data['ratio_v']
    r_d = data['ratio_d']
    
    # Status
    is_pass = gov_ratio <= 1.0
    status_text = "PASS ✅" if is_pass else "FAIL ❌"
    status_color = "green" if is_pass else "red"
    
    # --- 2. HEADER: THE VERDICT ---
    st.subheader("🏁 Governing Criteria Analysis")
    
    # Create a highlight box
    box_color = "#dcfce7" if is_pass else "#fee2e2" # light green / light red
    border_color = "#16a34a" if is_pass else "#dc2626"
    
    st.markdown(f"""
    <div style="background-color: {box_color}; padding: 20px; border-radius: 10px; border-left: 6px solid {border_color}; margin-bottom: 20px;">
        <h2 style="margin:0; color: #1f2937;">Controlled by: <span style="text-decoration: underline;">{gov_cause}</span></h2>
        <p style="margin-top:5px; font-size: 1.1em; color: #4b5563;">
            Utilization Ratio: <strong>{gov_ratio:.2f}</strong> ({gov_ratio*100:.1f}%) | Status: <strong>{status_text}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # --- 3. VISUALIZATION: THE RACE ---
    c1, c2 = st.columns([1, 1.5])
    
    with c1:
        # GAUGE CHART (Speedometer)
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = gov_ratio,
            title = {'text': "Max Utilization Ratio"},
            gauge = {
                'axis': {'range': [None, 1.5], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': border_color},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 0.6], 'color': "#e0f2fe"},  # Safe/Conservative
                    {'range': [0.6, 1.0], 'color': "#dcfce7"}, # Optimal
                    {'range': [1.0, 1.5], 'color': "#fee2e2"}  # Fail
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 1.0
                }
            }
        ))
        fig_gauge.update_layout(height=300, margin=dict(l=20,r=20,t=50,b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with c2:
        # BAR CHART (Comparison)
        categories = ['Shear', 'Moment', 'Deflection']
        values = [r_v, r_m, r_d]
        colors = ['#94a3b8', '#94a3b8', '#94a3b8'] # Default Gray
        
        # Highlight the winner
        if gov_cause == 'Shear': colors[0] = '#f59e0b' # Orange
        elif gov_cause == 'Moment': colors[1] = '#3b82f6' # Blue
        elif gov_cause == 'Deflection': colors[2] = '#10b981' # Green
        
        # Make Failures Red
        for i, val in enumerate(values):
            if val > 1.0: colors[i] = '#ef4444'

        fig_bar = go.Figure(go.Bar(
            x=values,
            y=categories,
            orientation='h',
            marker_color=colors,
            text=[f"{v:.2f}" for v in values],
            textposition='auto'
        ))
        
        fig_bar.add_vline(x=1.0, line_dash="dash", line_color="red", annotation_text="Limit (1.0)")
        
        fig_bar.update_layout(
            title="Criteria Comparison (Who is working hardest?)",
            xaxis_title="Utilization Ratio (Actual / Allowable)",
            height=300,
            margin=dict(l=20,r=20,t=40,b=20)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- 4. INSIGHTS & RECOMMENDATION ---
    st.divider()
    st.subheader("💡 Engineering Insights")

    # Generate Advice Logic
    col_ins1, col_ins2 = st.columns(2)
    
    with col_ins1:
        st.markdown("**What does this mean?**")
        if gov_cause == "Moment":
            st.info("""
            **Moment Controls:** คานรับแรงดัดมากที่สุด
            - โดยทั่วไปเกิดกับคานที่มีช่วงยาว (Long Span)
            - หรือคานที่ไม่มีการค้ำยันด้านข้าง (High Lb) ทำให้เกิด LTB
            """)
        elif gov_cause == "Deflection":
            st.info("""
            **Deflection Controls:** คานแอ่นตัวมากเกินพิกัด
            - มักเกิดกับคานช่วงยาวมาก (Very Long Span)
            - แม้คานจะรับแรงได้ (Strength ผ่าน) แต่แอ่นตัวจนน่าเกลียดหรือใช้งานไม่ได้
            """)
        elif gov_cause == "Shear":
            st.info("""
            **Shear Controls:** คานรับแรงเฉือนมากที่สุด
            - มักเกิดกับคานช่วงสั้น (Short Span) ที่รับน้ำหนักบรรทุกสูงมาก
            - หรือจุดที่มี Point Load กระทำใกล้จุดรองรับ
            """)
            
    with col_ins2:
        st.markdown("**Optimization Tips:**")
        
        if gov_ratio > 1.0:
            st.error("❌ **Action Required:** Section Fails!")
            if gov_cause == "Moment":
                st.write("- เลือกหน้าตัดที่มี **Weight** หรือ **Zx** มากขึ้น")
                st.write("- ลดระยะค้ำยันด้านข้าง (**Lb**) ลง")
            elif gov_cause == "Deflection":
                st.write("- ต้องเพิ่มค่า **Ix** (เลือกหน้าตัดที่ลึกขึ้น Deep Beam)")
            elif gov_cause == "Shear":
                st.write("- เลือกหน้าตัดที่มีเนื้อที่เอว (**Aw**) มากขึ้น (เพิ่ม t_w หรือ Depth)")
                
        elif gov_ratio < 0.5:
            st.warning("⚠️ **Over-designed:** Section is too big.")
            st.write("- คุณสามารถลดขนาดหน้าตัดลงได้เพื่อประหยัด cost")
            st.write("- ลองเลือกหน้าตัดที่เบาลง 1-2 เบอร์")
            
        else:
            st.success("✅ **Good Design:** Efficient use of material.")
            st.write("- Ratio อยู่ในช่วง 0.5 - 1.0 ถือว่าออกแบบได้ประหยัดและปลอดภัย")

    # --- 5. DETAILED TABLE ---
    st.divider()
    with st.expander("Show Detailed Values Table"):
        df_summary = pd.DataFrame({
            "Criteria": ["Shear (V)", "Moment (M)", "Deflection (Δ)"],
            "Ratio": [r_v, r_m, r_d],
            "Status": ["Pass" if r <=1 else "Fail" for r in [r_v, r_m, r_d]]
        })
        st.table(df_summary)
