# report_generator.py (V21 - Professional Shop Drawing Edition)
import streamlit as st
import streamlit.components.v1 as components

def get_connection_logic(res, p):
    v_act = res.get('v_act', 0)
    h_beam = p.get('h', 0)
    
    # Structural Calculation for Bolts
    rows = max(2, int(v_act / 3800) + 1)
    pitch = 75   # mm
    edge = 40    # mm (Standard Min for M20)
    plate_h = (rows - 1) * pitch + (2 * edge)
    
    # Guardrail: Plate height should not exceed 80% of beam depth
    if plate_h > (h_beam - 60):
        rows = max(2, rows - 1)
        plate_h = (rows - 1) * pitch + (2 * edge)

    return {
        "rows": rows, "pitch": pitch, "edge": edge,
        "plate_h": int(plate_h),
        "plate_t": max(9, int(p.get('tw', 6) + 3)),
        "weld_size": 6 if p.get('tw', 6) <= 10 else 8
    }

def render_report_tab(method, is_lrfd, sec_name, steel_grade, p, res, bolt):
    conn = get_connection_logic(res, p)
    max_r = max(res.get('v_act', 0)/res.get('v_cap', 1), res.get('m_act', 0)/res.get('m_cap', 1))
    
    # --- SVG AUTO-LAYOUT ENGINE ---
    svg_w, svg_h = 320, 400
    p_h = conn['plate_h']
    offset_y = (svg_h - p_h) / 2
    
    # Bolts & Dimensions Layout
    bolt_circles = ""
    dim_lines = ""
    for i in range(conn['rows']):
        by = offset_y + conn['edge'] + (i * conn['pitch'])
        bolt_circles += f'<circle cx="140" cy="{by}" r="5" fill="none" stroke="black" stroke-width="1.5"/><path d="M{136} {by-4} L{144} {by+4} M{144} {by-4} L{136} {by+4}" stroke="black" stroke-width="1"/>'
        if i < conn['rows'] - 1:
            dim_lines += f'<line x1="180" y1="{by}" x2="180" y2="{by + conn["pitch"]}" stroke="#64748b" stroke-width="1" marker-end="url(#arrow)" marker-start="url(#arrow)"/>'
            dim_lines += f'<text x="185" y="{by + conn["pitch"]/2 + 4}" font-size="11" fill="#475569">{conn["pitch"]} mm</text>'

    html_content = f"""
    <div style="background:#f1f5f9; padding:40px; font-family:'Inter', system-ui, sans-serif;">
        <div style="max-width:900px; margin:auto; background:white; padding:50px; border-radius:4px; box-shadow:0 10px 15px -3px rgba(0,0,0,0.1);">
            
            <div style="border-bottom:3px solid #0f172a; padding-bottom:15px; margin-bottom:30px; display:flex; justify-content:space-between; align-items:center;">
                <h1 style="margin:0; font-size:24px; color:#0f172a;">STRUCTURAL DESIGN RECORD</h1>
                <div style="text-align:right; background:{'#059669' if max_r <= 1 else '#dc2626'}; color:white; padding:5px 20px; border-radius:4px; font-weight:bold;">
                    { "PASS" if max_r <= 1 else "FAIL" } ({(max_r*100):.1f}%)
                </div>
            </div>

            <div style="display:grid; grid-template-columns: 1.2fr 1fr; gap:40px; border:1px solid #e2e8f0; border-radius:8px; padding:30px; background:#fcfcfc;">
                <div style="background:white; border:1px solid #cbd5e1; padding:10px; border-radius:4px;">
                    <svg width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}">
                        <defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="5" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#64748b" /></marker></defs>
                        
                        <path d="M120 20 L300 20 M120 {svg_h-20} L300 {svg_h-20}" stroke="#94a3b8" stroke-width="2" stroke-dasharray="5,5"/>
                        <path d="M120 20 L120 {svg_h-20}" stroke="#1e293b" stroke-width="4"/> <rect x="120" y="{offset_y}" width="60" height="{p_h}" fill="#3b82f6" fill-opacity="0.1" stroke="#3b82f6" stroke-width="2" />
                        
                        <line x1="260" y1="{offset_y}" x2="260" y2="{offset_y + p_h}" stroke="#64748b" stroke-width="1" marker-end="url(#arrow)" marker-start="url(#arrow)"/>
                        <text x="265" y="{offset_y + p_h/2}" font-size="12" fill="#1e293b" font-weight="bold" transform="rotate(90 265,{offset_y + p_h/2})">PLATE HT: {p_h} mm</text>
                        
                        {bolt_circles}
                        {dim_lines}

                        <path d="M120 {offset_y + 20} L80 10 L40 10" fill="none" stroke="#ef4444" stroke-width="1.5"/>
                        <text x="40" y="5" font-size="11" fill="#ef4444" font-weight="bold">WELD {conn['weld_size']} mm (TYP)</text>
                        
                        <text x="140" y="{svg_h - 5}" font-size="12" font-weight="bold" text-anchor="middle">CONNECTION ELEVATION (N.T.S)</text>
                    </svg>
                </div>

                <div style="font-size:14px; color:#334155;">
                    <h3 style="margin-top:0; color:#1e40af; border-bottom:2px solid #1e40af; padding-bottom:5px;">CONSTRUCTION NOTES</h3>
                    <ul style="padding-left:20px; line-height:1.8;">
                        <li><b>Member:</b> {sec_name}</li>
                        <li><b>Fin Plate:</b> PL {conn['plate_t']} mm (Grade S275/SS400)</li>
                        <li><b>Bolt Group:</b> {conn['rows']} x {bolt.get('size','M20')} (Gr 8.8)</li>
                        <li><b>Standard Pitch:</b> {conn['pitch']} mm</li>
                        <li><b>Edge Distance:</b> {conn['edge']} mm (Top/Bottom)</li>
                        <li><b>Welding:</b> All-around fillet weld to support.</li>
                    </ul>
                    <div style="margin-top:30px; padding:15px; background:#fff7ed; border-left:4px solid #f59e0b; font-size:12px;">
                        <b>SENIOR ENGINEER ADVICE:</b> <br>
                        Verify that the support member (Column/Web) has sufficient thickness to receive the {conn['weld_size']}mm weld without burn-through.
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    components.html(html_content, height=1300, scrolling=True)
