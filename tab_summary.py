# tab_summary.py
import streamlit as st
import plotly.graph_objects as go
import numpy as np

def render(data):
    # --- ป้องกัน KeyError: เช็คว่ามี key หรือไม่ ถ้าไม่มีให้ใช้ค่า Default ---
    section_name = data.get('section_name', 'Selected Section')
    
    st.subheader(f"📈 Capacity Analysis: {section_name}")
    
    # 1. เตรียมพารามิเตอร์คำนวณ
    E = data['E']
    Ix = data['Ix']
    M_cap = data['M_cap']  # kg-m
    defl_denom = data['defl_denom']
    
    # สร้างช่วง Span 1.0 - 15.0 เมตร
    spans = np.linspace(1.0, 15.0, 100)
    w_moment = []
    w_defl = []
    
    for L in spans:
        # Limit จาก Moment: w = 8M / L^2
        w_m = (8 * M_cap) / (L**2)
        w_moment.append(w_m)
        
        # Limit จาก Deflection: w = (384 * E * Ix) / (5 * denom * L^3 * 100^2)
        # สูตรถอดมาจากการตัดหน่วย kg/m
        L_cm = L * 100
        w_d_kgcm = (384 * E * Ix) / (5 * defl_denom * (L_cm**3))
        w_d_kgm = w_d_kgcm * 100
        w_defl.append(w_d_kgm)

    # 2. คำนวณหาจุดตัด (Crossover) เพื่อระบายสี
    w_moment = np.array(w_moment)
    w_defl = np.array(w_defl)
    safe_w = np.minimum(w_moment, w_defl)
    
    # 3. สร้างกราฟ
    fig = go.Figure()

    # เส้นขอบเขต Moment (Limit Line)
    fig.add_trace(go.Scatter(x=spans, y=w_moment, name='Moment Limit',
                             line=dict(color='blue', dash='dot', width=1)))
    
    # เส้นขอบเขต Deflection (Limit Line)
    fig.add_trace(go.Scatter(x=spans, y=w_defl, name='Deflection Limit',
                             line=dict(color='red', dash='dot', width=1)))

    # ระบายช่วงที่ Moment Control (สีน้ำเงินอ่อน)
    mask_m = w_moment <= w_defl
    fig.add_trace(go.Scatter(
        x=spans[mask_m], y=safe_w[mask_m],
        fill='tozeroy', name='Moment Control Zone',
        fillcolor='rgba(59, 130, 246, 0.3)', line=dict(color='blue', width=3)
    ))

    # ระบายช่วงที่ Deflection Control (สีแดงอ่อน)
    mask_d = w_defl < w_moment
    fig.add_trace(go.Scatter(
        x=spans[mask_d], y=safe_w[mask_d],
        fill='tozeroy', name='Deflection Control Zone',
        fillcolor='rgba(239, 68, 68, 0.3)', line=dict(color='red', width=3)
    ))

    # จุดปัจจุบัน (Current State)
    curr_l = data['user_span']
    curr_w = data['w_load'] if data.get('is_check_mode', True) else data.get('w_safe', 0)
    
    fig.add_trace(go.Scatter(
        x=[curr_l], y=[curr_w],
        mode='markers+text', name='Current Design',
        text=[f"Current: {curr_w:,.0f} kg/m"],
        textposition="top right",
        marker=dict(color='black', size=12, symbol='diamond')
    ))

    fig.update_layout(
        title=f"Allowable Load (w) vs Span for {section_name}",
        xaxis_title="Span (m)",
        yaxis_title="Allowable Load (kg/m)",
        hovermode="x unified",
        template="plotly_white"
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # --- 4. ตารางสรุปจุดควบคุม ---
    st.markdown("### 📋 Control Comparison Table")
    
    # สุ่มระยะมาโชว์ในตารางเพื่อให้เห็นภาพ
    sample_spans = [4, 6, 8, 10, 12, 14]
    table_data = []
    for s in sample_spans:
        wm = (8 * M_cap) / (s**2)
        wd = (384 * E * Ix * 100) / (5 * defl_denom * (s*100)**3)
        control = "Moment" if wm < wd else "Deflection"
        table_data.append({
            "Span (m)": s,
            "Max Load by Moment (kg/m)": f"{wm:,.2f}",
            "Max Load by Defl. (kg/m)": f"{wd:,.2f}",
            "Governing": control
        })
    
    st.table(table_data)
