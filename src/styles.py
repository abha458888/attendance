"""
src/styles.py
Custom CSS for the Registrar Attendance Management System — a "ledger / official record" look.
"""

def get_css(theme: str = "light") -> str:
    dark = theme == "dark"

    bg = "#0F1416" if dark else "#F6F3EC"
    surface = "#171E21" if dark else "#FFFFFF"
    ink = "#EAE6DA" if dark else "#20241F"
    muted = "#9AA79E" if dark else "#5B6660"
    line = "#2A3336" if dark else "#DDD6C4"
    accent = "#2F8F82"
    accent_soft = "rgba(47,143,130,0.12)"
    hero_bg = "linear-gradient(135deg, #123832 0%, #0B211D 100%)"

    return f"""
    <style>
    .stApp {{
        background: {bg};
        color: {ink};
    }}
    * {{ font-family: 'Georgia', 'Iowan Old Style', serif; }}
    .rg-mono, .rg-mono * {{ font-family: 'Courier New', monospace !important; }}

    .rg-eyebrow {{
        display: inline-block;
        font-size: 0.72rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: {accent};
        background: {accent_soft};
        padding: 4px 10px;
        border-radius: 3px;
        margin-bottom: 6px;
    }}

    .rg-muted {{ color: {muted}; }}

    .rg-hero {{
        background: {hero_bg};
        color: #F3F1E7;
        border-radius: 10px;
        padding: 40px 34px;
        margin-bottom: 22px;
        position: relative;
        border: 1px solid {line};
    }}
    .rg-hero h1 {{
        font-size: 2.3rem;
        margin: 10px 0 8px 0;
        color: #FFFFFF;
    }}
    .rg-hero p {{
        color: #C9D6D1;
        max-width: 560px;
        font-size: 1.02rem;
        line-height: 1.5;
    }}
    .rg-seal {{
        position: absolute;
        top: 28px;
        right: 32px;
        border: 2px solid #8FE0D3;
        color: #8FE0D3;
        border-radius: 50%;
        width: 84px;
        height: 84px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        font-size: 0.62rem;
        letter-spacing: 0.05em;
        font-weight: bold;
        transform: rotate(8deg);
    }}

    .rg-card {{
        background: {surface};
        border: 1px solid {line};
        border-radius: 8px;
        padding: 18px 20px;
        color: {ink};
    }}

    .rg-row {{
        background: {surface};
        border: 1px solid {line};
        border-radius: 6px;
        padding: 10px 14px;
        margin-bottom: 4px;
        color: {ink};
    }}
    .rg-id {{ color: {muted}; font-size: 0.85rem; }}

    .rg-stat {{
        background: {surface};
        border: 1px solid {line};
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }}
    .rg-stat .num {{ font-size: 1.5rem; font-weight: bold; color: {ink}; }}
    .rg-stat .lbl {{ font-size: 0.78rem; color: {muted}; text-transform: uppercase; letter-spacing: 0.06em; margin-top: 4px; }}

    .rg-badge {{
        display: inline-block;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 2px 9px;
        border-radius: 20px;
        font-family: 'Courier New', monospace;
    }}
    .rg-badge.active     {{ background: rgba(47,143,130,0.15); color: #2F8F82; }}
    .rg-badge.pending    {{ background: rgba(214,158,46,0.15); color: #B9860B; }}
    .rg-badge.suspended  {{ background: rgba(214,90,46,0.15);  color: #C24E1F; }}
    .rg-badge.rejected   {{ background: rgba(190,50,50,0.15);  color: #B23434; }}
    .rg-badge.Present    {{ background: rgba(47,143,130,0.15); color: #2F8F82; }}
    .rg-badge.Absent     {{ background: rgba(190,50,50,0.15);  color: #B23434; }}

    div[data-testid="stButton"] button {{
        border-radius: 5px;
        border: 1px solid {line};
    }}
    </style>
    """
