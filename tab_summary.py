# tab_summary.py
import streamlit as st
import plotly.graph_objects as go
import numpy as np

def render(data):
    st.subheader("📈 Capacity Limit & Control Zones")
    
    # --- 1. เตรียมข้อมูลหน้าตัด ---
    E = data['E']
    Ix = data['Ix']
    M_cap = data['M_cap']  # kg-m
    defl_denom = data['defl_denom']
    
    # สร้างช่วง Span สำหรับวาดกราฟ (เช่น 1m ถึง 15m)
    spans = np.linspace(1.0, 15.0, 100)
    
    w_moment_limit = []
    w_deflection_limit = []
    
    for L in spans:
        # 1. หาน้ำหนักสูงสุดที่ Moment ยอมให้: w = (8 * M) / L^2
        w_m = (8 * M_cap) / (L**2)
        w_moment_limit.append(w_m)
        
        # 2. หาน้ำหนักสูงสุดที่ Deflection ยอมให้: 
        # จาก Δ_all = L/denom และ Δ_act = 5wL^4 / 384EI
        # แก้สมการหา w (หน่วย kg/m): w = (384 * E * Ix * 100) / (5 * denom * (L*100)^3)
        # *หมายเหตุ: L^3 เพราะ Δ_all มี L ตัวนึงไปตัดกับ L^4 ในสูตร Δ_act
        L_cm = L * 100
        w_d_kgcm = (384 * E * Ix) / (5 * defl_denom * (L_cm**3))
        w_d_kgm = w_d_kgcm * 100 
        w_deflection_limit.append(w_d_kgm)

    # --- 2. สร้างกราฟด้วย Plotly ---
    fig = go.Figure()

    # เส้นขอบเขต Moment
    fig.add_trace(go.Scatter(
        x=spans, y=w_moment_limit,
        name='Moment Limit',
        line=dict(color='blue', dash='dot')
    ))

    # เส้นขอบเขต Deflection
    fig.add_trace(go.Scatter(
        x=spans, y=w_deflection_limit,
        name='Deflection Limit',
        line=dict(color='red', dash='dot')
    ))

    # คำนวณหาเส้นที่ต่ำที่สุด (Capacity จริง)
    safe_w = np.minimum(w_moment_limit, w_deflection_limit)
    
    # ระบายสีช่วง Moment Control (ช่วงที่เส้น Moment ต่ำกว่า)
    moment_control_x = spans[np.array(w_moment_limit) <= np.array(w_deflection_limit)]
    moment_control_y = safe_w[np.array(w_moment_limit) <= np.array(w_deflection_limit)]
    
    if len(moment_control_x) > 0:
        fig.add_trace(go.Scatter(
            x=moment_control_x, y=moment_control_y,
            fill='tozeroy',
            name='Moment Control Zone',
            fillcolor='rgba(0, 0, 255, 0.2)',
            line=dict(color='blue', width=3)
        ))

    # ระบายสีช่วง Deflection Control (ช่วงที่เส้น Deflection ต่ำกว่า)
    defl_control_x = spans[np.array(w_deflection_limit) < np.array(w_moment_limit)]
    defl_control_y = safe_w[np.array(w_deflection_limit) < np.array(w_moment_limit)]
    
    if len(defl_control_x) > 0:
        fig.add_trace(go.Scatter(
            x=defl_control_x, y=defl_control_y,
            fill='tozeroy',
            name='Deflection Control Zone',
            fillcolor='rgba(255, 0, 0, 0.2)',
            line=dict(color='red', width=3)
        ))

    # จุดปัจจุบันของผู้ใช้
    current_w = data['w_load'] if data['is_check_mode'] else data['w_safe']
    fig.add_trace(go.Scatter(
        x=[data['user_span']], y=[current_w],
        mode='markers+text',
        name='Current Design',
        text=["จุดปัจจุบัน"],
        textposition="top right",
        marker=dict(color='black', size=12, symbol='x')
    ))

    fig.update_layout(
        title=f"W-Capacity vs Span (Section: {data['section_name']})",
        xaxis_title="Span (m)",
        yaxis_title="Max Allowable Load (kg/m)",
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- 3. คำอธิบายตาราง ---
    st.info("""
    **💡 วิธีการอ่านกราฟ:**
    - **พื้นที่สีฟ้า:** คือช่วงที่ความแข็งแรง (Moment) เป็นตัวกำหนดน้ำหนักบรรทุก
    - **พื้นที่สีแดง:** คือช่วงที่ความยาวมากจนการแอ่นตัว (Deflection) กลายเป็นข้อจำกัด
    - **จุดตัด:** คือระยะ Span ที่เหมาะสมที่สุดที่ใช้ประสิทธิภาพของเหล็กได้เต็มที่ทั้ง Strength และ Stiffness
    """)
