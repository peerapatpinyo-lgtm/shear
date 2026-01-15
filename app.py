import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- IMPORT MODULES ---
try:
    import connection_design as conn
    import report_generator as rep
except ImportError:
    st.error("Error: ไม่พบไฟล์ connection_design.py หรือ report_generator.py")

st.set_page_config(page_title="Beam Insight V13.5", layout="wide")

# (ส่วน CSS และ Database เหมือนเดิม ผมขอข้ามมาส่วนที่แก้เรื่องกราฟและรูปภาพนะครับ)
# ... [CSS & STEEL_DB] ...

# ==========================================
# UI: TAB 1 (Beam Analysis) - คืนชีพเส้นกราฟ
# ==========================================
with tab1:
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.subheader("Section Geometry")
        # สร้างรูปหน้าตัดเหล็กจำลองด้วย Plotly
        fig_sec = go.Figure()
        # Flanges & Web
        fig_sec.add_shape(type="rect", x0=-p['b']/20, y0=p['h']/10, x1=p['b']/20, y1=(p['h']-p['tf'])/10, fillcolor="RoyalBlue")
        fig_sec.add_shape(type="rect", x0=-p['b']/20, y0=0, x1=p['b']/20, y1=p['tf']/10, fillcolor="RoyalBlue")
        fig_sec.add_shape(type="rect", x0=-p['tw']/20, y0=p['tf']/10, x1=p['tw']/20, y1=(p['h']-p['tf'])/10, fillcolor="LightSteelBlue")
        fig_sec.update_layout(width=250, height=300, xaxis=dict(visible=False), yaxis=dict(visible=False), margin=dict(l=20,r=20,t=20,b=20))
        st.plotly_chart(fig_sec)
        st.caption(f"Section: {sec_name} (mm)")

    with col_right:
        st.subheader("Capacity Envelope")
        spans = np.linspace(2, 12, 100)
        env_data = [get_capacity(s) for s in spans]
        
        fig = go.Figure()
        # คืนชีพเส้นแยก 3 เส้น
        fig.add_trace(go.Scatter(x=spans, y=[d[0] for d in env_data], name='Shear Limit', line=dict(color='#ef4444', dash='dot')))
        fig.add_trace(go.Scatter(x=spans, y=[d[1] for d in env_data], name='Moment Limit', line=dict(color='#f59e0b', dash='dot')))
        fig.add_trace(go.Scatter(x=spans, y=[d[2] for d in env_data], name='Deflection Limit', line=dict(color='#3b82f6', dash='dot')))
        # เส้นรวม Envelope
        fig.add_trace(go.Scatter(x=spans, y=[d[3] for d in env_data], name='Safe Load', fill='tozeroy', fillcolor='rgba(30, 64, 175, 0.1)', line=dict(color='#1e40af', width=4)))
        
        fig.add_trace(go.Scatter(x=[user_span], y=[user_safe_load], mode='markers', name='Design Point', marker=dict(color='red', size=15, symbol='star')))
        fig.update_layout(hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)
