import matplotlib.pyplot as plt
from io import BytesIO

def fig_to_png_download(fig, filename):
    """Convert matplotlib figure to PNG bytes for download"""
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    return buf.getvalue()

def add_plotly_animations(fig, duration=500):
    """
    Add smooth fade-in animations to Plotly charts.
    
    Args:
        fig: Plotly figure object
        duration: Animation duration in milliseconds (default 500ms)
    
    Returns:
        Modified figure with animations
    """
    fig.update_layout(
        transition_duration=duration,
        updatemenus=[],  # Clear any existing update menus
        hovermode='closest'
    )
    
    # Add smooth transitions for all traces
    for trace in fig.data:
        trace.update(
            marker=dict(
                line=dict(width=1, color='rgba(255, 255, 255, 0.3)')
            )
        )
    
    return fig
