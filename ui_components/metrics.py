"""
Enhanced metric components with visual hierarchy and color coding.
"""

import streamlit as st

# Color system based on metric type
METRIC_COLORS = {
    "gain": {
        "bg": "linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(5, 150, 105, 0.25))",
        "border": "#10b981",
        "icon_color": "#10b981",
        "text_color": "#10b981"
    },
    "risk": {
        "bg": "linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(220, 38, 38, 0.25))",
        "border": "#ef4444",
        "icon_color": "#ef4444",
        "text_color": "#ef4444"
    },
    "analytics": {
        "bg": "linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(37, 99, 235, 0.25))",
        "border": "#3b82f6",
        "icon_color": "#3b82f6",
        "text_color": "#3b82f6"
    },
    "goal": {
        "bg": "linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(217, 119, 6, 0.25))",
        "border": "#f59e0b",
        "icon_color": "#f59e0b",
        "text_color": "#f59e0b"
    },
    "neutral": {
        "bg": "linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(124, 58, 237, 0.25))",
        "border": "#8b5cf6",
        "icon_color": "#8b5cf6",
        "text_color": "#8b5cf6"
    }
}

def render_metric_card(label, value, delta=None, kind="neutral", help_text=None):
    """
    Render an enhanced metric card with colored background and glassmorphism.
    
    Args:
        label: Metric label/title
        value: Main value to display
        delta: Optional delta/change indicator
        kind: Metric type - "gain", "risk", "analytics", "goal", or "neutral"
        help_text: Optional tooltip text
    """
    colors = METRIC_COLORS.get(kind, METRIC_COLORS["neutral"])
    
    # Build delta HTML if provided
    delta_html = ""
    if delta:
        delta_color = colors["text_color"] if kind == "gain" else colors["icon_color"]
        delta_html = f'<div style="font-size: 0.875rem; color: {delta_color}; margin-top: 4px;">{delta}</div>'
    
    # Help icon if help text provided
    help_icon = f'<span title="{help_text}" style="opacity: 0.6; margin-left: 8px; cursor: help;">ℹ️</span>' if help_text else ""
    
    metric_html = f"""
    <div style="
        background: {colors['bg']};
        backdrop-filter: blur(10px);
        border: 1px solid {colors['border']};
        border-radius: 12px;
        padding: 20px;
        margin: 8px 0;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    ">
        <div style="
            font-size: 0.875rem;
            color: rgba(255, 255, 255, 0.8);
            font-weight: 500;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        ">
            {label}{help_icon}
        </div>
        <div style="
            font-size: 2rem;
            font-weight: 700;
            color: {colors['text_color']};
            line-height: 1.2;
        ">
            {value}
        </div>
        {delta_html}
    </div>
    """
    
    st.markdown(metric_html, unsafe_allow_html=True)

def render_metric_row(metrics):
    """
    Render multiple metrics in a responsive row.
    
    Args:
        metrics: List of dicts with keys: label, value, delta (optional), kind, help_text (optional)
    
    Example:
        render_metric_row([
            {"label": "Total Wealth", "value": "$125,000", "kind": "gain"},
            {"label": "Risk Level", "value": "Medium", "kind": "risk"}
        ])
    """
    cols = st.columns(len(metrics))
    for col, metric in zip(cols, metrics):
        with col:
            render_metric_card(
                label=metric.get("label", ""),
                value=metric.get("value", ""),
                delta=metric.get("delta"),
                kind=metric.get("kind", "neutral"),
                help_text=metric.get("help_text")
            )

def render_highlight_box(title, message, kind="neutral"):
    """
    Render a highlighted insight box.
    
    Args:
        title: Box title
        message: Main message content
        kind: Style type - "gain", "risk", "analytics", "goal", or "neutral"
    """
    colors = METRIC_COLORS.get(kind, METRIC_COLORS["neutral"])
    
    box_html = f"""
    <div style="
        background: {colors['bg']};
        backdrop-filter: blur(10px);
        border-left: 4px solid {colors['border']};
        border-radius: 8px;
        padding: 16px 20px;
        margin: 12px 0;
        animation: slideIn 0.4s ease;
    ">
        <div style="
            font-size: 1rem;
            font-weight: 600;
            color: {colors['text_color']};
            margin-bottom: 8px;
        ">
            {title}
        </div>
        <div style="
            font-size: 0.9rem;
            color: rgba(255, 255, 255, 0.9);
            line-height: 1.5;
        ">
            {message}
        </div>
    </div>
    
    <style>
        @keyframes slideIn {{
            from {{
                opacity: 0;
                transform: translateX(-20px);
            }}
            to {{
                opacity: 1;
                transform: translateX(0);
            }}
        }}
    </style>
    """
    
    st.markdown(box_html, unsafe_allow_html=True)
