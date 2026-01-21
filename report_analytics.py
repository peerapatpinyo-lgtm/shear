# report_analytics.py
# Version: 9.0 (Added: Single Beam Deep Dive - Control Zones)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math

try:
    from report_generator import get_standard_sections, calculate_connection, calculate_full_properties
except ImportError:
    st.error("⚠️ Error: Missing report_generator.py")
    st.stop()

def render_analytics_section(load_pct, bolt_dia, load_case, factor):
    """
    Main Dashboard:
    1. Graph 1: Overview
    2. Graph 2: Efficiency
    3. Graph 3: 3-Lines Limits
    4. NEW SECTION: Deep Dive (Control Zones for specific beam)
    """
    st.markdown("## 📊 Structural Analysis Dashboard")
    
    # --- Data Prep ---
    all_sections = get_standard_sections()
    data_list = []
    
    for sec in all_sections:
        r = calculate_connection(sec, load_pct, bolt_dia, factor, load_case)
        full_props = calculate_full_properties(sec) 
        
        # Calculate W Logic (Simplified for table)
        L_m = r['L_safe']
        if L_m > 0:
            w_shear = (2 * r['Vn_beam']) / L_m
            phi_Mn_kgm = (0.90 * sec['Fy'] * full_props['Zx (cm3)']) / 100
            w_moment = (8 * phi_Mn_kgm) / (L_m**2)
            E=2040000; Ix=full_props['Ix (cm4)']; L_cm=L_m*100; delta=L_cm/360
            w_defl = ((384*E*Ix*delta)/(5*(L_cm**4))) * 100
            safe_w = min(w_shear, w_moment, w_defl)
        else:
            safe_w = 0

        # Reverse Calculate Limits
        try: l_shear = (2 * r['Vn_beam']) / safe_w if safe_w > 0 else 0
        except: l_shear = 0
        try: l_moment = math.sqrt((8 * phi_Mn_kgm) / safe_w) if safe_w > 0 else 0
        except: l_moment = 0
        try:
             w_cm = safe_w/100
             l_cube = (384*E*Ix)/(1800*w_cm) if w_cm > 0 else 0
             l_defl = (l_cube**(1/3))/100
        except: l_defl = 0

        data_list.append({
            "Name": sec['name'].replace("H-", ""), 
            "Section": sec['name'],
            "Moment Limit": r['L_crit_moment'],
            "Deflection Limit": r['L_crit_defl'],
            "Shear Cap": r['Vn_beam'],
            "Max Span": r['L_safe'],
            "Weight (kg/m)": full_props['Area (cm2)']*0.785,
            "Safe W": safe_w,
            "L_Shear": l_shear, "L_Moment": l_moment, "L_Defl": l_defl,
            "Raw_Sec": sec # เก็บ object เต็มไว้ใช้ช่วง Deep Dive
        })

    df = pd.DataFrame(data_list)
    names = df['Name']
    x = np.arange(len(names))

    # ==========================================
    # 📉 GRAPH 1-3 (EXISTING DASHBOARD)
    # ==========================================
    # (ผมย่อโค้ดส่วนนี้เพื่อให้โฟกัสที่ของใหม่ แต่ในไฟล์จริงต้องมีโค้ดกราฟ 1,2,3 เดิมอยู่ตรงนี้ครับ)
    # ... [Code Graph 1, 2, 3 ที่คุณมีอยู่แล้ว] ...
    
    # เพื่อความชัวร์ ผมขออนุญาตแปะ Graph 3 (3 Lines) ให้ดูอีกทีเพราะมันคล้ายกับอันใหม่
    st.subheader("3️⃣ Theoretical Limits (Overview)")
    fig3, ax5 = plt.subplots(figsize=(12, 4))
    ax5.grid(True, linestyle='--', alpha=0.3)
    ax5.plot(x, df['L_Shear'], color='#9B59B6', linestyle=':', label='Limit: Shear')
    ax5.plot(x, df['L_Moment'], color='#E74C3C', linestyle='-', label='Limit: Moment')
    ax5.plot(x, df['L_Defl'], color='#2ECC71', linestyle='-', label='Limit: Deflection')
    ax5.set_ylabel('Span (m)'); ax5.set_xticks(x); ax5.set_xticklabels(names, rotation=90)
    ax5.legend(loc='upper left', fontsize=8)
    st.pyplot(fig3)
    st.divider()

    # ==========================================
    # 🔬 NEW SECTION: DEEP DIVE (SINGLE BEAM)
    # ==========================================
    st.markdown("## 🔬 Deep Dive: Control Zones Analysis")
    st.write("เลือกหน้าตัดเหล็ก เพื่อดูพฤติกรรมว่าช่วงความยาวไหน ถูกควบคุมด้วยแรงอะไร (Shear vs Moment vs Deflection)")

    # 1. Select Box
    selected_name = st.selectbox("Select Section to Analyze:", df['Section'].unique())
    
    # 2. Find selected section data
    selected_row = df[df['Section'] == selected_name].iloc[0]
    sec_data = selected_row['Raw_Sec']
    full_props = calculate_full_properties(sec_data)

    # 3. Generate Curve Data (Span 0.5m to 15m)
    spans = np.linspace(1.0, 15.0, 100) # แกน X: ระยะความยาว 1 - 15 เมตร
    
    w_shears = []
    w_moments = []
    w_defls = []
    governing_w = []
    control_mode = [] # เก็บว่าจุดนั้นใครคุม

    E_ksc = 2040000
    Fy = sec_data['Fy']
    Zx = full_props['Zx (cm3)']
    Ix = full_props['Ix (cm4)']
    # Shear Cap (Constant V_n)
    # Recalculate Vn purely (0.6FyAw)
    h, tw = sec_data['h'], sec_data['tw']
    Aw = h * tw # area web approx
    Vn = 0.60 * Fy * Aw

    for L in spans:
        # A. Shear Limit: w = 2V/L
        ws = (2 * Vn) / L
        
        # B. Moment Limit: w = 8M/L^2
        phi_Mn_kgm = (0.90 * Fy * Zx) / 100
        wm = (8 * phi_Mn_kgm) / (L**2)
        
        # C. Deflection Limit: w derived from delta = L/360
        # delta = 5wL^4 / 384EI -> w = 384EI delta / 5L^4
        L_cm = L * 100
        delta_allow = L_cm / 360
        w_d_kg_cm = (384 * E_ksc * Ix * delta_allow) / (5 * (L_cm**4))
        wd = w_d_kg_cm * 100

        w_shears.append(ws)
        w_moments.append(wm)
        w_defls.append(wd)
        
        # Check who controls
        min_val = min(ws, wm, wd)
        governing_w.append(min_val)
        
        if min_val == ws: control_mode.append('Shear')
        elif min_val == wm: control_mode.append('Moment')
        else: control_mode.append('Deflection')

    # --- PLOT DEEP DIVE GRAPH ---
    fig_deep, ax_d = plt.subplots(figsize=(10, 6))
    
    # Plot Curves
    ax_d.plot(spans, w_shears, color='#9B59B6', linestyle=':', linewidth=1.5, label='Shear Limit ($1/L$)', alpha=0.6)
    ax_d.plot(spans, w_moments, color='#E74C3C', linestyle='--', linewidth=2, label='Moment Limit ($1/L^2$)')
    ax_d.plot(spans, w_defls, color='#2ECC71', linestyle='-.', linewidth=2, label='Deflection Limit ($1/L^3$)')
    
    # Highlight Governing Line (Solid Thick)
    ax_d.plot(spans, governing_w, color='#34495E', linewidth=3, alpha=0.8, label='✅ Safe Capacity Curve')

    # Fill Zones (Color code background)
    # Logic: Fill area under curve based on control mode implies using fill_between with condition
    # But simplified visual: Just Look at the curves crossing
    
    ax_d.set_title(f"Capacity Curve for {selected_name}", fontweight='bold')
    ax_d.set_xlabel("Span Length (m)", fontweight='bold')
    ax_d.set_ylabel("Uniform Load Capacity (kg/m)", fontweight='bold')
    
    # Zoom in to relevant area
    max_y_show = max(np.max(governing_w)*1.5, 1000)
    ax_d.set_ylim(0, max_y_show)
    ax_d.set_xlim(1, 15)
    ax_d.grid(True, which='both', linestyle='--', alpha=0.4)
    ax_d.legend()

    # Create Zone Annotations
    # หาจุดตัดเพื่อเขียน text บอกโซน
    # ง่ายๆคือเช็คที่ span สั้น กลาง ยาว
    idx_short = 5 # approx 1.5m
    idx_med = 50  # approx 7m
    idx_long = 90 # approx 14m
    
    def get_zone_color(mode):
        if mode == 'Shear': return '#9B59B6'
        if mode == 'Moment': return '#E74C3C'
        return '#2ECC71'

    # Annotation Logic could be complex, let's use Streamlit text below instead for clarity
    
    st.pyplot(fig_deep)
    
    # Show Zone Explanation
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**Short Span:** Usually controlled by **{control_mode[5]}**")
    with col2:
        st.info(f"**Medium Span:** Usually controlled by **{control_mode[50]}**")
    with col3:
        st.info(f"**Long Span:** Usually controlled by **{control_mode[-1]}**")
