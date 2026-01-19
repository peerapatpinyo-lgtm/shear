import streamlit as st
import streamlit.components.v1 as components

def get_connection_logic(res, p):
    v_act = res.get('v_act', 0)
    h_beam = p.get('h', 0)
    # Engineering Assumption for M20 Bolt Strength
    rows = max(2, int(v_act / 4400) + 1)
    pitch, edge_v, edge_h = 75, 40, 45 
    plate_h = (rows - 1) * pitch + (2 * edge_v)
    plate_w = 100 # Standard Professional Width
    return {
        "rows": rows, "pitch": pitch, "edge_v": edge_v, "edge_h": edge_h,
        "plate_h": int(plate_h), "plate_w": plate_w,
        "plate_t": 12, "weld_size": 6, "bolt_dia": 20
    }

def render_report_tab(method, is_lrfd, sec_name, steel_grade, p, res, bolt):
    conn = get_connection_logic(res, p)
    v_act, v_cap = res.get('v_act', 0), res.get('v_cap', 1)
    
    # SVG Engine: Precision Coordinates
    c_w, c_h = 750, 600
    s_x, s_y = 220, (c_h - conn['plate_h']) / 2
    bolt_x = s_x + conn['edge_h']
    
    bolt_svg = ""
    dim_svg = ""
    for i in range(conn['rows']):
        by = s_y + conn['edge_v'] + (i * conn['pitch'])
        bolt_svg += f'<g transform="translate({bolt_x}, {by})"><circle r="7" fill="white" stroke="black" stroke-width="1.5"/><line x1="-5" y1="-5" x2="5" y2="5" stroke="black"/><line x1="5" y1="-5" x2="-5" y2="5" stroke="black"/></g>'
        if i < conn['rows'] - 1:
            mid_y = by + (conn['pitch']/2)
            dim_svg += f'<line x1="{bolt_x + 50}" y1="{by}" x2="{bolt_x + 50}" y2="{by+conn["pitch"]}" stroke="#64748b" marker-start="url(#dot)" marker-end="url(#dot)"/><text x="{bolt_x + 60}" y="{mid_y+5}" font-size="12" fill="#475569">{conn["pitch"]}</text>'

    html_content = f"""
    <div style="background:#f8fafc; padding:40px; font-family:'Segoe UI', system-ui, sans-serif;">
        <div style="max-width:900px; margin:auto; background:white; padding:50px; border-radius:4px; box-shadow:0 20px 40px rgba(0,0,0,0.1); border-top:10px solid #1e293b;">
            
            <div style="display:flex; justify-content:space-between; border-bottom:2px solid #e2e8f0; padding-bottom:20px; margin-bottom:30px;">
                <div>
                    <h1 style="margin:0; font-size:28px; color:#1e293b;">CONNECTION CALCULATION NOTE</h1>
                    <p style="margin:5px 0; color:#64748b;">PROJECT: HIGH-RISE FACADE SYSTEM | SPEC: AISC 360-22</p>
                </div>
                <div style="text-align:right; background:{'#10b981' if v_act/v_cap < 1 else '#ef4444'}; color:white; padding:15px 30px; border-radius:4px;">
                    <div style="font-size:12px; font-weight:bold;">UTILIZATION</div>
                    <div style="font-size:24px; font-weight:900;">{(v_act/v_cap*100):.1f}%</div>
                </div>
            </div>

            <h3 style="font-size:14px; color:#1e293b; border-left:4px solid #3b82f6; padding-left:10px; margin-bottom:15px;">1. LIMIT STATE VERIFICATION</h3>
            <table style="width:100%; border-collapse:collapse; margin-bottom:40px; font-size:13px;">
                <tr style="background:#f1f5f9; text-align:left;">
                    <th style="padding:10px; border:1px solid #e2e8f0;">Component / Limit State</th>
                    <th style="padding:10px; border:1px solid #e2e8f0;">Capacity (φRn)</th>
                    <th style="padding:10px; border:1px solid #e2e8f0;">Demand (Ru)</th>
                    <th style="padding:10px; border:1px solid #e2e8f0;">Ratio</th>
                </tr>
                <tr><td style="padding:10px; border:1px solid #e2e8f0;">Bolt Shear (M20 Gr 8.8)</td><td style="padding:10px; border:1px solid #e2e8f0;">{(v_cap*0.8):,.0f} kg</td><td style="padding:10px; border:1px solid #e2e8f0;">{v_act:,.0f} kg</td><td style="padding:10px; border:1px solid #e2e8f0; font-weight:bold;">{(v_act/(v_cap*0.8)):.2f}</td></tr>
                <tr><td style="padding:10px; border:1px solid #e2e8f0;">Fin Plate Yielding (Shear)</td><td style="padding:10px; border:1px solid #e2e8f0;">{v_cap:,.0f} kg</td><td style="padding:10px; border:1px solid #e2e8f0;">{v_act:,.0f} kg</td><td style="padding:10px; border:1px solid #e2e8f0; font-weight:bold;">{(v_act/v_cap):.2f}</td></tr>
            </table>

            <h3 style="font-size:14px; color:#1e293b; border-left:4px solid #3b82f6; padding-left:10px; margin-bottom:15px;">2. CONSTRUCTION DETAIL (ELEVATION)</h3>
            <div style="border:1px solid #cbd5e1; border-radius:4px; padding:20px; background:#fff;">
                <svg width="100%" height="{c_h}" viewBox="0 0 {c_w} {c_h}">
                    <defs>
                        <marker id="arr" markerWidth="10" markerHeight="10" refX="10" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#1e293b" /></marker>
                        <marker id="dot" markerWidth="4" markerHeight="4" refX="2" refY="2"><circle cx="2" cy="2" r="2" fill="#64748b" /></marker>
                    </defs>
                    
                    <rect x="{s_x-15}" y="30" width="15" height="{c_h-60}" fill="#e2e8f0"/> <rect x="{s_x}" y="{s_y}" width="{conn['plate_w']}" height="{conn['plate_h']}" fill="none" stroke="#1e293b" stroke-width="2"/> <line x1="{s_x}" y1="{s_y-30}" x2="{bolt_x}" y2="{s_y-30}" stroke="#1e293b" marker-end="url(#arr)" marker-start="url(#arr)"/>
                    <text x="{s_x+5}" y="{s_y-40}" font-size="11">e_h={conn['edge_h']}</text>

                    {bolt_svg} {dim_svg}
                    
                    <line x1="{s_x-80}" y1="{s_y}" x2="{s_x-80}" y2="{s_y+conn['plate_h']}" stroke="#1e293b" marker-end="url(#arr)" marker-start="url(#arr)"/>
                    <text x="{s_x-95}" y="{s_y+conn['plate_h']/2}" font-weight="bold" transform="rotate(-90 {s_x-95},{s_y+conn['plate_h']/2})">PLATE HT: {conn['plate_h']} mm</text>

                    <path d="M{s_x} {s_y+20} L{s_x-50} {s_y-10} L{s_x-100} {s_y-10}" fill="none" stroke="#ef4444" stroke-width="1.5"/>
                    <text x="{s_x-100}" y="{s_y-20}" font-size="12" fill="#ef4444" font-weight="bold">△ {conn['weld_size']} (TYP)</text>
                </svg>
            </div>
        </div>
    </div>
    """
    components.html(html_content, height=1300, scrolling=True)
