# tab_summary.py
import streamlit as st
import plotly.graph_objects as go

def render(data):
    # --- 1. SETUP & CONSTANTS ---
    is_lrfd = data.get('is_lrfd', False)
    method = "LRFD (Load and Resistance Factor Design)" if is_lrfd else "ASD (Allowable Strength Design)"
    
    # ดึงค่าพื้นฐาน
    L_m = data['user_span']
    L_cm = L_m * 100
    w_kgm = data['w_load'] if data.get('is_check_mode', True) else data.get('w_safe', 0)
    
    # Section Properties
    name = data.get('section_name', 'Unknown')
    Ix = data['Ix']
    Zx = data.get('Zx', 0)
    Sx = data.get('Sx', 0)
    Fy = data.get('Fy', 2500)
    E = data['E'] # 2,040,000 kg/cm²
    
    st.title("📄 รายการคำนวณโครงสร้างเหล็กโดยละเอียด")
    st.markdown(f"**หน้าตัด:** `{name}` | **มาตรฐานการออกแบบ:** `{method}`")

    # --- ส่วนที่ 0: คุณสมบัติหน้าตัดและการเตรียมข้อมูล ---
    with st.expander("0️⃣ การเตรียมข้อมูลและคุณสมบัติหน้าตัด (Section Properties)", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**คุณสมบัติทางเรขาคณิต:**")
            st.write(f"- $I_x$ (Moment of Inertia) = {Ix:,.2f} $cm^4$")
            st.write(f"- $S_x$ (Elastic Modulus) = {Sx:,.2f} $cm^3$")
            st.write(f"- $Z_x$ (Plastic Modulus) = {Zx:,.2f} $cm^3$")
        with col2:
            st.markdown("**คุณสมบัติวัสดุและน้ำหนัก:**")
            st.write(f"- $E$ (Modulus of Elasticity) = {E:,.0f} $kg/cm^2$")
            st.write(f"- $F_y$ (Yield Strength) = {Fy:,.0f} $kg/cm^2$")
            st.write(f"- $w$ (Total Load) = {w_kgm:,.2f} $kg/m$")

    # --- ส่วนที่ 1: การตรวจสอบการแอ่นตัว (Deflection) ---
    st.markdown("---")
    st.subheader("1️⃣ การตรวจสอบการแอ่นตัว (Deflection Serviceability)")
    
    with st.container(border=True):
        st.markdown("**1.1 การแปลงหน่วยน้ำหนัก (Load Unit Conversion):**")
        st.latex(rf"w = \frac{{{w_kgm:,.2f} \text{{ kg/m}}}}{{100}} = {w_kgm/100:.4f} \text{{ kg/cm}}")
        
        st.markdown("**1.2 คำนวณการแอ่นตัวที่เกิดขึ้นจริง ($\Delta_{{actual}}$):**")
        st.latex(r"\Delta_{act} = \frac{5 \cdot w \cdot L^4}{384 \cdot E \cdot I_x}")
        # กางตัวเลข
        st.latex(rf"""
        \Delta_{{act}} = \frac{{5 \cdot ({w_kgm/100:.4f}) \cdot ({L_cm:,.0f})^4}}{{384 \cdot ({E:,.0f}) \cdot ({Ix:,.2f})}}
        """)
        # ผลลัพธ์ขั้นกลาง
        numerator = 5 * (w_kgm/100) * (L_cm**4)
        denominator = 384 * E * Ix
        st.latex(rf"\Delta_{{act}} = \frac{{{numerator:,.2e}}}{{{denominator:,.2e}}} = {data['d_act']:.4f} \text{{ cm}}")
        
        st.markdown("**1.3 คำนวณพิกัดการแอ่นตัวที่ยอมให้ ($\Delta_{{allowable}}$):**")
        st.latex(rf"\Delta_{{all}} = \frac{{L}}{{{data['defl_denom']}}} = \frac{{{L_cm:,.0f} \text{{ cm}}}}{{{data['defl_denom']}}} = {data['d_allow']:.4f} \text{{ cm}}")
        
        st.markdown("**1.4 อัตราส่วนการแอ่นตัว (Deflection Utilization):**")
        st.latex(rf"Ratio_{{\Delta}} = \frac{{\Delta_{{act}}}}{{\Delta_{{all}}}} = \frac{{{data['d_act']:.4f}}}{{{data['d_allow']:.4f}}} = {data['ratio_d']:.4f}")

    # --- ส่วนที่ 2: แรงดัด (Flexure) ---
    st.subheader("2️⃣ การตรวจสอบกำลังรับแรงดัด (Flexural Strength)")
    with st.container(border=True):
        st.markdown("**2.1 โมเมนต์ดัดสูงสุดที่เกิดขึ้น (Required Moment, $M_u$ or $M_a$):**")
        st.latex(r"M_{req} = \frac{w \cdot L^2}{8}")
        st.latex(rf"M_{{req}} = \frac{{{w_kgm:,.2f} \cdot {L_m:,.2f}^2}}{{8}} = {data['m_act']:,.2f} \text{{ kg-m}}")
        
        st.markdown("**2.2 กำลังรับแรงดัดของหน้าตัด (Design Moment Capacity, $\phi M_n$ or $M_n/\Omega$):**")
        if is_lrfd:
            st.latex(r"\phi M_n = \phi \cdot F_y \cdot Z_x \quad (\phi = 0.90)")
            st.latex(rf"\phi M_n = 0.90 \cdot {Fy} \cdot {Zx:,.2f} = {(0.9 * Fy * Zx / 100):,.2f} \text{{ kg-m}}")
        else:
            st.latex(r"M_n / \Omega = \frac{F_y \cdot S_x}{\Omega} \quad (\Omega = 1.67)")
            st.latex(rf"M_{{all}} = \frac{{{Fy} \cdot {Sx:,.2f}}}{{1.67}} \cdot \frac{{1}}{{100}} = {data['M_cap']:,.2f} \text{{ kg-m}}")
        
        st.markdown("**2.3 อัตราส่วนแรงดัด (Moment Utilization):**")
        st.latex(rf"Ratio_{{M}} = \frac{{M_{{req}}}}{{M_{{cap}}}} = \frac{{{data['m_act']:,.2f}}}{{{data['M_cap']:,.2f}}} = {data['ratio_m']:.4f}")

    # --- ส่วนที่ 3: แรงเฉือน (Shear) ---
    st.subheader("3️⃣ การตรวจสอบกำลังรับแรงเฉือน (Shear Strength)")
    with st.container(border=True):
        st.markdown("**3.1 แรงเฉือนสูงสุดที่เกิดขึ้น (Required Shear, $V_u$ or $V_a$):**")
        st.latex(r"V_{req} = \frac{w \cdot L}{2}")
        st.latex(rf"V_{{req}} = \frac{{{w_kgm:,.2f} \cdot {L_m:,.2f}}}{{2}} = {data['v_act']:,.2f} \text{{ kg}}")
        
        st.markdown("**3.2 กำลังรับแรงเฉือนที่ยอมให้ (Shear Capacity):**")
        st.write(f"จากฐานข้อมูลหน้าตัด: $V_{{cap}}$ = {data['V_cap']:,.2f} kg")
        
        st.markdown("**3.3 อัตราส่วนแรงเฉือน (Shear Utilization):**")
        st.latex(rf"Ratio_{{V}} = \frac{{V_{{req}}}}{{V_{{cap}}}} = \frac{{{data['v_act']:,.2f}}}{{{data['V_cap']:,.2f}}} = {data['ratio_v']:.4f}")

    # --- ส่วนสรุปผลการตรวจสอบ ---
    st.markdown("---")
    st.subheader("📝 สรุปผลการตรวจสอบ (Conclusion)")
    
    # คำนวณสถานะรวม
    gov_ratio = data['gov_ratio']
    status = "ผ่าน (PASS)" if gov_ratio <= 1.0 else "ไม่ผ่าน (FAIL)"
    color = "green" if gov_ratio <= 1.0 else "red"
    
    st.markdown(f"""
    <div style="padding:20px; border-radius:10px; border: 2px solid {color}; background-color:{color}10;">
        <h3 style="color:{color}; margin-top:0;">ผลการตรวจสอบ: {status}</h3>
        <ul>
            <li>อัตราส่วนการรับแรงสูงสุด (Max Utilization): <b>{gov_ratio:.2%}</b></li>
            <li>เกณฑ์ที่ควบคุมการออกแบบ (Governing Criteria): <b>{data['gov_cause']}</b></li>
        </ul>
        <p><i>*หมายเหตุ: รายการคำนวณนี้เป็นการตรวจสอบเบื้องต้นสำหรับคานเหล็ก Simple Span รับ Uniform Load เท่านั้น</i></p>
    </div>
    """, unsafe_allow_html=True)
