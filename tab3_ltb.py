import streamlit as st
import plotly.graph_objects as go
import numpy as np
import math

def render(data):
    """
    Render Tab 3: LTB Insight (Interactive Version)
    data: Context dictionary from app.py
    """
    # 1. Unpack Data
    Lb_real = data['Lb']         # ค่าจริงจาก Sidebar
    Lp_cm = data['Lp_cm']
    Lr_cm = data['Lr_cm']
    Mp = data['Mp']
    Fy = data['Fy']
    Sx = data['Sx']
    E = data['E']
    Cb = data['Cb']
    r_ts = data['r_ts']
    val_A = data['val_A']
    user_span = data['user_span']
    
    # แปลงหน่วยเพื่อการคำนวณและแสดงผล
    Lp_m = Lp_cm / 100
    Lr_m = Lr_cm / 100
    Mp_kgm = Mp / 100

    st.subheader("🛡️ LTB Stability Analysis")
    st.caption("Lateral-Torsional Buckling Behavior & Simulation")

    # --- PART 1: CONTROL & SIMULATION ---
    col_sim, col_info = st.columns([1, 2])
    
    with col_sim:
        st.markdown("#### 🎮 Simulator")
        st.info("ลองเลื่อน Slider เพื่อดูว่าถ้าลดระยะค้ำยัน ($L_b$) แล้วกำลังรับโมเมนต์ ($M_n$) จะเปลี่ยนไปอย่างไร")
        
        # Slider สำหรับจำลอง Lb (default คือค่าจริงที่ User กรอก)
        lb_sim = st.slider("Simulate Unbraced Length (m)", 
                           min_value=0.5, 
                           max_value=float(user_span), 
                           value=float(Lb_real),
                           step=0.25)
        
        # คำนวณ Mn ตามค่า Simulation
        lb_sim_cm = lb_sim * 100
        if lb_sim_cm <= Lp_cm:
            mn_sim = Mp
            zone_sim = "Zone 1 (Plastic)"
            zone_color = "#10b981" # Green
        elif lb_sim_cm <= Lr_cm:
            term = (Mp - 0.7 * Fy * Sx) * ((lb_sim_cm - Lp_cm) / (Lr_cm - Lp_cm))
            mn_sim = min(Cb * (Mp - term), Mp)
            zone_sim = "Zone 2 (Inelastic)"
            zone_color = "#f59e0b" # Orange
        else:
            slend = (lb_sim_cm / r_ts)
            fcr = (Cb * math.pi**2 * E) / (slend**2) * math.sqrt(1 + 0.078 * val_A * slend**2)
            mn_sim = min(fcr * Sx, Mp)
            zone_sim = "Zone 3 (Elastic)"
            zone_color = "#ef4444" # Red
            
        mn_sim_kgm = mn_sim / 100
        
        # แสดงผลลัพธ์ Simulation
        st.markdown(f"""
        <div style="text-align:center; padding:15px; background:{zone_color}20; border-radius:10px; border:1px solid {zone_color};">
            <small style="color:{zone_color}; font-weight:bold;">Current State</small>
            <h2 style="margin:0; color:{zone_color};">{mn_sim_kgm:,.0f} <span style="font-size:16px">kg-m</span></h2>
            <div style="margin-top:5px; font-weight:bold;">{zone_sim}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_info:
        # --- PART 2: GRAPH VISUALIZATION ---
        # สร้างกราฟ LTB Curve
        max_len = max(Lr_m * 1.5, user_span)
        x_vals = np.linspace(0.1, max_len, 100)
        y_vals = []
        
        for l in x_vals:
            l_cm = l * 100
            if l_cm <= Lp_cm: 
                m = Mp
            elif l_cm <= Lr_cm:
                term = (Mp - 0.7 * Fy * Sx) * ((l_cm - Lp_cm) / (Lr_cm - Lp_cm))
                m = min(Cb * (Mp - term), Mp)
            else:
                slend = (l_cm / r_ts)
                fcr = (Cb * math.pi**2 * E) / (slend**2) * math.sqrt(1 + 0.078 * val_A * slend**2)
                m = min(fcr * Sx, Mp)
            y_vals.append(m/100)

        fig = go.Figure()

        # เส้นกราฟหลัก
        fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', name='Mn Capacity', line=dict(color='#334155', width=3)))

        # จุด Simulation
        fig.add_trace(go.Scatter(
            x=[lb_sim], y=[mn_sim_kgm], 
            mode='markers', 
            name='Simulation Point', 
            marker=dict(size=14, color=zone_color, symbol='diamond', line=dict(width=2, color='white'))
        ))

        # จุด Actual Design (ถ้าค่า Simulation ไม่ตรงกับค่าจริง ให้โชว์จุดจริงจางๆ ด้วย)
        if abs(lb_sim - Lb_real) > 0.05:
             # คำนวณ Mn จริงเพื่อ plot จุด
             # (ใช้ logic เดียวกับข้างบน หรือดึงจาก data ถ้ามี Mn_real ส่งมา แต่คำนวณใหม่ชัวร์สุด)
             if (Lb_real*100) <= Lp_cm: mn_real = Mp
             elif (Lb_real*100) <= Lr_cm:
                 term_r = (Mp - 0.7 * Fy * Sx) * (((Lb_real*100) - Lp_cm) / (Lr_cm - Lp_cm))
                 mn_real = min(Cb * (Mp - term_r), Mp)
             else:
                 slend_r = ((Lb_real*100) / r_ts)
                 fcr_r = (Cb * math.pi**2 * E) / (slend_r**2) * math.sqrt(1 + 0.078 * val_A * slend_r**2)
                 mn_real = min(fcr_r * Sx, Mp)
             
             fig.add_trace(go.Scatter(
                x=[Lb_real], y=[mn_real/100],
                mode='markers', name='Actual Input',
                marker=dict(size=10, color='gray', symbol='x', opacity=0.7)
             ))

        # ตกแต่ง Zones (Background shading)
        # Zone 1: Green
        fig.add_vrect(x0=0, x1=Lp_m, fillcolor="green", opacity=0.1, layer="below", line_width=0, annotation_text="Plastic", annotation_position="top left")
        # Zone 2: Orange
        fig.add_vrect(x0=Lp_m, x1=Lr_m, fillcolor="orange", opacity=0.1, layer="below", line_width=0, annotation_text="Inelastic", annotation_position="top left")
        # Zone 3: Red
        fig.add_vrect(x0=Lr_m, x1=max_len, fillcolor="red", opacity=0.1, layer="below", line_width=0, annotation_text="Elastic Buckling", annotation_position="top left")

        fig.update_layout(
            title="Nominal Moment Capacity ($M_n$) Curve",
            xaxis_title="Unbraced Length ($L_b$) [m]",
            yaxis_title="$M_n$ [kg-m]",
            margin=dict(l=20, r=20, t=40, b=20),
            height=380,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- PART 3: EXPLANATION ---
    st.divider()
    with st.expander("📚 ความหมายของแต่ละ Zone (คลิกเพื่ออ่าน)", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            **Zone 1: Plastic ($L_b \le {Lp_m:.2f}$ m)**
            - เหล็กรับแรงได้เต็มพิกัด ($M_p$)
            - ไม่เกิดการโก่งเดาะ (Buckling)
            - **คำแนะนำ:** ปลอดภัยที่สุด ใช้ค้ำยันถี่
            """)
        with c2:
            st.markdown(f"""
            **Zone 2: Inelastic ($L_b \le {Lr_m:.2f}$ m)**
            - เหล็กเริ่มเสียกำลังบางส่วน
            - เกิด Buckling แบบ Inelastic
            - กำลังรับโมเมนต์ลดลงเป็นเส้นตรง
            """)
        with c3:
            st.markdown(f"""
            **Zone 3: Elastic ($L_b > {Lr_m:.2f}$ m)**
            - **อันตราย:** เหล็กจะพลิกตัว (Buckle) ก่อนที่เนื้อเหล็กจะคราก
            - กำลังรับแรงลดลงฮวบฮาบ
            - **คำแนะนำ:** ควรเพิ่มจุดค้ำยัน (Bracing)
            """)
