import streamlit as st

def render_report_tab(method, is_lrfd, sec_name, fy, section_data, caps, bolt_info):
    """
    ฟังก์ชันสำหรับแสดงผล Tab Calculation Report
    """
    # Unpack ข้อมูล
    p = section_data
    M_cap, V_cap = caps['M_cap'], caps['V_cap']
    Aw = (p['h']/10) * (p['tw']/10)
    Zx = p['Zx']
    Ix = p['Ix']
    
    bolt_size = bolt_info['size']
    v_bolt = bolt_info['capacity']

    # เริ่มเขียน HTML
    st.markdown('<div class="report-paper">', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:right; color:#999;">METHOD: {method}</div>', unsafe_allow_html=True)
    
    # Section 1: Properties
    st.markdown('<div class="report-header">1. Section & Properties</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="report-line">Section: {sec_name} (Fy={fy} ksc)</div>
    <div class="report-line">Aw = {Aw:.2f} cm2, Zx = {Zx} cm3, Ix = {Ix} cm4</div>
    """, unsafe_allow_html=True)
    
    # Section 2: Beam Capacity
    st.markdown(f'<div class="report-header">2. Capacity Calculation ({method})</div>', unsafe_allow_html=True)
    if is_lrfd:
        # LRFD Format
        st.markdown(f"""
        <div class="report-line"><b>Moment (Phi Mn):</b></div>
        <div class="report-line">Phi = 0.90 (Flexure)</div>
        <div class="report-line">Phi Mn = 0.90 * Fy * Zx = 0.9 * {fy} * {Zx} = <b>{M_cap:,.0f} kg.cm</b></div>
        <br>
        <div class="report-line"><b>Shear (Phi Vn):</b></div>
        <div class="report-line">Phi = 1.00 (Shear), Vn = 0.6 Fy Aw</div>
        <div class="report-line">Phi Vn = 1.0 * 0.6 * {fy} * {Aw:.2f} = <b>{V_cap:,.0f} kg</b></div>
        """, unsafe_allow_html=True)
    else:
        # ASD Format
        st.markdown(f"""
        <div class="report-line"><b>Moment (Allowable):</b></div>
        <div class="report-line">M_all = 0.60 * Fy * Zx = 0.6 * {fy} * {Zx} = <b>{M_cap:,.0f} kg.cm</b></div>
        <br>
        <div class="report-line"><b>Shear (Allowable):</b></div>
        <div class="report-line">V_all = 0.40 * Fy * Aw = 0.4 * {fy} * {Aw:.2f} = <b>{V_cap:,.0f} kg</b></div>
        """, unsafe_allow_html=True)
        
    # Section 3: Bolt Capacity
    st.markdown('<div class="report-header">3. Bolt Capacity</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="report-line">Bolt: {bolt_size} (A325/Gr.8.8 approx)</div>
    <div class="report-line">Capacity per bolt = <b>{v_bolt:,.0f} kg</b> ({'Phi Rn' if is_lrfd else 'Rn/Omega'})</div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
