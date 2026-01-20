import streamlit as st
import math

def render(res_ctx, v_design):
    st.subheader("🧱 Column & Base Plate Design (AISC 360-22)")
    
    # --- 1. ดึงข้อมูลจาก Context หลัก ---
    h = res_ctx['h'] / 10      # cm
    b = res_ctx['b'] / 10      # cm
    tw = res_ctx['tw'] / 10    # cm
    tf = res_ctx['tf'] / 10    # cm
    Ag = res_ctx['ry']**2 * 0 + (2*b*tf + (h-2*tf)*tw) # Recalculate Ag in cm2
    ry = res_ctx['ry']         # Radius of gyration y-axis (cm)
    Fy = res_ctx['Fy']
    E = res_ctx['E']
    is_lrfd = res_ctx['is_lrfd']

    st.markdown("---")
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.markdown("#### 📏 Column Stability (Buckling)")
        # รับค่าความสูงเสา
        col_height = st.number_input("Column Height (m)", 0.5, 20.0, 3.0, step=0.1)
        k_factor = st.selectbox("Effective Length Factor (K)", 
                              options=[2.1, 1.0, 0.8, 0.65], 
                              format_func=lambda x: f"K={x} (Fixed-Free)" if x==2.1 else f"K={x}")
        
        st.markdown("#### 🧱 Base Plate Parameters")
        fc_prime = st.number_input("Concrete Strength f'c (ksc)", 150, 450, 240)
        N = st.number_input("Plate Length N (cm)", value=float(math.ceil(h + 10)))
        B = st.number_input("Plate Width B (cm)", value=float(math.ceil(b + 10)))

    # --- 2. Engineering Logic: Column Buckling ---
    L = col_height * 100  # m to cm
    slenderness = (k_factor * L) / ry
    
    # Euler Buckling Stress (Fe)
    Fe = (math.pi**2 * E) / (slenderness**2)
    
    # Critical Stress (Fcr)
    if slenderness <= 4.71 * math.sqrt(E/Fy):
        Fcr = (0.658**(Fy/Fe)) * Fy
    else:
        Fcr = 0.877 * Fe
    
    Pn = Fcr * Ag # Nominal Strength (kg)
    
    if is_lrfd:
        phi_comp = 0.90
        P_available = phi_comp * Pn
    else:
        omega_comp = 1.67
        P_available = Pn / omega_comp

    # --- 3. Engineering Logic: Base Plate ---
    A1 = N * B
    if is_lrfd:
        Pp = 0.65 * (0.85 * fc_prime * A1)
        t_req = ((N-0.95*h)/2) * math.sqrt((2*v_design)/(0.9*Fy*B*N))
    else:
        Pp = (0.85 * fc_prime * A1) / 2.31
        t_req = ((N-0.95*h)/2) * math.sqrt((2*v_design*1.67)/(Fy*B*N))

    # --- 4. การแสดงผลลัพธ์ ---
    with col2:
        # ส่วนแสดงผลเสา
        st.markdown("#### 📤 Column Analysis")
        col_ratio = v_design / P_available
        status_color = "red" if col_ratio > 1 or slenderness > 200 else "green"
        
        st.markdown(f"""
        <div class="calc-sheet">
            <div class="calc-header"><span>Column Capacity</span><span style="color:{status_color}">{col_ratio:.2%}</span></div>
            <div class="calc-row"><span class="calc-label">Slenderness (KL/r):</span><span class="calc-val">{slenderness:.2f}</span></div>
            <div class="calc-row"><span class="calc-label">Max Axial Capacity:</span><span class="calc-val">{P_available:,.0f} kg</span></div>
            <div class="calc-formula">{"⚠️ เสาชะลูดเกินไป (KL/r > 200)" if slenderness > 200 else "✅ ความชะลูดอยู่ในเกณฑ์ดี"}</div>
        </div>
        """, unsafe_allow_html=True)

        # ส่วนแสดงผล Base Plate
        st.markdown("#### 📤 Base Plate Analysis")
        bp_ratio = v_design / Pp
        st.markdown(f"""
        <div class="calc-sheet" style="border-top: 4px solid #10b981;">
            <div class="calc-header"><span>Bearing Check</span><span>{bp_ratio:.2%}</span></div>
            <div class="calc-row"><span class="calc-label">Concrete Capacity:</span><span class="calc-val">{Pp:,.0f} kg</span></div>
            <div class="calc-row"><span class="calc-label" style="color:#2563eb;">Required Plate Thickness:</span><span class="calc-val" style="color:#2563eb; font-weight:bold;">{t_req*10:.2f} mm</span></div>
        </div>
        """, unsafe_allow_html=True)

    if col_ratio > 1:
        st.error(f"❌ เสาขนาด {res_ctx['sec_name']} รับแรงไม่ไหว! กรุณาเพิ่มขนาดหน้าตัด")
    elif slenderness > 200:
        st.warning("⚠️ เสาสอบผ่านแรงกด แต่มีความชะลูดสูงเกินมาตรฐาน AISC (KL/r > 200)")
    else:
        st.success(f"✅ เสาขนาด {res_ctx['sec_name']} มั่นคงแข็งแรงและสอบผ่านการคำนวณ")
