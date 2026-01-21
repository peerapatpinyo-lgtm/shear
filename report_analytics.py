import streamlit as st
import pandas as pd
import numpy as np
import math
import plotly.graph_objects as go 

# --- Module Integrity Check ---
try:
    from report_generator import get_standard_sections, calculate_full_properties
except ImportError:
    st.error("🚨 Critical Error: Core module 'report_generator.py' is missing.")
    st.stop()

# --- Engineering Constants ---
E_STEEL_KSC = 2040000  
FY_PLATE = 2400 
FU_PLATE = 4000 
FV_BOLT = 2100  
FV_WELD = 1470  

def render_analytics_section(load_pct, bolt_dia, load_case, factor):
    """
    Renders the Structural Analytics Dashboard.
    - Version 37.0: 
        1. Fixed MISSING DATA: Brought back 'Moment Zone' span range into the table.
        2. Retained all Graph features (Authentic shading, Zero-lock axes).
    """
    
    st.markdown("## 🏗️ Structural Optimization Dashboard")
    st.divider()

    all_sections = get_standard_sections()
    if not all_sections:
        st.warning("⚠️ No sections found.")
        return

    data_list = []
    
    # --- 1. CALCULATION CORE ---
    for sec in all_sections:
        full_props = calculate_full_properties(sec) 
        
        # --- A. SHEAR CAPACITY (Nominal) ---
        h_cm = sec['h'] / 10
        tw_cm = sec['tw'] / 10
        Aw = h_cm * tw_cm
        V_beam_nominal = 0.60 * sec['Fy'] * Aw 
        
        V_target = V_beam_nominal * (load_pct / 100.0)

        # --- B. ZONES ---
        try:
            M_n_kgcm = sec['Fy'] * full_props['Zx (cm3)']
            M_limit_kgm = M_n_kgcm / 100 
        except: M_limit_kgm = 0
        
        Ix = full_props['Ix (cm4)']
        K_defl = (384 * E_STEEL_KSC * Ix) / 18000000 
        
        L_sm = (4 * M_limit_kgm) / V_beam_nominal if V_beam_nominal > 0 else 0
        L_md = K_defl / (8 * M_limit_kgm) if M_limit_kgm > 0 else 0
        
        # --- C. AUTO-DESIGN ---
        bolt_d_cm = bolt_dia / 10
        hole_d_cm = bolt_d_cm + 0.2
        pitch_cm = 3 * bolt_d_cm
        edge_cm = 4.0 
        req_bolts = 2; t_plate_cm = 0.9; 
        if V_target > 30000: t_plate_cm = 1.2
        
        is_safe = False; final_info = {}
        
        while not is_safe and req_bolts <= 24:
            plate_h_cm = math.ceil(((req_bolts - 1) * pitch_cm) + (2 * edge_cm))
            
            # Checks
            Rn_bolt = req_bolts * FV_BOLT * (3.14159 * bolt_d_cm**2 / 4)
            Lc_edge = edge_cm - hole_d_cm/2; Lc_inner = pitch_cm - hole_d_cm
            Rn_bear = (min(1.2*Lc_edge*t_plate_cm*FU_PLATE, 2.4*bolt_d_cm*t_plate_cm*FU_PLATE) + 
                       (req_bolts-1)*min(1.2*Lc_inner*t_plate_cm*FU_PLATE, 2.4*bolt_d_cm*t_plate_cm*FU_PLATE))
            Rn_yield = 0.60 * FY_PLATE * plate_h_cm * t_plate_cm
            Rn_rup = 0.50 * FU_PLATE * (plate_h_cm*t_plate_cm - req_bolts*hole_d_cm*t_plate_cm)
            Anv = (plate_h_cm-edge_cm)*t_plate_cm - (req_bolts-0.5)*hole_d_cm*t_plate_cm
            Ant = (4.0-0.5*hole_d_cm)*t_plate_cm
            Rn_block = (0.6 * FU_PLATE * Anv) + (1.0 * FU_PLATE * Ant)
            weld_sz = max(0.6, (t_plate_cm*10 - 2)/10)
            Rn_weld = 2 * 0.707 * weld_sz * plate_h_cm * FV_WELD
            
            limit_states = {"Bolt Shear": Rn_bolt, "Bearing": Rn_bear, "Yield": Rn_yield, 
                            "Rupture": Rn_rup, "Block Shear": Rn_block, "Weld": Rn_weld}
            min_cap = min(limit_states.values())
            ratio = V_target / min_cap
            
            if ratio <= 1.00:
                is_safe = True
                governing = min(limit_states, key=limit_states.get)
                final_info = {"Bolts": req_bolts, "Plate": f"PL-{t_plate_cm*10:.0f}x100x{plate_h_cm*10:.0f}", 
                              "Weld": f"{weld_sz*10:.0f}mm", "Ratio": ratio, "Mode": governing}
            else:
                req_bolts += 1
                if req_bolts > 12 and t_plate_cm < 1.6: t_plate_cm += 0.3; req_bolts = max(2, req_bolts - 3)

        data_list.append({
            "Section": sec['name'],
            "L_Start": L_sm, "L_End": L_md,
            "V_Nominal": V_beam_nominal,
            "V_Target": V_target,
            "Bolt Spec": f"{final_info.get('Bolts')} - M{int(bolt_dia)}",
            "Plate Size": final_info.get('Plate'),
            "Weld Spec": final_info.get('Weld'),
            "D/C Ratio": final_info.get('Ratio'),
            "Governing": final_info.get('Mode')
        })

    if not data_list: return
    df = pd.DataFrame(data_list)

    # --- 2. TABLE (FIXED: Added Moment Zone Column) ---
    st.subheader("📋 Specification Table")
    
    # Create formatted string column for display
    df["Moment Zone (m)"] = df.apply(lambda x: f"{x['L_Start']:.2f} - {x['L_End']:.2f}", axis=1)

    st.dataframe(
        df[[
            "Section", "V_Nominal", "Moment Zone (m)", # <-- Added Back
            "Bolt Spec", "Plate Size", "Weld Spec", 
            "Governing", "D/C Ratio"
        ]],
        use_container_width=True,
        column_config={
            "Section": st.column_config.TextColumn("Section", width="small"),
            "V_Nominal": st.column_config.NumberColumn("Shear Cap (Vn)", format="%.0f kg"),
            "Moment Zone (m)": st.column_config.TextColumn("Moment Zone", width="medium"), # <-- Config
            "Bolt Spec": st.column_config.TextColumn("Bolts", width="small"),
            "Plate Size": st.column_config.TextColumn("Plate", width="medium"),
            "Weld Spec": st.column_config.TextColumn("Weld", width="small"),
            "Governing": st.column_config.TextColumn("Crit. Mode", width="medium"),
            "D/C Ratio": st.column_config.ProgressColumn("Ratio", format="%.2f", min_value=0, max_value=1.5),
        },
        height=400,
        hide_index=True
    )

    # --- 3. INTERACTIVE GRAPH ---
    st.divider()
    st.subheader("🔬 Interactive Analysis Graph")
    
    col_sel, _ = st.columns([1, 2])
    with col_sel:
        selected_name = st.selectbox("Select Section to Analyze:", df['Section'].unique())

    row = df[df['Section'] == selected_name].iloc[0]
    
    V_graph = row['V_Nominal']
    L_start = row['L_Start']
    L_end = row['L_End']
    
    M_derived = (L_start * V_graph) / 4 if L_start > 0 else 0
    K_derived = L_end * 8 * M_derived if M_derived > 0 else 0

    max_span = max(10, L_end * 1.5)
    spans = np.linspace(0.1, max_span, 500)
    
    ws = (2 * V_graph) / spans 
    wm = (8 * M_derived) / (spans**2) 
    wd = K_derived / (spans**3) 
    w_safe = np.minimum(np.minimum(ws, wm), wd)

    # === PLOTLY SETUP ===
    fig = go.Figure()

    # 1. Limit Lines
    fig.add_trace(go.Scatter(x=spans, y=ws, mode='lines', name='Shear Limit', line=dict(color='#9B59B6', dash='dot')))
    fig.add_trace(go.Scatter(x=spans, y=wm, mode='lines', name='Moment Limit', line=dict(color='#E74C3C', dash='dash')))
    fig.add_trace(go.Scatter(x=spans, y=wd, mode='lines', name='Deflection Limit', line=dict(color='#2ECC71', dash='dashdot')))
    
    # 2. Safe Envelope
    fig.add_trace(go.Scatter(x=spans, y=w_safe, mode='lines', name='Safe Load Envelope', line=dict(color='#2C3E50', width=4)))

    # 3. ZONES SHADING
    if L_start > 0:
        fig.add_vrect(x0=0, x1=L_start, fillcolor="#9B59B6", opacity=0.1, layer="below", line_width=0)
        fig.add_annotation(x=L_start/2, y=V_graph*0.9, text="SHEAR", showarrow=False, font=dict(color="#8E44AD", size=10, weight="bold"))

    if L_end > L_start:
        mask_moment = (spans >= L_start) & (spans <= L_end)
        fig.add_trace(go.Scatter(
            x=spans[mask_moment], y=w_safe[mask_moment], 
            mode='none', fill='tozeroy', fillcolor='rgba(231, 76, 60, 0.2)', 
            name='Moment Zone', hoverinfo='skip'
        ))
        y_anno_m = np.interp((L_start+L_end)/2, spans, w_safe) * 0.5
        fig.add_annotation(x=(L_start+L_end)/2, y=y_anno_m, text="MOMENT", showarrow=False, font=dict(color="#C0392B", size=10, weight="bold"))

    if max_span > L_end:
        mask_defl = (spans >= L_end)
        fig.add_trace(go.Scatter(
            x=spans[mask_defl], y=w_safe[mask_defl], 
            mode='none', fill='tozeroy', fillcolor='rgba(46, 204, 113, 0.2)', 
            name='Deflection Zone', hoverinfo='skip'
        ))
        x_anno_d = (L_end + max_span)/2
        y_anno_d = np.interp(x_anno_d, spans, w_safe) * 0.5
        fig.add_annotation(x=x_anno_d, y=y_anno_d, text="DEFLECTION", showarrow=False, font=dict(color="#27AE60", size=10, weight="bold"))

    # Separators
    if L_end > L_start:
        fig.add_vline(x=L_start, line_width=1, line_dash="dash", line_color="#E74C3C")
        fig.add_vline(x=L_end, line_width=1, line_dash="dash", line_color="#2ECC71")

    # 4. Axes & Layout (STRICT LOCK)
    y_max_view = np.interp(1.0, spans, w_safe) * 1.5 if np.interp(1.0, spans, w_safe) > 0 else V_graph
    
    fig.update_layout(
        title=f"Critical Limit State Diagram: {selected_name}",
        xaxis_title="<b>Span Length (m)</b>",
        yaxis_title="<b>Safe Uniform Load (kg/m)</b>",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=550,
        margin=dict(l=20, r=20, t=60, b=40)
    )
    
    fig.update_xaxes(range=[0, max_span], rangemode="tozero", constrain="domain")
    fig.update_yaxes(range=[0, y_max_view], rangemode="tozero", constrain="domain")

    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
    
    c1, c2, c3 = st.columns(3)
    c1.info(f"**Max Capacity (Vn):** {row['V_Nominal']:,.0f} kg")
    c2.info(f"**Moment Zone:** {L_start:.2f} - {L_end:.2f} m")
    c3.success(f"**Governing Mode:** {row['Governing']}")
