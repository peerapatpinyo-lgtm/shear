import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# 1. SETUP & STYLE
# ==========================================
st.set_page_config(page_title="ProStructure: Typical Detail Generator", layout="wide", page_icon="🏗️")

st.markdown("""
<style>
    .main-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border: 1px solid #e0e0e0;
        margin-bottom: 20px;
    }
    .metric-box {
        text-align: center;
        padding: 15px;
        background-color: #f8f9fa;
        border-radius: 8px;
        border: 1px solid #dee2e6;
    }
    .recommend-box {
        background-color: #d1e7dd;
        color: #0f5132;
        padding: 20px;
        border-radius: 8px;
        border-left: 5px solid #198754;
        font-size: 18px;
        font-weight: bold;
    }
    .warning-box {
        background-color: #fff3cd;
        color: #664d03;
        padding: 20px;
        border-radius: 8px;
        border-left: 5px solid #ffc107;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA & FUNCTIONS
# ==========================================
def get_sys_data():
    data = [
        ("H 100x50x5x7", 100, 50, 5, 7, 378, 76.5),
        ("H 150x75x5x7", 150, 75, 5, 7, 666, 88.8),
        ("H 200x100x5.5x8", 200, 100, 5.5, 8, 1840, 184),
        ("H 250x125x6x9", 250, 125, 6, 9, 3690, 295),
        ("H 300x150x6.5x9", 300, 150, 6.5, 9, 7210, 481),
        ("H 350x175x7x11", 350, 175, 7, 11, 13600, 775),
        ("H 400x200x8x13", 400, 200, 8, 13, 23700, 1190),
        ("H 450x200x9x14", 450, 200, 9, 14, 33500, 1490),
        ("H 500x200x10x16", 500, 200, 10, 16, 47800, 1910),
        ("H 600x200x11x17", 600, 200, 11, 17, 77600, 2590),
        ("H 700x300x13x24", 700, 300, 13, 24, 201000, 5760),
        ("H 800x300x14x26", 800, 300, 14, 26, 292000, 7290),
        ("H 900x300x16x28", 900, 300, 16, 28, 411000, 9140)
    ]
    return pd.DataFrame(data, columns=["Section", "h", "b", "tw", "tf", "Ix", "Zx"])

def calculate_capacity(span_m, h, tw, Ix, Zx, Fy, E_val):
    L_cm = span_m * 100
    
    # 1. Shear
    Aw = (h/10) * (tw/10)
    V_shear = 0.6 * Fy * Aw
    
    # 2. Moment (Simple Beam: M = PL/4 -> P = 4M/L)
    M_allow = 0.6 * Fy * Zx
    V_moment = (4 * M_allow) / L_cm
    
    # 3. Deflection (Simple Beam Point Load: P = 48EI d / L^3 ... simplified to equiv shear limit)
    # Using standard limit L/360
    # Delta = PL^3 / 48EI  => P = (Delta * 48EI) / L^3
    # Delta_lim = L_cm / 360
    # V_defl = ( (L_cm/360) * 48 * E_val * Ix ) / (L_cm**3)
    # V_defl = (48 * E_val * Ix) / (360 * L_cm**2) ... (unit kg)
    
    # Note: Previous formula was 384/2400 (5wL^4 vs point load). 
    # Let's use strict Point Load Center Span stiffness for conservative check:
    V_defl = (48 * E_val * Ix) / (360 * (L_cm**2)) 

    return min(V_shear, V_moment, V_defl)

# ==========================================
# 3. SIDEBAR INPUTS
# ==========================================
with st.sidebar:
    st.header("🛠️ Design Input")
    df = get_sys_data()
    sec_name = st.selectbox("Select Section", df['Section'], index=5)
    
    st.markdown("---")
    st.markdown("**Design Criteria**")
    design_load = st.number_input("Typical Point Load (kg)", value=5000, step=500, help="แรงที่คาดว่าจะเกิดขึ้นจริง (Reaction)")
    
    Fy = 2400
    E_val = 2.04e6
    
    # Get Properties
    p = df[df['Section'] == sec_name].iloc[0]
    h, tw, tf, Ix, Zx = p['h'], p['tw'], p['tf'], p['Ix'], p['Zx']

# ==========================================
# 4. MAIN CALCULATION & OPTIMIZATION
# ==========================================
st.title(f"🏗️ Typical Detail Analysis: {sec_name}")

# --- LOOP TO FIND OPTIMAL RANGE ---
spans = np.linspace(1, 20, 200) # Check 1m to 20m
results = []
valid_spans = []

for s in spans:
    cap = calculate_capacity(s, h, tw, Ix, Zx, Fy, E_val)
    util = design_load / cap
    
    # Check criteria: 50% <= Util <= 70%
    if 0.50 <= util <= 0.70:
        valid_spans.append(s)
        
    results.append({
        "span": s,
        "capacity": cap,
        "utilization": util * 100, # Convert to %
        "L_d": s * 1000 / h
    })

df_res = pd.DataFrame(results)

# --- DETERMINE RECOMMENDATION ---
if len(valid_spans) > 0:
    min_s = min(valid_spans)
    max_s = max(valid_spans)
    status_html = f"""
    <div class="recommend-box">
        ✅ RECOMMENDED SPAN: {min_s:.1f} - {max_s:.1f} m<br>
        <span style="font-size:14px; font-weight:normal;">
        (ที่ Load {design_load:,.0f} kg จะใช้ประสิทธิภาพหน้าตัด 50-70%)
        </span>
    </div>
    """
else:
    # Check why failed
    min_util = df_res['utilization'].min()
    if min_util > 70:
        status_html = f"""
        <div class="warning-box">
            ⚠️ <b>Section Too Small!</b><br>
            ที่ Load {design_load:,.0f} kg หน้าตัดนี้รับแรงเกิน 70% ตลอดทุกระยะ<br>
            แนะนำให้: <b>เพิ่มขนาดหน้าตัด</b>
        </div>
        """
    else:
        status_html = f"""
        <div class="warning-box">
            ⚠️ <b>Section Too Big!</b><br>
            ที่ Load {design_load:,.0f} kg หน้าตัดนี้ใช้น้อยกว่า 50% (Overdesign)<br>
            แนะนำให้: <b>ลดขนาดหน้าตัด</b> หรือ <b>เพิ่มระยะ Span</b>
        </div>
        """

st.markdown(status_html, unsafe_allow_html=True)

# ==========================================
# 5. VISUALIZATION (THE "CLEAR" GRAPHS)
# ==========================================
st.markdown("### 📊 Analysis Charts")

tab1, tab2 = st.tabs(["🎯 % Utilization Graph (Target)", "📈 Capacity Curve"])

with tab1:
    # Graph showing Utilization % vs Span
    # This answers "Write graph as %"
    fig_util = go.Figure()
    
    # Plot the Utilization Curve
    fig_util.add_trace(go.Scatter(
        x=df_res['span'], 
        y=df_res['utilization'],
        mode='lines',
        name='Actual Utilization',
        line=dict(color='#154360', width=3)
    ))
    
    # Add Green Zone (50-70%)
    fig_util.add_shape(type="rect",
        x0=df_res['span'].min(), y0=50, x1=df_res['span'].max(), y1=70,
        fillcolor="green", opacity=0.15, layer="below", line_width=0,
    )
    
    # Add Limit Line (100%)
    fig_util.add_shape(type="line",
        x0=df_res['span'].min(), y0=100, x1=df_res['span'].max(), y1=100,
        line=dict(color="red", width=2, dash="dash"),
    )
    fig_util.add_annotation(x=df_res['span'].max(), y=100, text="Max Capacity (100%)", showarrow=False, yshift=10)
    fig_util.add_annotation(x=df_res['span'].max()/2, y=60, text="TARGET ZONE (50-70%)", showarrow=False, font=dict(color="green", size=14, weight="bold"))

    fig_util.update_layout(
        title=f"Utilization (%) for Load = {design_load:,.0f} kg",
        xaxis_title="Span Length (m)",
        yaxis_title="% Utilization",
        yaxis=dict(range=[0, 120]),
        height=450,
        hovermode="x unified"
    )
    st.plotly_chart(fig_util, use_container_width=True)
    
    st.caption("กราฟนี้แสดงให้เห็นว่า ถ้าคุณใช้หน้าตัดนี้รับแรงตามที่กำหนด ค่า % การใช้งานจะเปลี่ยนไปตามความยาวคานอย่างไร (ช่วงสีเขียวคือช่วงที่เหมาะสม)")

with tab2:
    # Standard Capacity Curve
    fig_cap = go.Figure()
    
    fig_cap.add_trace(go.Scatter(x=df_res['span'], y=df_res['capacity'], name='Max Capacity', line=dict(color='black', width=2)))
    
    # Plot the Design Load Line
    fig_cap.add_trace(go.Scatter(
        x=df_res['span'], 
        y=[design_load]*len(df_res), 
        name='Your Load', 
        line=dict(color='red', dash='dash')
    ))
    
    fig_cap.update_layout(
        title="Load (kg) vs Capacity",
        xaxis_title="Span Length (m)",
        yaxis_title="Load (kg)",
        height=450
    )
    st.plotly_chart(fig_cap, use_container_width=True)

# ==========================================
# 6. TYPICAL DETAIL SUMMARY
# ==========================================
st.markdown("---")
st.markdown("""<div class="topic-header">📝 TYPICAL DETAIL SPECIFICATION</div>""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("**1. Selected Section**")
    st.markdown(f"### {sec_name}")
    st.write(f"Depth: {h} mm")
    st.write(f"Weight: Est. {p['h']*0.1:.1f} kg/m") # Simplified estimation

with c2:
    st.markdown(f"**2. Design Load**")
    st.markdown(f"### {design_load:,.0f} kg")
    st.write("(Point Load / Reaction)")

with c3:
    st.markdown("**3. Approved Span Range**")
    if len(valid_spans) > 0:
        st.markdown(f"<h3 style='color:green'>{min_s:.1f} m  —  {max_s:.1f} m</h3>", unsafe_allow_html=True)
        st.write("Criteria: 50% - 70% Usage")
    else:
        st.markdown("<h3 style='color:red'>N/A</h3>", unsafe_allow_html=True)
        st.write("Please adjust Load or Section")

st.markdown("""
<div class="main-card" style="margin-top:20px;">
    <b>Engineering Note for Detailer:</b><br>
    <ul>
        <li>ใช้สำหรับทำแบบ Typical Detail แนะนำให้ระบุช่วงความยาวตามที่คำนวณได้ด้านบน</li>
        <li>หากความยาวเกินกว่านี้ (Utilization > 70%) ควรขยับไปใช้หน้าตัดถัดไป</li>
        <li>หากความยาวสั้นกว่านี้ (Utilization < 50%) หน้าตัดจะใหญ่เกินความจำเป็น (Overdesign)</li>
    </ul>
</div>
""", unsafe_allow_html=True)
