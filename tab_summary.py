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
        L_cm = L_m * 100.0
        section_name = data.get('section_name', 'Custom Section')
        
        # Section Properties (Default 0.0)
        d = float(data.get('d', 0.0))
        tw = float(data.get('tw', 0.0))
        Ix = float(data.get('Ix', 0.0))
        if Ix == 0: Ix = 1.0 # Prevent Div/0
        
        Fy = float(data.get('Fy', 2500.0))
        E = float(data.get('E', 2040000.0))
        Zx = float(data.get('Zx', 0.0))
        Sx = float(data.get('Sx', 0.0))
        
        # Capacities (จาก app.py)
        M_cap = float(data.get('M_cap', 0.0))
        V_cap = float(data.get('V_cap', 0.0))
        defl_denom = float(data.get('defl_denom', 360.0))
        
    except Exception as e:
        st.error(f"❌ Data Error: {e}")
        return

    st.title(f"📄 รายการคำนวณและวิเคราะห์ ({section_name})")
    st.markdown(f"**Method:** {method_str} | **Span:** {L_m:.2f} m.")

    # ==========================================
    # PART A: LOAD ANALYSIS
    # ==========================================
    st.header("1️⃣ Load Analysis (วิเคราะห์น้ำหนักบรรทุก)")
    
    with st.container(border=True):
        if is_check_mode:
            # --- Check Design Mode ---
            w_dead = float(data.get('w_dead_input', 0.0))
            w_live = float(data.get('w_live_input', 0.0))
            w_self = float(data.get('w_self_weight', 0.0))
            w_service = w_dead + w_live + w_self
            
            st.markdown("#### 1.1 น้ำหนักบรรทุกใช้งานจริง (Service Load)")
            st.latex(rf"W_{{service}} = {w_dead} + {w_live} + {w_self:.2f} = \mathbf{{{w_service:,.2f}}} \text{{ kg/m}}")
            
            if is_lrfd:
                w_u = 1.2*(w_dead + w_self) + 1.6*w_live
                w_calc_strength = w_u
                st.markdown(f"**Design Load (LRFD):** $W_u = {w_u:,.2f}$ kg/m")
            else:
                w_calc_strength = w_service
                
            w_calc_service = w_service # Deflection ใช้ Service Load เสมอ
            
        else:
            # --- Find Capacity Mode ---
            st.markdown("#### 1.1 คำนวณน้ำหนักบรรทุกปลอดภัย ($W_{safe}$)")
            
            # คำนวณ Limit ที่ระยะ L_m ปัจจุบันเพื่อโชว์ตัวเลข
            w_lim_m = (8 * M_cap) / (L_m**2) if L_m > 0 else 0
            w_lim_v = (2 * V_cap) / L_m if L_m > 0 else 0
            
            delta_limit = (L_m * 100) / defl_denom
            # w (kg/m) based on deflection
            w_lim_d = (delta_limit * 384 * E * Ix) / (5 * ((L_m*100)**4)) * 100
            
            w_safe = min(w_lim_m, w_lim_v, w_lim_d)
            
            st.write(f"- Moment Limit: `{w_lim_m:,.2f}` kg/m")
            st.write(f"- Shear Limit: `{w_lim_v:,.2f}` kg/m")
            st.write(f"- Deflection Limit: `{w_lim_d:,.2f}` kg/m")
            st.success(f"**สรุป $W_{{safe}}$:** `{w_safe:,.2f}` kg/m")
            
            w_calc_strength = w_safe
            w_calc_service = w_safe

    # ==========================================
    # PART B: GRAPH (Fixed Scaling & Missing Lines)
    # ==========================================
    st.header("2️⃣ Capacity Chart (กราฟวิเคราะห์)")
    
    with st.container(border=True):
        try:
            # 1. สร้าง Data Points (ระยะ 0.5m ถึง 12m)
            # ใช้ numpy vectorization เต็มรูปแบบเพื่อความเร็วและแม่นยำ
            x_vals = np.linspace(0.5, 12.0, 200) 
            
            # 2. คำนวณเส้น Limit ต่างๆ (ป้องกันหารด้วยศูนย์)
            # Shear: w = 2V/L
            y_shear = np.divide(2 * V_cap, x_vals)
            
            # Moment: w = 8M/L^2
            y_moment = np.divide(8 * M_cap, x_vals**2)
            
            # Deflection: w = (Delta_all * 384EI) / 5L^4
            # Delta_all = L/denom -> สูตรยุบรวม: w = (384 * E * Ix) / (5 * denom * L^3) * (conversion factors)
            # หน่วย: E(ksc), Ix(cm4), L(m) -> ต้องแปลง L เป็น cm ในสูตร แล้วคูณ 100 กลับเป็น kg/m
            # สูตรสำเร็จรูปหน่วย kg/m: K / L_m^3
            # K = (384 * E * Ix) / (5 * denom * 100^3) * 100
            K_defl = (384 * E * Ix * 100) / (5 * defl_denom * (100**4)) * 100 # check unit carefully
            # หรือใช้สูตรตรงๆ แบบ Loop เพื่อความชัวร์เรื่องหน่วย
            y_defl = []
            for x in x_vals:
                L_cm_i = x * 100
                d_all_i = L_cm_i / defl_denom
                w_kgcm = (d_all_i * 384 * E * Ix) / (5 * L_cm_i**4)
                y_defl.append(w_kgcm * 100) # kg/m
            y_defl = np.array(y_defl)

            # 3. Safe Load Envelope (ค่าต่ำสุด)
            y_safe = np.minimum(y_shear, np.minimum(y_moment, y_defl))
            
            # 4. Plotting
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Plot เส้น Limit (เส้นประ)
            ax.plot(x_vals, y_shear, color='purple', linestyle=':', linewidth=1.5, label='Shear Limit', alpha=0.7)
            ax.plot(x_vals, y_moment, color='orange', linestyle='--', linewidth=1.5, label='Moment Limit', alpha=0.7)
            ax.plot(x_vals, y_defl, color='green', linestyle='-.', linewidth=1.5, label='Deflection Limit', alpha=0.7)
            
            # Plot เส้น Safe Load (เส้นทึบหนา)
            ax.plot(x_vals, y_safe, color='#2c3e50', linewidth=3, label='Safe Load Envelope')
            
            # Fill Zones (ระบายสี)
            ax.fill_between(x_vals, 0, y_safe, where=(y_safe==y_shear), color='purple', alpha=0.1)
            ax.fill_between(x_vals, 0, y_safe, where=(y_safe==y_moment), color='orange', alpha=0.1)
            ax.fill_between(x_vals, 0, y_safe, where=(y_safe==y_defl), color='green', alpha=0.1)
            
            # จุดปัจจุบัน (Current Point)
            ax.scatter([L_m], [w_calc_strength], color='red', s=120, zorder=10, label='Current Design', edgecolors='white', linewidth=2)
            
            # เส้นแนวตั้งและแนวนอนระบุตำแหน่ง
            ax.axvline(x=L_m, color='red', linestyle=':', alpha=0.5)
            ax.axhline(y=w_calc_strength, color='red', linestyle=':', alpha=0.5)

            # 5. การตั้งค่าแกน (สำคัญมาก: แก้ไขเรื่องกราฟหาย)
            ax.set_title(f"Safe Load Capacity vs Span: {section_name}", fontsize=12)
            ax.set_xlabel("Span Length (m)", fontsize=10)
            ax.set_ylabel("Uniform Load (kg/m)", fontsize=10)
            ax.grid(True, linestyle='--', alpha=0.4)
            ax.legend(loc='upper right')
            
            # Auto-Scale Y-Axis อย่างชาญฉลาด
            # หาค่าสูงสุดในช่วง Span ที่สนใจ (เช่น ช่วง user_L +/- 2m หรือช่วงต้นๆ)
            # ถ้าไม่จำกัด Y กราฟช่วงต้น (L=0.5) จะสูงปรี๊ดจนเส้นอื่นแบนติดดิน
            # เราจะดูค่า y_safe ที่ระยะ 2 เมตร เป็น Reference ความสูง
            idx_ref = np.abs(x_vals - 2.0).argmin() 
            ref_height = y_safe[idx_ref]
            
            # ถ้า user_L อยู่ไกล ให้ดูค่าที่ user_L ด้วย
            user_height = w_calc_strength
            
            max_y_plot = max(ref_height * 2.5, user_height * 1.5) # เผื่อที่ด้านบน
            ax.set_ylim(0, max_y_plot)
            ax.set_xlim(0, 12)

            st.pyplot(fig)
            
        except Exception as plot_e:
            st.error(f"⚠️ Graph Error: {plot_e}")

    # ==========================================
    # PART C: DETAILED CALCULATIONS (แบบย่อเพื่อประหยัดที่)
    # ==========================================
    st.header("3️⃣ Detailed Checks (รายการคำนวณ)")
    
    # 3.1 Shear
    v_act = (w_calc_strength * L_m) / 2
    r_v = v_act / V_cap if V_cap else 0
    st.markdown(f"**Shear:** Demand = `{v_act:,.0f}` kg | Capacity = `{V_cap:,.0f}` kg | Ratio = `{r_v:.2f}`")
    
    # 3.2 Moment
    m_act = (w_calc_strength * L_m**2) / 8
    r_m = m_act / M_cap if M_cap else 0
    st.markdown(f"**Moment:** Demand = `{m_act:,.0f}` kg-m | Capacity = `{M_cap:,.0f}` kg-m | Ratio = `{r_m:.2f}`")
    
    # 3.3 Deflection
    w_kgcm = w_calc_service / 100
    d_act = (5 * w_kgcm * ((L_m*100)**4)) / (384 * E * Ix)
    d_all = (L_m * 100) / defl_denom
    r_d = d_act / d_all if d_all else 0
    st.markdown(f"**Deflection:** Actual = `{d_act:.4f}` cm | Allowable = `{d_all:.4f}` cm | Ratio = `{r_d:.2f}`")

    st.divider()
    # Final Status
    final_ratio = max(r_v, r_m, r_d)
    if final_ratio <= 1.0:
        st.success(f"✅ PASS (Ratio {final_ratio:.2%})")
    else:
        st.error(f"❌ FAIL (Ratio {final_ratio:.2%})")
