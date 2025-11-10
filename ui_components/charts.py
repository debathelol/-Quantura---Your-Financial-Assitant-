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
        updatemenus=[],
        hovermode='closest'
    )
    
    # Add smooth transitions only for traces that support markers
    for trace in fig.data:
        # Skip Candlestick and other traces that don't support marker property
        if hasattr(trace, 'marker') and trace.type not in ['candlestick', 'ohlc']:
            try:
                trace.update(
                    marker=dict(
                        line=dict(width=1, color='rgba(255, 255, 255, 0.3)')
                    )
                )
            except:
                pass
    
    return fig
