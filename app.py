import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ==========================================
# 1. SETUP & STYLE
# ==========================================
st.set_page_config(page_title="Beam Insight V12", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=Roboto+Mono:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
    
    .detail-card {
        background: white; border-radius: 12px; padding: 20px;
        border: 1px solid #e5e7eb; border-top: 6px solid #2563eb;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 20px;
    }
    .status-badge {
        padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 12px;
        float: right; text-transform: uppercase;
    }
    .pass { background-color: #dcfce7; color: #166534; }
    .fail { background-color: #fee2e2; color: #991b1b; }

    .highlight-card { 
        background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%);
        padding: 25px; border-radius: 20px; border-left: 8px solid #2563eb; 
        box-shadow: 0 10px 30px rgba(37, 99, 235, 0.08); margin-bottom: 25px; border: 1px solid #e5e7eb;
    }
    .big-num { color: #1e40af; font-size: 42px; font-weight: 800; font-family: 'Roboto Mono', monospace; }

    /* --- Report Style --- */
    .report-paper {
        background: white; padding: 40px; border: 1px solid #ddd;
        box-shadow: 0 0 15px rgba(0,0,0,0.1); color: #333;
        max-width: 850px; margin: auto;
    }
    .report-header { 
        border-bottom: 3px solid #1e40af; padding-bottom: 10px; margin-bottom: 20px;
        display: flex; justify-content: space-between; align-items: flex-end;
    }
    .report-section { background: #f8fafc; padding: 10px; font-weight: 700; margin: 15px 0; border-left: 4px solid #1e40af; }
    .report-row { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dashed #eee; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA & SIDEBAR
# ==========================================
steel_db = {
    "H 150x150x7x10":   {"h": 150, "b": 150, "tw": 7,   "tf": 10,  "Ix": 1640,   "Zx": 219,   "w": 31.5},
    "H 200x200x8x12":   {"h": 200, "b": 200, "tw": 8,   "tf": 12,  "Ix": 4720,   "Zx": 472,   "w": 49.9},
    "H 300x150x6.5x9":  {"h": 300, "b": 150, "tw": 6.5, "tf": 9,   "Ix": 7210,   "Zx": 481,   "w": 36.7},
    "H 400x200x8x13":   {"h": 400, "b": 200, "tw": 8,   "tf": 13,  "Ix": 23700,  "Zx": 1190,  "w": 66.0},
    "H 500x200x10x16":  {"h": 500, "b": 200, "tw": 10,  "tf": 16,  "Ix": 47800,  "Zx": 1910,  "w": 89.6},
}

with st.sidebar:
    st.title("🏗️ Beam Insight V12")
    method = st.radio("Design Method", ["ASD", "LRFD"])
    is_lrfd = method == "LRFD"
    sec_name = st.selectbox("Steel Section", list(steel_db.keys()), index=2)
    user_span = st.number_input("Span Length (m)", 1.0, 15.0, 6.0, 0.5)
    fy = st.number_input("Fy (kg/cm²)", 2400)
    defl_ratio = st.selectbox("Deflection Limit", ["L/300", "L/360", "L/400"], index=1)
    defl_lim_val = int(defl_ratio.split("/")[1])
    E_mod = 2.04e6 

# ==========================================
# 3. CALCULATIONS
# ==========================================
p = steel_db[sec_name]
Aw = (p['h']/10) * (p['tw']/10) 
Ix, Zx = p['Ix'], p['Zx']

if is_lrfd:
    M_cap, V_cap = 0.9 * fy * Zx, 1.0 * 0.6 * fy * Aw
    label_w = "Wu (Factored)"
else:
    M_cap, V_cap = 0.6 * fy * Zx, 0.4 * fy * Aw
    label_w = "w (Allowable)"

def get_cap(L_m):
    L_cm = L_m * 100
    wv = (2 * V_cap / L_cm) * 100
    wm = (8 * M_cap / (L_cm**2)) * 100
    wd = ((L_cm/defl_lim_val) * 384 * E_mod * Ix) / (5 * (L_cm**4)) * 100
    w_gov = min(wv, wm, wd)
    cause = "Shear" if w_gov == wv else ("Moment" if w_gov == wm else "Deflection")
    return wv, wm, wd, w_gov, cause

w_v, w_m, w_d, w_safe, cause_gov = get_cap(user_span)

# For Verification
V_act = w_safe * user_span / 2
M_act = w_safe * user_span**2 / 8
d_all = (user_span*100) / defl_lim_val
d_act = (5 * (w_safe/100) * ((user_span*100)**4)) / (384 * E_mod * Ix)

# ==========================================
# 4. TAB 1: ANALYSIS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Beam Analysis", "🔩 Connection", "💾 Load Table", "📝 Report"])

with tab1:
    st.markdown(f"""<div class="highlight-card"><div style="display: flex; justify-content: space-between;">
        <div><span style="color:#6b7280;">Max {label_w}</span><br><span class="big-num">{w_safe:,.0f}</span> kg/m</div>
        <div style="text-align:right;"><span style="color:#6b7280;">Limit by</span><br><span style="font-size:24px; font-weight:800; color:#1e40af;">{cause_gov.upper()}</span></div>
    </div></div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="detail-card"><h4>Shear Check</h4><hr>Ratio: {V_act/V_cap:.3f}<br>w_limit: <b>{w_v:,.0f}</b></div>', unsafe_allow_html=True)
        with st.expander("Show Calculation"):
            st.latex(fr"w_{{v}} = \frac{{2 \cdot {V_cap:,.0f}}}{{{user_span*100}}} \cdot 100 = {w_v:,.0f}")
    with c2:
        st.markdown(f'<div class="detail-card"><h4>Moment Check</h4><hr>Ratio: {M_act/(M_cap/100):.3f}<br>w_limit: <b>{w_m:,.0f}</b></div>', unsafe_allow_html=True)
        with st.expander("Show Calculation"):
            st.latex(fr"w_{{m}} = \frac{{8 \cdot {M_cap:,.0f}}}{{{user_span*100}^2}} \cdot 100 = {w_m:,.0f}")
    with c3:
        st.markdown(f'<div class="detail-card"><h4>Deflection Check</h4><hr>Ratio: {d_act/d_all:.3f}<br>w_limit: <b>{w_d:,.0f}</b></div>', unsafe_allow_html=True)
        with st.expander("Show Calculation"):
            st.latex(fr"w_{{d}} = \frac{{384 E I \Delta_{{all}}}}{{5 L^4}} = {w_d:,.0f}")

    # --- Graph with Marker ---
    spans = np.linspace(2, 12, 100)
    data = [get_cap(s) for s in spans]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spans, y=[d[3] for d in data], name='Capacity Envelope', fill='tozeroy', line=dict(color='#1e40af', width=3)))
    # ใส่จุดตำแหน่งปัจจุบัน
    fig.add_trace(go.Scatter(x=[user_span], y=[w_safe], mode='markers+text', name='Design Point', 
                             text=[f"  {w_safe:,.0f} kg/m"], textposition="top right",
                             marker=dict(color='red', size=12, symbol='diamond')))
    
    fig.update_layout(title="Span vs Capacity Envelope", hovermode="x", height=400, plot_bgcolor='white')
    st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 5. TAB 4: PROFESSIONAL REPORT
# ==========================================
with tab4:
    st.markdown(f"""
    <div class="report-paper">
        <div class="report-header">
            <div><h2 style="margin:0; color:#1e40af;">BEAM DESIGN REPORT</h2><small>Structural Analysis & Design Software</small></div>
            <div style="text-align:right;">Date: 15/01/2026<br>Method: <b>{method}</b></div>
        </div>
        
        <div class="report-section">1. SECTION PROPERTIES: {sec_name}</div>
        <div class="report-row"><span>Depth (h)</span> <b>{p['h']} mm</b></div>
        <div class="report-row"><span>Width (b)</span> <b>{p['b']} mm</b></div>
        <div class="report-row"><span>Web/Flange Thickness</span> <b>{p['tw']} / {p['tf']} mm</b></div>
        <div class="report-row"><span>Moment of Inertia (Ix)</span> <b>{p['Ix']:,.0f} cm⁴</b></div>
        
        <div class="report-section">2. DESIGN CRITERIA</div>
        <div class="report-row"><span>Span Length</span> <b>{user_span:.2f} m</b></div>
        <div class="report-row"><span>Yield Strength (Fy)</span> <b>{fy} kg/cm²</b></div>
        <div class="report-row"><span>Deflection Limit</span> <b>{defl_ratio} ({d_all:.2f} cm)</b></div>
        
        <div class="report-section">3. CAPACITY SUMMARY</div>
        <div class="report-row"><span>Shear Capacity (V_cap)</span> <b>{V_cap:,.0f} kg</b></div>
        <div class="report-row"><span>Moment Capacity (M_cap)</span> <b>{M_cap:,.0f} kg.cm</b></div>
        <div class="report-row" style="background:#eef2ff;"><span>GOVERNING SAFE LOAD</span> <b style="color:#1e40af; font-size:18px;">{w_safe:,.0f} kg/m</b></div>
        
        <div class="report-section">4. VERIFICATION</div>
        <div class="report-row"><span>Actual Shear (V_act)</span> <span>{V_act:,.0f} / {V_cap:,.0f} ➡️ <b>{(V_act/V_cap)*100:.1f}%</b></span></div>
        <div class="report-row"><span>Actual Moment (M_act)</span> <span>{M_act:,.0f} / {M_cap/100:,.0f} ➡️ <b>{(M_act/(M_cap/100))*100:.1f}%</b></span></div>
        <div class="report-row"><span>Actual Deflection (Δ)</span> <span>{d_act:.3f} / {d_all:.3f} ➡️ <b>{(d_act/d_all)*100:.1f}%</b></span></div>
        
        <div style="margin-top:30px; border-top: 2px solid #eee; padding-top:10px; text-align:center;">
            <span style="color:green; font-weight:bold; font-size:20px;">✅ STATUS: DESIGN PASS</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.button("🖨️ Print Report (PDF)", on_click=lambda: st.toast("Printing..."))
