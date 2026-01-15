# app.py (Final Integration V14)
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- IMPORT MODULES ---
try:
    import data_utils as db        # <--- New File
    import connection_design as conn
    import calculation_report as rep # <--- The Report Module
except ImportError:
    st.error("⚠️ Error: Missing required modules (data_utils, connection_design, calculation_report).")

st.set_page_config(page_title="Beam Insight V14", layout="wide", page_icon="🏗️")

# ... (Setup CSS & Styles - Same as before) ...

# ==========================================
# 2. INPUT SECTION (Using data_utils)
# ==========================================
with st.sidebar:
    st.title("🏗️ Beam Insight V14")
    
    method = st.radio("Method", ["ASD", "LRFD"])
    is_lrfd = "LRFD" in method
    
    # Project Info for Report
    with st.expander("📋 Project Info (For Report)"):
        proj_name = st.text_input("Project Name", "Warehouse A")
        eng_name = st.text_input("Engineer", "John Doe")

    sec_name = st.selectbox("Section", list(db.STEEL_DB.keys()), index=11)
    # ... (Span, Deflection inputs same as before) ...
    
    conn_type = st.selectbox("Connection Type", [
        "Fin Plate (Single Shear)", 
        "End Plate (Single Shear)", 
        "Double Angle (Double Shear)"
    ])
    
    design_mode = st.radio("Load Mode", ["Actual Load", "Fixed %"])
    target_pct = st.slider("Target %", 50, 100, 75) if design_mode == "Fixed %" else None

# ==========================================
# 3. BEAM CALCULATION
# ==========================================
p = db.STEEL_DB[sec_name] # Use DB from data_utils
# ... (Beam calculation logic - Ix, Zx, M_cap, V_cap ...) ...
# ... (Calculate v_act, m_act, d_act ...) ...

# Mocking beam results for cleaner integration
beam_res = {
    'w_safe': user_safe_load, 'v_act': v_act, 'v_cap': V_cap, 'v_ratio': v_act/V_cap,
    'm_act': m_act, 'm_cap': M_cap/100, 'm_ratio': m_act/(M_cap/100),
    'd_act': d_act, 'd_all': d_all, 'd_ratio': d_act/d_all,
    'pass': (v_act/V_cap <= 1) and (m_act/(M_cap/100) <= 1) and (d_act/d_all <= 1)
}

# ==========================================
# 4. TABS & INTEGRATION
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Beam", "🔩 Connection", "💾 Table", "📝 Report"])

with tab1:
    # ... (Render Beam Charts) ...
    st.info("Beam Analysis Complete. See details in Report tab.")

with tab2:
    # Call Connection Design & Get Full Result
    conn_result = conn.render_connection_tab(
        V_design=V_design, 
        method=method, 
        is_lrfd=is_lrfd, 
        section_data=p, 
        conn_type=conn_type
    )

with tab3:
    # ... (Load Table) ...
    st.dataframe(pd.DataFrame({"Span": [2,4,6], "Load": [1000, 500, 250]})) # Placeholder logic

with tab4:
    # ✅ เรียกใช้ calculation_report.py
    if conn_result:
        project_info = {
            'name': proj_name, 'eng': eng_name, 
            'sec': sec_name, 'method': method
        }
        rep.render_report_tab(project_info, beam_res, conn_result)
    else:
        st.warning("Please configure connection in Tab 2 first.")
