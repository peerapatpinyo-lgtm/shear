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
            
            st.markdown(f"**Service Load ($W_{{service}}$):** `{w_service:,.2f}` kg/m")
            
            if is_lrfd:
                w_u = 1.2*(w_dead + w_self) + 1.6*w_live
                w_calc_strength = w_u
            else:
                w_calc_strength = w_service
            
            w_calc_service = w_service # ใช้สำหรับคำนวณ Deflection Graph
            
        else:
            # --- Find Capacity Mode ---
            st.info("💡 โหมด Find Capacity จะแสดงกราฟตาม Limit ของหน้าตัด")
            # คำนวณ Limit ที่ระยะ L_m ปัจจุบันเพื่อใช้เป็น Reference
            delta_limit = (L_m * 100) / defl_denom
            w_lim_d = (delta_limit * 384 * E * Ix) / (5 * ((L_m*100)**4)) * 100
            w_calc_service = w_lim_d # สมมติโหลดเท่ากับ Limit เพื่อพล็อตกราฟ
            w_calc_strength = w_lim_d

    # ==========================================
    # PART B: GRAPHICS (2 TABS)
    # ==========================================
    st.header("2️⃣ Behavioral Analysis Charts (กราฟพฤติกรรม)")
    
    tab1, tab2 = st.tabs(["📊 Capacity Envelope (ภาพรวม)", "📉 Deflection Trend (การแอ่นตัว)"])

    # --- TAB 1: SAFE LOAD VS SPAN (กราฟเดิม) ---
    with tab1:
        try:
            x_vals = np.linspace(0.5, 12.0, 200)
            
            # 1. Limit Curves
            y_shear = np.divide(2 * V_cap, x_vals)
            y_moment = np.divide(8 * M_cap, x_vals**2)
            
            # Deflection Limit Load
            y_defl_limit_load = []
            for x in x_vals:
                L_cm_i = x * 100
                d_all_i = L_cm_i / defl_denom
                w_kgcm = (d_all_i * 384 * E * Ix) / (5 * L_cm_i**4)
                y_defl_limit_load.append(w_kgcm * 100)
            y_defl_limit_load = np.array(y_defl_limit_load)

            # Safe Envelope
            y_safe = np.minimum(y_shear, np.minimum(y_moment, y_defl_limit_load))
            
            # Plot
            fig1, ax1 = plt.subplots(figsize=(10, 5))
            ax1.plot(x_vals, y_shear, ':', color='purple', alpha=0.5, label='Shear Limit')
            ax1.plot(x_vals, y_moment, '--', color='orange', alpha=0.5, label='Moment Limit')
            ax1.plot(x_vals, y_defl_limit_load, '-.', color='green', alpha=0.5, label='Deflection Limit')
            ax1.plot(x_vals, y_safe, color='#2c3e50', linewidth=2.5, label='Safe Load')
            
            # Fill Zones
            ax1.fill_between(x_vals, 0, y_safe, where=(y_safe==y_defl_limit_load), color='green', alpha=0.1, label='Deflection Controlled')
            ax1.fill_between(x_vals, 0, y_safe, where=(y_safe==y_moment), color='orange', alpha=0.1, label='Moment Controlled')
            
            # User Point
            ax1.scatter([L_m], [w_calc_strength], color='red', s=100, zorder=5)
            
            ax1.set_title("Safe Load Capacity vs. Span Length")
            ax1.set_xlabel("Span (m)")
            ax1.set_ylabel("Max Load (kg/m)")
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            ax1.set_ylim(0, max(w_calc_strength*2, 500))
            
            st.pyplot(fig1)
            st.caption("กราฟนี้แสดงน้ำหนักปลอดภัยที่รับได้สูงสุด ณ ระยะต่างๆ")
            
        except Exception as e:
            st.error(f"Error plotting chart 1: {e}")

    # --- TAB 2: DEFLECTION VS SPAN (กราฟใหม่ที่คุณขอ) ---
    with tab2:
        st.markdown("#### ความสัมพันธ์ระหว่าง ระยะคาน (Span) กับ การแอ่นตัว (Deflection)")
        st.caption(f"กำหนดให้รับน้ำหนักคงที่ $W = {w_calc_service:,.2f}$ kg/m (น้ำหนักปัจจุบัน)")
        
        try:
            # ใช้ Range เดิม 0.5 - 12m
            x_vals = np.linspace(0.5, 12.0, 200)
            
            # 1. Actual Deflection Curve (Fixed Load)
            # Formula: Delta = (5 * w * L^4) / (384 * E * Ix)
            # w ต้องคงที่ (User Load) ส่วน L เปลี่ยนไปเรื่อยๆ
            w_kgcm_fixed = w_calc_service / 100
            
            # คำนวณ Delta Actual (cm)
            y_delta_act = (5 * w_kgcm_fixed * ((x_vals*100)**4)) / (384 * E * Ix)
            
            # 2. Allowable Deflection Line (Linear)
            # Formula: Delta_all = L / Denom
            y_delta_all = (x_vals * 100) / defl_denom
            
            # 3. Plotting
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            
            # เส้นพิกัด (Allowable) - สีเขียว
            ax2.plot(x_vals, y_delta_all, '--', color='green', linewidth=2, label=f'Allowable Limit (L/{defl_denom:.0f})')
            
            # เส้นแอ่นตัวจริง (Actual) - สีน้ำเงิน
            ax2.plot(x_vals, y_delta_act, '-', color='blue', linewidth=2, label=f'Actual Deflection (Load {w_calc_service:.0f} kg/m)')
            
            # พื้นที่ Fail (ระบายสีแดงเมื่อ Actual > Allowable)
            ax2.fill_between(x_vals, y_delta_all, y_delta_act, where=(y_delta_act > y_delta_all), 
                             color='red', alpha=0.2, label='FAIL Zone')
            
            # จุดปัจจุบัน (Current Point)
            current_delta = (5 * w_kgcm_fixed * ((L_m*100)**4)) / (384 * E * Ix)
            ax2.scatter([L_m], [current_delta], color='red', s=120, zorder=10, label=f'Current Span ({L_m}m)')
            
            # Annotation บอกค่า
            ax2.annotate(f"{current_delta:.2f} cm", (L_m, current_delta), xytext=(10, -20), 
                         textcoords='offset points', color='red', fontweight='bold')

            # Setting
            ax2.set_title(f"Deflection vs Span Length (Load: {w_calc_service:.0f} kg/m)")
            ax2.set_xlabel("Span Length (m)")
            ax2.set_ylabel("Deflection (cm)")
            
            # Limit แกน Y ไม่ให้กราฟพุ่งทะลุจอ (เพราะ L^4 มันชันมาก)
            # ให้สูงกว่า Limit Line ที่ปลายกราฟสัก 1.5 เท่า หรือ สูงกว่าจุดปัจจุบัน 2 เท่า
            max_y_limit = max(y_delta_all[-1] * 1.5, current_delta * 2)
            ax2.set_ylim(0, max_y_limit)
            ax2.set_xlim(0, 12)
            
            ax2.legend()
            ax2.grid(True, which='both', linestyle='--', alpha=0.4)
            
            st.pyplot(fig2)
            
            # คำอธิบายฟิสิกส์
            st.info("""
            **วิเคราะห์ผล (Insight):**
            * เส้นสีเขียว (Limit) เพิ่มขึ้นเป็น **เส้นตรง (Linear)** ตามความยาว
            * เส้นสีน้ำเงิน (Actual) พุ่งขึ้นแบบ **ยกกำลัง 4 ($L^4$)**
            * จุดตัดคือระยะไกลที่สุดที่คานนี้รับน้ำหนักนี้ได้โดยไม่แอ่นเกินพิกัด
            """)
            
        except Exception as e:
            st.error(f"Error plotting chart 2: {e}")

    # ==========================================
    # PART C: DETAILED CHECKS (สรุปตัวเลข)
    # ==========================================
    st.divider()
    # (ส่วนแสดงตัวเลข Shear/Moment/Deflection คงเดิมตามโค้ดก่อนหน้า)
    # ผมตัดมาเฉพาะส่วนกราฟเพื่อความกระชับ คุณสามารถแปะโค้ดนี้ทับส่วน render เดิมได้เลย
    # หรือถ้าจะเอาตัวเลขด้วย ให้ copy ส่วน PART C จากโค้ดก่อนหน้ามาต่อท้ายบรรทัดนี้ครับ
