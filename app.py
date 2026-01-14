import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ==========================================
# 1. CORE CALCULATION ENGINE (SOLVER & DESIGN)
# ==========================================

def get_rebar_area(dia, count):
    return count * (np.pi * (dia/2)**2)

def get_phi_Mn_single(d, b, As, fc, fy):
    """Calculate Moment Capacity (Single Reinforced)"""
    a = (As * fy) / (0.85 * fc * b)
    beta1 = 0.85 if fc <= 30 else max(0.65, 0.85 - 0.05 * (fc - 30) / 7)
    c = a / beta1
    epsilon_t = 0.003 * (d - c) / c
    phi = 0.9 if epsilon_t >= 0.005 else 0.65 + (epsilon_t - 0.002) * (250/3)
    Mn = As * fy * (d - a/2)
    return phi * Mn / 1e6  # kNm

def solve_simple_beam_fem(L, loads, E=25e9, I=0.001):
    """
    Simplified FEM solver for single span (Demonstration Purpose)
    For Multi-span/Complex loads, a full matrix solver is usually required.
    Here we simulate results for a simple supported beam to make the app runnable.
    """
    x = np.linspace(0, L, 100)
    
    # Superposition of loads
    M = np.zeros_like(x)
    V = np.zeros_like(x)
    D = np.zeros_like(x)
    
    for load in loads:
        mag = load['mag']
        if load['type'] == 'U': # UDL
            # Simple beam formula: M = wLx/2 - wx^2/2
            w = mag
            M += (w * L * x / 2) - (w * x**2 / 2)
            V += (w * L / 2) - (w * x)
            # Deflection: 5wL^4/384EI (approx shape)
            D += -(w * x * (L**3 - 2*L*x**2 + x**3)) / (24 * E * I)
            
    return x, M, V, D

# ==========================================
# 2. UI & PLOTTING FUNCTIONS
# ==========================================

def plot_section(b, h, cover, top_n, top_d, bot_n, bot_d, stir_d, stir_s):
    fig, ax = plt.subplots(figsize=(4, 5))
    # Concrete
    rect = patches.Rectangle((0, 0), b, h, linewidth=2, edgecolor='black', facecolor='#f0f2f6')
    ax.add_patch(rect)
    # Stirrup
    ax.add_patch(patches.Rectangle((cover, cover), b-2*cover, h-2*cover, 
                                   linewidth=1, edgecolor='blue', facecolor='none', linestyle='--'))
    
    # Rebar Circles
    def draw_bars(n, d_mm, y_pos, color):
        if n > 0:
            start = cover + d_mm/2
            end = b - cover - d_mm/2
            gap = (end - start) / (n - 1) if n > 1 else 0
            for i in range(n):
                cx = start + i * gap if n > 1 else b/2
                ax.add_patch(patches.Circle((cx, y_pos), d_mm/2, color=color))

    draw_bars(top_n, top_d, h - cover - top_d/2, 'red')
    draw_bars(bot_n, bot_d, cover + bot_d/2, 'green')
    
    ax.set_xlim(-50, b+50)
    ax.set_ylim(-50, h+50)
    ax.axis('off')
    ax.set_title(f"Section {int(b)}x{int(h)} mm", fontsize=10)
    return fig

# ==========================================
# 3. MAIN APP STRUCTURE
# ==========================================

st.set_page_config(page_title="RC Beam Design (Single File)", layout="wide")
st.title("🏗️ RC Beam Design Pro (Standalone)")

# --- SIDEBAR INPUTS ---
with st.sidebar:
    st.header("1. Material & Section")
    fc = st.number_input("f'c (MPa)", value=25.0)
    fy = st.number_input("fy (MPa)", value=400.0)
    
    # Smart Unit Logic
    raw_b = st.number_input("Width b (input m or mm)", value=0.25)
    raw_h = st.number_input("Depth h (input m or mm)", value=0.50)
    
    # Auto-convert to mm if user inputs meters
    b_mm = raw_b * 1000 if raw_b < 10 else raw_b
    h_mm = raw_h * 1000 if raw_h < 10 else raw_h
    
    if raw_b < 10: st.caption(f"✅ Converted b to {b_mm:.0f} mm")
    if raw_h < 10: st.caption(f"✅ Converted h to {h_mm:.0f} mm")

    st.header("2. Geometry & Loads")
    L_span = st.number_input("Span Length (m)", value=5.0)
    
    include_sw = st.checkbox("Include Self-weight", value=True)
    sw_load = (b_mm/1000) * (h_mm/1000) * 24000 # N/m
    
    st.subheader("Live Loads")
    ll_val = st.number_input("Uniform LL (kN/m)", value=10.0) * 1000 # convert to N/m

# --- MAIN LOGIC ---

# 1. Calculate Loads
total_load_factored = 0
loads_list = []

# DL (Self weight + Superimposed?) - For simplicity using 1.4DL + 1.7LL
w_u = 0
if include_sw:
    w_u += 1.4 * sw_load
    loads_list.append({'type': 'U', 'mag': 1.4 * sw_load})

w_u += 1.7 * ll_val
loads_list.append({'type': 'U', 'mag': 1.7 * ll_val})

# 2. Run Simple Solver (Calculates M, V diagrams)
# Note: This uses the simple solver function defined above
x, M, V, D = solve_simple_beam_fem(L_span, [{'type': 'U', 'mag': w_u}])

# Get Max Design Values
Mu_max = np.max(M) / 1e6 # kNm
Vu_max = np.max(np.abs(V)) / 1000 # kN

# --- TABS ---
tab1, tab2 = st.tabs(["📊 Analysis Results", "📝 Concrete Design"])

with tab1:
    c1, c2, c3 = st.columns(3)
    c1.metric("Factored Load (Wu)", f"{w_u/1000:.2f} kN/m")
    c2.metric("Max Moment (Mu)", f"{Mu_max:.2f} kNm")
    c3.metric("Max Shear (Vu)", f"{Vu_max:.2f} kN")
    
    st.subheader("Bending Moment Diagram (BMD)")
    st.line_chart(pd.DataFrame({'Moment (Nm)': M}, index=x))
    
    st.subheader("Shear Force Diagram (SFD)")
    st.line_chart(pd.DataFrame({'Shear (N)': V}, index=x))

with tab2:
    st.write(f"**Design Forces:** Mu = {Mu_max:.2f} kNm, Vu = {Vu_max:.2f} kN")
    
    col_d1, col_d2 = st.columns([2, 1])
    
    with col_d1:
        st.subheader("Reinforcement Selection")
        cover = st.slider("Cover (mm)", 20, 50, 25)
        
        # Flexure Design
        st.markdown("---")
        st.markdown("**Bottom Bars (Main Steel):**")
        c_b1, c_b2 = st.columns(2)
        dia_bot = c_b1.selectbox("Diameter", [12, 16, 20, 25], index=1)
        num_bot = c_b2.number_input("Number of Bars", 2, 10, 3)
        
        area_bot = get_rebar_area(dia_bot, num_bot)
        d_eff = h_mm - cover - 9 - dia_bot/2
        phi_Mn = get_phi_Mn_single(d_eff, b_mm, area_bot, fc, fy)
        
        # Check Flexure
        if phi_Mn >= Mu_max:
            st.success(f"✅ Flexure OK: Capacity {phi_Mn:.2f} > {Mu_max:.2f} kNm")
        else:
            st.error(f"❌ Flexure Fail: Capacity {phi_Mn:.2f} < {Mu_max:.2f} kNm")
            
        # Shear Design
        st.markdown("---")
        st.markdown("**Stirrups (Shear):**")
        c_s1, c_s2 = st.columns(2)
        dia_stir = c_s1.selectbox("Stirrup Dia", [6, 9], index=0)
        spacing = c_s2.number_input("Spacing (mm)", 50, 300, 150)
        
        # Simple Vc + Vs check
        Vc = 0.17 * np.sqrt(fc) * b_mm * d_eff / 1000 # kN
        Av = 2 * (np.pi * (dia_stir/2)**2)
        Vs = (Av * fy * d_eff / spacing) / 1000 # kN
        phi_Vn = 0.85 * (Vc + Vs)
        
        if phi_Vn >= Vu_max:
             st.success(f"✅ Shear OK: Capacity {phi_Vn:.2f} > {Vu_max:.2f} kN")
        else:
             st.error(f"❌ Shear Fail: Capacity {phi_Vn:.2f} < {Vu_max:.2f} kN")
             
    with col_d2:
        st.subheader("Section Preview")
        fig = plot_section(b_mm, h_mm, cover, 2, 12, num_bot, dia_bot, dia_stir, spacing)
        st.pyplot(fig)

    # BOQ
    st.markdown("---")
    st.subheader("💰 Basic BOQ (Estimation)")
    vol_conc = (b_mm/1000) * (h_mm/1000) * L_span
    weight_steel = (get_rebar_area(dia_bot, num_bot) / 100 * 0.785) * L_span # Approx weight
    
    st.info(f"""
    * **Concrete Volume:** {vol_conc:.2f} m³
    * **Rebar Weight (Approx):** {weight_steel:.2f} kg
    """)
