import streamlit as st
import pandas as pd
import numpy as np

# 1. Config & Style
st.set_page_config(page_title="Standard Load Table", layout="centered")

st.markdown("""
<style>
    /* ปรับแต่งตารางให้ดูเหมือนตารางใน Catalog เหล็ก */
    .stDataFrame { font-family: 'Arial', sans-serif; }
    div[data-testid="stMetricValue"] { font-size: 24px; }
</style>
""", unsafe_allow_html=True)

# 2. Database (H-Beam Basic Set)
def get_data():
    # Name, h, b, tw, tf, Ix, Zx
    return pd.DataFrame([
        ("H 150x75x5x7", 150, 75, 5, 7, 666, 88.8),
        ("H 200x100x5.5x8", 200, 100, 5.5, 8, 1840, 184),
        ("H 250x125x6x9", 250, 125, 6, 9, 3690, 295),
        ("H 300x150x6.5x9", 300, 150, 6.5, 9, 7210, 481),
        ("H 350x175x7x11", 350, 175, 7, 11, 13600, 775),
        ("H 400x200x8x13", 400, 200, 8, 13, 23700, 1190),
        ("H 500x200x10x16", 500, 200, 10, 16, 47800, 1910),
        ("H 600x200x11x17", 600, 200, 11, 17, 77600, 2590),
    ], columns=["Section", "h", "b", "tw", "tf", "Ix", "Zx"])

# 3. Calculation Logic (Standard Engineering Formulas)
def get_safe_load(span, h, tw, Ix, Zx):
    # Material Constants
    Fy = 2400  # ksc
    E = 2.04e6 # ksc
    L_cm = span * 100
    
    # Allowable Limits
    # 1. Shear (0.4Fy for conservative working stress or 0.6Fy? Let's use 0.6Fy standard)
    Aw = (h/10)*(tw/10)
    V_shear = 0.6 * Fy * Aw
    
    # 2. Moment (Fb = 0.6Fy) -> Simple Beam Point Load case (Worst case for reaction)
    # Note: If this is for Uniform Load, formulas change. Assuming Point Load for Reaction Capacity.
    # V = 4M/L (Point load at center)
    M_allow = 0.6 * Fy * Zx
    V_moment = (4 * M_allow) / L_cm
    
    # 3. Deflection (L/360)
    # V = (48EI * delta) / L^3 -> delta = L/360
    # V = (48 * E * Ix * (L/360)) / L^3 ... (units check: Ix cm4, L cm)
    # V = (48 * E * Ix) / (360 * L^2)
    V_defl = (48 * E * Ix) / (360 * (L_cm**2))
    
    safe_load = min(V_shear, V_moment, V_defl)
    
    # Determine what controls
    if safe_load == V_shear: control = "Shear"
    elif safe_load == V_moment: control = "Moment"
    else: control = "Deflection"
    
    return safe_load, control

# 4. App Interface
st.title("📋 Safe Load Table (Point Load)")

# Sidebar Select
df_db = get_data()
col_sel, col_info = st.columns([1, 2])
with col_sel:
    sec_name = st.selectbox("Select Section:", df_db['Section'], index=5)

# Get properties
prop = df_db[df_db['Section'] == sec_name].iloc[0]
d = prop['h']

# Generate Table Rows
rows = []
for span in range(2, 16): # 2m to 15m
    load, control = get_safe_load(span, prop['h'], prop['tw'], prop['Ix'], prop['Zx'])
    
    # Logic for Recommendation (L/d between 15 and 22 is generally good)
    ratio = (span * 1000) / d
    is_recommend = 15 <= ratio <= 22
    
    rows.append({
        "Span (m)": span,
        "Safe Load (kg)": load,
        "Control": control,
        "L/d Ratio": ratio,
        "Note": "★ Recommended" if is_recommend else ""
    })

df_result = pd.DataFrame(rows)

# 5. Display Table with Highlight
# ใช้ Pandas Styler เพื่อไฮไลท์บรรทัดที่แนะนำ
def highlight_rec(row):
    if "Recommended" in row['Note']:
        return ['background-color: #d4edda; color: black; font-weight: bold'] * len(row)
    elif "Deflection" in row['Control']:
        return ['color: #b0b0b0'] * len(row) # Grey out if deflection controls (usually too long)
    else:
        return [''] * len(row)

st.dataframe(
    df_result.style
    .apply(highlight_rec, axis=1)
    .format({"Safe Load (kg)": "{:,.0f}", "L/d Ratio": "{:.1f}"}),
    height=600,
    use_container_width=True
)

st.info("💡 **Note:** แถบสีเขียวคือช่วงความยาวที่เหมาะสม (Efficient Span) สำหรับหน้าตัดนี้")
