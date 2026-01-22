# tab_summary.py
import streamlit as st
import plotly.graph_objects as go

def render(data):
    # --- 1. ข้อมูลนำเข้า (Input Data) ---
    L_m = data['user_span']
    L_cm = L_m * 100
    is_lrfd = data.get('is_lrfd', False)
    Fy = data.get('Fy', 2500)
    E = data.get('E', 2040000)
    
    # ดึงค่าพิกัดหน้าตัด (Geometry)
    name = data.get('section_name', 'H-Beam')
    d_cm = data.get('d', 0)    # ความลึกหน้าตัด (cm)
    tw_cm = data.get('tw', 0)  # ความหนาเอว (cm)
    Ix = data.get('Ix', 0)
    
    st.title("📄 รายการคำนวณโครงสร้าง (Detailed Calculation Sheet)")

    # --- ส่วนที่ 1: ที่มาของน้ำหนักบรรทุก (Load Calculation) ---
    st.subheader("1️⃣ การวิเคราะห์น้ำหนักบรรทุก (Total Design Load, $W$)")
    with st.container(border=True):
        st.markdown("**1.1 องค์ประกอบของน้ำหนัก (Load Components):**")
        
        # กรณี Check Design
        if data.get('is_check_mode', True):
            w_dead = data.get('w_dead_input', 0)
            w_live = data.get('w_live_input', 0)
            w_self = data.get('w_self_weight', 0)
            w_total = w_dead + w_live + w_self
            
            st.write(f"- $w_{{dead}}$ (น้ำหนักบรรทุกคงที่เพิ่มเติม): `{w_dead:,.2f}` kg/m")
            st.write(f"- $w_{{live}}$ (น้ำหนักบรรทุกจร): `{w_live:,.2f}` kg/m")
            st.write(f"- $w_{{self\_weight}}$ (น้ำหนักหน้าตัดเหล็ก {name}): `{w_self:,.2f}` kg/m")
            
            st.markdown("**รวมน้ำหนักบรรทุกแผ่ (Total Uniform Load):**")
            st.latex(r"w_{total} = w_{dead} + w_{live} + w_{self\_weight}")
            st.latex(rf"w_{{total}} = {w_dead:,.2f} + {w_live:,.2f} + {w_self:,.2f} = {w_total:,.2f} \text{{ kg/m}}")
        else:
            # กรณี Find Capacity
            w_total = data.get('w_safe', 0)
            st.info(f"โหมดคำนวณกลับ: น้ำหนักบรรทุกปลอดภัยสูงสุดที่ยอมให้ ($w_{{safe}}$)")
            st.latex(rf"w_{{total}} = {w_total:,.2f} \text{{ kg/m}}")

    # --- ส่วนที่ 2: การตรวจสอบแรงเฉือน (Shear Strength Check) ---
    st.markdown("---")
    st.subheader("2️⃣ การตรวจสอบกำลังรับแรงเฉือน (Shear Strength Analysis)")
    with st.container(border=True):
        # 2.1 หาแรงเฉือนสูงสุด
        st.markdown("**2.1 แรงเฉือนที่เกิดจากน้ำหนักบรรทุก (Shear Demand):**")
        st.latex(r"V_{act} = \frac{w_{total} \cdot L}{2}")
        st.latex(rf"V_{{act}} = \frac{{{w_total:,.2f} \text{{ kg/m}} \cdot {L_m:,.2f} \text{{ m}}}}{{2}} = {data['v_act']:,.2f} \text{{ kg}}")

        # 2.2 กำลังรับแรงเฉือนของหน้าตัด
        st.markdown("**2.2 กำลังรับแรงเฉือนของหน้าตัด (Shear Capacity Calculation):**")
        st.write(f"คำนวณจากพื้นที่หน้าตัดส่วนเอว (Web Area) ของเหล็ก `{name}`:")
        
        # สมการพื้นที่ Web
        st.latex(rf"A_w = d \cdot t_w = {d_cm:,.1f} \text{{ cm}} \cdot {tw_cm:,.2f} \text{{ cm}} = {d_cm*tw_cm:,.2f} \text{{ cm}}^2")
        
        # กำลังเฉือนที่สภาวะขีดจำกัด
        st.latex(r"V_n = 0.6 \cdot F_y \cdot A_w")
        Vn = 0.6 * Fy * (d_cm * tw_cm)
        st.latex(rf"V_n = 0.6 \cdot {Fy:,.0f} \cdot {d_cm*tw_cm:,.2f} = {Vn:,.2f} \text{{ kg}}")

        # การประยุกต์ใช้ตัวคูณลดกำลัง (Factor)
        if is_lrfd:
            phi_v = 1.0
            V_cap = phi_v * Vn
            st.markdown(f"**ตามมาตรฐาน LRFD ($\phi_v = {phi_v}$):**")
            st.latex(rf"\phi_v V_n = {phi_v} \cdot {Vn:,.2f} = {V_cap:,.2f} \text{{ kg}}")
        else:
            omega_v = 1.67
            V_cap = Vn / omega_v
            st.markdown(f"**ตามมาตรฐาน ASD ($\Omega_v = {omega_v}$):**")
            st.latex(rf"V_n / \Omega_v = \frac{{{Vn:,.2f}}}{{{omega_v}}} = {V_cap:,.2f} \text{{ kg}}")

        # สรุป Ratio แรงเฉือน
        st.latex(rf"Ratio_V = \frac{{V_{{act}}}}{{V_{{cap}}}} = \frac{{{data['v_act']:,.2f}}}{{{V_cap:,.2f}}} = {data['ratio_v']:.4f}")

    # --- ส่วนที่ 3: การตรวจสอบการแอ่นตัว (Deflection Check) ---
    st.markdown("---")
    st.subheader("3️⃣ การตรวจสอบการแอ่นตัว (Deflection Serviceability)")
    with st.container(border=True):
        w_kgcm = w_total / 100
        st.markdown("**3.1 พารามิเตอร์ที่ใช้คำนวณ:**")
        st.write(f"- $w$ (หน่วย cm) = `{w_kgcm:.4f}` kg/cm")
        st.write(f"- $L$ (หน่วย cm) = `{L_cm:,.0f}` cm")
        
        st.markdown("**3.2 การคำนวณค่าการแอ่นตัวจริง:**")
        st.latex(rf"\Delta_{{act}} = \frac{{5 \cdot {w_kgcm:.4f} \cdot {L_cm:,.0f}^4}}{{384 \cdot {E:,.0f} \cdot {Ix:,.2f}}} = {data['d_act']:.4f} \text{{ cm}}")
        
        st.markdown("**3.3 การเปรียบเทียบกับพิกัดที่ยอมให้:**")
        st.latex(rf"\Delta_{{all}} = \frac{{{L_cm:,.0f}}}{{{data['defl_denom']}}} = {data['d_allow']:.4f} \text{{ cm}}")
        st.latex(rf"Ratio_\Delta = \frac{{{data['d_act']:.4f}}}{{{data['d_allow']:.4f}}} = {data['ratio_d']:.4f}")

    # --- ส่วนท้าย: สรุปผล ---
    st.divider()
    gov_color = "red" if data['gov_ratio'] > 1.0 else "green"
    st.markdown(f"""
    <div style="text-align:center; padding:20px; border:3px solid {gov_color}; border-radius:15px;">
        <h2 style="color:{gov_color}; margin-bottom:0;">Governing Ratio: {data['gov_ratio']:.2%}</h2>
        <p style="font-size:1.2em;">สาเหตุที่ควบคุม: <b>{data['gov_cause']}</b></p>
    </div>
    """, unsafe_allow_html=True)
