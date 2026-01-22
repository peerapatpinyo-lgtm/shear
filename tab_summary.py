# tab_summary.py
import streamlit as st
import plotly.graph_objects as go

def render(data):
    # --- 1. SETUP & DATA EXTRACTION ---
    is_lrfd = data.get('is_lrfd', False)
    method_str = "LRFD (Load & Resistance Factor Design)" if is_lrfd else "ASD (Allowable Strength Design)"
    
    # ดึงค่า Input
    L_m = data['user_span']
    L_cm = L_m * 100
    Fy = data.get('Fy', 2500) # ksc
    E = data.get('E', 2040000) # ksc
    
    # ดึงค่า Section Properties
    section_name = data.get('section_name', 'Custom Section')
    d = data.get('d', 0)      # Depth (cm)
    tw = data.get('tw', 0)    # Web Thickness (cm)
    bf = data.get('bf', 0)    # Flange Width (cm)
    tf = data.get('tf', 0)    # Flange Thickness (cm)
    Ix = data.get('Ix', 0)    # Inertia x (cm4)
    Zx = data.get('Zx', 0)    # Plastic Modulus (cm3)
    Sx = data.get('Sx', 0)    # Elastic Modulus (cm3)
    
    # --- HEADER ---
    st.title(f"📄 รายการคำนวณโครงสร้าง (Structural Calculation Sheet)")
    st.markdown(f"**โครงการ/ชิ้นส่วน:** {section_name} | **Span:** {L_m:.2f} m. | **Method:** {method_str}")
    
    st.divider()

    # =================================================================================
    # PART 1: LOAD ANALYSIS (วิเคราะห์น้ำหนักบรรทุก) - *ตามที่คุณย้ำ*
    # =================================================================================
    st.header("1️⃣ Load Analysis (วิเคราะห์น้ำหนักบรรทุก)")
    
    with st.container(border=True):
        st.markdown("#### 1.1 ที่มาของน้ำหนักบรรทุกรวม ($W_{total}$)")
        
        # เช็คว่ามาจากโหมดไหน
        if data.get('is_check_mode', True):
            # โหมด Check Design: ต้องบวก Dead + Live + Self
            w_dead = data.get('w_dead_input', 0)
            w_live = data.get('w_live_input', 0)
            
            # ถ้า data ไม่มี key นี้ ให้ลองคำนวณย้อนกลับหรือใช้ค่า default
            # (กัน Error กรณี app.py ไม่ได้ส่งมา)
            w_self = data.get('w_self_weight', 0) 
            
            st.write("องค์ประกอบของน้ำหนัก (Load Components):")
            col_l1, col_l2 = st.columns(2)
            with col_l1:
                st.markdown(f"- **Superimposed Dead Load ($w_{{DL}}$)**: `{w_dead:,.2f}` kg/m")
                st.markdown(f"- **Live Load ($w_{{LL}}$)**: `{w_live:,.2f}` kg/m")
            with col_l2:
                st.markdown(f"- **Self Weight ($w_{{SW}}$)**: `{w_self:,.2f}` kg/m (น้ำหนักเหล็ก)")
            
            # กางสมการบวกเลข
            st.markdown("---")
            st.markdown("**สมการรวมน้ำหนัก (Service Load Combination):**")
            st.latex(r"W_{service} = w_{DL} + w_{LL} + w_{SW}")
            st.latex(rf"W_{{service}} = {w_dead:,.2f} + {w_live:,.2f} + {w_self:,.2f} = \mathbf{{{w_dead + w_live + w_self:,.2f}}} \text{{ kg/m}}")
            
            # ถ้าเป็น LRFD ต้องโชว์ Factored Load ด้วย
            if is_lrfd:
                st.markdown("**กรณี LRFD (Factored Load Combination):**")
                st.latex(r"W_{u} = 1.2(w_{DL} + w_{SW}) + 1.6(w_{LL})")
                w_u = 1.2*(w_dead + w_self) + 1.6*w_live
                st.latex(rf"W_{{u}} = 1.2({w_dead+w_self:,.2f}) + 1.6({w_live:,.2f}) = \mathbf{{{w_u:,.2f}}} \text{{ kg/m}}")
                w_calc = w_u # ใช้ค่านี้คำนวณ Strength
                w_serv = w_dead + w_live + w_self # ใช้ค่านี้คำนวณ Deflection
            else:
                w_calc = w_dead + w_live + w_self
                w_serv = w_calc
                
        else:
            # โหมด Find Capacity
            w_calc = data.get('w_safe', 0)
            w_serv = w_calc
            st.info("💡 หมายเหตุ: อยู่ในโหมด **Find Capacity** (หาน้ำหนักบรรทุกสูงสุดที่ยอมให้)")
            st.latex(rf"W_{{safe}} = \mathbf{{{w_calc:,.2f}}} \text{{ kg/m}}")

    # =================================================================================
    # PART 2: SHEAR CHECK (แรงเฉือน) - *ละเอียด*
    # =================================================================================
    st.header("2️⃣ Shear Strength Check (ตรวจสอบแรงเฉือน)")
    
    with st.container(border=True):
        st.markdown("#### 2.1 Shear Demand ($V_{req}$)")
        st.latex(r"V_{req} = \frac{W \cdot L}{2}")
        st.latex(rf"V_{{req}} = \frac{{{w_calc:,.2f} \cdot {L_m:,.2f}}}{{2}} = \mathbf{{{data['v_act']:,.2f}}} \text{{ kg}}")
        
        st.markdown("#### 2.2 Shear Capacity ($V_n$)")
        st.markdown("คำนวณกำลังรับแรงเฉือนจากพื้นที่หน้าตัดเอวคาน ($A_w$):")
        
        # 1. หาพื้นที่ Web
        st.latex(r"A_w = d \times t_w")
        Aw = d * tw
        st.latex(rf"A_w = {d:.1f} \text{{ cm}} \times {tw:.2f} \text{{ cm}} = {Aw:.2f} \text{{ cm}}^2")
        
        # 2. หากำลัง Vn (Nominal Strength)
        st.markdown("กำลังรับแรงเฉือนระบุ ($V_n$) ตามมาตรฐาน AISC ($0.6F_y$):")
        st.latex(r"V_n = 0.6 \cdot F_y \cdot A_w")
        Vn = 0.6 * Fy * Aw
        st.latex(rf"V_n = 0.6 \cdot {Fy} \cdot {Aw:.2f} = \mathbf{{{Vn:,.2f}}} \text{{ kg}}")
        
        # 3. Apply Factor
        st.markdown(f"#### 2.3 Design Shear Strength ({'LRFD' if is_lrfd else 'ASD'})")
        if is_lrfd:
            phi = 1.00
            st.latex(rf"\phi_v V_n = {phi} \cdot {Vn:,.2f} = \mathbf{{{data['V_cap']:,.2f}}} \text{{ kg}}")
        else:
            omega = 1.67
            st.latex(rf"V_n / \Omega_v = \frac{{{Vn:,.2f}}}{{{omega}}} = \mathbf{{{data['V_cap']:,.2f}}} \text{{ kg}}")
            
        # 4. Check
        st.markdown("#### 2.4 Shear Ratio Check")
        ratio_v = data['v_act'] / data['V_cap']
        status_v = "✅ OK" if ratio_v <= 1.0 else "❌ FAIL"
        st.metric("Shear Ratio", f"{ratio_v:.4f}", status_v)

    # =================================================================================
    # PART 3: MOMENT CHECK (แรงดัด)
    # =================================================================================
    st.header("3️⃣ Flexural Strength Check (ตรวจสอบแรงดัด)")
    
    with st.container(border=True):
        st.markdown("#### 3.1 Moment Demand ($M_{req}$)")
        st.latex(r"M_{req} = \frac{W \cdot L^2}{8}")
        st.latex(rf"M_{{req}} = \frac{{{w_calc:,.2f} \cdot {L_m:,.2f}^2}}{{8}} = \mathbf{{{data['m_act']:,.2f}}} \text{{ kg-m}}")
        
        st.markdown("#### 3.2 Moment Capacity ($M_{cap}$)")
        st.markdown(f"คำนวณโมเมนต์ต้านทานจากค่า Modulus ({'Plastic Zx' if is_lrfd else 'Elastic Sx'}):")
        
        if is_lrfd:
            st.latex(r"M_n = F_y \cdot Z_x")
            Mn = (Fy * Zx) / 100 # kg-m
            st.latex(rf"M_n = {Fy} \cdot {Zx:.2f} = {Mn*100:,.0f} \text{{ kg-cm}} = {Mn:,.2f} \text{{ kg-m}}")
            st.latex(rf"\phi M_n = 0.90 \cdot {Mn:,.2f} = \mathbf{{{data['M_cap']:,.2f}}} \text{{ kg-m}}")
        else:
            st.latex(r"M_n = F_y \cdot S_x")
            Mn = (Fy * Sx) / 100 # kg-m
            st.latex(rf"M_n = {Fy} \cdot {Sx:.2f} = {Mn*100:,.0f} \text{{ kg-cm}} = {Mn:,.2f} \text{{ kg-m}}")
            st.latex(rf"M_a = \frac{{M_n}}{{\Omega}} = \frac{{{Mn:,.2f}}}{{1.67}} = \mathbf{{{data['M_cap']:,.2f}}} \text{{ kg-m}}")

        # Check
        st.markdown("#### 3.3 Moment Ratio Check")
        ratio_m = data['m_act'] / data['M_cap']
        status_m = "✅ OK" if ratio_m <= 1.0 else "❌ FAIL"
        st.metric("Moment Ratio", f"{ratio_m:.4f}", status_m)

    # =================================================================================
    # PART 4: DEFLECTION CHECK (การแอ่นตัว) - *ละเอียด*
    # =================================================================================
    st.header("4️⃣ Deflection Check (ตรวจสอบการแอ่นตัว)")
    
    
    with st.container(border=True):
        st.markdown("#### 4.1 Unit Conversion (แปลงหน่วย)")
        w_kgcm = w_serv / 100
        st.latex(rf"w = \frac{{{w_serv:,.2f}}}{{100}} = {w_kgcm:.4f} \text{{ kg/cm}}")
        st.latex(rf"L = {L_m} \times 100 = {L_cm:.0f} \text{{ cm}}")
        st.latex(rf"E = {E:,.0f} \text{{ ksc}}, \quad I_x = {Ix:,.2f} \text{{ cm}}^4")
        
        st.markdown("#### 4.2 Actual Deflection Calculation ($\Delta_{act}$)")
        st.latex(r"\Delta_{act} = \frac{5 \cdot w \cdot L^4}{384 \cdot E \cdot I_x}")
        
        # แทนค่าแบบเห็นตัวเลข
        st.markdown("**แทนค่าตัวเลข:**")
        formula_sub = rf"\Delta_{{act}} = \frac{{5 \cdot ({w_kgcm:.4f}) \cdot ({L_cm:.0f})^4}}{{384 \cdot ({E:,.0f}) \cdot ({Ix:,.2f})}}"
        st.latex(formula_sub)
        
        # ผลลัพธ์
        st.latex(rf"\Delta_{{act}} = \mathbf{{{data['d_act']:.4f}}} \text{{ cm}}")
        
        st.markdown("#### 4.3 Allowable Deflection ($\Delta_{all}$)")
        denom = data['defl_denom']
        st.latex(rf"\Delta_{{all}} = \frac{{L}}{{{denom}}} = \frac{{{L_cm:.0f}}}{{{denom}}} = \mathbf{{{data['d_allow']:.4f}}} \text{{ cm}}")
        
        # Check
        st.markdown("#### 4.4 Deflection Ratio Check")
        ratio_d = data['d_act'] / data['d_allow']
        status_d = "✅ OK" if ratio_d <= 1.0 else "❌ FAIL"
        st.metric("Deflection Ratio", f"{ratio_d:.4f}", status_d)

    # --- FINAL VERDICT ---
    st.divider()
    gov_cause = data['gov_cause']
    gov_ratio = data['gov_ratio']
    color = "green" if gov_ratio <= 1.0 else "red"
    
    st.markdown(f"""
    <div style="background-color:{color}; padding:20px; border-radius:10px; color:white; text-align:center;">
        <h3>FINAL RESULT: {'PASS' if gov_ratio <= 1.0 else 'FAIL'}</h3>
        <p>Controlled by <b>{gov_cause}</b> with Ratio <b>{gov_ratio:.2%}</b></p>
    </div>
    """, unsafe_allow_html=True)
