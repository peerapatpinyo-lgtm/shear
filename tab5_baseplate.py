# ==========================================
# 🧱 tab5_baseplate.py
# ==========================================
import streamlit as st
import math

def render(res_ctx, v_design):
    st.subheader("🧱 Base Plate Design (AISC 360-22)")
    
    # ดึงค่าจากหน้าแรกมาใช้ (No need to re-input)
    h = res_ctx['h'] / 10  # convert to cm
    b = res_ctx['b'] / 10  # convert to cm
    Fy = res_ctx['Fy']
    is_lrfd = res_ctx['is_lrfd']
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 📥 Input Parameters")
        fc_prime = st.number_input("Concrete Strength f'c (ksc)", 150, 450, 240)
        
        st.markdown("##### Plate Dimensions")
        c1, c2 = st.columns(2)
        with c1:
            N = st.number_input("Plate Length N (cm)", value=float(math.ceil(h + 10)))
        with c2:
            B = st.number_input("Plate Width B (cm)", value=float(math.ceil(b + 10)))
            
    # --- Engineering Calculation ---
    A1 = N * B
    # Bearing Strength Pp = 0.85 * f'c * A1 (Simplified)
    if is_lrfd:
        phi_c = 0.65
        Pp = phi_c * (0.85 * fc_prime * A1)
    else:
        omega_c = 2.31
        Pp = (0.85 * fc_prime * A1) / omega_c
        
    # Thickness Calculation (m, n distance)
    m = (N - 0.95 * h) / 2
    n = (B - 0.80 * b) / 2
    lambda_prime = 1.0 # Simplified
    l_max = max(m, n)
    
    # Required thickness
    if is_lrfd:
        Pu = v_design
        t_req = l_max * math.sqrt((2 * Pu) / (0.9 * Fy * B * N)) if A1 > 0 else 0
    else:
        Pa = v_design
        t_req = l_max * math.sqrt((2 * Pa * 1.67) / (Fy * B * N)) if A1 > 0 else 0

    with col2:
        st.markdown("#### 📤 Design Results")
        ratio = v_design / Pp if Pp > 0 else 0
        color = "green" if ratio < 1 else "red"
        
        st.markdown(f"""
        <div class="calc-sheet">
            <div class="calc-header"><span>Bearing Check</span><span style="color:{color}">{ratio:.2%}</span></div>
            <div class="calc-row"><span class="calc-label">Applied Load:</span><span class="calc-val">{v_design:,.0f} kg</span></div>
            <div class="calc-row"><span class="calc-label">Concrete Capacity:</span><span class="calc-val">{Pp:,.0f} kg</span></div>
            <div class="calc-formula">m = {m:.2f} cm, n = {n:.2f} cm</div>
            <hr>
            <div class="calc-row"><span class="calc-label" style="color:#1e40af;">Min Thickness Required:</span><span class="calc-val" style="color:#1e40af; font-size:1.2em;">{t_req*10:.2f} mm</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.success(f"✅ แนะนำให้ใช้แผ่นเหล็กขนาด {int(N*10)}x{int(B*10)} mm ความหนาอย่างน้อย {math.ceil(t_req*10)} mm")
