# report_analytics.py
# Version: 7.5 (3 Lines Strategy: Shear/Moment/Deflection Limits converted to Span)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math

# Import Logic
try:
    from report_generator import get_standard_sections, calculate_connection, calculate_full_properties
except ImportError:
    st.error("⚠️ Error: Missing report_generator.py")
    st.stop()

def render_analytics_section(load_pct, bolt_dia, load_case, factor):
    """
    Dashboard Updated V.7.5:
    Graph 2: Plot 3 Theoretical Span Limits (Shear vs Moment vs Deflection)
    Y-Axis = Span Length (m)
    """
    st.markdown("## 📊 Structural Analysis Dashboard")
    
    # --- 1. Data Processing ---
    all_sections = get_standard_sections()
    data_list = []
    
    for sec in all_sections:
        # ดึงค่าพื้นฐาน
        r = calculate_connection(sec, load_pct, bolt_dia, factor, load_case)
        full_props = calculate_full_properties(sec) 
        
        # คำนวณ Safe W (Governing Load) ก่อน เพื่อใช้เป็นฐาน
        L_m = r['L_safe']
        L_cm = L_m * 100
        safe_w_load = 0 # kg/m
        
        # Logic คำนวณ W (Load Capacity)
        w_shear_cap, w_moment_cap, w_defl_cap = 0, 0, 0
        
        if L_m > 0:
            # 1. Shear Load Capacity
            w_shear_cap = (2 * r['Vn_beam']) / L_m
            
            # 2. Moment Load Capacity
            phi_Mn_kgm = (0.90 * sec['Fy'] * full_props['Zx (cm3)']) / 100
            w_moment_cap = (8 * phi_Mn_kgm) / (L_m**2)
            
            # 3. Deflection Load Capacity
            E_ksc = 2040000; Ix = full_props['Ix (cm4)']; delta_allow_cm = L_cm / 360
            w_defl_kg_cm = (384 * E_ksc * Ix * delta_allow_cm) / (5 * (L_cm**4))
            w_defl_cap = w_defl_kg_cm * 100
            
            safe_w_load = min(w_shear_cap, w_moment_cap, w_defl_cap)

        # --- REVERSE CALCULATION: Convert Safe W back to Theoretical Max Span ---
        # "ถ้าต้องรับ W เท่านี้... แต่ละแรงยอมให้ยาวได้สูงสุดกี่เมตร?"
        
        # A. Span Limit by Shear: L = 2*Vn / w
        try:
            l_limit_shear = (2 * r['Vn_beam']) / safe_w_load if safe_w_load > 0 else 0
        except: l_limit_shear = 0

        # B. Span Limit by Moment: L = sqrt(8*Mn / w)
        try:
            phi_Mn_kgm = (0.90 * sec['Fy'] * full_props['Zx (cm3)']) / 100
            l_limit_moment = math.sqrt((8 * phi_Mn_kgm) / safe_w_load) if safe_w_load > 0 else 0
        except: l_limit_moment = 0

        # C. Span Limit by Deflection: L^3 = (384*E*I) / (5*w*360)  (Derived from delta=L/360)
        # สูตร: L = cube_root( (384EI)/(1800w) )  *ระวังหน่วย
        try:
            E = 2040000; Ix = full_props['Ix (cm4)']
            # w (kg/m) -> w/100 (kg/cm)
            w_cm = safe_w_load / 100
            # L^3 (cm3) = (384 * E * Ix) / (5 * w_cm * 360)
            l_cube_cm = (384 * E * Ix) / (1800 * w_cm)
            l_limit_defl = (l_cube_cm**(1/3)) / 100 # แปลงกลับเป็น m
        except: l_limit_defl = 0

        # น้ำหนักเหล็ก
        weight_kg_m = full_props['Area (cm2)'] * 0.785 
        
        data_list.append({
            "Name": sec['name'].replace("H-", ""), 
            "Section": sec['name'],
            "Weight (kg/m)": weight_kg_m,
            "Safe W": safe_w_load,
            "L_Shear": l_limit_shear,
            "L_Moment": l_limit_moment,
            "L_Defl": l_limit_defl,
            "L_Safe_Real": r['L_safe'] # คือค่าต่ำสุดของ 3 ตัวบน
        })

    df = pd.DataFrame(data_list)
    names = df['Name']
    x = np.arange(len(names))

    # ==================================================
    # 📈 GRAPH 1: OPTIMIZATION GAP (Original)
    # ==================================================
    # (คงกราฟเดิมไว้ตามขอ เพื่อดู Range)
    st.subheader("1️⃣ Optimization Gap (Span Range)")
    fig1, ax1 = plt.subplots(figsize=(12, 4))
    ax1.grid(which='major', axis='y', linestyle='--', linewidth=0.5, alpha=0.3)
    
    # Plot Simple Range
    ax1.bar(x, df['L_Safe_Real'], color='#2ECC71', alpha=0.5, label='Safe Span Limit')
    ax1.set_ylabel('Safe Span (m)', fontweight='bold')
    ax1.set_xticks(x); ax1.set_xticklabels(names, rotation=90, fontsize=9)
    ax1.set_xlim(-0.5, len(names)-0.5)
    st.pyplot(fig1)

    st.divider()

    # ==================================================
    # 📉 GRAPH 2: 3-LINES LIMITS (Y = Span Length)
    # ==================================================
    st.subheader("2️⃣ Theoretical Span Limits (Shear vs Moment vs Deflection)")
    st.caption("กราฟนี้แสดง 'ระยะไกลสุด' ที่แต่ละแรงยอมให้รับได้ (ที่น้ำหนักบรรทุก $W_{safe}$) \nเส้นที่ **ต่ำที่สุด** คือตัวกำหนดระยะปลอดภัยจริง")

    fig2, ax_main = plt.subplots(figsize=(12, 6))
    ax_main.grid(which='major', axis='y', linestyle='--', linewidth=0.5, color='gray', alpha=0.3)

    # 3 Lines Plotting
    # 1. Shear Limit (มักจะสูงมา เพราะเหล็กรับ Shear ได้เยอะ)
    ax_main.plot(x, df['L_Shear'], color='#9B59B6', linestyle=':', marker='x', markersize=4, linewidth=1.5, label='Limit by Shear', alpha=0.6)
    
    # 2. Moment Limit (สีแดง)
    ax_main.plot(x, df['L_Moment'], color='#E74C3C', linestyle='-', marker='o', markersize=4, linewidth=2, label='Limit by Moment')
    
    # 3. Deflection Limit (สีน้ำเงิน)
    ax_main.plot(x, df['L_Defl'], color='#3498DB', linestyle='-', marker='s', markersize=4, linewidth=2, label='Limit by Deflection')

    # Fill พื้นที่ใต้กราฟตัวต่ำสุด เพื่อให้เห็น Safe Zone
    min_vals = np.minimum(np.minimum(df['L_Shear'], df['L_Moment']), df['L_Defl'])
    ax_main.fill_between(x, 0, min_vals, color='#2ECC71', alpha=0.15, label='Safe Span Zone')

    # จัดแกน Y (Span)
    ax_main.set_ylabel('Theoretical Max Span (m)', fontweight='bold', color='#2C3E50')
    ax_main.set_xticks(x)
    ax_main.set_xticklabels(names, rotation=90, fontsize=9)
    ax_main.set_xlim(-0.5, len(names)-0.5)
    
    # Auto Scale Y (ตัด Shear ทิ้งถ้ามันโด่งเกินไป เพื่อให้เห็น Moment/Defl ชัดๆ)
    max_reasonable = max(df['L_Moment'].max(), df['L_Defl'].max()) * 1.3
    ax_main.set_ylim(0, max_reasonable)

    # Secondary Axis for Weight (คงของเดิมไว้ ไม่ตัดทิ้ง)
    ax_weight = ax_main.twinx()
    ax_weight.plot(x, df['Weight (kg/m)'], color='gray', linestyle='--', linewidth=1, alpha=0.5, label='Steel Weight (Ref)')
    ax_weight.set_ylabel('Steel Weight (kg/m) [Dashed]', color='gray', fontsize=8)
    
    # Legends
    lines1, labels1 = ax_main.get_legend_handles_labels()
    lines2, labels2 = ax_weight.get_legend_handles_labels()
    ax_main.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=9, ncol=2)

    st.pyplot(fig2)
    
    st.divider()

    # --- 3. Table ---
    st.subheader("📋 Specification Table")
    st.dataframe(
        df[["Section", "Safe W", "L_Moment", "L_Defl", "L_Shear", "L_Safe_Real"]],
        use_container_width=True,
        column_config={
            "Section": st.column_config.TextColumn("Section", width="medium"),
            "Safe W": st.column_config.NumberColumn("Load W (kg/m)", format="%.0f"),
            "L_Moment": st.column_config.NumberColumn("L(Moment)", format="%.2f m"),
            "L_Defl": st.column_config.NumberColumn("L(Defl)", format="%.2f m"),
            "L_Shear": st.column_config.NumberColumn("L(Shear)", format="%.2f m"),
            "L_Safe_Real": st.column_config.NumberColumn("✅ Safe Span", format="%.2f m"),
        },
        height=400,
        hide_index=True
    )
