# tab_summary.py
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

def render(data):
    # ==========================================
    # 1. ROBUST DATA EXTRACTION & SETUP
    # ==========================================
    try:
        # Check Mode or Capacity Mode
        is_check_mode = data.get('is_check_mode', True)
        is_lrfd = data.get('is_lrfd', False)
        method_str = "LRFD" if is_lrfd else "ASD"

        # Geometry & Section
        L_m = float(data.get('user_span', 6.0))
        L_cm = L_m * 100.0
        section_name = data.get('section_name', 'Custom Section')
        
        # Section Properties (Default to 0.0 to prevent crash, check for valid Ix)
        d = float(data.get('d', 0.0))
        tw = float(data.get('tw', 0.0))
        bf = float(data.get('bf', 0.0))
        tf = float(data.get('tf', 0.0))
        Ix = float(data.get('Ix', 0.0))
        if Ix == 0: Ix = 1.0 # Prevent Division by Zero
        
        Zx = float(data.get('Zx', 0.0))
        Sx = float(data.get('Sx', 0.0))
        Fy = float(data.get('Fy', 2500.0))
        E = float(data.get('E', 2040000.0))
        
        # Derived Capacities
        M_cap = float(data.get('M_cap', 0.0))
        V_cap = float(data.get('V_cap', 0.0))
        defl_denom = float(data.get('defl_denom', 360.0))

    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return

    st.title(f"📄 รายการคำนวณและวิเคราะห์ (Structural Analysis: {section_name})")
    st.markdown(f"**Method:** {method_str} | **Span:** {L_m:.2f} m.")

    # ==========================================
    # PART A: LOAD ANALYSIS (ที่มาของ W)
    # ==========================================
    st.header("1️⃣ Load Analysis (วิเคราะห์น้ำหนักบรรทุก)")
    
    with st.container(border=True):
        if is_check_mode:
            # --- 1.1 Check Design Mode (Summation) ---
            st.markdown("#### 1.1 ที่มาของน้ำหนักบรรทุกรวม ($W_{total}$)")
            
            w_dead = float(data.get('w_dead_input', 0.0))
            w_live = float(data.get('w_live_input', 0.0))
            w_self = float(data.get('w_self_weight', 0.0))
            
            st.write("องค์ประกอบของน้ำหนัก (Load Components):")
            c1, c2 = st.columns(2)
            c1.write(f"- Dead Load ($w_{{DL}}$): `{w_dead:,.2f}` kg/m")
            c1.write(f"- Live Load ($w_{{LL}}$): `{w_live:,.2f}` kg/m")
            c2.write(f"- Self Weight ($w_{{SW}}$): `{w_self:,.2f}` kg/m")
            
            w_sum = w_dead + w_live + w_self
            
            st.markdown("---")
            st.latex(r"W_{service} = w_{DL} + w_{LL} + w_{SW}")
            st.latex(rf"W_{{service}} = {w_dead:,.2f} + {w_live:,.2f} + {w_self:,.2f} = \mathbf{{{w_sum:,.2f}}} \text{{ kg/m}}")
            
            # กำหนดค่าที่จะใช้คำนวณต่อ
            if is_lrfd:
                w_u = 1.2*(w_dead + w_self) + 1.6*w_live
                st.latex(r"W_{u} (Factor) = 1.2(DL+SW) + 1.6(LL)")
                st.latex(rf"W_{{u}} = \mathbf{{{w_u:,.2f}}} \text{{ kg/m}}")
                w_calc_strength = w_u
                w_calc_service = w_sum
            else:
                w_calc_strength = w_sum
                w_calc_service = w_sum
                
        else:
            # --- 1.2 Find Capacity Mode (Back Calculation) ---
            st.markdown("#### 1.1 การคำนวณน้ำหนักบรรทุกสูงสุด ($W_{safe}$)")
            st.info("💡 โหมด Find Capacity: คำนวณย้อนกลับจาก Moment, Shear และ Deflection")
            
            # คำนวณ Limit ของแต่ละตัว
            # 1. Moment: w = 8M/L^2
            w_lim_m = (8 * M_cap) / (L_m**2)
            
            # 2. Shear: w = 2V/L
            w_lim_v = (2 * V_cap) / L_m
            
            # 3. Deflection: w (kg/m) = (Delta_all * 384EI) / (5 * L^4) * 100
            # Delta_all = L_cm / denom
            delta_limit = L_cm / defl_denom
            w_lim_d_kgcm = (delta_limit * 384 * E * Ix) / (5 * (L_cm**4))
            w_lim_d = w_lim_d_kgcm * 100
            
            st.latex(r"W_{safe} = \min(W_{Moment}, W_{Shear}, W_{Deflection})")
            st.write(f"- จาก Moment Limit: `{w_lim_m:,.2f}` kg/m")
            st.write(f"- จาก Shear Limit: `{w_lim_v:,.2f}` kg/m")
            st.write(f"- จาก Deflection Limit: `{w_lim_d:,.2f}` kg/m")
            
            w_final = min(w_lim_m, w_lim_v, w_lim_d)
            st.markdown(f"**สรุป $W_{{safe}}$ ที่ใช้:** `{w_final:,.2f}` kg/m")
            
            w_calc_strength = w_final
            w_calc_service = w_final

    # ==========================================
    # PART B: GOVERNING CHART (กราฟวิเคราะห์)
    # ==========================================
    st.header("2️⃣ Governing Criteria Chart (กราฟวิเคราะห์จุดวิกฤต)")
    
    with st.expander("📊 คลิกเพื่อดูกราฟวิเคราะห์พฤติกรรมคาน (Load vs Span)", expanded=True):
        # 1. Prepare Data for Plotting
        try:
            plot_L = np.linspace(0.5, 12.0, 100) # Plot from 0.5m to 12m
            
            # Shear Curve: w = 2V/L
            y_shear = (2 * V_cap) / plot_L
            
            # Moment Curve: w = 8M/L^2
            y_moment = (8 * M_cap) / (plot_L**2)
            
            # Deflection Curve: w = (L/denom * 384EI) / (5 L^4)
            # w (kg/m) = [ (L*100/denom) * 384 * E * Ix ] / [ 5 * (L*100)^4 ] * 100
            # Simplify constant K = (384 * E * Ix * 100) / (5 * denom * 100^3) -> L ตัด L^4 เหลือ L^3
            # แต่เพื่อความชัวร์ ใช้สูตรเต็ม
            y_defl = []
            for l_val in plot_L:
                l_cm_val = l_val * 100
                d_all = l_cm_val / defl_denom
                w_val_kgcm = (d_all * 384 * E * Ix) / (5 * l_cm_val**4)
                y_defl.append(w_val_kgcm * 100)
            y_defl = np.array(y_defl)
            
            # Safe Load Envelope
            y_safe = np.minimum(y_shear, np.minimum(y_moment, y_defl))
            
            # 2. Plotting with Matplotlib
            fig, ax = plt.subplots(figsize=(10, 5))
            
            # Limits
            ax.plot(plot_L, y_shear, ':', color='purple', label='Shear Limit', alpha=0.5)
            ax.plot(plot_L, y_moment, '--', color='orange', label='Moment Limit', alpha=0.5)
            ax.plot(plot_L, y_defl, '-.', color='green', label='Deflection Limit', alpha=0.5)
            
            # Safe Envelope
            ax.plot(plot_L, y_safe, '-', color='black', linewidth=2.5, label='Safe Load Envelope')
            
            # Fill Zones
            ax.fill_between(plot_L, 0, y_safe, where=(y_safe==y_shear), color='purple', alpha=0.1)
            ax.fill_between(plot_L, 0, y_safe, where=(y_safe==y_moment), color='orange', alpha=0.1)
            ax.fill_between(plot_L, 0, y_safe, where=(y_safe==y_defl), color='green', alpha=0.1)
            
            # User Point
            ax.scatter([L_m], [w_calc_strength], color='red', s=100, zorder=5, label='Current Design')
            ax.text(L_m, w_calc_strength*1.1, f"  Span {L_m}m", color='red', fontweight='bold')
            
            ax.set_xlabel("Span Length (m)")
            ax.set_ylabel("Max Uniform Load (kg/m)")
            ax.set_title(f"Capacity Curve for {section_name}")
            ax.legend()
            ax.grid(True, linestyle='--', alpha=0.4)
            ax.set_ylim(0, w_calc_strength * 3) # Zoom ให้เห็นจุดปัจจุบันชัดๆ
            
            st.pyplot(fig)
            st.caption("พื้นที่สีม่วง = Shear Control | พื้นที่สีส้ม = Moment Control | พื้นที่สีเขียว = Deflection Control")
            
        except Exception as plot_err:
            st.error(f"Cannot render chart: {plot_err}")

    # ==========================================
    # PART C: DETAILED CHECKS (SHEAR, MOMENT, DEFL)
    # ==========================================
    st.header("3️⃣ Detailed Calculation (รายการคำนวณละเอียด)")
    
    # --- 3.1 SHEAR ---
    with st.container(border=True):
        st.subheader("3.1 Shear Check (แรงเฉือน)")
        col_s1, col_s2 = st.columns([1, 1])
        
        # Demand
        v_act = (w_calc_strength * L_m) / 2
        with col_s1:
            st.markdown("**Shear Demand ($V_{req}$)**")
            st.latex(r"V_{req} = \frac{W \cdot L}{2}")
            st.latex(rf"V_{{req}} = \frac{{{w_calc_strength:,.2f} \cdot {L_m}}}{{2}} = \mathbf{{{v_act:,.2f}}} \text{{ kg}}")
        
        # Capacity
        with col_s2:
            st.markdown("**Shear Capacity ($V_{cap}$)**")
            # Show Aw calculation
            Aw = d * tw
            st.latex(rf"A_w = d \cdot t_w = {d} \cdot {tw} = {Aw:.2f} \text{{ cm}}^2")
            st.latex(rf"V_n = 0.6 F_y A_w = 0.6({Fy:.0f})({Aw:.2f}) = {0.6*Fy*Aw:,.0f} \text{{ kg}}")
            st.markdown(f"**Design Capacity ({method_str}):** `{V_cap:,.2f}` kg")
            
        # Ratio
        r_v = v_act / V_cap if V_cap > 0 else 999
        st.metric("Shear Ratio", f"{r_v:.4f}", "Pass" if r_v <= 1 else "Fail", delta_color="inverse")

    # --- 3.2 MOMENT ---
    with st.container(border=True):
        st.subheader("3.2 Moment Check (แรงดัด)")
        col_m1, col_m2 = st.columns([1, 1])
        
        # Demand
        m_act = (w_calc_strength * L_m**2) / 8
        with col_m1:
            st.markdown("**Moment Demand ($M_{req}$)**")
            st.latex(r"M_{req} = \frac{W \cdot L^2}{8}")
            st.latex(rf"M_{{req}} = \frac{{{w_calc_strength:,.2f} \cdot {L_m}^2}}{{8}} = \mathbf{{{m_act:,.2f}}} \text{{ kg-m}}")
        
        # Capacity
        with col_m2:
            st.markdown("**Moment Capacity ($M_{cap}$)**")
            prop = Zx if is_lrfd else Sx
            prop_name = "Z_x" if is_lrfd else "S_x"
            st.latex(rf"M_n = F_y \cdot {prop_name} = {Fy:.0f} \cdot {prop:.2f}")
            st.markdown(f"**Design Capacity ({method_str}):** `{M_cap:,.2f}` kg-m")
            
        # Ratio
        r_m = m_act / M_cap if M_cap > 0 else 999
        st.metric("Moment Ratio", f"{r_m:.4f}", "Pass" if r_m <= 1 else "Fail", delta_color="inverse")

    # --- 3.3 DEFLECTION (Detailed Trace) ---
    with st.container(border=True):
        st.subheader("3.3 Deflection Check (การแอ่นตัว)")
        
        # Unit Conversion Display
        st.markdown("**1) แปลงหน่วยเพื่อแทนค่า (Unit Conversion):**")
        w_kgcm = w_calc_service / 100
        st.latex(rf"w = {w_calc_service:,.2f}/100 = {w_kgcm:.4f} \text{{ kg/cm}}")
        st.latex(rf"L = {L_m} \times 100 = {L_cm:.0f} \text{{ cm}}")
        
        # Actual Deflection
        st.markdown("**2) คำนวณการแอ่นตัวจริง ($\Delta_{act}$):**")
        st.latex(r"\Delta_{act} = \frac{5 \cdot w \cdot L^4}{384 \cdot E \cdot I_x}")
        
        # Show substitution string
        sub_str = rf"\Delta_{{act}} = \frac{{5 \cdot ({w_kgcm:.4f}) \cdot ({L_cm:.0f})^4}}{{384 \cdot ({E:.0f}) \cdot ({Ix:.2f})}}"
        st.latex(sub_str)
        
        val_d_act = (5 * w_kgcm * (L_cm**4)) / (384 * E * Ix)
        st.latex(rf"\Delta_{{act}} = \mathbf{{{val_d_act:.4f}}} \text{{ cm}}")
        
        # Allowable
        st.markdown("**3) ตรวจสอบกับค่าที่ยอมให้ ($\Delta_{all}$):**")
        val_d_all = L_cm / defl_denom
        st.latex(rf"\Delta_{{all}} = L/{defl_denom:.0f} = {L_cm:.0f}/{defl_denom:.0f} = {val_d_all:.4f} \text{{ cm}}")
        
        # Ratio
        r_d = val_d_act / val_d_all if val_d_all > 0 else 999
        st.metric("Deflection Ratio", f"{r_d:.4f}", "Pass" if r_d <= 1 else "Fail", delta_color="inverse")

    # ==========================================
    # FINAL CONCLUSION
    # ==========================================
    st.divider()
    max_r = max(r_v, r_m, r_d)
    
    # Determine Governor
    if max_r == r_v: gov = "Shear (แรงเฉือน)"
    elif max_r == r_m: gov = "Moment (แรงดัด)"
    else: gov = "Deflection (การแอ่นตัว)"
    
    if max_r <= 1.0:
        st.success(f"✅ **PASS (ผ่านการตรวจสอบ)** | Controlled by: **{gov}** (Ratio: {max_r:.2%})")
    else:
        st.error(f"❌ **FAIL (ไม่ผ่านการตรวจสอบ)** | Controlled by: **{gov}** (Ratio: {max_r:.2%})")
