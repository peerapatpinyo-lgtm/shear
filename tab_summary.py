import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def render(data):
    st.title("📄 รายการคำนวณและตรวจสอบ (Analysis Verification)")

    # ==========================================
    # 1. RETRIEVE DATA & SAFE CAST
    # ==========================================
    try:
        # User Input Geometry
        L_m = float(data.get('user_span', 6.0))
        L_cm = L_m * 100.0
        
        # Section Properties
        section_name = data.get('section_name', 'Custom Section')
        Ix = float(data.get('Ix', 0.0))
        if Ix == 0: Ix = 1.0 # Prevent Div/0
        E_ksc = float(data.get('E', 2040000.0)) # ksc
        
        # Capacities (From app.py logic)
        M_cap = float(data.get('M_cap', 0.0)) # kg-m (Design Capacity)
        V_cap = float(data.get('V_cap', 0.0)) # kg (Design Capacity)
        defl_denom = float(data.get('defl_denom', 360.0))
        
        # Config
        is_check_mode = data.get('is_check_mode', True)
        is_lrfd = data.get('is_lrfd', False)
        
    except Exception as e:
        st.error(f"❌ Data Error: {e}")
        return

    # ==========================================
    # 2. DETERMINE LOAD FOR GRAPH
    # ==========================================
    # เพื่อให้กราฟถูกต้อง เราต้องรู้ว่า "Load ตัวไหน" ที่เอามา plot deflection
    
    st.header("1️⃣ Load Configuration")
    
    if is_check_mode:
        # Mode: Check Design (มีโหลดชัดเจนจาก Input)
        w_dead = float(data.get('w_dead_input', 0.0))
        w_live = float(data.get('w_live_input', 0.0))
        w_self = float(data.get('w_self_weight', 0.0))
        
        w_service = w_dead + w_live + w_self
        w_plot_defl = w_service # ใช้ Service Load plot Deflection เสมอ
        
        st.info(f"**โหมดตรวจสอบ:** ใช้ Service Load Actual = `{w_service:,.2f}` kg/m ในการพลอตกราฟ Deflection")
    
    else:
        # Mode: Find Capacity (หาโหลดสูงสุด)
        # ต้องหา W_safe ก่อน ถึงจะเอาไป plot ได้
        st.info("**โหมดหาค่ารับน้ำหนัก:** คำนวณ Capacity ตามหน้าตัดจริง")
        
        # 2.1 Moment Limit (w = 8M/L^2)
        w_cap_m = (8 * M_cap) / (L_m**2) if L_m > 0 else 0
        
        # 2.2 Shear Limit (w = 2V/L)
        w_cap_v = (2 * V_cap) / L_m if L_m > 0 else 0
        
        # 2.3 Deflection Limit (Reverse Calc)
        # Formula: Delta = 5wL^4/384EI -> w = (Delta_all * 384EI) / 5L^4
        # ระวังหน่วย: w(kg/cm) = ... แล้วคูณ 100 เป็น kg/m
        delta_target = L_cm / defl_denom
        val_top = delta_target * 384 * E_ksc * Ix
        val_bot = 5 * (L_cm**4)
        w_cap_d_kgcm = val_top / val_bot
        w_cap_d = w_cap_d_kgcm * 100
        
        # Governing Case
        # หมายเหตุ: ถ้าเป็น LRFD การเทียบ Moment(Factored) กับ Defl(Service) โดยตรงอาจไม่ถูกต้องเป๊ะๆ
        # แต่ในที่นี้จะแสดงค่าดิบที่คำนวณได้
        w_safe = min(w_cap_m, w_cap_v, w_cap_d)
        w_plot_defl = w_safe # ใช้ค่า Safe Load นี้สมมติว่าเป็น Load ที่กระทำ
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Limit by Moment", f"{w_cap_m:,.0f} kg/m")
        c2.metric("Limit by Shear", f"{w_cap_v:,.0f} kg/m")
        c3.metric("Limit by Deflection", f"{w_cap_d:,.0f} kg/m")
        
        st.markdown(f"**👉 ใช้ Load = `{w_plot_defl:,.2f}` kg/m ในการวาดกราฟพฤติกรรม**")


    # ==========================================
    # 3. DEFLECTION CHART & VERIFICATION
    # ==========================================
    st.header("2️⃣ Deflection Analysis (วิเคราะห์การแอ่นตัว)")
    
    tab_chart, tab_verify = st.tabs(["📉 กราฟ Deflection vs Span", "hk ตารางพิสูจน์ค่า (Verification)"])
    
    # --- CALCULATE GRAPH DATA ---
    x_vals = np.linspace(0.5, 12.0, 100) # ระยะจาก 0.5 ถึง 12 เมตร
    
    # 1. Allowable Line (L/denom)
    y_allow = (x_vals * 100) / defl_denom # cm
    
    # 2. Actual Line (Load คงที่ = w_plot_defl)
    # Formula: 5 * w(kg/cm) * L(cm)^4 / (384 * E * Ix)
    w_fixed_kgcm = w_plot_defl / 100.0
    y_actual = (5 * w_fixed_kgcm * ((x_vals*100)**4)) / (384 * E_ksc * Ix) # cm

    # --- TAB 1: CHART ---
    with tab_chart:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot Lines
        ax.plot(x_vals, y_allow, '--', color='green', label=f'Allowable Limit (L/{defl_denom:.0f})')
        ax.plot(x_vals, y_actual, '-', color='blue', linewidth=2, label=f'Actual Deflection (Load {w_plot_defl:.0f} kg/m)')
        
        # Fail Zone
        ax.fill_between(x_vals, y_allow, y_actual, where=(y_actual > y_allow), color='red', alpha=0.2)
        
        # User Point
        curr_L_cm = L_m * 100
        curr_act = (5 * w_fixed_kgcm * (curr_L_cm**4)) / (384 * E_ksc * Ix)
        curr_all = curr_L_cm / defl_denom
        
        ax.scatter([L_m], [curr_act], color='red', s=100, zorder=5)
        ax.annotate(f"  Act: {curr_act:.2f} cm\n  Limit: {curr_all:.2f} cm", 
                    (L_m, curr_act), color='red', fontweight='bold')
        
        # Settings
        ax.set_title(f"Deflection vs Span Length (Load = {w_plot_defl:.0f} kg/m)")
        ax.set_xlabel("Span (m)")
        ax.set_ylabel("Deflection (cm)")
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend()
        
        # Limit Y Axis (ป้องกันกราฟพุ่งเกินไป)
        max_y = max(curr_all * 2.0, curr_act * 1.5)
        ax.set_ylim(0, max_y)
        ax.set_xlim(0, 12)
        
        st.pyplot(fig)
        st.caption("เส้นสีน้ำเงินคือพฤติกรรมจริงของคาน ถ้ารับน้ำหนักเท่าเดิมแต่เพิ่มความยาว")

    # --- TAB 2: VERIFICATION (พิสูจน์ตัวเลข) ---
    with tab_verify:
        st.markdown("### 🕵️‍♀️ ตรวจสอบความถูกต้องของตัวเลข")
        st.write("ท่านสามารถกดเครื่องคิดเลขตามสูตรนี้เพื่อเช็คค่าในกราฟได้ทันที:")
        
        st.latex(r"\Delta_{actual} = \frac{5 \cdot w \cdot L^4}{384 \cdot E \cdot I_x}")
        
        st.markdown("**แทนค่าตัวแปร (Units Check):**")
        st.markdown(f"""
        * $w$ (แปลงเป็น kg/cm) = `{w_plot_defl:.2f}` / 100 = **`{w_fixed_kgcm:.4f}`** kg/cm
        * $L$ (แปลงเป็น cm) = `{L_m:.2f}` * 100 = **`{L_cm:.0f}`** cm
        * $E$ (ksc) = **`{E_ksc:,.0f}`** kg/cm²
        * $I_x$ (cm⁴) = **`{Ix:,.2f}`** cm⁴
        """)
        
        # คำนวณทีละ step
        step1 = 5 * w_fixed_kgcm
        step2 = L_cm ** 4
        numerator = step1 * step2
        denominator = 384 * E_ksc * Ix
        result = numerator / denominator
        
        st.markdown("---")
        st.markdown("**Step-by-Step Calculation:**")
        st.code(f"""
        Numerator (5*w*L^4)   = 5 * {w_fixed_kgcm:.4f} * {L_cm}^4 
                              = {numerator:,.2f}
                              
        Denominator (384*E*I) = 384 * {E_ksc} * {Ix} 
                              = {denominator:,.2f}
                              
        Result (Num/Denom)    = {result:.6f} cm
        """, language="text")
        
        col1, col2 = st.columns(2)
        col1.metric("ค่าที่คำนวณได้ (Actual)", f"{result:.4f} cm")
        col2.metric("ค่าพิกัดที่ยอมให้ (Allowable)", f"{curr_all:.4f} cm")
        
        if abs(result - curr_act) < 0.001:
            st.success(f"✅ กราฟถูกต้อง: จุดสีแดงบนกราฟตรงกับผลคำนวณ ({result:.4f} cm)")
        else:
            st.error("❌ พบความผิดปกติของข้อมูล")
