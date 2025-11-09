import matplotlib.pyplot as plt
from io import BytesIO

def fig_to_png_download(fig, filename):
    """Convert matplotlib figure to PNG bytes for download"""
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    return buf.getvalue()
