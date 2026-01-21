# report_analytics.py
# Version: 22.0 (Ultimate Design: 6 Failure Modes Check - Bolt, Bearing, Yield, Rupture, Block Shear, Weld)
# Engineered by: Senior Structural Engineer AI

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

# --- Engineering Constants (ASD - Allowable Stress Design) ---
E_STEEL_KSC = 2040000  

# Material Properties (SS400 / A36)
FY_PLATE = 2400 # ksc
FU_PLATE = 4000 # ksc (Ultimate tensile)

# Bolt Properties (A325 / F10T approx)
FV_BOLT = 2100   # Allowable Shear Stress (ksc)
# FP_BEARING = 1.2 * Fu (Basic check, will use formula)

# Weld Properties (E70xx)
FV_WELD = 0.30 * 4900 # Allowable shear on throat (approx 1470 ksc)

def render_analytics_section(load_pct, bolt_dia, load_case, factor):
    """
    Renders the Structural Analytics Dashboard.
    - Full AISC Failure Mode Analysis (6 Modes).
    - Auto-Optimization loop.
    """
    st.markdown("## 📊 Structural Integrity & Optimization Dashboard")
    st.markdown("Comprehensive connection design checking **6 failure modes** (Shear, Bearing, Yield, Rupture, Block Shear, Weld).")
    
    # --- 1. Data Processing ---
    all_sections = get_standard_sections()
    if not all_sections:
        st.warning("⚠️ System Notice: No structural sections found.")
        return

    data_list = []
    
    for sec in all_sections:
        full_props = calculate_full_properties(sec) 
        
        # 1.1 BEAM CAPACITY
        h_cm = sec['h'] / 10
        tw_cm = sec['tw'] / 10
        V_beam_nominal = 0.60 * sec['Fy'] * (h_cm * tw_cm)
        V_beam_allow = V_beam_nominal / factor if factor and factor > 0 else V_beam_nominal

        # 1.2 DESIGN TARGET (75%)
        V_target = V_beam_allow * 0.75

        # 1.3 GRAPH LIMITS (Standard)
        try:
            M_n_kgcm = sec['Fy'] * full_props['Zx (cm3)']
            M_allow_kgm = (M_n_kgcm / factor) / 100 if factor and factor > 0 else 0
        except: M_allow_kgm = 0
        
        Ix = full_props['Ix (cm4)']
        K_defl = (384 * E_STEEL_KSC * Ix) / 18000000 
        L_shear_moment_limit = (4 * M_allow_kgm) / V_beam_allow if V_beam_allow > 0 else 0
        L_moment_defl_limit = K_defl / (8 * M_allow_kgm) if M_allow_kgm > 0 else 0
        
        if L_moment_defl_limit > L_shear_moment_limit:
            zone_text = f"{L_shear_moment_limit:.2f} - {L_moment_defl_limit:.2f}"
        else: zone_text = "Check Design"

        # ============================================================
        # ⚙️ 1.4 ULTIMATE AUTO-DESIGN LOGIC (The 6 Checks)
        # ============================================================
        
        # Initial Assumptions
        bolt_d_cm = bolt_dia / 10
        hole_d_cm = bolt_d_cm + 0.2 # Standard hole clearance
        pitch_cm = 3 * bolt_d_cm
        edge_cm = 4.0 
        
        # Start Iteration
        req_bolts = 2
        t_plate_cm = 0.9 # Start 9mm
        if V_target > 30000: t_plate_cm = 1.2
        
        is_safe = False
        final_info = {}
        
        while not is_safe and req_bolts <= 20:
            # Geometry
            plate_h_cm = ((req_bolts - 1) * pitch_cm) + (2 * edge_cm)
            plate_h_cm = math.ceil(plate_h_cm) # Round up cm
            plate_w_cm = 10.0 # Standard width
            
            # --- CHECK 1: BOLT SHEAR ---
            Ab = 3.14159 * (bolt_d_cm**2) / 4
            Rn_bolt_shear = req_bolts * FV_BOLT * Ab
            
            # --- CHECK 2: BEARING (At Bolt Holes) ---
            # Rn = 1.2 * Lc * t * Fu <= 2.4 * d * t * Fu
            # Check edge bolt vs inner bolts
            Lc_edge = edge_cm - (hole_d_cm / 2)
            Rn_bear_edge = 1.2 * Lc_edge * t_plate_cm * FU_PLATE
            Rn_bear_edge_lim = 2.4 * bolt_d_cm * t_plate_cm * FU_PLATE
            Rn_bear_edge = min(Rn_bear_edge, Rn_bear_edge_lim)
            
            Lc_inner = pitch_cm - hole_d_cm
            Rn_bear_inner = 1.2 * Lc_inner * t_plate_cm * FU_PLATE
            Rn_bear_inner_lim = 2.4 * bolt_d_cm * t_plate_cm * FU_PLATE
            Rn_bear_inner = min(Rn_bear_inner, Rn_bear_inner_lim)
            
            Rn_bearing_total = Rn_bear_edge + ((req_bolts - 1) * Rn_bear_inner)
            
            # --- CHECK 3: PLATE GROSS YIELD ---
            Ag = plate_h_cm * t_plate_cm
            Rn_yield = 0.60 * FY_PLATE * Ag
            
            # --- CHECK 4: PLATE NET RUPTURE ---
            # An = Ag - (n * hole * t)
            An = Ag - (req_bolts * hole_d_cm * t_plate_cm)
            Rn_rupture = 0.50 * FU_PLATE * An # 0.5 Fu An (ASD conservative)
            
            # --- CHECK 5: BLOCK SHEAR ---
            # Failure path: Shear along vertical line of bolts + Tension on bottom edge
            # Agv (Gross Shear Area) = (H - Edge_top) * t
            # Anv (Net Shear Area) = Agv - (n - 0.5) * hole * t
            # Ant (Net Tension Area) = (Edge_side - 0.5*hole) * t -> Assume 40mm edge side
            edge_side_cm = 4.0 # Distance from weld to bolt line
            
            L_shear_path = plate_h_cm - edge_cm # Length from top bolt to bottom of plate (or vice versa)
            Agv = L_shear_path * t_plate_cm
            Anv = Agv - ((req_bolts - 0.5) * hole_d_cm * t_plate_cm)
            
            Ant = (edge_side_cm - (0.5 * hole_d_cm)) * t_plate_cm
            
            # Formula: Rn = 0.6 Fu Anv + Ubs Fu Ant
            Rn_block = (0.6 * FU_PLATE * Anv) + (1.0 * FU_PLATE * Ant)
            
            # --- CHECK 6: WELD CAPACITY ---
            # Double Fillet Weld (2 sides)
            weld_size_cm = (t_plate_cm * 10 - 2) / 10 # Rule of thumb: t_plate - 1.5mm ~ 2mm
            if weld_size_cm < 0.6: weld_size_cm = 0.6 # Min 6mm
            
            # Effective Throat = 0.707 * size
            # Length = Plate Height
            # Rn = 2 lines * 0.707 * w * L * F_weld
            Rn_weld = 2 * 0.707 * weld_size_cm * plate_h_cm * FV_WELD
            
            # --- EVALUATE ---
            capacities = {
                "Bolt Shear": Rn_bolt_shear,
                "Bearing": Rn_bearing_total,
                "Gross Yield": Rn_yield,
                "Net Rupture": Rn_rupture,
                "Block Shear": Rn_block,
                "Weld": Rn_weld
            }
            
            min_capacity = min(capacities.values())
            governing_mode = min(capacities, key=capacities.get)
            
            ratio = V_target / min_capacity
            
            if ratio <= 1.00:
                is_safe = True
                final_info = {
                    "Bolts": req_bolts,
                    "Plate": f"PL-{t_plate_cm*10:.0f}x100x{plate_h_cm*10:.0f}",
                    "Weld": f"{weld_size_cm*10:.0f}mm (2 sides)",
                    "Ratio": ratio,
                    "Governing": governing_mode
                }
            else:
                req_bolts += 1
                if req_bolts > 12 and t_plate_cm < 1.5:
                    t_plate_cm += 0.3 # Increase thickness if too many bolts needed
                    req_bolts = max(2, req_bolts - 2) # Reset bolts slightly
        
        # 1.5 Compiling Data
        data_list.append({
            "Section": sec['name'],
            "Moment Zone": zone_text,
            "V_Beam (100%)": V_beam_allow,
            "V_Target (75%)": V_target,
            "Bolt Spec": f"{final_info.get('Bolts',0)} - M{int(bolt_dia)}",
            "Plate Size": final_info.get('Plate','-'),
            "Weld Spec": final_info.get('Weld','-'),
            "D/C Ratio": final_info.get('Ratio', 9.99),
            "Governing Failure": final_info.get('Governing', 'Design Failed'),
            
            # Deep Dive
            "L_Start": L_shear_moment_limit, 
            "L_End": L_moment_defl_limit,
            "V_allow": V_beam_allow,         
            "M_allow_kgm": M_allow_kgm, 
            "K_defl": K_defl
        })

    if not data_list: return
    df = pd.DataFrame(data_list)

    # ==========================================
    # 🔬 GRAPH: DEEP DIVE (Same as before)
    # ==========================================
    st.subheader("🔬 Deep Dive: Critical Limit Analysis")
    
    if 'Section' not in df.columns or df.empty: return

    col_sel, col_empty = st.columns([1, 2])
    with col_sel:
        selected_name = st.selectbox("Select Section:", df['Section'].unique())

    row = df[df['Section'] == selected_name].iloc[0]
    V_allow = row['V_allow']
    M_allow_kgm = row['M_allow_kgm']
    K_defl = row['K_defl']
    L_start = row['L_Start']
    L_end = row['L_End']

    max_span_plot = max(8, L_end * 1.4)
    spans = np.linspace(0.5, max_span_plot, 300)
    
    ws = (2 * V_allow) / spans
    wm = (8 * M_allow_kgm) / (spans**2)
    wd = K_defl / (spans**3)
    w_safe_envelope = np.minimum(np.minimum(ws, wm), wd)

    fig_d, ax_d = plt.subplots(figsize=(10, 6))
    ax_d.grid(True, which='both', linestyle='--', alpha=0.4)
    ax_d.plot(spans, ws, color='#9B59B6', linestyle=':', linewidth=1.5, alpha=0.6, label='Beam Shear Limit')
    ax_d.plot(spans, wd, color='#2ECC71', linestyle='-.', linewidth=1.5, alpha=0.6, label='Deflection Limit')
    ax_d.plot(spans, wm, color='#E74C3C', linestyle='--', linewidth=1.5, alpha=0.6, label='Moment Limit')
    ax_d.plot(spans, w_safe_envelope, color='#2C3E50', linewidth=3, label='Safe Envelope')
    
    if L_end > L_start:
        idx_start = np.searchsorted(spans, L_start)
        idx_end = np.searchsorted(spans, L_end)
        ax_d.fill_between(spans[idx_start:idx_end], 0, w_safe_envelope[idx_start:idx_end], 
                          color='#E74C3C', alpha=0.15, label='Moment Zone')

    ax_d.set_ylim(0, max(w_safe_envelope)*1.2 if max(w_safe_envelope)>0 else 1000)
    ax_d.set_xlim(0.5, max_span_plot)
    ax_d.legend(loc='upper right')
    st.pyplot(fig_d)

    st.divider()

    # ==========================================
    # 📋 ULTIMATE SPECIFICATION TABLE
    # ==========================================
    st.subheader("📋 Specification Table: Fully Verified Design (6 Failure Modes)")
    
    st.dataframe(
        df[[
            "Section", "Moment Zone", "V_Target (75%)", 
            "Bolt Spec", "Plate Size", "Weld Spec", 
            "D/C Ratio", "Governing Failure"
        ]],
        use_container_width=True,
        column_config={
            "Section": st.column_config.TextColumn("Section", width="small"),
            "Moment Zone": st.column_config.TextColumn("Zone (m)", width="small"),
            "V_Target (75%)": st.column_config.NumberColumn("Load (kg)", format="%.0f"),
            "Bolt Spec": st.column_config.TextColumn("Bolts", width="small"),
            "Plate Size": st.column_config.TextColumn("Plate (mm)", width="medium"),
            "Weld Spec": st.column_config.TextColumn("Weld", width="small"),
            "D/C Ratio": st.column_config.NumberColumn(
                "Max Ratio", 
                format="%.2f", 
                help="Maximum Demand/Capacity Ratio from all 6 checks."
            ),
            "Governing Failure": st.column_config.TextColumn(
                "Critical Mode", 
                width="medium",
                help="The failure mode that caused the highest ratio."
            ),
        },
        height=500,
        hide_index=True
    )
    
    st.info("""
    **ℹ️ Engineering Note:**
    Design checks include: 
    1. Bolt Shear 2. Bolt Bearing 3. Plate Gross Yield 
    4. Plate Net Rupture 5. Block Shear 6. Weld Capacity
    """)
