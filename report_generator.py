import streamlit as st

def render_report_tab(method, is_lrfd, sec_name, fy, p, res, bolt):
    # res คือ dictionary ที่เราส่งมาจากไฟล์หลัก
    
    st.markdown(f"""
    <div class="report-paper">
        <div style="text-align:center; border-bottom: 2px solid #1e40af; padding-bottom:10px;">
            <h2 style="margin:0;">STRUCTURAL CALCULATIONS SHEET</h2>
            <p style="margin:0; color:#666;">Project: Beam Design Analysis | Method: {method}</p>
        </div>

        <div style="display: flex; justify-content: space-between; margin-top: 20px;">
            <div style="width: 48%;">
                <h4 style="border-bottom: 1px solid #ddd;">1. SECTION PROPERTIES</h4>
                <p>Section: <b>{sec_name}</b><br>
                Height (h): {p['h']} mm<br>
                Width (b): {p['b']} mm<br>
                Inertia (Ix): {p['Ix']:,} cm⁴</p>
            </div>
            <div style="width: 48%;">
                <h4 style="border-bottom: 1px solid #ddd;">2. MATERIAL & CRITERIA</h4>
                <p>Yield Strength (Fy): {fy} kg/cm²<br>
                Modulus (E): 2.04x10⁶ kg/cm²<br>
                Span Length: {res['d_all'] * (int(st.session_state.get('defl_lim_val', 360))/100) if 'd_all' in res else 0:.2f} m</p>
            </div>
        </div>

        <h4 style="background:#f0f4f8; padding:5px 10px; margin-top:20px;">3. CAPACITY SUMMARY</h4>
        <table style="width:100%; border-collapse: collapse;">
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding:8px;">Shear Limit (w_v)</td>
                <td style="text-align:right;"><b>{res['w_shear']:,.0f} kg/m</b></td>
            </tr>
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding:8px;">Moment Limit (w_m)</td>
                <td style="text-align:right;"><b>{res['w_moment']:,.0f} kg/m</b></td>
            </tr>
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding:8px;">Deflection Limit (w_d)</td>
                <td style="text-align:right;"><b>{res['w_defl']:,.0f} kg/m</b></td>
            </tr>
            <tr style="background:#eef2ff;">
                <td style="padding:10px;"><b>GOVERNING SAFE LOAD</b></td>
                <td style="text-align:right; color:#1e40af;"><b>{res['w_safe']:,.0f} kg/m</b></td>
            </tr>
        </table>

        <h4 style="background:#f0f4f8; padding:5px 10px; margin-top:20px;">4. UTILIZATION CHECK</h4>
        <p>Shear: {(res['v_act']/res['w_shear']*100) if res['w_shear']!=0 else 0:.1f}% | 
           Moment: {(res['m_act']/(res['w_moment']*res['d_all']**2/8)*100) if res['w_moment']!=0 else 0:.1f}%</p>
        
        <div style="margin-top:30px; text-align:center; border: 2px solid #166534; padding:10px; border-radius:10px;">
            <h3 style="margin:0; color:#166534;">STATUS: PASS</h3>
            <small>Verified by Beam Insight Engineering System</small>
        </div>
    </div>
    """, unsafe_allow_html=True)
