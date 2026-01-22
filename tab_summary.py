# tab_summary.py
import streamlit as st
import plotly.graph_objects as go

def render(data):
    # ==========================================
    # 1. ROBUST DATA EXTRACTION (ป้องกัน Error)
    # ==========================================
    # แปลงทุกอย่างให้เป็น Float และมี Default Value เสมอ
    try:
        is_check_mode = data.get('is_check_mode', True)
        is_lrfd = data.get('is_lrfd', False)
        
        # Geometry
        L_m = float(data.get('user_span', 6.0))
        L_cm = L_m * 100.0
        
        # Section Properties (ดึงค่า ถ้าไม่มีให้เป็น 0 กัน Error)
        d = float(data.get('d', 0.0))
        tw = float(data.get('tw', 0.0))
        bf = float(data.get('bf', 0.0))
        tf = float(data.get('tf', 0.0))
        Ix = float(data.get('Ix', 1.0)) # ห้ามเป็น 0 เดี๋ยวหารไม่ลงตัว
        Zx = float(data.get('Zx', 0.0))
        Sx = float(data.get('Sx', 0.0))
        Fy = float(data.get('Fy', 2500.0))
        E = float(data.get('E', 2040000.0))
        
        # Capacities (รับค่าที่คำนวณมาแล้วจาก app.py)
        M_cap = float(data.get('M_cap', 0.0))
        V_cap = float(data.get('V_cap', 0.0))
        defl_denom = float(data.get('defl_denom', 360.0))
        
        # Actual Results
        d_act = float(data.get('d_act', 0.0))
        d_allow = float(data.get('d_allow', 1.0))
        
    except Exception as e:
        st.error(f"Data Error: {e}")
        return

    # Header
    st.title("📄 รายการคำนวณโครงสร้าง (Structural Calculation)")
    st.write(f"**Section:** {data.get('section_name', 'N/A')} | **Span:** {L_m:.2f} m.")

    # ==========================================
    # PART 1: LOAD ANALYSIS (ที่มาของ W)
    # ==========================================
    st.header("1️⃣ Load Analysis (วิเคราะห์น้ำหนักบรรทุก)")
    
    with st.container(border=True):
        if is_check_mode:
            # --- CASE A: CHECK DESIGN (บวกเลขตรงๆ) ---
            st.markdown("#### 1.1 ที่มาของน้ำหนักบรรทุกรวม ($W_{total}$)")
            w_dead = float(data.get('w_dead_input', 0.0))
            w_live = float(data.get('w_live_input', 0.0))
            w_self = float(data.get('w_self_weight', 0.0))
            w_calc = w_dead + w_live + w_self
            
            st.latex(r"W_{total} = w_{dead} + w_{live} + w_{self\_weight}")
            st.latex(rf"W_{{total}} = {w_dead:,.2f} + {w_live:,.2f} + {w_self:,.2f} = \mathbf{{{w_calc:,.2f}}} \text{{ kg/m}}")
            
        else:
            # --- CASE B: FIND CAPACITY (คำนวณย้อนกลับ) ---
            # นี่คือสิ่งที่คุณต้องการ: กางสมการหา W_safe
            st.markdown("#### 1.1 การคำนวณน้ำหนักบรรทุกสูงสุด ($W_{safe}$)")
            st.markdown("ค่า $W_{safe}$ มาจากการเปรียบเทียบขีดจำกัดของ **โมเมนต์**, **แรงเฉือน** และ **การแอ่นตัว** โดยเลือกค่าที่น้อยที่สุด (Governing Case):")
            
            st.latex(r"W_{safe} = \min(W_{Moment}, W_{Shear}, W_{Deflection})")
            
            # 1. Limit from Moment
            # M = wL^2/8 -> w = 8M/L^2
            w_limit_m = (8 * M_cap) / (L_m**2)
            st.markdown(f"**ก) ขีดจำกัดจากโมเมนต์ ($W_M$):**")
            st.latex(rf"W_M = \frac{{8 \cdot M_{{cap}}}}{{L^2}} = \frac{{8 \cdot {M_cap:,.2f}}}{{{L_m}^2}} = {w_limit_m:,.2f} \text{{ kg/m}}")
            
            # 2. Limit from Shear
            # V = wL/2 -> w = 2V/L
            w_limit_v = (2 * V_cap) / L_m
            st.markdown(f"**ข) ขีดจำกัดจากแรงเฉือน ($W_V$):**")
            st.latex(rf"W_V = \frac{{2 \cdot V_{{cap}}}}{{L}} = \frac{{2 \cdot {V_cap:,.2f}}}{{{L_m}}} = {w_limit_v:,.2f} \text{{ kg/m}}")
            
            # 3. Limit from Deflection (Reverse equation)
            # Delta = 5wL^4 / 384EI -> w = (Delta_all * 384EI) / (5L^4)
            # ต้องระวังหน่วย! L ในสูตร Defl คือ cm, w ออกมาเป็น kg/cm แล้วค่อยแปลงเป็น kg/m
            delta_all = L_cm / defl_denom
            # w (kg/cm)
            w_limit_d_kgcm = (delta_all * 384 * E * Ix) / (5 * (L_cm**4))
            w_limit_d = w_limit_d_kgcm * 100 # แปลงเป็น kg/m
            
            st.markdown(f"**ค) ขีดจำกัดจากการแอ่นตัว ($W_\Delta$):**")
            st.latex(r"W_\Delta = \frac{\Delta_{all} \cdot 384 \cdot E \cdot I_x}{5 \cdot L^4}")
            st.latex(rf"W_\Delta = \frac{{{delta_all:.2f} \cdot 384 \cdot {E:,.0f} \cdot {Ix:,.0f}}}{{5 \cdot {L_cm:,.0f}^4}} \times 100 = {w_limit_d:,.2f} \text{{ kg/m}}")
            
            # สรุป
            w_final = min(w_limit_m, w_limit_v, w_limit_d)
            w_calc = w_final # ใช้ค่านี้คำนวณต่อใน section ล่าง
            
            st.markdown("---")
            st.markdown("**สรุปน้ำหนักบรรทุกปลอดภัย (Governing Load):**")
            st.latex(rf"W_{{safe}} = \min({w_limit_m:,.0f}, {w_limit_v:,.0f}, {w_limit_d:,.0f}) = \mathbf{{{w_final:,.2f}}} \text{{ kg/m}}")


    # ==========================================
    # PART 2: SHEAR CHECK (กางสูตรละเอียด)
    # ==========================================
    st.header("2️⃣ Shear Capacity Check (ตรวจสอบแรงเฉือน)")
    with st.container(border=True):
        st.markdown("**2.1 สูตรกำลังรับแรงเฉือน ($V_n$):**")
        st.latex(r"V_n = 0.6 \cdot F_y \cdot A_w")
        
        st.markdown("**2.2 แทนค่าตัวแปร:**")
        # แสดง Aw
        Aw = d * tw
        st.latex(rf"A_w (\text{{Web Area}}) = d \times t_w = {d} \times {tw} = {Aw:.2f} \text{{ cm}}^2")
        
        # แสดง Vn
        Vn = 0.6 * Fy * Aw
        st.latex(rf"V_n = 0.6 \cdot {Fy:,.0f} \cdot {Aw:.2f} = {Vn:,.2f} \text{{ kg}}")
        
        # Apply Factor
        st.markdown("**2.3 กำลังที่ยอมให้ (Allowable/Design Strength):**")
        if is_lrfd:
            st.latex(rf"\phi V_n = 1.0 \cdot {Vn:,.2f} = \mathbf{{{V_cap:,.2f}}} \text{{ kg}}")
        else:
            st.latex(rf"\frac{{V_n}}{{\Omega}} = \frac{{{Vn:,.2f}}}{{1.67}} = \mathbf{{{V_cap:,.2f}}} \text{{ kg}}")
            
        # Check against Demand
        st.markdown("**2.4 ตรวจสอบอัตราส่วน (Ratio):**")
        v_act = (w_calc * L_m) / 2
        st.latex(rf"V_{{act}} = \frac{{{w_calc:,.2f} \cdot {L_m}}}{{2}} = {v_act:,.2f} \text{{ kg}}")
        
        # ตรวจสอบตัวหารเป็น 0 หรือไม่
        ratio_v = v_act / V_cap if V_cap > 0 else 0
        st.latex(rf"Ratio = \frac{{{v_act:,.2f}}}{{{V_cap:,.2f}}} = \mathbf{{{ratio_v:.4f}}}")


    # ==========================================
    # PART 3: DEFLECTION CHECK (กางสูตรละเอียด)
    # ==========================================
    st.header("3️⃣ Deflection Check (ตรวจสอบการแอ่นตัว)")
    with st.container(border=True):
        st.markdown("**3.1 สูตรการแอ่นตัว ($\Delta_{act}$):**")
        st.latex(r"\Delta_{act} = \frac{5 \cdot w \cdot L^4}{384 \cdot E \cdot I_x}")
        
        st.markdown("**3.2 แทนค่าตัวเลข (หน่วย kg, cm):**")
        # แปลงหน่วยเพื่อแสดงในสมการ
        w_kgcm = w_calc / 100
        
        # ใช้ LaTeX แบบ String Format เพื่อป้องกัน Error
        sub_str = rf"\Delta_{{act}} = \frac{{5 \cdot ({w_kgcm:.4f}) \cdot ({L_cm:,.0f})^4}}{{384 \cdot ({E:,.0f}) \cdot ({Ix:,.2f})}}"
        st.latex(sub_str)
        
        # คำนวณจริงเพื่อโชว์ผลลัพธ์
        try:
            val_d_act = (5 * w_kgcm * (L_cm**4)) / (384 * E * Ix)
        except ZeroDivisionError:
            val_d_act = 0
            
        st.latex(rf"\Delta_{{act}} = \mathbf{{{val_d_act:.4f}}} \text{{ cm}}")
        
        st.markdown("**3.3 เปรียบเทียบกับค่าที่ยอมให้:**")
        val_d_all = L_cm / defl_denom
        st.latex(rf"\Delta_{{all}} = L/{defl_denom:.0f} = {val_d_all:.4f} \text{{ cm}}")
        
        ratio_d = val_d_act / val_d_all if val_d_all > 0 else 0
        st.latex(rf"Ratio = \frac{{{val_d_act:.4f}}}{{{val_d_all:.4f}}} = \mathbf{{{ratio_d:.4f}}}")

    # Final Summary Logic
    st.divider()
    gov_r = max(ratio_v, ratio_d) # คำนวณคร่าวๆ หรือดึงจาก data ถ้ามี
    if data.get('ratio_m', 0) > gov_r: gov_r = data['ratio_m']
    
    status_text = "PASS" if gov_r <= 1.0 else "FAIL"
    color = "green" if gov_r <= 1.0 else "red"
    st.markdown(f":{color}[**STATUS: {status_text} (Max Ratio = {gov_r:.2%})**]")
