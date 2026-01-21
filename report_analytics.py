# report_analytics.py
# Version: 1.0 (Separate Analytics Module)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
# Import Logic from main file (Make sure report_generator.py is in the same folder)
from report_generator import get_standard_sections, calculate_connection

def render_analytics_section(load_pct, bolt_dia, load_case, factor):
    """
    ฟังก์ชันสำหรับแสดงผลกราฟและตารางเปรียบเทียบ
    รับค่าพารามิเตอร์จากหน้าหลักมาคำนวณ batch analysis
    """
    st.markdown("## 📊 Analytics Dashboard")
    
    all_sections = get_standard_sections()
    names, moments, defls, shears = [], [], [], []
    batch_results = []

    # --- 1. Batch Calculation ---
    for sec in all_sections:
        r = calculate_connection(sec, load_pct, bolt_dia, factor, load_case)
        
        # Data for Graph
        names.append(sec['name'].replace("H-", "")) 
        moments.append(r['L_crit_moment'])
        defls.append(r['L_crit_defl'])
        shears.append(r['Vn_beam']) 
        
        # Data for Table
        actual_cap = r['Bolt Qty'] * r['phiRn_bolt']
        util = (r['V_target'] / actual_cap) * 100 if actual_cap > 0 else 0
        
        batch_results.append({
            "Section": r['Section'],
            "Design Vu (kg)": r['V_target'],
            "Max Span (m)": r['L_safe'],
            "Limit State": "Moment" if r['L_crit_moment'] < r['L_crit_defl'] else "Deflection",
            "Bolt Qty": r['Bolt Qty'],
            "Plate H (mm)": int(r['Plate Len']*10),
            "Util. (%)": util
        })

    # --- 2. Structural Limit States Diagram ---
    st.subheader("📈 Structural Limit States Diagram")
    
    fig, ax1 = plt.subplots(figsize=(12, 5))
    x = range(len(names))
    
    # Axis 1: Span Length
    ax1.set_ylabel('Span (m)', color='#27AE60', fontweight='bold')
    ax1.plot(x, moments, 'r--', label='Moment Limit', alpha=0.5)
    ax1.plot(x, defls, 'b-', label='Deflection Limit', alpha=0.5)
    ax1.fill_between(x, 0, np.minimum(moments, defls), color='#2ECC71', alpha=0.3, label='Safe Zone')
    ax1.legend(loc='upper left')
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=90, fontsize=8)
    ax1.grid(True, linestyle=':', alpha=0.5)
    
    # Axis 2: Shear Capacity (Reference)
    ax2 = ax1.twinx()
    ax2.set_ylabel('Shear Capacity (kg)', color='purple', fontweight='bold')
    ax2.plot(x, shears, color='purple', linestyle=':', label='Shear Check (Ref)')
    
    st.pyplot(fig)

    st.divider()

    # --- 3. Comparative Analysis Table ---
    st.subheader("📋 Comparative Analysis Table")
    
    # Filter/Sort Controls (Optional extra feature)
    col_sort, col_filter = st.columns(2)
    with col_sort:
        sort_by = st.selectbox("Sort By", ["Section", "Max Span (m)", "Util. (%)"], index=1)
        
    df_compare = pd.DataFrame(batch_results)
    
    # Sorting Logic
    if sort_by == "Max Span (m)":
        df_compare = df_compare.sort_values(by="Max Span (m)", ascending=False)
    elif sort_by == "Util. (%)":
        df_compare = df_compare.sort_values(by="Util. (%)", ascending=False)
        
    st.dataframe(
        df_compare,
        use_container_width=True,
        column_config={
            "Design Vu (kg)": st.column_config.NumberColumn("Load (kg)", format="%.0f"),
            "Max Span (m)": st.column_config.NumberColumn("Safe Span (m)", format="%.2f"),
            "Bolt Qty": st.column_config.NumberColumn("Bolts", format="%d"),
            "Util. (%)": st.column_config.ProgressColumn("Capacity Usage", format="%.0f%%", min_value=0, max_value=100),
        },
        hide_index=True, height=600
    )
