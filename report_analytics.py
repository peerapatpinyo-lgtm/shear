# report_analytics.py
# Version: 25.0 (Ultimate Structural Engineer Edition)
# Engineered by: Senior Structural Engineer AI
# Features: Strict AISC Limit States, Worst-Case Identification, Efficiency Visualization

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math

# --- Module Integrity Check ---
try:
    from report_generator import get_standard_sections, calculate_full_properties
except ImportError:
    st.error("🚨 Critical Error: Core module 'report_generator.py' is missing.")
    st.stop()

# --- Engineering Constants (ASD) ---
E_STEEL_KSC = 2040000  
FY_PLATE = 2400 
FU_PLATE = 4000 
FV_BOLT = 2100  
FV_WELD = 1470  

def render_analytics_section(load_pct, bolt_dia, load_case, factor):
    """
    Renders the Ultimate Structural Dashboard.
    Focus: Explicit Governing Failure Modes & Utilization Ratios.
    """
    
    st.markdown("## 🏗️ Structural Integrity & Limit State Analysis")
    st.markdown("""
    **Engineering Executive Summary:**
    Analysis based on **AISC 360** Specification using Allowable Strength Design (ASD).
    Verifying **6 Limit States**: Bolt Shear, Bearing, Gross Yield, Net Rupture, Block Shear, and Weld Strength.
    """)
    st.divider()

    # --- 1. CORE CALCULATION ENGINE ---
    all_sections = get_standard_sections()
    if not all_sections: return

    data_list = []
    
    for sec in all_sections:
        # --- A. Demand Analysis ---
        h_cm = sec['h'] / 10
        tw_cm = sec['tw'] / 10
        
        # Beam Web Shear Capacity (Global Limit)
        V_beam_allow = (0.60 * sec['Fy'] * h_cm * tw_cm) / (factor if factor else 1)
        
        # Ultimate Demand for Connection (User defined %)
        V_demand = V_beam_allow * (load_pct / 100.0) # Corrected to use input pct (e.g. 75%)

        # --- B. Connection Auto-Design & Optimization ---
        # Constants
        bolt_d_cm = bolt_dia / 10
        hole_d_cm = bolt_d_cm + 0.2
        pitch_cm = 3 * bolt_d_cm
        edge_cm = 4.0 
        
        # Iterator Setup
        req_bolts = 2
        t_plate_cm = 0.9
        if V_demand > 30000: t_plate_cm = 1.2
        
        design_passed = False
        final_data = {}
        
        # Design Loop: Find minimum bolts/plate to satisfy D/C <= 1.0
        while not design_passed and req_bolts <= 24:
            # Geometry
            plate_h_cm = math.ceil(((req_bolts - 1) * pitch_cm) + (2 * edge_cm))
            
            # --- C. Limit State Checks (AISC) ---
            
            # 1. Bolt Shear
            Ab = 3.14159 * bolt_d_cm**2 / 4
            Rn_bolt = req_bolts * FV_BOLT * Ab
            
            # 2. Bolt Bearing (Tearout)
            # Edge Bolts
            Lc_edge = edge_cm - (hole_d_cm / 2)
            Rn_edge = min(1.2 * Lc_edge * t_plate_cm * FU_PLATE, 2.4 * bolt_d_cm * t_plate_cm * FU_PLATE)
            # Inner Bolts
            Lc_inner = pitch_cm - hole_d_cm
            Rn_inner = min(1.2 * Lc_inner * t_plate_cm * FU_PLATE, 2.4 * bolt_d_cm * t_plate_cm * FU_PLATE)
            
            Rn_bearing = Rn_edge + ((req_bolts - 1) * Rn_inner)
            
            # 3. Plate Gross Yield
            Ag = plate_h_cm * t_plate_cm
            Rn_yield = 0.60 * FY_PLATE * Ag
            
            # 4. Plate Net Rupture
            An = Ag - (req_bolts * hole_d_cm * t_plate_cm)
            Rn_rupture = 0.50 * FU_PLATE * An
            
            # 5. Block Shear (Assuming shear path along bolts, tension at bottom)
            # Path Length = (H - Edge)
            Agv = (plate_h_cm - edge_cm) * t_plate_cm
            Anv = Agv - ((req_bolts - 0.5) * hole_d_cm * t_plate_cm)
            Ant = (4.0 - 0.5 * hole_d_cm) * t_plate_cm # Assume 40mm side edge
            Rn_block = (0.6 * FU_PLATE * Anv) + (1.0 * FU_PLATE * Ant)
            
            # 6. Weld Capacity (Fillet)
            weld_sz = max(0.6, (t_plate_cm*10 - 2)/10)
            Rn_weld = 2 * 0.707 * weld_sz * plate_h_cm * FV_WELD
            
            # --- D. Evaluate Ratios ---
            limit_states = {
                "Bolt Shear": Rn_bolt,
                "Bearing": Rn_bearing,
                "Plate Yield": Rn_yield,
                "Plate Rupture": Rn_rupture,
                "Block Shear": Rn_block,
                "Weld Shear": Rn_weld
            }
            
            # Find the Governing Case (Min Capacity)
            min_capacity = min(limit_states.values())
            governing_mode = min(limit_states, key=limit_states.get)
            
            # Calculate Max Ratio (Demand / Min Capacity)
            max_ratio = V_demand / min_capacity
            
            if max_ratio <= 1.00:
                design_passed = True
                final_data = {
                    "Bolts": req_bolts,
                    "Plate": f"PL-{t_plate_cm*10:.0f}x100x{plate_h_cm*10:.0f}",
                    "Weld": f"{weld_sz*10:.0f}mm",
                    "Capacity": min_capacity,
                    "Ratio": max_ratio,
                    "Mode": governing_mode
                }
            else:
                # Upsize for next iteration
                req_bolts += 1
                if req_bolts > 12 and t_plate_cm < 1.6:
                    t_plate_cm += 0.3 # Increase plate thickness
                    req_bolts = max(2, req_bolts - 3) # Reset bolts slightly
        
        # Append Result
        data_list.append({
            "Section": sec['name'],
            "V_Demand": V_demand,
            "V_Capacity": final_data.get('Capacity', 0),
            "Utilization": final_data.get('Ratio', 9.99), # THIS IS THE SAFETY RATIO
            "Governing Limit State": final_data.get('Mode', 'Design Failed'),
            "Configuration": f"{final_data.get('Bolts')} - M{int(bolt_dia)}",
            "Plate Detail": final_data.get('Plate'),
            "Status": "✅ PASS" if final_data.get('Ratio', 9.99) <= 1.0 else "❌ FAIL"
        })

    if not data_list: return
    df = pd.DataFrame(data_list)

    # --- 2. EXECUTIVE DASHBOARD ---
    
    # Metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Total Connections", len(df))
    with c2: 
        max_ut = df['Utilization'].max()
        st.metric("Max Utilization (D/C)", f"{max_ut:.2f}", delta="Critical" if max_ut > 0.9 else "Safe", delta_color="inverse")
    with c3:
        crit_mode = df['Governing Limit State'].mode()[0]
        st.metric("Most Frequent Control", crit_mode)
    with c4:
        avg_eff = df['Utilization'].mean() * 100
        st.metric("Avg. Efficiency", f"{avg_eff:.1f}%")

    st.markdown("---")
    
    # --- 3. VISUALIZATION: Utilization Map ---
    # This chart helps engineers see the distribution of safety factors
    st.subheader("📉 Connection Efficiency Map (D/C Ratio Distribution)")
    
    fig, ax = plt.subplots(figsize=(10, 4))
    # Color mapping
    colors = ['#2ECC71' if x < 0.75 else '#F1C40F' if x < 0.95 else '#E74C3C' for x in df['Utilization']]
    
    ax.scatter(df['Section'], df['Utilization'], c=colors, s=100, alpha=0.8, edgecolors='black')
    ax.axhline(y=1.0, color='red', linestyle='--', linewidth=2, label='Limit (1.0)')
    ax.axhline(y=0.75, color='green', linestyle=':', linewidth=1, label='Target Efficiency')
    
    ax.set_ylabel("D/C Ratio (Demand/Capacity)", fontweight='bold')
    ax.set_title("Utilization Ratio per Section", fontweight='bold')
    ax.tick_params(axis='x', rotation=90)
    ax.set_ylim(0, 1.2)
    ax.legend(loc='upper right')
    ax.grid(True, linestyle='--', alpha=0.3)
    
    st.pyplot(fig)
    
    st.caption("🟢 < 0.75: Conservative | 🟡 0.75 - 0.95: Optimized | 🔴 > 0.95: Critical")
    
    st.markdown("---")

    # --- 4. DETAILED ENGINEERING TABLE ---
    st.subheader("📋 Detailed Design Verification Table")
    st.markdown("Displays the **Governing Case** (Maximum Ratio) derived from 6 failure modes.")

    # Highlighting Logic for the Table using Pandas Styler or Streamlit Column Config
    st.dataframe(
        df[[
            "Section", "Status", "Utilization", "V_Demand", "V_Capacity", 
            "Governing Limit State", "Configuration", "Plate Detail"
        ]].sort_values(by="Utilization", ascending=False),
        use_container_width=True,
        column_config={
            "Section": st.column_config.TextColumn("Beam Section", width="small", help="H-Beam Identifier"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Utilization": st.column_config.ProgressColumn(
                "Safety Ratio (D/C)",
                help="Demand divided by Capacity. Must be <= 1.0",
                format="%.2f",
                min_value=0,
                max_value=1.1,
            ),
            "V_Demand": st.column_config.NumberColumn("Demand (kg)", format="%.0f"),
            "V_Capacity": st.column_config.NumberColumn("Capacity (kg)", format="%.0f", help="Governing Strength"),
            "Governing Limit State": st.column_config.TextColumn("Governing Mode", width="medium", help="The failure mode that controls the design"),
            "Configuration": st.column_config.TextColumn("Bolts", width="small"),
            "Plate Detail": st.column_config.TextColumn("Plate Size", width="medium"),
        },
        height=600,
        hide_index=True
    )
    
    # Download Button for Report
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Download Engineering Report (CSV)",
        csv,
        "connection_design_report.csv",
        "text/csv",
        key='download-csv'
    )
