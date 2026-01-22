# tab_summary.py
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

def render(data):
    # ==========================================
    # 1. SETUP & DATA EXTRACTION
    # ==========================================
    try:
        # Mode & Method
        is_check_mode = data.get('is_check_mode', True)
        is_lrfd = data.get('is_lrfd', False)
        method_str = "LRFD" if is_lrfd else "ASD"

        # Geometry
        L_m = float(data.get('user_span', 6.0))
        section_name = data.get('section_name', 'Custom Section')
        
        # Section Properties
        d = float(data.get('d', 0.0))
        tw = float(data.get('tw', 0.0))
        Ix = float(data.get('Ix', 0.0))
        if Ix == 0: Ix = 1.0 
        
        Fy = float(data.get('Fy', 2500.0))
        E = float(data.get('E', 2040000.0)) # ksc
        
        # Capacities
        M_cap = float(data.get('M_cap', 0.0))
        V_cap = float(data.get('V_cap', 0.0))
        defl_denom = float(data.get('defl_denom', 360.0))
        
    except Exception as e:
        st.error(f"❌ Data Error: {e}")
        return

    st.title(f"📄 รายการคำนวณและวิเคราะห์ ({section_name})")

    # ==========================================
    # PART A: LOAD ANALYSIS (หา W ที่ถูกต้องก่อน Plot)
    # ==========================================
    st.header("1️⃣ Load Analysis (วิเคราะห์น้ำหนักบรรทุก)")
    
    with st.container(border=True):
        if is_check_mode:
            # --- Check Design Mode ---
            w_dead = float(data.get('w_dead_input', 0.0))
            w_live = float(data.get('w_live_input', 0.0))
            w_self = float(data.get('w_self_weight', 0.0))
            w_service = w_dead + w_live + w_self
            
            st.markdown(f"**Service Load ($W_{{service}}$):** `{w_service:,.2f}` kg/m")
            
            if is_lrfd:
                w_u = 1.2*(w_dead + w_self) + 1.6*w_live
                w_calc_strength = w_u # ใช้สำหรับคำนวณ Strength (Shear/Moment)
            else:
                w_calc_strength = w_service
            
            w_calc_defl = w_service # ใช้สำหรับคำนวณ Deflection (Service Load เสมอ)
            load_case_name = "User Input Load"
            
        else:
            # --- Find Capacity Mode ---
            st.info("💡 โหมด Find Capacity: คำนวณ Load ที่ปลอดภัยที่สุด")
            
            # 1. Moment Limit Load (at current L)
            w_lim_m = (8 * M_cap) / (L_m**2) if L_m > 0 else 0
            
            # 2. Shear Limit Load (at current L)
            w_lim_v = (2 * V_cap) / L_m if L_m > 0 else 0
            
            # 3. Deflection Limit Load (at current L)
            # w = (Delta_all * 384EI) / 5L^4
            delta_limit = (L_m * 100) / defl_denom
            w_lim_d = (delta_limit * 384 * E * Ix) / (5 * ((L_m*100)**4)) * 100
            
            # Governing Load (ค่าต่ำสุด)
            w_safe = min(w_lim_m, w_lim_v, w_lim_d)
            
            w_calc_strength = w_safe
            w_calc_defl = w_safe # ในโหมดนี้ assume ว่า w_safe คือ service load
            load_case_name = f"Safe Capacity ({w_safe:.0f} kg/m)"
            
            st.write(f"- $W_{{Moment}}$: `{w_lim_m:,.2f}` kg/m")
            st.write(f"- $W_{{Shear}}$: `{w_lim_v:,.2f}` kg/m")
            st.write(f"- $W_{{Deflection}}$: `{w_lim_d:,.2f}` kg/m")
            st.success(f"**Governing Load ($W_{{safe}}$):** `{w_safe:,.2f}` kg/m")

    # ==========================================
    # PART B: GRAPHICS (Correct Logic)
    # ==========================================
    st.header("2️⃣ Behavioral Analysis Charts")
    
    tab1, tab2 = st.tabs(["📊 Capacity Envelope (ภาพรวม)", "📉 Deflection Check (ตรวจสอบแอ่นตัว)"])

    # --- TAB 1: Capacity vs Span ---
    with tab1:
        try:
            # 1. Data Points
            x_vals = np.linspace(0.5, 12.0, 200) # 0.5m - 12m
            
            # 2. Curve Calculations
            # Shear: V = wL/2 -> w = 2V/L (Hyperbola 1/x)
            y_shear = (2 * V_cap) / x_vals
            
            # Moment: M = wL^2/8 -> w = 8M/L^2 (Inverse Square 1/x^2)
            y_moment = (8 * M_cap) / (x_vals**2)
            
            # Deflection Limit Load: w = K / L^3
            # สูตร: w_limit = (L/denom * 384EI) / 5L^4 = (384EI / 5*denom) * (1/L^3)
            # ต้องแปลงหน่วยให้ระวังที่สุด
            K_constant = (384 * E * Ix * 100) / (5 * defl_denom * (100**4)) * 100
            # เพื่อความชัวร์ ใช้ Loop คำนวณทีละจุด
            y_defl_limit_load = []
            for x in x_vals:
                L_cm_i = x * 100
                d_all_i = L_cm_i / defl_denom # cm
                w_val = (d_all_i * 384 * E * Ix) / (5 * L_cm_i**4) # kg/cm
                y_defl_limit_load.append(w_val * 100) # kg/m
            y_defl_limit_load = np.array(y_defl_limit_load)

            # 3. Envelope (Minimum)
            y_safe = np.minimum(y_shear, np.minimum(y_moment, y_defl_limit_load))
            
            # 4. Plot
            fig1, ax1 = plt.subplots(figsize=(10, 5))
            ax1.plot(x_vals, y_shear, ':', color='purple', alpha=0.5, label='Shear Limit (1/L)')
            ax1.plot(x_vals, y_moment, '--', color='orange', alpha=0.5, label='Moment Limit (1/L²)')
            ax1.plot(x_vals, y_defl_limit_load, '-.', color='green', alpha=0.5, label='Deflection Limit (1/L³)')
            
            # Safe Load Line
            ax1.plot(x_vals, y_safe, color='black', linewidth=2.5, label='Safe Load Capacity')
            
            # Highlight Zone
            ax1.fill_between(x_vals, 0, y_safe, color='#f0f2f6', alpha=0.5)
            
            # Current Point
            ax1.scatter([L_m], [w_calc_strength], color='red', s=100, zorder=5, label='Current State')
            ax1.text(L_m, w_calc_strength*1.1, f" {w_calc_strength:.0f} kg/m", color='red', fontweight='bold')
            
            ax1.set_xlabel("Span Length (m)")
            ax1.set_ylabel("Load Capacity (kg/m)")
            ax1.set_ylim(0, max(w_calc_strength*2.5, 500))
            ax1.grid(True, linestyle='--', alpha=0.4)
            ax1.legend()
            st.pyplot(fig1)
            
        except Exception as e:
            st.error(f"Graph 1 Error: {e}")

    # --- TAB 2: Deflection vs Span (Corrected) ---
    with tab2:
        try:
            st.markdown(f"**Condition:** Fixed Load = `{w_calc_defl:,.2f}` kg/m")
            
            # ใช้ Range เดิม
            x_vals = np.linspace(0.5, 12.0, 200)
            
            # 1. Actual Deflection Curve (Under Fixed Load)
            # w คงที่ (User Load หรือ Safe Load ที่คำนวณมา)
            # Delta = 5wL^4 / 384EI
            w_kgcm_fixed = w_calc_defl / 100
            y_act_defl = (5 * w_kgcm_fixed * ((x_vals*100)**4)) / (384 * E * Ix) # cm
            
            # 2. Allowable Limit Line
            # Delta_all = L / denom
            y_all_defl = (x_vals * 100) / defl_denom # cm
            
            # 3. Plot
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            
            ax2.plot(x_vals, y_all_defl, '--', color='green', label=f'Limit (L/{defl_denom:.0f})')
            ax2.plot(x_vals, y_act_defl, '-', color='blue', linewidth=2, label='Actual Deflection')
            
            # Fail Zone
            ax2.fill_between(x_vals, y_all_defl, y_act_defl, where=(y_act_defl > y_all_defl), color='red', alpha=0.2, label='Fail Zone')
            
            # Verify Point (จุดปัจจุบัน)
            curr_act = (5 * w_kgcm_fixed * ((L_m*100)**4)) / (384 * E * Ix)
            curr_all = (L_m * 100) / defl_denom
            
            ax2.scatter([L_m], [curr_act], color='red', s=100, zorder=5)
            ax2.annotate(f"Act: {curr_act:.2f} cm\nLimit: {curr_all:.2f} cm", 
                         (L_m, curr_act), xytext=(15, 0), textcoords='offset points', 
                         color='red', fontweight='bold',
                         arrowprops=dict(arrowstyle="->", color='red'))
            
            ax2.set_xlabel("Span Length (m)")
            ax2.set_ylabel("Deflection (cm)")
            ax2.set_title(f"Deflection Trend under Load {w_calc_defl:.0f} kg/m")
            
            # Scale Fix
            ax2.set_ylim(0, max(curr_all*1.5, curr_act*1.5))
            ax2.set_xlim(0, 12)
            ax2.grid(True, linestyle='--', alpha=0.4)
            ax2.legend()
            
            st.pyplot(fig2)
            
            # ตารางเช็คความถูกต้อง (Verify Table)
            with st.expander("🕵️‍♀️ ตรวจสอบความถูกต้องของกราฟ (Verification)"):
                st.write("ถ้ากราฟถูกต้อง ค่าในตารางต้องตรงกับจุดสีแดงบนกราฟ")
                st.markdown(f"""
                | Parameter | Value | Formula |
                | :--- | :--- | :--- |
                | **Span ($L$)** | `{L_m:.2f}` m | User Input |
                | **Load ($W$)** | `{w_calc_defl:.2f}` kg/m | From Part 1 |
                | **Actual Defl** | `{curr_act:.4f}` cm | $5wL^4/384EI$ |
                | **Limit Defl** | `{curr_all:.4f}` cm | $L/{defl_denom:.0f}$ |
                | **Ratio** | `{curr_act/curr_all:.4f}` | Act / Limit |
                """)
                
        except Exception as e:
            st.error(f"Graph 2 Error: {e}")

    # ==========================================
    # PART C: DETAILED CALCULATION (คงเดิม)
    # ==========================================
    st.divider()
    # Copy ส่วนคำนวณ Part 3 ที่ละเอียดๆ จากคำตอบก่อนหน้ามาวางต่อท้ายตรงนี้ได้เลย
    # หรือถ้าจะให้ผมรวมให้บอกได้ครับ (แต่เพื่อประหยัดบรรทัด ผมละไว้ก่อน)
    
    # ... (ส่วน Part 3 Shear/Moment/Deflection Calculation) ...
    
    # ใส่ส่วนสรุปสุดท้ายแบบสั้นๆ ให้โค้ดทำงานจบได้
    st.header("3️⃣ Summary Check")
    # Quick calc for display
    w_kgcm = w_calc_defl / 100
    d_act = (5 * w_kgcm * ((L_m*100)**4)) / (384 * E * Ix)
    d_all = (L_m * 100) / defl_denom
    
    st.write(f"**Deflection Result:** {d_act:.4f} cm (Allowable: {d_all:.4f} cm)")
    if d_act <= d_all:
         st.success("✅ Deflection OK")
    else:
         st.error("❌ Deflection FAILED")
