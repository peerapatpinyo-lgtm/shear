# tab_summary.py
import streamlit as st
import plotly.graph_objects as go

def render(data):
    # --- 1. ข้อมูลพื้นฐาน ---
    is_lrfd = data.get('is_lrfd', False)
    method_name = "LRFD" if is_lrfd else "ASD"
    
    # หน้าตัดและสมบัติ
    name = data.get('section_name', 'H-Beam')
    d = data.get('d', 40) # depth (cm)
    tw = data.get('tw', 0.8) # web thickness (cm)
    Fy = data.get('Fy', 2500)
    E = data.get('E', 2040000)
    
    # Loads
    L_m = data['user_span']
    w_live = data.get('w_live', 0) # สมมติว่ามี key นี้ใน data
    w_dead = data.get('w_dead', 0) # สมมติว่ามี key นี้ใน data
    w_self = data.get('w_self_weight', 0)
    w_total = data['w_load'] if data.get('is_check_mode', True) else data.get('w_safe', 0)

    st.title("📑 รายการคำนวณโดยละเอียด (Full Structural Report)")

    # --- ส่วนที่ 1: ที่มาของน้ำหนักบรรทุก (Load Identification) ---
    with st.container(border=True):
        st.markdown("### 1️⃣ การวิเคราะห์น้ำหนักบรรทุก (Load Analysis)")
        st.write(f"น้ำหนักบรรทุกแผ่สม่ำเสมอ ($w$) คำนวณจาก:")
        
        # กรณี Check Design (User ใส่โหลดเอง)
        if data.get('is_check_mode', True):
            st.latex(r"w_{total} = w_{dead} + w_{live} + w_{self\_weight}")
            st.write(f"- $w_{{dead}}$ (น้ำหนักบรรทุกคงที่เพิ่มเติม): `{data.get('w_dead_input', 0):,.2f}` kg/m")
            st.write(f"- $w_{{live}}$ (น้ำหนักบรรทุกจร): `{data.get('w_live_input', 0):,.2f}` kg/m")
            st.write(f"- $w_{{self\_weight}}$ (น้ำหนักเหล็กจากการเปิดตาราง): `{w_self:,.2f}` kg/m")
            st.latex(rf"w_{{total}} = {w_total:,.2f} \text{{ kg/m}}")
        else:
            # กรณี Find Capacity
            st.info(f"อยู่ในโหมด **Find Capacity**: ค่า $w$ คือน้ำหนักบรรทุกปลอดภัยสูงสุดที่หน้าตัดรับได้")
            st.latex(rf"w_{{safe}} = {w_total:,.2f} \text{{ kg/m}}")

    # --- ส่วนที่ 2: การตรวจสอบแรงเฉือน (Shear Strength Check) ---
    st.markdown("---")
    st.subheader("2️⃣ การตรวจสอบกำลังรับแรงเฉือน (Shear Strength)")
    with st.container(border=True):
        st.markdown("**2.1 แรงเฉือนที่เกิดขึ้นจริง (Shear Demand, $V_{max}$):**")
        st.latex(r"V_{act} = \frac{w \cdot L}{2}")
        st.latex(rf"V_{{act}} = \frac{{{w_total:,.2f} \text{{ kg/m}} \cdot {L_m:,.2f} \text{{ m}}}}{{2}} = {data['v_act']:,.2f} \text{{ kg}}")

        st.markdown("**2.2 กำลังรับแรงเฉือนของหน้าตัด (Shear Capacity, $V_n$):**")
        st.write("คำนวณตามมาตรฐาน AISC (Simplified):")
        
        # คำนวณ Area of Web (Aw)
        Aw = d * tw
        st.latex(rf"A_w = d \cdot t_w = {d} \text{{ cm}} \cdot {tw} \text{{ cm}} = {Aw:,.2f} \text{{ cm}}^2")
        
        # กำลังเฉือนวิกฤต (Vn)
        Vn = 0.6 * Fy * Aw
        st.latex(r"V_n = 0.6 \cdot F_y \cdot A_w")
        st.latex(rf"V_n = 0.6 \cdot {Fy:,.0f} \cdot {Aw:,.2f} = {Vn:,.2f} \text{{ kg}}")

        # แยกตาม Method
        if is_lrfd:
            phi_v = 1.0 # สำหรับหน้าตัดส่วนใหญ่ใน AISC
            V_cap = phi_v * Vn
            st.markdown(f"**ตามวิธี LRFD ($\phi_v = {phi_v}$):**")
            st.latex(rf"\phi_v V_n = {phi_v} \cdot {Vn:,.2f} = {V_cap:,.2f} \text{{ kg}}")
        else:
            omega_v = 1.67
            V_cap = Vn / omega_v
            st.markdown(f"**ตามวิธี ASD ($\Omega_v = {omega_v}$):**")
            st.latex(rf"V_n / \Omega_v = \frac{{{Vn:,.2f}}}{{{omega_v}}} = {V_cap:,.2f} \text{{ kg}}")

        st.markdown("**2.3 อัตราส่วนแรงเฉือน (Shear Utilization Ratio):**")
        st.latex(rf"Ratio_V = \frac{{V_{{act}}}}{{V_{{cap}}}} = \frac{{{data['v_act']:,.2f}}}{{{V_cap:,.2f}}} = {data['ratio_v']:.4f}")

    # --- ส่วนที่ 3: การแอ่นตัว (Deflection - ละเอียดพิเศษ) ---
    st.markdown("---")
    st.subheader("3️⃣ การตรวจสอบการแอ่นตัว (Deflection Check)")
    with st.container(border=True):
        # แปลงหน่วย W ให้ดูอีกรอบ
        w_kgcm = w_total / 100
        L_cm = L_m * 100
        
        st.markdown("**3.1 การแทนค่าลงในสมการโก่งตัว:**")
        st.latex(rf"""
        \Delta_{{act}} = \frac{{5 \cdot ({w_kgcm:.4f} \text{{ kg/cm}}) \cdot ({L_cm:,.0f} \text{{ cm}})^4}}{{384 \cdot ({E:,.0f} \text{{ kg/cm}}^2) \cdot ({data['Ix']:,.2f} \text{{ cm}}^4)}}
        """)
        
        # ผลลัพธ์
        st.latex(rf"\Delta_{{act}} = {data['d_act']:.4f} \text{{ cm}}")
        
        st.markdown("**3.2 พิกัดที่ยอมให้และการเปรียบเทียบ:**")
        st.latex(rf"\Delta_{{all}} = \frac{{{L_cm:,.0f}}}{{{data['defl_denom']}}} = {data['d_allow']:.4f} \text{{ cm}}")
        st.latex(rf"Ratio_\Delta = \frac{{{data['d_act']:.4f}}}{{{data['d_allow']:.4f}}} = {data['ratio_d']:.4f}")

    # --- สรุปปิดท้าย ---
    st.divider()
    if data['gov_ratio'] <= 1.0:
        st.success(f"✔️ สรุปผล: หน้าตัด {name} **ผ่านเกณฑ์** ด้วยค่า Ratio {data['gov_ratio']:.2%} (ควบคุมโดย {data['gov_cause']})")
    else:
        st.error(f"❌ สรุปผล: หน้าตัด {name} **ไม่ผ่านเกณฑ์** (Ratio {data['gov_ratio']:.2%})")
